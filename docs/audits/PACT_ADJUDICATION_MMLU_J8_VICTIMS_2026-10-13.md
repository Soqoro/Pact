# Fixed-bank adjudication: MMLU-Pro / J8 victim audit

## Verified evidence

Run `pact-adjudication-diagnostic-001`; returned pair `1791819015419087502`.
PRIVATE SHA256: `f7ce87aa6292d9b90fc5898a6c74cb87343281c3afafa4b090035b543a107a81`.
SANITIZED SHA256: `4d8b8a76fbc63c3da94eca2f399ba548ed0f7586da79abeceb3c40ac121843cb`.
Unchanged source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`, plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`, pool
`d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05`.

Archive/internal checksums and repository frozen plan/bank/request/model journal
audit passed. Report reconstruction exactly matched the private and sanitized
summaries. All 3,126 previous call shards, pool bytes and clean summaries are
unchanged. All 230 private task IDs are absent from the sanitized archive.
Report reconstruction also checks preservation of correct candidates/coverage and
exact request identity for reused rationale-blind controls. Private extraction
stayed outside Git. No new GPU work or model downloads ran locally.

## Completion and paired results

All 182 accepted MMLU rewrites × three victim modes completed: 546 calls, with
530 valid responses, 11 abstentions, three invalid candidates and two malformed
outputs. The 28 rejected rewrites account for 84 unavailable mode-specific slots;
these are not pending calls and must not be replaced. Population: the original
42 tasks with valid correct/wrong QLM support, not all 140 MMLU tasks.

Each row uses its accepted matched subset. Flip means clean-correct to attacked
failure, including invalid/abstaining outputs. Repeated styles/modes are not
independent task samples. Ordinary rephrase remains a separate control.

| Mode | Style | Paired tasks | Clean correct | Attacked correct | Flips / clean-correct |
|---|---|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 38 | 20 | 18 | 4/20 |
| qlm_evidence_select | claimed_consensus | 40 | 22 | 22 | 4/22 |
| qlm_evidence_select | claimed_independence | 38 | 20 | 21 | 1/20 |
| qlm_evidence_select | claimed_verification | 40 | 22 | 20 | 5/22 |
| qlm_evidence_select | ordinary_rephrase | 26 | 12 | 14 | 0/12 |
| qlm_free_synthesis | argument_pressure | 38 | 20 | 19 | 4/20 |
| qlm_free_synthesis | claimed_consensus | 40 | 22 | 16 | 7/22 |
| qlm_free_synthesis | claimed_independence | 38 | 20 | 22 | 1/20 |
| qlm_free_synthesis | claimed_verification | 40 | 22 | 21 | 3/22 |
| qlm_free_synthesis | ordinary_rephrase | 26 | 13 | 12 | 2/13 |
| qlm_full_select | argument_pressure | 38 | 24 | 16 | 10/24 |
| qlm_full_select | claimed_consensus | 40 | 25 | 18 | 10/25 |
| qlm_full_select | claimed_independence | 38 | 25 | 19 | 7/25 |
| qlm_full_select | claimed_verification | 40 | 25 | 21 | 8/25 |
| qlm_full_select | ordinary_rephrase | 26 | 14 | 14 | 2/14 |

Full selection exhibits correct-to-failure flips for every style; argument
pressure gives 10/24 flips and claimed consensus 10/25. Evidence selection and
free synthesis also exhibit flips, with different clean-correct denominators.
Ordinary rephrase gives full selection 2/14 flips, evidence selection 0/12 and
free synthesis 2/13. Net accuracy can conceal offsetting regressions and repairs.
These descriptive counts do not establish a statistically superior defense or
certify attack semantics. Semantic validity and rationale truth remain unreviewed.

## Fixed four-style prefix robustness

Ordinary rephrase is excluded. Only 37/42 tasks have all four attack variants
available; five have rejected variants. Robust correctness requires the clean
answer and all four attacked answers to be correct.

| Mode | Robust / complete-prefix tasks | Full eligible lower–upper bound |
|---|---:|---:|
| Full selection | 14/37 | 14/42–15/42 |
| Evidence selection | 13/37 | 13/42–16/42 |
| Free synthesis | 13/37 | 13/42–15/42 |

These are availability bounds, not confidence intervals. The complete-prefix
bootstrap lacks the chemistry stratum, limiting its target estimand. Rejected
variants are unavailable, never counted as vacuous robust successes. No security,
equivalence, adaptive-attack or learned PACT efficacy claim follows.

## Accounting and remaining stages

546 new victim calls; 279,552 reserved output tokens; 355,023 actual input and
74,966 actual output tokens. Invocation wall time 3,975.14 seconds (66.25 minutes),
including 98.52 seconds model loading. Peak allocated/reserved bytes:
16,668,773,888 / 16,978,542,592. Compute units unreported.

Cumulative: 3,672 attempted/committed, zero unresolved; 1,880,064 reserved output
tokens; 2,954,456 input and 444,332 output tokens. Recovery safe. All clean outcomes
remain complete; no optimizer updates or teacher-forced forwards.

The report's 1,854 unobserved attack slots comprise 1,668 remaining accepted
requests plus 186 rejected-variant slots across the full study. Next prescribed
stage: MuSR/J8, 187 accepted variants × three modes = 561 requests. Then J14
MMLU (546) and MuSR (561). No next stage ran locally, and this evidence does not
authorize new tasks, replacement rewrites, training or final-test access.
