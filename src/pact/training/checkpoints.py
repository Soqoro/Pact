"""Immutable optimizer-boundary checkpoints, JSON and safetensors only."""
from __future__ import annotations

import math
from pathlib import Path
import shutil
import tempfile

from ..util import digest, file_hash, read_json, write_json

FILES = ("state.json", "tensors.safetensors")


def encode_state(value, is_tensor, tensors=None):
    """Typed tree preserves integer optimizer keys and tuple RNG states without pickle."""
    tensors = {} if tensors is None else tensors
    def pack(x):
        if is_tensor(x):
            key = f"tensor_{len(tensors)}"
            tensors[key] = x
            return {"tensor": key}
        if x is None or type(x) in (str, bool, int):
            return x
        if type(x) is float and math.isfinite(x):
            return x
        if type(x) in (tuple, list):
            return {"tuple" if type(x) is tuple else "list": [pack(v) for v in x]}
        if type(x) is dict:
            return {"dict": [[pack(k), pack(v)] for k, v in x.items()]}
        raise ValueError("Unsupported/nonfinite optimizer or RNG state")
    return pack(value), tensors


def decode_state(tree, tensors):
    used = set()
    def unpack(x):
        if x is None or type(x) in (str, bool, int) or type(x) is float and math.isfinite(x):
            return x
        if not isinstance(x, dict) or len(x) != 1:
            raise ValueError("Invalid checkpoint state tree")
        kind, value = next(iter(x.items()))
        if kind == "tensor":
            if value in used or value not in tensors:
                raise ValueError("Missing/reused checkpoint tensor")
            used.add(value)
            return tensors[value]
        if kind in ("list", "tuple"):
            values = [unpack(v) for v in value]
            return tuple(values) if kind == "tuple" else values
        if kind == "dict":
            pairs = [(unpack(k), unpack(v)) for k, v in value]
            result = dict(pairs)
            if len(result) != len(pairs):
                raise ValueError("Duplicate checkpoint state key")
            return result
        raise ValueError("Unknown checkpoint state node")
    result = unpack(tree)
    if used != set(tensors):
        raise ValueError("Unreferenced checkpoint tensors")
    return result


def read_checkpoint(path: Path, identity):
    inventory = read_json(path / "checksums.json")
    if set(inventory) != set(FILES):
        raise ValueError("Invalid checkpoint inventory")
    for name in FILES:
        p = path / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 1024**3 or file_hash(p) != inventory[name]:
            raise ValueError(f"Corrupt checkpoint: {name}")
    metadata = read_json(path / "state.json")
    if metadata.get("schema_version") != 1 or metadata.get("identity") != identity:
        raise ValueError("Incompatible checkpoint code/config/data/model/runtime identity")
    step = metadata.get("step")
    if type(step) is not int or step < 0 or path.name != f"step-{step:06d}":
        raise ValueError("Checkpoint progress/name mismatch")
    return metadata


def latest_checkpoint(root: Path, identity):
    paths = sorted(root.glob("step-*"))
    if not paths:
        raise ValueError("No complete warm-start checkpoint exists")
    for expected, path in enumerate(paths):
        metadata = read_checkpoint(path, identity)
        if metadata["step"] != expected:
            raise ValueError("Missing optimizer-boundary checkpoint")
    return paths[-1], metadata


def commit_checkpoint(root: Path, *, step, identity, tree, write_tensors):
    if type(step) is not int or step < 0:
        raise ValueError("Invalid checkpoint step")
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"step-{step:06d}"
    if target.exists():
        raise ValueError("Checkpoint exists; immutable writes cannot overwrite it")
    staging = Path(tempfile.mkdtemp(prefix=".pending-", dir=root))
    try:
        write_tensors(staging / "tensors.safetensors")
        write_json(staging / "state.json", {"schema_version": 1, "identity": identity, "step": step, "tree": tree})
        checksums = {name: file_hash(staging / name) for name in FILES}
        # Flush the tensor file before the last inventory marker.
        import os
        with (staging / "tensors.safetensors").open("rb") as stream:
            os.fsync(stream.fileno())
        for name in FILES:
            if file_hash(staging / name) != checksums[name]:
                raise ValueError("Checkpoint changed during write")
        write_json(staging / "checksums.json", checksums)
        staging.rename(target)
        read_checkpoint(target, identity)
        return target
    finally:
        if staging.exists():
            shutil.rmtree(staging)
