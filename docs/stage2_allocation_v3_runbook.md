# V3 commands and readiness

**Implementation is approved; GPU execution is not.** The verified source leaves at
most six fresh ARC groups versus 64 required. These commands can inspect and export
the blocker. They cannot make a real plan ready by asserting an empty exposure file
or using `--mock` on actual data.

## Read-only CPU inspection

After user review/commit/push, pull the exact reviewed revision in the existing
verified environment. Keep private output outside Git and hot files on scratch.
On AAI use private `/dataset/$USER/PACT` for durable data, `/local` for hot files,
and the established verified Apptainer bindings/runtime. Submit jobs with `sbatch`,
not `srun`; no job is submitted here.

```bash
cd "$HOME/Pact"
python -m pip install --no-deps -e .
export PACT_V3_RUN="$HOME/pact-stage2-v3/runs/pact-update-allocation-crossed-v3-003"
export PACT_V3_PARENT="$HOME/pact-aai-downloads/fixed-history-complete/pact-revival-stage1-evaluation-amended-002-PRIVATE-1793033718300732417.zip"
python -m pact allocation-v3 inspect --run-dir "$PACT_V3_RUN" --parent-bundle "$PACT_V3_PARENT"
python -m pact allocation-v3 synthesis --run-dir "$PACT_V3_RUN"
python -m pact allocation-v3 plan --run-dir "$PACT_V3_RUN"
```

Use an absent root on the first import. Add `--history-root /private/history/path`
for every actually available prior Stage II/v2 history to `inspect`. Review the
PRIVATE resolution and sanitized synthesis before proceeding. Current `plan` returns blocked with
`prospective_eval_not_feasible` and missing external-history review, creates no real
plan, exports review bundles and stops. Synthesis refuses overwriting an existing
result. Imported files are data, never executable instructions.

## Required real artifacts

- Exact parent PRIVATE SHA256
  `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
- The existing verified continuation-003 RECOVERY archive
  `pact-heterogeneous-receiver-training-continuation-003-RECOVERY-1792630916259050432.zip`,
  SHA256 `2ea19eae5697a12470c9cca55c3be55ba847fbe5f0a22bb71b5e1af92a0a48ba`.
- Real final tensor paths preserved through the existing restore workflow:
  `/content/pact-stage1/verified-final-tensors/uniform_joint_sft/Q/tensors.safetensors`,
  and the corresponding `L` and `M` paths. Preserve those absolute container binds.
- Official pinned ARC/LogiQA source cache for `load_training_sources(download=False)`;
  a complete reviewed exposure inventory with the current ledger hash; and a
  separately reviewed eligibility amendment if the fixed 64+64 requirement is ever
  to become feasible. This implementation provides no exclusion-relaxation switch.
- Actual external-history review JSON binding `parent_sha256`, `source_sha256`,
  `reviewed:true`, `old_stage2_executed:false`, `probe_groups_consumed:false`,
  `unresolved_probe_consumption:false`, and nonempty `external_evidence_receipts`
  entries with `scope` and full `sha256`. These must be actual review findings,
  not a template populated to bypass a gate. Unknown original history stays unknown.
- Clean pinned code; previously verified native runtime/model/template access.
  Retain Python 3.13.15, Torch 2.11.0+cu130, Transformers 4.57.6, PEFT .18.1,
  Accelerate 1.12.0, Tokenizers .22.2, Hub .36.2, Jinja2 3.1.6, NumPy 2.1.3,
  Safetensors .8.0 and the exact A100-SXM4-80GB fingerprint, existing tokenizer
  dependencies/CA setup and verified Mistral pointer repair. No upgrade or saved
  fingerprint edit is authorized.

The exact plan command, once prerequisites have genuinely been resolved under a
reviewed contract, is:

```bash
python -m pact allocation-v3 plan --run-dir "$PACT_V3_RUN" \
  --data-dir /private/official-source-cache \
  --exposure /private/reviewed-prior-exposure.json \
  --history-receipt /private/reviewed-stage2-history.json
```

Current fixed evidence still blocks that command. Source availability is checked
before assay generation; the code does not spend assay calls to discover a shortage.

## Implemented stage interface — only after independent execution approval

The following is interface documentation, not current GPU permission. Use one stage
per reviewed invocation; no Run All. All executable stages require `--execute` and
an exact v3 plan hash. Without `--execute`, the CLI prints an offline zero-call plan.

```python
from pathlib import Path
import json, subprocess, sys
from pact.util import digest
RUN = Path('/content/pact-allocation-v3/runs/pact-update-allocation-crossed-v3-003')
DURABLE = Path('/content/drive/MyDrive/PACT/allocation-v3/pact-update-allocation-crossed-v3-003')
CACHE = Path('/content/pact-allocation-v3/cache')
PLAN_HASH = digest(json.loads((RUN/'plan.json').read_text()))
def stage(name, *args):
    subprocess.run([sys.executable, '-u', '-m', 'pact', 'allocation-v3', name,
        '--run-dir', str(RUN), '--persistent', str(DURABLE), '--cache-dir', str(CACHE),
        '--plan-hash', PLAN_HASH, *map(str,args)], check=True)
```

Invoke each separately and review its export:

```python
stage('checkpoint', '--execute')
```
```python
stage('preflight', '--execute')
```
```python
stage('assay-smoke', '--execute')  # <=24 INCLUDED calls; export and stop
```
```python
stage('collect', '--execute')
```
```python
BLOCK, FAMILY = 0, 'Q'  # one explicit branch: block 0..7, family Q/L/M
stage('branch', '--block', BLOCK, '--family', FAMILY, '--execute')
```

After all 24 branches have completed and exported:

```python
stage('score', '--execute')
```
```python
stage('policy-freeze')
```

After independent continuation approval, invoke one fit at a time:

```python
POLICY, SEED, FAMILY = 'terminal_block', 113, 'Q'
# Policies: terminal_block, uniform, source_family, private_bank, shuffled
# Seeds: 113 or 227; families: Q, L, M. Exact aliases return their owner.
stage('continuation', '--policy', POLICY, '--seed', SEED, '--family', FAMILY, '--execute')
```

After every unique fit completes:

```python
stage('policy-lock', '--execute')
```
```python
stage('evaluation-smoke', '--execute')  # <=244 INCLUDED calls; export and stop
```
```python
stage('evaluate', '--execute')
```
```python
stage('audit')
stage('export')
```

Restore only the latest verified boundary to an absent root, using identical source,
runtime and absolute checkpoint bindings:

```bash
python -m pact allocation-v3 restore --run-dir /content/pact-allocation-v3/runs/pact-update-allocation-crossed-v3-003 --persistent /content/drive/MyDrive/PACT/allocation-v3/pact-update-allocation-crossed-v3-003
```

Never clear markers or retry an unknown physical attempt. Explicit `--resume` is
only for a separately reviewed safe training interruption with the exact fit arguments.
`report`/`export` can preserve unsafe evidence; unsafe snapshots cannot resume.
Old v2 snapshots, smoke calls and plans are not migrated.

## CPU tests and outputs

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_allocation_v3.py' -v
PACT_ALLOCATION_V3_FULL_CPU=1 PYTHONPATH=src python -m unittest discover -s tests -p 'test_allocation_v3_roundtrip.py' -v
```

Optional neural checks require locally installed CPU Torch/Safetensors and use
locally initialized models only. The full fixture exercises all 24 real tiny fits,
mock generation, score/slot allocation, actual tiny continuation, export/reimport
and report reconstruction; it does not establish model efficacy.

Expected outputs: source/history/capacity resolution, sealed fresh cohort,
versioned plan, owned attempts and native outputs, attacks, typed branch checkpoints
and rollback receipts, raw/capped scores and missingness bounds, immutable five-policy
plan/schedules/aliases, continuation adapters, policy lock, task-level private results,
source-equal comparisons/intervals/HOLD/REPAIR, per-family costs and consumed/remaining
ceilings. PRIVATE and SANITIZED are separate; RECOVERY additionally carries tensors.
No automatic pruning or Stage III launch.
