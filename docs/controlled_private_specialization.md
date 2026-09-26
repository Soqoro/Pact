# Controlled private replay and fixed-bank specialization v1

This implements [the authorized update](PACT_Codex_Controlled_Private_Replay_Update.md).
It is a new child study, `qwen3-controlled-specialization-001`, not a repair or
continuation of the stopped parent's natural-pair experiment. There are no new GPU
results. The 1,216 parent calls and its failed support gate remain unchanged.

## Parent evidence and import

The pinned parent ZIP SHA256 is
`555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f`;
its plan is `99ff21066f93f26fae33e6cbf70623313b0f9acd09e9e6d49e0702674af5131c`.
Import checks the archive, reconstructs the original collection/selector, checks
five natural cells on two tasks, verifies zero subsequent stages, and retains a
metadata copy for offline auditing. Real weights are required separately.
The child keeps all original tasks/options, 64 natural anchors, 32 unevaluated
development groups, clean/early payloads and effective actor identities.
A recorded later-use review is required: any reported development optimization or
outcome selection stops planning rather than replacing tasks. Such an attestation
cannot discover unrecorded external experiments.

Local reconstruction of the real parent (no model): 768 additional candidates,
361 valid-correct, 405 valid-wrong and two length-limited outputs; selector outcomes
100 missing-correct, 87 missing-incorrect and five eligible cells. These are
candidate/cell counts, not initial-team coverage or performance estimates.

## Source and estimand

`controlled_private_packets_v1` uses the existing symmetric donor template and
validator, plus a versioned construction-metadata rejection rule. One wrong option
is selected before generation with `node_seed(parent_seed, SOURCE, task_id,
'wrong-option')`. At most two attempts per positive/negative target; first valid
wins. All attempts are journaled. The generator is the pinned base with adapters
physically disabled, with adapter/gradient/mode restoration even on exceptions.
It sees only trusted task/options and the requested option. Neither actor IDs,
original packets, early material nor desired credits enter its messages.

The same accepted raw pair and terminal token IDs serve all three actor slots and
both conditions. Length-bin matching is diagnostic only. Structural/answer
acceptance never certifies a rationale. Eight fitting review IDs (four per family)
are frozen before generation; unsupported examples are retained, not replaced.

`controlled_slot_delta_v1` clones the original initial tuple, replaces actor i's
own packet and the delivered views derived from it, then runs all three revisions
and frozen readout. All other source packets/attack bytes remain unchanged.
The packet object's generator call remains provenance; only its packet text is
rendered into defender own/peer views. Original actor prompts are retained for
scoring/training, never generator prompts.

Suffix seeds are `node_seed(parent_seed, ESTIMATOR, task_id, condition, 'suffix', k)`.
Protocol physical revision/final node seeds derive from this seed; neither sign,
intervention actor, display variant nor branch lengths enter seed derivation.
Cache keys additionally include the full branch/source/estimator/anchor/pair,
physical intervention actor, display order, complete request and model identity.
Negative/zero effects remain valid; missing remains absent. This is a full-packet
insertion effect, including wording differences, not on-policy credit, an internal
belief intervention, COMA/Shapley credit or an exact policy gradient.

The legacy natural loader explicitly rejects controlled provenance. Its selector,
protocol defaults, replay estimator and historical results are unchanged.

## Fixed interpretation controls

Eight preselected fitting tasks receive reversed peer and readout list order.
Original shuffles are applied first, then their presentation lists are reversed;
source labels, actors, own states, payloads and physical node seeds are unchanged.
Primary credits always use original order. Order reports include raw/centered
changes, preferred-actor changes and full-bank responsibility movement, including
balance-mediated movement outside the controlled rows.

The five retained natural cells are separately replayed using their original
selected packet bytes and the same controlled suffix seeds. They never enter the
primary mask or select donors. A missing controlled pair gives a null matched
comparison. Five cells on two tasks cannot validate a population estimator.

## Assignment and training contract

Original answer targets are canonical answer JSON plus EOS, under the original
private prompt. Controlled specialization targets are the complete accepted
synthetic positive packet plus its terminal EOS, under that same original prompt.
Prompt tokens and padding are masked. Mean completion-token NLL is used for both;
there is no receiver answer-prefix substitution or duplicated auxiliary base loss.

Answer NLL is standardized once over eligible cells globally (population std,
scale one for zero variance), inherited explicitly from the parent specialization
variant. Local and credit use identical masks/transform; gamma=0/1, tau=.2,
balance=.1. Both single-seed diagnostics and the reversed-order replacement solve
keep the primary transform and masks. No per-agent or subset restandardization.

Arms: `controlled_uniform_sft`, `controlled_local_specialization`, and
`controlled_continuation_specialization`. All use identical positive targets,
base supervision, initialization, schedule and target exposure; only R differs.
For U=64 and B eligible rows:

```
L_base = sum_b,i answer_NLL[b,i] / (3*U)
L_spec = sum_b,i omega[b] * R[b,i] * packet_NLL[b,i] / B
L_total = L_base + L_spec
```

omega is inverse one plus NATURAL anchor correct count, normalized once over
eligible rows. The production trainer accumulates four one-row microbatches with
global coefficients multiplied by U/4=16. It never renormalizes an actor's mass.
All eligible forwards occur even at a numerical zero responsibility; missing
packets contribute no term. Base targets cover all 192 cells. Two passes yield
384 base presentations and at most384 packet presentations per arm (1,152 each
across three arms). Frozen scoring forwards are separate.

Reuse sequential FP32 LoRA updates over the frozen BF16 backbone: AdamW lr1e-5,
betas(.9,.999), eps1e-8, weight_decay0, foreach=False, clip1, no scheduler,
32 steps/actor,96/arm. Each arm reloads the exact historical effective team;
nonfocal FP32→BF16→FP32 history is preserved. Final evaluation loads the exact
completed checkpoint values, not a new lossy adapter conversion. Only active
adapters change; updated adapters serve BOTH private and revision turns.

## Gates, review and evaluation

Before replay: at least eight distinct fitting tasks with pair support and eight
with multi-eligible support. After complete replay/scoring: numerical contrast
>1e-6, task-average multi-row L1≥.10 and at least eight tasks each with mean L1≥.10.
Failure statuses are insufficient_controlled_support, no_assignment_contrast or
insufficient_practical_contrast; no symmetry-breaking fallback.

A pass is `ready_for_user_review`, not reliable credit. Training requires a
separate command and a review JSON bound to the plan and exact assignment,
packet-review, seed and order artifacts. It records reviewer/notes, the frozen
review IDs and an explicit decision. A declared systematic packet defect stops
GPU work; fixing it requires a new source version. Review means human inspection,
not certified reasoning. No automatic train/evaluate loop exists in the notebook.

Natural development evaluation uses frozen plus the three final trained teams,
32 original development tasks × clean/early × eight calls. No donors/gold prefixes
enter evaluation prompts. Reports include per-agent strength, coverage gain over
best member, joint failure/all-wrong frequency, N0→N1, all-correct degradation,
vote/synthesis/debate, erasure/utilization/construction/readout loss, tokens and
paired task-clustered comparisons. Thirty-two groups, not calls, are the units.
One training seed and boundary bootstrap intervals cannot establish equivalence.
A gain over frozen alone could be common synthetic-data distillation; credit must
be compared with both uniform and local. Full PACT and preservation remain open.

## Budgets and recovery

| New stage | Calls | Reserved output tokens |
|---|---:|---:|
| Acquisition |128|32,768|
| Primary replay |3,072|638,976|
| Order control |768|159,744|
| Natural calibration |80|16,640|
| Four-system evaluation |2,048|425,984|
| Total |6,096|1,274,112|

At most192 answer scores and192 packet scores; at most288 optimizer updates.
The parent's1,216 calls are imported evidence, not remaining/new budget. Journals
count dispatch intents, commitments, unresolved attempts and reservations; cache
reuse never resets budgets. Unknown calls/updates stop resume. Full latest-only
snapshots preserve optimizer/RNG/actor states; review ZIPs omit weights. Scratch
holds hot files and local exports precede bounded Drive copies. No data refresh,
new seed search, GPQA access, receiver/DPO loss or final-test execution.

Commands and prerequisites: [Colab runbook](controlled_private_colab.md).
GPU behavior remains unverified until an actual returned child bundle is audited.

## Exact fictional example

[tests/fixtures/controlled_private_v1.json](../tests/fixtures/controlled_private_v1.json)
contains both complete generator messages, all three receivers' branch messages,
physical-node seeds, original learner prompt, synthetic output and exact scored
mask using a fictional character tokenizer (EOS=0, not Qwen tokenization).
The positive/negative generator user messages differ only in support_option A/B.
For slot0 insertion, positive own text and both peer-1 views contain the same
positive packet; negative views contain the same negative packet. Generator
support_option instructions never appear in those receiver messages.

A separate eight-task fictional solver fixture has equal answer NLL and
prespecified varying slot effects. Its first row has uniform/local
[.333333,.333333,.333333] and credit [.985301,.006639,.008060]. These values illustrate
the existing solver; they are not measured credit, a desired scientific result,
or an assignment to real tasks. Global balance couples rows; do not infer a
softmax independently for each actor from this illustrative first row.

Validation at handoff:215 default tests (201 pass,14 optional skips), seven final
guard tests and three separately executed tiny CPU neural tests pass. The complete
mock round trip and actual-parent zero-model plan/export/import pass. Actual
training token counts and per-step optimizer timers are recorded separately from
planned exposure and persistence. Training-initialization receipts and final
trained-evaluation receipts are distinct immutable artifacts. No real child GPU
stage, pretrained download, commit or push occurred; PEFT/8B behavior is unverified.
