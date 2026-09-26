# Controlled private specialization: Colab commands

Open notebooks/08_controlled_private_specialization_colab.ipynb, or copy the three
cells below into a fresh Google Colab notebook. Pin the reviewed PUSHED code's full
SHA; no commit or GPU run was made during implementation. CPU suffices for plan.
GPU stages require the same environment/precision as the completed parent. The
loader checks runtime, tokenizer/template and actual effective actor identities.

Prerequisites:
- The exact stopped parent ZIP and SHA below, on Drive. Metadata supplies original
  contexts and cohort; no new dataset selection/download is needed.
- For any GPU stage: actual completed90-step preparation reference weights in the
  named durable snapshot. The review ZIP is not a weight checkpoint.
- Review later use of the original32 development groups. Set
  DEVELOPMENT_USE_REVIEWED=True and a concrete review note only after checking.
  This guard implements section4 of the supplied specification; a later
  incompatible use stops planning, rather than silently replacing tasks.
- New child plan hash printed after planning; do not use the parent's plan hash.

```python
from pathlib import Path
import os, sys, subprocess, json, re
from google.colab import drive
GIT_REF = "PASTE_REVIEWED_FULL_COMMIT_SHA"
STAGE = "plan"  # plan/acquire/build-bank/replay/score-assign/train/evaluate/report/export/restore
EXECUTE = False
PLAN_HASH = ""
ARM = "frozen"
RESUME = False
STOP_AFTER = None
DEVELOPMENT_USE_REVIEWED = False  # explicit prerequisite, not a model result
DEVELOPMENT_REVIEW_NOTE = ""  # who checked which records / any external uses
LATER_DEVELOPMENT_USES = []  # any optimization/outcome-selection use stops planning
SCRATCH = Path("/content/pact-scratch")
CHECKOUT = SCRATCH / "checkout"
DRIVE = Path("/content/drive/MyDrive/PACT")
RUN = SCRATCH / "controlled-specialization/qwen3-controlled-specialization-001"
PERSISTENT = DRIVE / "controlled-specialization/qwen3-controlled-specialization-001"
PARENT_NAME = "qwen3-specialization-contrast-001-handoff-1790416052208683365.zip"
PARENT_DRIVE = DRIVE / "specialization/qwen3-specialization-contrast-001/bundles" / PARENT_NAME
PARENT = SCRATCH / "sources/controlled-specialization-parent.zip"
PARENT_SHA = "555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f"
INITIAL = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
PREP_SNAPSHOT = DRIVE / "actor-preparation/qwen3-preparation-120-001/training/snapshots/1789930640656395583-479df47c14d9"
REVIEW_FILE = SCRATCH / "controlled-training-review.json"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF)
drive.mount("/content/drive")
SCRATCH.mkdir(parents=True, exist_ok=True)
def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()
if not CHECKOUT.exists():
    subprocess.run(["git", "clone", "https://github.com/Soqoro/Pact.git", str(CHECKOUT)], check=True)
assert not git("-C", str(CHECKOUT), "status", "--porcelain"), "Preserve local changes."
assert git("-C", str(CHECKOUT), "remote", "get-url", "origin") == "https://github.com/Soqoro/Pact.git"
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```

```python
from pact.colab import install_dependencies
install_dependencies(CHECKOUT)
from pact.storage import storage_operation
from pact.util import read_json, write_json, file_hash, digest
if not PARENT.exists():
    assert PARENT_DRIVE.is_file(), f"Required parent ZIP missing: {PARENT_DRIVE}"
    PARENT.parent.mkdir(parents=True, exist_ok=True)
    print(storage_operation("bundle-restore", PARENT_DRIVE, PARENT,
                            sha256=PARENT_SHA, timeout_seconds=600))
assert file_hash(PARENT) == PARENT_SHA

def study(stage, *options):
    command = [sys.executable, "-u", "-m", "pact.training.controlled_specialization",
               stage, "--run-dir", str(RUN), "--persistent", str(PERSISTENT),
               *map(str, options)]
    log = SCRATCH / f"controlled-{stage}-{__import__('time').time_ns()}.log"
    print("Starting:", stage, "Log:", log, flush=True)
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)
    with log.open("w") as stream:
        for line in process.stdout:
            print(line, end="", flush=True)
            stream.write(line)
            stream.flush()
    if process.wait():
        raise RuntimeError(f"{stage} stopped. Preserve scratch/attempts and return {log}.")
```

```python
if STAGE == "restore":
    assert not RUN.exists(), "Restore requires fresh scratch; never erase partial work."
    snapshots = sorted(p for p in (PERSISTENT / "snapshots").glob("*") if p.is_dir())
    assert snapshots, "No full child snapshot. Review ZIPs are not resumable weights."
    study("restore", "--snapshot", snapshots[-1])
elif STAGE == "plan":
    assert DEVELOPMENT_USE_REVIEWED and DEVELOPMENT_REVIEW_NOTE, "Complete the later-development-use review required by specification section4."
    exposure = SCRATCH / "controlled-development-exposure.json"
    write_json(exposure, {"reviewed": DEVELOPMENT_USE_REVIEWED,
                         "provenance": DEVELOPMENT_REVIEW_NOTE,
                         "development_used_for_optimization_or_outcome_selection": LATER_DEVELOPMENT_USES})
    study("plan", "--parent-bundle", PARENT, "--exposure-review", exposure)
    PLAN_HASH = digest(read_json(RUN / "plan.json"))
    print("Frozen PLAN_HASH:", PLAN_HASH)
else:
    assert re.fullmatch(r"[0-9a-f]{64}", PLAN_HASH), "Use the printed child plan hash."
    assert digest(read_json(RUN / "plan.json")) == PLAN_HASH
    options = ["--plan-hash", PLAN_HASH]
    if STAGE in ("acquire", "replay", "score-assign", "train", "evaluate"):
        assert EXECUTE, "Explicitly select this one GPU stage."
        from pact.training.preparation_restore import restore_preparation_references, verify_inference_export
        if not INITIAL.exists():
            print(restore_preparation_references(PREP_SNAPSHOT, INITIAL, timeout_seconds=1800))
        verify_inference_export(INITIAL)
        options += ["--execute", "--initialization-root", INITIAL, "--cache-dir", SCRATCH / "cache"]
        if STOP_AFTER is not None:
            options += ["--stop-after", str(STOP_AFTER)]
        if STAGE in ("train", "evaluate"):
            options += ["--arm", ARM]
            if REVIEW_FILE.exists(): options += ["--review", REVIEW_FILE]
        if RESUME: options.append("--resume")
    study(STAGE, *options)
```

## Explicit individual stages after setup

Run only the requested stage. These commands are alternatives to changing STAGE
in the third notebook cell, not an automatic sequence for Run All.

```python
from pact.training.preparation_restore import restore_preparation_references, verify_inference_export
if not INITIAL.exists():
    print(restore_preparation_references(PREP_SNAPSHOT, INITIAL, timeout_seconds=1800))
verify_inference_export(INITIAL)
H = ["--plan-hash", PLAN_HASH]
GPU = ["--execute", "--initialization-root", INITIAL,
       "--cache-dir", SCRATCH / "cache"]
study("acquire", *H, *GPU)                 # only128 calls maximum
study("build-bank", *H)                   # CPU, structural eight-task support gate
study("replay", *H, *GPU)                 # primary + fixed order + five-cell calibration
study("score-assign", *H, *GPU)           # ≤384 frozen scores; stops for review
study("export", *H)                      # return ZIP + SHA before deciding to train
```

At most6,096 calls/1,274,112 reserved output tokens for the entire child;
parent calls do not reset. Acquisition128, primary3072, order768, calibration80,
evaluation2048. Use --stop-after N for a bounded pause before a new generation;
repeating the stage consumes saved calls before dispatching new ones. An unresolved
attempt stops rather than invisibly retrying. score-assign is a distinct stage;
no training follows automatically. Training uses --stop-after for new updates.

## Required review before training

Inspect pair_quality_and_review.json (both packets for the frozen eight task IDs),
assignment_contrast.json, order_sensitivity.json, seed_assignment_sensitivity.json
and natural_controlled_calibration.json. Passing structural/practical screens is
not a claim that the credit is reliable. A systematic content or metadata defect
stops work; pass its review with systematic_packet_defect=true to record the stop.
Changing the generator requires a new source version.

This cell prepares an UNAPPROVED review form, without authorizing a run:

```python
files = ("assignment_contrast.json", "pair_quality_and_review.json",
         "order_sensitivity.json", "seed_assignment_sensitivity.json")
review = {
    "plan_hash": PLAN_HASH,
    "artifact_hashes": {name: digest(read_json(RUN / name)) for name in files},
    "reviewed_task_ids": read_json(RUN / "plan.json")["review_task_ids"],
    "reviewer": "",
    "notes": "",
    "systematic_packet_defect": None,
    "decision": "pending",
}
write_json(REVIEW_FILE, review)
print(REVIEW_FILE)
```

After an explicit decision to train, fill actual reviewer/notes, confirm no
systematic defect with false, and set decision to approve_training. The CLI binds
this decision to the exact plan and review artifacts, preserves it in the child,
and refuses training if support or practical contrast failed. Review records
sample inspection, not verified reasoning. Do not fabricate reviewer statements.

Run each desired arm separately, with identical final96-update budgets:

```python
ARM = "controlled_uniform_sft"  # later: controlled_local_specialization / controlled_continuation_specialization
study("train", *H, *GPU, "--arm", ARM, "--review", REVIEW_FILE)
# For interrupted training of that SAME arm only:
# study("train", *H, *GPU, "--arm", ARM, "--review", REVIEW_FILE, "--resume")
```

After training, individually evaluate frozen and each completed trained arm:

```python
ARM = "frozen"  # later choose one completed controlled training arm
study("evaluate", *H, *GPU, "--arm", ARM, "--review", REVIEW_FILE)
study("report", *H)
study("export", *H)
```

Evaluation uses only natural private packets, no synthetic donor or answer target.
A final complete comparison requires all four systems, but there is no notebook
sweep. Each arm is512 calls/106,496 reserved tokens; 32 task clusters, clean/early
reported separately. No additional development sampling or checkpoint selection.

## Runtime restart and handoff

Rerun setup with the SAME pinned commit, set STAGE=restore on fresh scratch, then
set the SAME child plan hash and the desired stage. Restoration is latest-only
and requires a safe snapshot; unknown attempts stop. Never delete locks or results
without inspecting the owning process. Checkpoint tensors/optimizer states live
in full Drive snapshots. Review ZIPs contain metadata and cannot restore training.

Export creates a local bundle before bounded verified Drive copies. Return the
printed ZIP and SHA256. Expected artifacts: parent_import_receipt.json,
natural_candidate_missingness.json, controlled_pair_manifest.json,
controlled_pair_attempts.jsonl, pair_quality_and_review.json, controlled_support.json,
controlled_replay_cells.jsonl, order_sensitivity.json,
natural_controlled_calibration.json, answer_score_definition.json,
assignment_transform.json, assignment_{uniform,local,credit}.json,
assignment_contrast.json, seed_assignment_sensitivity.json, pretraining_decision.md,
loss_weight_audit.json, training_arms.json, development_results.json, resource_usage.json,
CODEX_HANDOFF.md plus exact call/score/checkpoint journals. Unexecuted stages remain
absent or explicitly missing; full tensors are excluded from the review ZIP.
Keep raw task/model output bundles private and outside Git.

Local returned-bundle audit (no model):

```bash
PYTHONPATH=src python -m pact.training.controlled_specialization audit \
  --source-bundle /absolute/path/to/returned.zip --sha256 RETURNED_SHA256 \
  --run-dir results_import/controlled-specialization-audit
```

Default CPU tests: `PYTHONPATH=src python -m unittest discover -s tests -v`.
Optional tiny local tests require PACT_TINY_SPECIALIZATION=1 and locally installed
torch/safetensors; no pretrained downloads. No outcome authorizes another run.
