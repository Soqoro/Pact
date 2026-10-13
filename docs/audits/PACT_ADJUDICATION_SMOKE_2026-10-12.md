# Fixed-bank adjudication: imported J8 smoke audit

The returned two-task MMLU-Pro smoke passes local integrity, journal and report
reconstruction checks. This verifies the exercised J8 inference path, not the
full study or scientific efficacy. No additional inference was run locally.

## Evidence

- Run: `pact-adjudication-diagnostic-001`.
- Clean source: `8b0f750f29467af84d5ffa9fc30230ce79f3fea1`.
- Plan: `ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.
- Matched bundle timestamp: `1791775339796803377`.
- PRIVATE SHA256: `af19f35685f7a9d34bbb03a8e9d4958603b8ce434a03c5138d78e0680989ec0f`.
- SANITIZED SHA256: `a57b71f5ff21d305019bdec0cbe76e4dfcc767a5307c14af302cc9a72d87f6c1`.

Both ZIP checksums and internal review checksums passed. The repository audit
reconstructed the frozen plan/bank and matched call requests, identities and
journal entries. Recovery is safe. Recomputing the report from saved responses
exactly reproduced the uploaded summary; the sanitized summary also matched.
Its members contain only the aggregate export artifacts and handoff metadata;
all 230 private task IDs are absent. Private files were extracted outside Git.

## Results

| Measure | Observed |
|---|---:|
| Tasks | 2 |
| Attempted / committed calls | 12 / 12 |
| Unresolved calls | 0 |
| Valid parsed responses | 12 / 12 |
| Reserved output tokens | 6,144 |
| Actual input / output tokens | 4,540 / 1,510 |
| Optimizer updates / teacher-forced forwards | 0 / 0 |

Every mode scored **0/2**: task-only free, QLM answers selection, QLM full
selection, QLM evidence selection, QLM free synthesis and QQQ full selection.
One of the two tasks had original QLM correct-answer coverage; each QLM mode
failed to use it. This is a descriptive observation on two shared tasks, not
twelve independent samples. It establishes neither equivalence nor a population
effect. No rationale truth annotation has been performed.

The recorded J8 invocation took 182.26 seconds, including 97.70 seconds of model
loading. Peak allocated memory was 16,511,726,592 bytes; peak reserved memory was
16,607,346,688 bytes. These measurements do not establish J14 fit or throughput.

## Scope and next stage

The 12 smoke requests belong to the unchanged full clean plan and must be reused.
There are 2,748 clean calls still unobserved. No rewrites or victims ran; the pool
is not frozen. J14 and rewrite Q have access evidence, not executed GPU evidence.
The study ceiling remains 5,560 calls / 2,846,720 reserved output tokens.

The next prescribed stage is clean MMLU-Pro adjudication with J8: 840 total
requests, of which 12 are already committed, leaving 828 new calls. Continue
with the same pinned source, plan hash and safe run state. Do not rerun planning
or replace the smoke tasks because their answers were wrong. No new study,
training, final-test execution or manuscript claim is authorized by this audit.
