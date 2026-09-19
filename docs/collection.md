# Frozen-reference scoring and bounded training collection

`collect-bank` and `cache-reference` are implemented and CPU tested. Their default
invocations only produce plans. The [complete returned GPU bank](reviews/qwen3-bank-001-complete.md)
now verifies the six-record recipe, compatible resume, five private pairs and
20 suffix branches. It produces zero receiver preference pairs; GPU frozen-reference
scoring remains unverified and the full revision objective is not ready. This
stage collects engineering evidence; it does not update adapters, run full PACT
training, or access final-test data. No further invocation is requested now.

## Fixed recipe

[`collection_engineering.json`](../experiments/collection_engineering.json) pins the
reviewed 12-task training manifest, completed warm-start reference manifest and
three adapter hashes. It selects the first task in each family in that frozen
manifest: `arc_challenge:MCAS_2004_5_13` and `logiqa:train-7374`. Selection does not
depend on model outcomes. Both tasks were in the warm start; they are suitable for
an engineering check, not held-out effectiveness evidence.

There are six debate records: two tasks × clean/early/exchange. Each uses three
frozen actors, four private candidates per agent, K=2 paired suffix seeds, and up
to four candidates per eligible receiver. The uninterrupted upper bounds are
474 generation calls, 106,368 generated tokens and 72 teacher-forced forwards
(18 gold-answer scores, at most 18 positive-packet scores and 36 reference scores).
These are caps, not runtime estimates or promised pair counts. Per-call progress
is printed; records may take much longer than a single ordinary debate.

The backbone is loaded explicitly at the existing Qwen3-8B revision, BF16/SDPA,
thinking disabled, 4,096-token context, 256-token packets and 64-token final
readout. Exported adapter configs contain a Colab cache path; that path is never
used to choose the backbone. Three actor adapters and three separate frozen
reference copies share one backbone. Readout disables every adapter. The exact
base snapshot and adapter config/tensor hashes must match the completed warm start.
The first returned record reports six-adapter execution at approximately
15.517 GiB peak allocated memory; full-context fit is unverified.

Gold-answer mean completion NLL is teacher-forced under the original private
prompt using canonical answer-only JSON plus EOS. Sampled positive private-packet
NLL and receiver reference scores use actual generated token IDs, including EOS;
sampled text is not decoded and re-tokenized to manufacture scoring targets.
Reference scores are sums of causally shifted completion-token log probabilities,
excluding prompt tokens. Scoring restores adapter selection, module modes and
gradient flags even after a forward exception. The implementation accounts for
the gradient-flag behavior in the [pinned PEFT source](https://github.com/huggingface/peft/blob/v0.18.1/src/peft/peft_model.py).

Every raw trajectory, candidate, paired suffix and nullable credit is retained.
Labels and hold/repair metadata stay outside model inputs. Invalid completions
are failures, not preference negatives. Missing pairs stay missing; absent
hold/repair strata leave `full_revision_ready=false`. This fixed pool does not
implement sparse-support sampling, outer refreshes or joint optimization.

## Local plan

```bash
python -m pact collect-bank \
  --config experiments/collection_engineering.json \
  --data-dir results_import/training-data-001/engineering-12 \
  --references-dir scratch/warmstart/qwen3-warmstart-001/references \
  --run-dir scratch/collection/qwen3-bank-001
```

Planning verifies the frozen training data but does not require adapter files,
load a model, create the run directory or contact a model hub.

## Original first-record Colab setup (completed)

All six records are now reviewed. The setup below and the earlier continuation
cell are retained as execution records, not instructions to repeat this bank.
See the [completed review](reviews/qwen3-bank-001-complete.md) for the next local task.

Publish this increment and pin its full commit SHA before running it in Colab.
`a277794d271720665d57308cc15f3122f1934e27` contains the completed warm start but
does not contain this collector. Reuse only the checkout/install/Drive-mount
setup from notebook 02 with the new SHA; do not execute its training cells or use
Run All. There is no new collection notebook. Run these Python cells in order
after the pinned installation. The existing installer preserves Colab's torch
build and pins the model dependencies.

```python
from pathlib import Path
import subprocess, sys
SCRATCH = Path('/content/pact-scratch')
DATA = SCRATCH / 'training-data/engineering-12'
WARMSTART = SCRATCH / 'warmstart/qwen3-warmstart-001'
REFERENCES = WARMSTART / 'references'
RUN = SCRATCH / 'collection/qwen3-bank-001'
DURABLE = Path('/content/drive/MyDrive/PACT/collection/qwen3-bank-001')
CONFIG = Path('experiments/collection_engineering.json')
TIMEOUT = 120

if not DATA.exists():
    subprocess.run([sys.executable, '-m', 'pact', 'prepare-training-data',
        '--cache-dir', str(SCRATCH / 'cache/data'), '--output-dir', str(DATA),
        '--items', '12', '--seed', '20260918', '--download'], check=True)

from pact.training.colab import restore_snapshot
from pact.training.collection_config import load_collection_config, collection_plan
from pact.training.scoring import verify_references
recipe = load_collection_config(CONFIG)
print(collection_plan(recipe, DATA)[4])
if not WARMSTART.exists():
    print(restore_snapshot(
        '/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/snapshots/1789796424349439412-7eeb6af87200',
        WARMSTART, timeout_seconds=TIMEOUT))
verify_references(REFERENCES, recipe)
print('Completed warm-start references verified; no warm-start updates requested.')
```

Restore verifies the full approximately 1.57 GB warm-start snapshot, including
optimizer files. It requires the whole Drive object store, not the metadata review
ZIP. If a healthy copy needs longer, explicitly raise `TIMEOUT`; an existing
incomplete directory is not silently replaced.

```python
# Start with a plan. Set EXECUTE=True for the reviewed bounded GPU invocation.
EXECUTE = False
RESUME = False
STOP_AFTER = 1  # First return one completed raw record for review.
args = [sys.executable, '-m', 'pact', 'collect-bank',
    '--config', str(CONFIG), '--data-dir', str(DATA),
    '--references-dir', str(REFERENCES), '--run-dir', str(RUN),
    '--cache-dir', str(SCRATCH / 'cache/models'),
    '--persistent', str(DURABLE), '--storage-timeout', str(TIMEOUT)]
if EXECUTE:
    args += ['--execute']
    if RESUME:
        args += ['--resume']
    if STOP_AFTER is not None:
        args += ['--stop-after', str(STOP_AFTER)]
status = subprocess.run(args).returncode
if status:
    raise RuntimeError('Collection failed; retain scratch and inspect the printed diagnostic ZIP.')
```

Download the exact printed `persistent_bundle`, or the local `path` if persistence
failed. It uses `HANDOFF.json` plus `review_checksums.json`; the validation
`import-bundle` command does not accept this review format. A one-record stop
reports `interrupted_at_record_boundary`, exit zero, and raw records without a
complete `bank.json`. Review that handoff before continuing the same commit and
run with `RESUME=True`, `STOP_AFTER=None`.

## Persistence, recovery and reference caching

Completed records are immutable JSON shards with hash markers. Each record
boundary verifies a durable snapshot when `--persistent` is set. Finalization
creates a local review ZIP before the final Drive snapshot and handoff copy.
Each storage operation has its own deadline and progress notices. Completion of
six records does not imply a completed Drive copy. The enclosing handoff receipt
reports verification; the scratch manifest retains its local-only persistence flag.

After a runtime reset, restore the **exact printed collection snapshot** into an
absent scratch run, restore the warm-start references separately if needed, then
use `--execute --resume` with the same code, config, data and runtime identity:

```python
from pact.training.collection import restore_collection
COLLECTION_SNAPSHOT = ''  # Copy the exact verified snapshot path from your receipt.
assert COLLECTION_SNAPSHOT, 'Set the explicit collection snapshot path.'
print(restore_collection(COLLECTION_SNAPSHOT, RUN, timeout_seconds=TIMEOUT))
```

An interruption within a record may require regenerating that incomplete record;
completed records and cached reference scores are reused. Incompatible source,
data, model or runtime identities fail instead of silently continuing. If model
initialization never completed, use a new run directory. Resource attempts record
fresh generation and scoring calls; work lost in an abrupt runtime failure may
have unknown cost. Compute units remain unknown unless separately measured.

The complete bank automatically builds preferences and caches actual frozen
reference scores. The standalone command below plans a separate cache; add
`--execute` to score, and `--resume` only for that same existing cache identity:

```bash
python -m pact cache-reference \
  --config experiments/collection_engineering.json \
  --bank /content/pact-scratch/collection/qwen3-bank-001/bank.json \
  --references-dir /content/pact-scratch/warmstart/qwen3-warmstart-001/references \
  --output-dir /content/pact-scratch/reference-cache/qwen3-bank-001
```

An empty preference set creates no fictitious scores and loads no model.
Standalone cache output is local; the integrated collector includes its cache in
verified snapshots. Review archives contain metadata/raw JSON, not tensor weights
or shard marker files; use snapshots for resume. A 90 MiB metadata limit fails
explicitly rather than silently omitting raw traces. Post-reset Drive restoration,
GPU frozen-reference scoring remains unverified; the completed bank has no usable
receiver preferences. Full bank collection and compatible continuation now pass
the returned audit. [Local test evidence](reviews/collection-implementation-001.md).
