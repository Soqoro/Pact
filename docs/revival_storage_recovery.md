# Revival storage correction and recovery boundary

Routine checkpoints now use `revival_files_v1`, with independently hashed files
rather than one new full recovery ZIP per optimizer boundary. Unchanged tensors
and metadata share the existing object. Latest, step-zero and epoch tensor
selection is unchanged. Explicit recovery exports still contain real tensors.
No training schedule, target, model, precision or budget changes.

## Failure behavior

A synchronous storage worker runs under the caller's run lock and 600-second
storage deadline. It verifies the latest snapshot before appending. Before copying,
it writes and verifies `SNAPSHOT_PENDING.json`; interrupted or capacity-failed
snapshots retain that marker. A new completion marker is written only after object
and index verification. Pending optimizer/generation/scoring intents remain unsafe.
Restore verifies every object and restored file and validates execution state
before exposing the destination. Missing latest objects and incomplete directories
stop restoration. There is no older-safe fallback.

The object directory has a 32 GiB hard admission ceiling. Existing objects, including
unknown ones, count toward it. Capacity failure stops without copying new objects,
keeps scratch and leaves the pending marker. This assumes the existing single-writer
run lock; do not run competing notebook writers against one persistent root.
Plans without a retention policy do not collect garbage. The separately proposed
[replacement retention policy](revival_replacement_plan.md) permits audited deletion
of obsolete tensor objects only when explicitly frozen into a new plan. Changing
tensors still need staging headroom; the cap does not guarantee completion of all fits. Snapshot metadata and explicit
export bundles are outside this limit. Small-file Drive latency and GPU performance
remain unverified.

## Existing interrupted study: do not resume

The incident run remains blocked. Verified step28 is earlier than missing later
state. This patch does not authorize replaying those updates, deleting the newest
incomplete directories, marking the old receipt safe, changing the plan source
identity or selecting an older snapshot. The writer rejects legacy ZIP snapshot
roots rather than silently changing their storage format. Legacy restoration is
still supported only when the actual newest snapshot is complete, fully verified
and safe. That condition is not established for the incident run.

Next review must decide the disposition of unresolved optimizer history. The separately reviewed replacement creates a new source-bound child and does not
migrate this interrupted parent.
There are deliberately no resume commands for the incident run in this patch.
Preserve the three retained archives and cleanup audit described in
[audit](audits/PACT_REVIVAL_STORAGE_INCIDENT_2026-10-19.md).

## Local verification

Run without downloads or GPU:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_revival*.py' -v
PYTHONPATH=src python -m unittest discover -s tests -p 'test_storage.py' -v
PYTHONPATH=src python -m unittest discover -s tests -p 'test_artifacts.py' -v
```

The regression fixtures exercise deduplication, full restore, unsafe optimizer and
call/score intents, capacity stop, interrupted copy/completion, missing newest
objects, symlink rejection, plan isolation, legacy refusal and worker integration.

The [replacement child](revival_replacement_plan.md) now has a CPU-tested
import/training path and exact Colab cells. The original run remains non-resumable;
no child GPU execution has yet been verified.
