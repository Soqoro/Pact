# Private-support second-seed control: fresh Colab runtime

This new control keeps the same 24 training tasks and frozen actors and changes
only private-generation seed 1729 to 1730. Maximum **72 calls / 18,432 output
tokens**. It generates no receiver revisions, final answers or training pairs.
It is implemented and CPU tested; real GPU execution remains unverified.
[Reason for the control](reviews/receiver-support-review-001.md).

Review, commit and push the new implementation first. Use that new full SHA below;
`b3951fde...` contains the completed receiver run, not this new command. Select the
same L4 runtime. Run these cells in order after a reset.

**1. Mount Drive and pin the new code**

```python
from pathlib import Path
import os, re, subprocess, sys
from google.colab import drive

GIT_REF = "PASTE_NEW_FULL_COMMIT_SHA"
REPO_URL = "https://github.com/Soqoro/Pact.git"
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
    raise RuntimeError("Preserve checkout changes before switching code.")
if git("-C", str(CHECKOUT), "remote", "get-url", "origin") != REPO_URL:
    raise RuntimeError("Checkout origin differs.")
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["HF_HOME"] = str(SCRATCH / "cache/huggingface")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
print("Pinned commit:", GIT_REF)
```

**2. Install, verify the parent ZIP and check the runtime**

This reuses the returned receiver ZIP to recover the frozen task selection and
baseline prompts. It does not prepare new training data or rerun the receiver screen.

```python
from pact.colab import install_dependencies, cpu_checks
install_dependencies(CHECKOUT)
cpu_checks(CHECKOUT)

from pact.training.private_control import (
    load_private_config, copy_private_source, private_control_plan, actor_recipe,
)
from pact.environment import runtime_fingerprint
import torch

CONFIG = CHECKOUT / "experiments/private_support_control.json"
config = load_private_config(CONFIG)
TIMEOUT = 120
BUNDLE = SCRATCH / "sources/qwen3-receiver-feasibility-001.zip"
SOURCE = Path(
    "/content/drive/MyDrive/PACT/receiver-feasibility/qwen3-receiver-feasibility-001/"
    "bundles/qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip"
)
print(copy_private_source(SOURCE, BUNDLE, config, timeout_seconds=TIMEOUT))
PLAN = private_control_plan(config, BUNDLE)
recipe = actor_recipe(PLAN)
print("Requests hash:", PLAN["requests_hash"])
print("Budget:", PLAN["budget"])
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert torch.cuda.is_bf16_supported()
print("GPU:", torch.cuda.get_device_name(0))
print("Expected runtime:", recipe.runtime_fingerprint)
print("Current runtime: ", runtime_fingerprint())
if runtime_fingerprint() != recipe.runtime_fingerprint:
    raise RuntimeError("Runtime mismatch: stop and report this output.")
```

**3. Restore and verify the existing actors**

The full completed warm-start snapshot is about 1.57 GB. The small review ZIP does
not contain weights. No new warm-start training is requested.

```python
from pact.training.colab import restore_snapshot
from pact.training.scoring import verify_references

WARMSTART = SCRATCH / "warmstart/qwen3-warmstart-001"
REFERENCES = WARMSTART / "references"
RUN = SCRATCH / "private-support/qwen3-private-support-control-001"
DURABLE = Path("/content/drive/MyDrive/PACT/private-support/qwen3-private-support-control-001")

if not WARMSTART.exists():
    print(restore_snapshot(
        "/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/"
        "snapshots/1789796424349439412-7eeb6af87200",
        WARMSTART, timeout_seconds=TIMEOUT,
    ))
verify_references(REFERENCES, recipe)
print("Frozen actors verified.")
```

**4. Execute or resume the private-only control**

Set `EXECUTE=True` to collect the declared 72 calls. Leave `STOP_AFTER=None` for
the full run; a positive integer requests a pause after that many new calls.
If scratch was reset, the cell attempts to restore the latest snapshot of this
new control. It never restores or extends the completed receiver run.

```python
import json
from pact.training.private_control import restore_private_control

EXECUTE = False
STOP_AFTER = None
if EXECUTE and not RUN.exists():
    snapshot_dir = DURABLE / "snapshots"
    snapshots = sorted(p for p in snapshot_dir.iterdir() if p.is_dir()) if snapshot_dir.exists() else []
    if snapshots:
        print(restore_private_control(snapshots[-1], RUN, timeout_seconds=TIMEOUT))

args = [
    sys.executable, "-u", "-m", "pact", "private-support-control",
    "--config", str(CONFIG), "--bundle", str(BUNDLE),
    "--references-dir", str(REFERENCES), "--run-dir", str(RUN),
    "--cache-dir", str(SCRATCH / "cache/models"),
    "--persistent", str(DURABLE), "--storage-timeout", str(TIMEOUT),
]
if EXECUTE:
    args.append("--execute")
    if RUN.exists():
        args.append("--resume")
    if STOP_AFTER is not None:
        args += ["--stop-after", str(STOP_AFTER)]

CONTROL_RESULT = None
with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end="", flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "exit_code" in value and "path" in value:
            CONTROL_RESULT = value
    exit_code = process.wait()
if CONTROL_RESULT:
    print("Local ZIP:", CONTROL_RESULT["path"])
    print("Drive ZIP:", CONTROL_RESULT.get("persistent_bundle"))
    print("SHA256:", CONTROL_RESULT["sha256"])
    print("Verified snapshot:", CONTROL_RESULT.get("persistent_snapshot"))
if exit_code:
    raise RuntimeError("Keep scratch and return the error and available ZIP before retrying.")
if EXECUTE:
    assert CONTROL_RESULT is not None, "Missing control receipt."
```

Expected full completion: `private_support_complete_local`, `completed_records=72`,
`committed_calls=72`, `exit_code=0`, `persistent_copy_verified=true`, and
`training_executed=false`. The report compares the two private draws separately.
It cannot establish receiver preference availability because it samples no revisions.

**5. Download and return the ZIP**

```python
from google.colab import files
assert CONTROL_RESULT is not None, "Execute the control first."
print("SHA256:", CONTROL_RESULT["sha256"])
print("Drive copy:", CONTROL_RESULT.get("persistent_bundle"))
files.download(CONTROL_RESULT["path"])
```

Upload to `results_import` and return the checksum and final receipt. Preserve
Drive snapshots and objects. A paused run can resume through cell 4; completed
calls are reused and retain the original cap. A completed run repeats with no
fresh generation if final persistence needs retrying.

Before a task's new calls the runner verifies a durable unsafe marker; after its
three calls or a handled pause it publishes a safe snapshot. An abrupt reset can
lose calls already charged to the budget, so restore rejects unsafe or older
snapshots. Local resume rejects any intent without a verified result. Return that
error for recovery review instead of deleting attempts or changing run IDs.
Each storage operation has its own 120-second deadline; a valid local ZIP is
created before final Drive operations. Current Drive contents and actual GPU
reset/resume remain unverified until returned evidence exercises those paths.
