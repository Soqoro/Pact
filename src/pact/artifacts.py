from __future__ import annotations

import contextlib
import os
import shutil
import socket
import stat
import tempfile
import time
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from .util import atomic_write, canonical, digest, file_hash, read_json, write_json


def safe_relative(name: str) -> PurePosixPath:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or any(x in ("..", ".") for x in p.parts) or "\\" in name or ":" in name or "\x00" in name:
        raise ValueError(f"Unsafe artifact path: {name!r}")
    return p


@contextlib.contextmanager
def run_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".lock"
    if path.exists():
        old = read_json(path)
        alive = False
        if os.name == "nt":
            # Windows os.kill(pid, 0) can terminate a process; never use it as a probe.
            raise RuntimeError("Run lock exists; inspect its owning process before removing the stale .lock on Windows")
        if old["host"] == socket.gethostname():
            try:
                os.kill(old["pid"], 0)
                alive = True
            except ProcessLookupError:
                pass
        if alive or old["host"] != socket.gethostname():
            raise RuntimeError("Run already locked; inspect the owning process before removing .lock")
        path.unlink()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(canonical({"pid": os.getpid(), "host": socket.gethostname()}))
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


class ShardStore:
    def __init__(self, root: Path):
        self.root = root
        (root / "shards").mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("Shard key must be SHA256")
        return self.root / "shards" / f"{key}.json"

    def read(self, key: str):
        path = self.path(key)
        marker = path.with_suffix(".sha256")
        if marker.exists():
            if not path.exists() or file_hash(path) != marker.read_text().strip():
                raise ValueError(f"Completed shard corrupted or incomplete: {key}")
            value = read_json(path)
            if value.get("work_id") != key or value.get("schema_version") != 1:
                raise ValueError("Shard identity/schema mismatch")
            return value
        if path.exists():
            archive = self.root / "incomplete" / f"{key}-{uuid.uuid4().hex}.json"
            archive.parent.mkdir(exist_ok=True)
            shutil.move(str(path), archive)
        return None

    def put(self, key: str, value: dict, *, interrupt_after_data=False):
        existing = self.read(key)
        if existing is not None:
            if canonical(existing) != canonical(value):
                raise ValueError("Attempt to overwrite immutable completed shard")
            return
        path = self.path(key)
        write_json(path, value)
        if interrupt_after_data:
            raise InterruptedError("Simulated interruption before completion marker")
        atomic_write(path.with_suffix(".sha256"), file_hash(path) + "\n")

    def records(self) -> list[dict]:
        return [value for p in sorted((self.root / "shards").glob("*.json"))
                if (value := self.read(p.stem)) is not None]


def artifact_files(root: Path) -> list[Path]:
    files = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if any(part.startswith(".") for part in rel.parts) or rel.parts[0] in ("incomplete", "cache"):
            continue
        if p.is_symlink():
            raise ValueError("Artifact symlinks are not allowed")
        if p.is_file():
            if rel.parts[0] == "shards" and p.suffix == ".json" and not p.with_suffix(".sha256").exists():
                continue
            files.append(p)
    return files


def sync_run(root: Path, destination: Path, *, interrupt_before_marker=False) -> Path:
    """Content-addressed immutable copies; never assume Drive rename is atomic."""
    destination.mkdir(parents=True, exist_ok=True)
    objects = destination / "objects"
    objects.mkdir(exist_ok=True)
    entries = {}
    for path in artifact_files(root):
        sha = file_hash(path)
        target = objects / sha
        if not target.exists() or file_hash(target) != sha:
            # Incomplete object copies are never reachable from a completed snapshot.
            with path.open("rb") as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
                dst.flush()
                os.fsync(dst.fileno())
        if file_hash(target) != sha:
            raise OSError("Persistent copy checksum verification failed")
        entries[path.relative_to(root).as_posix()] = sha
    index = {"schema_version": 1, "created_ns": time.time_ns(), "files": entries}
    snapshot = destination / "snapshots" / f'{index["created_ns"]}-{digest(index)[:12]}'
    snapshot.mkdir(parents=True)
    (snapshot / "index.json").write_text(canonical(index), encoding="utf-8")
    if read_json(snapshot / "index.json") != index:
        raise OSError("Persistent index copy verification failed")
    if interrupt_before_marker:
        raise InterruptedError("Simulated incomplete persistent copy")
    # Write this last. Readers verify marker, index and every referenced object.
    (snapshot / "COMPLETE").write_text(file_hash(snapshot / "index.json"), encoding="ascii")
    if (snapshot / "COMPLETE").read_text() != file_hash(snapshot / "index.json"):
        raise OSError("Completion marker verification failed")
    return snapshot


def restore_run(destination: Path, root: Path) -> dict:
    if root.exists() and any(root.iterdir()):
        raise ValueError("Restore requires an empty local run directory")
    rejected = []
    for snapshot in sorted((destination / "snapshots").glob("*"), reverse=True):
        try:
            marker, index_path = snapshot / "COMPLETE", snapshot / "index.json"
            if not marker.is_file() or marker.read_text() != file_hash(index_path):
                raise ValueError("missing/invalid completion marker")
            index = read_json(index_path)
            if index["schema_version"] != 1 or "manifest.json" not in index["files"]:
                raise ValueError("invalid snapshot schema")
            for name, sha in index["files"].items():
                safe_relative(name)
                if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                    raise ValueError("invalid object hash")
                obj = destination / "objects" / sha
                if obj.is_symlink() or file_hash(obj) != sha:
                    raise ValueError("corrupted object")
            root.mkdir(parents=True, exist_ok=True)
            for name, sha in index["files"].items():
                atomic_write(root / name, (destination / "objects" / sha).read_bytes())
            return {"restored_snapshot": snapshot.name, "rejected_newer_snapshots": rejected}
        except (OSError, ValueError, KeyError) as exc:
            rejected.append({"snapshot": snapshot.name, "reason": str(exc)})
    raise ValueError(f"No verified complete persistent snapshot: {rejected}")


EXPORT_NAMES = {"manifest.json", "resolved_config.yaml", "environment.json", "package_freeze.txt",
                "data_manifest.json", "metrics.json", "metrics_by_condition.csv", "per_task_metrics.csv",
                "resource_usage.json", "diagnostics.json", "failures.jsonl", "sample_traces.jsonl",
                "CODEX_HANDOFF.md", "evaluations.json", "probe_summary.json", "artifact_inventory.json"}


def export_bundle(root: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"Bundle already exists: {output}")
    files = [p for p in artifact_files(root) if p.name in EXPORT_NAMES and p.parent == root or p.parent == root / "logs"]
    if not (root / "CODEX_HANDOFF.md").exists():
        raise ValueError("Generate a report before exporting")
    checksums = {p.relative_to(root).as_posix(): file_hash(p) for p in files}
    write_json(root / "checksums.json", checksums)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".partial-bundle-", dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(root).as_posix())
            archive.write(root / "checksums.json", "checksums.json")
        validate_bundle(Path(tmp))
        os.replace(tmp, output)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return {"path": str(output), "sha256": file_hash(output), "bytes": output.stat().st_size}


def validate_bundle(bundle: Path, *, max_bytes=100 * 1024 * 1024, max_files=1000) -> dict[str, bytes]:
    import hashlib
    import json
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        if len(infos) > max_files or sum(i.file_size for i in infos) > max_bytes:
            raise ValueError("Bundle exceeds extraction limits")
        seen = set()
        for info in infos:
            name = safe_relative(info.filename).as_posix()
            mode = info.external_attr >> 16
            if name in seen or info.is_dir() or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
                raise ValueError("Duplicate, directory, symlink or special archive member")
            seen.add(name)
            if name not in EXPORT_NAMES | {"checksums.json"} and not (name.startswith("logs/") and name.endswith((".json", ".jsonl", ".txt"))):
                raise ValueError("Unexpected bundle member")
        if "checksums.json" not in seen:
            raise ValueError("Missing checksum manifest")
        payload = {i.filename: archive.read(i) for i in infos}
        checksums = json.loads(payload["checksums.json"])
        if set(checksums) != seen - {"checksums.json"}:
            raise ValueError("Checksum membership mismatch")
        if any(hashlib.sha256(payload[n]).hexdigest() != sha for n, sha in checksums.items()):
            raise ValueError("Bundle checksum mismatch")
        for required in ("manifest.json", "resolved_config.yaml", "evaluations.json", "CODEX_HANDOFF.md"):
            if required not in payload:
                raise ValueError(f"Missing required member: {required}")
        return payload


def import_bundle(bundle: Path, destination: Path) -> dict:
    payload = validate_bundle(bundle)
    if destination.exists():
        raise FileExistsError("Import destination already exists; never overwrite a prior review")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".partial-import-", dir=destination.parent))
    try:
        for name, value in payload.items():
            atomic_write(staging / name, value)
        os.replace(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {"path": str(destination), "files": len(payload), "trust": "untrusted data; no contents executed"}
