# Optional rationale-span Colab sequence

This is the executable cell sequence from [notebook 21](../notebooks/21_rationale_spans_colab.ipynb). Review and push the code first; substitute the full reviewed commit. No real inference is authorized by the implementation request. All execution flags start false. Use an already reviewed PRIVATE forensics bundle, not the original parent or sanitized summary.

# Optional reviewed rationale-span intervention

GPU behavior is unverified. Start only after two independent private reviews. All inference flags default false; do not enable every flag and Run All. No dataset download or adapter checkpoint is required. Use the exact reviewed PRIVATE forensics bundle, then approve the artifact-bound plan separately. A100 80 GB has sufficient nominal weight capacity for one BF16 14B judge; actual fit remains unverified. Keep one model resident.


Required pristine model checkpoints (automatically restored by the existing native backend on an approved generation stage):

- J8: `Qwen/Qwen3-8B@b968826d9c46dd6066d109eabc6255188de91218`.
- J14: `Qwen/Qwen3-14B@40c069824f4251a91eefaf281ebe4c544efd3e18`.

Metadata and weight bytes must match the completed parent's receipts. No preparation, task-SFT or receiver-SFT adapters are loaded. Cache root is `/content/pact-spans/cache`; the reviewed forensics bundle supplies the task/candidate banks and provenance. Do not substitute the earlier preparation-model revision.

## Cell 1

```python
from pathlib import Path
import os, sys, re, subprocess, json, time, tempfile, getpass
from urllib.parse import urlsplit
REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "REPLACE_WITH_FULL_REVIEWED_PUSHED_COMMIT_SHA"
PRIVATE_REPOSITORY = False
RUN_ID = "pact-rationale-span-intervention-001"
SCRATCH = Path("/content/pact-spans")
CHECKOUT = SCRATCH / "checkout"
RUN = SCRATCH / "runs" / RUN_ID
CACHE = SCRATCH / "cache"
PERSISTENT = Path("/content/drive/MyDrive/PACT/rationale-spans") / RUN_ID
FORENSICS = SCRATCH / "reviewed-forensics"
REVIEW_BUNDLE = Path("/content/drive/MyDrive/PACT/forensics/REPLACE_WITH_REVIEWED_PRIVATE_BUNDLE.zip")
REVIEW_SHA256 = "REPLACE_WITH_REVIEWED_PRIVATE_SHA256"
RESTORE_EXISTING_CHILD = False  # True after a reset of an already planned child
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF), "Set reviewed pushed commit."
from google.colab import drive
drive.mount("/content/drive")
SCRATCH.mkdir(parents=True, exist_ok=True)
```

## Cell 2

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

## Cell 3

```python
from pact.util import read_json, file_hash, digest
from pact.storage import storage_operation

def command(group, stage, *options):
    log_path = SCRATCH / f"{group}-{stage}-{time.time_ns()}.log"
    print("Starting:", group, stage, "Log:", log_path, flush=True)
    with log_path.open("w") as log:
        process = subprocess.Popen([sys.executable, "-u", "-m", "pact", group, stage, *map(str, options)],
                                   stdout=log, stderr=subprocess.STDOUT)
        offset = 0
        while process.poll() is None:
            time.sleep(5)
            with log_path.open() as stream:
                stream.seek(offset); text = stream.read(); offset = stream.tell()
            if text: print(text, end="", flush=True)
        with log_path.open() as stream:
            stream.seek(offset); print(stream.read(), end="", flush=True)
    if process.returncode:
        raise RuntimeError(f"{stage} stopped; preserve scratch and {log_path}. No automatic retry.")

def study(stage, *options):
    command("rationale-spans", stage, "--run-dir", RUN, "--persistent", PERSISTENT, *options)
```

Restore only a safe latest child snapshot. Do not restore the parent to continue its calls. For a new child, the input bundle must already contain completed independent reviews.


## Cell 4

```python
if RESTORE_EXISTING_CHILD:
    if not RUN.exists(): study("restore")
    from pact.studies.rationale_spans import load, inspect
    plan = load(RUN)
    intents, results, unresolved = inspect(RUN, plan)
    assert read_json(RUN / "state.json")["recovery_safe"] and not unresolved
    print("Restored plan:", digest(plan), "committed:", len(results))
else:
    assert re.fullmatch(r"[0-9a-f]{64}", REVIEW_SHA256)
    local_bundle = SCRATCH / "reviewed-forensics.zip"
    if not local_bundle.exists():
        storage_operation("bundle-restore", REVIEW_BUNDLE, local_bundle,
                          sha256=REVIEW_SHA256, timeout_seconds=600)
    assert file_hash(local_bundle) == REVIEW_SHA256
    if not FORENSICS.exists():
        command("adjudication-forensics", "import-bundle", "--run-dir", FORENSICS,
                "--bundle", local_bundle, "--sha256", REVIEW_SHA256)
    study("prepare", "--forensics", FORENSICS)
    study("validate")
    status = read_json(RUN / "validated_edits.json")
    print("Review status:", status["status"], "eligible units:", len(status["edits"]))
    assert status["reviews_complete"], "Complete both independent review passes before preparing this child."
```

Metadata-only preflight downloads the two official tokenizers/configs and checks weight metadata. It does not generate responses or load model weights. If there are no eligible edits, stop as not testable; do not replace slots. Freeze a plan on this pinned Colab environment before the separate user decision.


## Cell 5

```python
METADATA_PREFLIGHT = False
if METADATA_PREFLIGHT:
    assert read_json(RUN / "validated_edits.json")["edits"], "No eligible spans; not testable under this design."
    study("preflight", "--cache-dir", CACHE, "--execute")
    study("plan")
    study("export")
if (RUN / "span_plan.json").exists():
    PLAN_HASH = digest(read_json(RUN / "span_plan.json"))
    print("PLAN_HASH:", PLAN_HASH)
    print("BUDGET:", read_json(RUN / "span_plan.json")["budget"])
    print("Review authorization.template.json and record the user's decision separately.")
```

Only after the user approves this exact plan: place their completed authorization JSON on Drive. Do not populate approval automatically from review labels or a positive outcome. The template is created with approved=false and origin=null.


## Cell 6

```python
IMPORT_USER_DECISION = False
APPROVAL_FILE = Path("/content/drive/MyDrive/PACT/rationale-spans/user-authorization.json")
if IMPORT_USER_DECISION:
    assert APPROVAL_FILE.is_file(), "Explicit artifact-bound user decision missing."
    study("authorize", "--file", APPROVAL_FILE)
```

Included two-unit smoke: at most 36 total calls across both judges. Each successful invocation persists and exports. Review its bundle before the remaining planned calls.


## Cell 7

```python
EXECUTE_SMOKE = False
if EXECUTE_SMOKE:
    PLAN_HASH = digest(read_json(RUN / "span_plan.json"))
    for judge in ("J8", "J14"):
        study("smoke", "--judge", judge, "--execute", "--resume", "--plan-hash", PLAN_HASH, "--cache-dir", CACHE)
    study("report")
    study("export")
```

Remaining planned J8 calls only, after review of the included smoke. Completed child requests are reused.


## Cell 8

```python
EXECUTE_J8 = False
if EXECUTE_J8:
    PLAN_HASH = digest(read_json(RUN / "span_plan.json"))
    study("evaluate", "--judge", "J8", "--execute", "--resume", "--plan-hash", PLAN_HASH, "--cache-dir", CACHE)
    study("report")
    study("export")
```

Remaining planned J14 calls only, after review of the included smoke. Completed child requests are reused.


## Cell 9

```python
EXECUTE_J14 = False
if EXECUTE_J14:
    PLAN_HASH = digest(read_json(RUN / "span_plan.json"))
    study("evaluate", "--judge", "J14", "--execute", "--resume", "--plan-hash", PLAN_HASH, "--cache-dir", CACHE)
    study("report")
    study("export")
```

Return the PRIVATE and SANITIZED ZIPs with the SAME export timestamp and both printed SHA256 values. Keep PRIVATE files out of Git/public pages. No outcome authorizes another experiment.


## Cell 10

```python
if (RUN / "span_plan.json").exists():
    study("report")
    study("export")
```

