# Benchmark breadth: exact Colab sequence

Use [notebook 10](../notebooks/10_benchmark_breadth_colab.ipynb), or the cells below.
Review/commit/push the implementation yourself first. Replace `GIT_REF` with that
full 40-character commit; the implementation is currently uncommitted, so this
document cannot name its future Git SHA. Use a fresh child run, never an old study
ID. Select one GPU with BF16 support and enough scratch disk for all four official
model caches; one model is resident at a time. GPU compatibility is unverified.

Accept official access terms for Llama, Mistral where required, and GPQA if selected.
Store `HF_TOKEN` in Colab Secrets with notebook access. No old adapter checkpoint
is required. Only GPQA needs the historical **data/partition JSON**, not weights.
All raw benchmark data must live outside the Git checkout. Never paste tokens into
commands or repository URLs. The notebook's default is plan only, no generation.

## 1. Mount and parameters

```python
from pathlib import Path
import os, sys, subprocess, re, json, getpass
from google.colab import drive, userdata
drive.mount('/content/drive')

GIT_REF = 'PASTE_REVIEWED_FULL_COMMIT_SHA'
REPO_URL = 'https://github.com/Soqoro/Pact.git'
DATASET = 'mmlu-pro'  # choose ONE from the table below
RESUME = False       # True after a reset of an already planned study
SCRATCH = Path('/content/pact-breadth')
CHECKOUT = SCRATCH / 'checkout'
CACHE = SCRATCH / 'cache'
SOURCE = SCRATCH / 'sources' / DATASET
DATA = SCRATCH / 'prepared' / (DATASET + '.json')
RUN = SCRATCH / 'runs' / ('pact-breadth-' + DATASET + '-001')
PERSISTENT = Path('/content/drive/MyDrive/PACT/breadth') / RUN.name
SCORER_PYTHON = None
GPQA_PARENT = None
```

## 2. Pinned checkout and existing dependencies

```python
assert re.fullmatch(r'[0-9a-fA-F]{40}', GIT_REF)
SCRATCH.mkdir(parents=True, exist_ok=True)
def git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True,
                            env={**os.environ, 'GIT_TERMINAL_PROMPT':'0'})
    if result.returncode:
        raise RuntimeError('Verify repository access and pushed SHA; output suppressed.')
    return result.stdout.strip()
if not CHECKOUT.exists():
    git('clone', '--filter=blob:none', REPO_URL, str(CHECKOUT))
assert not git('-C', str(CHECKOUT), 'status', '--porcelain'), 'Preserve local edits.'
assert git('-C', str(CHECKOUT), 'remote', 'get-url', 'origin') == REPO_URL
git('-C', str(CHECKOUT), 'fetch', '--depth', '1', 'origin', GIT_REF)
git('-C', str(CHECKOUT), 'checkout', '--detach', GIT_REF)
assert git('-C', str(CHECKOUT), 'rev-parse', 'HEAD') == GIT_REF.lower()
os.chdir(CHECKOUT)
os.environ['PYTHONPATH'] = str(CHECKOUT / 'src')
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
subprocess.run([sys.executable, '-c',
    'from pact.colab import install_dependencies; from pathlib import Path; install_dependencies(Path.cwd())'], check=True)
try:
    token = userdata.get('HF_TOKEN')
except Exception:
    token = getpass.getpass('Authorized Hugging Face token (hidden): ')
if token:
    os.environ['HF_TOKEN'] = token
token = None
```

The existing installer preserves the installed Torch build and pins the working
Transformers/PEFT/Accelerate/PyArrow versions. Do not upgrade or quantize models to
work around a failed preflight. A runtime/source change cannot resume implicitly.

## 3. Streaming command helper and source plan

```python
def command(*args):
    print('Starting:', *map(str, args), flush=True)
    with subprocess.Popen([sys.executable, '-u', '-m', 'pact', *map(str, args)],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True) as process:
        for line in process.stdout:
            print(line, end='', flush=True)
        code = process.wait()
    if code:
        raise RuntimeError('Stage stopped. Preserve scratch; no automatic retry.')

def study(stage, *options):
    command('breadth', stage, '--run-dir', RUN, '--persistent', PERSISTENT, *options)

if RESUME and not RUN.exists():
    study('restore')  # latest verified compact snapshot only; refuses unsafe state

if not (RUN / 'plan.json').exists():
    assert not list((PERSISTENT / 'snapshots').glob('*')), 'Existing study: use RESUME=True.'
    if not DATA.exists():
        args = ['benchmarks', 'prepare', '--dataset', DATASET,
                '--source-dir', SOURCE, '--output', DATA, '--download']
        names = ('mmlu-pro','musr','math-500','mbpp-plus','gpqa','livebench')
        prior = sorted(p for p in DATA.parent.glob('*.json')
                       if p.name in {n+'.json' for n in names} and p != DATA)
        if prior:
            exposure = SCRATCH / 'exposure-index.json'
            command('benchmarks','exposure-index','--prepared',*prior,'--output',exposure)
            args += ['--exposure', exposure]
        if GPQA_PARENT is not None:
            args += ['--parent', GPQA_PARENT]
        command(*args)
    study('plan', '--data', DATA)

result = subprocess.run([sys.executable, '-c',
    'import sys; from pathlib import Path; from pact.studies.breadth import load; '
    'from pact.util import digest; print(digest(load(Path(sys.argv[1]))))', str(RUN)],
    check=True, capture_output=True, text=True)
PLAN_HASH = result.stdout.strip()
COMMON = ['--plan-hash', PLAN_HASH, '--cache-dir', CACHE]
SCORE_OPTIONS = ['--scorer-python', SCORER_PYTHON] if SCORER_PYTHON else []
print('PLAN_HASH:', PLAN_HASH)
print(json.loads((RUN / 'budget_plan.json').read_text()))
```

Before preparing another dataset, restore previous prepared manifests from their
private plans, so the exposure index sees earlier locked groups too. No benchmark
results are needed. After a reset, repeat cells 1-3 with `RESUME=True` and the SAME
Git SHA. Do not choose an older snapshot, remove a lock blindly or re-plan an ID.

## 4. First MMLU-Pro smoke: these are the first model commands

```python
assert DATASET == 'mmlu-pro'
study('preflight', *COMMON, '--execute')
study('smoke', *COMMON, '--execute', '--phase', 'A')
study('score', *COMMON)
study('report')
study('export')
```

Preflight resolves all four official model/tokenizer identities and checks access,
disk, GPU and selected private-prompt lengths before any generation. The smoke
dispatches six Q, six L, six M calls, one model at a time. It uses the exact two-task
prefix of the 140-task plan. A partial full-cohort report is expected after smoke;
there should be 18 committed attempts and no unresolved calls. Return the exports
for review; there is no automatic full-cohort continuation or support gate.

## 5. Explicit Phase A continuation, one selected dataset

Run each line as its own cell after choosing to execute that stage. For MMLU the
smoke requests are reused, not regenerated. These same commands work for each
independently prepared dataset below.

```python
study('private', *COMMON, '--execute', '--phase', 'A', '--model', 'Q')
```

```python
study('private', *COMMON, '--execute', '--phase', 'A', '--model', 'L')
```

```python
study('private', *COMMON, '--execute', '--phase', 'A', '--model', 'M')
```

```python
study('score', *COMMON, *SCORE_OPTIONS)
study('report')
study('export')
```

For more frequent durable boundaries append, for example, `--stop-after 30` to a
single family invocation. It means at most thirty NEW calls, preserving the same
request plan and overall ceiling. Repeat explicitly to continue that family.
Already committed calls are reused. An unknown dispatch window still stops.

## 6. Explicit Phase B for the four cores only

Run separately from A, after all nine private calls/task are present. It does not
depend on positive support. GPQA and LiveBench reject these stages in this design.
Each following call can be a separate cell; do not put this in default Run All.

```python
assert DATASET in ('mmlu-pro', 'musr', 'math-500', 'mbpp-plus')
study('revisions', *COMMON, '--execute', '--phase', 'B', '--model', 'Q')
```

```python
study('revisions', *COMMON, '--execute', '--phase', 'B', '--model', 'L')
```

```python
study('revisions', *COMMON, '--execute', '--phase', 'B', '--model', 'M')
```

```python
study('readout', *COMMON, '--execute', '--phase', 'B')
```

```python
study('score', *COMMON, *SCORE_OPTIONS)
study('report')
study('export')
```

## Per-dataset prerequisites and commands

Set `DATASET` before cell 1 and follow cells 1-3 for that single child. These are
separate datasets/stages, not one portfolio job.

| DATASET | Source/scorer prerequisite | Preflight after plan | Allowed later stages |
|---|---|---|---|
| `mmlu-pro` | Public official test parquet; strict MCQ | `study('preflight', *COMMON, '--execute')` | smoke/private/score, then separately B |
| `musr` | Official three CSVs; full narratives; strict MCQ | Same | Same |
| `math-500` | Official test JSONL; pinned scorer venv below | `study('preflight', *COMMON, '--execute', *SCORE_OPTIONS)` | Same, passing `SCORE_OPTIONS` to score |
| `mbpp-plus` | Official v0.2.0 asset; isolated EvalPlus | `study('preflight', *COMMON, '--execute', *SCORE_OPTIONS)` when verified; otherwise explicitly append `--allow-pending-scoring` | Same generation stages; score/export-jobs then import, never ordinary notebook execution |
| `gpqa` | Authorized official gate plus exact old parent partition JSON | `study('preflight', *COMMON, '--execute')` | A only; new32, never old32 |
| `livebench` | Verified official 2026-06-25 inventories and native scorers | Currently **blocked at prepare** with `requested_release_unavailable` | A only if source proof becomes available through a reviewed update |

For MuSR/Math/MBPP/GPQA, the optional smoke is also
`study('smoke', *COMMON, '--execute', '--phase', 'A')`; it always reuses the selected
two-task prefix. All names in the table are exact CLI choices.

Math prerequisite (before its preflight; installs no model):

```python
MATH_ENV = SCRATCH / 'math-evaluator'
subprocess.run([sys.executable, '-m', 'venv', str(MATH_ENV)], check=True)
SCORER_PYTHON = MATH_ENV / 'bin/python'
subprocess.run([str(SCORER_PYTHON), '-m', 'pip', 'install',
    'https://github.com/huggingface/Math-Verify/archive/ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b.zip',
    'latex2sympy2_extended==1.11.0', 'sympy==1.14.0',
    'mpmath==1.3.0', 'antlr4-python3-runtime==4.13.2'], check=True)
SCORE_OPTIONS = ['--scorer-python', SCORER_PYTHON]
```

The preflight checks all selected gold references without showing them to a model.
If any official answer is not supported by the frozen parser, stop with that
dataset's artifacts; do not alter selected answers or use an LLM judge.

GPQA prerequisite: privately restore `data.json` from the completed original
`qwen3-gpqa-diamond-support-001` study (or its exact `manifest` object). Set
`GPQA_PARENT = Path('/content/pact-breadth/sources/gpqa-parent-data.json')` before
cell 3. The original private return SHA was
`8db5120f4c25bc9bb99f6c04b3d7571a1c791a5cb13899176fb3a466169b3012`.
Verify your private archive before extracting this JSON. The loader recomputes
and exactly checks its parent partition against the pinned official CSV; it will
not guess a parent from filenames or reselect the old exposed 32.

## Isolated MBPP / native scoring

Use [notebook 11](../notebooks/11_isolated_code_scoring.ipynb) on a dedicated Linux
evaluator. Colab user namespaces may be unavailable; no successful sandbox run is
claimed. Administrator-provided `bwrap` and `prlimit`, unprivileged namespaces, and
a dedicated venv outside Git/home/Drive are prerequisites. Do not mount Drive or
copy tokens into this evaluator. Copy only checksum-verified private scoring jobs
and a reviewed checkout. No GPU is needed.

On that isolated evaluator, prepare a dedicated runtime (paths are examples to
create on that evaluator, not the local development repository):

```bash
python3 -m venv /opt/pact-evaluator
/opt/pact-evaluator/bin/python -m pip install 'git+https://github.com/evalplus/evalplus.git@26d6d00bb1fd0fa37f39c99d5290da67891d1c5e'
```

If and only if the requested LiveBench source becomes verified, its separate venv
needs `git+https://github.com/LiveBench/LiveBench.git@8f8e5c381a16e3f24257776edd53471fe86f8091`.
These evaluator installs are isolated from the generation environment. Their full
dependency resolution/runtime behavior still requires the capability and scorer
checks; package pins alone are not evidence of safe execution.

Generate/export jobs in Colab without executing programs:

```python
study('score', *COMMON)
study('export-jobs')
# Transfer RUN/'scoring_jobs.json' privately with its SHA256.
import hashlib
JOBS = RUN / 'scoring_jobs.json'
print('Jobs SHA256:', hashlib.sha256(JOBS.read_bytes()).hexdigest())
study('export')
```

Run from the reviewed checkout on the evaluator:

```bash
PYTHONPATH=src python -m pact benchmarks code-probe --evaluator-python /opt/pact-evaluator/bin/python
PYTHONPATH=src python -m pact benchmarks code-run --evaluator-python /opt/pact-evaluator/bin/python --jobs /private/scoring_jobs.json --output /private/scoring_results.json
```

The worker checks hashes, pinned package source, isolation and expanded tests. It
records partial progress after each job and refuses output overwrite. A worker
crash remains an unavailable score; inspect it rather than silently rerunning or
editing the receipt. Return the private result file, verify its transport SHA256,
then import in the original Colab study:

```python
study('import-scores', *COMMON, '--scores', '/content/private/scoring_results.json')
study('report')
study('export')
```

No manually fabricated receipt, reliability-guard-only fallback or in-notebook
`exec` is valid. Different evaluator identities must not overwrite old outcomes.

## Artifacts to return

Return the latest matching `RUN_ID-PRIVATE-TIMESTAMP.zip` and
`RUN_ID-SANITIZED-TIMESTAMP.zip`, plus both printed SHA256 values. The CLI persists
them under `PERSISTENT/bundles/`; compact snapshots contain `state.zip`/receipt.
Private archives contain the selected-data plan, partitions/exposure flags, source
receipts, budgets/contracts, model/runtime identities, request/dependency journals,
raw/token records, scoring jobs/results, resources, per-task metrics, summary and
report. They omit model weights and the full source cache. Preserve the latter
privately if you need offline source reconstruction after a reset.

The sanitized archive contains aggregate `summary.json` and `report.md`, not raw
benchmark text, golds, tests or token arrays. Public summaries are still development
subset results, not official full-benchmark scores. Report missing/blocked datasets
explicitly with `benchmarks suite-report --runs-root ... --output ...`.

Offline private audit, outside every Git checkout:

```bash
PYTHONPATH=src python -m pact breadth audit --run-dir /private/new-audit-directory --bundle /private/returned-PRIVATE.zip --sha256 FULL_PRIVATE_ZIP_SHA256
```

Audit recomputes request identities, accounting and summaries without model calls.
It does not authorize further execution. Do not upload private archives to GitHub.
