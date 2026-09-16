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
    p = argparse.ArgumentParser(prog="pact", description="PACT validation diagnostic pipeline (Milestones 0–2)")
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
    for name in ("train", "warmstart", "adaptive-evaluate", "evaluate", "assign", "build-preferences", "collect-bank"):
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
        else:
            raise NotImplementedError(f"{command}: not_implemented; deferred to Milestones 3–5")
        print(canonical(result))
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        from .util import redact
        print(redact(f"{type(exc).__name__}: {exc}"), file=sys.stderr)
        return 2
