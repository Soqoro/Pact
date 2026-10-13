# Fixed-bank adjudication: completed MuSR / J8 audit

## Verified evidence

Run `pact-adjudication-diagnostic-001`, matched bundle timestamp
`1791789278906883011`. Unchanged plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`
and pinned source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`.

- PRIVATE SHA256: `27c1a3b72aeb279448a3047a7fa260179d1cb0d9e40808f4e55c8c07e3d58f69`.
- SANITIZED SHA256: `4b6666f9c07ba9c49b621716a3ce20a79620b70206c2a7df70c41a5eb1a18655`.

Both archive and internal manifest checksums passed. Repository audit validated
frozen plan/bank, request journal and saved model/access identities. Local report
reconstruction from saved responses exactly matched the uploaded summary and the
sanitized summary. All 230 private task IDs are absent from the sanitized bundle.
All 823 previously imported MMLU-Pro call shards remain byte-identical. Extraction
and regenerated private reports stayed outside Git. Root ZIP uploads are ignored
by the existing `*.zip` rule. No GPU calls or pretrained downloads ran locally.

## MuSR results: 90 shared development tasks

| Mode | Correct | Accuracy | Generated | Missing |
|---|---:|---:|---:|---:|
| qlm_answers_select | 45/90 | 50.00% | 90 | 0 |
| qlm_evidence_select | 47/90 | 52.22% | 90 | 0 |
| qlm_free_synthesis | 48/90 | 53.33% | 90 | 0 |
| qlm_full_select | 48/90 | 53.33% | 90 | 0 |
| qqq_full_select | 48/90 | 53.33% | 90 | 0 |
| task_only_free | 50/90 | 55.56% | 90 | 0 |

All 540 outcomes are scored. QLM full selection and free synthesis each recover
48/62 originally covered tasks, losing 14 covered tasks. Free synthesis constructs
zero correct answers on the 28 originally uncovered tasks. Task-only solves
43/62 covered and 7/28 uncovered tasks, giving 50 total. QQQ full selection recovers
48/50 originally covered tasks. Correct answers do not certify rationale truth.

Adding full rationales to QLM answers-only selection changes eight failures to
successes and five successes to failures: net +3/90 (+3.33 percentage points),
exploratory paired stratified bootstrap interval [-4.44, +11.11] points.
Task-only exceeds QLM free synthesis by +2/90 (+2.22 points), interval
[-10.00, +12.22]; versus full selection the interval is [-10.00, +13.33].
Full selection and free synthesis have equal totals but disagree on six tasks
(three correctness changes in each direction). Equal totals do not show equivalence.
All comparisons are exploratory, unadjusted for multiple comparisons, with task
groups as sampling units rather than calls. No learned PACT efficacy claim follows.

## Accounting

MuSR: 540 new committed calls, 276,480 reserved output tokens, 704,553 actual
input tokens and 68,049 actual output tokens. Invocation wall time 3,528.17 seconds
(58.80 minutes), including 56.49 seconds model loading. Peak allocated/reserved
memory: 16,881,737,728 / 17,377,001,472 bytes. Compute units were not reported.

Cumulative J8: 1,363 attempted and committed calls, zero unresolved; 697,856
reserved output tokens; 1,144,104 actual input and 177,217 actual output tokens.
All 1,380 task-mode outcomes across 230 tasks are scored. The 17 no-call empty
candidate failures belong to the previous MMLU-Pro QQQ stage. Recovery is safe.
Optimizer updates and teacher-forced forwards remain zero.

## Remaining work

Both J8 clean datasets are complete. All 1,380 J14 clean outcomes remain
unobserved. No rewrite or victim calls ran and the perturbation pool is not frozen.
J14 and rewrite GPU behavior remains unverified; metadata access is not execution.

Next prescribed stage is J14/MMLU-Pro clean on the same 140 tasks, at most 840
calls (empty selectable sets can reduce generation), using the unchanged source
and plan. No re-plan, new cohort, budget expansion, training, final-test access or
new study is authorized by these results. No next stage was launched locally.
