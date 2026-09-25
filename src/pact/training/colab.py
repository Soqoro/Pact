"""Bounded warm-start Colab execution and durable recovery; no notebook science."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from ..artifacts import artifact_files, safe_relative, sync_run
from ..storage import persist_bundle, storage_operation
from ..util import canonical, file_hash, read_json, redact, safe_name, write_json
from .checkpoints import latest_checkpoint
from .warmstart_config import load_warmstart_config, warmstart_plan


def _restore_snapshot(snapshot: Path, destination: Path, *, progress=lambda message: None, kind="warmstart"):
    """Restore only the explicitly selected, complete snapshot; never fall back."""
    if destination.exists():
        raise ValueError("Restore requires a new scratch run directory")
    index_path = snapshot / "index.json"
    if snapshot.parent.name != "snapshots" or (snapshot / "COMPLETE").read_text() != file_hash(index_path):
        raise ValueError("Invalid snapshot completion marker")
    index = read_json(index_path)
    entries = index["files"]
    if index.get("schema_version") != 1 or not isinstance(entries, dict) or not 1 <= len(entries) <= (40000 if kind == "specialization_fixed_bank" else 10000 if kind in ("receiver_supervision", "gpqa_support") else 5000):
        raise ValueError("Invalid snapshot inventory")
    if kind not in ("specialization_fixed_bank", "gpqa_support", "receiver_supervision", "warmstart", "training_bank", "preference_feasibility_diagnostic", "receiver_feasibility_diagnostic", "private_support_control", "curated_repair_diagnostic", "actor_preparation_probe", "preparation_prompt_control"):
        raise ValueError("Unknown snapshot kind")
    required = {"run.json", "examples.json"} if kind == "warmstart" else {"manifest.json", "data_manifest.json", "model_identity.json"}
    if kind in ("preference_feasibility_diagnostic", "private_support_control", "curated_repair_diagnostic", "actor_preparation_probe", "preparation_prompt_control"):
        required = {"manifest.json", "plan.json", "model_identity.json"}
    if kind in ("specialization_fixed_bank", "receiver_supervision", "gpqa_support"): required = ({"state.json", "plan.json"} if kind in ("gpqa_support", "specialization_fixed_bank") else {"state.json", "plan.json", "recipe.json"})
    if not required <= entries.keys():
        raise ValueError("Snapshot is not an initialized run of the requested kind")
    if kind in ("receiver_feasibility_diagnostic", "private_support_control", "curated_repair_diagnostic", "actor_preparation_probe", "preparation_prompt_control"):
        latest = max(p.name for p in snapshot.parent.iterdir() if p.is_dir())
        if snapshot.name != latest:
            raise ValueError("Receiver restore must use latest snapshot; no rollback of attempted-call budget")
    if kind in ("specialization_fixed_bank", "receiver_supervision", "gpqa_support") and snapshot.name != max(p.name for p in snapshot.parent.iterdir() if p.is_dir()):
        raise ValueError("Receiver study restore requires latest snapshot; no budget rollback")
    objects = snapshot.parent.parent / "objects"
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".pact-restore-", dir=destination.parent))
    try:
        size = 0
        for position, (name, sha) in enumerate(entries.items(), 1):
            rel = safe_relative(name)
            if any(part.startswith(".") for part in rel.parts) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                raise ValueError("Invalid snapshot entry")
            obj = objects / sha
            if obj.is_symlink() or not obj.is_file():
                raise ValueError("Missing or symlinked snapshot object")
            size += obj.stat().st_size
            if size > 20 * 1024**3:
                raise ValueError("Snapshot exceeds 20 GiB restore limit")
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(obj, target)
            if file_hash(target) != sha:
                raise ValueError("Corrupt snapshot object")
            if position == 1 or position % 10 == 0 or position == len(entries):
                progress(f"Restoring verified {kind} files: {position}/{len(entries)}")
        if kind == "specialization_fixed_bank":
            from .specialization_study import load_plan, validate_recovery
            plan = load_plan(staging)
            if not read_json(staging / "state.json")["recovery_safe"]:
                raise ValueError("Unsafe specialization snapshot; no rollback")
            validate_recovery(staging, plan)
        elif kind == "gpqa_support":
            from ..studies.gpqa_study import load_plan, journals
            plan = load_plan(staging)
            if not read_json(staging / "state.json")["recovery_safe"] or journals(staging, plan)[2]:
                raise ValueError("Unsafe GPQA snapshot; no rollback or invisible retry")
        elif kind == "receiver_supervision":
            from .receiver_study import validate_local_recovery
            from ..util import digest
            state = read_json(staging / "state.json")
            if not state.get("recovery_safe") or state["study_hash"] != digest(read_json(staging / "recipe.json")):
                raise ValueError("Unsafe receiver study snapshot; possible lost attempts")
            if read_json(staging / "plan.json") != read_json(staging / "recipe.json")["plan"]:
                raise ValueError("Receiver study plan mismatch")
            validate_local_recovery(staging, read_json(staging / "plan.json"))
        elif kind == "warmstart":
            latest_checkpoint(staging / "checkpoints", read_json(staging / "run.json")["identity"])
        else:
            from ..artifacts import ShardStore
            from ..util import digest
            manifest = read_json(staging / "manifest.json")
            expected_kind = "training_bank_engineering" if kind == "training_bank" else kind
            if (manifest.get("kind") != expected_kind
                    or manifest["recipe_hash"] != digest(manifest["recipe"])
                    or manifest["identity"]["recipe_hash"] != manifest["recipe_hash"]
                    or len(ShardStore(staging).records()) != manifest["completed_records"]):
                raise ValueError("Collection snapshot provenance/count mismatch")
            if kind in ("receiver_feasibility_diagnostic", "private_support_control", "curated_repair_diagnostic", "actor_preparation_probe", "preparation_prompt_control"):
                from .receiver import inspect_journal
                if not manifest.get("recovery_safe"):
                    raise ValueError("Snapshot precedes possible lost calls; explicit recovery-budget review required")
                _, calls = inspect_journal(staging, read_json(staging/"plan.json")["budget"])
                if len(calls) != manifest.get("committed_calls"):
                    raise ValueError("Restored call journal count mismatch")
        staging.rename(destination)
        return {"restored_snapshot": str(snapshot), "run_dir": str(destination)}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def restore_snapshot(snapshot, destination, *, timeout_seconds=120):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return storage_operation("warmstart-restore", Path(snapshot), destination,
                             timeout_seconds=timeout_seconds)


def review_bundle(root: Path, output: Path, outcome: dict, *, kind="warmstart_engineering_review",
                  scientific_status="clean_answer_warmstart_engineering_only", max_metadata_bytes=90 * 1024**2, include_markdown=False):
    """Small diagnostic archive. Tensor checkpoints remain in the full snapshot."""
    if output.exists():
        raise FileExistsError("Never overwrite a prior handoff")
    files = artifact_files(root) if root.exists() else []
    inventory = {p.relative_to(root).as_posix(): {"sha256": file_hash(p), "bytes": p.stat().st_size}
                 for p in files}
    # JSON state contains tensor references, not tensor payloads. Include it for audit.
    metadata = [p for p in files if p.suffix in ((".json", ".jsonl", ".txt", ".md") if include_markdown else (".json", ".jsonl", ".txt"))]
    if sum(p.stat().st_size for p in metadata) > max_metadata_bytes:
        raise ValueError("Review metadata exceeds declared byte limit")
    payload = {p.relative_to(root).as_posix(): p.read_bytes() for p in metadata}
    payload["HANDOFF.json"] = canonical({"kind": kind, "schema_version": 1,
        "resume_archive": False, "outcome": outcome, "inventory": inventory,
        "scientific_status": scientific_status}).encode()
    import hashlib
    payload["review_checksums.json"] = canonical({n: hashlib.sha256(v).hexdigest() for n, v in payload.items()}).encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".review-", dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in payload.items():
                archive.writestr(name, data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() or any(archive.read(n) != v for n, v in payload.items()):
                raise ValueError("Review ZIP verification failed")
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"path": str(output), "sha256": file_hash(output), "bytes": output.stat().st_size}


def handoff(*, root, bundles, persistent, run_id, outcome, timeout_seconds=120):
    """Always make a local review first; Drive failures cannot block it indefinitely."""
    root, bundles, persistent = Path(root), Path(bundles), Path(persistent)
    safe_name(run_id)
    outcome = dict(outcome, persistent_copy_verified=False, persistent_snapshot=None)
    local = bundles / f"{run_id}-local-review-{time.time_ns()}.zip"
    result = review_bundle(root, local, outcome)
    print(f"Local review ZIP ready: {local} SHA256: {result['sha256']}", flush=True)
    result.update(outcome, persistent_bundle=None)
    try:
        # Only checkpoint-bearing runs can support recovery after a runtime reset.
        latest_checkpoint(root / "checkpoints", read_json(root / "run.json")["identity"])
        snapshot = sync_run(root, persistent / "warmstart" / run_id, timeout_seconds=timeout_seconds)
        result.update(persistent_copy_verified=True, persistent_snapshot=str(snapshot))
        verified = bundles / f"{run_id}-handoff-{time.time_ns()}.zip"
        result.update(review_bundle(root, verified, {**outcome, "persistent_copy_verified": True,
                                                   "persistent_snapshot": str(snapshot)}))
        target = persistent / "bundles" / verified.name
        persist_bundle(verified, target, result["sha256"], timeout_seconds=timeout_seconds)
        result["persistent_bundle"] = str(target)
    except (Exception, KeyboardInterrupt) as exc:
        result.update(persistence_error=redact(str(exc)), exit_code=2)
        print("Persistence incomplete; keep this runtime and all scratch checkpoints. "
              "The review ZIP alone cannot resume training.", flush=True)
    print(canonical(result), flush=True)
    return result


def execute(*, checkout, data_dir, run_id, scratch, persistent, resume=False,
            stop_after=1, timeout_seconds=120):
    """Explicit execution entry point; called only by the notebook's gated cell."""
    safe_name(run_id)
    checkout, data_dir, scratch = Path(checkout), Path(data_dir), Path(scratch)
    config = checkout / "experiments" / "warmstart_engineering.json"
    warmstart_plan(load_warmstart_config(config), data_dir)
    root = scratch / "warmstart" / run_id
    if (root.exists() and not resume) or (resume and not (root / "run.json").is_file()):
        raise ValueError("Use a new run ID, or restore the same run and explicitly resume")
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be positive or None")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("Storage timeout must be positive and finite")
    scratch.mkdir(parents=True, exist_ok=True)
    log_dir = scratch / "warmstart-logs" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / f"invocation-{time.time_ns()}.txt"
    args = [sys.executable, "-u", "-m", "pact", "warmstart", "--execute", "--config", str(config),
            "--data-dir", str(data_dir), "--run-dir", str(root), "--cache-dir", str(scratch / "cache" / "models")]
    if resume:
        args.append("--resume")
    if stop_after is not None:
        args.extend(["--stop-after", str(stop_after)])
    env = {**os.environ, "HF_HOME": str(scratch / "cache" / "huggingface"),
           "TOKENIZERS_PARALLELISM": "false", "PYTHONPATH": str(checkout / "src")}
    started = time.monotonic()
    # A child releases GPU allocations before copying checkpoints and constructing ZIPs.
    with log.open("w") as stream:
        process = subprocess.Popen(args, cwd=checkout, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True)
        try:
            for line in process.stdout:
                line = redact(line)
                print(line, end="", flush=True)
                stream.write(line)
                stream.flush()
            code = process.wait()
        except KeyboardInterrupt:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            code = 130
        finally:
            process.stdout.close()
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    shutil.copyfile(log, root / "logs" / log.name)
    outcome = {"exit_code": code, "invocation_seconds": time.monotonic() - started,
               "resume": resume, "stop_after": stop_after,
               "status": read_json(root / "status.json") if (root / "status.json").exists() else None}
    write_json(root / "invocation.json", outcome)
    return handoff(root=root, bundles=scratch / "bundles", persistent=persistent,
                   run_id=run_id, outcome=outcome, timeout_seconds=timeout_seconds)
