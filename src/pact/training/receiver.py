"""Frozen-actor receiver feasibility with immutable per-call recovery."""
from __future__ import annotations

from collections import Counter
import dataclasses as dc
import json
import math
from pathlib import Path
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..attacks import fixed_attack
from ..environment import code_identity, runtime_fingerprint, versions
from ..evaluation import aggregate, rate, score
from ..parsing import parse_answer
from ..protocol import Protocol
from ..schemas import CallRecord, Message
from ..storage import persist_bundle, storage_operation
from ..util import canonical, digest, file_hash, node_seed, read_json, redact, write_json
from .colab import review_bundle
from .collection_config import CollectionRuntime
from .data import read_training_data
from .receiver_plan import receiver_feasibility_plan
from .scoring import CollectionBackend, verify_references

KIND = "receiver_feasibility_diagnostic"
SCIENTIFIC_STATUS = "train_only_receiver_feasibility_diagnostic"


class CallBoundaryStop(Exception):
    """Requested pause before a new call; completed calls remain reusable."""


def call_from_dict(value):
    value = dict(value)
    value.pop("schema_version", None)
    value["messages"] = tuple(Message(m["role"], m["content"]) for m in value["messages"])
    return CallRecord(**value)


def inspect_journal(root, budget):
    """Never discard an incomplete result and silently regenerate its request."""
    root = Path(root)
    intents = {p.stem:read_json(p) for p in (root/"call-intents").glob("*.json")}
    store = ShardStore(root/"calls")
    files = list((root/"calls/shards").glob("*"))
    if any(p.suffix not in (".json", ".sha256") or p.stem not in intents for p in files):
        raise ValueError("Unknown receiver call artifact")
    results = {}
    for key, intent in intents.items():
        path = store.path(key)
        if (intent.get("work_id") != key or intent.get("schema_version") != 1
                or intent.get("max_tokens") not in (64, 256)):
            raise ValueError("Invalid call intent")
        if not path.exists() or not path.with_suffix(".sha256").exists():
            raise ValueError("Ambiguous attempted call; no automatic regeneration or budget reset")
        result = store.read(key)
        if result["intent"] != intent:
            raise ValueError("Call intent/result mismatch")
        results[key] = result
    if (len(intents) > budget["generation_calls_upper_bound"]
            or sum(i["max_tokens"] for i in intents.values()) > budget["generated_tokens_upper_bound"]):
        raise ValueError("Persisted attempted-call budget exceeded")
    return intents, results


class JournalBackend:
    """Protocol-compatible cache keyed by record and ordered logical call slot."""
    def __init__(self, backend, root, budget, *, stop_after=None, before_new=lambda:None):
        self.backend, self.root, self.budget = backend, Path(root), budget
        self.identity = backend.identity
        self.intents, self.results = inspect_journal(root, budget)
        self.store = ShardStore(self.root/"calls")
        self.stop_after, self.before_new = stop_after, before_new
        self.calls, self.seen, self.generation_tokens = [], set(), {}
        self.new_calls = 0

    def begin_record(self, key):
        self.record_key, self.slot = key, 0
        self.generation_tokens.clear()

    def count_tokens(self, text):
        return self.backend.count_tokens(text)

    def truncate(self, text, tokens):
        return self.backend.truncate(text, tokens)

    def generate(self, request):
        if (request.task.split != "train" or request.phase not in ("private", "revision", "final")
                or request.actor not in ("base", "agent-0", "agent-1", "agent-2")
                or request.max_tokens != (64 if request.phase == "final" else 256)
                or request.deterministic != (request.phase == "final")
                or (request.actor == "base") != (request.phase == "final")):
            raise ValueError("Receiver diagnostic request outside fixed design")
        key = digest([self.record_key, self.slot])
        self.slot += 1
        intent = {"schema_version":1, "work_id":key, "record_id":self.record_key,
                  "slot":self.slot-1, "request_hash":digest(request), "max_tokens":request.max_tokens}
        result = self.results.get(key)
        if result is None:
            if self.stop_after is not None and self.new_calls >= self.stop_after:
                raise CallBoundaryStop()
            if (len(self.intents)+1 > self.budget["generation_calls_upper_bound"]
                    or sum(i["max_tokens"] for i in self.intents.values())+request.max_tokens
                       > self.budget["generated_tokens_upper_bound"]):
                raise ValueError("Attempted-call/output reservation budget exhausted")
            self.before_new()
            write_json(self.root/"call-intents"/f"{key}.json", intent)
            self.intents[key] = intent
            raw, call = self.backend.generate(request)
            result = {"schema_version":1, "work_id":key, "intent":intent,
                      "raw":raw, "call":dc.asdict(call), "tokens":dict(self.backend.last_generation)}
            # Validate before publishing a marker; a failed check leaves the intent unresolved.
            self._validate(request, intent, result)
            self.store.put(key, result)
            self.results[key] = result
            self.new_calls += 1
            print(f"Receiver call {len(self.results)}/{self.budget['generation_calls_upper_bound']} "
                  f"{request.task.task_id}/{request.actor}/{request.phase}", flush=True)
        call = self._validate(request, intent, result)
        self.calls.append(call)
        self.seen.add(key)
        self.last_generation = result["tokens"]
        self.generation_tokens[digest(call)] = self.last_generation
        return result["raw"], call

    def _validate(self, request, intent, result):
        call = call_from_dict(result["call"]); tokens = result["tokens"]
        params = json.loads(call.parameters_json)
        if (result["intent"] != intent or call.messages != request.messages or call.seed != request.seed
                or call.actor != request.actor or call.phase != request.phase
                or call.snapshot != self.identity["snapshot"]
                or call.template_hash != self.identity["template_hash"]
                or call.context_hash != digest(call.rendered_prompt)
                or tokens["context_hash"] != call.context_hash or tokens["raw"] != result["raw"]
                or call.input_tokens != len(tokens["prompt_ids"])
                or call.output_tokens != len(tokens["completion_ids"])
                or not 0 <= call.output_tokens <= request.max_tokens
                or not math.isfinite(call.elapsed_seconds) or call.elapsed_seconds < 0
                or params["max_new_tokens"] != request.max_tokens
                or params["do_sample"] != (not request.deterministic)):
            raise ValueError("Receiver call provenance/token/length mismatch")
        if any(type(t) is not int or t < 0 for t in tokens["prompt_ids"]+tokens["completion_ids"]):
            raise ValueError("Invalid sampled token IDs")
        if not request.deterministic and any(params.get(k) != v for k,v in
                                           (("temperature",.7),("top_p",.8),("top_k",20))):
            raise ValueError("Receiver sampling changed")
        if call.stop_reason == "context_overflow":
            if call.output_tokens or result["raw"] or call.input_tokens+request.max_tokens <= 4096:
                raise ValueError("Inconsistent context-overflow result")
        elif call.input_tokens+request.max_tokens > 4096:
            raise ValueError("Call exceeded context budget")
        if call.stop_reason == "eos" and (not tokens["completion_ids"]
                or tokens["completion_ids"][-1] != self.backend.tokenizer.eos_token_id):
            raise ValueError("EOS completion is missing terminal EOS")
        if call.stop_reason not in ("eos", "length", "context_overflow"):
            raise ValueError("Unknown completion stop reason")
        return call


def collect_receiver_record(protocol, task, label, attack, key, partial_path):
    backend = protocol.backend
    trajectory = protocol.run(task, "debate", attack)
    evaluation = score(trajectory, label)
    record = {"schema_version":1, "work_id":key, "trajectory":dc.asdict(trajectory),
              "label":dc.asdict(label), "evaluation":evaluation, "receivers":[], "complete":False}
    for agent, original in enumerate(trajectory.revised):
        stratum = ("hold" if evaluation["initial"][agent] and evaluation["misleading"][agent]
                   else "repair" if not evaluation["initial"][agent] and evaluation["helpful"][agent]
                   else "ineligible_context")
        tokens = backend.generation_tokens[digest(original.call)]
        record["receivers"].append({"agent":agent, "stratum":stratum,
            "initial_parser_status":trajectory.private[agent].parser_status,
            "initial_correct":evaluation["initial"][agent],
            "prompt":original.call.rendered_prompt, "prompt_ids":tokens["prompt_ids"],
            "context_hash":original.call.context_hash, "candidates":[],
            "complete":stratum == "ineligible_context"})
    write_json(partial_path, record)
    for context in record["receivers"]:
        if context["stratum"] == "ineligible_context":
            continue
        agent = context["agent"]
        for index in range(4):
            packet = protocol.packet(task, agent, "revision", trajectory.revised[agent].call.messages,
                node_seed(protocol.config.seed, trajectory.trajectory_id, agent, "receiver", index))
            tokens = backend.generation_tokens[digest(packet.call)]
            if (packet.call.rendered_prompt != context["prompt"]
                    or tokens["prompt_ids"] != context["prompt_ids"]):
                raise ValueError("Receiver candidate changed original prompt or token prefix")
            context["candidates"].append({"raw":packet.raw, "call":dc.asdict(packet.call), "tokens":tokens})
            context["complete"] = len(context["candidates"]) == 4
            write_json(partial_path, record)
    record["complete"] = True
    return record


def receiver_report(plan, records, partial=None):
    expected = plan["budget"]["records"]
    observed = [*records, *([partial] if partial else [])]
    if len({r["work_id"] for r in observed}) != len(observed) or len(records) > expected:
        raise ValueError("Duplicate/excess receiver records")
    complete = len(records) == expected and partial is None
    contexts = []
    for record in observed:
        task = record["trajectory"]["task"]; gold = record["label"]["answer_id"]
        for context in record["receivers"]:
            candidates = context["candidates"]
            allowed = tuple(o["answer_id"] for o in task["options"])
            parsed = [parse_answer(c["raw"], allowed, stop_reason=c["call"]["stop_reason"]) for c in candidates]
            counts = Counter("correct" if answer == gold and status == "ok" else
                             "wrong" if status == "ok" else status for answer, _, status in parsed)
            positives = [i for i,p in enumerate(parsed) if p[2] == "ok" and p[0] == gold]
            negatives = [i for i,p in enumerate(parsed) if p[2] == "ok" and p[0] != gold]
            eligible = context["stratum"] != "ineligible_context"
            full = eligible and context["complete"] and len(candidates) == 4
            reason = ("ineligible_context" if not eligible else "incomplete_pool" if not full else
                      "missing_both" if not positives and not negatives else
                      "missing_correct" if not positives else "missing_incorrect" if not negatives else None)
            pair = None
            if reason is None:
                def rank(indices):
                    a,b = (len(candidates[i]["tokens"]["completion_ids"]) for i in indices)
                    return (a//32 != b//32, abs(a-b), *indices)
                p,n = min(((p,n) for p in positives for n in negatives), key=rank)
                pair = {"positive_index":p, "negative_index":n, "length_matched":not rank((p,n))[0]}
            contexts.append({"record_id":record["work_id"], "task_id":task["task_id"],
                "family":task["family"], "condition":record["trajectory"]["condition"],
                "agent":context["agent"], "stratum":context["stratum"],
                "initial_parser_status":context["initial_parser_status"],
                "initial_correct":context["initial_correct"], "context_hash":context["context_hash"],
                "candidate_count":len(candidates), "fully_sampled":full, "counts":dict(counts),
                "missing_reason":reason, "pair":pair})
    strata = {}
    for stratum in ("hold", "repair"):
        cohort = [c for c in contexts if c["stratum"] == stratum]
        pairs = [c for c in cohort if c["pair"]]
        tasks = sorted({c["task_id"] for c in pairs})
        families = sorted({c["family"] for c in pairs})
        gate = plan["decision_gate"]
        strata[stratum] = {"eligible_contexts_observed":len(cohort),
            "fully_sampled_contexts":sum(c["fully_sampled"] for c in cohort), "pairs":len(pairs),
            "pair_yield":rate(len(pairs),sum(c["fully_sampled"] for c in cohort)),
            "supporting_tasks":tasks, "supporting_families":families,
            "pairs_by_agent":{str(i):sum(c["agent"]==i for c in pairs) for i in range(3)},
            "pair_task_fraction":rate(len(tasks), plan["budget"]["tasks"]),
            "coverage_gate_passed":complete and len(pairs)>=gate["per_stratum_minimum_pairs"]
                and len(tasks)>=gate["per_stratum_minimum_distinct_tasks"]
                and set(families)>=set(gate["per_stratum_required_families"])}
    decision = ("incomplete" if not complete else
        "missing_eligible_stratum" if any(not s["eligible_contexts_observed"] for s in strata.values()) else
        "no_pairs" if all(not s["pairs"] for s in strata.values()) else
        "one_stratum_only" if any(not s["pairs"] for s in strata.values()) else
        "broader_support_observed" if all(s["coverage_gate_passed"] for s in strata.values()) else
        "limited_both_strata")
    grouped = []
    families = sorted({e["family"] for e in plan["selection"]["selected"]})
    for family in families:
        for condition in ("clean", "exchange"):
            for stratum in ("hold", "repair"):
                cohort = [c for c in contexts if (c["family"],c["condition"],c["stratum"]) == (family,condition,stratum)]
                paired = [c for c in cohort if c["pair"]]
                grouped.append({"family":family,"condition":condition,"stratum":stratum,
                    "eligible_contexts_observed":len(cohort),
                    "fully_sampled_contexts":sum(c["fully_sampled"] for c in cohort),
                    "pairs":len(paired),"supporting_tasks":sorted({c["task_id"] for c in paired}),
                    "pair_yield":rate(len(paired),sum(c["fully_sampled"] for c in cohort)),
                    "missing_reasons":dict(Counter(c["missing_reason"] for c in cohort if c["missing_reason"]))})
    evaluations = [r["evaluation"] for r in observed]
    by_task = {e["task_id"]:[] for e in plan["selection"]["selected"]}
    for evaluation in evaluations:
        by_task[evaluation["task_id"]].append(evaluation)
    return {"kind":KIND, "complete":complete, "completed_records":len(records),
        "expected_records":expected, "missing_records":expected-len(records),
        "contexts":contexts, "strata":strata, "by_family_condition":grouped, "decision":decision,
        "main_completed_records":len(evaluations),
        "ineligible_contexts":sum(c["stratum"]=="ineligible_context" for c in contexts),
        "unobserved_contexts":expected*3-len(contexts),
        "main_by_condition":{s:aggregate([e for e in evaluations if e["condition"]==s]) for s in ("clean","exchange")},
        "main_by_task":by_task, "training_executed":False, "training_pairs_exported":False,
        "full_pact_ready":False, "limitations":"training-only screen; candidates and repeated conditions are not independent tasks"}


def run_receiver(config, data_dir, warmstart_data_dir, selection_path, references_dir, root, cache_dir,
                 *, resume=False, stop_after=None, persistent=None, timeout_seconds=120):
    root = Path(root)
    plan = receiver_feasibility_plan(config, data_dir, warmstart_data_dir, selection_path)
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive number of new calls")
    if not 0 < timeout_seconds < float("inf"):
        raise ValueError("Invalid storage deadline")
    persistent = Path(persistent) if persistent is not None else None
    if persistent is not None and (root.absolute()==persistent.absolute()
            or root.absolute() in persistent.absolute().parents or persistent.absolute() in root.absolute().parents):
        raise ValueError("Persistent destination must be outside scratch run")
    tasks, labels, data_manifest, _ = read_training_data(Path(data_dir))
    tasks = {t.task_id:t for t in tasks}
    selected = [tasks[e["task_id"]] for e in plan["selection"]["selected"]]
    recipe = {"config":dc.asdict(config), "plan_hash":digest(plan),
              "source":code_identity(Path(__file__).resolve().parents[3])}
    old = read_json(root/"manifest.json") if resume else None
    if root.exists() and not resume:
        raise ValueError("Receiver run exists; use compatible resume")
    if old and (old["recipe_hash"] != digest(recipe) or "identity" not in old):
        raise ValueError("Receiver resume source/recipe mismatch or uninitialized model")
    if old:
        inspect_journal(root, plan["budget"])
    with run_lock(root):
        manifest = {"schema_version":1, "kind":KIND, "recipe":recipe, "recipe_hash":digest(recipe),
            "expected_records":plan["budget"]["records"], "completed_records":0, "status":"loading", "recovery_safe":True,
            "persistent_copy_verified":False}
        if old:
            manifest["identity"] = old["identity"]
        for name, value in (("plan.json",plan), ("data_manifest.json",data_manifest),
                            ("tasks.json",selected), ("labels.json",{t.task_id:labels[t.task_id] for t in selected}),
                            ("manifest.json",manifest), ("package_versions.json",versions())):
            write_json(root/name, value)
        backend = journal = None
        started = time.monotonic(); records = []
        result = {"exit_code":0, "persistent_copy_verified":False, "persistent_snapshot":None,
                  "persistent_bundle":None, "scientific_status":SCIENTIFIC_STATUS}
        try:
            if runtime_fingerprint() != config.runtime_fingerprint:
                raise ValueError("Receiver runtime fingerprint changed; no model downloaded")
            verify_references(references_dir, config)
            runtime = CollectionRuntime(digest(config), config.generation_seed)
            backend = CollectionBackend(runtime, Path(cache_dir), references_dir, config)
            if (backend.base_identity["snapshot"] != config.base_snapshot
                    or backend.identity["runtime_fingerprint"] != config.runtime_fingerprint):
                raise ValueError("Receiver model/runtime differs from pinned recipe")
            if backend.identity.get("backend") == "mock":
                result["scientific_status"] = "synthetic_fixture"
            identity = {"recipe_hash":digest(recipe), "actor":backend.identity["snapshot"],
                        "base":config.base_snapshot, "runtime":config.runtime_fingerprint}
            if old and old["identity"] != identity:
                raise ValueError("Receiver resume actor/model identity changed")
            manifest.update(identity=identity, status="collecting")
            write_json(root/"model_identity.json", {"actors":backend.identity,"base":backend.base_identity})
            def checkpoint():
                manifest["committed_calls"] = len(journal.results) if journal else 0
                write_json(root/"manifest.json",manifest)
                if persistent is not None:
                    result["last_verified_snapshot"] = str(sync_run(root,persistent,timeout_seconds=timeout_seconds))
            # A durable unsafe marker precedes each task's fresh calls. A reset may
            # not restore an older safe snapshot and quietly repeat lost work.
            def before_new():
                if manifest["recovery_safe"]:
                    manifest["recovery_safe"] = False
                    checkpoint()
            journal = JournalBackend(backend,root,plan["budget"],stop_after=stop_after,before_new=before_new)
            protocol = Protocol(runtime,journal); store = ShardStore(root)
            expected = set()
            for position, task in enumerate(selected):
                for condition in config.conditions:
                    attack = fixed_attack(task,labels[task.task_id],condition,position,config.generation_seed,journal,256)
                    key = digest([digest(config),task,attack,backend.identity["snapshot"]])
                    expected.add(key); journal.begin_record(key)
                    (root/"partial_record.json").unlink(missing_ok=True)
                    record = collect_receiver_record(protocol,task,labels[task.task_id],attack,key,root/"partial_record.json")
                    store.put(key,record); records.append(record)
                    (root/"partial_record.json").unlink(missing_ok=True)
                    manifest["completed_records"] = len(records)
                    print(f"Receiver records {len(records)}/{manifest['expected_records']} {task.task_id}/{condition}",flush=True)
                backend.assert_unchanged()
                if not manifest["recovery_safe"]:
                    manifest["recovery_safe"] = True; checkpoint()
            if {p.stem for p in (root/"shards").glob("*.json")} != expected or set(journal.results) != journal.seen:
                raise ValueError("Unexpected receiver record or unused cached call")
            verify_references(references_dir,config)
            if backend.scorer.forwards:
                raise ValueError("Receiver-only run performed forbidden scoring")
            manifest["status"] = "receiver_feasibility_complete_local"
        except CallBoundaryStop:
            manifest["status"] = "interrupted_at_call_boundary"
        except (Exception, KeyboardInterrupt) as exc:
            import traceback
            manifest.update(status="failed",failure={"type":type(exc).__name__,"message":redact(str(exc))})
            write_json(root/"failure.json",{"traceback":redact(traceback.format_exc())})
            result["exit_code"] = 2
        finally:
            # A handled pause has a complete call journal. Unknown attempts remain
            # explicitly unsafe even when we manage to export their diagnostics.
            try:
                intents, finished = inspect_journal(root,plan["budget"])
                manifest["recovery_safe"] = True
            except ValueError:
                intents = {p.stem:read_json(p) for p in (root/"call-intents").glob("*.json")}
                finished = {}
                for p in (root/"calls/shards").glob("*.sha256"):
                    try:
                        value = ShardStore(root/"calls").read(p.stem)
                        if value is not None:
                            finished[p.stem] = value
                    except ValueError:
                        pass
                manifest["recovery_safe"] = False
            try:
                records = ShardStore(root).records()
            except ValueError:
                # Keep the corrupted bytes for review; do not fabricate a complete report.
                records = []; result["exit_code"] = 2
                manifest.update(status="failed",recovery_safe=False)
            partial_path = root/"partial_record.json"
            partial = read_json(partial_path) if partial_path.exists() else None
            if partial and any(r["work_id"]==partial["work_id"] for r in records):
                partial = None
            report = receiver_report(plan,records,partial)
            if result["exit_code"]:
                report["complete"] = False; report["decision"] = "incomplete"
                for value in report["strata"].values():
                    value["coverage_gate_passed"] = False
            report["generation_accounting"] = {
                "attempted_calls":len(intents), "committed_calls":len(finished),
                "unresolved_attempts":len(intents)-len(finished),
                "input_tokens":sum(r["call"]["input_tokens"] for r in finished.values()),
                "output_tokens":sum(r["call"]["output_tokens"] for r in finished.values()),
                "stop_reasons":dict(Counter(r["call"]["stop_reason"] for r in finished.values())),
                "reserved_output_tokens":sum(i["max_tokens"] for i in intents.values())}
            name = "report.json" if report["complete"] else "partial_report.json"
            if (root/name).exists() and name == "report.json" and canonical(read_json(root/name)) != canonical(report):
                raise ValueError("Cannot replace completed receiver report")
            write_json(root/name,report)
            resources = {"invocation_seconds":time.monotonic()-started,"exit_code":result["exit_code"],
                "attempted_calls_total":len(intents),"committed_calls_total":len(finished),
                "reserved_output_tokens":sum(i["max_tokens"] for i in intents.values()),
                "new_calls":journal.new_calls if journal else 0, "training_executed":False,
                "teacher_forced_forwards":len(backend.scorer.forwards) if backend else 0}
            if backend:
                resources.update(backend.resource_usage(),generation_calls=len(backend.calls),
                    input_tokens=sum(c.input_tokens for c in backend.calls),
                    output_tokens=sum(c.output_tokens for c in backend.calls),pending_call=getattr(backend,"pending_call",None))
            resources["cache_hits"] = len(journal.seen)-journal.new_calls if journal else 0
            for name in ("resources.json",f"attempts/{time.time_ns()}.json"):
                write_json(root/name,resources)
            manifest.update(scientific_status=result["scientific_status"],completed_records=len(records),
                            committed_calls=len(finished))
            write_json(root/"manifest.json",manifest)
            output = root.parent/"bundles"/f"{root.name}-review-{time.time_ns()}.zip"
            result.update(review_bundle(root,output,{**result,"status":manifest["status"]},
                kind="receiver_feasibility_review",scientific_status=result["scientific_status"]))
            print(f"Local receiver ZIP: {output} SHA256: {result['sha256']}",flush=True)
        if persistent is not None and result["exit_code"] == 0:
            try:
                snapshot = sync_run(root,persistent,timeout_seconds=timeout_seconds)
                result.update(persistent_copy_verified=True,persistent_snapshot=str(snapshot))
                output = root.parent/"bundles"/f"{root.name}-handoff-{time.time_ns()}.zip"
                result.update(review_bundle(root,output,{**result,"status":manifest["status"]},
                    kind="receiver_feasibility_review",scientific_status=result["scientific_status"]))
                target = persistent/"bundles"/output.name
                persist_bundle(output,target,result["sha256"],timeout_seconds=timeout_seconds)
                result["persistent_bundle"] = str(target)
            except (Exception,KeyboardInterrupt) as exc:
                result.update(exit_code=2,persistence_error=redact(str(exc)))
        return {**result,"status":manifest["status"],"completed_records":manifest["completed_records"],
                "committed_calls":manifest["committed_calls"],"training_executed":False}


def restore_receiver(snapshot,destination,*,timeout_seconds=120):
    destination = Path(destination); destination.parent.mkdir(parents=True,exist_ok=True)
    return storage_operation("receiver-restore",Path(snapshot),destination,timeout_seconds=timeout_seconds)


def read_receiver_review(bundle, expected_sha):
    from .feasibility import read_review
    # Up to 912 call JSONs + intents + 48 records, with the same 100 MiB bound.
    result = read_review(bundle,expected_sha,max_members=3000)
    if result["HANDOFF.json"]["kind"] != "receiver_feasibility_review":
        raise ValueError("Not a receiver-feasibility review archive")
    return result
