# Bounded actor preparation — design v1, 2026-09-20

The next increment is one **120-task clean-answer warm start**, followed by two
fixed training-only probes. This changes actor preparation rather than extending
completed sampling runs. The offline planner and bounded training/probe runner are **implemented and CPU
tested; GPU unverified**. See the [implementation review](reviews/actor-preparation-implementation-001.md)
and [Colab cells](actor_preparation_colab.md). The experiment below remains frozen.

Proposed runs: `qwen3-preparation-120-001` (training) and
`qwen3-preparation-probe-001` (104 generation calls). These are engineering
diagnostics, not full PACT training, held-out evaluation or a hyperparameter sweep.

## Question and rationale

The nine-step warm start was designed to verify training mechanics on twelve
examples, not to prepare specialized actors. The broader receiver screen found
zero within-prompt pairs, the second private draw found no mixed teams, and the
[completed curated check](reviews/qwen3-curated-repair-001.md) showed correction
on one task but still no pairs. Repeating its seeds or enlarging its sampling cap
would extend a closed diagnostic without addressing the actor preparation limit.

Ask whether a single, moderately larger clean-answer preparation changes private
competence/agreement and receiver behavior on the already frozen probes. Increasing
supervision could improve accuracy, increase agreement, damage revision behavior
or change nothing. It is not assumed to solve pair scarcity. Retain the existing
answer-only training target so that a new revision target or fabricated rationale
does not become an additional intervention. The train/inference format difference
(answer-only supervision versus answer-and-justification inference) remains a
limitation, not something this experiment resolves.

This is a comparison of two preparation recipes: twelve versus 120 tasks and
nine versus 90 total updates, with changed shuffled orders. It cannot separately
attribute differences to task count, data content or optimization duration.
A matched-step or revised-target control would be a separately budgeted design.

## Frozen training selection

Source: the already audited 1,200-task training pool, manifest
`92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a`.
Retain all twelve original warm-start tasks, manifest
`2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e`.
Exclude all 24 broader-probe task IDs, audited component IDs and content-group
IDs before selecting additions. No probe labels, accuracy or donor availability
rank training candidates.

For each family retain the original six tasks, then add the first 54 eligible
pool entries ordered by `digest([20260920, "actor-preparation-120", group_id])`,
with task ID as tie-breaker. Store the resulting 120 entries sorted by task ID.
Reject insufficient support, duplicate groups, changed inputs or inconsistent
source manifests; never replace a selected example after observing its length,
loss or probe result. The set is exactly 60 ARC and 60 original English LogiQA.

The [tracked selection](../experiments/actor_preparation_selection.json) records
IDs and input/label/group hashes. Selection hash:
`57fb394c7aee9be6569fd12c48819bec9f06086d5cc022ee65510c7fa30a15fe`.
Config hash:
`ec1ba60de4b4a904e278282b5e34dd79803110fa0ee4079bf6757e74aec15dc5`.
The inherited exact/lexical validation-overlap screen remains in force. Semantic
paraphrase separation and final-test overlap are unverified. The reused probes
are excluded from new optimization but were repeatedly inspected during design;
they are development probes from the training split, not untouched validation.

## Training recipe and bounds

Create fresh adapters on the same pinned Qwen3-8B base, using original initialization
seeds 1729/1730/1731 and the existing adapter-init seed derivation. Do not continue
the old trained adapters or import their optimizer state. Keep rank 16, alpha 32,
q_proj/v_proj modules, dropout zero, BF16 backbone, FP32 LoRA parameters, SDPA and
thinking disabled. Frozen base/tokenizer/runtime identities match the old run;
new actor/reference hashes must be recorded after all updates.

Each agent sees all 120 tasks exactly once, ordered by `digest([agent_seed,
task_id])` with task-ID tie-breaker, as in the existing engineering planner.
Microbatch one, effective batch four, 30 optimizer steps per agent: **360 example
presentations and 90 optimizer steps total**. AdamW, learning rate 1e-5, betas
(0.9, 0.999), epsilon 1e-8, foreach=False, weight decay zero, gradient norm cap one,
constant learning rate and no scheduler. Target: canonical answer-only JSON plus
EOS; mean completion-token NLL, matching the existing warm start.

Tokenize every selected training example with the pinned tokenizer before the
first update. Require prompt plus complete target within 4,096 tokens; fail the
fixed recipe on overflow rather than truncate or drop tasks. The conservative
sequence-token presentation ceiling is **1,474,560** (=360×4096), not a prediction
of actual tokens or a training FLOP estimate. Count all training forwards and
backwards separately from generation; there are no reference-scoring forwards.
GPU duration and 120-example length profile remain unmeasured.

Only one adapter is trainable at a time. Verify backbone and inactive-adapter
invariance. Store optimizer/RNG state at update boundaries and retain the final
three immutable reference exports. Resume only the same source, data, recipe,
model/runtime and checkpoint identities, counting already completed updates.
Do not generate probes until all 90 steps and durable reference exports verify.
Use the final checkpoint only—no best-checkpoint selection from probe outcomes,
early stopping on accuracy, extra epoch, alternative seed or learning-rate retry.
An execution failure closes the invocation as incomplete; compatible recovery
may finish only its original budget.

## Fixed post-training probes

Run both complete probes, regardless of the first one's outcomes, with frozen
new actors. No optimizer update can occur between or during probes.

| Probe | Fixed inputs and seeds | New calls | Existing comparison |
|---|---|---:|---|
| Private | Same 24 tasks, three agents; seed-1730 private requests | 72 | Completed private-support control |
| Receiver | Same eight curated/original contexts, recipients and four seeds each | 32 | Completed curated helpful-peer diagnostic |

Use temperature 0.7, top-p 0.8, top-k 20 and a 256-token output cap, context 4,096.
**104 calls maximum; 26,624 reserved output tokens; 399,360 theoretical input
tokens.** No final readout, new donor generation, attack search, suffix replay,
reference scoring, data-driven receiver expansion or optimizer step is permitted
in the probe stage. Invalid/abstaining/truncated samples remain failures; none is
replaced with a fresh draw.

Private request inventory hash:
`98e749e8b4d2c3fe20f8a3643af7fc8e362febff4a4ae7dae1450cbbf5333571`.
Receiver context hash:
`66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab`.
These pin old task/messages/seeds, not the old actor identity: the new frozen
checkpoint is the intended intervention. Preflight all actual probe prompts and
compare their serialized text, token prefixes and decoding parameters to the
old artifacts. Reject runtime/template differences; do not silently substitute
a different GPU configuration or quantized model.

The receiver probe intentionally retains the **old** complete private states and
old same-task donors. Do not feed the newly sampled private packets into those
contexts. This isolates receiver-policy changes at fixed history; it does not
measure a natural team rollout under the new actors. Only the matched recipient
adapter changes. Its curated repair designation refers to the stored old wrong
private state, not a new private response. Neither checkpoint supplies candidate
completions to the other's preference pools.

Required engineering: separate attempted-call journal; local ZIP before timed
Drive writes; verified unsafe marker before fresh calls, latest safe snapshot
restore, no automatic regeneration of unresolved intents; immutable prefixes,
requests and outputs. Preserve both old runs and new stage identities. Do not
resume this run into an old bank or overwrite old references.

## Reports and decisions fixed before new outcomes

Private: report paired answer/correctness transitions, per-agent/family counts,
all-correct/mixed/all-wrong teams, unanimity and potential clean-repair contexts
for complete triples. Baseline is 45/72 correct answers, 15/24 all-correct teams,
nine all-wrong, no mixed teams and no potential clean-repair contexts. Increased
agreement is not complementarity; lower individual accuracy is not a desirable
route to more mixed teams. Show accuracy and support together.

Receiver: retain per-sample raw text/tokens and failure categories. Report paired
old/new outcomes under each identical prompt/seed, plus original-versus-curated
comparisons **within the new checkpoint**. Baseline original peers yield zero
correct/eight wrong/eight abstentions; curated help yields eight correct/eight
wrong. Report both tasks and all four recipients, rather than only an aggregate.

Within each new four-sample exact-prompt pool, require valid-correct and valid-wrong
outputs for a diagnostic preference pair. Keep the existing 32-token-bin matching
rule. Never pair across arms, seeds from different prompt pools, or checkpoints.
Abstentions/invalid text are failures, not default negative counterparts. Report
all missing classes and incomplete pools. Export no preference training pairs.

| Outcome | Decision |
|---|---|
| Better private accuracy, unchanged/no pair support | Larger clean preparation helps this development probe; revision pair scarcity remains |
| More mixed private teams or new within-prompt pairs | Local support change; assess accompanying accuracy, family and task coverage before a separate collection design |
| New pairs appear with lower private accuracy | No readiness promotion based on diversity/pairs alone; record the competence tradeoff |
| Receiver behavior changes but private support does not | Fixed-history receiver-policy sensitivity; not evidence of natural-team benefit |
| No useful change, worse outcomes, or more agreement | Close the bounded preparation check; no automatic larger warm start or seed search |
| Incomplete training/probe or identity/context mismatch | Incomplete; no efficacy or absence-of-effect conclusion |

All complete outcomes end this experiment. No outcome automatically unlocks PACT
training, additional sampling or a larger grid. `full_pact_ready=false` throughout:
there are no new hold contexts, only two post-selected ARC receiver tasks, and no
LogiQA receiver or terminal evaluation. Reused development probes and one training
seed per agent cannot establish generalization, statistical superiority, or
training-seed stability. Final-test data and manuscript result placeholders remain
untouched.

## Reproduce the offline plan

```bash
python -m pact plan-actor-preparation \
  --config experiments/actor_preparation_120.json \
  --data-dir results_import/training-data-001/proposal-1200 \
  --warmstart-data-dir results_import/training-data-001/engineering-12 \
  --receiver-bundle results_import/qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip \
  --private-bundle results_import/qwen3-private-support-control-001-handoff-1789909726537323854.zip \
  --curated-bundle results_import/qwen3-curated-repair-001-handoff-1789919214853319498.zip
```

The command is plan-only and has no `--execute` option. It verifies source
manifests/archives, reconstructs the prior context and request inventories, freezes
training orders and reports the budget. It loads no model and writes no training
run. Local evidence is retained at `results_import/actor-preparation-design-001/`.

The existing `warmstart` runner still caps engineering data at 32 tasks and steps
per agent at 16. The separate `actor-preparation` command now implements the
120-task recipe with explicit training/probe stages and default planning mode.
CPU recovery and handoff checks pass; actual larger GPU training, new-example
context fit, storage profile and GPU reset/resume remain unverified. User review
and publication precede the pinned Colab run. Do not enlarge the old engineering
JSON or reuse a completed old run directory.
