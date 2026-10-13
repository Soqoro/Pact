# Fixed-bank adjudication: complete clean-stage audit

## Evidence and validation

Run `pact-adjudication-diagnostic-001`, matched bundle `1791812264006463251`.
Pinned source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`; unchanged plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.

- PRIVATE SHA256: `db47febb6ca30ef2d5d88848e5745495430c37b01302ed4270765e21b8da57d1`.
- SANITIZED SHA256: `6b02d9515098b0b35f91edcd2f15c42053b1a4286cdf0add6610fd1797f3e69a`.

Archive/internal checksum checks and repository audit of frozen plan/bank,
request journal and saved model/access identities passed. Reconstructed reports
exactly match the private and sanitized summaries. All 230 private task IDs are
absent from the sanitized archive. All 2,186 previously audited call shards are
byte-identical. Private extraction/report reconstruction stayed outside Git.
No GPU inference or pretrained downloads were run locally.

## Complete clean results

Counts are correct outcomes, including invalid outputs/abstentions as failures.

| Mode | MMLU J8 /140 | MMLU J14 /140 | MuSR J8 /90 | MuSR J14 /90 |
|---|---:|---:|---:|---:|
| task_only_free | 58 | 63 | 50 | 51 |
| qlm_answers_select | 42 | 43 | 45 | 38 |
| qlm_full_select | 45 | 43 | 48 | 49 |
| qlm_evidence_select | 42 | 37 | 47 | 43 |
| qlm_free_synthesis | 49 | 53 | 48 | 50 |
| qqq_full_select | 34 | 30 | 48 | 47 |

Task-only has the highest observed accuracy in each dataset/judge block. This
is not a claim that every paired difference is distinguishable from zero. All
reported J8-to-J14 paired intervals include zero in both datasets. Larger judge
capacity does not consistently improve the measured end-to-end selection modes.

MuSR/J14 full QLM selection exceeds answers-only by 11/90 (+12.22 percentage
points), with 16 improvements and five regressions; the exploratory stratified
paired bootstrap interval is [+3.33, +21.11] points. Answers-only has 13 invalid
candidate outputs and two abstentions, versus all 90 valid responses for full
selection. This is an end-to-end difference that includes format compliance,
not isolated evidence of improved reasoning. Do not salvage or regenerate them.

MuSR/J14 task-only exceeds free synthesis by 1/90 (+1.11 points), interval
[-8.89, +11.11]. Task-only solves 45/62 originally QLM-covered tasks plus 6/28
uncovered tasks; free synthesis solves 49/62 plus 1/28. Full selection recovers
49/62 covered tasks, while QQQ selection recovers 47/50. These decompositions
separate existing correct coverage from new correct answers; they do not certify
rationale truth. No human rationale annotation has been performed.

Comparisons are exploratory and unadjusted for multiplicity, using task groups
within strata as sampling units, not generation calls. Historical 64-token
readouts are descriptive, not matched controls for these 512-token modes.
The results are development evidence, not learned PACT efficacy or final tests.

## Completion and resources

All 2,760 planned clean task-mode outcomes across 230 tasks and two judges are
scored, with zero missing. There are 2,726 attempted/committed calls and 34
prescribed deterministic no-call failures (17 empty QQQ candidate sets for each
MMLU judge). Unresolved calls: zero; recovery safe. Total reserved output tokens:
1,395,712; actual input/output tokens: 2,288,208 / 323,213. Optimizer updates and
teacher-forced forwards: zero. Compute units are unreported.

Latest MuSR/J14 invocation: 540 new calls, 276,480 reserved output tokens,
704,553 input and 55,651 output tokens. Wall time 3,483.15 seconds (58.05 minutes),
including 175.45 seconds loading. Peak allocated/reserved bytes:
30,132,692,992 / 31,201,427,456. Both judges now have real clean-stage GPU evidence;
this does not establish compatibility with arbitrary future runtimes.

## Remaining prescribed study stages

No rewrite attempts or victim calls have run; the shared pool is not frozen.
The next stage is frozen rationale-only rewrite acquisition: 42 MMLU and 38 MuSR
eligible tasks, five one-attempt styles each, at most 400 calls total (210/190).
Both datasets must finish and the full pool must freeze before any victim call.
Rejected variants stay rejected, with no replacement sampling. Preserve candidate
answers, all correct packets, fixed identities and the original plan/budgets.
Victim evaluation remains a separate subsequent stage, at most 2,400 calls.

No further stage was launched locally. These outcomes do not authorize a new
study, training, inference-contract changes or final-test access. Manuscript
PACT placeholders remain unfilled.
