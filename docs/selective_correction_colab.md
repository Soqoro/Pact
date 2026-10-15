# Selective correction: explicit Colab stages

Status: implemented with fictional CPU validation; real source collection, GPU behavior,
learned operating point and development/transfer outcomes are unverified. Human review
and span work stay deferred. Use `notebooks/22_selective_correction_colab.ipynb` or the
cells below. No Run All starts model generation: choose one stage explicitly.

## Prerequisites

- A reviewed full Git SHA containing this implementation, pushed by you.
- Access to the pinned Qwen2.5-7B, Llama3.1-8B, Mistral-7B-v0.3 and pristine Qwen3-8B
  official repositories; accept any model access conditions in your account first.
  Use a runtime Hugging Face secret for gated access; never paste a token into code/URLs.
- One BF16-capable CUDA GPU and sufficient RAM/disk for one 8B-class model and cache.
  We do not claim a measured hardware/runtime requirement from the fixtures.
- Private `prior-exposure.json`: a reviewed ID/hash-only inventory covering past uses
  **and locked groups**, including cross-dataset fingerprints, with this exact shape:

```json
{
  "reviewed_complete": true,
  "ledger_sha256": "<SHA256 of docs/benchmark_exposure_ledger.md in the pinned checkout>",
  "task_ids": ["<previously used or locked ID>"],
  "group_ids": ["<previously used or locked group digest>"],
  "content_groups": ["<existing QA content-group digest>"],
  "cross_dataset_fingerprints": ["<existing breadth fingerprint>"],
  "source_receipts": [{"name": "<reviewed inventory source>", "sha256": "<SHA256>"}]
}
```

Do not fill this with empty lists or set `reviewed_complete` merely to bypass readiness.
The implementation additionally reconstructs/excludes the entire old 1,200-task
preparation allocation and full validation-connected groups automatically. That does
not replace the cross-study/locked inventory. The subsequent metadata-only review
produced `/var/tmp/pact-selective-exposure-20261014/prior-exposure.json`, SHA256
`c1632567b6b1be2d1351f3389e0fcbc474a7aa7eb8abcb10ee2cb125a0d305c7`.
See [the inventory review](audits/PACT_SELECTIVE_EXPOSURE_INVENTORY_2026-10-14.md).
Upload that private file to the required Drive path before Cell 3. It is compatible
with pushed revision `9b65ae343b52777b5b716c9adf090959588b72c3`; no runtime code patch
or new plan is needed. This is a provenance/metadata review, not human semantic review.
Only inventory hashes/IDs are needed, not protected question text or labels. Do not
open protected datasets to manufacture this file. If the inventory cannot be supplied,
real source preparation remains blocked; the complete fixture path is still runnable.

Optional transfer additionally requires exactly:
`pact-adjudication-diagnostic-001-PRIVATE-1791903639856421059.zip`, SHA256
`2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f`.
No preparation/LoRA checkpoints are needed. Pristine weights are verified/downloaded
by the explicit native preflight/inference stages into `SCRATCH/cache`.

## Cell 1 — parameters, Drive and pinned checkout

```python
from pathlib import Path
import os, re, subprocess, sys
from google.colab import drive

drive.mount('/content/drive')
REPO_URL = 'https://github.com/Soqoro/Pact.git'
GIT_REF = 'PASTE_THE_FULL_REVIEWED_COMMIT_SHA'
assert re.fullmatch(r'[0-9a-fA-F]{40}', GIT_REF), 'Set the pushed full SHA'
SCRATCH = Path('/content/pact-selective')
CHECKOUT = SCRATCH / 'checkout'
RUN = SCRATCH / 'runs' / 'pact-selective-correction-001'
PERSISTENT = Path('/content/drive/MyDrive/PACT/selective-correction/pact-selective-correction-001')
SCRATCH.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(['git', 'clone', REPO_URL, str(CHECKOUT)], check=True)
assert not subprocess.check_output(['git', '-C', str(CHECKOUT), 'status', '--porcelain'], text=True).strip()
assert subprocess.check_output(['git', '-C', str(CHECKOUT), 'remote', 'get-url', 'origin'], text=True).strip() == REPO_URL
subprocess.run(['git', '-C', str(CHECKOUT), 'fetch', 'origin', GIT_REF], check=True)
subprocess.run(['git', '-C', str(CHECKOUT), 'checkout', '--detach', GIT_REF], check=True)
assert subprocess.check_output(['git', '-C', str(CHECKOUT), 'rev-parse', 'HEAD'], text=True).strip().lower() == GIT_REF.lower()
subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', str(CHECKOUT)+'[model,gate]'], check=True)
os.environ['PYTHONPATH'] = str(CHECKOUT / 'src')
os.chdir(CHECKOUT)
```

## Cell 2 — authenticated runtime and streaming command wrapper

```python
import json, time
from google.colab import userdata
try:
    os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')
except Exception:
    pass  # If gated model access fails, stop and resolve account access.

def study(stage, *options):
    command = [sys.executable, '-u', '-m', 'pact', 'selective-correction', stage,
               '--run-dir', str(RUN), '--persistent', str(PERSISTENT),
               '--cache-dir', str(SCRATCH / 'cache'), *map(str, options)]
    log = SCRATCH / f'{stage}-{time.time_ns()}.log'
    print('Starting:', stage, 'Log:', log, flush=True)
    with log.open('w') as output:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end='', flush=True)
            output.write(line); output.flush()
        code = proc.wait()
    if code:
        raise RuntimeError(f'{stage} stopped ({code}); preserve scratch and inspect {log}. No automatic retry.')

def read(path):
    return json.loads(Path(path).read_text())
```

## Cell 3 — restore OR prepare and freeze; zero model calls

For an existing study after runtime reset, use the latest compact snapshot. Do not
re-plan the ID or fall back to an older safe snapshot:

```python
if not (RUN / 'plan.json').exists():
    if (PERSISTENT / 'snapshots').exists():
        study('restore')
    else:
        EXPOSURE = Path('/content/drive/MyDrive/PACT/selective-correction/prior-exposure.json')
        assert EXPOSURE.is_file(), 'Reviewed prior/locked exposure inventory missing; see prerequisites'
        SOURCE = SCRATCH / 'prepared-source.json'
        if not SOURCE.exists():
            study('prepare-source', '--source', SOURCE, '--exposure', EXPOSURE, '--download')
        study('plan', '--source', SOURCE)
PLAN_HASH = read(RUN / 'state.json')['plan_hash']
study('inspect')
print('PLAN_HASH:', PLAN_HASH)
```

An unsafe restore is a stop, not permission to remove flags or rerun calls. A handoff
can alternatively be restored to an absent RUN using `import-bundle --bundle PATH
--sha256 SHA`, after checking it is the latest complete private state.

## Cell 4 — explicit preflight and first eight-call source smoke

These are commands to invoke manually after reviewing the frozen plan. They are gated
in the supplied notebook, and do not run under its default parameters.

```python
study('preflight')
study('collect-source', '--split', 'fit', '--smoke', '--execute', '--plan-hash', PLAN_HASH)
study('report')
study('export')
```

The smoke is exactly the first two FIT tasks, four source calls/task, already included
in the 3,360 fit/tuning cap. Subsequent commands reuse these eight results.

## Cell 5 — explicitly acquire the fitting and tuning evidence

Run one split at a time. There is no support gate that skips all-wrong/unanimous tasks.
Each rewrite pool freezes before checking it. If interrupted, inspect/restore, then
repeat the **same** command on the same pinned source; safe exact requests are reused.

```python
SPLIT = 'fit'  # Then run this cell again with 'threshold_tuning'.
study('collect-source', '--split', SPLIT, '--execute', '--plan-hash', PLAN_HASH)
study('acquire-rewrites', '--split', SPLIT, '--execute', '--plan-hash', PLAN_HASH)
study('build-check-bank', '--split', SPLIT, '--execute', '--plan-hash', PLAN_HASH)
study('export')
```

## Cell 6 — five CPU fits, tuning and immutable policy receipt

```python
study('fit-gates')
study('tune-thresholds')
study('freeze-policies')
study('export')
print(read(RUN / 'fit_diagnostics.json'))
print({arm: value['threshold'] for arm, value in read(RUN / 'threshold_selection.json').items()})
```

No LLM calls in these commands. Missing empirical rescue support or KEEP_ONLY remains
a valid negative outcome; continue the evaluation. Numerical optimizer failure is an
error with a consumed fit intent, not permission for extra fits or altered thresholds.

## Cell 7 — explicitly execute the 64-task source-development evaluation

```python
SPLIT = 'source_development_holdout'
study('collect-source', '--split', SPLIT, '--execute', '--plan-hash', PLAN_HASH)
study('acquire-rewrites', '--split', SPLIT, '--execute', '--plan-hash', PLAN_HASH)
study('evaluate-core', '--execute', '--plan-hash', PLAN_HASH)
study('report')
study('export')
```

This stage cannot dispatch until policies freeze. Maximum 2,240 calls including
source packets, three rewrite attempts, checks, selection and six-call reconsideration.

## Cell 8 — optional transfer, separately invoked

Only invoke if you choose to run this separate 5,156-call allocation. It does not
train, tune, regenerate old packets or reactivate human review.

```python
from pact.storage import storage_operation
PARENT = SCRATCH / 'adjudication-parent.zip'
PARENT_SHA = '2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f'
DRIVE_PARENT = Path('/content/drive/MyDrive/PACT/adjudication/pact-adjudication-diagnostic-001/bundles/pact-adjudication-diagnostic-001-PRIVATE-1791903639856421059.zip')
if not PARENT.exists():
    print(storage_operation('bundle-restore', DRIVE_PARENT, PARENT, sha256=PARENT_SHA, timeout_seconds=600))
study('import-transfer', '--bundle', PARENT, '--sha256', PARENT_SHA)
study('evaluate-transfer', '--execute', '--plan-hash', PLAN_HASH)
study('report')
study('export')
```

## Return artifacts

Return the newest matching PRIVATE/SANITIZED ZIP pair and both SHA256 values printed
by `export`, under `PERSISTENT/bundles`. Keep PRIVATE outside Git/public outputs.
It includes frozen plan/source and exposure receipt, isolated split labels, natural
banks, raw per-call shards/token arrays, frozen attack pools, pair features and spans,
five gate coefficient files, weights/support/fit diagnostics, threshold curves,
frozen policy receipt, core/transfer per-task outcomes, reports and resource records.
SANITIZED contains aggregate summaries only. No model tensors are bundled.

CPU fixture round trip (no real source/model access):

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_selective_correction.py -v
python tools/verify_selective_design.py
```
