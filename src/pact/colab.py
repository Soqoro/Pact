"""Thin Colab orchestration helpers. Scientific logic lives in the ordinary CLI."""
from __future__ import annotations

import importlib.metadata
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .artifacts import export_bundle, sync_run
from .cli import main
from .config import load_config
from .reporting import report
from .util import file_hash, safe_name

PRESETS = {
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
    target = persistent / "bundles" / bundle_name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(local, target)
    if file_hash(target) != result["sha256"]:
        raise OSError(f"Bundle persistence checksum mismatch; retained local bundle at {local}")
    target.with_suffix(".zip.sha256").write_text(result["sha256"] + "\n", encoding="ascii")
    snapshot = sync_run(root, persistent / run_id)
    result.update(persistent_bundle=str(target), persistent_snapshot=str(snapshot), exit_code=exit_code)
    print(result)
    if exit_code:
        print("The stage failed or was interrupted. The diagnostic bundle is preserved; use the recorded recovery command.")
    return result
