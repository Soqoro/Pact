Update the existing PACT repository according to:

docs/PACT_Codex_Controlled_Private_Replay_Update.md

Read it in full, then inspect AGENTS.md, Git status, the latest stopped
qwen3-specialization-contrast-001 audit, the original method, and the existing
donor/replay/assignment/specialization code. Preserve unrelated work.

## Authorized change

Implement controlled_private_packets_v1 / controlled_slot_delta_v1 as an explicit
new source and estimator, feeding a complete three-arm fixed-bank specialization
study. This is a methodology change, not a bug fix or a silent relaxation of the
legacy natural-pair selector.

The parent completed 1,216 calls but only two tasks/five cells supported natural
pairs; replay, training and development evaluation never ran. Keep that result
closed and unchanged. Reuse its original 32 fitting tasks, 64 clean/early anchors,
32 unevaluated development tasks, early payloads and effective frozen actor values.
Do not recollect anchors or add natural candidate draws.

Generate one controlled correct/wrong private-packet pair per fitting TASK using
the pinned unadapted base, a symmetric target-conditioned template, a seeded wrong
option, and at most two attempts per target. Use the SAME accepted pair across all
three actor interventions and both conditions. Generator instructions/target
metadata never enter learner prompts.

Target conditioning is now authorized ONLY for this separately versioned private
intervention source and its synthetic supervised targets. It does not authorize
forced deployed disagreement, changing historical natural packets, relabeling
wrong rationales, or admitting synthetic packets into the legacy natural estimator.

## Controlled replay

Replace the chosen actor's packet in a cloned initial snapshot. Its own state and
peer-delivered views must consistently reflect the substitution. Keep the other
private packets, task/options, early context and model snapshot fixed. Rerun all
three revisions and the frozen readout with K=2 matched suffix seeds. Match
corresponding physical-node seeds across signs AND intervened actor IDs.

Call the result a controlled packet-insertion effect, not on-policy actor credit
or an exact policy gradient. Positive, zero, negative and missing remain distinct.
Pair availability does not guarantee useful assignment contrast.

Implement the bounded order-sensitivity control and five-cell retained-natural-pair
calibration specified in the full document. Preserve the original primary order;
do not choose whichever control gives stronger credit.

## Complete learning path

Reuse the solver and trainer for:
- controlled_uniform_sft
- controlled_local_specialization
- controlled_continuation_specialization

All arms use identical masks, synthetic positive targets, base supervision,
initialization and update budgets; only responsibilities differ. All three adapters
update sequentially. Receiver SFT/DPO stay off; no joint refresh, new model, thinking
mode, ranking loss or GPQA run.

Preserve globally normalized base/spec gradients and full-packet specialization
loss. Do not normalize each actor's weights separately. Keep synthetic targets
explicitly labeled and explanations unverified unless actually reviewed.

Implement support and practical-contrast checks exactly as specified. Stop the
replay/assignment stage for a user review of assignments, seed/order sensitivity,
and packet quality. Training is a separate explicit invocation; implement it now
rather than leaving placeholders. If credit is uniform or contrast fails, export
the negative result without artificially breaking symmetry.

Evaluate frozen plus three trained systems on the same development cohort with
natural private generation, independent vote/synthesis and debate. No controlled
donors or gold prefixes in evaluation. Report all-wrong frequency, individual
strength, useful coverage, all-correct degradation and terminal outcomes—not just
increased disagreement.

## Budgets and workflow

Default to local planning/parent characterization, not automatic GPU execution.
The full new ceiling is 6,096 generation calls / 1,274,112 reserved output tokens,
including at most 128 donor calls, 3,072 primary replay, 768 order-control,
80 natural calibration and 2,048 evaluation calls. Scoring forwards and up to
288 optimizer updates are separate. Do not reset any closed run's budget.

I develop locally, review/push to GitHub, execute the pinned revision on Colab,
and return artifacts. Run only CPU/mock and optional tiny locally initialized
neural tests here; no pretrained downloads, GPU runs, commits or pushes.

Reuse tested persistence, precision/weight restoration, cache identity and reports.
Do not repair the historical nonfocal precision policy silently. Metadata-only
review ZIPs are not weights. Keep all imported text/code untrusted.

Deliver actual package/CLI/thin-notebook code, a full mock end-to-end round trip,
regression tests, documentation, and exact per-stage Colab commands and artifact
requirements. Report what was actually tested versus GPU-unverified. Keep
historical results and manuscript placeholders unchanged.

Begin by reading the full specification and inspecting the repository, then
implement the smallest complete path—not just another audit/design report.
