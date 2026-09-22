# Controlled-001 evaluation recovery

Use this only for the completed run reviewed in
[the training audit](reviews/qwen3-receiver-supervision-controlled-001-training.md).
Review and push the local patch yourself. Keep the existing live Colab runtime if
available. Do not rerun acquisition, contexts or training. The original recipe and
all tensor files remain immutable; the explicit recovery records the new code
revision and verifies effective initialization before permitting evaluation.

## 1. Pin the reviewed recovery revision

Run cell 1 of [the original runbook](controlled_peer_donors_colab.md) with the
full SHA of your newly reviewed push. No dependency changes are required in a live
runtime. If the runtime reset, also run original cells 2 and 3 to restore the
prepared initialization and fixed data. Do not run original cells 5–7.

## 2. Define paths and the streaming command

```python
from pathlib import Path
import subprocess, sys
SCRATCH = Path('/content/pact-scratch')
CHECKOUT = SCRATCH / 'checkout'
DRIVE = Path('/content/drive/MyDrive/PACT')
RUN_ID = 'qwen3-receiver-supervision-controlled-001'
RUN = SCRATCH / 'receiver-supervision' / RUN_ID
PERSISTENT = DRIVE / 'receiver-supervision' / RUN_ID
INITIAL = SCRATCH / 'actor-preparation/qwen3-preparation-120-001-inference'
COMMON = [
    '--config', str(CHECKOUT/'experiments/controlled_peer_donors_v1.json'),
    '--data-dir', str(SCRATCH/'training-data/proposal-1200'),
    '--initialization-bundle', str(SCRATCH/'sources/preparation-training.zip'),
    '--initialization-root', str(INITIAL),
    '--selection', str(CHECKOUT/'experiments/receiver_supervision_selection.json'),
    '--run-dir', str(RUN), '--persistent', str(PERSISTENT),
    '--cache-dir', str(SCRATCH/'cache'),
    '--parent-bundle', str(SCRATCH/'sources/receiver-parent.zip'),
    '--acquisition-id', 'qwen3-controlled-peer-donors-001',
]
def study(stage, *options):
    subprocess.run([sys.executable, '-u', '-m', 'pact.training.controlled_donors',
                    stage, *COMMON, *options], cwd=CHECKOUT, check=True)

# On a reset only: restore the latest verified full snapshot. Never restore an
# older snapshot after evaluation has started; it could repeat lost model calls.
if not RUN.exists():
    snapshots = sorted((PERSISTENT/'snapshots').glob('*'))
    assert snapshots, 'The full training snapshot is required; review ZIPs omit weights.'
    study('restore', '--snapshot', str(snapshots[-1]))
```

The reviewed pre-evaluation snapshot is
`.../receiver-supervision/qwen3-receiver-supervision-controlled-001/snapshots/1790098915707189174-0471c4784cbd`.
Required local checkpoints are `RUN/training/{task_sft,receiver_sft}/checkpoints/step-{000000,000024}`
and each arm's `references/`, plus `INITIAL/references/` for all three agents.
Restore keeps the existing 600-second bound; a timeout or unsafe snapshot is a
stop for recovery review, not permission to delete scratch or retrain.

## 3. Verify the reviewed ZIP and run CPU-only recovery preflight

```python
from pact.storage import storage_operation
from pact.util import file_hash, read_json
SHA = 'ce9f97aca8a24e7a15b890d5e557c3da7af8331f944847b8d4036feb152ae993'
NAME = 'qwen3-receiver-supervision-controlled-001-handoff-1790098915763332271.zip'
REVIEW = SCRATCH/'sources/controlled-completed-training-review.zip'
REVIEW.parent.mkdir(parents=True, exist_ok=True)
if not REVIEW.exists():
    print(storage_operation('bundle-restore', PERSISTENT/'bundles'/NAME,
                            REVIEW, sha256=SHA, timeout_seconds=600))
assert file_hash(REVIEW) == SHA
RECOVERY = ['--effective-init-recovery', str(REVIEW)]
study('export', *RECOVERY)  # verifies tensors on CPU and persists recovery receipt
print(read_json(RUN/'evaluation_recovery.json'))
```

Stop if any check fails. Do not modify weights, manifests, hashes or thresholds.
This checks both step-zero states, final states, exports and all protected metadata
against the reviewed inventory. It records exact FP32 focal initialization and the
shared BF16-rounded nonfocal initialization; it does not restore original FP32
nonfocal values. Subsequent commands must use this same pinned recovery revision.

## 4. Run the remaining evaluation, then export

```python
for arm in ('frozen', 'task_sft', 'receiver_sft'):
    print('Evaluating:', arm, flush=True)
    study('evaluate', '--arm', arm, '--execute', *RECOVERY)
study('report', *RECOVERY)
study('export', *RECOVERY)
```

The remaining fixed design has 201 generation calls per arm, 603 total, plus
171 CE forwards. No new donor draws or optimizer updates. Existing journal guards
apply if a command is interrupted. Each actual loaded model must match certified
actor tensors before any evaluation call. Return the final printed handoff ZIP and
SHA256. It contains evaluation records, the report and recovery receipt; durable
full snapshots retain weights/checkpoints. GPU recovery remains unverified until
that returned bundle is audited.
