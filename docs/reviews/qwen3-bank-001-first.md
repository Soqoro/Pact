# First training-bank record review — 2026-09-19

The returned record passes the bounded engineering audit. Resume the same run at
the same commit to collect the remaining five records. No sampling expansion or
optimizer update is warranted by this result.

## Integrity and execution

- Archive: `qwen3-bank-001-handoff-1789803598490756574.zip`, 25,657 bytes.
  SHA256 `ceba32531b82864d694020ac29dce8e612b887c031da198cc644e5982697a7c3`
  matches the supplied checksum. Ten safe members and all nine payload checksums
  pass. Inventory hashes/sizes match; the excluded shard marker's recorded hash
  reproduces from the included shard bytes and expected newline.
- Source: clean `12861a1ca4dce794a1f4daaa27e02618fed2956e`, source hash
  `17a43e51f98f28f5e01ec96f85ee4054bcdefb5a035f265bdf1fbe3217dc1e52`.
  Config, frozen training manifest, task/label identity, whole-team snapshot,
  reference manifest and all three adapter hashes match the reviewed recipe.
- Status: `interrupted_at_record_boundary`, one of six records, exit zero.
  This is the requested intentional stop. No complete bank or reference cache
  should exist yet; both are absent.
- Pinned Qwen3-8B BF16/SDPA, thinking disabled; the runtime fingerprint matches
  the previously reported L4 environment. This archive contains no fresh GPU-name
  report. Its successful code path verifies adapter-file hashes before/after
  loading and guards frozen parameters. Real tensor bytes are not in this ZIP.
- Receipt reports verified snapshot:
  `/content/drive/MyDrive/PACT/collection/qwen3-bank-001/snapshots/1789803598420081006-9645623d1b3e`.
  The nested local manifest's `persistent_copy_verified=false` predates this
  verification. The receipt's ZIP path/hash refer to the earlier local review
  ZIP, and `persistent_bundle=null` predates the subsequent copy. These are
  staged receipt fields, not checksum failures. Current Drive contents, successful
  final ZIP copying and post-reset restoration are not independently verified.

## What the record establishes

The first task is clean `arc_challenge:MCAS_2004_5_13`, whose trusted source label
is B (removing sufficient heat freezes water). All three initial packets, three
revisions, 12 private alternatives and the base readout answer C. All 19 outputs
parse correctly and terminate at EOS, but all are wrong. This is a recorded task
failure; it is not evidence of warm-start benefit or a measured regression against
a matched pre-training control.

All three private candidate pools lack a correct completion. Their credits remain
null, with no selected pair and no suffix branches. All three receiver contexts
are ineligible because no initial peer supplies the correct answer. No receiver
candidates or hold/repair preferences were generated. Derived accounting preserves
zero pairs and `full_revision_ready=false`; sampling caps are unchanged.

Three actor answer-scoring forwards executed. Each targets canonical answer B plus
EOS under the original private prompt, with six supervised tokens. Mean NLLs are
5.406839, 5.502017 and 5.549066. Recorded score sums, token counts, target IDs and
mean reductions agree. The audit reconstructs all defender messages, rendered
chat templates, seed assignments, frozen private delivery and revised-only base
readout; evaluator labels/strata were not added to prompts. All actual token
arrays match their recorded call lengths and exact context associations.

No frozen-reference scoring forward or paired suffix branch executed. Promote
only real adapter loading, frozen-team generation and answer-scoring execution;
leave GPU reference scoring, positive-packet scoring, collection resume and the
remaining conditions unverified. The CPU review checks score arithmetic and
provenance, not independent model-logit or tokenizer recomputation.

## Recorded resources and retained evidence

19 generation calls use 3,826 input and 892 output tokens; three teacher-forced
forwards use 522 combined input tokens, including 18 completion tokens. Summed
generation time is 64.664 seconds. Invocation time is 180.863 seconds, including
56.551 seconds for the bare model load and record-boundary persistence; final ZIP
creation/snapshot copying occur after that timer. Peak allocated/reserved memory
is approximately 15.517/15.619 GiB. No full-context fit or total-session cost claim
follows. Compute units are unknown; no pending call or failure is recorded.

Original extracted data is preserved in
`results_import/qwen3-bank-001-first-review/`. The reproducible CPU audit, JSON
report and explicitly derived preference accounting are in
`results_import/qwen3-bank-001-first-analysis/`. Run the audit from the repository:

```bash
PYTHONPATH=src python results_import/qwen3-bank-001-first-analysis/audit.py
```

No executable source change was needed, so the suite was not rerun for this
artifact review. The preceding implementation's 90-test evidence remains separate.

## Continue the remaining five records

Keep the Colab checkout at `12861a1ca4dce794a1f4daaa27e02618fed2956e`.
In an intact runtime, run the cell below instead of the original first-run cell.
After a runtime reset, first repeat setup/install/data/reference cells 1–4 from
the previous instructions at the same SHA; this cell then restores the reviewed
collection snapshot if the scratch run is absent. It does not overwrite an
existing run. Source/data/model/runtime compatibility is checked by the CLI.

```python
from pathlib import Path
import json, subprocess, sys
from pact.training.collection import restore_collection

scratch = Path('/content/pact-scratch')
checkout = scratch / 'checkout'
run = scratch / 'collection/qwen3-bank-001'
assert subprocess.check_output(
    ['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True
).strip() == '12861a1ca4dce794a1f4daaa27e02618fed2956e'

if not run.exists():
    print(restore_collection(
        '/content/drive/MyDrive/PACT/collection/qwen3-bank-001/snapshots/1789803598420081006-9645623d1b3e',
        run, timeout_seconds=120))

args = [sys.executable, '-u', '-m', 'pact', 'collect-bank',
    '--config', str(checkout / 'experiments/collection_engineering.json'),
    '--data-dir', str(scratch / 'training-data/engineering-12'),
    '--references-dir', str(scratch / 'warmstart/qwen3-warmstart-001/references'),
    '--run-dir', str(run), '--cache-dir', str(scratch / 'cache/models'),
    '--persistent', '/content/drive/MyDrive/PACT/collection/qwen3-bank-001',
    '--storage-timeout', '120', '--execute', '--resume']

COLLECTION_RESULT = None
with subprocess.Popen(args, cwd=checkout, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end='', flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and 'exit_code' in value and 'path' in value:
            COLLECTION_RESULT = value
    exit_code = process.wait()

if COLLECTION_RESULT:
    print('Local ZIP:', COLLECTION_RESULT['path'])
    print('Drive ZIP:', COLLECTION_RESULT.get('persistent_bundle'))
    print('SHA256:', COLLECTION_RESULT['sha256'])
    print('Verified snapshot:', COLLECTION_RESULT.get('persistent_snapshot'))
if exit_code:
    raise RuntimeError('Preserve scratch and inspect the diagnostic ZIP.')
assert COLLECTION_RESULT is not None, 'No handoff receipt found.'
```

Then download the new ZIP and return it with the printed checksum:

```python
from google.colab import files
files.download(COLLECTION_RESULT['path'])
```

Expected successful final status: `collection_complete_local`,
`completed_records=6`, `exit_code=0`, enclosing
`persistent_copy_verified=true`. Missing preferences can still be a valid outcome;
they do not justify another run or a changed sampling policy automatically.
