"""Rebuild missing fit-16 inputs from pinned Stage I evidence and model receipts."""
import os
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import snapshot_download
from pact.util import digest, read_json, file_hash
from pact.revival.mistral_cache import repair
from pact.revival.stage1.evidence import archive
from pact.revival.stage1.weights import tensor_inventory

local = Path(os.environ["PACT_LOCAL"])
dataset = Path(os.environ["PACT_DATASET"])
run = "pact-stage2-documented-execution-001"
plan = read_json(local/"runs"/run/"plan.json")
if digest(plan) != "024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9":
    raise ValueError("Wrong plan")
parent = Path(plan["parent_path"])
name = parent.name
bundle = dataset/"stage1-execution-v1/persistent"/name/"bundles"/(name+"-PRIVATE-1793033718300732417.zip")
if not parent.exists():
    parent.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent.parent) as temp:
        staging = Path(temp)/name
        z, checks = archive(bundle, "754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0")
        with z:
            for member in checks:
                target = staging/member
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
        staging.rename(parent)
for member, expected in plan["parent_files"].items():
    if file_hash(parent/member) != expected:
        raise ValueError("Parent evidence mismatch")
cache = local/"cache"
os.environ["HF_TOKEN"] = (Path.home()/".config/pact/hf-token").read_text().strip()
repair(cache)
access = read_json(parent/"evidence/access.json")
for family in "QLM":
    _, inventory = tensor_inventory(parent, "uniform_joint_sft/"+family)
    if inventory["adapter_hash"] != plan["s0"][family]:
        raise ValueError("Starting adapter mismatch")
    receipt = access[family]
    spec = receipt["spec"]
    names = [*receipt["metadata_hashes"], *receipt["weight_files"]]
    path = Path(snapshot_download(spec["repository"], revision=spec["revision"],
                                  cache_dir=str(cache), allow_patterns=names,
                                  token=os.environ["HF_TOKEN"]))
    for member, expected in receipt["metadata_hashes"].items():
        if file_hash(path/member) != expected:
            raise ValueError("Model metadata mismatch")
    for member, info in receipt["weight_metadata"].items():
        if (path/member).stat().st_size != info["bytes"] or (len(info["etag"]) == 64 and file_hash(path/member) != info["etag"]):
            raise ValueError("Base weight mismatch")
    print("Training inputs verified:", family, flush=True)
