#!/bin/bash
#SBATCH --job-name=pact-zip-review
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=02:00:00
#SBATCH --output=pact-zip-review-%j.out
#SBATCH --error=pact-zip-review-%j.err
set -eu
umask 077
local_root="/local/pact-stage2-documented-export-fixed-$USER"
exec 9<"$local_root/remaining-branches-batch.lock"
flock -n -x 9
python3 - "$local_root" "$@" <<'PY'
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

local = Path(sys.argv[1])
run = "pact-stage2-documented-execution-001"
base = Path("/dataset") / os.environ["USER"] / "PACT"
stores = [base / name / run for name in (
    "stage2-documented-execution-export-fixed-v1", "stage2-documented-step77-recovery-v1")]
manifest = base / "stage2-fit15-local-zips-v1.json"
apply = len(sys.argv) == 4 and sys.argv[2] == "--apply"
if len(sys.argv) != 2 and not apply:
    raise SystemExit("Supply no arguments for review, or --apply MANIFEST_SHA256")
if not (stores[1]/"training-from-step77-v1/source_family-113-M.receipt.json").is_file():
    raise SystemExit("Fit 15 receipt missing")
if (local/"runs"/run/"continuations/source_family/227/Q").exists() or any(
        (stores[1]/n).exists() for n in ("SNAPSHOT_PENDING.json", "INFLIGHT.json")):
    raise SystemExit("Fit boundary changed")
folder = local/"runs/bundles"
def sha(p):
    with p.open("rb") as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(8*1024**2), b""):
            h.update(chunk)
        return h.hexdigest()
def check(p):
    if p.is_symlink() or not p.is_file() or not re.fullmatch(
            re.escape(run)+r"-(PRIVATE|SANITIZED|RECOVERY)-[0-9]+\.zip", p.name):
        raise ValueError("Unexpected local archive")
    h = sha(p)
    for store in stores:
        copy = store/"bundles"/p.name
        if (not copy.is_symlink() and copy.is_file() and copy.stat().st_size == p.stat().st_size
                and sha(copy) == h):
            return {"name": p.name, "bytes": p.stat().st_size, "sha256": h, "copy": str(copy)}
    raise ValueError("Durable copy mismatch: "+p.name)

paths = sorted(folder.glob(run+"-*.zip"))
if len(paths) != 135:
    raise SystemExit("Inventory changed; preserve remaining files for review")
if apply:
    if sha(manifest) != sys.argv[3]:
        raise SystemExit("Manifest checksum mismatch")
    expected = json.loads(manifest.read_text())
    if [row["name"] for row in expected] != [p.name for p in paths]:
        raise SystemExit("Manifest inventory mismatch")
    free = shutil.disk_usage(local).free
    for p, row in zip(paths, expected):
        if check(p) != row:
            raise SystemExit("Archive changed; stop for review")
        p.unlink()
    print("Removed 135 verified local duplicates; actual free-space change GiB:",
          round((shutil.disk_usage(local).free-free)/1024**3, 2))
else:
    rows = [check(p) for p in paths]
    data = json.dumps(rows, sort_keys=True, indent=2)+"\n"
    if manifest.exists():
        if manifest.read_text() != data:
            raise SystemExit("Existing manifest differs")
    else:
        with manifest.open("x") as f:
            f.write(data)
    print("Manifest:", manifest)
    print("Manifest SHA256:", sha(manifest))
    print("Verified archives:", len(rows), "logical GiB:", round(sum(r["bytes"] for r in rows)/1024**3,2))
print("Scratch available GiB:", round(shutil.disk_usage(local).free/1024**3,2))
PY
