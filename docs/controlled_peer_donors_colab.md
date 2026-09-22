# Controlled peer donors v1: fresh or restarted Colab

This NEW child study imports the completed parent collection read-only. It does not
repeat preparation, the 672 parent calls, or the closed prompt control. The source
is `controlled_peer_donors_v1`; the objective remains `receiver_supervision_v1`.
Donors are offline label-conditioned synthetic messages, with unreviewed rationales.
Use the same audited runtime; incompatible runtime fingerprints stop execution.
Review and push the implementation yourself, then fill in the resulting full SHA.

Ceilings: 384 donor calls (98,304 output reservation), 288 controlled receiver calls
(73,728), 96 natural private calls (24,576), 336 natural team calls (76,800).
Total **1,104 / 273,408**. At most 32 updates per trained arm, 64 combined; 512
training forward/backward microbatches including 256 anchors; 288 separate CE
forwards. Actual schedules and input costs are logged separately. No extra GPU
smoke calls. Support minima are 8 fit / 4 held-out distinct tasks **per stratum**.
Missing opposite donors do not disqualify primary support.

Cells 5–7 require explicit switches, initially false. Run the stages in order;
review the frozen plan before setting acquisition true. All learning/evaluation
remains GPU-unverified. A support stop exports evidence and authorizes no training.

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
                "-p", "test_controlled_donors.py", "-v"], check=True)
```

## 3. Restore initialization weights and prepare the fixed training pool

The ZIP below is provenance metadata, **not weights**. Actual weights come from
`training/snapshots/1789930640656395583-479df47c14d9`. Compact restoration is accepted
only as initialization of this new study. It cannot resume either new optimizer.

```python
from pact.storage import storage_operation
from pact.training.preparation_restore import restore_preparation_references
from pact.training.controlled_donors import load_config as load_rx_config
from pact.training.controlled_donors import plan as controlled_plan, PARENT_SHA
from pact.training.receiver_study import initial_recipe
from pact.environment import runtime_fingerprint
from pact.util import file_hash
DRIVE = Path("/content/drive/MyDrive/PACT")
PREP = DRIVE / "actor-preparation/qwen3-preparation-120-001"
CONFIG = CHECKOUT / "experiments/controlled_peer_donors_v1.json"
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
PARENT_ZIP = SCRATCH / "sources/receiver-parent.zip"
if not PARENT_ZIP.exists():
    print(storage_operation("bundle-restore",
        DRIVE / "receiver-supervision/qwen3-receiver-supervision-001/bundles/qwen3-receiver-supervision-001-handoff-1790063068160794241.zip",
        PARENT_ZIP, sha256=PARENT_SHA, timeout_seconds=600))
assert file_hash(PARENT_ZIP) == PARENT_SHA
ACQUISITION_ID = "qwen3-controlled-peer-donors-001"
PLAN = controlled_plan(config, DATA, TRAIN_ZIP, SELECTION, PARENT_ZIP, ACQUISITION_ID)
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
RUN_ID = "qwen3-receiver-supervision-controlled-001"
RUN = SCRATCH / "receiver-supervision" / RUN_ID
PERSISTENT = DRIVE / "receiver-supervision" / RUN_ID
COMMON = ["--config", str(CONFIG), "--data-dir", str(DATA),
    "--initialization-bundle", str(TRAIN_ZIP), "--initialization-root", str(INITIAL),
    "--selection", str(SELECTION), "--run-dir", str(RUN),
    "--persistent", str(PERSISTENT), "--cache-dir", str(SCRATCH / "cache"),
    "--parent-bundle", str(PARENT_ZIP), "--acquisition-id", ACQUISITION_ID]
def study(stage, *options):
    subprocess.run([sys.executable, "-m", "pact.training.controlled_donors",
                    stage, *COMMON, *options], check=True)
study("plan")  # dry run, no model load or generation
if not RUN.exists():
    snapshots = sorted((PERSISTENT / "snapshots").glob("*"))
    if snapshots:
        study("restore", "--snapshot", str(snapshots[-1]))
    else:
        study("plan", "--execute")  # freezes membership and verifies persistence
```

## 5. Acquire donors and freeze contexts (explicit opt-in)

Two targets per eligible original own state, at most two attempts per target,
first structurally accepted packet wins. Resume the same run; no fresh budget.
The original nonreplaced peer may abstain, but malformed/invalid/truncated material
is unsupported. Replaced peer bytes remain in the audit record. Rationale status is
`not_reviewed`. Existing committed donor calls are revalidated, never regenerated.

```python
from pact.util import read_json
RUN_ACQUISITION = False  # set True after reviewing the printed plan
if RUN_ACQUISITION:
    study("acquire", "--execute")
if (RUN / "contexts.json").exists():
    CONTEXTS = read_json(RUN / "contexts.json")
    print({p: {k: v for k, v in part.items() if k != "records"}
           for p, part in CONTEXTS["partitions"].items()})
    if CONTEXTS["status"] != "ready":
        study("report")
        raise RuntimeError("insufficient_context_support: return the handoff ZIP; no more draws or training.")
```

The `acquire` stage also freezes contexts, target masks, both arm schedules and the
16-donor offline review sample. `study("contexts", "--execute")` can reconstruct
those artifacts from the committed bank with the pinned tokenizer; it makes zero
new donor calls and refuses an incomplete bank.

## 6. Train the two comparison arms

Both start from the same three prepared adapters, but update **only agent0**.
`--resume` consumes only this new arm's own checkpoint. A completed arm runs zero
additional updates. Do not view held-out model outcomes or choose a checkpoint
between these commands.

```python
RUN_TRAINING = False  # set True only after the context gate passes
if RUN_TRAINING:
    assert read_json(RUN / "contexts.json")["status"] == "ready"
for arm in (("task_sft", "receiver_sft") if RUN_TRAINING else ()):
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
available correct-donor/wrong-donor/peer-withheld contexts, 32 natural private answers per arm, and eight naturally
generated teams per arm under clean/exchange. No all-agent refresh or final test.

```python
RUN_EVALUATION = False  # set True only after BOTH trained arms finish
for arm in (("frozen", "task_sft", "receiver_sft") if RUN_EVALUATION else ()):
    study("evaluate", "--arm", arm, "--execute")
```

## 8. Report and return the review bundle

```python
# This also works for an acquisition support stop; report.json exists only after evaluation.
if all((RUN / "evaluation" / a / "status.json").exists()
       for a in ("frozen", "task_sft", "receiver_sft")):
    study("report")
    REPORT = read_json(RUN / "report.json")
    print(REPORT["generation_accounting"])
    print(REPORT["controlled_donor_comparisons"])
else:
    study("export")
    print(read_json(RUN / "source_report.json"))
from google.colab import files
latest = max((RUN.parent / "bundles").glob(f"{RUN_ID}-handoff-*.zip"), key=lambda p: p.stat().st_mtime_ns)
print("Review:", latest, "SHA256:", file_hash(latest))
print("Drive copy:", PERSISTENT / "bundles" / latest.name)
files.download(str(latest))
```

The full new-study snapshot retains `training/task_sft/checkpoints` and
`training/receiver_sft/checkpoints`, including optimizer and RNG. Evaluation exports
are `training/{arm}/references/agent{0,1,2}`. The original prepared references remain
at `INITIAL/references/agent{0,1,2}`. Review ZIPs omit tensor payloads; their inventory
and handoff identify full snapshots and checkpoint paths.

Expected metadata: `plan.json`, `recipe.json`, `state.json`, `environment.json`,
`donors/shards`, `donors/call-intents`, `donors/calls/shards`, token traces,
`donor_review.json`, `source_report.json`, `training_schedule.json`, `contexts.json`,
`target_masks.json`, arm `examples.json` / `run.json` / `status.json`, immutable
checkpoint metadata, evaluation shards/CE records, `report.json`, resource records,
`CODEX_HANDOFF.md`, `CODEX_HANDOFF.json`, and review checksums. Unknown billed compute
units stay null. Controlled synthetic and natural results are separate; teacher-forced CE is not
free-generation accuracy.

Drive operations have a 120-second deadline (restore: 600 seconds). Many files can
still make Drive slow. A local recovery ZIP is produced on failure; do not interpret
it as proof that tensor checkpoints reached Drive. Preserve it and return the error.
No change to runtime, context length, seed budget or missing-support gate is automatic.

The acquisition ID is a linked child bank under `RUN/donors`, persisted atomically
with its consumer study; it is not an independently resumable duplicate bank.
Return `qwen3-receiver-supervision-controlled-001-handoff-*.zip` and its SHA256,
including on a support stop. Preserve the full durable `objects/` and `snapshots/`
for optimizer resume. The review archive deliberately omits tensor weights.

CLI stages (the notebook constructs all required `COMMON` arguments explicitly):
`plan`, `plan --execute`, `acquire --execute`, `train --arm task_sft --execute`,
`train --arm receiver_sft --execute`, `evaluate --arm frozen --execute`,
`evaluate --arm task_sft --execute`, `evaluate --arm receiver_sft --execute`,
`report`, `export`. Add `--resume` only to an existing new arm's training run.
