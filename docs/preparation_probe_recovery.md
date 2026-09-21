# Recover the preparation probe after the full-restore timeout

The supplied receipt reports successful 90-update training with verified final
snapshot `1789930640656395583-479df47c14d9`. The full restore later exceeded 600
seconds. This procedure restores only the final inference adapters and metadata,
then runs/resumes the same 104-call probe. **It never retrains.**

First review, commit and push the storage repair. Use that new full SHA in cell 1,
not `ff349969...`, which lacks the compact restore. Restart the Colab session to
clear cached Python imports, select the same L4, and run these seven cells.
Actual Drive recovery on this new path remains unverified until returned evidence.

The new code explicitly accepts the exact reviewed training source
`ff349969996b2066979529b2f43d773f5a1b88e6` with executable hash
`6e0b6512f014c6f5cbda44de04b198a65c0e67b7a5f5254f69620c4812c4815a`.
If a probe journal exists from that source, its plan/model/config must be identical;
verified calls and attempts are retained, with a source-migration record. There is
no budget reset. Unsafe snapshots or unresolved calls still stop recovery. Do not
fall back to an older probe snapshot or a replacement run ID.

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
TIMEOUT = 600
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

**5. Restore only the completed inference exports**

Training already completed. Restore the final adapters and verified metadata to
a new scratch directory. Do not retry the full optimizer-history restore or
delete its partial staging directories while a storage worker may still be alive.
This compact directory is explicitly inference-only and cannot resume training.

```python
from pact.training.preparation_restore import restore_preparation_references
from pact.training.preparation_runner import preparation_references

TRAIN = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
TRAIN_SNAPSHOT = DURABLE / "training/snapshots/1789930640656395583-479df47c14d9"
if not TRAIN.exists():
    print(restore_preparation_references(
        TRAIN_SNAPSHOT, TRAIN, timeout_seconds=TIMEOUT,
    ))
recipe = preparation_references(PLAN, TRAIN)
print("Final 90-step adapters verified:", recipe.reference_hashes)
```

This copies 12 selected files plus snapshot proof files, without reading the
optimizer tensor objects. It validates all selected file hashes, final-step
metadata, training order/log, source provenance and adapter architecture/hashes.
It does not re-verify omitted historical optimizer tensors. The three adapter
hashes should be:

- `30838afc94ae2c3367ed7b4ef2477c2bc3e25944f9992ed70f3708a49780ec19`
- `ceb8d513127bd526d7be4621384aa25de6ccff6247c6f00ae2312d898dcf9e37`
- `be5e6b7b46e608ad6cecfd80b42f607b855307993f001586daed69763c72e28e`

**6. Run or resume the fixed 104-call probe**

The runner verifies and durably copies the compact inference export to its own
`inference` folder before loading the probe model. It preserves the original
full training snapshot and does not copy its optimizer history again. It then generates 72 private responses and 32
receiver responses with the new frozen actors. Receiver histories remain the
old saved states and donors; new private outputs do not enter those prompts.

```python
from pact.training.preparation_probe import restore_preparation_probe

EXECUTE_PROBE = True  # Training already completed; run/resume inference only.
STOP_AFTER_CALLS = None
assert TRAIN.exists(), "Run cell 5 to restore the inference exports first."
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

**7. Download the existing training ZIP and new probe ZIP**

```python
from google.colab import files

TRAIN_ZIP = SCRATCH / "bundles/completed-preparation-training.zip"
TRAIN_SHA = "a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388"
TRAIN_DRIVE_ZIP = DURABLE / "training/bundles/qwen3-preparation-120-001-handoff-1789930640697369191.zip"
TRAIN_ZIP.parent.mkdir(parents=True, exist_ok=True)
if not TRAIN_ZIP.exists():
    print(storage_operation("bundle-restore", TRAIN_DRIVE_ZIP, TRAIN_ZIP,
                            sha256=TRAIN_SHA, timeout_seconds=TIMEOUT))
assert file_hash(TRAIN_ZIP) == TRAIN_SHA
print("Training SHA256:", TRAIN_SHA)
files.download(str(TRAIN_ZIP))
assert PROBE_RESULT is not None, "Complete cell 6 first."
print("Probe SHA256:", PROBE_RESULT["sha256"])
print("Probe Drive copy:", PROBE_RESULT.get("persistent_bundle"))
files.download(PROBE_RESULT["path"])
```

Return both ZIPs, checksums and the final probe receipt. No training command is
included in this recovery procedure. Preserve the original full Drive training
snapshot and all probe journals/snapshots.
