from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from .artifacts import export_bundle, import_bundle, restore_run, sync_run
from .config import budget, load_config
from .datasets import prepare
from .environment import doctor
from .reporting import report
from .runner import inspect_run, run
from .util import canonical, write_json


def parser():
    p = argparse.ArgumentParser(prog="pact", description="PACT validation diagnostics and local learning foundations")
    commands = p.add_subparsers(dest="command", required=True)
    d = commands.add_parser("doctor")
    d.add_argument("--scratch", type=Path, default=Path("scratch"))
    d.add_argument("--persistent", type=Path)
    d.add_argument("--config", type=Path)
    v = commands.add_parser("validate-config")
    v.add_argument("--config", required=True, type=Path)
    data = commands.add_parser("prepare-data")
    data.add_argument("--config", required=True, type=Path)
    data.add_argument("--scratch", type=Path, default=Path("scratch"))
    data = commands.add_parser("prepare-training-data", help="freeze train-only tasks after full validation overlap screening")
    data.add_argument("--cache-dir", required=True, type=Path)
    data.add_argument("--output-dir", required=True, type=Path)
    data.add_argument("--items", required=True, type=int)
    data.add_argument("--seed", required=True, type=int)
    data.add_argument("--download", action="store_true", help="explicitly fetch missing pinned train/validation sources")
    data = commands.add_parser("inspect-training-data")
    data.add_argument("--data-dir", required=True, type=Path)
    for name in ("smoke", "profile", "pilot"):
        r = commands.add_parser(name)
        r.add_argument("--config", required=True, type=Path)
        r.add_argument("--run-id", default="local-smoke" if name == "smoke" else None, required=name != "smoke")
        r.add_argument("--scratch", type=Path, default=Path("scratch"))
        r.add_argument("--persistent", type=Path)
        r.add_argument("--resume", action="store_true")
        r.add_argument("--dry-run", action="store_true")
        r.add_argument("--stop-after", type=int, help="Simulate interruption after N newly completed records")
    for name in ("inspect-run", "report", "export-bundle", "sync"):
        r = commands.add_parser(name)
        r.add_argument("--run-dir", required=True, type=Path)
        if name == "export-bundle":
            r.add_argument("--output", required=True, type=Path)
        elif name == "sync":
            r.add_argument("--destination", required=True, type=Path)
    r = commands.add_parser("import-bundle")
    r.add_argument("--bundle", required=True, type=Path)
    r.add_argument("--destination", required=True, type=Path)
    r = commands.add_parser("restore")
    r.add_argument("--source", required=True, type=Path)
    r.add_argument("--run-dir", required=True, type=Path)
    r = commands.add_parser("training-check", help="synthetic CPU foundations check; no model training")
    r.add_argument("--output-dir", required=True, type=Path)
    r = commands.add_parser("warmstart", help="plan bounded clean-answer training; --execute opts into GPU/model use")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--data-dir", required=True, type=Path)
    r.add_argument("--run-dir", required=True, type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int, help="interrupt after N newly committed optimizer updates")
    for name in ("assign", "build-preferences"):
        r = commands.add_parser(name, help="process an explicit scored training bank")
        r.add_argument("--bank", required=True, type=Path)
        r.add_argument("--output", required=True, type=Path)
        r.add_argument("--allow-synthetic", action="store_true")
        if name == "assign":
            r.add_argument("--nll-mode", choices=("raw", "standardized"), default="standardized")
            r.add_argument("--gamma", type=float, default=1.0)
            r.add_argument("--tau", type=float, default=0.2)
            r.add_argument("--balance", type=float, default=0.1)
    for name in ("collect-bank", "cache-reference"):
        r = commands.add_parser(name, help="bounded train-only engineering stage; default plan, --execute loads model")
        r.add_argument("--config", required=True, type=Path)
        r.add_argument("--references-dir", required=True, type=Path)
        r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
        r.add_argument("--execute", action="store_true")
        r.add_argument("--resume", action="store_true")
        if name == "collect-bank":
            r.add_argument("--data-dir", required=True, type=Path)
            r.add_argument("--run-dir", required=True, type=Path)
            r.add_argument("--persistent", type=Path)
            r.add_argument("--storage-timeout", type=float, default=120)
            r.add_argument("--stop-after", type=int)
        else:
            r.add_argument("--bank", required=True, type=Path)
            r.add_argument("--output-dir", required=True, type=Path)
    r = commands.add_parser("plan-receiver-feasibility", help="verify frozen broader training-only design; no execution")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--data-dir", required=True, type=Path)
    r.add_argument("--warmstart-data-dir", required=True, type=Path)
    r.add_argument("--selection", required=True, type=Path)
    r = commands.add_parser("actor-preparation", help="bounded 120-task preparation/probe; default plan only")
    for name in ("config", "data-dir", "warmstart-data-dir", "receiver-bundle", "private-bundle", "curated-bundle", "run-dir", "persistent"):
        r.add_argument("--"+name, required=True, type=Path)
    r.add_argument("--stage", choices=("training", "probe"), required=True)
    r.add_argument("--training-root", type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--storage-timeout", type=float, default=120)
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int)
    r = commands.add_parser("plan-actor-preparation", help="freeze 120-task preparation design; no execution")
    for name in ("config", "data-dir", "warmstart-data-dir", "receiver-bundle", "private-bundle", "curated-bundle"):
        r.add_argument("--"+name, required=True, type=Path)
    r = commands.add_parser("plan-curated-repair", help="verify fixed curated helpful-peer design; no execution")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--receiver-bundle", required=True, type=Path)
    r.add_argument("--private-bundle", required=True, type=Path)
    r = commands.add_parser("curated-repair", help="fixed 32-call helpful-peer diagnostic; default plan only")
    for name in ("config", "receiver-bundle", "private-bundle", "references-dir", "run-dir"):
        r.add_argument("--"+name, required=True, type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--persistent", type=Path)
    r.add_argument("--storage-timeout", type=float, default=120)
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int)
    r = commands.add_parser("private-support-control", help="one additional private draw; default plan only")
    for name in ("config", "bundle", "references-dir", "run-dir"):
        r.add_argument("--"+name, required=True, type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--persistent", type=Path)
    r.add_argument("--storage-timeout", type=float, default=120)
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int)
    r = commands.add_parser("receiver-feasibility", help="bounded frozen-actor receiver diagnostic; default plan only")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--data-dir", required=True, type=Path)
    r.add_argument("--warmstart-data-dir", required=True, type=Path)
    r.add_argument("--selection", required=True, type=Path)
    r.add_argument("--references-dir", required=True, type=Path)
    r.add_argument("--run-dir", required=True, type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--persistent", type=Path)
    r.add_argument("--storage-timeout", type=float, default=120)
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int, help="pause before more than N new committed calls")
    r = commands.add_parser("preference-diagnostic", help="matched base control on frozen training contexts; default plan only")
    r.add_argument("--config", required=True, type=Path)
    r.add_argument("--bundle", required=True, type=Path)
    r.add_argument("--run-dir", required=True, type=Path)
    r.add_argument("--cache-dir", type=Path, default=Path("scratch/cache/models"))
    r.add_argument("--persistent", type=Path)
    r.add_argument("--storage-timeout", type=float, default=120)
    r.add_argument("--execute", action="store_true")
    r.add_argument("--resume", action="store_true")
    r.add_argument("--stop-after", type=int)
    for name in ("train", "adaptive-evaluate", "evaluate"):
        commands.add_parser(name, help="not_implemented: deferred milestone")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        command = args.command
        if command == "doctor":
            result = doctor(args.scratch, args.persistent, load_config(args.config) if args.config else None)
            print(canonical(result))
            return int(bool(result["errors"]))
        if command == "validate-config":
            config = load_config(args.config)
            result = {"valid": True, "config_hash": config.identity, "resolved_config": dataclasses.asdict(config), "budget": budget(config)}
        elif command == "prepare-data":
            config = load_config(args.config)
            _, _, result = prepare(config, args.scratch / "cache" / "datasets")
            write_json(args.scratch / "prepared" / f"{config.identity}.json", result)
        elif command == "prepare-training-data":
            from .training.data import prepare_training_data
            result = prepare_training_data(args.cache_dir, args.output_dir, items=args.items, seed=args.seed, download=args.download)
        elif command == "inspect-training-data":
            from .training.data import read_training_data
            from .util import digest
            tasks, labels, manifest, audit = read_training_data(args.data_dir)
            result = {"status": "verified_training_data_no_model_training", "manifest_hash": digest(manifest),
                      "realized": len(tasks), "family_counts": manifest["family_counts"],
                      "excluded_rows": len(audit["exclusions"])}
        elif command in ("smoke", "profile", "pilot"):
            config = load_config(args.config)
            if config.stage != command:
                raise ValueError("CLI stage must match the declared configuration stage")
            print(canonical({"resolved_config": dataclasses.asdict(config), "budget": budget(config)}), flush=True)
            if args.dry_run:
                return 0
            if args.stop_after is not None and args.stop_after <= 0:
                raise ValueError("--stop-after must be positive")
            root = run(config, run_id=args.run_id, scratch=args.scratch, persistent=args.persistent,
                       resume=args.resume, stop_after=args.stop_after,
                       invocation=tuple(["python", "-m", "pact", *(argv if argv is not None else sys.argv[1:])]))
            result = inspect_run(root)
            result["run_dir"] = str(root)
        elif command == "inspect-run":
            result = inspect_run(args.run_dir)
        elif command == "report":
            metrics = report(args.run_dir)
            output_dir = args.run_dir / "analysis" if not (args.run_dir / "shards").exists() and (args.run_dir / "checksums.json").exists() else args.run_dir
            result = {"metrics": str(output_dir / "metrics.json"), "status": metrics["status"], "missing_records": metrics["missing_records"]}
        elif command == "export-bundle":
            report(args.run_dir)
            result = export_bundle(args.run_dir, args.output)
        elif command == "import-bundle":
            result = import_bundle(args.bundle, args.destination)
        elif command == "sync":
            result = {"verified_snapshot": str(sync_run(args.run_dir, args.destination))}
        elif command == "restore":
            result = restore_run(args.source, args.run_dir)
        elif command == "training-check":
            from .training.checks import training_check
            result = training_check(args.output_dir)
        elif command == "warmstart":
            from .training.warmstart_config import load_warmstart_config, warmstart_plan
            config = load_warmstart_config(args.config)
            if args.stop_after is not None and args.stop_after < 1:
                raise ValueError("--stop-after must be positive")
            if args.execute:
                from .training.warmstart import run_warmstart
                result = run_warmstart(config, args.data_dir, args.run_dir, args.cache_dir,
                                       resume=args.resume, stop_after=args.stop_after)
            else:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = warmstart_plan(config, args.data_dir)[3]
        elif command == "collect-bank":
            from .training.collection_config import load_collection_config, collection_plan
            config = load_collection_config(args.config)
            if not args.execute:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = collection_plan(config, args.data_dir)[4]
            else:
                from .training.collection import run_collection
                result = run_collection(config, args.data_dir, args.references_dir, args.run_dir, args.cache_dir,
                            resume=args.resume, stop_after=args.stop_after, persistent=args.persistent,
                            timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "plan-receiver-feasibility":
            from .training.receiver_plan import load_receiver_config, receiver_feasibility_plan
            result = receiver_feasibility_plan(load_receiver_config(args.config), args.data_dir,
                                               args.warmstart_data_dir, args.selection)
        elif command == "actor-preparation":
            from .training.actor_preparation import load_actor_preparation_config, actor_preparation_plan
            config = load_actor_preparation_config(args.config)
            result = actor_preparation_plan(config,args.data_dir,args.warmstart_data_dir,
                args.receiver_bundle,args.private_bundle,args.curated_bundle)
            if not args.execute:
                if args.resume or args.stop_after is not None:raise ValueError("Resume/stop-after require --execute")
            else:
                if args.stage == "training":
                    from .training.preparation_runner import run_preparation_training
                    result = run_preparation_training(result,args.run_dir,args.cache_dir,persistent=args.persistent,
                        resume=args.resume,stop_after=args.stop_after,timeout_seconds=args.storage_timeout)
                else:
                    if args.training_root is None:raise ValueError("Probe requires --training-root")
                    from .training.preparation_probe import run_preparation_probe
                    result = run_preparation_probe(config,result,args.training_root,args.run_dir,args.cache_dir,
                        persistent=args.persistent,resume=args.resume,stop_after=args.stop_after,
                        timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "plan-actor-preparation":
            from .training.actor_preparation import load_actor_preparation_config, actor_preparation_plan
            result = actor_preparation_plan(load_actor_preparation_config(args.config),
                args.data_dir,args.warmstart_data_dir,args.receiver_bundle,args.private_bundle,args.curated_bundle)
        elif command == "plan-curated-repair":
            from .training.curated_repair import load_curated_config, curated_repair_plan
            result = curated_repair_plan(load_curated_config(args.config),args.receiver_bundle,args.private_bundle)
        elif command == "curated-repair":
            from .training.curated_repair import load_curated_config, curated_repair_plan
            config = load_curated_config(args.config)
            if not args.execute:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = curated_repair_plan(config,args.receiver_bundle,args.private_bundle)
            else:
                from .training.curated_runner import run_curated_repair
                result = run_curated_repair(config,args.receiver_bundle,args.private_bundle,
                    args.references_dir,args.run_dir,args.cache_dir,resume=args.resume,
                    stop_after=args.stop_after,persistent=args.persistent,timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "private-support-control":
            from .training.private_control import load_private_config, private_control_plan, run_private_control
            config = load_private_config(args.config)
            if not args.execute:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = private_control_plan(config,args.bundle)
            else:
                result = run_private_control(config,args.bundle,args.references_dir,args.run_dir,args.cache_dir,
                    resume=args.resume,stop_after=args.stop_after,persistent=args.persistent,
                    timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "receiver-feasibility":
            from .training.receiver_plan import load_receiver_config, receiver_feasibility_plan
            config = load_receiver_config(args.config)
            if not args.execute:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = receiver_feasibility_plan(config,args.data_dir,args.warmstart_data_dir,args.selection)
            else:
                from .training.receiver import run_receiver
                result = run_receiver(config,args.data_dir,args.warmstart_data_dir,args.selection,args.references_dir,
                    args.run_dir,args.cache_dir,resume=args.resume,stop_after=args.stop_after,
                    persistent=args.persistent,timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "preference-diagnostic":
            from .training.feasibility import load_feasibility_config, prepare_feasibility, run_feasibility
            config = load_feasibility_config(args.config)
            if not args.execute:
                if args.resume or args.stop_after is not None:
                    raise ValueError("Resume/stop-after require explicit --execute")
                result = prepare_feasibility(config,args.bundle)["summary"]
            else:
                result = run_feasibility(config,args.bundle,args.run_dir,args.cache_dir,resume=args.resume,
                    stop_after=args.stop_after,persistent=args.persistent,timeout_seconds=args.storage_timeout)
                print(canonical(result))
                return result["exit_code"]
        elif command == "cache-reference":
            from .training.collection_config import load_collection_config
            from .training.bank import read_bank
            from .training.collection import reference_cache_plan, run_reference_cache
            config, bank = load_collection_config(args.config), read_bank(args.bank)
            if not args.execute:
                if args.resume:
                    raise ValueError("Resume requires explicit --execute")
                result = reference_cache_plan(config, bank)
            else:
                result = run_reference_cache(config, bank, args.references_dir, args.output_dir,
                                             args.cache_dir, resume=args.resume)
        elif command in ("assign", "build-preferences"):
            from .training.bank import read_bank, assign_bank
            from .training.preferences import build_preferences
            if args.output.exists():
                raise ValueError("Output exists; choose a new path to preserve prior evidence")
            bank = read_bank(args.bank, allow_synthetic=args.allow_synthetic)
            if command == "assign":
                result = assign_bank(bank, allow_synthetic=args.allow_synthetic, nll_mode=args.nll_mode,
                                     gamma=args.gamma, tau=args.tau, balance=args.balance)
            else:
                result = build_preferences(bank, allow_synthetic=args.allow_synthetic)
            write_json(args.output, result)
            if command == "assign" and result["solver"]["status"] == "not_converged":
                raise RuntimeError("Assignment did not converge; diagnostic saved, do not use for training")
        else:
            raise NotImplementedError(f"{command}: not_implemented; deferred to Milestones 3–5")
        print(canonical(result))
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        from .util import redact
        print(redact(f"{type(exc).__name__}: {exc}"), file=sys.stderr)
        return 2
