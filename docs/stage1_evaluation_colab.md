# Fresh Colab: Stage I checkpoint verification and staged evaluation

Use notebook27 or these identical cells in order. Pin the **new reviewed evaluation
commit**, not the training commit. The inherited runtime is exactly the recorded
A100-SXM4-80GB environment (fingerprint e4e0376b…); a40GB A100 is different.
The code will check the entire fingerprint, not only GPU name. No compatibility
exception is implicit. No automatic dependency upgrade is a remedy for mismatch.

Prerequisites: both audited review ZIPs, the final RECOVERY ZIP plus its SHA sidecar,
reviewed current exposure inventory, gated official Q/L/M/R model access using the
Colab HF_TOKEN secret. Model access is needed only for verification/inference.
RECOVERY remains on Drive. The scratch tensor map selects the six final step128
files by metadata/ancestor binding, never a directory called latest. After a reset,
restore only this evaluation child and recopy these immutable tensors to the same
scratch paths. Do not restore/retrain continuation003 or replacement002.

The current real resolver exports two blockers: the prompt's128/128 versus actual
120/136 source-evaluation allocation, and unresolved original-run later generation
ownership. **Do not run freeze or benchmark stages until those are explicitly
resolved in reviewed code/evidence.** Verification can proceed independently.
No GPU has been verified for this new evaluation implementation yet.

## Cell 1

```python
from pathlib import Path
import os, re, sys, subprocess, json, shutil
from google.colab import drive
drive.mount("/content/drive")

REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "PASTE_THE_REVIEWED_40_CHARACTER_COMMIT_AFTER_PUSH"
assert re.fullmatch(r"[0-9a-f]{40}", GIT_REF), "Set the reviewed evaluation commit."
SCRATCH = Path("/content/pact-stage1")
CHECKOUT = SCRATCH / ("checkout-" + GIT_REF[:12])
RUN = SCRATCH / "runs/pact-revival-stage1-evaluation-001"
CACHE = SCRATCH / "cache"
PERSISTENT = Path("/content/drive/MyDrive/PACT/stage1-evaluation") / RUN.name
SCRATCH.mkdir(parents=True, exist_ok=True)
RUN.parent.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(["git", "clone", "--filter=blob:none", REPO_URL, str(CHECKOUT)], check=True)
assert subprocess.check_output(["git", "-C", str(CHECKOUT), "remote", "get-url", "origin"], text=True).strip() == REPO_URL
assert not subprocess.check_output(["git", "-C", str(CHECKOUT), "status", "--porcelain"], text=True).strip(), "Preserve local changes; do not reset them."
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
os.chdir(CHECKOUT)
```

## Cell 2

```python
subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[model]"], check=True)
# Do not replace Colab Torch/CUDA or change runtime versions to bypass a guard.
sys.path.insert(0, str(CHECKOUT / "src"))
from pact.util import read_json, digest
from pact.revival.stage1 import evidence
from google.colab import userdata
try:
    token = userdata.get("HF_TOKEN")
    if token:
        os.environ["HF_TOKEN"] = token
finally:
    token = None
```

## Cell 3

```python
SOURCE = Path("/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-continuation-003/bundles")
PRIVATE = SOURCE / "pact-heterogeneous-receiver-training-continuation-003-PRIVATE-1792630912628874679.zip"
SANITIZED = SOURCE / "pact-heterogeneous-receiver-training-continuation-003-SANITIZED-1792630916043928268.zip"
RECOVERY = SOURCE / "pact-heterogeneous-receiver-training-continuation-003-RECOVERY-1792630916259050432.zip"
# Supply the actual reviewed inventory, with its current ledger binding and
# typed self-exposure events if necessary. Never create an empty substitute.
EXPOSURE = Path("/content/drive/MyDrive/PACT/SET_REVIEWED_EXPOSURE_INVENTORY_PATH.json")
assert all(p.is_file() for p in (PRIVATE, SANITIZED, RECOVERY, EXPOSURE)), "Required evidence/inventory missing."
RECOVERY_SHA = RECOVERY.with_suffix(".zip.sha256").read_text().strip()
evidence.sha(RECOVERY_SHA)
TENSOR_DIR = SCRATCH / "verified-final-tensors"
MAP = TENSOR_DIR / "checkpoint-map.json"
```

## Cell 4

```python
import time
from pact.util import redact

def stage(name, *options):
    command = [sys.executable, "-u", "-m", "pact.revival.stage1", name,
               "--run-dir", str(RUN), "--cache-dir", str(CACHE), *map(str, options)]
    log_path = SCRATCH / f"stage1-{name}-{time.time_ns()}.log"
    print("Starting:", name, "Log:", log_path, flush=True)
    with log_path.open("w") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            clean = redact(line)
            secret = os.environ.get("HF_TOKEN")
            if secret:
                clean = clean.replace(secret, "[REDACTED]")
            print(clean, end="", flush=True)
            log.write(clean); log.flush()
        code = process.wait()
    if code:
        raise RuntimeError(f"{name} stopped ({code}); preserve scratch and log. No automatic retry.")
    print("Finished:", name)

# CPU-only copies; all historical tensor/member hashes are checked first.
if not MAP.exists():
    stage("map-recovery", "--private", PRIVATE, "--recovery-bundle", RECOVERY,
          "--recovery-sha", RECOVERY_SHA, "--tensor-dir", TENSOR_DIR)
```

## Cell 5

```python
if RUN.exists():
    stage("inspect")
elif PERSISTENT.exists() and any(PERSISTENT.iterdir()):
    stage("restore", "--persistent", PERSISTENT)
else:
    stage("resolve", "--private", PRIVATE, "--sanitized", SANITIZED,
          "--exposure", EXPOSURE, "--checkpoint-map", MAP)
stage("export", "--export-stage", "inspect", "--persistent", PERSISTENT)
RESOLUTION_HASH = digest(read_json(RUN / "contract_resolution.json"))
print("Resolution hash:", RESOLUTION_HASH)
print("Blockers:", read_json(RUN / "contract_resolution.json")["blockers"])
```

## Cell 6

```python
# Deliberately one stage per explicit invocation. Run All defaults to inspect.
# verify -> exports checkpoint-only evidence and STOPS (at most16 synthetic forwards).
# freeze/smoke/later stages remain blocked until real contract conflicts are resolved.
ACTION = "inspect"
assert ACTION in {"inspect", "verify", "freeze", "smoke", "validation", "source_evaluation", "fixed_history", "report"}
if ACTION == "verify":
    stage("repair-tokenizer-cache", "--execute", "--plan-hash", RESOLUTION_HASH, "--persistent", PERSISTENT)
    stage(ACTION, "--execute", "--plan-hash", RESOLUTION_HASH, "--persistent", PERSISTENT)
elif ACTION in {"smoke", "validation", "source_evaluation", "fixed_history"}:
    PLAN_HASH = digest(read_json(RUN / "plan.json"))
    stage(ACTION, "--execute", "--plan-hash", PLAN_HASH, "--persistent", PERSISTENT)
else:
    stage(ACTION, "--persistent", PERSISTENT)
```

## Exact subsequent single-stage commands

The `stage` helper above passes the real module, run directory and cache. Invoke
ONE line at a time, after reviewing the previous export; do not turn these into a
loop. Negative valid outcomes do not authorize method changes or selective reporting.
Current contract blockers prevent the freeze and benchmark commands.

```python
stage("repair-tokenizer-cache", "--execute", "--plan-hash", RESOLUTION_HASH, "--persistent", PERSISTENT)
stage("verify", "--execute", "--plan-hash", RESOLUTION_HASH, "--persistent", PERSISTENT)
# Return checkpoint-only PRIVATE and SANITIZED exports, then stop.
```

Once real contract blockers have an explicit reviewed resolution:

```python
stage("freeze", "--persistent", PERSISTENT)
PLAN_HASH = digest(read_json(RUN / "plan.json"))
```

```python
stage("smoke", "--execute", "--plan-hash", PLAN_HASH, "--persistent", PERSISTENT)
```

```python
stage("validation", "--execute", "--plan-hash", PLAN_HASH, "--persistent", PERSISTENT)
```

```python
stage("source_evaluation", "--execute", "--plan-hash", PLAN_HASH, "--persistent", PERSISTENT)
```

```python
stage("fixed_history", "--execute", "--plan-hash", PLAN_HASH, "--persistent", PERSISTENT)
```

Each generation stage reports/exports and exits. Rejected attacks remain unavailable,
not defensive successes; incomplete infrastructure stays missing. Inspect export
preserves partial evidence without authorizing retries:

```python
stage("export", "--export-stage", "inspect", "--persistent", PERSISTENT)
```

Bring back PRIVATE and SANITIZED ZIPs, their hashes and any error log. Keep tensors,
RECOVERY ZIPs and parent snapshots. Expected child artifacts include contract and
lineage resolution, checkpoint inventory/verification receipt, frozen plan,
reconciled budget, immutable attempt/result/link shards, source/attack availability,
live/fixed-history private rows, paired metrics/interaction and cost report.

Local trusted audit (no archive code execution):

```bash
PYTHONPATH=src python -m pact.revival.stage1 audit --run-dir /outside/git/stage1-audit --private /path/to/PRIVATE.zip
```

## Pending inspection snapshot incident

For the audited 1792657561217646069 inspection return with a pending marker and
no snapshot, use [the compact recovery sequence](stage1_compact_recovery_colab.md)
after pushing the maintenance revision. Do not rerun Cell 5 or manually clear the
marker. This separately invoked recovery preserves the old resolution, records a
storage-only source transition, persists a compact archive and stops without models.
