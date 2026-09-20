# Bounded actor preparation implementation — 2026-09-21

The frozen [120-task design](../actor_preparation_design.md) now has separate
training and probe stages, a default plan-only CLI and a
[seven-cell Colab procedure](../actor_preparation_colab.md). This is implementation
and CPU evidence. No new model download, GPU update, generated answer or scientific
result was produced locally.

## Preserved experiment

The tracked 120-task selection, config, training order/recipe and both old probe
inventories remain unchanged. Selection hash:
`57fb394c7aee9be6569fd12c48819bec9f06086d5cc022ee65510c7fa30a15fe`;
config hash `ec1ba60de4b4a904e278282b5e34dd79803110fa0ee4079bf6757e74aec15dc5`;
training recipe hash
`84e1ba5ad529023796f2f3d5bee8cf057bc38f4059b313476aaeb2013ca9ded5`.
The executable plan additionally retains the old receiver token prefixes so the
new checkpoint must receive exactly the old rendered and tokenized inputs.
That sidecar and execution-status metadata change the whole plan identity;
they do not change selected tasks, prompts, seeds, training settings or budgets.

A dedicated immutable training config fixes 30 steps per agent, batch four and
one complete pass through 120 tasks. The existing engineering config still
rejects more than 16 steps per agent and more than 32 tasks. The shared neural
engine retains the same initialization, losses, optimization, checkpoint/RNG
resume, frozen-backbone/inactive-adapter checks and exact reference export checks.
New runtime/base/template guards run before updates; all examples tokenize before
adapter training, with whole-example overflow rejection.

The new path records each attempted training example before its forward and
marks completion after backward. Receipts report attempts and sequence tokens
across invocations, separately from optimizer progress. If interruption forces
recomputation of an uncommitted microbatch, those attempts remain accounted;
only the compatible optimizer checkpoint determines which of the fixed 90 updates
remain. Generation and reference-scoring counts during training are zero.

## Persistence and final-checkpoint gate

Every optimizer boundary retains an immutable local checkpoint. A callback
verifies a durable snapshot every ten updates; final/handled-stop handoffs create
a local review ZIP before timed Drive operations. Training invocation receipts
include elapsed time and attempted-example accounting. A storage timeout stops
the invocation with local recovery artifacts; the final checkpoint is not silently
substituted or selected by probe accuracy.

Training checkpoints retain optimizer/RNG state and tensor payloads. Full storage
for 90 steps and new-example GPU lengths/time remain unmeasured. The existing
20-GiB restore limit and per-operation 120-second deadline are unchanged. The
metadata review ZIP cannot resume training by itself.

Before probing, require the same full design, clean published source identity
on Colab, complete 90-step log matching every task/order, final checkpoint, and
three final reference exports. Tensor/config hashes and architecture are verified.
The new reference checker explicitly expects step 90; old consumers still default
to step nine. A full verified training snapshot is made before fresh inference.
Partial training and mismatched code/data/runtime cannot enter the probe.

## Fixed probe and reporting

The probe uses the established intent/result journal with a 104-call / 26,624
reserved-output-token cap. All 72 private and eight receiver prompts preflight
against the old saved text/token prefixes before sampling. The new actor hash is
the intentional checkpoint change. The other runtime/template/sampling settings
remain fixed; labels and arm/evaluation annotations stay outside model messages.

The first 72 calls regenerate the old private requests. The following 32 calls
use the old private histories/donors, not those newly sampled private responses.
Both probes run irrespective of intermediate correctness. There is no readout,
reference scoring, donor generation, adaptive expansion or optimizer activity.

Reports reuse separate-draw private accounting and exact within-arm receiver
pair rules, plus per-sample old/new checkpoint comparisons. Old completions are
comparison data only; they never supply a negative or positive to a new-checkpoint
pool. Invalid/abstaining outputs remain failures. Partial reports retain missing
counts. No training pairs are exported and full PACT readiness stays false.

A verified unsafe snapshot precedes new inference, with safe checkpoints every
eight committed calls and at handled stops/completion. Resume rejects unresolved
attempts or changed source/recipe/model identity. Restore accepts only the latest
safe probe snapshot. Completed repeats make no new generation calls. The earlier
training and curated artifacts are preserved.

## Local evidence and next action

Six new CPU tests cover strict new/old training bounds and frozen orders;
failed-training local export and incompatible resume; synthetic optimizer-boundary
pause/restore/final gate and exact 90-step schedule; 74-call pause/resume through
104 calls, immutable outputs, no scoring and zero-call repeats; verified restore
and stale-snapshot rejection; exact old-context preflight, ambiguous-call rejection,
and nonexecuting CLI. Synthetic orchestration is not neural-training verification.

Full default suite: **135 passed, six optional neural tests skipped (141 total)**.
The optional tiny neural environment is unavailable; its historical results were
not rerun. The shared neural engine's new GPU path and attempted-forward logging
require returned evidence. Actual source plan reconstruction, unchanged frozen
hashes/budgets, all seven Colab cells and documentation links are checked locally.
Evidence: `results_import/actor-preparation-implementation-001/`.

Next: user review/commit/push, then pin that new SHA in the Colab guide. Return
both stage ZIPs, checksums and final receipts. No GPU or final-test execution,
commit, push or manuscript result update was performed by this implementation.
