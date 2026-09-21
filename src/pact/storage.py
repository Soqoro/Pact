"""Isolate mounted-filesystem writes so a stalled Drive cannot block the notebook."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .util import file_hash, read_json, redact, write_json

DEFAULT_TIMEOUT_SECONDS = 120.0


def storage_operation(operation: str, source: Path, destination: Path, *,
                      timeout_seconds=DEFAULT_TIMEOUT_SECONDS, **options) -> dict:
    if operation not in ("snapshot", "bundle", "bundle-restore", "warmstart-restore", "collection-restore", "feasibility-restore", "receiver-restore", "private-control-restore", "curated-repair-restore", "preparation-probe-restore", "preparation-references-restore") or not 0 < timeout_seconds < float("inf"):
        raise ValueError("Invalid storage operation or timeout")
    # This control directory must stay on scratch, never on the mounted destination.
    control_parent = destination.parent if operation.endswith("-restore") else source.parent
    with tempfile.TemporaryDirectory(prefix=".pact-storage-", dir=control_parent) as temp:
        control = Path(temp)
        write_json(control / "request.json", {"operation": operation, "source": str(source.absolute()),
                   "destination": str(destination.absolute()), "options": options})
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(filter(None, (str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH"))))
        print(f"Persisting {operation}: {destination} (timeout {timeout_seconds:g}s)", flush=True)
        with (control / "stderr.txt").open("w") as errors:
            process = subprocess.Popen([sys.executable, "-m", "pact.storage", str(control)],
                                       env=env, stdout=subprocess.DEVNULL, stderr=errors)
            started = time.monotonic()
            last_progress, last_notice = None, started
            try:
                while process.poll() is None:
                    elapsed = time.monotonic() - started
                    if elapsed >= timeout_seconds:
                        raise TimeoutError(f"{operation} persistence exceeded {timeout_seconds:g}s; local results retained")
                    progress_file = control / "progress.json"
                    if progress_file.exists():
                        progress = read_json(progress_file)["message"]
                        if progress != last_progress:
                            print(progress, flush=True)
                            last_progress, last_notice = progress, time.monotonic()
                    if time.monotonic() - last_notice >= 10:
                        print(f"Waiting for {operation} persistence ({elapsed:.0f}s elapsed)", flush=True)
                        last_notice = time.monotonic()
                    try:
                        process.wait(timeout=min(0.2, max(0.001, timeout_seconds - elapsed)))
                    except subprocess.TimeoutExpired:
                        pass
                result_file = control / "result.json"
                if not result_file.exists():
                    raise OSError(f"Storage worker exited {process.returncode} without a verified result")
                result = read_json(result_file)
                if process.returncode or "error" in result:
                    error = result.get("error", {})
                    kind = {"InterruptedError": InterruptedError, "ValueError": ValueError}.get(error.get("type"), OSError)
                    raise kind(error.get("message", "Storage worker failed"))
                return result
            finally:
                if process.poll() is None:
                    process.kill()
                    # A process blocked inside an OS mount may not exit immediately.
                    # Never replace the storage deadline with an unbounded wait.
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        print("Storage worker termination is pending in the OS; no persistence success claimed.", flush=True)


def persist_bundle(source: Path, destination: Path, sha256: str, *,
                   timeout_seconds=DEFAULT_TIMEOUT_SECONDS) -> dict:
    return storage_operation("bundle", source, destination, timeout_seconds=timeout_seconds, sha256=sha256)


def _worker(control: Path) -> int:
    request = read_json(control / "request.json")
    source, destination = Path(request["source"]), Path(request["destination"])
    def progress(message):
        write_json(control / "progress.json", {"message": message})
    try:
        if request["operation"] == "preparation-references-restore":
            from .training.preparation_restore import _restore_preparation_references
            result = _restore_preparation_references(source,destination,progress=progress)
        elif request["operation"] in ("warmstart-restore", "collection-restore", "feasibility-restore", "receiver-restore", "private-control-restore", "curated-repair-restore", "preparation-probe-restore"):
            from .training.colab import _restore_snapshot
            kind = {"warmstart-restore":"warmstart", "collection-restore":"training_bank",
                    "feasibility-restore":"preference_feasibility_diagnostic",
                    "receiver-restore":"receiver_feasibility_diagnostic",
                    "private-control-restore":"private_support_control",
                    "curated-repair-restore":"curated_repair_diagnostic",
                    "preparation-probe-restore":"actor_preparation_probe"}[request["operation"]]
            result = _restore_snapshot(source, destination, progress=progress, kind=kind)
        elif request["operation"] == "snapshot":
            from .artifacts import _sync_run
            snapshot = _sync_run(source, destination, progress=progress, **request["options"])
            result = {"snapshot": str(snapshot)}
        else:
            expected = request["options"]["sha256"]
            if file_hash(source) != expected:
                raise ValueError("Local bundle checksum changed before persistence")
            progress("Copying and verifying the handoff ZIP")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            if file_hash(destination) != expected:
                raise OSError("Persistent bundle checksum mismatch")
            sidecar = destination.with_suffix(".zip.sha256")
            sidecar.write_text(expected + "\n", encoding="ascii")
            if sidecar.read_text(encoding="ascii").strip() != expected:
                raise OSError("Persistent bundle checksum sidecar mismatch")
            result = {"path": str(destination), "sha256": expected}
        write_json(control / "result.json", result)
        return 0
    except Exception as exc:
        write_json(control / "result.json", {"error": {"type": type(exc).__name__, "message": redact(str(exc))}})
        return 1


if __name__ == "__main__":
    raise SystemExit(_worker(Path(sys.argv[1])))
