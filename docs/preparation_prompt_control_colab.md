# Run the fixed 72-call prompt control after a Colab restart

Review, commit and push the implementation locally, then use its full SHA in cell 1.
Use the same L4 runtime. These six cells load the existing final adapters and generate
72 answer-only responses; they never retrain. The comparison is the completed prepared
packet probe, not the old engineering actors or an unmatched seed. Real execution
remains unverified until a returned bundle is audited.

The two source ZIPs and full training snapshot must remain on Drive. No dataset
re-download or restoration of optimizer history is needed. Keep this run ID fixed;
a reset resumes the latest safe snapshot and never resets the attempted-call budget.

**Cell 1 — Mount Drive and pin the newly published code**

```python
from pathlib import Path
import os, re, subprocess, sys, json
from google.colab import drive

GIT_REF = "PASTE_NEW_FULL_COMMIT_SHA"
REPO_URL = "https://github.com/Soqoro/Pact.git"
assert re.fullmatch(r"[0-9a-fA-F]{40}", GIT_REF), "Set the new published full SHA."
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
assert git("-C", str(CHECKOUT), "remote", "get-url", "origin") == REPO_URL
subprocess.run(["git", "-C", str(CHECKOUT), "fetch", "--depth", "1", "origin", GIT_REF], check=True)
subprocess.run(["git", "-C", str(CHECKOUT), "checkout", "--detach", GIT_REF], check=True)
assert git("-C", str(CHECKOUT), "rev-parse", "HEAD").lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
sys.path.insert(0, str(CHECKOUT / "src"))
os.environ["HF_HOME"] = str(SCRATCH / "cache/huggingface")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
print("Pinned code:", GIT_REF)
```

**Cell 2 — Install and check dependencies**

```python
from pact.colab import install_dependencies, cpu_checks
install_dependencies(CHECKOUT)
cpu_checks(CHECKOUT)
```

**Cell 3 — Recover the two source ZIPs and verify the frozen plan**

```python
from pact.storage import storage_operation
from pact.util import file_hash
from pact.training.prompt_control import load_prompt_config, prompt_plan
from pact.environment import runtime_fingerprint
import torch

TIMEOUT = 600
DRIVE = Path("/content/drive/MyDrive/PACT")
PREPARATION = DRIVE / "actor-preparation/qwen3-preparation-120-001"
CONFIG = CHECKOUT / "experiments/preparation_prompt_control.json"
config = load_prompt_config(CONFIG)
TRAIN_ZIP = SCRATCH / "sources/preparation-training.zip"
PROBE_ZIP = SCRATCH / "sources/preparation-probe.zip"
sources = [
    (PREPARATION / "training/bundles/qwen3-preparation-120-001-handoff-1789930640697369191.zip",
     TRAIN_ZIP, config["training_bundle_sha256"]),
    (PREPARATION / "probe/bundles/qwen3-preparation-probe-001-handoff-1789972354005267043.zip",
     PROBE_ZIP, config["probe_bundle_sha256"]),
]
for source, target, expected in sources:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print(storage_operation("bundle-restore", source, target,
                                sha256=expected, timeout_seconds=TIMEOUT))
    assert file_hash(target) == expected, "Source ZIP checksum mismatch."
PLAN = prompt_plan(config, TRAIN_ZIP, PROBE_ZIP)
print("Frozen request hash:", PLAN["requests_hash"])
print("Budget:", PLAN["budget"])
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
assert torch.cuda.is_bf16_supported()
print("GPU:", torch.cuda.get_device_name(0))
print("Runtime:", runtime_fingerprint())
assert runtime_fingerprint() == PLAN["models"]["base"]["runtime_fingerprint"], "Runtime changed; stop and return this output."
```

**Cell 4 — Restore the compact final adapters**

```python
from pact.training.preparation_restore import restore_preparation_references
from pact.training.preparation_runner import preparation_references

TRAIN = SCRATCH / "actor-preparation/qwen3-preparation-120-001-inference"
SNAPSHOT = PREPARATION / "training/snapshots/1789930640656395583-479df47c14d9"
if not TRAIN.exists():
    print(restore_preparation_references(SNAPSHOT, TRAIN, timeout_seconds=TIMEOUT))
parent = preparation_references(PLAN["training_design"], TRAIN)
assert parent.reference_manifest_hash == PLAN["reference_manifest_hash"]
print("Final 90-step adapters verified:", parent.reference_hashes)
```

**Cell 5 — Run or resume the 72-call diagnostic**

```python
from pact.training.prompt_control_runner import restore_prompt_control

RUN_ID = config["run_id"]
RUN = SCRATCH / "prompt-control" / RUN_ID
DURABLE = DRIVE / "prompt-control" / RUN_ID
if not RUN.exists():
    folder = DURABLE / "snapshots"
    saved = sorted(p for p in folder.iterdir() if p.is_dir()) if folder.exists() else []
    if saved:
        print(restore_prompt_control(saved[-1], RUN, timeout_seconds=TIMEOUT))

args = [
    sys.executable, "-u", "-m", "pact", "preparation-prompt-control",
    "--config", str(CONFIG),
    "--training-bundle", str(TRAIN_ZIP), "--probe-bundle", str(PROBE_ZIP),
    "--training-root", str(TRAIN), "--run-dir", str(RUN),
    "--persistent", str(DURABLE), "--cache-dir", str(SCRATCH / "cache/models"),
    "--storage-timeout", str(TIMEOUT), "--execute",
]
if RUN.exists():
    args.append("--resume")
RESULT = None
with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end="", flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "exit_code" in value and "path" in value:
            RESULT = value
    code = process.wait()
if RESULT:
    print("Local ZIP:", RESULT["path"])
    print("Drive ZIP:", RESULT.get("persistent_bundle"))
    print("SHA256:", RESULT["sha256"])
if code:
    raise RuntimeError("Diagnostic stopped. Preserve scratch and return the error and any local ZIP.")
assert RESULT is not None
assert RESULT["status"] == "prompt_control_complete_local"
assert RESULT["completed_records"] == RESULT["committed_calls"] == 72
assert RESULT["persistent_copy_verified"]
assert RESULT["training_executed"] is False
```

A failure or unsafe snapshot is not permission to delete a run, restore an older
snapshot, change the run ID or generate replacements. Preserve its journal for review.

**Cell 6 — Show results and download the review ZIP**

```python
from pact.util import read_json
from google.colab import files

report = read_json(RUN / "report.json")
print(json.dumps({
    "summary": report["summary"],
    "by_family": report["by_family"],
    "generation_accounting": report["generation_accounting"],
    "full_pact_ready": report["full_pact_ready"],
}, indent=2))
assert file_hash(Path(RESULT["path"])) == RESULT["sha256"]
print("SHA256:", RESULT["sha256"])
print("Drive copy:", RESULT["persistent_bundle"])
files.download(RESULT["path"])
```

Return the downloaded ZIP, SHA256 and cell 6 output. Expected durable bundle:
`/content/drive/MyDrive/PACT/prompt-control/qwen3-preparation-prompt-control-001/bundles/`.
The archive retains raw responses, comparator provenance, failures, tokens and paired
counts. It is a diagnostic result, not training pairs or a PACT efficacy claim.
