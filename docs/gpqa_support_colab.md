# GPQA Diamond support: ordered Colab cells

This is the same thin sequence as [the notebook](../notebooks/06_gpqa_support_colab.ipynb).


# GPQA Diamond natural support — development only
Fixed run `qwen3-gpqa-diamond-support-001`:32 tasks,256 calls,53248 reserved output tokens.
No training, attacks, extra samples or final-test execution. GPU behavior is unverified.
Personally accept the official dataset conditions at https://huggingface.co/datasets/Idavidrein/gpqa.
Use a private, access-controlled Drive directory. Keep raw artifacts and notebook outputs private.
Review/push code first and supply its full commit SHA. Set RUN_GPU only after reviewing the frozen plan.



## Cell 1

```python
from pathlib import Path
import os, re, sys, subprocess, json
from google.colab import drive
GIT_REF = "PASTE_FULL_REVIEWED_COMMIT_SHA"
REPO_URL = "https://github.com/Soqoro/Pact.git"
RUN_GPU = False
DOWNLOAD_DATASET = True  # False for an already authorized pinned official source directory
SCRATCH = Path("/content/pact-scratch")
CHECKOUT = SCRATCH / "checkout"
PRIVATE = SCRATCH / "gpqa-private"
DRIVE = Path("/content/drive/MyDrive/PACT")
RUN_ID = "qwen3-gpqa-diamond-support-001"
RUN = PRIVATE / RUN_ID
PERSISTENT = DRIVE / "gpqa-private" / RUN_ID
DATASET_DIR = PRIVATE / "official-source"
PREPARED = PRIVATE / "selected-development.json"
INITIAL = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
PREP_SNAPSHOT = DRIVE / "actor-preparation/qwen3-preparation-120-001/training/snapshots/1789930640656395583-479df47c14d9"
SOURCE_NAME = "qwen3-receiver-supervision-controlled-001-handoff-1790186567377083314.zip"
SOURCE_SHA = "ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea"
SOURCE_DRIVE = DRIVE / "receiver-supervision/qwen3-receiver-supervision-controlled-001/bundles" / SOURCE_NAME
SOURCE = PRIVATE / "completed-controlled-review.zip"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF)
drive.mount("/content/drive")
PRIVATE.mkdir(parents=True, exist_ok=True)
def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()
if not CHECKOUT.exists():
    subprocess.run(["git", "clone", "--filter=blob:none", REPO_URL, str(CHECKOUT)], check=True)
assert not git("-C", str(CHECKOUT), "status", "--porcelain"), "Preserve local changes first."
assert git("-C", str(CHECKOUT), "remote", "get-url", "origin") == REPO_URL
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["HF_HOME"] = str(SCRATCH / "cache/huggingface")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
```



## Cell 2

```python
from pact.colab import install_dependencies
install_dependencies(CHECKOUT)
subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_gpqa_support.py", "-v"], check=True)
COMMON = ["--run-dir", str(RUN), "--persistent", str(PERSISTENT)]
def study(stage, *options):
    # Merge stderr into notebook-visible stdout; scientific code suppresses raw error text.
    command = [sys.executable, "-u", "-m", "pact.studies.gpqa_study", stage, *COMMON, *options]
    print("Starting GPQA stage:", stage, flush=True)
    process = subprocess.Popen(command, cwd=CHECKOUT, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in process.stdout:
        print(line, end="", flush=True)
    code = process.wait()
    if code:
        raise RuntimeError(f"GPQA {stage} stopped ({code}). Preserve private scratch; do not retry ambiguous calls.")
```


## Official access and partition before model loading
For local-file mode place the authorized files `gpqa_diamond.csv`, `README.md` and
`license.txt` from official revision `83022cefff930aea54f654c0b282e74b9eeda5c6` in DATASET_DIR.
Their pinned Git blob identities are verified. No mirrors or remote dataset scripts.
For download mode put a read token for your authorized HF account in Colab secret `HF_TOKEN`.
Do not paste tokens or examples into cells, logs or public output.



## Cell 3

```python
from pact.storage import storage_operation
from pact.util import file_hash, read_json
if DOWNLOAD_DATASET:
    from google.colab import userdata
    try:
        os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
    except Exception:
        raise RuntimeError("Add the HF_TOKEN Colab secret after personally accepting official GPQA access terms.") from None
try:
    options = ["--dataset-dir", str(DATASET_DIR), "--prepared", str(PREPARED)]
    if DOWNLOAD_DATASET:
        options.append("--download")
    study("dataset", *options)
finally:
    os.environ.pop("HF_TOKEN", None)
```



## Cell 4

```python
from pact.training.preparation_restore import restore_preparation_references
from pact.studies.gpqa_model import source_contract
from pact.training.receiver_study import initial_recipe
from pact.environment import runtime_fingerprint
if not SOURCE.exists():
    print(storage_operation("bundle-restore", SOURCE_DRIVE, SOURCE,
                            sha256=SOURCE_SHA, timeout_seconds=600))
assert file_hash(SOURCE) == SOURCE_SHA
contract = source_contract(SOURCE)
if not INITIAL.exists():
    print(restore_preparation_references(PREP_SNAPSHOT, INITIAL, timeout_seconds=600))
initial_recipe(contract, INITIAL)  # checks actual stored preparation weights, not merely ZIP metadata
assert runtime_fingerprint() == contract["checkpoint"]["runtime_fingerprint"], "Runtime differs from evaluated frozen arm; stop for review."
print("Selected arm:", contract["arm"])
print("Required effective tensor hashes:", contract["checkpoint"]["effective_actor_tensor_hashes"])
# Actual loaded effective tensors are additionally verified before any generation.
```



## Cell 5

```python
PLAN_ARGS = ["--dataset-dir", str(DATASET_DIR), "--prepared", str(PREPARED),
             "--source-bundle", str(SOURCE), "--initialization-root", str(INITIAL)]
if not RUN.exists():
    snapshots = sorted(p for p in (PERSISTENT / "snapshots").glob("*") if p.is_dir())
    if snapshots:
        study("restore", "--snapshot", str(snapshots[-1]))
# Refuse changed code/data/options/selection; never fall back to an older snapshot.
study("plan", *PLAN_ARGS)
plan = read_json(RUN / "plan.json")
print("Budget:", plan["budget"])
print("Selected domain counts:", plan["dataset"]["manifest"]["selected_domain_counts"])
print("Development items:", len(plan["dataset"]["manifest"]["selected_ids"]))
print("Protected items:", len(plan["dataset"]["manifest"]["protected_ids"]))
print("Source-integrity excluded items:", len(plan["dataset"]["manifest"]["source_integrity_excluded_ids"]))
print("Eligible groups:", plan["dataset"]["manifest"]["eligible_group_count"])
```



## Cell 6

```python
GPU_ARGS = ["--initialization-root", str(INITIAL), "--cache-dir", str(SCRATCH / "cache"), "--execute"]
if RUN_GPU:
    # First two selected tasks, exact frozen requests, at most16 calls within the256 cap.
    study("complete", "--smoke", *GPU_ARGS)
else:
    print("GPU stages disabled. Review plan, then set RUN_GPU=True to execute this fixed study.")
```



## Cell 7

```python
if RUN_GPU:
    # All32 tasks regardless of agreement; the smoke's16 calls are reused.
    study("complete", *GPU_ARGS)
    study("report")
    study("export")
    summary = read_json(RUN / "summary.json")
    print({k: summary[k] for k in ("completed_tasks", "missing_tasks", "screen_flag")})
    # Returned paths/SHA256 appear above. PRIVATE ZIP is not for public redistribution.
```


Bring back the PRIVATE ZIP through a private local channel for raw-prompt auditing;
keep it outside Git. The SANITIZED ZIP may be used for text-free summary review but
cannot support a full raw audit. If an attempt is unresolved or a persistence timeout
occurs, preserve scratch and return the private recovery bundle. Do not delete journals,
repeat lost calls, choose an older safe snapshot, change hardware/precision silently, or
expand the sample. The study stops after these32 tasks; no outcome authorizes a follow-up.



Optional private-only checkpoint stage (same plan, at most96 private calls):
```python
study("private", *GPU_ARGS)
```
Then `complete` reuses those private calls. This is not a different study or a support-based stop.
A bounded pause can use `--stop-after N`; it counts only fresh calls in that invocation.
No automatic retry is allowed for an interrupted in-flight generation. A zombie owner
may retain `.lock`; inspect its recorded PID/host before removing only a stale lock.

Official file header validation runs after authorized access. No real CSV was downloaded
locally during implementation, so actual domain counts/schema acceptance remain a
Colab data preflight, and no GPQA results are claimed. Full-source parsing reads198
records for automated grouping/partitioning; only selected32 tasks become model requests.

## Local private-bundle audit after return

Keep the downloaded PRIVATE ZIP outside the repository and public upload channels.
The sanitized bundle alone cannot verify raw prompt/option isolation.

```python
from pact.studies.gpqa_study import audit_private_bundle, read_bundle
summary = audit_private_bundle("/absolute/private/path/PRIVATE.zip", "RETURNED_SHA256")
# summary contains sanitized metrics only; raw reconstruction happens in temporary private scratch.
print(summary["completed_tasks"], summary["missing_tasks"], summary["screen_flag"])
```

Private bundles contain selected32 text and mappings but no model weights or full
198-row source CSV. Reproducing partition selection additionally needs the authorized
pinned official source; accessing the protected remainder for generation is forbidden.

If the runtime is interrupted while a task is in flight, do not choose an older
snapshot or remove call intents. The newest snapshot may deliberately be unsafe.
Report/export are CPU-only; local private recovery artifacts preserve raw audit data.
The notebook rechecks exact code/runtime/data identities after a reset. Merely
restarting with a new run ID is not an authorized budget reset.


### Restart after the approved duplicate-option fix

Review/commit/push the amendment locally and put that new full SHA in Cell1.
Rerun Cells1–5, then6–7 after successful preflight. The failed dataset stage used
no generation calls. The downloaded pinned source can be reused in Cell3 with
`DOWNLOAD_DATASET=False`; do not edit the CSV or delete a prepared manifest/plan.
Dataset preparation should report32 items and2 source-integrity excluded items
for the user-verified pinned source. The exact protected count depends on duplicate
groups and prior exclusions;164 is the count if only those two singleton rows are
excluded. Changed prepared data or an existing incompatible frozen plan stops for
review; do not change run ID or overwrite artifacts to bypass that guard.
