"""Thin Colab orchestration helpers. Scientific logic lives in the ordinary CLI."""
from __future__ import annotations

import importlib.metadata
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .artifacts import export_bundle
from .cli import main
from .config import load_config
from .reporting import report
from .storage import persist_bundle
from .util import read_json, redact, safe_name

PRESETS = {
    "storage": "configs/smoke/storage.yaml",
    "smoke": "configs/smoke/qwen3_8b.yaml",
    "profile": "configs/pilot/profile_20.yaml",
    "pilot": "configs/pilot/validation_80.yaml",
    "matched": "configs/baselines/matched_80.yaml",
    "engineering": "configs/smoke/qwen3_06b_engineering.yaml",
}


def install_dependencies(checkout: str | Path) -> None:
    """Preserve the installed torch build using a constraint; never repair CUDA implicitly."""
    try:
        version = importlib.metadata.version("torch")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("Select a Colab GPU runtime with its preinstalled PyTorch first") from exc
    with tempfile.TemporaryDirectory(prefix="pact-install-") as temp:
        constraints = Path(temp) / "torch-constraint.txt"
        constraints.write_text(f"torch=={version}\n", encoding="utf-8")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade-strategy", "only-if-needed",
                        "-c", str(constraints), "-e", f"{Path(checkout).resolve()}[model]"], check=True)
    if importlib.metadata.version("torch") != version:
        raise RuntimeError("PyTorch build changed unexpectedly; stop and inspect installation")
    # pip check can expose unrelated Colab conflicts; display them for review without changing packages.
    check = subprocess.run([sys.executable, "-m", "pip", "check"], text=True, capture_output=True)
    print(check.stdout or "Dependency consistency check passed.")
    print("Selected library releases are pinned; actual GPU compatibility remains a runtime check.")


def cpu_checks(checkout: str | Path) -> None:
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=checkout, check=True)


def execute(*, checkout: str | Path, preset: str, run_id: str, scratch: str | Path,
            persistent: str | Path, resume: bool = False, stage: str | None = None) -> dict:
    if preset not in PRESETS:
        raise ValueError(f"Choose exactly one bounded preset: {sorted(PRESETS)}")
    safe_name(run_id)
    checkout, scratch, persistent = Path(checkout), Path(scratch), Path(persistent)
    os.environ["HF_HOME"] = str(scratch / "cache" / "huggingface")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    config_path = checkout / PRESETS[preset]
    config = load_config(config_path)
    if stage is not None and stage != config.stage:
        raise ValueError("Explicit STAGE must match the selected preset's stage")
    args = [config.stage, "--config", str(config_path), "--run-id", run_id, "--scratch", str(scratch), "--persistent", str(persistent)]
    if resume:
        args.append("--resume")
    exit_code = main(args)
    root = scratch / "runs" / run_id
    if not (root / "manifest.json").is_file():
        raise RuntimeError("Run did not initialize. Read the CLI error above; no bundle exists yet.")
    report(root)
    # Every notebook invocation makes a new bundle; preserve earlier handoffs.
    import time
    bundle_name = f"{run_id}-handoff-{time.time_ns()}.zip"
    local = scratch / "bundles" / bundle_name
    result = export_bundle(root, local)
    print(f"Local handoff ZIP ready: {local} SHA256: {result['sha256']}", flush=True)
    target = persistent / "bundles" / bundle_name
    manifest = read_json(root / "manifest.json")
    result.update(persistent_bundle=None, persistent_snapshot=manifest.get("verified_snapshot"), exit_code=exit_code)
    if not exit_code:
        try:
            persist_bundle(local, target, result["sha256"])
            result["persistent_bundle"] = str(target)
        except (Exception, KeyboardInterrupt) as exc:
            result.update(exit_code=2, persistence_error=redact(str(exc)))
            print(f"ZIP persistence failed; download the local ZIP: {local}", flush=True)
    # The runner already verified the raw-run snapshot. Do not sync it a third time.
    print(result, flush=True)
    if result["exit_code"]:
        print("The stage failed or was interrupted. The diagnostic bundle is preserved; use the recorded recovery command.")
    return result
