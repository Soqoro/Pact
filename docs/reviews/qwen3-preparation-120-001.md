# Completed 120-task actor preparation and fixed probe review

The imported training and probe metadata pass the CPU audit. The larger clean-answer
preparation completed, but the fixed probe does not show improved receiver correctness
or usable within-context preference pairs. `full_pact_ready` remains false. This is a
training-only feasibility result, not final-test or generalization evidence.

## Evidence and verification

- Training: `qwen3-preparation-120-001-handoff-1789930640697369191.zip`, SHA256
  `a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388`.
- Probe: `qwen3-preparation-probe-001-handoff-1789972354005267043.zip`, SHA256
  `ae6a0268d66af76319f5206f04fbb070f34e5283bdde4efe5c344ec70256528f`.
- Reproducible audit: `results_import/qwen3-preparation-120-001-analysis/audit.py`;
  outputs: `metrics.json`, `recomputed_report.json`, `verification.json`, `audit.log`.
  Run with `PYTHONPATH=src python results_import/qwen3-preparation-120-001-analysis/audit.py`.

The audit validates both ZIP hashes, every included payload checksum and inventory
entry, and reconstructs the frozen design from local pinned data and prior bundles.
It checks training configuration, source, task orders, example hash, all 91 checkpoint
metadata records (initial plus 90 updates), and 360 completed example presentations.
The final reference manifest reconstructs exactly the probe plan and model identities.
All 104 calls replay from the stored journal without a model, and the recomputed report
matches the imported report exactly, including prompts, token prefixes, seeds and accounting.

These are review archives, not tensor backups. The training inventory includes 94
omitted tensor files (91 optimizer checkpoints and three adapters), plus an omitted
reference README. Their recorded hashes are checked for internal consistency; their
actual bytes were not independently verified locally. They remain in the full Drive
snapshot. The handoff receipts report verified persistence; this audit does not inspect
current Drive contents or independently reproduce neural/tokenizer execution.

## Execution

Training used the fixed 120 tasks, 60 ARC Challenge and 60 LogiQA, with one pass per
agent: 30 updates each, 90 total, batch four, 360 completed forward/backward example
presentations and 73,974 sequence tokens. The training stage performed no generation
or reference-scoring calls. Its recorded invocation duration was 990.5 seconds.

The first probe invocation actually completed all 104 calls in 540.6 seconds. The
later recovery invocation took 121.7 seconds and used 104 cache hits with zero new
calls. The recorded source migration from `ff349969996b2066979529b2f43d773f5a1b88e6`
to `6364c52906c190890e7c1cce580951d3a3cb8fdd` retained all 104 committed calls.
There were zero unresolved attempts, 29,147 input tokens and 5,770 output tokens.
Neither probe invocation trained or performed teacher-forced reference scoring.
The recovery receipt points to the compact inference snapshot; it provides evidence
of completed-run recovery, not an interrupted-generation or optimizer-resume test.

## Results

| Fixed probe measure | Previous actors | Prepared actors |
|---|---:|---:|
| Correct private responses (matched seed 1730) | 45/72 | 45/72 |
| Tasks with all three agents correct | 15/24 | 15/24 |
| Tasks with at least one correct agent | 15/24 | 15/24 |
| Potential clean-repair contexts | 0 | 0 |
| Correct receiver responses, original peers | 0/16 | 0/16 |
| Correct receiver responses, curated help | 8/16 | 8/16 |
| Eligible within-arm preference pairs | 0 | 0 |

The matched-seed private comparison has 45 correct-to-correct and 27 wrong-to-wrong
responses; 71 answers are identical and one wrong answer changes to another wrong answer.
An audit correction is necessary: the imported report compares against the older seed-1729
trajectory (46/72), not the design’s seed-1730 private control (45/72). Its previously
reported 46-to-45 change is cross-seed and cannot isolate preparation. The corrected
comparison uses the completed private-control ZIP, verifies identical seeds, messages
and token prefixes, and leaves the imported report untouched. Evidence:
`results_import/preparation-objective-review-001/matched_seed_comparison.json`. Receiver comparisons had eight correct-to-correct,
16 wrong-to-wrong, seven abstention-to-abstention and one abstention-to-wrong transition.
Thus receiver correctness did not change; reduced abstention here was not an improvement.

Curated help still yields eight correct responses on `arc_challenge:Mercury_7210613`
and none on `arc_challenge:Mercury_406916`. Original-peer contexts yield none on either.
The eight-response difference between arms is unchanged from the previous checkpoint.
It is not evidence that the larger preparation helped, and cross-arm responses cannot
be relabeled as within-context preference pairs. Curated repair pairs also remain zero.

## Decision and limits

Close this bounded run as completed. Do not rerun its training/probe or expand the
same recipe into a sweep on the strength of these results. Review the actor objective
and the absence of useful within-context variation before specifying another bounded
experiment; no next GPU run or methodology change is authorized by this audit.

The 72 private draws cover 24 fixed training tasks. Receiver evidence covers only two
post-selected ARC tasks, with repeated samples on old saved receiver histories and
donors; new private outputs do not enter those histories. This does not establish hold
behavior, natural-team repair, LogiQA receiver behavior, terminal efficacy or generalization.
No training pairs were exported and no final-test data were used.
