from __future__ import annotations

import dataclasses
import shlex
import time
import traceback
import uuid
from pathlib import Path

from .artifacts import ShardStore, export_bundle, restore_run, run_lock, sync_run
from .backends import create_backend
from .config import Config, budget
from .datasets import prepare
from .environment import code_identity, doctor
from .evaluation import score
from .protocol import Protocol
from .replay import probe
from .reporting import report
from .schemas import RunManifest
from .attacks import fixed_attack
from .util import atomic_write, canonical, digest, read_json, redact, safe_name, write_json


class RunFailed(RuntimeError):
    pass


def inspect_run(root: Path) -> dict:
    manifest = read_json(root / "manifest.json")
    records = ShardStore(root).records() if (root / "shards").exists() else read_json(root / "evaluations.json")
    return {"run_id": manifest["run_id"], "scientific_status": manifest["scientific_status"],
            "stage_status": manifest["stage_status"], "completed": len(records), "expected": manifest["expected_records"],
            "missing": manifest["expected_records"] - len(records), "config_hash": manifest["config_hash"],
            "model_snapshot": manifest.get("model_identity", {}).get("snapshot"), "source": manifest["code"]}


def run(config: Config, *, run_id: str, scratch: Path, persistent: Path | None = None,
        resume=False, stop_after: int | None = None, invocation: tuple[str, ...] = (),
        backend_factory=create_backend) -> Path:
    config.validate()
    safe_name(run_id)
    selection = getattr(config, "selection", None)
    if selection and run_id == selection.source_run_id:
        raise ValueError("Selected feasibility requires a new run ID, distinct from its source run")
    scratch = scratch.resolve()
    persistent = persistent.resolve() if persistent else None
    if persistent and (scratch == persistent or scratch in persistent.parents or persistent in scratch.parents):
        raise ValueError("Scratch and persistent roots must be separate, non-nested locations")
    root = scratch / "runs" / run_id
    remote = persistent / run_id if persistent else None
    if resume and not (root / "manifest.json").exists() and remote and remote.exists():
        restore_run(remote, root)
    if root.exists() and (root / "manifest.json").exists() and not resume:
        raise FileExistsError("Run exists. Use --resume for the identical configuration or a new run ID")
    if root.exists() and any(root.iterdir()) and not (root / "manifest.json").exists() and not resume:
        raise FileExistsError("Nonempty run directory lacks a manifest; inspect it or choose a new run ID")
    if resume and not (root / "manifest.json").exists():
        raise FileNotFoundError("No run to resume locally or in verified persistent snapshots")
    source = code_identity(Path(__file__).resolve().parents[2])
    old = read_json(root / "manifest.json") if resume else None
    if old and (old["config_hash"] != config.identity or old["code"]["source_hash"] != source["source_hash"] or old["code"]["git_commit"] != source["git_commit"]):
        raise ValueError("Configuration/code mismatch on resume; create a new run ID (no implicit statistical continuation)")
    root.mkdir(parents=True, exist_ok=True)
    expected = config.items * len(config.methods) * len(config.conditions)
    manifest = old or dataclasses.asdict(RunManifest(run_id, config.identity, source, {}, "", config.seed,
             {"preflight": "pending", "data": "pending", "collection": "pending", "report": "pending",
              "training": "deferred", "final_test": "deferred"}, expected, 0, invocation,
             "mock_only" if config.backend == "mock" else "untrained_validation_diagnostic", ""))
    if selection:
        manifest["selection"] = dataclasses.asdict(selection)
        if config.backend != "mock":
            manifest["scientific_status"] = "selected_validation_feasibility"
    manifest["persistent_root"] = str(remote) if remote else None
    manifest["stage_status"]["persistence"] = "pending" if remote else "not_configured"
    manifest.pop("verified_snapshot", None)
    manifest["budget"] = budget(config)
    next_command = ["python", "-m", "pact", config.stage, "--config", str(root / "resolved_config.yaml"),
                    "--run-id", run_id, "--scratch", str(scratch), "--resume"]
    if persistent:
        next_command += ["--persistent", str(persistent)]
    backend = None
    checkpoint_error = None
    store = ShardStore(root)
    attempt_id = uuid.uuid4().hex
    started = time.perf_counter()
    with run_lock(root):
        write_json(root / "resolved_config.yaml", dataclasses.asdict(config))
        write_json(root / "manifest.json", manifest)
        for name in ("environment.json", "data_manifest.json"):
            if not (root / name).exists():
                write_json(root / name, {"status": "not_collected", "reason": "stage not reached"})
        if not (root / "package_freeze.txt").exists():
            atomic_write(root / "package_freeze.txt", "")
        attempt = {"schema_version": 1, "attempt_id": attempt_id, "status": "running", "invocation": list(invocation),
                   "completed_new_records": 0, "uncommitted_calls": [], "error": None}
        write_json(root / "attempts" / f"{attempt_id}.json", attempt)
        try:
            env = doctor(scratch, persistent, config)
            if old and old["runtime_fingerprint"] and old["runtime_fingerprint"] != env["runtime_fingerprint"]:
                raise ValueError("Runtime/library fingerprint changed; resume would not be exact. Use a new run ID")
            manifest["runtime_fingerprint"] = env["runtime_fingerprint"]
            write_json(root / "environment.json", env)
            atomic_write(root / "package_freeze.txt", "".join(f"{k}=={v}\n" for k, v in env["packages"].items()))
            if env["errors"]:
                raise RuntimeError("Preflight failed: " + "; ".join(env["errors"]))
            manifest["stage_status"]["preflight"] = "complete"
            tasks, labels, data_manifest = prepare(config, scratch / "cache" / "datasets")
            if old and old["data_manifest_hash"] and old["data_manifest_hash"] != digest(data_manifest):
                raise ValueError("Dataset manifest mismatch")
            manifest["data_manifest_hash"] = digest(data_manifest)
            write_json(root / "data_manifest.json", data_manifest)
            write_json(root / "task_inputs.json", [dataclasses.asdict(t) for t in tasks])
            write_json(root / "task_labels.json", {k: dataclasses.asdict(v) for k, v in labels.items()})
            manifest["stage_status"]["data"] = "complete"
            write_json(root / "manifest.json", manifest)
            backend = backend_factory(config, scratch / "cache" / "models")
            if selection and backend.identity["snapshot"] != selection.source_model_snapshot:
                raise ValueError("Selected source model snapshot mismatch; no generation permitted")
            selected_attacks = {}
            if selection:
                # Validate every source attack before the first model generation.
                for task, chosen in zip(tasks, selection.tasks):
                    for condition in config.conditions:
                        attack = fixed_attack(task, labels[task.task_id], condition, chosen.source_position,
                                              config.seed, backend, config.limits.payload)
                        if attack.attack_id != getattr(chosen, f"{condition}_attack_id"):
                            raise ValueError("Selected source attack mismatch; no generation permitted")
                        selected_attacks[task.task_id, condition] = attack
            if old and old["model_identity"] and old["model_identity"]["snapshot"] != backend.identity["snapshot"]:
                raise ValueError("Model/adapter/checkpoint snapshot mismatch")
            manifest["model_identity"] = backend.identity
            manifest["stage_status"]["collection"] = "running"
            write_json(root / "manifest.json", manifest)
            protocol = Protocol(config, backend)
            # One balanced reference attack assignment per task/channel, independent of compared method.
            for position, task in enumerate(tasks):
                for condition in config.conditions:
                    source_position = data_manifest["selected"][position].get("source_position", position)
                    attack = (selected_attacks[task.task_id, condition] if selection else
                              fixed_attack(task, labels[task.task_id], condition, source_position, config.seed, backend, config.limits.payload))
                    for method in config.methods:
                        key = digest([config.identity, task.task_id, attack.attack_id, method, backend.identity["snapshot"]])
                        existing = store.read(key)
                        if existing is not None:
                            if existing["config_hash"] != config.identity or existing["snapshot"] != backend.identity["snapshot"]:
                                raise ValueError("Completed shard config/checkpoint mismatch")
                            continue
                        attempt["work_in_progress"] = {"task_id": task.task_id, "method": method, "condition": condition, "work_id": key}
                        write_json(root / "attempts" / f"{attempt_id}.json", attempt)
                        backend.calls.clear()
                        trajectory = protocol.run(task, method, attack)
                        replays, preferences = ((), ())
                        if method == "debate" and position < config.probe.tasks:
                            replays, preferences = probe(protocol, trajectory, labels[task.task_id])
                        calls = tuple(backend.calls)
                        value = {"schema_version": 1, "work_id": key, "config_hash": config.identity,
                                 "snapshot": backend.identity["snapshot"], "trajectory": dataclasses.asdict(trajectory),
                                 "evaluation": score(trajectory, labels[task.task_id]),
                                 "replays": [dataclasses.asdict(p) for p in replays],
                                 "preferences": [dataclasses.asdict(p) for p in preferences],
                                 "resources": {"calls": len(calls), "input_tokens": sum(c.input_tokens for c in calls),
                                               "output_tokens": sum(c.output_tokens for c in calls),
                                               "generation_seconds": sum(c.elapsed_seconds for c in calls)}}
                        store.put(key, value)
                        backend.calls.clear()
                        attempt["completed_new_records"] += 1
                        manifest["completed_records"] = len(list((root / "shards").glob("*.sha256")))
                        write_json(root / "manifest.json", manifest)
                        print(f"[{run_id}] {manifest['completed_records']}/{expected} {method}/{condition}", flush=True)
                        if remote and manifest["completed_records"] < expected and attempt["completed_new_records"] % config.sync_every == 0:
                            try:
                                sync_run(root, remote)
                            except (Exception, KeyboardInterrupt) as exc:
                                checkpoint_error = exc
                                raise
                        if stop_after and attempt["completed_new_records"] >= stop_after:
                            raise InterruptedError("Requested simulated interruption at completed-record boundary")
            manifest["stage_status"]["collection"] = "complete"
            attempt["status"] = "complete"
        except (Exception, KeyboardInterrupt) as exc:
            attempt.update(status="interrupted" if isinstance(exc, (KeyboardInterrupt, InterruptedError)) else "failed",
                           error={"type": type(exc).__name__, "message": redact(str(exc)),
                                  "traceback": redact(traceback.format_exc()), "next_command": shlex.join(next_command),
                                  "oom_guidance": "Inspect resource_usage.json; retry the SAME config with --resume, or select an explicit smaller engineering preset and NEW run ID. No settings were changed."},
                           uncommitted_calls=[dataclasses.asdict(c) for c in backend.calls] if backend else [])
            attempt["failed_call_context"] = getattr(backend, "pending_call", None)
            manifest["stage_status"]["collection"] = attempt["status"]
        finally:
            attempt["elapsed_seconds"] = time.perf_counter() - started
            attempt["backend_resources"] = backend.resource_usage() if backend else {}
            if config.backend == "transformers" and not backend:
                import importlib.util
                if importlib.util.find_spec("torch"):
                    import torch
                    if torch.cuda.is_available():
                        attempt["backend_resources"].update(peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                                                            peak_reserved_bytes=torch.cuda.max_memory_reserved())
            write_json(root / "attempts" / f"{attempt_id}.json", attempt)
            write_json(root / "logs" / f"{attempt_id}.json", {k: attempt.get(k) for k in
                       ("attempt_id", "status", "elapsed_seconds", "completed_new_records", "work_in_progress", "error", "backend_resources")})
            try:
                records = store.records()
            except (ValueError, OSError) as exc:
                records = []
                attempt["artifact_integrity_error"] = redact(str(exc))
                attempt["status"] = "failed"
                manifest["stage_status"]["collection"] = "failed"
                attempt["error"] = attempt.get("error") or {"type": type(exc).__name__, "message": redact(str(exc)),
                    "next_command": f"python -m pact inspect-run --run-dir {shlex.quote(str(root))}"}
                write_json(root / "attempts" / f"{attempt_id}.json", attempt)
            manifest["completed_records"] = len(records)
            attempts = [read_json(p) for p in (root / "attempts").glob("*.json")]
            usage = {key: sum(r["resources"][key] for r in records) for key in ("calls", "input_tokens", "output_tokens", "generation_seconds")}
            usage.update(compute_units=None, cache_hits=0,
                         failed_attempts=sum(a["status"] not in ("complete", "running") for a in attempts),
                         interrupted_attempts_with_unknown_cost=sum(a["status"] == "running" for a in attempts),
                         failed_record_input_tokens=sum(c["input_tokens"] for a in attempts for c in a.get("uncommitted_calls", [])),
                         failed_record_output_tokens=sum(c["output_tokens"] for a in attempts for c in a.get("uncommitted_calls", [])),
                         elapsed_attempt_seconds=sum(a.get("elapsed_seconds", 0) for a in attempts),
                         accelerator_hours=sum(a.get("elapsed_seconds", 0) for a in attempts) / 3600 if config.backend == "transformers" and config.model.device == "cuda" else None,
                         token_unit="mock lexical tokens" if config.backend == "mock" else "model tokenizer tokens",
                         attempts=[{k: a.get(k) for k in ("attempt_id", "status", "elapsed_seconds", "backend_resources")} for a in attempts],
                         profiling={"inference": "measured" if backend else "unavailable", "training_microbatch": "deferred", "length_sensitivity": "deferred"})
            usage["output_tokens_per_generation_second"] = usage["output_tokens"] / usage["generation_seconds"] if usage["generation_seconds"] else None
            for name in ("peak_allocated_bytes", "peak_reserved_bytes"):
                measured = [a.get("backend_resources", {}).get(name) for a in attempts]
                usage[name] = max((x for x in measured if x is not None), default=None)
            usage["failed_generation_output_tokens_unknown"] = sum(bool(a.get("failed_call_context")) for a in attempts)
            write_json(root / "resource_usage.json", usage)
            manifest["stage_status"]["report"] = "complete"
            if remote:
                manifest["stage_status"]["persistence"] = "pending"
            write_json(root / "manifest.json", manifest)
            report(root, validated_records=records)
            if remote:
                # Make recovery possible before touching Drive, even if the mount stalls.
                recovery = scratch / "bundles" / f"{run_id}-local-{attempt_id[:8]}.zip"
                local_bundle = export_bundle(root, recovery)
                print(f"Local recovery ZIP ready: {recovery} SHA256: {local_bundle['sha256']}", flush=True)
                try:
                    if checkpoint_error is not None:
                        raise OSError(f"Earlier checkpoint failed; not retrying storage automatically: {checkpoint_error}")
                    snapshot = sync_run(root, remote)
                    manifest["stage_status"]["persistence"] = "complete"
                    manifest["verified_snapshot"] = str(snapshot)
                    write_json(root / "manifest.json", manifest)
                    report(root, validated_records=records)
                    print(f"Verified persistent snapshot: {snapshot}", flush=True)
                except (Exception, KeyboardInterrupt) as exc:
                    attempt["persistence_error"] = redact(str(exc))
                    attempt["persistence_status"] = "failed"
                    manifest["stage_status"]["persistence"] = "failed"
                    write_json(root / "attempts" / f"{attempt_id}.json", attempt)
                    write_json(root / "logs" / f"{attempt_id}.json", {k: attempt.get(k) for k in
                               ("attempt_id", "status", "elapsed_seconds", "completed_new_records", "error",
                                "backend_resources", "persistence_error", "persistence_status")})
                    write_json(root / "manifest.json", manifest)
                    report(root, validated_records=records)
                    bundle = scratch / "bundles" / f"{run_id}-diagnostic-{attempt_id[:8]}.zip"
                    export_bundle(root, bundle)
                    # Keep local diagnostics and fail visibly; never report remote completion.
                    raise RunFailed(f"Persistence failed; local diagnostic bundle: {bundle}. Retry: {shlex.join(next_command)}") from exc
            if attempt["status"] != "complete":
                bundle = scratch / "bundles" / f"{run_id}-diagnostic-{attempt_id[:8]}.zip"
                export_bundle(root, bundle)
                raise RunFailed(f"{attempt['error']['type']}: {attempt['error']['message']}\nDiagnostic bundle: {bundle}\nNext command: {shlex.join(next_command)}")
    return root
