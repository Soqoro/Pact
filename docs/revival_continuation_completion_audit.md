# Continuation-003 completed training audit

Reviewed locally on 2026-10-22 from the uploaded PRIVATE and SANITIZED bundles.
Run: `pact-heterogeneous-receiver-training-continuation-003`.

## Finding

All six fits record 128/128 committed updates. The amended path contains 477
inherited plus 291 new updates, totaling 768. New committed training forwards are
6,319, within the 6,984 ceiling. Each complete fit records 2,776 forwards; the six-fit
path totals 16,656. No new generation or evaluation is recorded by this child.
The summary records recovery_safe=true and no unresolved new optimizer attempts.
This is completed adapter training, not evidence of improved held-out performance
or executed full PACT. Evaluation and Stage II remain deferred.

The original replacement-002 step 94 remains unknown. It is not counted as zero
or retroactively made safe. The amended physical bound remains at most 769 updates
for replacement plus continuation; the earlier original-run history is separate.

## Provenance and verification

Frozen plan: `bbd6decefbd9ba4808de22b31c87f02f4d19094ee1b4035383db0285000d5897`.
Recorded clean source: `3e3fddf8d2fde03dd1bd903bfa7e3b4313c63fd5`.
Amendment: `2546efe226d2f6d80d0b13bb04930a482487ea7477a892ec821f763de618f0db`.

- PRIVATE SHA256: `2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959`; 918 manifest-listed payload members verified.
- SANITIZED SHA256: `9a34de7cb4d5602b1fa4beeaa735ca14d9418f47fc08cdc14b4b11e2dbf72d1a`; 1 manifest-listed payload members verified.

PRIVATE has 920 total members; SANITIZED has three. Envelope HANDOFF/checksums
files are not themselves member-hashed; whole-archive hashes above bind them.
These hashes were computed locally; no independent user-supplied archive hash was
available for this pair. Both summaries agree exactly. ZIP paths, duplicate names,
symlink attributes, exact manifest coverage and every listed payload hash passed.
No archive was extracted or its code executed.

Plan/review hashes, lineage-file hashes, embedded parent PRIVATE archive hash,
and available independent checkpoint metadata/status hashes match their bindings.
All six step-128 state records match their contracts and status logs. Logs contain
exactly steps 1–128, with finite loss, gradient norm and learning rate. Forward
counts recompute correctly. The first 93 joint-Q log entries equal the inherited
record exactly. Saved active intents do not exceed committed steps.

The returned preflight records Q/L/M native and initialization identity verification
and runtime fingerprint `e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0`.
This is imported real-GPU execution evidence, not a new local GPU test. The separate
user Drive diagnostic reports no pending/inflight markers and a safe latest snapshot;
those remote files were not independently inspected locally.

## Descriptive training losses

Values below are unweighted means of the 64 logged update losses in each epoch.
They are training diagnostics, not held-out accuracy, comparable calibrated model
scores, or an efficacy ranking between objectives or model families.

| Arm | Family | Epoch 1 mean | Epoch 2 mean | Final update loss |
|---|---|---:|---:|---:|
| independent_adversarial_sft | L | 1.3348 | 0.8290 | 0.9807 |
| independent_adversarial_sft | M | 1.5235 | 1.0220 | 0.9072 |
| independent_adversarial_sft | Q | 1.9047 | 0.7446 | 0.5815 |
| uniform_joint_sft | L | 1.2199 | 0.8586 | 0.9006 |
| uniform_joint_sft | M | 1.3991 | 1.0023 | 0.8878 |
| uniform_joint_sft | Q | 1.6946 | 0.7686 | 0.6024 |

All six epoch-2 means are lower than epoch-1 means. No generalization or
communication benefit follows from this observation alone.

## Limits and next review

Neither review bundle contains `.safetensors` files. Final adapter/optimizer tensor
bytes, finiteness, and live reload remain unverified in this local audit. Preserve
RECOVERY and Drive snapshots; do not delete them based on this metadata review.
A checkpoint verification and a separately reviewed evaluation path are needed
before performance conclusions. This audit authorizes no new run or methodological
change. Historical unknown work and the parent interruption audit remain intact.

Validation executed: read-only Python archive/checksum/provenance/log/accounting
assertions, all passed. No training, model downloads, GPU work, final-test access,
commit, push, or existing artifact mutation occurred. No regression suite was run
because this handoff changes documentation only.
