# Selective correction: completed core study, KEEP_ONLY operating point

All five CPU gates trained and converged on the real collected fitting evidence.
All five selected **KEEP_ONLY** on the separate tuning split. On the 64-task
source-development cohort, the prespecified restricted-augmented policy therefore
preserves the independent anchor: **44/64 correct, zero rescues, zero harms and
zero switches**. This is a completed negative result for useful learned correction
under this preset, not demonstrated PACT improvement or a risk certificate.

The anchor-inclusive selection control has a material format failure: all 202
clean/variant outputs are malformed under its frozen schema. Its deployed result
is entirely original-anchor fallback. It cannot support a claim that a functioning
selector independently matched the anchor. Optional transfer has not been invoked.

## Evidence and accounting

Returned matching pair: `pact-selective-correction-001-{PRIVATE,SANITIZED}-1791993400383124336.zip`.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| PRIVATE | 22,242,012 | `b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449` |
| SANITIZED | 8,882 | `120cffccfd552fdd6c0bf747ebbd0cfb6e7e8455700bf2200c53b9b1e96dab4e` |

Pinned clean commit: `9b65ae343b52777b5b716c9adf090959588b72c3`.
Plan hash: `848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6`.
There are 224 distinct tasks/groups: 128 fit, 32 tuning, 64 source-development,
equal ARC-Challenge/original English LogiQA allocation within each split. Selected
IDs, group IDs, content groups and cross-dataset fingerprints do not intersect the
recorded exclusion inventory. This is recorded lexical screening, not semantic
decontamination or verification against unknown external use.

| Quantity | Observed |
|---|---:|
| Attempted / committed calls | 3,579 / 3,579 |
| Unresolved calls | 0 |
| Fit / tuning / development calls | 1,669 / 371 / 1,539 |
| Fit+tuning cap / development cap | 3,360 / 2,240 |
| Reserved output tokens | 1,832,448 |
| Actual input / output tokens | 1,876,965 / 346,520 |
| Gate fits / maximum iterations observed | 5 / 189 |
| LLM optimizer updates / teacher-forced forwards | 0 / 0 |

All 896 source calls are present: 224 independent anchors and 672 natural private
packets. The remaining calls are 364 rewrite attempts, 579 shared extractions,
577 full and 577 restricted verifications, 202 anchor-inclusive selections and
384 independent critique/reconsider calls. Lower-than-ceiling totals reflect
inapplicable targets, no-op alternatives, disabled extraction paths and exact reuse;
the cohort was not reduced. Saved recovery state is safe. Reported GPU resource
records accompany all four pristine models; no adapters or LLM updates occurred.

## Fitting and threshold selection

All fits used NumPy 2.2.3 and the specified weighted multinomial objective. Clean
fitting has 171 candidate rows: 112 harmful, 27 neutral and 32 improving replacements.
Improvement examples occur on 22 distinct fit groups; harmful examples on 63.
Augmentation has 487 correlated rows (336 harmful / 81 neutral / 70 improving),
not 487 independent tasks. All five models genuinely trained; KEEP_ONLY was selected
by tuning rather than forced by absent improvement support.

Iterations: full-clean 175, full-augmented 189, restricted-clean 162,
restricted-augmented 160, metadata-augmented 50. Recomputed saved-coefficient loss
and analytic gradient match the recorded objective; each gradient infinity norm is
below 1e-6. No local refitting was performed.

The tuning anchor is correct on 25/32 tasks. For the primary restricted-augmented
gate, every finite grid threshold already produces zero switches and zero gain;
KEEP_ONLY wins the prescribed final tie-break. The same is true for full-augmented,
restricted-clean and metadata. Full-clean at thresholds 0 through .35 incurs one
attack-pool harm with no clean gain; thresholds .50/.75 and KEEP_ONLY tie at zero
switches, with KEEP_ONLY again selected. The 5% screen was not relaxed.

## Clean source-development results

Each dataset has 32 tasks. Rescue/harm are relative to the exact independent anchor.

| Method | ARC correct | ARC rescue / harm | LogiQA correct | LogiQA rescue / harm |
|---|---:|---:|---:|---:|
| Always KEEP | 27 | 0 / 0 | 17 | 0 / 0 |
| Primary restricted-augmented | 27 | 0 / 0 | 17 | 0 / 0 |
| Each other learned gate | 27 | 0 / 0 | 17 | 0 / 0 |
| Anchor-inclusive selector, **fallback result only** | 27 | 0 / 0 | 17 | 0 / 0 |
| Six-call independent reconsideration | 27 | 1 / 1 | 17 | 1 / 1 |
| Fixed restricted-verdict rule | 15 | 0 / 12 | 14 | 3 / 6 |

The available anchor-plus-peer oracle covers 27/32 ARC and 26/32 LogiQA tasks.
There are no wrong-anchor/correct-peer opportunities on ARC and nine on LogiQA.
The primary policy uses none of those nine. Independent reconsideration may construct
answers outside the peer bank; its ARC rescue is not evidence of peer utilization.
Its five final abstentions use the explicit original-anchor fallback; strict correct
counts are 26 ARC / 15 LogiQA versus deployed 27 / 17.

The selector has 0/64 strict clean successes and 202/202 malformed outputs overall.
Of these, 198 are JSON objects with keys `decision_basis`, `candidate_id`, **and an
extra `anchor` field**; four do not parse as JSON. The instruction's wording lists
`"candidate_id", "anchor", c0/c1/c2 or "ABSTAIN"` while requiring exactly two keys.
This is a plausible prompt-contract ambiguity, not proof of the causal mechanism.
No field was stripped, parser relaxed or result silently rescored. A prospective
correction requires an explicit decision; it does not authorize replacement calls.

## Attack and checker evidence

Fit has 183 accepted rewrites and one malformed attempt; tuning has 42 accepted
rewrites. Source-development has 138 accepted rewrites: three styles on 46 eligible
tasks, with no missing development variants. Remaining slots have no valid wrong
peer target. Acceptance does not establish semantic preservation.

For the primary KEEP_ONLY policy, clean-and-both-attack correctness is 15/20 eligible
ARC tasks and 12/26 eligible LogiQA tasks. The two-attack prefixes are complete and
their missingness bounds coincide. Ordinary rephrase is reported separately. These
outcomes are invariant by construction when copying the anchor, not learned evidence
filtering or an adaptive robustness guarantee.

Development has 295 candidate/view feature rows, with one malformed extractor row,
two disabled full paths and seven disabled restricted paths. Full/restricted verdicts
agree on 258/295 rows. Intrinsic-knowledge assessment is dominant: 259 full and 245
restricted rows, versus 23 and 42 explicit-task rows. These are unverified model
assessments; exact source spans are not proof. The 883 logical collection paths
reuse 324 paths, leaving 559 unique checking calls.

## Disposition

Preserve this completed core run and its negative learned-policy outcome. Do not
lower thresholds, rerun completed tasks or repair the selector by retrospective
parsing. Review the prompt/format limitation before deciding on further experiments.
Transfer remains separately invoked and unexecuted; with frozen KEEP_ONLY policies,
the learned gate decisions would remain anchor copies on transfer as well.
Human semantic review, cue/sham intervention and original full-PACT training remain
deferred. No result automatically authorizes another run.

## Local audit validation

Both user-supplied ZIP hashes and internal archive checksums passed. The trusted
reader checked paths before extraction into
`/var/tmp/pact-selective-audit-1791993400383124336`, outside Git. All call identities,
native model/access identities, token accounting, extractor dependencies and recovery
state validated. Reconstructed natural sources, immutable target/rewrite pools and
all three split feature banks from committed evidence with execution disabled.
Verified the five existing model/fit hashes without fitting; recomputed weighted
objective and gradients at saved coefficients; reproduced all threshold curves and
choices, saved baseline outputs, frozen policy decisions and the full summary.

Repeated immutable metadata/source reads were cached only within the offline audit
process, with byte hashes checked before and after and an uncached plan validation
at the end. No inference implementation was changed. The sanitized summary equals
the reconstructed private summary; all selected task IDs and question strings were
checked absent from its payload. The source PRIVATE archive remains unchanged.
Receipt: `local_audit_receipt.json` in the private audit directory.

This was artifact reconstruction, not a fresh GPU run. Zero new model calls, fits,
downloads, human annotations, commits or pushes. Existing local exposure-inventory
follow-up changes were preserved. The exposure builder now refuses a ledger newer
than its reviewed coverage, preventing the old inventory from silently certifying
the just-executed 224 tasks as fresh. Its four focused CPU tests passed in 0.039s;
the full regression suite was not rerun for this audit. `git diff --check` passed.
