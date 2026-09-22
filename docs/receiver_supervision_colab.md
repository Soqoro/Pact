# Receiver supervision v1: fresh or restarted Colab

This is a new training-only experiment, initialized from the completed 90-step
120-task preparation. It does not resume that preparation or rerun the 72-call
prompt diagnostic. Review and push this patch yourself; enter the resulting full
commit SHA below. Use the same L4/BF16 environment. Runtime fingerprint mismatch
is a blocker, not permission to change precision or dependencies.

The preset permits at most 1,296 generation calls / 322,560 reserved output tokens:
672 source/donor, 192 receiver/control, 96 private, 336 natural-team calls. Training
is at most 32 updates per trained arm, 512 total microbatch forward/backward calls
including anchors; teacher-forced evaluation adds at most 192 forwards. These are
ceilings, not wall-clock estimates. The frozen arm performs no new updates.

Run these cells in order. Each GPU stage is a subprocess; model memory is released
between arms. No gold prefix is supplied to free generation.

## 1. Mount and pin code

```python
from pathlib import Path
import os, re, subprocess, sys, json
from google.colab import drive
GIT_REF = "PASTE_FULL_SHA_OF_YOUR_REVIEWED_PUSH"
REPO_URL = "https://github.com/Soqoro/Pact.git"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF)
drive.mount("/content/drive")
SCRATCH = Path("/content/pact-scratch")
CHECKOUT = SCRATCH / "checkout"
SCRATCH.mkdir(parents=True, exist_ok=True)
def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()
if not CHECKOUT.exists():
    subprocess.run(["git", "clone", "--filter=blob:none", REPO_URL, str(CHECKOUT)], check=True)
assert not git("-C", str(CHECKOUT), "status", "--porcelain"), "Preserve local checkout edits first."
assert git("-C", str(CHECKOUT), "remote", "get-url", "origin") == REPO_URL
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["HF_HOME"] = str(SCRATCH / "cache/huggingface")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```

## 2. Install the existing pinned stack

```python
from pact.colab import install_dependencies
install_dependencies(CHECKOUT)
# Focused CPU checks; these do not download model weights.
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_receiver_supervision.py", "-v"], check=True)
```

## 3. Restore initialization weights and prepare the fixed training pool

The ZIP below is provenance metadata, **not weights**. Actual weights come from
`training/snapshots/1789930640656395583-479df47c14d9`. Compact restoration is accepted
only as initialization of this new study. It cannot resume either new optimizer.

```python
from pact.storage import storage_operation
from pact.training.preparation_restore import restore_preparation_references
from pact.training.receiver_supervision import load_rx_config, study_plan
from pact.training.receiver_study import initial_recipe
from pact.environment import runtime_fingerprint
from pact.util import file_hash
DRIVE = Path("/content/drive/MyDrive/PACT")
PREP = DRIVE / "actor-preparation/qwen3-preparation-120-001"
CONFIG = CHECKOUT / "experiments/receiver_supervision_v1.json"
SELECTION = CHECKOUT / "experiments/receiver_supervision_selection.json"
config = load_rx_config(CONFIG)
TRAIN_ZIP = SCRATCH / "sources/preparation-training.zip"
TRAIN_ZIP.parent.mkdir(parents=True, exist_ok=True)
if not TRAIN_ZIP.exists():
    print(storage_operation("bundle-restore",
        PREP / "training/bundles/qwen3-preparation-120-001-handoff-1789930640697369191.zip",
        TRAIN_ZIP, sha256=config.initialization_bundle_sha256, timeout_seconds=600))
assert file_hash(TRAIN_ZIP) == config.initialization_bundle_sha256
INITIAL = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
if not INITIAL.exists():
    print(restore_preparation_references(
        PREP / "training/snapshots/1789930640656395583-479df47c14d9",
        INITIAL, timeout_seconds=600))
DATA = SCRATCH / "training-data/proposal-1200"
if not DATA.exists():
    subprocess.run([sys.executable, "-m", "pact", "prepare-training-data",
        "--cache-dir", str(SCRATCH / "cache/datasets"), "--output-dir", str(DATA),
        "--items", "1200", "--seed", "20260918", "--download"], check=True)
PLAN = study_plan(config, DATA, TRAIN_ZIP, SELECTION)
initial_recipe(PLAN, INITIAL)  # checks actual adapter files; no model load
print("Budget:", PLAN["budget"])
print("Runtime:", runtime_fingerprint())
assert runtime_fingerprint() == PLAN["model"]["runtime_fingerprint"], "Runtime changed; return this output for review."
```

## 4. Freeze the study or restore its latest verified snapshot

Keep the same run ID. Do not delete an incomplete run and start again to reset its
budget. A reset restores the complete new-study snapshot, including optimizer/RNG
state. An unsafe latest snapshot stops for review rather than falling back to an
older snapshot that might repeat lost calls. On the same live scratch disk, complete
journals/checkpoints can prove an interrupted operation committed successfully.

```python
RUN_ID = "qwen3-receiver-supervision-001"
RUN = SCRATCH / "receiver-supervision" / RUN_ID
PERSISTENT = DRIVE / "receiver-supervision" / RUN_ID
COMMON = ["--config", str(CONFIG), "--data-dir", str(DATA),
    "--initialization-bundle", str(TRAIN_ZIP), "--initialization-root", str(INITIAL),
    "--selection", str(SELECTION), "--run-dir", str(RUN),
    "--persistent", str(PERSISTENT), "--cache-dir", str(SCRATCH / "cache")]
def study(stage, *options):
    subprocess.run([sys.executable, "-m", "pact.training.receiver_study",
                    stage, *COMMON, *options], check=True)
study("plan")  # dry run, no model load or generation
if not RUN.exists():
    snapshots = sorted((PERSISTENT / "snapshots").glob("*"))
    if snapshots:
        study("restore", "--snapshot", str(snapshots[-1]))
    else:
        study("plan", "--execute")  # freezes membership and verifies persistence
```

## 5. Prepare bounded contexts

Already committed calls are revalidated and reused. No receiver positive/negative
sampling is needed. All source tasks get three initial packets and four draws from
one predesignated focal donor. Unsupported contexts are retained in the audit.

```python
from pact.util import read_json
if not (RUN / "contexts.json").exists():
    study("contexts", "--execute")
CONTEXTS = read_json(RUN / "contexts.json")
print({p: {k: v for k, v in part.items() if k != "records"}
       for p, part in CONTEXTS["partitions"].items()})
if CONTEXTS["status"] != "ready":
    study("export")
    raise RuntimeError("insufficient_context_support: return the ZIP; do not add draws or replace tasks.")
assert (RUN / "target_masks.json").exists(), "Context preflight incomplete; rerun contexts on the same scratch run."
```

## 6. Train the two comparison arms

Both start from the same three prepared adapters, but update **only agent0**.
`--resume` consumes only this new arm's own checkpoint. A completed arm runs zero
additional updates. Do not view held-out model outcomes or choose a checkpoint
between these commands.

```python
for arm in ("task_sft", "receiver_sft"):
    arm_root = RUN / "training" / arm
    options = ["--arm", arm, "--execute"]
    if (arm_root / "run.json").exists():
        options.append("--resume")
    study("train", *options)
    assert read_json(arm_root / "status.json")["complete"]
```

## 7. Evaluate all three arms

Both trained arms must be complete before **any** held-out evaluation. Evaluation
uses the declared last checkpoint, normal complete-packet generation, frozen-history
full/peer-withheld contexts, 32 natural private answers per arm, and eight naturally
generated teams per arm under clean/exchange. No all-agent refresh or final test.

```python
for arm in ("frozen", "task_sft", "receiver_sft"):
    study("evaluate", "--arm", arm, "--execute")
```

## 8. Report and return the review bundle

```python
study("report")
REPORT = read_json(RUN / "report.json")
print(REPORT["generation_accounting"])
print(REPORT["paired_receiver_transitions"])
print(REPORT["paired_peer_effects"])
print("Drive bundles:", PERSISTENT / "bundles")
# The report command prints the exact ZIP, SHA256, full snapshot and Drive copy.
# Download the newest review ZIP, then upload it for local audit.
from google.colab import files
latest = max((RUN.parent / "bundles").glob(f"{RUN_ID}-*.zip"), key=lambda p: p.stat().st_mtime_ns)
print("Review:", latest, "SHA256:", file_hash(latest))
files.download(str(latest))
```

The full new-study snapshot retains `training/task_sft/checkpoints` and
`training/receiver_sft/checkpoints`, including optimizer and RNG. Evaluation exports
are `training/{arm}/references/agent{0,1,2}`. The original prepared references remain
at `INITIAL/references/agent{0,1,2}`. Review ZIPs omit tensor payloads; their inventory
and handoff identify full snapshots and checkpoint paths.

Expected metadata: `plan.json`, `recipe.json`, `state.json`, `environment.json`,
`contexts/shards`, attempted-call journals and token traces, `contexts.json`,
`target_masks.json`, arm `examples.json` / `run.json` / `status.json`, immutable
checkpoint metadata, evaluation shards/CE records, `report.json`, resource records,
`CODEX_HANDOFF.md`, `CODEX_HANDOFF.json`, and review checksums. Unknown billed compute
units stay null. Natural and curated results are separate; teacher-forced CE is not
free-generation accuracy.

Drive operations have a 120-second deadline (restore: 600 seconds). Many files can
still make Drive slow. A local recovery ZIP is produced on failure; do not interpret
it as proof that tensor checkpoints reached Drive. Preserve it and return the error.
No change to runtime, context length, seed budget or missing-support gate is automatic.
