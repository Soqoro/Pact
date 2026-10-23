# Approved Stage I additional evaluation child

The user explicitly approved proposal
`49de20c60cb493467fb940b5f27e98280bd7ba0021d612db69c6cb86125642a6` with
“proceed” after the concrete amendment question. This implements that decision;
it does not reconstruct missing history. Approval is recorded separately in
`stage1_evaluation_accounting_approval.json`; the original proposed JSON and
original evaluation-001 artifacts remain unchanged.

## Scope and identity

Reserved child: `pact-revival-stage1-evaluation-amended-002`. The only real parent
is verification PRIVATE SHA256
`6836c626fbfb502c7da4f59db2f70280669db84611ef155280fcc73f8626efda`.
The initializer verifies all archived checksums and the exact approved source,
peer-use, receipt and identity-manifest hashes before creating a separate child.
It requires a clean pinned checkout and absent destination. Existing parent or
child directories are never overwritten. The old storage-only transition is not
extended to this new scientific accounting implementation; old runs retain their
old pinned code. The new child records its own source identity.

Parent resolution/budget/maintenance records and synthetic attempts move into the
child's `parent_verification/` provenance copy. The original parent is read-only.
The child preserves the exact tensor paths, all six historical adapter identities,
Q/L/M/R model identities, protocol, prompts, seeds, precision, token caps, source
IDs, exclusions, attack decisions and fixed-history cohort. Its imported-file
inventory is immutable. No adapter tensor bytes are in the review archive; map the
original training RECOVERY archive to the same external scratch paths after reset.

The child resolves the two inherited blockers by explicit decision, not a claim
that either original record changed: retain ARC120/LogiQA136 source evaluation
(and ARC64/LogiQA64 validation), and use an additional approved envelope while
retaining unresolved original generation history. All original blockers remain
in provenance; historical_execution_closed stays false.

## Accounting and execution

Additional ceilings: validation 4,224; source evaluation 8,448; fixed-history
1,920; attacks zero. Total 14,592 generations / 7,471,104 reserved output tokens.
The original 17,030 cap and 2,438 confirmed original attempts remain in a separate
historical ledger, with later original attempts unknown. No arithmetic labels the
new envelope an unused remainder. New physical work can repeat unrecoverable
original requests: that possibility is explicitly approved and reported.

Each child intent binds its owner run, frozen plan and canonical request into a
physical-attempt identity. Canonical equality still enables exact reuse *within*
the child; it does not erase original physical work. Existing ancestor attack
records are reused only on exact canonical equality. Missing/unresolved attacks
stop; the zero attack ceiling prohibits replacement acquisition. No component
transfers or retries of ambiguous child dispatch. Conditional combined historical
ceilings remain conditional, not measured actual usage.

The initial smoke is the same outcome-independent one validation group per source,
at most 66 live calls / 33,792 reserved tokens, included in validation. There are
no new attack draws and no new synthetic checks. Runtime limits are enforced
before dispatch, including smoke, per-component and whole-child caps. Each stage
exports and stops; later stages require the prior stage export. Negative valid
results do not authorize method/task/seed changes. No training, teacher-forced
scoring, new synthetic forwards, final tests or Stage II/III.

## Verification and reporting

The 16 completed synthetic checks are inherited evidence, not repeated child
forwards. Calling verify on the amended child is rejected. Every real model load
still checks exact runtime, native model identity and effective adapter values;
no extra benchmark probes are introduced. Reporting separately labels inherited
verification forwards (16), new synthetic attempts (0), known ancestor attempts,
unknown later history and new child physical work. Per-source and equal-source
metrics and task-group paired analysis remain unchanged. Frozen readout behavior,
all-three private packet freeze and initial-peer-only synchronous exchange remain.

Compact snapshots, pending markers, safe latest-only restore and private/sanitized
exports are reused. Exports and durable markers carry the child run ID. Parent
persistence paths are rejected. No old snapshot or checkpoint is deleted.

CPU fixtures exercise the entire stage sequence with tiny locally initialized
models and inherited mock attacks. Actual returned parent import is checked on
CPU without model downloads. New child GPU evaluation is unexecuted and unverified
until user-returned evidence; the earlier GPU checkpoint verification remains valid
within its audited scope.
