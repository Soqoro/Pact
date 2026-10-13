# Fixed-bank adjudication: completed MMLU-Pro / J8 audit

## Evidence and validation

Run `pact-adjudication-diagnostic-001`, matched bundle timestamp
`1791783404661337736`, unchanged source
`8b0f750f29467af84d5ffa9fc30230ce79f3fea1` and plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.

- PRIVATE SHA256: `db93e1a92b4d1d7c97fcc65c96f11a075251c757b9c1383d5b38f42c1a16680a`.
- SANITIZED SHA256: `fcbb96f1c0e3e197f713ae4db348d98e31f4d0cd28ade03c37522038d2aa353b`.

Both archive/internal checksums passed. The repository audit reconstructed the
plan/bank and checked the journal against planned requests and saved model/access
identities. Recomputing the report from saved responses exactly matched the
private summary and the sanitized summary. All 230 private task IDs are absent
from the sanitized archive. The 12 prior smoke call shards are byte-identical.
Private extraction stayed outside Git. No local GPU calls or pretrained downloads
were performed; these are artifact checks, not a fresh rerun of the GPU outputs.

## Results on the same 140 development tasks

| Mode | Correct | Accuracy | Generated | Scored | Missing |
|---|---:|---:|---:|---:|---:|
| qlm_answers_select | 42/140 | 30.00% | 140 | 140 | 0 |
| qlm_evidence_select | 42/140 | 30.00% | 140 | 140 | 0 |
| qlm_free_synthesis | 49/140 | 35.00% | 140 | 140 | 0 |
| qlm_full_select | 45/140 | 32.14% | 140 | 140 | 0 |
| qqq_full_select | 34/140 | 24.29% | 123 | 140 | 0 |
| task_only_free | 58/140 | 41.43% | 140 | 140 | 0 |

Task-only has the highest observed accuracy. Full QLM selection recovers 45/61
originally covered tasks; free synthesis recovers 42/61 and adds 7 correct answers
on 79 originally uncovered tasks. Task-only solves 36/61 covered and 22/79
uncovered tasks. QQQ selection recovers 34/40 covered tasks. These counts describe
answer correctness, not rationale truth or independent reasoning.

Adding full rationales to answers-only selection changes six failures to successes
and three successes to failures: net +3/140 (+2.14 percentage points), exploratory
stratified paired bootstrap interval [-1.43, +6.43] points. Task-only exceeds QLM
free synthesis by 9/140 (+6.43 points), interval [-2.14, +15.00]. Task-only exceeds
full QLM selection by 13/140 (+9.29 points), interval [+0.71, +17.86]. These are
unadjusted exploratory comparisons with 140 task groups as sampling units, not
840 independent observations. Historical 64-token readouts are not matched to
these 512-token modes. No learned PACT efficacy or robustness claim follows.

## Accounting and missingness

823 attempted/committed calls, zero unresolved; 421,376 reserved output tokens,
439,551 actual input tokens, 109,168 actual output tokens. All 840 task-mode
outcomes are scored: 17 QQQ cases have no selectable candidates and produce
prespecified deterministic abstentions without generation. They count as task
failures, not missingness. The previous guidance's 828 additional calls was an
upper bound: this invocation actually made 811, reusing the original 12.

Continuation invocation wall time: 5,472.87 seconds (91.21 minutes), including
56.68 seconds model loading. Peak allocated/reserved bytes:
16,779,995,136 / 17,200,840,704. Compute units were not reported. Optimizer updates
and teacher-forced forwards remain zero. Recovery is safe.

## Remaining work

J8/MMLU-Pro clean is complete. J8/MuSR and both J14 dataset stages remain
unexecuted (1,920 clean outcomes). No rewrite attempts or victims ran; the shared
pool is not frozen. J14/rewrite runtime behavior remains GPU-unverified.

Next prescribed stage: J8 clean adjudication on the same 90 MuSR tasks, at most
540 generation calls, under the existing source and plan. Empty selectable banks
may reduce actual generation. No re-plan, regenerated smoke, budget expansion,
training, new study or final-test use is implied. No next stage was launched locally.
