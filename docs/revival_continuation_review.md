# Replacement continuation proposal — 2026-10-22

Status: local implementation requested by the user on 2026-10-22 after review of
the 291-update proposal. No GPU execution performed. The separately pinned Colab
child requires the exact amendment review hash below; the old run remains unsafe.

Parent: `pact-heterogeneous-receiver-training-replacement-002`, plan
`0cd17021ec0b11865e2ddb5b761e086b88650d356c870494d86ec78c1d689f55`.
Evidence archive SHA256:
`bb9d759af00b2ee7942ad25236bced0b6ebf95cbdaccf2f582a22586148d9015`.
See [the forensic audit](revival_replacement_interruption_audit.md).

## Concrete decision for review

A possible amended continuation would use a NEW run ID and separate storage root,
reference independent Q/L/M final checkpoints unchanged, and initialize joint Q
from its verified step-93 checkpoint including optimizer, RNG and sampler state.
It would execute 35 remaining Q updates and 128 each for L/M: 291 new committed
updates. L/M must use the original verified seeded initializations and fixed bank,
with unchanged objective, schedule, model/runtime identities and masking. No
collection, evaluation or Stage II is included. Do not pool a repeated step with
unknown historical work or represent this as an uninterrupted original run.

Step 94 may already have executed in lost scratch. Therefore the proposal requires
an explicit exception to the original no-retry/budget contract: the resulting path
would contain 768 committed updates but physical historical execution may include
one additional update and an unknown number of forwards in the interrupted step.
The previous original-run interruption remains separately accounted as well.
The new dedicated child implements this exception only with the exact artifact-bound
amendment hash. It preserves the old intent under lineage and never rewrites the old
run. Without executing the child, the historical study remains partial at 477 updates.

The prerequisite archive check now verifies that the original PRIVATE bundle supplies
the exact missing bank, access and initialization assets. Tiny CPU continuation
checks cover optimizer/RNG restoration. Preparation freezes a distinct child plan
and clean source commit. Its amendment separately bounds 291 new committed updates,
6,984 new forwards, and at most one unknown historical step (up to 24 forwards).
No parent directory, marker, snapshot, or checkpoint may be modified.

## Operational changes implemented locally

Future training callbacks now pass explicit pre_update/post_update, arm, family
and step. Persistence checks those against saved intent/contract/status and records
hashes, a fresh transaction ID, and plan identity in SNAPSHOT_PENDING. After snapshot
and retention verification it writes and verifies a transaction completion record
binding that ID to the snapshot index, then removes the pending marker. Non-training
checkpoints are labeled checkpoint, not inferred as optimizer phases. The synchronous
pre-update boundary remains before any forward/backward/optimizer execution.

These records improve future diagnosis only. They do not prove an old phase, make
an unsafe snapshot safe, or authorize automatic retry. Latest-only restore still
rejects pending markers and unsafe receipts. Old pinned run/source identities remain
unchanged; do not pull this code into the existing run and resume it.

Retention now caches object presence/hash verification only within one locked
invocation. Shared historical references no longer repeat Drive stat calls for each
snapshot, and receipt objects are not hashed twice in the same pass. Fresh calls
and restores still perform validation; there is no persistent trust cache. History
indexes/audits are still scanned. This is a bounded optimization, not a constant-time
storage redesign or a measured Colab speedup. Large-model/Drive timing remains
unverified. A more invasive incremental index requires its own versioned design.

## Executable child

Module: `pact.revival.continuation`. Run ID:
`pact-heterogeneous-receiver-training-continuation-003`. Amendment review hash:
`2546efe226d2f6d80d0b13bb04930a482487ea7477a892ec821f763de618f0db`.

Preparation requires BOTH the exact original pre-main-training PRIVATE bundle and
the forensic archive above. Independent checkpoints are imported immutable. Joint Q
uses the exact inherited neural contract, optimizer/RNG/sampler state and fixed bank;
the outer child plan binds new code and amended accounting separately. New Q/L/M
training is the only execution branch. There is no generate/evaluate/Stage-II entry
point. Preflight uses real pristine model identity and initialization checks, plus
restored Q adapter identity. Source/runtime changes, pending child transactions and
unresolved new intents stop execution. No automated restart is implemented.

See [the Colab sequence](revival_continuation_colab.md) and notebook 26.
