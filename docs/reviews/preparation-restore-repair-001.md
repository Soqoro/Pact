# Preparation probe storage repair — 2026-09-21

The user reports successful 90-update training, 360 forward/backward examples and
verified final persistence, followed by a full training restore timing out after
600 seconds. The probe startup also re-verifies the entire training history.
The logs do not establish that any probe call ran; the original 104-call journal
and latest-safe-snapshot checks must decide recovery.

The old path restores all optimizer checkpoints for a stage that only needs the
final inference adapters. Increasing the deadline alone did not resolve recovery.
The repair adds a bounded inference-only restore: **12 selected payload files**
plus the original snapshot index, completion marker and an explicit inference-only
marker. It copies final adapter tensors/configs, the final reference manifest,
run/design/status metadata and final checkpoint metadata/checksums. Historical
optimizer tensors are neither downloaded nor re-hashed.

Every selected object is hashed against the completed snapshot index. Final-step
metadata, reference identity, exact training log/order, architecture and all three
adapter hashes are checked before the staging directory is published. Corruption
or incomplete training leaves no published destination. Per-file and aggregate
size limits apply. This verifies the selected inference export, not every omitted
optimizer tensor. Original full training snapshots remain untouched. The compact
export cannot resume training.

Probe startup persists only the compact export under a separate `inference`
directory. Calls, generation settings, tasks, old receiver states and 104-call
budget are unchanged. Full-root behavior remains available for original training
workflows; the recovery guide explicitly uses the compact root.

Changing source code requires an explicit compatibility rule: accept the exact
reviewed clean `ff349969996b2066979529b2f43d773f5a1b88e6` source with executable hash
`6e0b6512f014c6f5cbda44de04b198a65c0e67b7a5f5254f69620c4812c4815a`
for reading completed training. Optimizer resume remains source-strict. For old
probe journals, allow only that source transition with identical config/plan and
verified recipe identity. Record the migration and retain committed call shards,
intents, seeds, model identity and budget. Unknown sources, changed plans, stale
snapshots and unresolved attempts remain rejected.

Four new CPU tests cover selected-file restore without any optimizer object,
final-step validation and training prohibition, adapter/marker corruption,
incomplete training/unreviewed source rejection, and exact source migration.
The existing 74-call pause/resume test now exercises that migration and verifies
104 total calls, immutable earlier results and zero-call repeated completion.
Full default suite: **139 passed, six optional neural tests skipped (145 total)**.
No model or GPU was run. Evidence: `results_import/preparation-restore-repair-001/`.

The supplied training receipt identifies the final ZIP checksum as
`a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388`.
Training outcome is reported from logs; its ZIP has not yet been imported/audited
locally. Actual compact Drive restore and probe execution remain GPU-unverified.

Next: user review/commit/push, then the [seven recovery cells](../preparation_probe_recovery.md)
with the new full SHA. No rerun of the 90 training updates or expansion of the
probe is requested. Return the existing training ZIP and final probe ZIP.
