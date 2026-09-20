# Bounded actor preparation: fresh Colab runtime

Review, commit and push the implementation, then pin that new full SHA below.
Use the same L4 runtime. The old `43151280...` commit lacks these commands.
The [frozen design](actor_preparation_design.md) permits exactly 90 training
updates and 104 probe generations. This path is CPU tested; larger GPU training,
actual new-example lengths and GPU reset/resume remain unverified.

Run cells in order. Training and probing execute in separate child processes,
so the training model is released before probe loading. The two execution flags
default to false; set each to true when ready for its stage. Keep the same SHA,
run paths and configuration on resume.

The full training snapshot contains optimizer/RNG checkpoints and weights; the
small ZIP does not. Ninety updates retain more checkpoint data than the previous
nine-update warm start. The restore limit is 20 GiB; actual storage/time is not yet
measured. Snapshots are verified every ten updates and after handled completion
or pause. Every storage operation has a 120-second deadline. On failure, preserve
scratch and return the error/local ZIP; do not discard checkpoints or enlarge the
recipe. A reset may require restoring the last verified training checkpoint.

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

**2. Install and check CPU dependencies**

```python
from pact.colab import install_dependencies, cpu_checks
install_dependencies(CHECKOUT)
cpu_checks(CHECKOUT)
```

**3. Recover the pinned data and completed source ZIPs**

The data commands fetch only the already pinned training/validation source files
if needed. They do not run a model or access final-test data.

```python
from pact.training.actor_preparation import load_actor_preparation_config, actor_preparation_plan
from pact.storage import storage_operation
from pact.util import file_hash, read_json, canonical
from pact.environment import runtime_fingerprint
import torch

CONFIG = CHECKOUT / "experiments/actor_preparation_120.json"
config = load_actor_preparation_config(CONFIG)
TIMEOUT = 120
DATA = SCRATCH / "training-data/proposal-1200"
OLD_DATA = SCRATCH / "training-data/engineering-12"
for target, count in ((DATA, 1200), (OLD_DATA, 12)):
    if not target.exists():
        subprocess.run([
            sys.executable, "-u", "-m", "pact", "prepare-training-data",
            "--cache-dir", str(SCRATCH / "cache/training-sources"),
            "--output-dir", str(target), "--items", str(count),
            "--seed", "20260918", "--download",
        ], check=True, cwd=CHECKOUT)

RECEIVER = SCRATCH / "sources/receiver.zip"
PRIVATE = SCRATCH / "sources/private.zip"
CURATED = SCRATCH / "sources/curated.zip"
sources = [
    ("receiver-feasibility/qwen3-receiver-feasibility-001/bundles/"
     "qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip",
     RECEIVER, config.receiver_bundle_sha256),
    ("private-support/qwen3-private-support-control-001/bundles/"
     "qwen3-private-support-control-001-handoff-1789909726537323854.zip",
     PRIVATE, config.private_bundle_sha256),
    ("curated-repair/qwen3-curated-repair-001/bundles/"
     "qwen3-curated-repair-001-handoff-1789919214853319498.zip",
     CURATED, config.curated_bundle_sha256),
]
for relative, target, expected in sources:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(storage_operation(
            "bundle-restore", Path("/content/drive/MyDrive/PACT") / relative,
            target, sha256=expected, timeout_seconds=TIMEOUT,
        ))
    assert file_hash(target) == expected, "Source archive checksum mismatch."

PLAN = actor_preparation_plan(config, DATA, OLD_DATA, RECEIVER, PRIVATE, CURATED)
selection = read_json(CHECKOUT / "experiments/actor_preparation_selection.json")
assert PLAN["selection_hash"] == selection["selection_hash"]
assert canonical(PLAN["selection"]) == canonical(selection["selected"])
print("Selection:", PLAN["selection_hash"])
print("Budget:", PLAN["budget"])
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert torch.cuda.is_bf16_supported()
print("GPU:", torch.cuda.get_device_name(0))
print("Runtime:", runtime_fingerprint())
assert runtime_fingerprint() == PLAN["baseline_models"]["base"]["runtime_fingerprint"], "Runtime changed; stop and return this output."
```

**4. Define the stage commands and output streaming**

```python
import json

TRAIN = SCRATCH / "actor-preparation/qwen3-preparation-120-001"
PROBE = SCRATCH / "actor-preparation/qwen3-preparation-probe-001"
DURABLE = Path("/content/drive/MyDrive/PACT/actor-preparation/qwen3-preparation-120-001")
BASE_ARGS = [
    sys.executable, "-u", "-m", "pact", "actor-preparation",
    "--config", str(CONFIG), "--data-dir", str(DATA),
    "--warmstart-data-dir", str(OLD_DATA),
    "--receiver-bundle", str(RECEIVER), "--private-bundle", str(PRIVATE),
    "--curated-bundle", str(CURATED),
    "--cache-dir", str(SCRATCH / "cache/models"),
    "--storage-timeout", str(TIMEOUT),
]

def latest_snapshot(path):
    folder = path / "snapshots"
    values = sorted(p for p in folder.iterdir() if p.is_dir()) if folder.exists() else []
    return values[-1] if values else None

def run_stage(args):
    result = None
    with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
        for line in process.stdout:
            print(line, end="", flush=True)
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and "exit_code" in value and "path" in value:
                result = value
        code = process.wait()
    if result:
        print("Local ZIP:", result["path"])
        print("Drive ZIP:", result.get("persistent_bundle"))
        print("SHA256:", result["sha256"])
    if code:
        raise RuntimeError("Stage failed. Preserve scratch and return the error and available ZIP.")
    return result
```

**5. Train or resume the fixed 90-update preparation**

This starts fresh adapters; it does not restore the old nine-step warm start.
`STOP_AFTER_UPDATES` can request a handled pause after that many new updates;
it does not increase the total 90-update budget. Leave it `None` for completion.

```python
from pact.training.colab import restore_snapshot

EXECUTE_TRAIN = False  # Set True to train the declared recipe.
STOP_AFTER_UPDATES = None
if EXECUTE_TRAIN and not TRAIN.exists():
    saved = latest_snapshot(DURABLE / "training")
    if saved is not None:
        print(restore_snapshot(saved, TRAIN, timeout_seconds=TIMEOUT))

args = BASE_ARGS + ["--stage", "training", "--run-dir", str(TRAIN),
                    "--persistent", str(DURABLE / "training")]
if EXECUTE_TRAIN:
    args.append("--execute")
    if TRAIN.exists():
        args.append("--resume")
    if STOP_AFTER_UPDATES is not None:
        args += ["--stop-after", str(STOP_AFTER_UPDATES)]
TRAIN_RESULT = run_stage(args)
if EXECUTE_TRAIN:
    assert TRAIN_RESULT is not None
    print("Training status:", TRAIN_RESULT.get("status"))
```

Full training completion requires `status.status=warmstart_updates_complete`,
`status.completed_steps=90`, `exit_code=0`, verified durable copying, and three
final reference exports. A handled pause is not completion. Finish cell 5 before
executing cell 6. Return any failure for review without moving to probing.

**6. Run or resume the fixed 104-call probe**

The runner verifies and durably copies final training checkpoints/references
before loading the probe model. It then generates 72 private responses and 32
receiver responses with the new frozen actors. Receiver histories remain the
old saved states and donors; new private outputs do not enter those prompts.

```python
from pact.training.preparation_probe import restore_preparation_probe

EXECUTE_PROBE = False  # Set True only after training completes.
STOP_AFTER_CALLS = None
if EXECUTE_PROBE and not TRAIN.exists():
    saved = latest_snapshot(DURABLE / "training")
    assert saved is not None, "No saved preparation training snapshot."
    print(restore_snapshot(saved, TRAIN, timeout_seconds=TIMEOUT))
if EXECUTE_PROBE and not PROBE.exists():
    saved = latest_snapshot(DURABLE / "probe")
    if saved is not None:
        print(restore_preparation_probe(saved, PROBE, timeout_seconds=TIMEOUT))

args = BASE_ARGS + ["--stage", "probe", "--training-root", str(TRAIN),
                    "--run-dir", str(PROBE), "--persistent", str(DURABLE / "probe")]
if EXECUTE_PROBE:
    args.append("--execute")
    if PROBE.exists():
        args.append("--resume")
    if STOP_AFTER_CALLS is not None:
        args += ["--stop-after", str(STOP_AFTER_CALLS)]
PROBE_RESULT = run_stage(args)
if EXECUTE_PROBE:
    assert PROBE_RESULT is not None
    print("Probe status:", PROBE_RESULT["status"])
```

Expected complete probe: `preparation_probe_complete_local`, 104 completed
records/calls, `exit_code=0`, verified durable copying and `training_executed=false`
for this inference stage. `full_pact_ready` stays false. An unsafe snapshot or
ambiguous attempted call requires review; do not delete it or start a replacement
run to reset the budget. Completed reruns reuse cached calls.

**7. Download both review ZIPs**

```python
from google.colab import files

for name, result in (("training", TRAIN_RESULT), ("probe", PROBE_RESULT)):
    assert result is not None, f"Execute {name} first."
    print(name, "SHA256:", result["sha256"])
    print("Drive copy:", result.get("persistent_bundle"))
    files.download(result["path"])
```

Return both ZIPs, checksums and final receipts. If a kernel reset clears these
variables, the verified ZIPs remain in the corresponding Drive `bundles` folders;
download those files directly. Preserve the full training snapshots/object store.
Review ZIPs are metadata only and cannot replace the weights needed for recovery.
