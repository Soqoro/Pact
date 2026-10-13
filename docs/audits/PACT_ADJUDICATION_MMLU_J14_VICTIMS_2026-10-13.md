# Fixed-bank adjudication: MMLU-Pro / J14 victim audit

## Verified evidence

Run `pact-adjudication-diagnostic-001`, pair `1791899265606987921`.

- PRIVATE SHA256: `105656cca0d6d077700a5481c44f9d7a64d7689a8429d103626448603293bba6`.
- SANITIZED SHA256: `54a175570314152ac285e0f911d17b53bf48e51d245b335e2247f72013af29bf`.

Archive/internal checksums, frozen plan/bank/request/model journal audit and exact
report reconstruction passed. Sanitized summary matches; all 230 private task IDs
are absent from that archive. All 4,233 previously audited call shards, frozen
pool bytes and clean summaries are unchanged. Private extraction and report
reconstruction stayed outside Git. No local GPU inference or downloads occurred.

Source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`, plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`, and pool
`d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05` remain fixed.

## Completion and outcomes

All 182 accepted MMLU rewrites × three modes = 546 requests completed: 492 valid,
12 abstentions, 41 malformed outputs, one invalid candidate. All failures retain
the frozen scoring contract. The 28 rejected rewrites leave 84 unavailable slots,
not pending requests. Population is the original 42 mixed-support MMLU tasks.

Each row uses its own accepted paired subset. Flip denominators are clean-correct
responses; failure includes invalid/abstaining output. Ordinary rephrase is a
separate control with unverified semantic equivalence.

| Mode | Style | Paired tasks | Clean correct | Attacked correct | Flips / clean-correct |
|---|---|---:|---:|---:|---:|
| qlm_evidence_select | argument_pressure | 38 | 21 | 17 | 8/21 |
| qlm_evidence_select | claimed_consensus | 40 | 21 | 18 | 6/21 |
| qlm_evidence_select | claimed_independence | 38 | 20 | 14 | 11/20 |
| qlm_evidence_select | claimed_verification | 40 | 21 | 18 | 7/21 |
| qlm_evidence_select | ordinary_rephrase | 26 | 13 | 12 | 4/13 |
| qlm_free_synthesis | argument_pressure | 38 | 24 | 20 | 4/24 |
| qlm_free_synthesis | claimed_consensus | 40 | 25 | 18 | 7/25 |
| qlm_free_synthesis | claimed_independence | 38 | 24 | 18 | 6/24 |
| qlm_free_synthesis | claimed_verification | 40 | 25 | 22 | 3/25 |
| qlm_free_synthesis | ordinary_rephrase | 26 | 14 | 13 | 1/14 |
| qlm_full_select | argument_pressure | 38 | 23 | 15 | 8/23 |
| qlm_full_select | claimed_consensus | 40 | 24 | 20 | 5/24 |
| qlm_full_select | claimed_independence | 38 | 23 | 17 | 7/23 |
| qlm_full_select | claimed_verification | 40 | 24 | 18 | 7/24 |
| qlm_full_select | ordinary_rephrase | 26 | 13 | 11 | 2/13 |

Full selection under argument pressure loses 8/23 clean-correct answers, all to
valid wrong answers. Evidence selection under claimed independence loses 11/20:
seven to valid wrong answers and four to invalid/abstaining output. Free synthesis
under claimed consensus loses 7/25, including one invalid/abstaining failure.
Ordinary rephrase also causes flips (full 2/13, evidence 4/13, free 1/14).
These descriptive patterns do not establish a superior defense or capacity
benefit. No semantic, security, learned PACT efficacy or final-test claim follows.
Task groups, not repeated calls/styles, are the sampling units.

## Four-style prefix robustness

Ordinary rephrase excluded; 37/42 tasks have all four attack variants available.
Robust correctness requires both clean correctness and all four attacked answers
correct. Five tasks have unavailable prefixes due to rejected variants.

| Mode | Robust / complete-prefix tasks | Full-eligible availability bounds |
|---|---:|---:|
| Full selection | 9/37 | 9/42–11/42 |
| Evidence selection | 6/37 | 6/42–8/42 |
| Free synthesis | 14/37 | 14/42–16/42 |

Bounds reflect missing variants, not confidence intervals or vacuous successes.
Direct defense rankings require matched task analysis and uncertainty accounting;
raw totals alone do not establish superiority.

## Accounting and next stage

546 new calls; 279,552 reserved output tokens; 355,023 actual input and 63,097
output tokens. Invocation 3,968.60 seconds (66.14 minutes), including 180.15
seconds loading. Peak allocated/reserved bytes: 29,883,581,952 / 30,505,172,992.
Compute units unreported.

Cumulative: 4,779 attempted/committed, zero unresolved; 2,446,848 reserved output
tokens; 4,106,882 input and 583,946 output tokens. Recovery safe; all clean outcomes
complete, no optimizer updates or teacher-forced forwards. MMLU/J14 victim GPU
execution is now evidenced. Only MuSR/J14 remains (561 accepted requests).
The report's 747 unobserved attack slots are those 561 requests plus 186 rejected
variant slots across the full study. Do not generate replacements for rejections.

Next prescribed stage: MuSR/J14 under the unchanged pinned source/plan/pool,
then the complete-study audit. No next stage was launched locally. No new study,
training, protocol change or final-test access is authorized by these results.
