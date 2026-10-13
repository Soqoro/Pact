# PACT semantic forensics: offline audit, 14 October 2026

The completed private adjudication evidence contains genuine judge-relative peer rescue, alongside enough regressions to reduce aggregate accuracy. This analysis does not establish why particular rationale edits changed judgments. Human semantic review and the optional span intervention have not been executed.

## Verified evidence

Read the actual final PRIVATE parent pair `1791903639856421059`, SHA256 `2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f`. Frozen source is `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`, parent plan `ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`, pool `d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05`. The parent archive was rehashed after analysis and remains unchanged. Analysis code is the local uncommitted implementation recorded in `census_receipt.json`; no reviewed new Git revision exists yet.

The existing safe readers, frozen-request journal validation, strict parser and original report independently reconstructed:

| Quantity | Reconstructed |
|---|---:|
| Existing development tasks | 230: 140 MMLU-Pro, 90 MuSR |
| Clean scored outcomes | 2,760 |
| Clean dispatched calls | 2,726 |
| Deterministic no-selectable-candidate failures | 34 |
| Rewrite attempts | 400 |
| Accepted / rejected rewrites | 369 / 31 |
| Observed victim calls | 2,214 |
| Rejected-variant victim slots, unavailable | 186 |
| Parent total dispatched calls / unresolved | 5,340 / 0 |
| New real model calls in this analysis | 0 |

No private trace was reconstructed from a sanitized summary. Original task/options, candidate IDs/answers/order, non-target packets and correct packets remain protected by parent invariance checks. Reused rationale-blind controls retain their original request/result identities, not additional observations.

## Judge-relative opportunities and clean peer outcomes

T is the particular judge's saved task-only correctness; O is original selectable QLM correct coverage. Quadrants below are task counts on the complete dataset. QQQ is a separate matched comparison, not a substitute for O.

| Dataset / judge | T=0,O=0 | T=0,O=1 | T=1,O=0 | T=1,O=1 | Task-only correct |
|---|---:|---:|---:|---:|---:|
| MMLU-Pro / J8 | 57 | 25 | 22 | 36 | 58/140 |
| MMLU-Pro / J14 | 53 | 24 | 26 | 37 | 63/140 |
| MuSR / J8 | 21 | 19 | 7 | 43 | 50/90 |
| MuSR / J14 | 22 | 17 | 6 | 45 | 51/90 |

`Rescue` is success among T=0,O=1. `Regression` is failure among T=1. `Net correct` is all gains minus all losses, exactly the difference from task-only's number correct. Free synthesis can also construct correct answers on O=0, so rescue alone is not always all gains.

| Dataset / judge / mode | Rescue | Regression | Structural selector losses | Net correct |
|---|---:|---:|---:|---:|
| MMLU-Pro / J8 / full selection | 15/25 | 28/58 | 22 | -13/140 |
| MMLU-Pro / J8 / free synthesis | 14/25 | 25/58 | — | -9/140 |
| MMLU-Pro / J14 / full selection | 12/24 | 32/63 | 26 | -20/140 |
| MMLU-Pro / J14 / free synthesis | 11/24 | 21/63 | — | -10/140 |
| MuSR / J8 / full selection | 13/19 | 15/50 | 7 | -2/90 |
| MuSR / J8 / free synthesis | 11/19 | 13/50 | — | -2/90 |
| MuSR / J14 / full selection | 10/17 | 12/51 | 6 | -2/90 |
| MuSR / J14 / free synthesis | 9/17 | 10/51 | — | -1/90 |

A constrained selector cannot choose a correct answer that is absent from its selectable candidates. For example, 22 of the 28 MMLU/J8 full-selection losses are structural T=1,O=0 cases; six occur despite correct candidate availability. The report separately records covered regression, answer-only/evidence/full comparisons, free construction and QLM/QQQ comparisons.

Potential independent-or-candidate availability is an oracle diagnostic, not a deployable rule or a free-solving upper bound. The exact net counts above are unweighted task-cohort identities. Bootstrap outputs use the inherited equal-stratum weighting and task-group resampling, and are explicitly exploratory; their point estimate need not equal a raw count ratio when stratum sizes differ.

## A matched edited-rationale example

On MuSR/J14 full selection, claimed-consensus rewrites produced 17 clean-correct → valid-wrong flips. Fourteen lost an independently correct answer; three lost an earlier peer-assisted rescue. Two initially wrong selections became correct. There were 27 target-answer adoptions but 26 attacked-candidate selections: those are different events because duplicate answer labels can appear in different candidates.

Ordinary rephrase produced four clean-correct → valid-wrong flips, two wrong → correct changes and two unavailable rejected variants. Comparing the two styles only on their **36 shared available tasks** gives 14 both-wrong, one consensus-only correct, 13 rephrase-only correct and eight both-correct outcomes. The paired consensus-minus-rephrase difference is -12/36 (-33.3 percentage points); the inherited exploratory task-group bootstrap interval is [-50.0, -16.7] points. This is an unadjusted development comparison, not evidence that a particular social cue caused the difference. The full census includes all styles, parser failures, missingness and both-clean-correct judge comparisons.

## Frozen review cohorts

- Main panel: 20 task groups, ten per dataset; all 100 scheduled pair units retained.
- Main availability: 82 accepted pairs, 18 unavailable; no replacements.
- Main plus enriched examples: 115 distinct display units, 97 available. Enriched-only examples are not prevalence data or intervention candidates.
- Potential span slots: 32 main-panel accepted consensus/verification sources, frozen before any semantic labels. These are potential slots, **not** 32 validated edits.
- Two blank reviewer registrations/casebooks; **zero actual reviewers with submitted records, zero independent review pairs, zero semantic adjudications**.

The review sampling frame is the existing label-conditioned mixed-support population, not all 230 tasks or untouched confirmation data. Both private A/B casebooks hide explicit gold, outcomes, style names and model identities. Reviewer-specific sealed maps remain separate. Imported text is escaped and inert. Actual reviews, their origin/blinding and any disagreements still need to be supplied by people.

## Implementation and validation

Implemented `adjudication-forensics` import/census/opportunities/sampling, two-pass casebooks, locked annotation imports, third-person resolutions, agreement/semantic reports and separate exports. Implemented `rationale-spans` exact-edit validation, native metadata/tokenizer preflight, immutable plan and explicit authorization binding, actual native generation, journaled resume, compact durable restore, paired report and exports. The optional notebook defaults all inference flags to false. A fictional offline external-provider fixture carries version/reasoning/refusal/usage/cost metadata; no live API client exists.

The focused CPU suite passed 19 tests, and a separately executed negative-effect fixture also passed (20 new distinct tests), including the complete fictional parent → census → independent fixture reviews → exact spans → explicit fixture approval → 36-call included smoke → all 144 planned fixture calls → export/reimport path. It checked blinding/locks, third-person preservation, missing edits, LLM-origin rejection, HTML escaping, Unicode spans, recipient token-size rules, opportunity identities, source/approval/budget guards, ambiguous dispatch, unsafe latest restore, slot independence from outcomes and notebook defaults. Fixture approvals are not real user approval; fixture outcomes are not scientific evidence.

The real PRIVATE and SANITIZED ZIPs passed checksum/size validation, and the recorded analysis source still matched the current implementation. The sanitized ZIP's checksums were verified. All 230 original task IDs and raw sensitive field names were checked absent. The source PRIVATE archive hash still matches. No GPU, pretrained download, paid API, credential access, commit, push, training or final-test work occurred. GPU/native execution of the new child remains unverified. The wider discovery run executed 315 tests: 296 passed, 17 optional tests skipped, and two existing GPQA fixture tests were blocked by `/tmp` being inside Git. Both passed when rerun with an outside-Git `TMPDIR`; the guard stayed intact. Together with the additional negative-effect fixture, 299 distinct tests passed and 17 were skipped across the executed runs. See [implementation status](../implementation_status.md) for exact commands and timings.

## Private artifacts and next action

Final private review directory: `/var/tmp/pact-semantic-review-20261014`.
The earlier `/var/tmp/pact-adjudication-forensics-001` directory is an intermediate development derivative; use the final review directory above.

Matching export pair:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| `pact-adjudication-forensics-001-PRIVATE-1791909368515824783.zip` | 55,758,672 | `ae7aaeb94ceec7a91a8ea980d6118f80513d568081d7c0ad1c6eb3b229ea402f` |
| `pact-adjudication-forensics-001-SANITIZED-1791909368515824783.zip` | 20,733 | `5fcd328bb1467d0fe73375417239be79375e4570032cfdf7182fb8b5c6c088ea` |

Both are under `/var/tmp/bundles/`. Back up the private directory/ZIP outside Git. These are **pre-review** exports: they cannot unlock real span inference. After actual reviews, export a new reviewed private/sanitized pair and preserve both hashes.

Follow the [local review commands](../semantic_forensics_runbook.md). Give each reviewer only their own `pass1` directory, not analyst mappings or this outcome audit. A reviewer who already saw outcomes must declare `outcome_blinded=false`; the span gate will not treat that as blinded approval. Existing source text can still offer rhetorical clues.

Only after reviews and a separate artifact-bound user decision may the [optional Colab notebook](../../notebooks/21_rationale_spans_colab.ipynb) run exact cue/sham deletions. Maximum 576 new judge attempts / 294,912 reserved output tokens; smoke ≤36 included. There is no minimum-effect gate or replacement for unsuitable controls. No valid controls means not testable. Return matching PRIVATE/SANITIZED child bundles with hashes; no result authorizes another experiment.

Supported finding: peer rescue exists despite lower net accuracy, and selector restrictions account for many losses. Hypothesis: independent-first evidence-gated revision may retain rescue while reducing regression. Missing evidence: independent semantic labels and reviewed cue-versus-sham outcomes. Proposed next comparison: the separately approved local intervention only. No trained remedy or full-PACT efficacy is established; paper placeholders remain unfilled.
