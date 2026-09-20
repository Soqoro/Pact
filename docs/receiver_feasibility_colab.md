# Broader receiver feasibility: Colab sequence

**Completed run:** `qwen3-receiver-feasibility-001` now passes
[returned artifact review](reviews/qwen3-receiver-feasibility-001.md): 48 records,
472 calls and zero preference pairs. Do not repeat this completed run. The cells
below document its execution and recovery procedure; GPU reset/resume remains
unverified. The frozen [24-task design](receiver_feasibility_design.md) is unchanged.

First review, commit and push the new implementation. Obtain the new full SHA with
`git rev-parse HEAD`. The earlier `80992b4...` commit does not contain this runner.
Select an **L4 GPU runtime**, matching the recorded runtime fingerprint. For a fresh
run, execute the following cells in order. No warm-start optimization is requested.

**1. Mount Drive and pin the new code**

```python
from pathlib import Path
import os, re, subprocess, sys
from google.colab import drive

REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "PASTE_NEW_FULL_COMMIT_SHA"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF), "Set the newly published full SHA."

drive.mount("/content/drive")
SCRATCH = Path("/content/pact-scratch")
CHECKOUT = SCRATCH / "checkout"
SCRATCH.mkdir(parents=True, exist_ok=True)

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

if not CHECKOUT.exists():
    subprocess.run(["git", "clone", "--filter=blob:none", REPO_URL, str(CHECKOUT)], check=True)
if git("-C", str(CHECKOUT), "status", "--porcelain"):
    raise RuntimeError("Checkout has local changes; preserve them before switching code.")
if git("-C", str(CHECKOUT), "remote", "get-url", "origin") != REPO_URL:
    raise RuntimeError("Existing checkout has a different origin.")
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()

os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["HF_HOME"] = str(SCRATCH / "cache/huggingface")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
print("Pinned commit:", GIT_REF)
```

**2. Install, run CPU checks and verify the runtime**

```python
from pact.colab import install_dependencies, cpu_checks
from pact.training.receiver_plan import load_receiver_config

install_dependencies(CHECKOUT)
cpu_checks(CHECKOUT)

import torch
from pact.environment import runtime_fingerprint

CONFIG = CHECKOUT / "experiments/receiver_feasibility.json"
SELECTION = CHECKOUT / "experiments/receiver_feasibility_selection.json"
recipe = load_receiver_config(CONFIG)
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert torch.cuda.is_bf16_supported()
print("GPU:", torch.cuda.get_device_name(0))
print("Expected runtime:", recipe.runtime_fingerprint)
print("Current runtime: ", runtime_fingerprint())
if runtime_fingerprint() != recipe.runtime_fingerprint:
    raise RuntimeError("Runtime mismatch: stop and report this output before downloading the model.")
```

**3. Prepare the pinned data and restore the completed actors**

This prepares source data only. It verifies the existing 1,200-task and 12-task
manifest hashes. A fresh scratch runtime restores the full completed warm-start
snapshot (approximately 1.57 GB, including optimizer artifacts); the small handoff
ZIP is insufficient. An intact scratch copy is verified and reused.

```python
from pact.training.receiver_plan import receiver_feasibility_plan
from pact.training.colab import restore_snapshot
from pact.training.scoring import verify_references

DATA = SCRATCH / "training-data/proposal-1200"
WARM_DATA = SCRATCH / "training-data/engineering-12"
WARMSTART = SCRATCH / "warmstart/qwen3-warmstart-001"
REFERENCES = WARMSTART / "references"
RUN = SCRATCH / "receiver-feasibility/qwen3-receiver-feasibility-001"
DURABLE = Path("/content/drive/MyDrive/PACT/receiver-feasibility/qwen3-receiver-feasibility-001")
TIMEOUT = 120

for destination, items in [(DATA, 1200), (WARM_DATA, 12)]:
    if not destination.exists():
        subprocess.run([
            sys.executable, "-m", "pact", "prepare-training-data",
            "--cache-dir", str(SCRATCH / "cache/data"),
            "--output-dir", str(destination), "--items", str(items),
            "--seed", "20260918", "--download",
        ], check=True)

PLAN = receiver_feasibility_plan(recipe, DATA, WARM_DATA, SELECTION)
print("Selection:", PLAN["selection_hash"])
print("Budget:", PLAN["budget"])

if not WARMSTART.exists():
    print(restore_snapshot(
        "/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/snapshots/1789796424349439412-7eeb6af87200",
        WARMSTART, timeout_seconds=TIMEOUT,
    ))
verify_references(REFERENCES, recipe)
print("Frozen actors verified.")
```

**4. Execute the bounded diagnostic**

Set `EXECUTE=True` to run the declared experiment; `False` prints only the plan.
Keep `RESUME=False` for the first invocation and `STOP_AFTER=None` to run the full
schedule. An optional positive `STOP_AFTER` pauses at that many new committed
calls and preserves the same design, independent of outcomes. It counts calls,
not tasks or records.

```python
import json

EXECUTE = False
RESUME = False
STOP_AFTER = None

args = [
    sys.executable, "-u", "-m", "pact", "receiver-feasibility",
    "--config", str(CONFIG), "--data-dir", str(DATA),
    "--warmstart-data-dir", str(WARM_DATA), "--selection", str(SELECTION),
    "--references-dir", str(REFERENCES), "--run-dir", str(RUN),
    "--cache-dir", str(SCRATCH / "cache/models"),
    "--persistent", str(DURABLE), "--storage-timeout", str(TIMEOUT),
]
if EXECUTE:
    args.append("--execute")
    if RESUME:
        args.append("--resume")
    if STOP_AFTER is not None:
        args += ["--stop-after", str(STOP_AFTER)]

RECEIVER_RESULT = None
with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end="", flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "exit_code" in value and "path" in value:
            RECEIVER_RESULT = value
    exit_code = process.wait()

if RECEIVER_RESULT:
    print("Local ZIP:", RECEIVER_RESULT["path"])
    print("Drive ZIP:", RECEIVER_RESULT.get("persistent_bundle"))
    print("SHA256:", RECEIVER_RESULT["sha256"])
    print("Verified snapshot:", RECEIVER_RESULT.get("persistent_snapshot"))
if exit_code:
    raise RuntimeError("Keep scratch and return the diagnostic ZIP/error before retrying.")
if EXECUTE:
    assert RECEIVER_RESULT is not None, "Missing receiver handoff receipt."
```

Expected full completion: `receiver_feasibility_complete_local`,
`completed_records=48`, `exit_code=0`, `persistent_copy_verified=true` and
`training_executed=false`. The generation counter shows a ceiling of 912; an
actual count below that is expected when some receivers are ineligible. A valid
experiment may end with zero pairs. Requested pauses instead report
`interrupted_at_call_boundary`.

**5. Download and return the review ZIP**

```python
from google.colab import files
assert RECEIVER_RESULT is not None, "Execute the run first."
print("SHA256:", RECEIVER_RESULT["sha256"])
print("Drive copy:", RECEIVER_RESULT.get("persistent_bundle"))
files.download(RECEIVER_RESULT["path"])
```

Upload this ZIP to `results_import` and return the checksum and final receipt.
The archive contains actual call tokens, attempts, main trajectories, candidate
pools and diagnostic accounting. It exports no training pairs or weight files.

**Recovery after a pause or reset**

With intact scratch, rerun cell 4 using `EXECUTE=True`, `RESUME=True` and
`STOP_AFTER=None`. Completed call shards are reused; cached candidates count
toward the same original four-sample pool and global budget. A complete run can
be revisited to retry persistence without fresh generation. Preserve the same
clean commit, data, selection, references, hardware and library fingerprint.

After reset, run cells 1–3 and restore the exact latest printed receiver snapshot
into an absent receiver run directory, then resume:

```python
from pact.training.receiver import restore_receiver
RECEIVER_SNAPSHOT = ""  # Exact latest receiver snapshot path from the receipt.
assert RECEIVER_SNAPSHOT, "Set the latest receiver snapshot path."
print(restore_receiver(RECEIVER_SNAPSHOT, RUN, timeout_seconds=TIMEOUT))
```

The runner persists an unsafe recovery marker before a task's fresh calls and a
safe snapshot at task completion or a handled call-boundary pause. If abrupt
runtime loss occurred inside that window, a restored snapshot may omit calls that
already consumed budget. Restore therefore rejects unsafe or older snapshots,
and local resume rejects any intent lacking a verified result. Return the error
and available ZIP for an explicit recovery-budget review. Selecting an older safe
snapshot, changing the run ID or deleting an unresolved intent is not a compatible
resume. This conservative behavior preserves the declared sampling cap.

Each storage operation has its own deadline. A timeout may leave a valid local
ZIP without a verified final Drive copy. Keep the runtime and local artifacts;
do not treat a completed generation counter as proof of persistence. Real GPU
interruption/restore and current Drive contents remain unverified until returned
evidence exercises them.
