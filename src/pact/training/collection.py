"""Bounded frozen-team training bank, immutable raw shards and resumable scoring."""
from __future__ import annotations

import dataclasses
from pathlib import Path
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..attacks import fixed_attack
from ..environment import code_identity, versions
from ..parsing import parse_answer
from ..protocol import Protocol
from ..replay import probe
from ..storage import persist_bundle
from ..util import canonical, digest, read_json, redact, write_json
from .bank import BankRow, Candidate, ReceiverContext, ScoredBank, WarmstartReference, bank_from_dict
from .collection_config import collection_plan
from .losses import answer_target
from .preferences import build_preferences
from .reference import ReferenceCache, reference_request
from .scoring import ACTORS, CollectionBackend, verify_references


def bank_for(records, config, backend, *, synthetic=False):
    base = backend.base_identity
    bank = {"schema_version": 1, "kind": "synthetic_fixture" if synthetic else "training", "split": "train",
            "actor_snapshot": backend.identity["snapshot"], "base_snapshot": base["snapshot"],
            "data_manifest_hash": config.data_manifest_hash, "tokenizer_revision": base["tokenizer_revision"],
            "template_hash": base["template_hash"], "precision": base["precision"],
            "runtime_fingerprint": base["runtime_fingerprint"], "eos_id": backend.tokenizer.eos_token_id,
            "warmstart_references": [dataclasses.asdict(WarmstartReference(i, "warm_start_adapter", h))
                                     for i, h in enumerate(config.reference_hashes)],
            "rows": [r["row"] for r in records],
            "receivers": [c for r in records for c in r["receivers"]]}
    # Normalize tuple/list structure as it will appear in immutable JSON shards.
    import json
    return bank_from_dict(json.loads(canonical(bank)), allow_synthetic=synthetic)


def cache_reference_scores(bank, backend, root, *, synthetic=False):
    bank.validate(allow_synthetic=synthetic)
    base = backend.base_identity
    if (bank.actor_snapshot != backend.identity["snapshot"] or bank.base_snapshot != base["snapshot"]
            or bank.tokenizer_revision != base["tokenizer_revision"] or bank.template_hash != base["template_hash"]
            or bank.precision != base["precision"] or bank.runtime_fingerprint != base["runtime_fingerprint"]
            or bank.eos_id != backend.tokenizer.eos_token_id
            or tuple(r.adapter_hash for r in sorted(bank.warmstart_references, key=lambda r: r.agent))
               != tuple(backend.scorer.reference_hashes)):
        raise ValueError("Bank differs from loaded actors/reference/model/runtime")
    backend.assert_unchanged()
    preferences = build_preferences(bank, allow_synthetic=synthetic)
    cache = ReferenceCache(Path(root))
    scores = []
    for pair in preferences["pairs"]:
        for side in ("positive", "negative"):
            request = reference_request(bank, pair, side)
            path = cache.root / f"{request.key}.json"
            if not path.exists():
                cache.put(request, backend.scorer.reference_score(request))
            scores.append({"context_id": pair["context_id"], "agent": pair["agent"], "side": side,
                           "request_key": request.key, "sum_logp": cache.get(request),
                           "token_count": len(request.completion_ids)})
    backend.assert_unchanged()
    return preferences, {"bank_hash": bank.identity, "reduction": "sum including terminal EOS",
                         "scores": scores, "reference_forward_required": bool(scores),
                         "missing_strata": preferences["missing_strata"]}


def collect_record(protocol, task, label, attack, work_id):
    backend = protocol.backend
    if task.split != "train" or label.task_id != task.task_id or attack.split != "train":
        raise ValueError("Collection requires same-task training provenance")
    backend.assert_unchanged()
    backend.generation_tokens.clear()
    start = len(backend.calls)
    trajectory = protocol.run(task, "debate", attack)
    pairs, preferences = probe(protocol, trajectory, label)
    answer_scores = [backend.scorer.answer_score(i, p.call.rendered_prompt, answer_target(label.answer_id))
                     for i, p in enumerate(trajectory.private)]
    packet_scores = []
    for pair in pairs:
        if pair.status == "eligible":
            packet = pair.candidates[pair.positive_index]
            tokens = backend.generation_tokens[digest(packet.call)]
            scored = backend.scorer.token_score(ACTORS[pair.agent], packet.call.rendered_prompt,
                         tokens["prompt_ids"], packet.raw, tokens["completion_ids"])
            packet_scores.append({"agent": pair.agent, "pair_id": pair.pair_id, **scored})
    row = BankRow(work_id, task.task_id, task.split, task.source_hash, digest(label),
                  tuple(o.answer_id for o in task.options), label.answer_id,
                  tuple(p.answer_id == label.answer_id and p.parser_status == "ok" for p in trajectory.private),
                  tuple(s["mean_nll"] for s in answer_scores), tuple(p.delta for p in pairs),
                  tuple(p.pair_id if p.status == "eligible" else None for p in pairs))
    receivers = []
    for preference in preferences:
        original = trajectory.revised[preference.agent].call
        original_tokens = backend.generation_tokens[digest(original)]
        answers = [parse_answer(m.text, row.allowed_answers)[0] for m in trajectory.delivered
                   if m.recipient == preference.agent]
        candidates = []
        for packet in preference.candidates:
            tokens = backend.generation_tokens[digest(packet.call)]
            if (tokens["prompt_ids"] != original_tokens["prompt_ids"] or packet.call.rendered_prompt != original.rendered_prompt
                    or tokens["raw"] != packet.raw or tokens["context_hash"] != original.context_hash):
                raise ValueError("Receiver token/prompt provenance changed")
            candidates.append(Candidate(packet.raw, original.context_hash, tuple(tokens["prompt_ids"]),
                                        tuple(tokens["completion_ids"]), packet.call.stop_reason))
        receivers.append(ReceiverContext(work_id, preference.agent, original.rendered_prompt,
                          tuple(original_tokens["prompt_ids"]), label.answer_id in answers,
                          any(a is not None and a != label.answer_id for a in answers), tuple(candidates)))
    backend.assert_unchanged()
    calls = backend.calls[start:]
    if len(calls) > 79:
        raise RuntimeError("Per-record generation budget exceeded")
    return {"schema_version": 1, "work_id": work_id, "trajectory": dataclasses.asdict(trajectory),
            "replays": [dataclasses.asdict(p) for p in pairs],
            "receiver_probes": [dataclasses.asdict(p) for p in preferences],
            "row": dataclasses.asdict(row), "receivers": [dataclasses.asdict(c) for c in receivers],
            "answer_scores": answer_scores, "packet_scores": packet_scores,
            "generation_tokens": dict(backend.generation_tokens),
            "generation_calls": len(calls), "input_tokens": sum(c.input_tokens for c in calls),
            "output_tokens": sum(c.output_tokens for c in calls)}


def collect_records(config, tasks, labels, runtime, backend, root, *, stop_after=None, boundary=lambda: None, synthetic=False):
    """Resume by immutable task/attack shard. Partial shards never become bank rows."""
    store = ShardStore(root)
    protocol = Protocol(runtime, backend)
    scheduled = [(task, fixed_attack(task, labels[task.task_id], channel, position, config.seed, backend, runtime.limits.payload))
                 for position, task in enumerate(tasks) for channel in config.conditions]
    work = [(task, attack, digest([digest(config), task, attack, backend.identity["snapshot"]])) for task, attack in scheduled]
    expected = {key for _, _, key in work}
    if any(p.stem not in expected for p in (root / "shards").glob("*.sha256")):
        raise ValueError("Unexpected completed collection shard")
    records, newly_completed = [], 0
    for task, attack, key in work:
        record = store.read(key)
        if record is None:
            record = collect_record(protocol, task, labels[task.task_id], attack, key)
            bank_for([record], config, backend, synthetic=synthetic)  # Fail before publishing invalid data.
            store.put(key, record)
            newly_completed += 1
        if (record["row"]["row_id"] != key or record["row"]["task_id"] != task.task_id
                or record["row"]["label_hash"] != digest(labels[task.task_id])
                or canonical(record["trajectory"]["attack"]) != canonical(attack)
                or record["trajectory"]["snapshot"] != backend.identity["snapshot"]):
            raise ValueError("Completed shard provenance differs from scheduled training work")
        records.append(record)
        boundary()
        print(f"Training bank {len(records)}/{len(work)} {task.task_id}/{attack.channel}", flush=True)
        if stop_after is not None and newly_completed >= stop_after and len(records) < len(work):
            return records, False
    return records, True


def export_review(root, output, outcome):
    from .colab import review_bundle
    return review_bundle(root, output, outcome, kind="training_bank_engineering_review",
                         scientific_status=outcome.get("scientific_status", "train_only_collection_engineering"))


def run_collection(config, data_dir, reference_dir, root, cache_dir, *, resume=False, stop_after=None,
                   persistent=None, timeout_seconds=120):
    tasks, labels, data_manifest, runtime, plan = collection_plan(config, data_dir)
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive number of new records")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("Invalid persistence deadline")
    if persistent is not None:
        persistent = Path(persistent)
        if (root.absolute() == persistent.absolute() or root.absolute() in persistent.absolute().parents
                or persistent.absolute() in root.absolute().parents):
            raise ValueError("Persistent destination must be outside the scratch run")
    if root.exists() and not resume:
        raise ValueError("Collection path exists; use compatible resume or a new path")
    recipe = {"config": dataclasses.asdict(config), "source": code_identity(Path(__file__).resolve().parents[3]),
              "data_manifest_hash": digest(data_manifest)}
    old = read_json(root / "manifest.json") if resume else None
    if old and "identity" not in old:
        raise ValueError("Collection never initialized a model identity; use a new run path")
    if old and old["recipe_hash"] != digest(recipe):
        raise ValueError("Collection resume changed code/config/data before model load")
    verify_references(reference_dir, config)
    with run_lock(root):
        backend = None
        manifest = {"schema_version": 1, "kind": "training_bank_engineering", "recipe": recipe,
                    "recipe_hash": digest(recipe), "expected_records": 6, "status": "loading", "persistent_copy_verified": False}
        if old:
            manifest.update(identity=old["identity"])
        write_json(root / "manifest.json", manifest)
        write_json(root / "plan.json", plan)
        write_json(root / "data_manifest.json", data_manifest)
        write_json(root / "package_versions.json", versions())
        started = time.monotonic()
        result = {"exit_code": 0, "persistent_copy_verified": False, "persistent_snapshot": None,
                  "persistent_bundle": None, "scientific_status": "train_only_collection_engineering"}
        try:
            backend = CollectionBackend(runtime, cache_dir, reference_dir, config)
            synthetic = backend.identity.get("backend") == "mock"
            if synthetic:
                result["scientific_status"] = "synthetic_fixture"
            manifest["scientific_status"] = result["scientific_status"]
            identity = {"recipe_hash": digest(recipe), "actor": backend.identity["snapshot"],
                        "base": backend.base_identity["snapshot"], "runtime": backend.identity["runtime_fingerprint"],
                        "reference_manifest": config.reference_manifest_hash}
            if old and old["identity"] != identity:
                raise ValueError("Collection model/runtime resume mismatch")
            manifest.update(identity=identity, status="collecting")
            write_json(root / "manifest.json", manifest)
            write_json(root / "model_identity.json", {"actors": backend.identity, "base": backend.base_identity})
            def boundary():
                manifest["completed_records"] = len(list((root / "shards").glob("*.sha256")))
                write_json(root / "manifest.json", manifest)
                if persistent is not None:
                    snapshot = sync_run(root, persistent, timeout_seconds=timeout_seconds)
                    result["last_verified_snapshot"] = str(snapshot)
            records, complete = collect_records(config, tasks, labels, runtime, backend, root,
                                                 stop_after=stop_after, boundary=boundary, synthetic=synthetic)
            bank = bank_for(records, config, backend, synthetic=synthetic)
            # Only publish a complete immutable bank. Partial raw records remain resumable.
            if complete:
                preferences, scores = cache_reference_scores(bank, backend, root / "reference-cache", synthetic=synthetic)
                for name, value in (("bank.json", bank), ("preferences.json", preferences), ("reference_scores.json", scores)):
                    path = root / name
                    if path.exists() and canonical(read_json(path)) != canonical(value):
                        raise ValueError("Attempt to replace frozen collection output")
                    if not path.exists():
                        write_json(path, value)
                manifest.update(status="collection_complete_local", bank_hash=bank.identity,
                                pair_counts=preferences["pair_counts"], full_revision_ready=preferences["full_revision_ready"])
            else:
                manifest["status"] = "interrupted_at_record_boundary"
            backend.assert_unchanged()
            verify_references(reference_dir, config)
        except (Exception, KeyboardInterrupt) as exc:
            import traceback
            manifest.update(status="failed", failure={"type": type(exc).__name__, "message": redact(str(exc))})
            write_json(root / "failure.json", {"traceback": redact(traceback.format_exc())})
            result["exit_code"] = 2
        finally:
            manifest["invocation_seconds"] = time.monotonic()-started
            if backend is not None:
                resources = {**backend.resource_usage(),
                    "invocation_generation_calls": len(backend.calls), "invocation_teacher_forced_forwards": len(backend.scorer.forwards),
                    "teacher_forced_input_tokens": sum(len(s["prompt_ids"])+len(s["completion_ids"]) for s in backend.scorer.forwards),
                    "generation_input_tokens": sum(c.input_tokens for c in backend.calls),
                    "generation_output_tokens": sum(c.output_tokens for c in backend.calls),
                    "pending_call": getattr(backend, "pending_call", None),
                    "invocation_seconds": manifest["invocation_seconds"], "exit_code": result["exit_code"]}
                write_json(root / "resources.json", resources)
                write_json(root / "attempts" / f"{time.time_ns()}.json", resources)
            write_json(root / "manifest.json", manifest)
            # Local diagnostic ZIP precedes any final mounted-filesystem work.
            output = root.parent / "bundles" / f"{root.name}-review-{time.time_ns()}.zip"
            result.update(export_review(root, output, {**result, "status": manifest["status"]}))
            print(f"Local training bank ZIP: {output} SHA256: {result['sha256']}", flush=True)
        if result["exit_code"] == 0 and persistent is not None:
            try:
                snapshot = sync_run(root, persistent, timeout_seconds=timeout_seconds)
                result.update(persistent_copy_verified=True, persistent_snapshot=str(snapshot))
                output = root.parent / "bundles" / f"{root.name}-handoff-{time.time_ns()}.zip"
                result.update(export_review(root, output, {**result, "status": manifest["status"]}))
                target = persistent / "bundles" / output.name
                persist_bundle(output, target, result["sha256"], timeout_seconds=timeout_seconds)
                result["persistent_bundle"] = str(target)
            except (Exception, KeyboardInterrupt) as exc:
                result.update(exit_code=2, persistence_error=redact(str(exc)))
        return {**result, "status": manifest["status"], "completed_records": manifest.get("completed_records", 0),
                "training_executed": False, "scientific_status": "synthetic_fixture" if backend is not None and backend.identity.get("backend") == "mock" else "train_only_collection_engineering"}


def reference_cache_plan(config, bank):
    config.validate(); bank.validate()
    if (bank.data_manifest_hash != config.data_manifest_hash or len(bank.rows) != 6 or len(bank.receivers) > 18
            or tuple(r.adapter_hash for r in sorted(bank.warmstart_references, key=lambda r: r.agent)) != config.reference_hashes):
        raise ValueError("Bank does not belong to this bounded reference recipe")
    preferences = build_preferences(bank)
    return {"status": "reference_cache_plan_only", "bank_hash": bank.identity,
            "pair_counts": preferences["pair_counts"], "teacher_forced_forwards_upper_bound": 2*len(preferences["pairs"]),
            "training_executed": False, "reference_manifest_hash": config.reference_manifest_hash}


def run_reference_cache(config, bank, reference_dir, output_dir, cache_dir, *, resume=False):
    from .collection_config import CollectionRuntime
    plan = reference_cache_plan(config, bank)
    if output_dir.exists() and not resume:
        raise ValueError("Reference output exists; choose explicit resume or a new path")
    identity = {"config_hash": digest(config), "bank_hash": bank.identity,
                "source": code_identity(Path(__file__).resolve().parents[3])}
    if resume and read_json(output_dir / "identity.json") != identity:
        raise ValueError("Reference cache resume changed code/config/bank")
    with run_lock(output_dir):
        write_json(output_dir / "identity.json", identity)
        if plan["teacher_forced_forwards_upper_bound"] == 0:
            result = {**plan, "status": "no_eligible_preferences", "model_loaded": False, "scores": []}
        else:
            backend = CollectionBackend(CollectionRuntime(digest(config), config.seed), cache_dir, reference_dir, config)
            _, scores = cache_reference_scores(bank, backend, output_dir / "reference-cache")
            result = {**scores, "status": "reference_scores_complete", "training_executed": False,
                      "model_loaded": True, "new_reference_forwards": len(backend.scorer.forwards),
                      "resources": backend.resource_usage()}
        write_json(output_dir / "summary.json", result)
        return result


def restore_collection(snapshot, destination, *, timeout_seconds=120):
    from ..storage import storage_operation
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return storage_operation("collection-restore", Path(snapshot), destination, timeout_seconds=timeout_seconds)
