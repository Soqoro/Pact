# Curated helpful-peer diagnostic — design v1, 2026-09-20

Completed run: `qwen3-curated-repair-001`. **[Returned GPU audit](reviews/qwen3-curated-repair-001.md)
passes for 32/32 calls; zero within-prompt preference pairs.** The frozen design
below records the decisions made before sampling. This is a 32-call, two-task diagnostic of
receiver response to a recorded correct peer message. It cannot establish broad
preference availability, natural-team accuracy or full PACT readiness.

## Question and choice

The [completed second-seed control](reviews/qwen3-private-support-control-001.md)
has nine all-wrong teams and no natural repair context. Before changing actor
training, ask: on fixed wrong private states, does replacing one outgoing peer
message with a genuine, previously sampled correct packet change recipient
correctness or expose same-prompt preference contrasts?

The specification and proposal permit same-task stored helpful packets when
provenance is retained and curated insertions are distinguished from natural
communication. This design applies that permission narrowly. It introduces no
manual gold-answer rationale, new donor generation, private resampling, stronger
attack, temperature change, adapter update or final readout.

An inventory of the nine all-wrong tasks finds correct packets in the broader
run's original private/revised trajectories for only two ARC tasks. The other
seven tasks, including all five all-wrong LogiQA tasks, lack such a donor. This
absence is retained; no task or message is substituted. The earlier two-task bank
concerns different tasks and cannot supply same-task donors for this selection.

## Frozen sources and selection

Baseline private states: the completed seed-1730 control ZIP,
SHA256 `f67045fc3f2bc102e7345ba3337c5406796360e76f437355dd849302cb33bc06`.
Donor pool: the completed broader receiver ZIP,
SHA256 `d61cb9bb82895f09f146a83ac52a26d4fdad18238585fb0bcf4bd13034996a9f`.
Both use the same frozen warm-start actors and pinned Qwen3-8B/runtime identity.

Inventory all nine tasks whose seed-1730 private answers are wrong. Search only
original main private/revised packets from the broader run on the exact same
normalized training task. Exclude final readouts, candidate pools and all other
tasks. Require a valid answer equal to the unchanged official label. Choose one
packet per available task by: private before revised; clean before exchange;
lower agent index; then call hash. This rule and the resulting two-task inventory
are now frozen, before any receiver outputs for this intervention.

| Task | Gold | Saved private answers | Donor agent | Donor origin | Recipients |
|---|---|---|---:|---|---|
| `arc_challenge:Mercury_406916` | A | B, B, B | 2 | Seed-1729 clean private packet | 0, 1 |
| `arc_challenge:Mercury_7210613` | C | D, D, D | 0 | Seed-1729 exchange main revision | 1, 2 |

Both donor rationales have been read alongside their task and options. Their
answers match the official labels; retain the raw sampled text without claiming
formal verification of the reasoning. The second donor has revision-stage context
in its history, unlike the first. Record that phase difference, exact source
record/call/packet hashes, source actor, and both archive checksums. It limits
cross-task interpretation and must not be disguised as a fresh private sample.

Selection deliberately uses already observed wrong states and correct donor
availability. This is post-selected diagnostic support, not a random sample of
ARC, a held-out evaluation, or a replacement for the previous outcome-independent
24-task selection. LogiQA support remains absent.

## Intervention and matched control

Freeze each complete three-packet seed-1730 private state. Keep the donor's source
agent as the sender; do not reattribute another actor's text. Sample only the
other two recipients. The sender's current saved private state stays wrong and
unchanged, even though its substituted outgoing text is a correct packet from
its own earlier trajectory.

Each recipient has two arms:

- `original_peers`: its own saved private packet and both original peer messages.
- `curated_help`: exactly the same own private packet and peer order, with the
  selected sender's outgoing text replaced by the donor's raw bytes. The other
  peer is unchanged. Both recipients receive identical replacement bytes.

The normal trusted-task serialization, revision instruction and peer envelopes
are unchanged. No stratum, arm label, gold label, donor provenance or evaluator
annotation enters defender messages. Those remain separate metadata. Each arm
sees initial saved peers only; no generated receiver revision enters another
receiver prompt. This is controlled message substitution, not a full natural
team rollout or an adversarial exchange evaluation.

Use the same four corresponding receiver seeds in both arms:
`node_seed(20260920, "curated-repair-v1", task_id, recipient, sample_index)` for
indices 0–3. Freeze peer order using the existing
`node_seed(1729, task_id, recipient, "peer-order")` rule. Keep BF16/SDPA, disabled
thinking, temperature 0.7, top-p 0.8 and top-k 20. Preserve the 4,096-token context
and 256-token output cap. Tokenized prefixes must match within each four-sample
pool; the two arms intentionally have different prompts.

## Budget and accounting

Two tasks × two recipients × two arms × four samples = **32 new revision calls**;
maximum **8,192 output tokens**, theoretical 122,880 input tokens. There are eight
pools, four recipient comparisons, and 16 distinct seed values reused across arms.
No private, donor-generation, final-readout, reference-scoring or optimizer calls.
No extra sample is drawn to replace an invalid output or obtain a missing class.

The runner checks all actual rendered/tokenized contexts before sampling;
if the fixed context budget cannot fit, stop and report incompatibility instead
of trimming messages or silently omitting a case. The planner does not load a
tokenizer and has not verified those tokenized lengths. Failed/unresolved attempts
must remain charged and must not be silently regenerated on resume. Require the
same immutable-call, latest-safe-snapshot and local-ZIP-before-Drive contract as
the completed control, with explicit failure/incomplete accounting.

Report every pool's correct, valid-wrong, abstaining, invalid and length-failure
counts. `original_peers` is a no-help control, not a repair stratum; `curated_help`
is a deliberately constructed repair context. Report paired correctness
transitions for each matching seed and per-recipient/per-task counts. Four samples
are not four independent tasks. Do not claim population-level significance from
two ARC tasks.

Within each fully sampled arm, diagnostic pair availability requires both a valid
correct and valid-wrong completion under that exact prompt. Never pair a correct
curated-arm output with a wrong control-arm output. Retain the existing 32-token
length-bin preference diagnostic rule if both classes occur, but export no
training pairs and run no scores. There are no hold contexts in this design;
`full_pact_ready=false` for every outcome.

## Decisions fixed before sampling

| Observation | Interpretation / next review |
|---|---|
| Curated messages help, but pools remain single-class | Context supply matters on these cases; no within-prompt preference support established |
| Curated arm has correct/wrong mixtures | Local diagnostic repair-pair support; no natural-support, LogiQA or hold claim |
| Both arms already correct | These saved wrong states can be repaired without this helpful insertion; no demonstrated need for the donor |
| Curated messages fail to help or reduce correctness | Correct answer-bearing text alone is insufficient on these cases; inspect recorded responses without relabeling or resampling |
| Partial run, incompatible context or unresolved call | Incomplete diagnostic; no absence-of-effect or readiness conclusion |

The comparison changes content and possibly length/style, not correctness alone.
Any difference concerns this particular message intervention; it does not isolate
an abstract causal effect of truth, establish terminal team benefit, or prove
that the receiver used the peer rather than re-solving the task.

All outcomes close this fixed diagnostic. Further donor acquisition, actor
preparation, attack changes or more tasks require a separate design. A larger
warm start changes the actors and may increase agreement; it is not an established
fix. This smaller intervention keeps the current actors fixed and uses existing
provenance to test the context-supply hypothesis first.

## Local reproducibility and implementation gate

```bash
PYTHONPATH=src python -m pact plan-curated-repair \
  --config experiments/curated_repair.json \
  --receiver-bundle results_import/qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip \
  --private-bundle results_import/qwen3-private-support-control-001-handoff-1789909726537323854.zip
```

This command verifies both archives and the parent plan, recomputes private
support, and builds the exact eight prompts without loading a model or writing a
run. It has no `--execute` option. Config hash:
`ac29ebf94ee954729923ed7d72c8e474cf165e48a289a545fe0e8b6a002587d4`.
Context inventory hash:
`66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab`.

The dedicated runner now preserves this inventory, preflights all actual tokenized
contexts, reports within-arm outcomes and paired seed comparisons, and supports
bounded recovery and verified handoff. See the [CPU implementation review](reviews/curated-repair-implementation-001.md)
and [Colab cells](curated_repair_colab.md). The pinned GPU run is now complete and audited, including actual context fit.
GPU reset/resume remains unverified. The design and stop rules above are unchanged;
do not extend this completed diagnostic.
