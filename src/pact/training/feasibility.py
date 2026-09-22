"""Matched base-model diagnosis on frozen training contexts; never training pairs."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import time
import zipfile
from collections import Counter

from ..artifacts import ShardStore, run_lock, safe_relative, sync_run
from ..backends import Request
from ..backends.transformers import TransformersBackend
from ..environment import code_identity, versions
from ..parsing import parse_answer
from ..schemas import Message, task_from_dict
from ..storage import persist_bundle, storage_operation
from ..util import canonical, digest, file_hash, read_json, redact, write_json
from .bank import bank_from_dict, sha
from .collection_config import CollectionRuntime
from .colab import review_bundle
from .preferences import build_preferences


@dataclasses.dataclass(frozen=True)
class FeasibilityConfig:
    source_bundle_sha256: str
    source_bank_hash: str
    schema_version: int = 1
    purpose: str = "train_only_frozen_context_base_control"

    def validate(self):
        sha(self.source_bundle_sha256); sha(self.source_bank_hash)
        if type(self.schema_version) is not int or self.schema_version != 1 or self.purpose != "train_only_frozen_context_base_control":
            raise ValueError("Unsupported diagnostic recipe")
        return self


def load_feasibility_config(path):
    return FeasibilityConfig(**read_json(Path(path))).validate()


def copy_source_bundle(source,destination,config,*,timeout_seconds=120):
    """Timed Drive-to-scratch copy, with worker control files on scratch."""
    config.validate();destination=Path(destination)
    if destination.exists():
        read_review(destination,config.source_bundle_sha256)
        return {"path":str(destination),"sha256":config.source_bundle_sha256,"reused":True}
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".pact-source-",dir=destination.parent) as temp:
        staged=Path(temp)/"source.zip"
        result=storage_operation("bundle-restore",Path(source),staged,
            timeout_seconds=timeout_seconds,sha256=config.source_bundle_sha256)
        read_review(staged,config.source_bundle_sha256)
        staged.replace(destination)
    return {**result,"path":str(destination)}


def read_review(bundle, expected_sha, *, max_members=1000, max_bytes=100*1024**2, allow_text=False):
    """Read checksummed JSON as data, with no extraction or imported execution."""
    bundle = Path(bundle)
    if bundle.is_symlink() or bundle.stat().st_size > max_bytes or file_hash(bundle) != expected_sha:
        raise ValueError("Diagnostic source ZIP hash/size mismatch")
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        if len(infos) > max_members or sum(i.file_size for i in infos) > max_bytes:
            raise ValueError("Review archive exceeds bounds")
        names = set()
        for item in infos:
            safe_relative(item.filename)
            if item.filename in names or item.is_dir() or stat.S_IFMT(item.external_attr >> 16) not in (0, stat.S_IFREG):
                raise ValueError("Duplicate or nonregular review member")
            names.add(item.filename)
        checks = json.loads(archive.read("review_checksums.json"))
        if set(checks) != names - {"review_checksums.json"}:
            raise ValueError("Review checksum inventory mismatch")
        content = {}
        for name in sorted(checks):
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != checks[name]:
                raise ValueError("Corrupt review payload")
            if allow_text and name.endswith((".md", ".txt", ".jsonl")):
                content[name] = payload.decode("utf-8")
                continue
            if not name.endswith(".json"):
                raise ValueError("Diagnostic source expects JSON-only review metadata")
            content[name] = json.loads(payload)
    return content


def prepare_feasibility(config, bundle):
    config.validate()
    source = read_review(bundle, config.source_bundle_sha256)
    handoff, manifest = source["HANDOFF.json"], source["manifest.json"]
    bank = bank_from_dict(source["bank.json"])
    if (handoff["kind"] != "training_bank_engineering_review"
            or manifest["status"] != "collection_complete_local" or manifest["completed_records"] != 6
            or len(bank.rows) != 6 or bank.identity != config.source_bank_hash or manifest["bank_hash"] != bank.identity):
        raise ValueError("Diagnostic requires the pinned complete training bank")
    preferences = build_preferences(bank)
    if canonical(preferences) != canonical(source["preferences.json"]) or preferences["pairs"]:
        raise ValueError("This diagnostic is pinned to an empty-preference bank")
    models = source["model_identity.json"]
    if (bank.base_snapshot != models["base"]["snapshot"] or bank.actor_snapshot != models["actors"]["snapshot"]
            or bank.runtime_fingerprint != models["base"]["runtime_fingerprint"]
            or manifest["recipe"]["data_manifest_hash"] != bank.data_manifest_hash):
        raise ValueError("Source model/data identity mismatch")
    records = {r["work_id"]:r for n,r in source.items() if n.startswith("shards/") and n.endswith(".json")}
    if set(records) != {r.row_id for r in bank.rows}:
        raise ValueError("Source raw shards do not cover the bank")
    requests, context_groups = [], []
    def add(row, record, agent, phase, stratum, candidates):
        group = digest([row.row_id, agent, phase])
        context_groups.append({"group_id":group, "row_id":row.row_id, "task_id":row.task_id,
            "condition":record["trajectory"]["condition"], "agent":agent, "phase":phase,
            "stratum":stratum, "candidate_count":len(candidates)})
        prompt = candidates[0]["call"]["rendered_prompt"]
        prefix = record["generation_tokens"][digest(candidates[0]["call"])]["prompt_ids"]
        for index, packet in enumerate(candidates):
            call = packet["call"]; tokens = record["generation_tokens"][digest(call)]
            params = json.loads(call["parameters_json"])
            if (call["phase"] != phase or call["actor"] != f"agent-{agent}" or call["rendered_prompt"] != prompt
                    or tokens["prompt_ids"] != prefix or tokens["raw"] != packet["raw"]
                    or call["context_hash"] != digest(prompt) or call["snapshot"] != bank.actor_snapshot
                    or call["template_hash"] != bank.template_hash or params["do_sample"] is not True
                    or params["max_new_tokens"] != 256 or any(params[k] != v for k,v in
                       (("temperature",.7),("top_p",.8),("top_k",20)))
                    or call["input_tokens"]+256 > 4096):
                raise ValueError("Source context/sampling differs from matched-control contract")
            item = {"group_id":group,"row_id":row.row_id,"phase":phase,"agent":agent,"index":index,
                "source_call_hash":digest(call),"task":record["trajectory"]["task"],
                "messages":call["messages"],"prompt":prompt,"prompt_ids":prefix,"seed":call["seed"],
                "actor_raw":packet["raw"],"actor_stop_reason":call["stop_reason"],
                "actor_completion_ids":tokens["completion_ids"],"gold":row.gold,
                "stratum":stratum,"condition":record["trajectory"]["condition"]}
            item["request_id"] = digest(item)
            requests.append(item)
    for row in bank.rows:
        record = records[row.row_id]
        task = task_from_dict(record["trajectory"]["task"])
        if (canonical(record["row"]) != canonical(row) or task.split != "train"
                or task.task_id != row.task_id or task.source_hash != row.source_hash):
            raise ValueError("Raw training record provenance mismatch")
        if record["trajectory"]["condition"] == "clean":
            for agent in range(3):
                add(row,record,agent,"private","private_control",
                    [record["trajectory"]["private"][agent], *record["replays"][agent]["candidates"]])
        for context in (c for c in preferences["contexts"] if c["row_id"] == row.row_id and c["stratum"] in ("hold","repair")):
            agent = context["agent"]
            add(row,record,agent,"revision",context["stratum"],record["receiver_probes"][agent]["candidates"])
    counts = dict(Counter(i["phase"] for i in requests))
    if (len({r.task_id for r in bank.rows}) != 2 or counts != {"private":30,"revision":24}
            or len({i["request_id"] for i in requests}) != 54
            or Counter(g["stratum"] for g in context_groups) != {"private_control":6,"hold":2,"repair":4}
            or any(g["candidate_count"] != (5 if g["phase"]=="private" else 4) for g in context_groups)):
        raise ValueError("Source does not match the fixed 54-call control design")
    summary = {"status":"preference_diagnostic_plan_only","scientific_status":"train_only_fixed_context_base_control",
        "training_executed":False,"gpu_diagnostic_verified":False,"config_hash":digest(config),
        "source_bank_hash":bank.identity,"source_bundle_sha256":config.source_bundle_sha256,
        "requests_hash":digest(requests),"fresh_base_calls":54,"reused_actor_calls":54,
        "generated_tokens_upper_bound":54*256,"context_limit":4096,"private_calls":30,"receiver_calls":24,
        "receiver_contexts":{"hold":2,"repair":4},"seed_policy":"reuse recorded actor call seeds",
        "selection":"all eligible original receivers; both clean tasks, all initial/private alternative calls",
        "source_pair_counts":preferences["pair_counts"],"scope":"diagnostic only; no training-pair export or actor resampling"}
    return {"summary":summary,"groups":context_groups,"requests":requests,"models":models,
            "config":dataclasses.asdict(config)}


def diagnose(plan, records):
    """Report fixed-context outcomes separately; never merge actor/base pools."""
    indexed = {r["request_id"]:r for r in records}
    if len(indexed) != len(records) or set(indexed)-{i["request_id"] for i in plan["requests"]}:
        raise ValueError("Unknown or repeated diagnostic output")
    groups, transitions = [], Counter()
    for group in plan["groups"]:
        items = [i for i in plan["requests"] if i["group_id"]==group["group_id"]]
        outcomes = {"actor":Counter(),"base":Counter()}
        for item in items:
            allowed = tuple(o["answer_id"] for o in item["task"]["options"])
            def outcome(raw, stop):
                answer,_,status = parse_answer(raw,allowed,stop_reason=stop)
                return "correct" if status=="ok" and answer==item["gold"] else "wrong" if status=="ok" else status
            actor = outcome(item["actor_raw"],item["actor_stop_reason"])
            outcomes["actor"][actor] += 1
            if item["request_id"] in indexed:
                result = indexed[item["request_id"]]
                base = outcome(result["raw"],result["call"]["stop_reason"])
                outcomes["base"][base] += 1
                transitions[f"{actor}->{base}"] += 1
        complete = sum(outcomes["base"].values()) == len(items)
        groups.append({**group,"complete":complete,"counts":{k:dict(v) for k,v in outcomes.items()},
            "actor_pair_available":group["phase"]=="revision" and bool(outcomes["actor"]["correct"] and outcomes["actor"]["wrong"]),
            "base_pair_available":group["phase"]=="revision" and complete and bool(outcomes["base"]["correct"] and outcomes["base"]["wrong"])})
    return {"kind":"preference_feasibility_diagnostic","training_executed":False,"training_pairs_exported":False,
        "source_bank_hash":plan["summary"]["source_bank_hash"],"completed":len(records),"expected":54,
        "groups":groups,"paired_outcome_counts":dict(transitions),
        "base_receiver_pair_contexts":{s:sum(g["stratum"]==s and g["base_pair_available"] for g in groups) for s in ("hold","repair")},
        "limitation":"base on actor-produced fixed contexts; not an independently generated base team or a trained-policy preference bank"}


def collect_control(plan, backend, root, *, stop_after=None, boundary=lambda:None):
    store = ShardStore(Path(root)); expected = {i["request_id"] for i in plan["requests"]}
    if any(p.stem not in expected for p in (Path(root)/"shards").glob("*.sha256")):
        raise ValueError("Unexpected diagnostic shard")
    records, new = [], 0
    for item in plan["requests"]:
        key = item["request_id"]; result = store.read(key)
        if result is None:
            # Labels, original outcomes and stratum never enter the model request.
            request = Request(task_from_dict(item["task"]),tuple(Message(m["role"],m["content"]) for m in item["messages"]),
                              "base",item["phase"],item["seed"],256,False)
            raw,call = backend.generate(request); tokens = backend.last_generation
            if (call.actor != "base" or call.rendered_prompt != item["prompt"] or call.seed != item["seed"]
                    or tokens["prompt_ids"] != item["prompt_ids"] or tokens["raw"] != raw
                    or call.snapshot != plan["models"]["base"]["snapshot"]):
                raise ValueError("Base control changed the frozen prompt/token/seed/model identity")
            result = {"schema_version":1,"work_id":key,"request_id":key,"request_hash":digest(item),
                      "raw":raw,"call":dataclasses.asdict(call),"tokens":tokens}
            store.put(key,result); new += 1
        if result["request_hash"] != digest(item):
            raise ValueError("Diagnostic shard request mismatch")
        records.append(result); boundary()
        print(f"Base control {len(records)}/54 {item['task']['task_id']}/{item['phase']}",flush=True)
        if stop_after is not None and new >= stop_after and len(records)<54:break
    return records


def run_feasibility(config,bundle,root,cache_dir,*,resume=False,stop_after=None,persistent=None,timeout_seconds=120):
    root = Path(root); plan = prepare_feasibility(config,bundle)
    if stop_after is not None and (type(stop_after) is not int or stop_after<1):
        raise ValueError("stop_after must be a positive number of new calls")
    if not 0 < timeout_seconds < float("inf"):raise ValueError("Invalid storage deadline")
    if persistent is not None:
        persistent = Path(persistent)
        # Lexical check only: mounted-path filesystem reads belong in timed workers.
        if root.absolute()==persistent.absolute() or root.absolute() in persistent.absolute().parents or persistent.absolute() in root.absolute().parents:
            raise ValueError("Persistent destination must be outside the scratch run")
    recipe = {"config":dataclasses.asdict(config),"plan_hash":digest(plan),"source":code_identity(Path(__file__).resolve().parents[3])}
    old = read_json(root/"manifest.json") if resume else None
    if root.exists() and not resume:raise ValueError("Diagnostic run exists; use compatible resume or a new path")
    if old and (old["recipe_hash"]!=digest(recipe) or "identity" not in old):
        raise ValueError("Diagnostic resume source/recipe mismatch or uninitialized model")
    with run_lock(root):
        manifest = {"schema_version":1,"kind":"preference_feasibility_diagnostic","recipe":recipe,"recipe_hash":digest(recipe),
            "status":"loading","completed_records":0,"expected_records":54,"persistent_copy_verified":False}
        if old:manifest["identity"]=old["identity"]
        write_json(root/"plan.json",plan);write_json(root/"manifest.json",manifest)
        write_json(root/"package_versions.json",versions())
        backend=None;started=time.monotonic()
        result={"exit_code":0,"persistent_copy_verified":False,"persistent_snapshot":None,"persistent_bundle":None,
                "scientific_status":"train_only_fixed_context_base_control"}
        try:
            backend=TransformersBackend(CollectionRuntime(digest(config),1729),Path(cache_dir))
            expected=plan["models"]["base"]
            if (backend.identity["snapshot"]!=expected["snapshot"] or backend.identity["runtime_fingerprint"]!=expected["runtime_fingerprint"]
                    or backend.identity.get("adapters")):
                raise ValueError("Matched base control requires the original model/runtime and no adapters")
            identity={"recipe_hash":digest(recipe),"base":expected["snapshot"],"runtime":expected["runtime_fingerprint"]}
            if old and old["identity"]!=identity:raise ValueError("Diagnostic runtime resume mismatch")
            manifest.update(identity=identity,status="collecting")
            if backend.identity.get("backend")=="mock":result["scientific_status"]="synthetic_fixture"
            write_json(root/"model_identity.json",backend.identity)
            def boundary():
                count=len(list((root/"shards").glob("*.sha256")))
                manifest["completed_records"]=count;write_json(root/"manifest.json",manifest)
                if persistent is not None and count%6==0 and count<54:
                    result["last_verified_snapshot"]=str(sync_run(root,persistent,timeout_seconds=timeout_seconds))
            records=collect_control(plan,backend,root,stop_after=stop_after,boundary=boundary)
            report=diagnose(plan,records)
            complete=len(records)==54
            report_name="report.json" if complete else "partial_report.json"
            if complete and (root/report_name).exists() and canonical(read_json(root/report_name))!=canonical(report):
                raise ValueError("Cannot replace completed diagnostic report")
            write_json(root/report_name,report)
            manifest["status"]="diagnostic_complete_local" if complete else "interrupted_at_call_boundary"
        except (Exception,KeyboardInterrupt) as exc:
            import traceback
            manifest.update(status="failed",failure={"type":type(exc).__name__,"message":redact(str(exc))})
            write_json(root/"failure.json",{"traceback":redact(traceback.format_exc())});result["exit_code"]=2
        finally:
            resources={"invocation_seconds":time.monotonic()-started,"exit_code":result["exit_code"]}
            if backend is not None:
                resources.update(backend.resource_usage(),generation_calls=len(backend.calls),
                    input_tokens=sum(c.input_tokens for c in backend.calls),output_tokens=sum(c.output_tokens for c in backend.calls),
                    pending_call=getattr(backend,"pending_call",None))
            write_json(root/"resources.json",resources);write_json(root/"attempts"/f"{time.time_ns()}.json",resources)
            manifest["scientific_status"]=result["scientific_status"];write_json(root/"manifest.json",manifest)
            output=root.parent/"bundles"/f"{root.name}-review-{time.time_ns()}.zip"
            result.update(review_bundle(root,output,{**result,"status":manifest["status"]},kind="preference_feasibility_diagnostic_review",
                                        scientific_status=result["scientific_status"]))
            print(f"Local base-control ZIP: {output} SHA256: {result['sha256']}",flush=True)
        if result["exit_code"]==0 and persistent is not None:
            try:
                snapshot=sync_run(root,persistent,timeout_seconds=timeout_seconds)
                result.update(persistent_copy_verified=True,persistent_snapshot=str(snapshot))
                output=root.parent/"bundles"/f"{root.name}-handoff-{time.time_ns()}.zip"
                result.update(review_bundle(root,output,{**result,"status":manifest["status"]},kind="preference_feasibility_diagnostic_review",
                                            scientific_status=result["scientific_status"]))
                target=persistent/"bundles"/output.name
                persist_bundle(output,target,result["sha256"],timeout_seconds=timeout_seconds);result["persistent_bundle"]=str(target)
            except (Exception,KeyboardInterrupt) as exc:result.update(exit_code=2,persistence_error=redact(str(exc)))
        return {**result,"status":manifest["status"],"completed_records":manifest["completed_records"],"training_executed":False}


def restore_feasibility(snapshot,destination,*,timeout_seconds=120):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    return storage_operation("feasibility-restore",Path(snapshot),destination,timeout_seconds=timeout_seconds)
