# Reviewed-v2 allocation commands

**Real planning is currently blocked by the 3/5 versus 4/4 block and 24/40 versus
32/32 probe conflict.** Do not alter the parent, invent a history receipt or run
`--mock` on real data to bypass it. Review `stage2_allocation_methodology.md` first.
No GPU stage has been verified for this new implementation.

## Local review and exact parent inspection (no model calls)

From the repository, with the project's installed Python environment:

```bash
python -m pip install -e .
export PACT_ALLOCATION_ROOT="$HOME/pact-scratch/pact-update-allocation-crossed-002"
export PACT_PARENT_PRIVATE="$PWD/results_import/pact-revival-stage1-evaluation-amended-002-PRIVATE-1793033718300732417.zip"
python -m pact allocation inspect --run-dir "$PACT_ALLOCATION_ROOT" --parent-bundle "$PACT_PARENT_PRIVATE"
python -m pact allocation synthesis --run-dir "$PACT_ALLOCATION_ROOT"
python -m pact allocation plan --run-dir "$PACT_ALLOCATION_ROOT"
```

Use an absent scratch root for import; synthesis intentionally refuses overwrite.
The final command currently returns blockers, zero calls, and `new_plan_created:false`.
Supply additional `--history-root /private/path` arguments to `inspect` for each
available old-assay history. Inspection preserves raw IDs only in private storage.

Required real artifacts after an explicit source-contract amendment:

- The exact parent PRIVATE archive above (SHA256 `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`).
- Verified continuation-003 RECOVERY archive
  `pact-heterogeneous-receiver-training-continuation-003-RECOVERY-1792630916259050432.zip`,
  SHA256 `2ea19eae5697a12470c9cca55c3be55ba847fbe5f0a22bb71b5e1af92a0a48ba`.
  Use the existing Stage I restore/verification workflow, not arbitrary extraction.
- Exact final tensor paths recorded in the parent:
  `/content/pact-stage1/verified-final-tensors/uniform_joint_sft/{Q,L,M}/tensors.safetensors`.
  On AAI retain the existing `/content` private bind and verified checkpoint map.
- Official pinned ARC/LogiQA training source cache accepted by
  `pact.training.data.load_training_sources(..., download=False)`; a reviewed complete
  exposure JSON accepted by `pact.selective.data.validate_exposure` with current ledger hash.
- An actual reviewed history JSON with `parent_sha256`, `reviewed:true`,
  `old_stage2_executed:false`, `probe_groups_consumed:false`. These are review findings,
  not values to assert without checking external history.
- Clean pinned repository revision, original model access, native metadata and runtime.
  Existing exact AAI runtime is Python 3.13.15, Torch 2.11.0+cu130, Transformers 4.57.6,
  PEFT .18.1, Accelerate 1.12.0, Tokenizers .22.2, Hub .36.2, Jinja2 3.1.6,
  NumPy 2.1.3, Safetensors .8.0, single A100-SXM4-80GB. Existing verified tokenizer
  dependencies/CA bundle and Mistral pointer repair remain prerequisites. No dependency
  upgrade or fingerprint rewrite is authorized by this runbook.

## Stage interface (implemented, gated; not permission to bypass current blockers)

These calls document exact implemented syntax. A reviewed source amendment and
successful real plan must exist before substituting the paths below. `--execute`
is required for every model stage. Without it the command prints a zero-call plan.
Each invocation exports and stops; inspect/review its bundles before invoking the
next stage. Do not paste all cells into Run All.

```python
from pathlib import Path
import json, subprocess, sys
RUN = Path('/content/pact-allocation/runs/pact-update-allocation-crossed-002')
DURABLE = Path('/content/drive/MyDrive/PACT/allocation/pact-update-allocation-crossed-002')
CACHE = Path('/content/pact-allocation/cache')
PLAN_HASH = __import__('pact.util', fromlist=['digest']).digest(
    json.loads((RUN / 'plan.json').read_text()))

def stage(name, *options):
    subprocess.run([sys.executable, '-u', '-m', 'pact', 'allocation', name,
                    '--run-dir', str(RUN), '--persistent', str(DURABLE),
                    '--cache-dir', str(CACHE), '--plan-hash', PLAN_HASH,
                    *map(str, options)], check=True)
```

Separate reviewed invocations:

```python
stage('checkpoint', '--execute')
```
```python
stage('preflight', '--execute')
```
```python
stage('assay-smoke', '--execute')  # <=24 included calls; export/review
```
```python
stage('collect', '--execute')
```
```python
BLOCK = 0  # explicitly select one of 0..7
FAMILY = 'Q'  # Q, L or M; one invocation per branch
stage('branch', '--block', BLOCK, '--family', FAMILY, '--execute')
```

After all 24 branch exports are complete:

```python
stage('score', '--execute')
```
```python
stage('policy-freeze')
```
```python
POLICY = 'terminal_block'  # uniform, source_family, private_bank, shuffled
SEED = 113  # or 227
FAMILY = 'Q'  # Q, L or M
stage('continuation', '--policy', POLICY, '--seed', SEED, '--family', FAMILY, '--execute')
```

Invoke the requested policy/seed/family fits explicitly. Exact aliases report their
owner and consume no additional budget. After every unique fit completes:

```python
stage('policy-lock', '--execute')
```
```python
stage('evaluation-smoke', '--execute')  # <=244 included calls; export/review
```
```python
stage('evaluate', '--execute')
```
```python
stage('report')
stage('export')
```

After reset, use the **same pinned runtime/source and absolute bindings**. Restore
only to an absent root:

```bash
python -m pact allocation restore --run-dir /content/pact-allocation/runs/pact-update-allocation-crossed-002 --persistent /content/drive/MyDrive/PACT/allocation/pact-update-allocation-crossed-002
```

Unknown attempts, pending persistence, missing latest objects or changed identities
stop recovery. `--resume` applies only to a reviewed safe interrupted training
checkpoint, with its exact family/branch/policy arguments. Never clear markers or
replay an ambiguous step. Use `report`/`export` to return unsafe evidence. AAI users
use the existing verified Apptainer/runtime and **sbatch**, with private datasets
under `/dataset/$USER/PACT` and hot files on `/local`; no cluster job is submitted
by this implementation or this runbook.

Expected artifacts: resolution and import receipts; retrospective synthesis;
sealed prospective selection; frozen plan; owned attempts/events; natural packet
banks and fixed attacks; temporary typed checkpoints/rollback receipts; raw/capped
scores; five quota matrices/full schedules/aliases; final family checkpoints;
policy lock; task-level private outcomes; aggregate assay/policy comparisons,
bootstrap intervals and costs; PRIVATE, SANITIZED and RECOVERY ZIPs with checksums.

CPU tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_allocation_v2.py' -v
```

Neural tests use only the locally initialized tiny fixture if Torch/Safetensors
are installed; otherwise they explicitly skip. They never download pretrained
weights. Real planning remains blocked even if every fixture passes.

For the complete invented-data CPU pipeline, including real tiny-model branch and
continuation optimization and export/reimport (slower than focused tests):

```bash
PACT_ALLOCATION_FULL_CPU=1 PYTHONPATH=src python -m unittest discover -s tests -p 'test_allocation_v2_roundtrip.py' -v
```

This uses no official data or pretrained downloads. It deliberately exercises flat
fixture credits and exact aliases; its generated answers are mocks even though its
tiny adapter optimizer updates are real.
