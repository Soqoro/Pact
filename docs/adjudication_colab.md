# Fixed-bank adjudication: exact fresh-Colab sequence

Use [notebooks/20_adjudication_colab.ipynb](../notebooks/20_adjudication_colab.ipynb).
The cells below are its actual implementation, not pseudocode. Pin the full commit
**after you review and push this change**; no new reviewed commit SHA exists yet.
Do not reuse an earlier breadth plan hash for this new study. The import/plan cell
prints the new artifact-bound PLAN_HASH.

One BF16 GPU is required for real inference. No adapter checkpoints or training
ZIPs are needed. Use the three exact completed PRIVATE breadth bundles already
on Drive; SANITIZED bundles cannot restore candidate banks. The required paths
are constructed below, with hashes enforced from adjudication_data.PARENTS.
Qwen3-14B runtime fit and throughput remain unverified; there is no automatic
quantized/smaller/offloaded fallback. Leave the current PyTorch/CUDA stack intact.

Run setup and metadata preflight first. Every generation cell defaults EXECUTE
False: change **only the stage you intend to run** to True. Do not Run All with
all flags enabled. Each stage reports, exports and stops. The first compute stage
is the included J8 two-task smoke (12 calls), followed by review.

## Code cell 1

```python
from pathlib import Path
import os, sys, re, subprocess, json, time, tempfile, getpass
from urllib.parse import urlsplit
REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "REPLACE_WITH_FULL_REVIEWED_PUSHED_COMMIT_SHA"
RUN_ID = "pact-adjudication-diagnostic-001"
SCRATCH = Path("/content/pact-adjudication")
CHECKOUT = SCRATCH / "checkout"
RUN = SCRATCH / "runs" / RUN_ID
CACHE = SCRATCH / "cache"
PERSISTENT = Path("/content/drive/MyDrive/PACT/adjudication") / RUN_ID
PRIVATE_REPOSITORY = False
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF), "Set the full reviewed commit SHA."
from google.colab import drive
drive.mount("/content/drive")
SCRATCH.mkdir(parents=True, exist_ok=True)
```

## Code cell 2

```python
url = urlsplit(REPO_URL)
assert url.scheme == "https" and url.hostname and not any((url.username,url.password,url.query,url.fragment))
secret = None
if PRIVATE_REPOSITORY:
    try:
        from google.colab import userdata
        secret = userdata.get("PACT_GITHUB_TOKEN")
    except Exception:
        secret = getpass.getpass("GitHub token (hidden): ")
try:
    with tempfile.TemporaryDirectory() as auth:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        if secret:
            helper = Path(auth) / "askpass.py"
            helper.write_text('#!/usr/bin/env python3\nimport os,sys\nprint("x-access-token" if "username" in sys.argv[1].lower() else os.environ["PACT_GIT_TOKEN"])\n')
            helper.chmod(0o700)
            env.update(GIT_ASKPASS=str(helper), PACT_GIT_TOKEN=secret)
        def git(*args):
            result = subprocess.run(["git", "-c", "credential.helper=", *args], env=env, capture_output=True, text=True)
            if result.returncode: raise RuntimeError("Git failed; credential-sensitive output suppressed.")
            return result.stdout.strip()
        if not CHECKOUT.exists(): git("clone", "--filter=blob:none", REPO_URL, str(CHECKOUT))
        assert git("-C",str(CHECKOUT),"remote","get-url","origin") == REPO_URL
        assert not git("-C",str(CHECKOUT),"status","--porcelain"), "Preserve local edits."
        git("-C",str(CHECKOUT),"fetch","--depth","1","origin",GIT_REF)
        git("-C",str(CHECKOUT),"checkout","--detach",GIT_REF)
        assert git("-C",str(CHECKOUT),"rev-parse","HEAD").lower() == GIT_REF.lower()
finally:
    secret = None
    if "env" in globals(): env.pop("PACT_GIT_TOKEN", None)
os.chdir(CHECKOUT)
subprocess.run([sys.executable,"-m","pip","install","-e",".[model]"],check=True)
sys.path.insert(0,str(CHECKOUT/"src"))
subprocess.run(["nvidia-smi"],check=True)
```

## Code cell 3

```python
from pact.util import read_json, file_hash, digest
from pact.storage import storage_operation
from pact.studies.adjudication_data import PARENTS

def study(stage, *options):
    command = [sys.executable,"-u","-m","pact","adjudication",stage,
               "--run-dir",str(RUN),"--persistent",str(PERSISTENT),*map(str,options)]
    log = SCRATCH / f"adjudication-{stage}-{time.time_ns()}.log"
    print("Starting:",stage,*options,"Log:",log,flush=True)
    with log.open("w") as stream:
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in process.stdout:
            print(line,end="",flush=True);stream.write(line);stream.flush()
        status = process.wait()
    if status: raise RuntimeError(f"{stage} stopped ({status}); preserve scratch and inspect {log}. No automatic retry.")

# Only official model access is needed; no dataset access or new checkpoint adapters.
# Public Qwen models normally need no token. For an authorized Hub token, use Secrets:
# from google.colab import userdata
# os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
```

## Code cell 4

```python
if not (RUN/"adjudication_plan.json").exists() and (PERSISTENT/"snapshots").exists():
    assert not RUN.exists(), "Partial scratch exists; inspect rather than overwrite."
    study("restore")
if not (RUN/"bank.json").exists():
    SOURCES = SCRATCH / "sources"
    SOURCES.mkdir(parents=True,exist_ok=True)
    paths = {}
    for name,spec in PARENTS.items():
        source = Path("/content/drive/MyDrive/PACT/breadth") / f"pact-breadth-{name}-001" / "bundles" / spec["file"]
        target = SOURCES / spec["file"]
        assert source.is_file(), f"Required completed PRIVATE parent missing: {source}"
        if not target.exists():
            print(storage_operation("bundle-restore",source,target,sha256=spec["sha256"],timeout_seconds=600))
        assert file_hash(target) == spec["sha256"]
        paths[name] = target
    study("import","--mmlu-bundle",paths["mmlu-pro"],"--musr-bundle",paths["musr"],"--math-bundle",paths["math-500"])
study("analyze")
if not (RUN/"adjudication_plan.json").exists(): study("plan")
PLAN = read_json(RUN/"adjudication_plan.json")
PLAN_HASH = digest(PLAN)
assert read_json(RUN/"state.json")["recovery_safe"], "Unsafe persisted dispatch; stop and return artifacts."
print("PLAN_HASH:",PLAN_HASH)
print("BUDGET:",json.dumps(PLAN["budgets"],indent=2))
COMMON = ["--execute","--plan-hash",PLAN_HASH,"--cache-dir",str(CACHE),"--resume"]
```

Preflight downloads tokenizer/config metadata only and verifies official weight access. It checks all currently available clean and rewrite requests. It does not generate or download weights. Attacked views are checked again after the pool exists. A metadata/runtime mismatch stops; do not rewrite receipts.

## Code cell 5

```python
study("preflight",*COMMON)
```

First included smoke: set only this EXECUTE flag true to run 12 J8 calls on the first two MMLU tasks. They are reused by full clean. Review the report/bundles; no automatic continuation.

## Code cell 6

```python
EXECUTE = False
if EXECUTE:
    study("smoke","--dataset","mmlu-pro","--judge","J8",*COMMON)
```

Clean stage: run each cell explicitly, in model-major order. Each command exports and stops. Use --stop-after N if you need a smaller safe boundary; rerun the identical command with --resume to continue. No budget is replenished. Unavailable or unsafe states require inspection.

## Code cell 7

```python
EXECUTE = False
if EXECUTE:
    study("clean","--dataset","mmlu-pro","--judge","J8",*COMMON)
```

## Code cell 8

```python
EXECUTE = False
if EXECUTE:
    study("clean","--dataset","musr","--judge","J8",*COMMON)
```

## Code cell 9

```python
EXECUTE = False
if EXECUTE:
    study("clean","--dataset","mmlu-pro","--judge","J14",*COMMON)
```

## Code cell 10

```python
EXECUTE = False
if EXECUTE:
    study("clean","--dataset","musr","--judge","J14",*COMMON)
```

Separate acquisition stage. Both dataset pools must finish before any victim call. Fixed one-attempt styles; no clean-outcome selection. Set flags only when deliberately starting this stage.

## Code cell 11

```python
EXECUTE = False
if EXECUTE:
    study("acquire-perturbations","--dataset","mmlu-pro",*COMMON)
```

## Code cell 12

```python
EXECUTE = False
if EXECUTE:
    study("acquire-perturbations","--dataset","musr",*COMMON)
```

After acquisition, preflight the frozen perturbed recipient requests. This is metadata/tokenization only.

## Code cell 13

```python
EXECUTE = False
if EXECUTE:
    assert (RUN/"pool.json").is_file(), "Entire two-dataset pool is not frozen."
    study("preflight",*COMMON)
```

Separate victim stage; all accepted edits go to the fixed six victims. Model-major order. No QQQ attacks or new invariant-control calls.

## Code cell 14

```python
EXECUTE = False
if EXECUTE:
    study("evaluate-perturbations","--dataset","mmlu-pro","--judge","J8",*COMMON)
```

## Code cell 15

```python
EXECUTE = False
if EXECUTE:
    study("evaluate-perturbations","--dataset","musr","--judge","J8",*COMMON)
```

## Code cell 16

```python
EXECUTE = False
if EXECUTE:
    study("evaluate-perturbations","--dataset","mmlu-pro","--judge","J14",*COMMON)
```

## Code cell 17

```python
EXECUTE = False
if EXECUTE:
    study("evaluate-perturbations","--dataset","musr","--judge","J14",*COMMON)
```

## Code cell 18

```python
study("report")
study("export")
for p in sorted((RUN.parent/"bundles").glob(f"{RUN_ID}-*zip")):
    if "-PRIVATE-" in p.name or "-SANITIZED-" in p.name:
        print("ZIP:",p,"SHA256:",file_hash(p),"Drive:",PERSISTENT/"bundles"/p.name)
```

Return the newest matched PRIVATE and SANITIZED pair and both SHA256 values. PRIVATE contains benchmark text, rationales and decodable tokens: do not publish or commit it. Stop for review; no result authorizes another study. A reset restores only the latest verified safe compact snapshot; never fall back from an unsafe latest snapshot.

## Direct CLI equivalents after setup

These use RUN, PERSISTENT, CACHE and PLAN_HASH defined above. Do not execute all
stages as one shell script. In order, the explicit inference invocations are:

```python
study("smoke", "--dataset", "mmlu-pro", "--judge", "J8", *COMMON)
# Stop for review. These continue the included requests, never repeat smoke calls.
study("clean", "--dataset", "mmlu-pro", "--judge", "J8", *COMMON)
study("clean", "--dataset", "musr", "--judge", "J8", *COMMON)
study("clean", "--dataset", "mmlu-pro", "--judge", "J14", *COMMON)
study("clean", "--dataset", "musr", "--judge", "J14", *COMMON)
# Separate deliberate acquisition stage; pool must freeze across both datasets.
study("acquire-perturbations", "--dataset", "mmlu-pro", *COMMON)
study("acquire-perturbations", "--dataset", "musr", *COMMON)
study("preflight", *COMMON)
# Separate deliberate victim stage.
study("evaluate-perturbations", "--dataset", "mmlu-pro", "--judge", "J8", *COMMON)
study("evaluate-perturbations", "--dataset", "musr", "--judge", "J8", *COMMON)
study("evaluate-perturbations", "--dataset", "mmlu-pro", "--judge", "J14", *COMMON)
study("evaluate-perturbations", "--dataset", "musr", "--judge", "J14", *COMMON)
study("report")
study("export")
```

A safe smaller invocation may append `"--stop-after", "100"` to clean, acquisition
or victim calls. Continue with the exact same command/plan and `--resume`; this
bounds new committed calls without changing the scientific schedule. This option
is unavailable for smoke, whose prefix is fixed. Do not choose a new root to evade
an unsafe or exhausted existing journal.

After a reset, rerun setup with the SAME commit. The restore cell uses only the
latest verified safe compact Drive snapshot. An unsafe latest snapshot stops:
return its private evidence for review, without retrying unknown generations.
A changed runtime fingerprint is a blocker; do not delete access receipts to
force a new precision/runtime into an existing run.

## Expected files and handoff

Run root: `/content/pact-adjudication/runs/pact-adjudication-diagnostic-001`.
Persistent root: `/content/drive/MyDrive/PACT/adjudication/pact-adjudication-diagnostic-001`.
Local bundles: `/content/pact-adjudication/runs/bundles/`.

The run contains parent_import_receipts.json, bank.json, private selected parent
evidence, candidate_bank_manifest.jsonl, joint_failure_map.json,
rationale_review_sample.private.jsonl, adjudication_plan.json, model_registry.json,
prompt_contracts.json, clean_requests.jsonl, clean_per_task.jsonl,
clean_comparisons.json, attack_eligibility.json, perturbation_plan.json,
perturbation_attempts.jsonl, accepted_perturbations.private.jsonl, pool.json,
coverage_invariance_checks.json, attacked_per_task.jsonl, q_prefix_robustness.json,
rationale_tradeoff_report.json, resource_usage.json, missingness.json, checksums.json,
REPORT.md, CODEX_HANDOFF.md, and immutable call/preflight/identity records.
Pool-dependent files appear when acquisition is terminal; missing stages are
reported as missing rather than empty successful experiments.

Return the latest matching `pact-adjudication-diagnostic-001-PRIVATE-<stamp>.zip`
and `...-SANITIZED-<stamp>.zip`, with both SHA256 values. PRIVATE is for local
review only and contains benchmark text/prompts/decodable IDs. Do not commit it.
No outcome automatically authorizes training, more tasks/seeds, or another study.
