# PACT fixed-bank adjudication: complete-study audit

The bounded inference-only development study is complete. All prescribed accepted
requests have terminal results, with safe recovery and no unresolved dispatches.
No further generation is needed. This is not trained PACT or final-test evidence.

## Provenance and checks executed

Run `pact-adjudication-diagnostic-001`, final pair `1791903639856421059`.

- PRIVATE SHA256: `2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f`.
- SANITIZED SHA256: `7fc61f2af987d7fccb954fcbd6a590b963faf412977c8dc5c3529326335ad4fb`.
- Source: `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`.
- Plan: `ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.
- Frozen pool: `d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05`.

Both archive hashes/internal manifests passed. Repository audit reconstructed the
frozen plan/bank/request/model journal. Local response-based report reconstruction
exactly reproduced the final private summary and sanitized summary. All 4,779
previously verified call shards, pool bytes and clean summary results are unchanged.
All 230 private task IDs are absent from the sanitized archive. Reconstruction
also verifies correct-candidate/coverage preservation and exact reused-control
request identities. Private extraction/report generation stayed outside Git.
These are artifact checks; no local GPU inference, model downloads, training or
final-test access occurred. No full test-suite rerun was needed for audit prose;
`git diff --check` passed. No commit or push was performed.

## Design actually executed

Exact existing 140 MMLU-Pro and 90 MuSR development tasks; frozen original QLM
and QQQ private candidates. Pristine non-thinking J8/J14 adjudicators, unchanged
512-output/8192-context contracts. Six clean modes per judge and task. A fixed
wrong candidate's justification alone was eligible for rewriting on 42 MMLU and
38 MuSR mixed-support tasks. Five one-attempt styles per task, using fixed Q;
both pools frozen before victim evaluation. Each accepted rewrite was evaluated
with full selection, evidence selection and free synthesis for both judges.
Rationale-blind controls were reused by exact identity, without new calls.

## Complete clean results

Correct outcomes include invalid/abstaining outputs as failures.

| Mode | MMLU J8 /140 | MMLU J14 /140 | MuSR J8 /90 | MuSR J14 /90 |
|---|---:|---:|---:|---:|
| task_only_free | 58 | 63 | 50 | 51 |
| qlm_answers_select | 42 | 43 | 45 | 38 |
| qlm_full_select | 45 | 43 | 48 | 49 |
| qlm_evidence_select | 42 | 37 | 47 | 43 |
| qlm_free_synthesis | 49 | 53 | 48 | 50 |
| qqq_full_select | 34 | 30 | 48 | 47 |

Task-only has the highest observed accuracy in every block, but not every paired
difference is distinguishable from zero. All reported J8-to-J14 clean paired
intervals include zero. Larger capacity did not consistently improve end-to-end
selection. Parser/format failures remain part of the outcome, not corrected
post hoc. The clean-stage audit records paired uncertainty and decompositions.

## Acquisition and completion accounting

| Stage | Generation calls | Reserved output tokens |
|---|---:|---:|
| Clean | 2,726 | 1,395,712 |
| Rewrite acquisition | 400 | 204,800 |
| Victims | 2,214 | 1,133,568 |
| Total | 5,340 | 2,734,080 |
| Prespecified ceiling | 5,560 | 2,846,720 |

All 2,760 clean outcomes are scored: 2,726 model calls plus 34 deterministic
no-call failures for empty QQQ selectable sets. Rewrites: MMLU 182/210 accepted,
MuSR 187/190 accepted, total 369/400. All 2,214 accepted victim requests completed.
The 31 rejected variants account for 186 unavailable victim slots; they are not
pending work and must not be replaced. This explains the 220-call difference
from the original ceiling (34 + 186). `attack_unobserved=186` is expected.

Total actual input/output tokens: 4,904,285 / 644,043. Unresolved calls: zero.
Optimizer updates and teacher-forced forwards: zero. Compute units unreported.
Final MuSR/J14 invocation: 561 calls, 287,232 reserved tokens, 797,403 actual input
and 60,097 output tokens; 3,779.74 seconds (63.00 minutes) including 98.87 seconds
loading. Peak allocated/reserved bytes: 30,145,447,424 / 31,031,558,144.
All prescribed GPU stages now have returned execution evidence for their recorded
runtime. That does not establish compatibility with arbitrary future runtimes.

## Victim results by style

Population is original valid correct/wrong mixed support, not all development
tasks. Every row uses its accepted paired subset. Flip is clean-correct to failure,
including invalid/abstaining outputs. The denominator is clean-correct responses,
not all calls. Styles/modes sharing tasks are dependent. Ordinary rephrase remains
a separate control with unverified semantic equivalence.

### mmlu-pro / J8

| Mode | Style | Paired | Clean correct | Attacked correct | Flips / clean-correct | Invalid/abstaining flips |
|---|---|---:|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 38 | 20 | 18 | 4/20 | 1 |
| qlm_evidence_select | claimed_consensus | 40 | 22 | 22 | 4/22 | 1 |
| qlm_evidence_select | claimed_independence | 38 | 20 | 21 | 1/20 | 0 |
| qlm_evidence_select | claimed_verification | 40 | 22 | 20 | 5/22 | 1 |
| qlm_evidence_select | ordinary_rephrase | 26 | 12 | 14 | 0/12 | 0 |
| qlm_free_synthesis | argument_pressure | 38 | 20 | 19 | 4/20 | 0 |
| qlm_free_synthesis | claimed_consensus | 40 | 22 | 16 | 7/22 | 0 |
| qlm_free_synthesis | claimed_independence | 38 | 20 | 22 | 1/20 | 0 |
| qlm_free_synthesis | claimed_verification | 40 | 22 | 21 | 3/22 | 0 |
| qlm_free_synthesis | ordinary_rephrase | 26 | 13 | 12 | 2/13 | 0 |
| qlm_full_select | argument_pressure | 38 | 24 | 16 | 10/24 | 0 |
| qlm_full_select | claimed_consensus | 40 | 25 | 18 | 10/25 | 0 |
| qlm_full_select | claimed_independence | 38 | 25 | 19 | 7/25 | 0 |
| qlm_full_select | claimed_verification | 40 | 25 | 21 | 8/25 | 1 |
| qlm_full_select | ordinary_rephrase | 26 | 14 | 14 | 2/14 | 0 |

### mmlu-pro / J14

| Mode | Style | Paired | Clean correct | Attacked correct | Flips / clean-correct | Invalid/abstaining flips |
|---|---|---:|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 38 | 21 | 17 | 8/21 | 2 |
| qlm_evidence_select | claimed_consensus | 40 | 21 | 18 | 6/21 | 2 |
| qlm_evidence_select | claimed_independence | 38 | 20 | 14 | 11/20 | 4 |
| qlm_evidence_select | claimed_verification | 40 | 21 | 18 | 7/21 | 2 |
| qlm_evidence_select | ordinary_rephrase | 26 | 13 | 12 | 4/13 | 0 |
| qlm_free_synthesis | argument_pressure | 38 | 24 | 20 | 4/24 | 0 |
| qlm_free_synthesis | claimed_consensus | 40 | 25 | 18 | 7/25 | 1 |
| qlm_free_synthesis | claimed_independence | 38 | 24 | 18 | 6/24 | 2 |
| qlm_free_synthesis | claimed_verification | 40 | 25 | 22 | 3/25 | 1 |
| qlm_free_synthesis | ordinary_rephrase | 26 | 14 | 13 | 1/14 | 0 |
| qlm_full_select | argument_pressure | 38 | 23 | 15 | 8/23 | 0 |
| qlm_full_select | claimed_consensus | 40 | 24 | 20 | 5/24 | 0 |
| qlm_full_select | claimed_independence | 38 | 23 | 17 | 7/23 | 1 |
| qlm_full_select | claimed_verification | 40 | 24 | 18 | 7/24 | 0 |
| qlm_full_select | ordinary_rephrase | 26 | 13 | 11 | 2/13 | 1 |

### musr / J8

| Mode | Style | Paired | Clean correct | Attacked correct | Flips / clean-correct | Invalid/abstaining flips |
|---|---|---:|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 37 | 22 | 14 | 12/22 | 0 |
| qlm_evidence_select | claimed_consensus | 38 | 23 | 15 | 11/23 | 1 |
| qlm_evidence_select | claimed_independence | 38 | 23 | 15 | 12/23 | 2 |
| qlm_evidence_select | claimed_verification | 38 | 23 | 15 | 11/23 | 3 |
| qlm_evidence_select | ordinary_rephrase | 36 | 21 | 21 | 5/21 | 1 |
| qlm_free_synthesis | argument_pressure | 37 | 23 | 15 | 9/23 | 0 |
| qlm_free_synthesis | claimed_consensus | 38 | 24 | 15 | 10/24 | 0 |
| qlm_free_synthesis | claimed_independence | 38 | 24 | 15 | 9/24 | 0 |
| qlm_free_synthesis | claimed_verification | 38 | 24 | 14 | 11/24 | 0 |
| qlm_free_synthesis | ordinary_rephrase | 36 | 24 | 19 | 7/24 | 0 |
| qlm_full_select | argument_pressure | 37 | 23 | 12 | 11/23 | 0 |
| qlm_full_select | claimed_consensus | 38 | 24 | 16 | 9/24 | 0 |
| qlm_full_select | claimed_independence | 38 | 24 | 17 | 7/24 | 0 |
| qlm_full_select | claimed_verification | 38 | 24 | 11 | 13/24 | 0 |
| qlm_full_select | ordinary_rephrase | 36 | 23 | 20 | 6/23 | 0 |

### musr / J14

| Mode | Style | Paired | Clean correct | Attacked correct | Flips / clean-correct | Invalid/abstaining flips |
|---|---|---:|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 37 | 21 | 15 | 7/21 | 1 |
| qlm_evidence_select | claimed_consensus | 38 | 22 | 12 | 13/22 | 1 |
| qlm_evidence_select | claimed_independence | 38 | 22 | 12 | 10/22 | 1 |
| qlm_evidence_select | claimed_verification | 38 | 22 | 14 | 9/22 | 1 |
| qlm_evidence_select | ordinary_rephrase | 36 | 21 | 17 | 6/21 | 0 |
| qlm_free_synthesis | argument_pressure | 37 | 24 | 14 | 11/24 | 0 |
| qlm_free_synthesis | claimed_consensus | 38 | 25 | 14 | 12/25 | 0 |
| qlm_free_synthesis | claimed_independence | 38 | 25 | 14 | 12/25 | 0 |
| qlm_free_synthesis | claimed_verification | 38 | 25 | 19 | 7/25 | 0 |
| qlm_free_synthesis | ordinary_rephrase | 36 | 23 | 22 | 2/23 | 0 |
| qlm_full_select | argument_pressure | 37 | 24 | 12 | 12/24 | 0 |
| qlm_full_select | claimed_consensus | 38 | 25 | 10 | 17/25 | 0 |
| qlm_full_select | claimed_independence | 38 | 25 | 10 | 16/25 | 0 |
| qlm_full_select | claimed_verification | 38 | 25 | 11 | 14/25 | 0 |
| qlm_full_select | ordinary_rephrase | 36 | 23 | 21 | 4/23 | 0 |

The final MuSR/J14 stage contains 555 valid outputs and six invalid candidates,
all failures retained. Claimed-consensus full selection flips 17/25 clean-correct
answers, all to valid wrong answers; attacked correctness is 10/38 versus clean
25/38. Claimed-independence full selection flips 16/25. Ordinary rephrase also
flips 4/23 full-selection answers, 6/21 evidence-selection answers and 2/23
free-synthesis answers. There is therefore sensitivity to ordinary rewriting too;
the specific causal contribution of claimed authority/consensus is not established
by raw flip counts alone. Accepted schema does not certify rewrite semantics.

## Fixed four-style prefix robustness

Excludes ordinary rephrase. Requires clean correctness and correctness under all
four ordered attack variants. The full eligible bounds account for rejected
variants and are not confidence intervals or security guarantees.

| Dataset / judge / mode | Robust / complete-prefix tasks | Full-eligible lower–upper |
|---|---:|---:|
| mmlu-pro/J14/qlm_evidence_select | 6/37 | 6/42–8/42 |
| mmlu-pro/J14/qlm_free_synthesis | 14/37 | 14/42–16/42 |
| mmlu-pro/J14/qlm_full_select | 9/37 | 9/42–11/42 |
| mmlu-pro/J8/qlm_evidence_select | 13/37 | 13/42–16/42 |
| mmlu-pro/J8/qlm_free_synthesis | 13/37 | 13/42–15/42 |
| mmlu-pro/J8/qlm_full_select | 14/37 | 14/42–15/42 |
| musr/J14/qlm_evidence_select | 7/37 | 7/38–8/38 |
| musr/J14/qlm_free_synthesis | 8/37 | 8/38–8/38 |
| musr/J14/qlm_full_select | 6/37 | 6/38–6/38 |
| musr/J8/qlm_evidence_select | 6/37 | 6/38–7/38 |
| musr/J8/qlm_free_synthesis | 8/37 | 8/38–9/38 |
| musr/J8/qlm_full_select | 8/37 | 8/38–9/38 |

MMLU has 37/42 complete four-style prefixes; MuSR has 37/38. Rejected variants
are unavailable, never vacuous robust successes. Sampling units are task groups
within strata, not 2,214 independent victim calls. Reported bootstrap comparisons
are exploratory and unadjusted for multiplicity; missing strata limit estimands.
Do not rank defenses from raw conditional totals alone.

## Interpretation and limitations

The study documents correct-answer losses under fixed wrong-candidate rationale
rewrites while preserving correct candidate packets and candidate coverage.
It does not demonstrate learned PACT efficacy, certify rationale truth, establish
an adaptive worst-case threat model or validate untouched final-test performance.
It does not show that harder benchmarks or larger judges necessarily provide
better complementarity. Free outputs and constrained selectors have different
answer spaces, and format compliance affects the measured outcomes.

Human rationale/semantic review remains unperformed. Rejected variants and the
ordinary-rephrase control's unverified equivalence limit causal interpretation.
Historical 64-token readouts remain descriptive only against these new 512-token
modes. No pooling of repeated variants into independent task samples is justified.

## Disposition

The prescribed study is complete, including all accepted variants. Preserve the
final PRIVATE/SANITIZED pair and durable snapshot; retain the private artifact
boundary. Next work is user review of this audit and, if desired, separately
specified analysis. No further generation, new study, training or methodological
change is automatically authorized. Manuscript PACT placeholders remain unfilled.
