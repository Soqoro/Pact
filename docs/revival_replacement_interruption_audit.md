# Replacement training interruption audit — 2026-10-21

Run: `pact-heterogeneous-receiver-training-replacement-002`.
Plan: `0cd17021ec0b11865e2ddb5b761e086b88650d356c870494d86ec78c1d689f55`.
Private forensic archive SHA256:
`bb9d759af00b2ee7942ad25236bced0b6ebf95cbdaccf2f582a22586148d9015`.
Archive size: 576,446,353 bytes. Raw evidence remains in ignored results_import;
this report includes no benchmark text, prompts, targets or tensor contents.

## Verified evidence

Local streaming checks verified the archive SHA and all 48 manifested members,
with no duplicate or extra ZIP members. The three included snapshot indexes match
their COMPLETE markers and recovery receipt member maps. Four checkpoint inventories,
state step numbers, training contracts and saved statuses agree; tensor hashes pass.
This verifies serialized files, not live GPU restoration or optimizer replay.

| Arm | Q | L | M |
| --- | --- | --- | --- |
| Independent adversarial SFT | 128 | 128 | 128 |
| Uniform joint SFT | 93 | no saved status | no saved status |

477 of 768 planned updates are durably recorded. The latest snapshot
`1792486927348121446-eefe02888431` is unsafe: joint Q status is 93 while
update_attempt is 94. No step-94 checkpoint is indexed in the inspected snapshots.
The preceding snapshot records step 93 safe; it cannot override subsequent history.
SNAPSHOT_PENDING is present; INFLIGHT is absent. The latter concerns generation
and does not certify optimizer safety. No completed study result or efficacy follows.

## Pinned execution order

The plan records clean commit `ab9ae8a54be868cd29dea9b96d8e4cdd6b73b8d8`.
The six inspected training/persistence implementation files match that commit.
`neural.train` writes update intent, synchronously calls persistence, then computes
loss/backward/optimizer.step, writes a checkpoint/status, and calls persistence again.
`storage_operation` waits for the worker's result, raising on failure or timeout.
Thus a failed PRE-update callback prevents that update from executing in that invocation.

However, SNAPSHOT_PENDING contains only format and plan hash, not a transaction ID,
optimizer step, or pre/post phase. A completed pre-update transaction followed by an
interrupted post-update transaction can leave the same latest unsafe snapshot and
pending marker before a newer index is published. Lost scratch logs are not in this
bundle. The supplied evidence does not distinguish these cases. Step 94 remains
unresolved; absence of its indexed checkpoint is not proof of nonexecution.

The three exported retention audits refer to histories ending at snapshots
1792485582496035025-508ae00ce87f, 1792486022477445523-3863a86afc54, and
1792486474019898723-60b0c618ee19 respectively. They do not establish completion of
the transaction associated with the latest snapshot. Only three audits were exported;
modification-time selection is not an exhaustive retention audit.

## Performance finding and limits

Each persistence invocation verifies the latest snapshot objects. Retention then
traverses historical snapshots/audits and hashes protected objects. Before/after
callbacks therefore repeat work as history grows. The three inspected snapshot IDs
are about 233 and 221 seconds apart (ID timestamps, not measured stage durations).
This is consistent with substantial persistence overhead, but does not establish
whether timeout, runtime reset, or another storage failure caused this interruption.
There is no proof here of a renewed storage-capacity exhaustion.

## Disposition

Keep this run and its pending intent immutable. No marker deletion, intent rewrite,
older-snapshot resume, replacement run, or extra optimizer budget is authorized.
Do not ask the user to repeat tensor hashes: they have now been independently verified.
A future operational design should bind durable transactions to pre/post-update phase
and step, and avoid repeated history-wide verification on each optimizer update.
Such future changes cannot retroactively resolve this incident. Any explicit recovery
or amended continuation must preserve unknown-work accounting and be reviewed as a
separate decision. No implementation, GPU execution, model download or resume occurred
in this forensic review.
