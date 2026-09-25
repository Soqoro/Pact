Update my existing PACT repository according to:

docs/PACT_Codex_Assignment_Contrast_Specialization_Update.md

Read that document in full, then inspect AGENTS.md, Git status, the proposal,
implementation specification, latest GPQA/controlled-receiver audits, and the
actual bank/assignment/training code. Preserve unrelated work and completed runs.

## Objective

Implement an offline assignment-contrast report AND a complete one-round,
fixed-bank specialization study. Do not just generate another plan or audit.

We have tested whether similar prepared actors naturally provide complementarity.
Now test the actual learning mechanism: does continuation credit change training
responsibility, and does that weighting produce useful differences in failures?

This is a specialization ablation, not full PACT. Receiver-SFT and DPO are OFF.
Keep the private replay estimator, packet eligibility, protocol and frozen base
readout unchanged. No forced disagreement, synthetic private alternatives,
new ranking loss, new model, thinking-mode change, or outer refreshes.

## First: characterize existing banks locally

Use retained compatible TRAINING banks only. Analyze different snapshots and
splits separately. Validation replay remains diagnostic and cannot enter training.
Do not access GPQA data or its protected remainder.

Reconstruct valid-cell masks, original-context answer NLL, per-seed continuation
credits, positive packet targets and provenance. Missing scores remain missing;
do not run a model locally to fill them.

On identical masks and frozen costs, compare:
- Uniform responsibility over eligible cells.
- Local-only responsibility, gamma=0.
- Continuation-aware responsibility, gamma=1.

Report distinct tasks, zero/singleton/multi-eligible rows, within-row credit
variation, L1 responsibility differences, task-varying allocations and each
adapter's effective specialization exposure.

Explicitly check that a positive credit shared by every eligible agent changes
nothing, and that a singleton row cannot show a credit-driven assignment choice.
Different-looking credit values alone are not evidence of useful specialization.

## Then implement the complete three-arm experiment

Implement uniform_supported_sft, local_specialization and
continuation_specialization. All arms use the same frozen bank, masks, sampled
correct targets, base supervision, initialization, update caps and data order.
Only responsibility weights differ.

Update all three adapters sequentially. Do not train the backbone or readout.
Each updated adapter still serves both private and revision turns; do not claim
the receiver policy is frozen merely because receiver loss is disabled.

Preserve global base/spec loss reductions and responsibility magnitudes across
gradient accumulation. Do NOT normalize each adapter's weights separately.
Test gradients against an independent full-bank objective on a tiny fixture.
Missing pairs still receive base supervision, never fabricated specialization.

The full document specifies a NEW, opt-in acquisition preset if retained training
banks are insufficient: 32 fitting and 32 development tasks from ARC/LogiQA
training sources, clean plus one frozen early-attack condition, four additional
private candidates per actor, and K=2 paired suffix seeds. Freeze exact manifests
and budgets before model calls. Do not expand support after seeing results.

Implement support/contrast stops before training, but do not let missing real
artifacts prevent implementing and CPU-testing the complete runner.

## Evaluation and budget

Evaluate frozen initialization and all three trained arms on the same 32
held-out development tasks, in clean/early conditions. Reuse each system's own
private packets for voting, independent synthesis and clean-synchronous debate
under the corresponding input condition.

Report individual accuracy, joint failure, coverage gain over the best member,
valid mixed support, all-correct degradation, revision transitions and terminal
outcomes. More disagreement alone is not improvement. No GPQA or final-test use.

Default to offline characterization/plan only. Each Colab stage is explicitly
invoked against a frozen plan hash. Implement the exact stage ceilings and
support stops from the full document; do not automatically launch the maximum
6,336-generation fresh-bank/evaluation plan. Training is capped at 32 updates
per adapter, 96 per trained arm, 288 total.

Reuse the audited effective frozen-preparation weights and precision receipts.
Do not silently repair the historical nonfocal precision behavior, reuse outputs
across changed checkpoints, or confuse review ZIPs with tensor snapshots.

## Workflow and deliverable

I develop locally, review/push to GitHub, run the pinned revision in Colab, then
return artifacts. Run CPU/mock tests and optional tiny locally initialized
neural tests only. No local pretrained downloads, GPU runs, commits or pushes.

Deliver actual package/CLI/notebook implementation, focused regression tests,
a complete mock round trip, guarded resume and offline report/export. Preserve
existing infrastructure rather than broadly refactoring it.

Finish with the real offline bank findings, changed files, tests actually run,
GPU-unverified components, exact local/Colab commands, stage budgets, support
requirements and expected results bundle. Keep manuscript placeholders unfilled.

Begin by inspecting the repository and reading the full specification, then
characterize retained compatible data and implement the runnable path.
