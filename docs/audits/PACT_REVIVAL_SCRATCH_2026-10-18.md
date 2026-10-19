# Revival fixed bank and scratch-training audit — 18 October 2026

Run `pact-heterogeneous-receiver-training-001`, v2 allocation; clean pinned source
`3605dcf70cef4c12092b72231456fad8355b0492`. Plan hash:
`a8ee5cf50d0878dbe6fec8c36364e8b1469cc79c39afd66244b9ecf5f1e5bc71`.

## Evidence verification

Archive suffix `1792171769996477145`:

- PRIVATE SHA256 `f9a78141d0c662c06be903b49318f0235f6253d11e42f5bb17b2dd8adf9f2793`
- SANITIZED SHA256 `9088813ff3e2399fb717ab10d201f12bc98366d4487aee8a36fd118df3bf4432`

Both hashes, all archive member checksums and the complete journal verified.
Archive paths, duplicate names and symlink entries were checked before extraction
outside the repository. PRIVATE and SANITIZED summaries agree. The existing report
was independently recomputed from the imported records and matched exactly. The
shared training bank was rebuilt and passed immutable-content equality. Source
quotas, exclusion inventory and 3/5 probe blocks validate. The plan and six original
smoke calls are unchanged from the earlier verified bundle. No raw benchmark text,
model responses or decodable IDs are included in this report.

## Collection

2,438 attempts / 2,438 committed / zero unresolved:
1,536 fitting private calls, 896 attack attempts and six post-update scratch calls.
Accounting: 629,431 input tokens, 123,827 output tokens, 1,248,256 reserved tokens.

| Actor | Fitting calls | Valid | Correct | Invalid | Abstentions |
|---|---:|---:|---:|---:|---:|
| Q | 512 | 460 | 249 | 2 | 50 |
| L | 512 | 490 | 202 | 0 | 22 |
| M | 512 | 477 | 194 | 18 | 17 |

Initial number-correct histogram across 512 fitting tasks: N0=0:165, N0=1:141,
N0=2:114, N0=3:92. At least one correct private answer exists on 347 tasks. This
is fitting-bank description, not held-out performance; noncorrect packets include
invalid/abstention cases, so mixed N0 does not itself prove valid correct/wrong support.

| Attack cohort | Accepted | Rejected |
|---|---:|---:|
| Fitting | 364 | 148 |
| Validation | 99 | 29 |
| Source evaluation | 205 | 51 |
| Total | 668 | 228 |

Acceptance means parser/assigned-wrong-answer compliance, not demonstrated attack
effectiveness. Rejected attacks remain missing exchange conditions, with clean
supervision retained. No retries or replacements were introduced.

## Real scratch-training evidence

| Actor | Updates / forwards | Correct before (of 2) | Correct after (of 2) | Restoration hashes |
|---|---:|---:|---:|---|
| Q | 16 / 16 | 2 | 2 | Match |
| L | 16 / 16 | 1 | 2 | Match |
| M | 16 / 16 | 0 | 2 | Match |

All 48 optimizer logs have finite losses and finite nonzero gradient norms. Final
adapter hashes differ from initialization; each recorded restoration hash equals
its initialization hash. Receipt statuses match saved status files, and all six
post-update calls are committed in the validated journal.

Maximum logged gradient norms: Q 4.4554, L 31.3459, M 1495.8011. The pinned training
implementation logs the pre-clipping norm returned by `clip_grad_norm_` and applies
norm clipping at 1. These large initial values are retained, not hidden or treated
as evidence of numerical failure when finite. Native training enforces FP32 adapter/
optimizer states and frozen-base mutation guards before completing each update.

These are repeated updates on the two prescribed fitting tasks, not independent
generalization measurements. The PRIVATE review bundle omits safetensors: matching
restoration receipts and successful runtime checks are observable, but the restored
weights/optimizer tensors cannot be independently rehashed locally from these ZIPs.
RECOVERY remains the required weight-bearing artifact on Drive.

## Disposition and limits

The bounded scratch engineering milestone is complete. Main six-adapter training
has not started; there is no on-policy receiver evaluation, peer-use result,
allocation assay or full PACT efficacy finding. Native private-prefix training is
now observed on all three actors; full receiver-prefix training, longer-context
memory fit, R generation and real Stage II remain unverified.

Next authorized study milestone is the six explicit main fits (independent and
joint, Q/L/M), each initialized by the prescribed matched family initialization,
with fresh optimizer state, 128 updates and fixed epoch-2 primary checkpoints.
Do not initialize main fits from disposable scratch weights. Continue the existing
pinned Colab plan; these documentation updates do not require a source migration.
No automatic Stage II or coupled-training run is authorized by these results.

Local validation executed: archive hash/member checks, source/journal validation,
exact report reproduction, immutable training-bank reconstruction, old-smoke
comparison and all three scratch receipt/log checks. Audit script:
`/tmp/audit_revival_scratch.py`; aggregate output:
`/tmp/pact-revival-scratch-audit-summary.json`. No local GPU calls, pretrained
downloads or code changes were needed; no unit-test rerun is claimed for this audit.
