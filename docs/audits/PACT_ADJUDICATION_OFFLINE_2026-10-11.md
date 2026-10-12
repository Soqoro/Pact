# Fixed-bank adjudication: offline evidence and implementation audit

Prepared 11 October 2026. No new model inference or training was performed.
This report verifies the three required completed breadth parents and records the
new implementation. It does not change the [project-wide audit](PACT_PROJECT_AUDIT_2026-10-11.md)
or claim an adjudication improvement.

## Verified parent findings

The exact pinned PRIVATE MMLU-Pro, MuSR and MATH bundles passed safe archive and
internal checksum validation, frozen source/plan/model checks, full call/dependency
reconstruction, complete A/B status and deterministic old-report comparison.
All MMLU/MuSR MCQ scores were independently recomputed using the existing strict
parser/scorer. MATH format/joint findings use its recorded pinned Math-Verify
scores; this phase did not independently rerun symbolic scoring or generations.

| QLM measure | MMLU-Pro | MuSR | MATH-500 (offline only) |
|---|---:|---:|---:|
| Tasks | 140 | 90 | 100 |
| Initial coverage O0 | 61 | 62 | 74 |
| Revised coverage O1 | 59 | 57 | 74 |
| Old private synthesis correct | 40 | 45 | 81 |
| Old revised readout correct Y | 43 | 46 | 77 |
| Old task-only correct | 35 | 52 | 74 |
| Erasure: O0=1, O1=0 | 11 | 5 | 2 |
| New availability: O0=0, O1=1 | 9 | 0 | 2 |
| Initially covered terminal failure | 23 | 16 | 4 |
| Revised readout loss: O1=1, Y=0 | 16 | 11 | 3 |
| Construction from initial unavailability | 5 | 0 | 7 |
| Construction from revised unavailability | 0 | 0 | 6 |
| Initial valid correct/wrong mixed support | 42 | 38 | Not an attack cohort |

The joint table below uses the binary key **O0 O1 Y**. Its cells sum to each
original task count. Exact availability and terminal-failure identities passed.

| Joint key | MMLU-Pro | MuSR | MATH-500 |
|---|---:|---:|---:|
| 000 | 70 | 28 | 18 |
| 001 | 0 | 0 | 6 |
| 010 | 4 | 0 | 1 |
| 011 | 5 | 0 | 1 |
| 100 | 11 | 5 | 2 |
| 101 | 0 | 0 | 0 |
| 110 | 12 | 11 | 2 |
| 111 | 38 | 46 | 70 |

MMLU's 61−43=18 coverage/accuracy gap is **not** its initially covered failure
count (23): five initially uncovered tasks become final successes. MuSR has 16
initially covered failures, of which five lose all revised correct answers and
11 retain a correct revised answer but fail readout. MATH's final accuracy can
exceed initial coverage through construction. None of these observations proves
that correct rationales were ignored or that surviving rationales were sound.

Old QLM synthesis→debate paired gains/losses are MMLU 5/2, MuSR 2/1 and MATH 0/4.
Old debate→task-only gains/losses are respectively 11/19, 14/8 and 5/8. These are
different protocols under the old budget; the new matched 512-token modes have
not been executed.

The private human-review pack contains at most eight revised-readout-loss and
eight revised-covered-success tasks per primary dataset, fixed hash order, no
replacement. All annotation fields remain `not_reviewed`. The pack contains real
benchmark material and must stay outside Git. It cannot filter the new cohort.

## Frozen new scope

Import reconstructed all 230 primary tasks and exactly 80 eligible attack tasks
(42 MMLU / 38 MuSR), preserving original QLM/QQQ bindings. Six new clean modes
are implemented for each of two pristine non-thinking Qwen3 judges. The new
512-output/8192-context profile is explicit, not a repair of old results.

One fixed wrong candidate per eligible task is targeted only in its justification.
Five one-attempt styles include a separate ordinary-rephrase control. The entire
pool must freeze before six victim configurations run. Correct packets, answer
coverage and rationale-blind requests remain identical by construction. Partial
results, rejected variants and unsafe dispatches cannot become robust successes.

Maximum new calls: 2,760 clean + 400 rewrites + 2,400 attacked victims = 5,560;
maximum reserved output tokens: 2,846,720. Smoke is included. No new actor,
revision, replay, NLL or training calls are authorized. GPQA B, MBPP, LiveBench,
locked cohorts and prior incomplete runs are unchanged.

## Artifacts and reproducibility

Local private offline run:
`/var/tmp/pact-adjudication-reviewed-20261011/pact-adjudication-diagnostic-001`.
It includes selected parent output evidence, receipts, bank, frozen eligibility,
joint/format maps, review forms, a development plan and a zero-new-call report.
Its dirty local source identity is an implementation audit, **not** the future
pushed Colab plan. Import and plan afresh in the reviewed pinned checkout.

Offline export pair (no new neural results):

- PRIVATE: `pact-adjudication-diagnostic-001-PRIVATE-1791708425981179549.zip`,
  SHA256 `4e09b2b3d6d3e44f2f4c805667a21ea068dc4af920e81a167bd90d8f69c60904`.
- SANITIZED: `pact-adjudication-diagnostic-001-SANITIZED-1791708425981179549.zip`,
  SHA256 `cc36107376d5be8a13dc78f6d88cfa7157e1e7f35c47085c09650dc58432d2b2`.

Both are under `/var/tmp/pact-adjudication-reviewed-20261011/bundles`. The public report
contains aggregates and hashes only. Private source text, raw continuations and
decodable token arrays were not added to Git.

The [methodology](../adjudication_methodology.md) specifies contracts and limits;
[the complete Colab cells](../adjudication_colab.md) give actual stage commands and
checkpoint/bundle prerequisites. No adapters are needed. Official immutable model
weights are restored and byte-verified only during explicit Colab inference.

## Interpretation and remaining evidence

Implemented paths include real native inference, typed candidate views, strict
selection/free response parsing, bounded rewrite generation, victim execution,
paired metrics, guarded resume, compact durable snapshots and private/sanitized
exports. CPU/mock validation exercises these paths with fictional responses; it
cannot establish real neural behavior, capacity, latency, 14B memory fit or attack
strength. The returned GPU evidence is still required.

No new trained defense, AgentAuditor/ACPO or JudgeDeceiver reproduction, adaptive
security, full-PACT gain, semantic rationale verification or untouched final-test
performance is claimed. All paper placeholders remain unfilled.

## Executed software validation

The final complete CPU/mock suite ran **296 tests: 279 passed, 17 optional skips,
zero failures/errors** in 499.514 seconds. The final focused adjudication suite
ran **31 tests, all passed**. Tests cover complete zero-effect and attack-effect
round trips, rejected/missing variants, empty/no-support cases, exact caps and
included smoke, inference-only model isolation, strict schemas, role-delimiter
escaping, paired statistics, unsafe recovery, real CLI and private export guards.
No GPU or pretrained neural test was enabled.

The real-data zero-call PRIVATE export was restored with the final reader and its
report reproduced exactly. SANITIZED was scanned against original task IDs,
questions and token-array field names with no leakage found. There are 230
primary tasks, 80 eligible tasks and 32 private unreviewed review records.
The 18 notebook code cells compile with empty outputs; local links, supplied-design
budget equality and repository whitespace checks pass.

An initial full test run used `/tmp`, which is a Git checkout in this environment;
two existing GPQA fixture-path guards correctly rejected it. The guards were not
weakened. The successful suite used `/var/tmp/pact-adjudication-cpu-tests` instead.
Intermediate superseded runs are not final pass evidence. Logs are
`/tmp/pact-adjudication-verified-suite.log` and
`/tmp/pact-adjudication-verified-focused.log`.
