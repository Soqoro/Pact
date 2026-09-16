from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def canonical(value: Any) -> str:
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    def encode(obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Unsupported canonical JSON type: {type(obj).__name__}")
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False, default=encode)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def node_seed(*parts: Any) -> int:
    return int(digest(parts)[:8], 16) % (2**31)


def atomic_write(path: Path, data: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".partial-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data.encode() if isinstance(data, str) else data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path: Path, value: Any) -> None:
    atomic_write(path, canonical(value) + "\n")


def read_json(path: Path) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", name):
        raise ValueError("Run ID must be 1–100 letters, digits, dots, underscores or hyphens")
    return name


def redact(text: str) -> str:
    text = re.sub(r"(?i)(https?://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"\b(?:hf_|ghp_|github_pat_|sk-)[A-Za-z0-9_-]{8,}", "[REDACTED]", text)
    for key, value in os.environ.items():
        if any(s in key.upper() for s in ("TOKEN", "PASSWORD", "SECRET", "API_KEY")) and len(value) >= 8:
            text = text.replace(value, "[REDACTED]")
    return text
