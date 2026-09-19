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
