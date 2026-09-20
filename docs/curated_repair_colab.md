# Curated helpful-peer diagnostic: fresh Colab runtime

**Completed:** [returned run audit](reviews/qwen3-curated-repair-001.md) verifies
32/32 calls and zero within-prompt pairs. Preserve the completed run; do not rerun
it. These cells document its procedure. GPU reset/resume remains unverified.

Review, commit and push the new implementation first, then use its full SHA in
cell 1. Commit `91655a83503a466c4f773a49053d86b54fb71cab` does not include this
command. Select the same L4 runtime as the completed controls.

The [frozen design](curated_repair_design.md) uses two post-selected ARC tasks,
eight fixed prompts and **32 revision calls maximum / 8,192 output tokens**.
All three saved private states remain fixed. Only the outgoing text from the
selected sender changes. There is no training, new private sampling or readout.
Actual GPU execution and tokenized prompt fit now pass returned artifact audit.
GPU reset/resume remains unverified.

Run these five cells in order. Cell 4 defaults to planning; set `EXECUTE=True`
when ready to run the declared diagnostic. Keep the same code SHA on resume.

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

This verifies both completed source archives on scratch. It does not prepare new
training data or rerun either completed control.

```python
from pact.colab import install_dependencies, cpu_checks
install_dependencies(CHECKOUT)
cpu_checks(CHECKOUT)

from pact.training.curated_repair import load_curated_config, curated_repair_plan
from pact.training.private_control import actor_recipe
from pact.storage import storage_operation
from pact.util import file_hash
from pact.environment import runtime_fingerprint
import torch

CONFIG = CHECKOUT / "experiments/curated_repair.json"
config = load_curated_config(CONFIG)
TIMEOUT = 120
RECEIVER_BUNDLE = SCRATCH / "sources/qwen3-receiver-feasibility-001.zip"
PRIVATE_BUNDLE = SCRATCH / "sources/qwen3-private-support-control-001.zip"
sources = [
    ("/content/drive/MyDrive/PACT/receiver-feasibility/qwen3-receiver-feasibility-001/"
     "bundles/qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip",
     RECEIVER_BUNDLE, config.receiver_bundle_sha256),
    ("/content/drive/MyDrive/PACT/private-support/qwen3-private-support-control-001/"
     "bundles/qwen3-private-support-control-001-handoff-1789909726537323854.zip",
     PRIVATE_BUNDLE, config.private_bundle_sha256),
]
for source, target, expected in sources:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(storage_operation("bundle-restore", Path(source), target,
                                timeout_seconds=TIMEOUT, sha256=expected))
    assert file_hash(target) == expected, "Source ZIP checksum mismatch."
PLAN = curated_repair_plan(config, RECEIVER_BUNDLE, PRIVATE_BUNDLE)
recipe = actor_recipe(PLAN)
assert PLAN["contexts_hash"] == "66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab"
print("Contexts hash:", PLAN["contexts_hash"])
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
RUN = SCRATCH / "curated-repair/qwen3-curated-repair-001"
DURABLE = Path("/content/drive/MyDrive/PACT/curated-repair/qwen3-curated-repair-001")

if not WARMSTART.exists():
    print(restore_snapshot(
        "/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/"
        "snapshots/1789796424349439412-7eeb6af87200",
        WARMSTART, timeout_seconds=TIMEOUT,
    ))
verify_references(REFERENCES, recipe)
print("Frozen actors verified.")
```

**4. Execute or resume the curated diagnostic**

Set `EXECUTE=True` to collect the declared 32 calls. Leave `STOP_AFTER=None` for
the full run; a positive integer requests a pause after that many new calls.
If scratch was reset, the cell attempts to restore the latest snapshot of this
new diagnostic. It never restores or extends the completed receiver run.

```python
import json
from pact.training.curated_runner import restore_curated_repair

EXECUTE = False
STOP_AFTER = None
if EXECUTE and not RUN.exists():
    snapshot_dir = DURABLE / "snapshots"
    snapshots = sorted(p for p in snapshot_dir.iterdir() if p.is_dir()) if snapshot_dir.exists() else []
    if snapshots:
        print(restore_curated_repair(snapshots[-1], RUN, timeout_seconds=TIMEOUT))

args = [
    sys.executable, "-u", "-m", "pact", "curated-repair",
    "--config", str(CONFIG), "--receiver-bundle", str(RECEIVER_BUNDLE),
    "--private-bundle", str(PRIVATE_BUNDLE),
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

CURATED_RESULT = None
with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end="", flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "exit_code" in value and "path" in value:
            CURATED_RESULT = value
    exit_code = process.wait()
if CURATED_RESULT:
    print("Local ZIP:", CURATED_RESULT["path"])
    print("Drive ZIP:", CURATED_RESULT.get("persistent_bundle"))
    print("SHA256:", CURATED_RESULT["sha256"])
    print("Verified snapshot:", CURATED_RESULT.get("persistent_snapshot"))
if exit_code:
    raise RuntimeError("Keep scratch and return the error and available ZIP before retrying.")
if EXECUTE:
    assert CURATED_RESULT is not None, "Missing diagnostic receipt."
```

Expected full completion: `curated_repair_complete_local`, `completed_records=32`,
`committed_calls=32`, `exit_code=0`, `persistent_copy_verified=true`, and
`training_executed=false`. The report has eight within-arm pools, four recipient
comparisons and 16 matched seed comparisons. A completed diagnostic still has
`full_pact_ready=false`, regardless of pair availability.

**5. Download and return the ZIP**

```python
from google.colab import files
assert CURATED_RESULT is not None, "Execute the diagnostic first."
print("SHA256:", CURATED_RESULT["sha256"])
print("Drive copy:", CURATED_RESULT.get("persistent_bundle"))
files.download(CURATED_RESULT["path"])
```

Upload to `results_import` and return the checksum and final receipt. Preserve
Drive snapshots and objects. A paused run can resume through cell 4; completed
calls are reused and retain the original cap. A completed run repeats with no
fresh generation if final persistence needs retrying.

Before a recipient's new calls the runner verifies a durable unsafe marker; after its
eight calls (both arms) or a handled pause it publishes a safe snapshot. An abrupt reset can
lose calls already charged to the budget, so restore rejects unsafe or older
snapshots. Local resume rejects any intent without a verified result. Return that
error for recovery review instead of deleting attempts or changing run IDs.
Each storage operation has its own 120-second deadline; a valid local ZIP is
created before final Drive operations. Current Drive contents and actual GPU
reset/resume remain unverified until returned evidence exercises those paths.
