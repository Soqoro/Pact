# Fixed-bank specialization: exact Colab cells

# Fixed-bank specialization: explicit stages only
No GPQA, final-test, receiver loss, DPO, or automatic acquisition. Review/push code and pin the full SHA.
Run All defaults to plan only. Change STAGE and explicitly set EXECUTE for one GPU stage at a time.
Hard ceiling6336 generation calls /1363968 reserved output tokens;288 training updates.
These are caps, not estimates of runtime or cost. Failed support stops the study.


```python
from pathlib import Path
import os, sys, subprocess, json, re
from google.colab import drive
GIT_REF = "PASTE_REVIEWED_FULL_COMMIT_SHA"
STAGE = "plan"  # plan, collect, replay, assign, train, evaluate, report, export, restore
ARM = "frozen"  # frozen or uniform_supported_sft / local_specialization / continuation_specialization
EXECUTE = False
RESUME = False
PLAN_HASH = ""  # copy the printed plan hash after planning; never guess or change it
STOP_AFTER = None  # optional bounded new-call/update prefix; no extra smoke requests
SCRATCH = Path("/content/pact-scratch")
CHECKOUT = SCRATCH / "checkout"
DRIVE = Path("/content/drive/MyDrive/PACT")
RUN = SCRATCH / "specialization/qwen3-specialization-contrast-001"
PERSISTENT = DRIVE / "specialization/qwen3-specialization-contrast-001"
DATA = SCRATCH / "training-data/proposal-1200"
INITIAL = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
PREP_SNAPSHOT = DRIVE / "actor-preparation/qwen3-preparation-120-001/training/snapshots/1789930640656395583-479df47c14d9"
SOURCE_NAME = "qwen3-receiver-supervision-controlled-001-handoff-1790186567377083314.zip"
SOURCE_DRIVE = DRIVE / "receiver-supervision/qwen3-receiver-supervision-controlled-001/bundles" / SOURCE_NAME
SOURCE = SCRATCH / "sources/specialization-frozen-source.zip"
SOURCE_SHA = "ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea"
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
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD") == GIT_REF
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

```

```python
from pact.colab import install_dependencies
install_dependencies(CHECKOUT)
from pact.storage import storage_operation
from pact.util import file_hash, read_json
if not SOURCE.exists():
    print(storage_operation("bundle-restore", SOURCE_DRIVE, SOURCE, sha256=SOURCE_SHA, timeout_seconds=600))
assert file_hash(SOURCE) == SOURCE_SHA
if not DATA.exists():
    subprocess.run([sys.executable, "-m", "pact", "prepare-training-data",
        "--cache-dir", str(SCRATCH / "cache"), "--output-dir", str(DATA),
        "--items", "1200", "--seed", "20260918", "--download"], check=True)
def study(stage, *options):
    command = [sys.executable, "-u", "-m", "pact.training.specialization_study", stage,
               "--run-dir", str(RUN), "--persistent", str(PERSISTENT), *options]
    print("Starting specialization stage:", stage, flush=True)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in p.stdout:
        print(line, end="", flush=True)
    if p.wait():
        raise RuntimeError("Stage stopped. Preserve scratch and return the error; do not erase attempts or change run ID.")

```

```python
if STAGE == "restore":
    assert not RUN.exists(), "Restore requires a fresh scratch directory."
    snapshots = sorted(p for p in (PERSISTENT / "snapshots").glob("*") if p.is_dir())
    assert snapshots, "No full snapshot exists; review ZIPs omit tensors."
    study("restore", "--snapshot", str(snapshots[-1]))
elif STAGE == "plan":
    study("plan", "--data-dir", str(DATA), "--source-bundle", str(SOURCE))
else:
    assert re.fullmatch(r"[0-9a-f]{64}", PLAN_HASH), "Set the frozen plan hash from the plan output."
    options = ["--plan-hash", PLAN_HASH]
    if STAGE in ("collect", "replay", "train", "evaluate"):
        assert EXECUTE, "Set EXECUTE=True for this one explicit GPU stage."
        from pact.training.preparation_restore import restore_preparation_references
        if not INITIAL.exists():
            print(restore_preparation_references(PREP_SNAPSHOT, INITIAL, timeout_seconds=1800))
        options += ["--execute", "--initialization-root", str(INITIAL), "--cache-dir", str(SCRATCH / "cache")]
        if STAGE in ("train", "evaluate"):
            options += ["--arm", ARM]
        if RESUME:
            options.append("--resume")
        if STOP_AFTER is not None:
            options += ["--stop-after", str(STOP_AFTER)]
    study(STAGE, *options)

```
Order after plan review: collect → inspect candidate_support.json → replay → assign → inspect assignment_contrast.json → explicitly train each of the three arms → explicitly evaluate frozen and each trained arm → report → export.
Support minima:8 fitting tasks with pairs,8 with a multi-eligible row; mean multi-row credit/local L1>1e-6. If a gate fails, export and stop. No extra draws or task replacement.
On runtime loss restore the LATEST full study snapshot before continuing. Use the same pinned code/plan/initialization; never restore an older safe snapshot over lost attempts.
Training resume additionally requires --resume; complete arms are not retrained. Report/export require no GPU. Return ZIP+SHA256; full tensors remain in durable snapshots.


## Exact local commands (zero GPU)

```bash
PYTHONPATH=src python -m pact.training.specialization_study characterize \
  --source-bundle results_import/qwen3-bank-001-handoff-1789804954424856576.zip \
  --sha256 a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39 \
  --run-dir results_import/assignment-contrast-001

PYTHONPATH=src python -m pact.training.specialization_study plan \
  --data-dir results_import/training-data-001/proposal-1200 \
  --source-bundle results_import/qwen3-receiver-supervision-controlled-001-handoff-1790186567377083314.zip \
  --run-dir /tmp/pact-specialization-plan
```

A local dirty-source plan is only a design artifact. The Colab plan must be created
from the reviewed pushed commit; preserve any prior incompatible plan instead of
overwriting it. The plan output prints its actual hash and all caps.

After the setup cells above, these are equivalent individual Colab invocations.
Run ONE requested stage at a time; do not paste the whole list into a Run All cell.
Each train/evaluate invocation requires a specific `ARM` value; there is no sweep.

```python
H = ["--plan-hash", PLAN_HASH]
GPU = ["--execute", "--initialization-root", str(INITIAL),
       "--cache-dir", str(SCRATCH / "cache")]
# Choose one line/stage explicitly:
study("collect", *H, *GPU)
study("replay", *H, *GPU)  # only after ready_for_replay
study("assign", *H)       # CPU; must report ready before train/evaluate
study("train", *H, *GPU, "--arm", ARM)  # add --resume only for this arm's own checkpoint
study("evaluate", *H, *GPU, "--arm", ARM)
study("report", *H)
study("export", *H)
```

Training arms: `uniform_supported_sft`, `local_specialization`,
`continuation_specialization`. Evaluation adds `frozen`. Each training invocation
updates all three actors sequentially; each evaluation invocation covers32 tasks
and both conditions. All three trained arms use the same96-update schedule.
A deliberate generation pause uses `--stop-after N`; training interprets it as
new optimizer updates. It never means new tasks, new seeds or budget renewal.

Return the final handoff ZIP and SHA256, preserving full snapshots in Drive.
Expected metadata includes the source/exposure and bank manifests, raw natural
anchors/candidates/replays and call/score journals, candidate support, NLL definition,
transform, three assignments, contrast, loss/weight audit, training by arm/actor,
evaluation JSONL, results, resource accounting and CODEX_HANDOFF.md. Missing-stage
artifacts stay missing in partial exports; no fake readiness/completion record is
created. Safe local re-audit after return:

```bash
PYTHONPATH=src python -m pact.training.specialization_study audit \
  --source-bundle /absolute/path/to/returned.zip \
  --sha256 RETURNED_SHA256 --run-dir results_import/specialization-return-audit
```

The reader checks bounded members and checksums, reconstructs recorded protocol
requests, scores and assignments with trusted package code, and compares the
saved report. It never imports code or loads tensors from a review ZIP.
