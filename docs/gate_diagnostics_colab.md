# Gate diagnostics and selector comparison: exact commands

Local offline path (use an absent private directory **outside Git**):

```bash
python -m pip install -e ".[gate]"
python -m pact gate-diagnostics import-parent --run-dir /var/tmp/pact-gate-diagnostics-001 --bundle pact-selective-correction-001-PRIVATE-1791993400383124336.zip --sha256 b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449
python -m pact gate-diagnostics analyze --run-dir /var/tmp/pact-gate-diagnostics-001
python -m pact gate-diagnostics export --run-dir /var/tmp/pact-gate-diagnostics-001
```

The local import above has already been executed in this workspace. Do not rerun import into that existing directory; `analyze` verifies its receipt and can reconstruct reports again. No model/checkpoint is required for offline analysis. No fitting routine is invoked.

Fresh Colab: use [notebook 23](../notebooks/23_gate_diagnostics_selector_colab.ipynb), or paste the following cells in order. Supply the full reviewed commit after pushing these changes. Default flags leave all model access and generation off. The parent ZIP includes actual saved gate coefficients, but the selector uses no gate model or adapter. The exact pristine Qwen3-8B revision/tokenizer/template comes from the parent identity, verified against official weights in `/content/pact-selector/cache`. A resumed child keeps its pinned source and runtime identity; do not migrate silently.

# Prospective selector contract comparison

Exact closed selective parent; 202 views, two fresh arms, at most 404 attempts / 206,848 reserved output tokens. No training. Default is model-free plan. Run smoke separately (at most 16 included calls), review its exported artifacts, then explicitly invoke continuation. Raw evidence stays private outside Git. GPU behavior is unverified until returned evidence is audited.

```python
# Cell 1 — mount Drive, pin the reviewed code and install existing dependencies.
from pathlib import Path
import os, re, sys, subprocess, json, time
from google.colab import drive
drive.mount('/content/drive')
REPO_URL = 'https://github.com/Soqoro/Pact.git'
GIT_REF = input('Full 40-character reviewed and pushed commit SHA: ').strip()
assert re.fullmatch(r'[0-9a-fA-F]{40}', GIT_REF), 'Full reviewed SHA required'
SCRATCH = Path('/content/pact-selector')
CHECKOUT = SCRATCH / 'checkout'
RUN = SCRATCH / 'runs' / 'pact-anchor-selector-contract-002'
PERSISTENT = Path('/content/drive/MyDrive/PACT/selector-contract/pact-anchor-selector-contract-002')
CACHE = SCRATCH / 'cache'
SCRATCH.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(['git', 'clone', REPO_URL, str(CHECKOUT)], check=True)
assert not subprocess.check_output(['git', '-C', str(CHECKOUT), 'status', '--porcelain'], text=True).strip()
assert subprocess.check_output(['git', '-C', str(CHECKOUT), 'remote', 'get-url', 'origin'], text=True).strip() == REPO_URL
subprocess.run(['git', '-C', str(CHECKOUT), 'fetch', 'origin', GIT_REF], check=True)
subprocess.run(['git', '-C', str(CHECKOUT), 'checkout', '--detach', GIT_REF], check=True)
assert subprocess.check_output(['git', '-C', str(CHECKOUT), 'rev-parse', 'HEAD'], text=True).strip().lower() == GIT_REF.lower()
subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', str(CHECKOUT)+'[model,gate]'], check=True)
os.environ['PYTHONPATH'] = str(CHECKOUT/'src')
sys.path.insert(0, str(CHECKOUT/'src'))
os.chdir(CHECKOUT)
```

```python
# Cell 2 — logged CLI wrapper; heartbeat during model loading.
from pact.util import read_json, file_hash

def study(stage, *options):
    command = [sys.executable, '-u', '-m', 'pact', 'selector-contract', stage,
               '--run-dir', str(RUN), '--persistent', str(PERSISTENT),
               '--cache-dir', str(CACHE), *map(str, options)]
    log = SCRATCH / f'selector-{stage}-{time.time_ns()}.log'
    print('Starting:', stage, 'Log:', log, flush=True)
    with log.open('w') as output:
        proc = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT)
        with log.open() as reader:
            heartbeat = time.monotonic()
            while True:
                text = reader.read()
                if text:
                    print(text, end='', flush=True)
                if proc.poll() is not None:
                    print(reader.read(), end='', flush=True)
                    break
                if time.monotonic() - heartbeat >= 30:
                    print(stage, 'still running; log:', log, flush=True)
                    heartbeat = time.monotonic()
                time.sleep(1)
    if proc.returncode:
        raise RuntimeError(f'{stage} failed ({proc.returncode}). Preserve scratch and send final error lines. No automatic retry.')
```

```python
# Cell 3 — restore latest child OR import the exact parent and freeze a new plan.
# No new source allocation or exposure-inventory certification is needed.
PARENT_SHA = 'b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449'
PARENT_DRIVE = Path('/content/drive/MyDrive/PACT/selective-correction/pact-selective-correction-001/bundles/pact-selective-correction-001-PRIVATE-1791993400383124336.zip')
PARENT_LOCAL = SCRATCH / 'sources' / PARENT_DRIVE.name
PARENT_LOCAL.parent.mkdir(parents=True, exist_ok=True)
if not (RUN/'selector_child_plan.json').exists():
    snapshots = sorted((PERSISTENT/'snapshots').glob('*'))
    if snapshots:
        assert not RUN.exists(), 'Partial local child exists: preserve and inspect; do not overwrite.'
        study('restore')  # newest unsafe snapshot is an error; never fall back
    else:
        if not (RUN/'parent_import_receipt.json').exists():
            assert not RUN.exists(), 'Partial local import exists; inspect before retrying.'
            assert PARENT_DRIVE.is_file(), f'Required PRIVATE parent missing: {PARENT_DRIVE}'
            from pact.storage import storage_operation
            if not PARENT_LOCAL.exists():
                print(storage_operation('bundle-restore', PARENT_DRIVE, PARENT_LOCAL,
                                        sha256=PARENT_SHA, timeout_seconds=600))
            assert file_hash(PARENT_LOCAL) == PARENT_SHA
            study('import-parent', '--bundle', PARENT_LOCAL, '--sha256', PARENT_SHA)
        study('plan')
study('inspect')
PLAN_HASH = read_json(RUN/'state.json')['plan_hash']
PLAN = read_json(RUN/'selector_child_plan.json')
print('PLAN_HASH:', PLAN_HASH)
print('Views:', PLAN['expected_views'], 'Calls:', PLAN['expected_calls'], 'Smoke calls:', 2*len(PLAN['smoke_views']))
assert PLAN['expected_views'] == 202 and PLAN['expected_calls'] == 404
```

Stop here for the default, model-free path. The following stages require explicit invocation. Only pristine Qwen3-8B/J8 is loaded. No Q/L/M weights or adapter checkpoints are needed. If the runtime resets, rerun cells 1–3 at the same pinned commit; restore checks the latest compact snapshot.

```python
# Cell 4 — explicit access/tokenizer preflight (no generation).
RUN_PREFLIGHT = False
if RUN_PREFLIGHT:
    study('preflight')
else:
    print('Preflight not invoked. Set RUN_PREFLIGHT = True when ready for Colab inference.')
```

```python
# Cell 5 — explicit included smoke; exports PRIVATE and SANITIZED bundles and stops.
RUN_SMOKE = False
if RUN_SMOKE:
    study('smoke', '--execute', '--plan-hash', PLAN_HASH)
else:
    print('Smoke not invoked. At most 16 INCLUDED calls; no prompt or task changes after it.')
```

Review the smoke status and exports. Poor compliance or accuracy does not change the frozen plan. If you decide to continue, invoke the next cell separately; do not use Run All to combine smoke and full execution.

```python
# Cell 6 — separately invoked continuation on the same frozen requests.
RUN_REMAINDER = False
if RUN_REMAINDER:
    study('run', '--execute', '--plan-hash', PLAN_HASH)
else:
    print('Continuation not invoked. It reuses completed child calls and completes the remaining planned views.')
```

```python
# Cell 7 — reconstruct/report/export without generation.
study('report')
study('export')
print(json.dumps(read_json(RUN/'resource_usage.json'), indent=2))
print('Private bundle directory:', PERSISTENT/'bundles')
print('Return the matching latest PRIVATE and SANITIZED pair plus SHA256 values. Do not publish the private ZIP.')
```

Artifacts: offline score/weight/signal/checker/collision/grid/tuning tables, escaped PRIVATE opportunity dossier, audit and checksums; child frozen plan and exact prompt diff, immutable call intents/results/resources, per-view PRIVATE outcomes, strict/fallback and paired/attack aggregate reports, compact verified snapshots, separate PRIVATE/SANITIZED ZIPs.

Only the child can generate: 404 attempts maximum including smoke, 206,848 reserved output tokens. New source/checker/rewrite calls, fits, updates and teacher-forced forwards are zero. Unresolved intents or an unsafe latest snapshot stop recovery. No manual deletion of lock/intents or safety-flag editing. Missing files are prerequisites, never successful anchor fallback.
