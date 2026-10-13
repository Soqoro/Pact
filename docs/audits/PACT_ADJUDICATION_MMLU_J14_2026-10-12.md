# Fixed-bank adjudication: completed MMLU-Pro / J14 audit

## Evidence and validation

Run `pact-adjudication-diagnostic-001`, bundle timestamp `1791795047291016862`.
Pinned source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`; unchanged plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.

- PRIVATE SHA256: `a8d2328286cfd203ffa724bf430c957818c1a832ffe239d4d888b04ef8f51bbd`.
- SANITIZED SHA256: `cfdabb27e0d4f56907476898cc3cbf6a7069b5bf09fd156481e9647cebcf66ac`.

The uploaded filenames have a `(1)` suffix; both hashes match. Archive/internal
checksums and the repository's frozen plan/bank/request/model identity journal
audit passed. Reconstructing the report from saved responses reproduced the
private summary exactly; the sanitized summary matches too. All 230 private task
IDs are absent from the sanitized archive. All 1,363 prior J8 call shards are
byte-identical. Private extraction/report generation stayed outside Git. No new
GPU inference or model download was performed locally.

## Matched MMLU-Pro results

| Mode | J8 correct /140 | J14 correct /140 | J14 accuracy | J14 malformed |
|---|---:|---:|---:|---:|
| task_only_free | 58 | 63 | 45.00% | 1 |
| qlm_answers_select | 42 | 43 | 30.71% | 8 |
| qlm_full_select | 45 | 43 | 30.71% | 15 |
| qlm_evidence_select | 42 | 37 | 26.43% | 17 |
| qlm_free_synthesis | 49 | 53 | 37.86% | 0 |
| qqq_full_select | 34 | 30 | 21.43% | 11 |

Every J14 mode has 140 scored outcomes and zero missing. The 52 malformed outputs,
three invalid-candidate outputs, one length-limited output and abstentions remain
failures under the frozen parser; no salvage or retries were used. Answer quality
and format compliance both affect these end-to-end results.

Task-only is highest on observed accuracy. Relative to J8, J14 gains five correct
task-only answers and four free-synthesis answers, but loses two full-selection,
five evidence-selection and four QQQ-selection answers; answers-only gains one.
All six reported paired J8-to-J14 bootstrap intervals include zero. This does not
establish a general capacity benefit, equivalence, or PACT efficacy.

J14 answers-only and full QLM selection each score 43/140, with five improvements
and five regressions between them. The paired difference is zero, bootstrap
interval [-4.29, +4.29] percentage points. Task-only exceeds free synthesis by
10/140 (+7.14 points), interval [0.00, +14.29]. These are exploratory, unadjusted
stratified paired comparisons with task groups as sampling units, not calls.

QLM full selection recovers 43/61 covered tasks; free synthesis recovers 44/61
and constructs 9/79 uncovered answers. Task-only solves 37/61 covered and 26/79
uncovered tasks. QQQ selection recovers 30/40 covered tasks. Correctness does not
certify rationale truth; historical 64-token readouts are descriptive only.

## Accounting and execution evidence

J14/MMLU-Pro: 823 new calls plus 17 deterministic no-call QQQ abstentions;
421,376 reserved output tokens, 439,551 actual input and 90,345 actual output
tokens. Invocation time 5,428.41 seconds (90.47 minutes), including 174.60 seconds
model loading. Peak allocated/reserved bytes: 30,016,430,080 / 30,572,281,856.
J14 execution is now evidenced for this stage and runtime, not every GPU/runtime.

Cumulative: 2,186 attempted/committed calls, zero unresolved; 1,119,232 reserved
output tokens, 1,583,655 input and 267,562 output tokens. All 2,220 completed
stage task-mode outcomes are scored, including 34 no-call failures across the
two MMLU judges. Recovery safe. No optimizer updates or teacher-forced forwards.
Compute units are unreported.

## Remaining work

Only MuSR/J14 remains in clean adjudication: 540 task-mode outcomes, at most
540 calls. It must use the same pinned source and plan. No rewrites or victim
calls have run; the shared pool is not frozen and rewrite GPU behavior remains
unverified. No new study, training, final-test execution, inference-contract
change or paper result claim is authorized by these observations. No subsequent
stage was launched locally.
