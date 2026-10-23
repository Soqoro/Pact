# Proposed Stage I accounting amendment

**Not authorized or executable.** No frozen artifact or runtime blocker is changed.
This is the concrete decision requested after the completed checkpoint audit and
unavailable original-run closure. Machine-readable proposal:
`stage1_evaluation_accounting_amendment_proposal.json`.

Canonical proposal hash:
`49de20c60cb493467fb940b5f27e98280bd7ba0021d612db69c6cb86125642a6`.

## What approval would change

The evaluation brief §10 forbids a fresh budget and replay of ambiguous historical
generation. This proposal explicitly changes that rule for one separately named
evaluation child, `pact-revival-stage1-evaluation-amended-002`, because the original
terminal ledger is unavailable. It does NOT reconstruct or close that history,
assert that unknown calls were zero, or claim unused allowance under the old cap.
New physical evaluation calls may repeat requests made in unrecoverable original
history. Approval must knowingly accept that possibility and additional compute.
These would be fresh child attempts with distinct physical provenance, not resumed
or recovered historical results. Within the new child, ambiguous dispatch remains
reserved and blocks automatic retry. Export duplicates never count as fresh work.

The original evaluation-001 remains the immutable verified prerequisite. Reuse
its verified six adapters, four backbones, 16-forward verification evidence and
exact source/task identities; no repeated verification forwards are proposed.
Any further load must retain normal identity/isolation checks. No model, precision,
prompt, seed, token cap, training, attack semantics or source changes are allowed.

## Exact scope and ceilings

| Component | Maximum additional generations | Reserved output tokens |
|---|---:|---:|
| Validation (128 original groups) | 4,224 | 2,162,688 |
| Source evaluation (256 original groups) | 8,448 | 4,325,376 |
| Fixed-history diagnostic (original 64 validation groups) | 1,920 | 983,040 |
| New attack acquisition | 0 | 0 |
| Total | **14,592** | **7,471,104** |

The two-task smoke is included: at most 66 live calls / 33,792 tokens, followed by
export and stop. Validation, source evaluation and fixed-history each remain
separately invoked stages. All 384 previously attempted evaluation attacks retain
their exact accepted/rejected decisions; no replacement draws or fresh donors.
Known exact reuses are deduplicated; no unused component allowance is transferred.
New optimizer updates, training forwards, synthetic checks and teacher-forced
scoring forwards are all zero. Negative scores do not permit outcome-based stopping,
selection, reallocation or method changes. No final-test or Stage II execution.

Keep validation at ARC64/LogiQA64 and source evaluation at ARC120/LogiQA136. This
records precedence of the already approved/executed allocation over the later
128/128 prose. No task IDs change. Preserve per-source and equal-source reporting.

## Historical ledger remains separate and uncertain

Original confirmed calls: 2,438, including the 384 evaluation attack acquisitions.
Later original attempts remain unknown. Replacement/continuation new generations:
zero. Verification-001: zero generations plus its consumed 16 synthetic forwards.
No correction erases unknown original optimizer history or replacement step94.

The additional ceiling is not evidence that total lineage use is 17,030. If the
original obeyed its 17,030 cap, the combined original-plus-proposed ceiling would
be 31,622 generations and 16,190,464 reserved output tokens. This is a conditional
planning bound, not reconstructed actual usage or proof of original compliance.
Any later-discovered historical work must be recorded separately, not silently
netted against child results or erased. No outcome-dependent replacement of child
observations with newly found historical results is allowed.

## Implementation only after approval

Bind the exact proposal hash and explicit user decision into a separate child plan,
with unchanged prerequisite hashes and independent physical-attempt accounting.
Preserve original resolution/blockers rather than rewriting evaluation-001. Add
focused CPU tests for caps, exact attack reuse, no synthetic repeats, source identity,
new-child provenance and interrupted-call refusal. Review/push/pin precedes any
Colab invocation. Approval of this accounting proposal is not automatic execution
of all stages; the first future GPU stage remains the included smoke only.

## Subsequent explicit decision

The user answered “proceed” to the concrete approval question for this proposal.
Approval is now recorded in `stage1_evaluation_accounting_approval.json`, separately
from the unchanged proposal JSON/hash. Implementation and scope are described in
`stage1_amended_evaluation_methodology.md`. Historical text above describes the
proposal at creation; no original-run ledger or evaluation-001 artifact is rewritten.
