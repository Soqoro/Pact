# Replacement training: fresh Colab sequence

Use the same GPU/runtime as the original scratch run. Exact runtime mismatches stop;
do not overwrite access receipts. Set the full new pushed commit SHA in cell 1.
These cells authorize no evaluation, Stage II, collection or scratch rerun. They
execute the reviewed additional 768-update replacement attempt on the original bank.
The interrupted parent is never restored or overwritten.

Required input is the parent **PRIVATE** ZIP at the path in cell 1. No trained
parent checkpoint or RECOVERY ZIP is needed: original initialization is recreated
and verified against the retained Q/L/M scratch receipts. Model weights are fetched
from the original pinned official repositories after HF authorization. The cache
repair cell handles the already diagnosed Mistral pointer issue without changing
revision or expected payload hash.

Review [the replacement plan](revival_replacement_plan.md) and retained history.
Drive's account quota is not reported reliably by mount free-space checks; the
child uses a 32 GiB object cap, but explicit exports and metadata need additional
space. Capacity projection is a structural estimate, not a measured GPU guarantee.

## Cell 1

```python
from pathlib import Path
import os, sys, re, subprocess, json, hashlib, shutil, time
from google.colab import drive
drive.mount("/content/drive")

GIT_REF = "SET_FULL_REVIEWED_COMMIT_SHA"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF), "Set your pushed full commit SHA."
REPO_URL = "https://github.com/Soqoro/Pact.git"
SCRATCH = Path("/content/pact-replacement")
CHECKOUT = SCRATCH / ("checkout-" + GIT_REF[:12])
RUN_ID = "pact-heterogeneous-receiver-training-replacement-002"
RUN = SCRATCH / "runs" / RUN_ID
CACHE = SCRATCH / "cache"
PERSISTENT = Path("/content/drive/MyDrive/PACT/revival") / RUN_ID
PARENT = Path("/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-001/bundles/pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip")
PARENT_SHA = "f9a78141d0c662c06be903b49318f0235f6253d11e42f5bb17b2dd8adf9f2793"
REVIEW_SHA = "a67a7000801c4c96d19cd3b6d8521ee9d5fa9f5b2305c101eded1e11b4a066a3"
SCRATCH.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(["git", "clone", REPO_URL, str(CHECKOUT)], check=True)
assert subprocess.check_output(["git", "-C", str(CHECKOUT), "remote", "get-url", "origin"], text=True).strip() == REPO_URL
assert not subprocess.check_output(["git", "-C", str(CHECKOUT), "status", "--porcelain"], text=True).strip(), "Preserve local checkout changes."
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert subprocess.check_output(["git", "-C", str(CHECKOUT), "rev-parse", "HEAD"], text=True).strip().lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
```

## Cell 2

```python
subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[model]"], check=True)
from google.colab import userdata
if not os.environ.get("HF_TOKEN"):
    os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
assert os.environ.get("HF_TOKEN"), "Authorized HF_TOKEN secret required."
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "0"
sys.path.insert(0, str(CHECKOUT / "src"))
subprocess.run([sys.executable, "-c", "import torch; from transformers import AutoTokenizer, AutoModelForCausalLM; assert torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.cuda.is_bf16_supported(); print('GPU:', torch.cuda.get_device_name(0)); print('Fresh-process imports OK')"], check=True)
```

## Cell 3

```python
from pact.util import read_json, digest, file_hash, redact

def study(stage, *options):
    command = [sys.executable, "-u", "-m", "pact.revival.replacement", stage,
               "--run-dir", str(RUN), "--cache-dir", str(CACHE),
               "--persistent", str(PERSISTENT), *map(str, options)]
    log = SCRATCH / f"replacement-{stage}-{time.time_ns()}.log"
    print("Starting:", stage, "Log:", log, flush=True)
    with log.open("w") as output:
        process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
    position = 0
    last_notice = time.monotonic()
    while True:
        with log.open(errors="replace") as stream:
            stream.seek(position)
            text = stream.read()
            position = stream.tell()
        if text:
            print(redact(text), end="", flush=True)
            last_notice = time.monotonic()
        if process.poll() is not None:
            with log.open(errors="replace") as stream:
                stream.seek(position)
                print(redact(stream.read()), end="", flush=True)
            break
        if time.monotonic() - last_notice > 30:
            print(stage, "still running; log:", log, flush=True)
            last_notice = time.monotonic()
        time.sleep(1)
    if process.returncode:
        raise RuntimeError(f"{stage} stopped ({process.returncode}). Preserve scratch and log; no automatic retry.")
    print("Finished:", stage, flush=True)
```

## Cell 4

```python
# New import or latest CHILD restoration only. Never select a parent snapshot.
if RUN.exists():
    assert (RUN / "plan.json").is_file(), "Partial child import: preserve and inspect."
    study("inspect")
elif PERSISTENT.exists() and any(PERSISTENT.iterdir()):
    study("restore")
else:
    assert PARENT.is_file(), "Exact parent PRIVATE bank bundle missing."
    assert file_hash(PARENT) == PARENT_SHA
    local_parent = SCRATCH / "parent-private.zip"
    shutil.copyfile(PARENT, local_parent)
    assert file_hash(local_parent) == PARENT_SHA
    study("import-parent", "--parent-private", local_parent, "--review-sha256", REVIEW_SHA)
PLAN_HASH = digest(read_json(RUN / "plan.json"))
print("Child plan:", PLAN_HASH)
study("inspect")
```

## Cell 5

```python
# Official Mistral pointer workaround verifies raw Git and payload hashes.
# It changes only the local model cache, never the frozen model identity.
study("repair-tokenizer-cache", "--execute", "--plan-hash", PLAN_HASH)
# Loads Q/L/M one at a time and checks native weights + original adapter hashes.
# No generation or training forwards.
study("preflight", "--execute", "--plan-hash", PLAN_HASH)
```

## Cell 6

```python
# One INCLUDED optimizer update; do not repeat completed work.
arm = "independent_adversarial_sft"
folder = RUN / "training" / arm / "Q"
status = read_json(folder / "status.json") if (folder / "status.json").exists() else {}
if status.get("completed_steps", 0) == 0:
    options = ["--arm", arm, "--family", "Q", "--stop-after", "1", "--execute", "--plan-hash", PLAN_HASH]
    if (folder / "contract.json").exists():
        options.append("--resume")
    study("train-agent", *options)
study("report")
assert read_json(RUN / "summary.json")["recovery_safe"], "Stop: unresolved update."
```

## Cell 7

```python
# Complete exactly the six reviewed fits, retaining the included first update.
for arm in ("independent_adversarial_sft", "uniform_joint_sft"):
    for family in ("Q", "L", "M"):
        folder = RUN / "training" / arm / family
        status = read_json(folder / "status.json") if (folder / "status.json").exists() else {}
        if status.get("complete"):
            print("Already complete:", arm, family, flush=True)
            continue
        options = ["--arm", arm, "--family", family, "--execute", "--plan-hash", PLAN_HASH]
        if (folder / "contract.json").exists():
            options.append("--resume")
        study("train-agent", *options)
        study("report")
```

## Cell 8

```python
study("report")
summary = read_json(RUN / "summary.json")
print(json.dumps(summary, indent=2))
assert summary["training_complete"] and summary["new_work"]["committed_updates"] == 768
assert summary["new_work"]["generation_calls"] == 0
study("export")
print("Return the PRIVATE and SANITIZED ZIPs printed above.")
print("Keep RECOVERY on Drive; it contains real adapter/optimizer tensors.")
print("No evaluation or Stage II is authorized by these cells.")
```

## Outputs and reset handling

Outputs live under the distinct replacement root printed in cell 1. Training
checkpoints are `training/{arm}/{Q,L,M}/checkpoints/step-NNNNNN/`; each completed
fit has `epoch1.json`, `epoch2.json` and `status.json`. The review ZIP excludes
tensors; the RECOVERY ZIP contains latest and epoch tensors. SANITIZED contains
aggregate summary only. Old parent calls stay byte-identical inside
`parent-private.zip`; their plan identity is not rewritten.

After a reset, use this same commit and rerun cells in order. Cell 4 restores only
the latest verified child snapshot. Pending markers, unsafe updates, incomplete
latest snapshots, source/runtime mismatch or missing protected objects stop the
sequence; do not delete markers, fall back or choose an older snapshot. If cell 7
stops, preserve its log and scratch. No automatic retry or runtime migration.

Fresh-process preflight/training prevents stale notebook Transformers imports.
The notebook uses no torch/model imports in the notebook kernel itself. Optional
CPU neural tests use locally initialized models only. Real child GPU/Drive behavior
remains unverified until returned execution evidence is audited.
