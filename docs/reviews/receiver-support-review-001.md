# Receiver-support review — 2026-09-20

The immediate limitation is the availability of useful learning contexts and
within-context answer variation. The broader screen has almost unanimous private
answers; the eligible receiver pools then contain only correct completions.
Increasing the existing receiver sample cap would not create missing natural
repair contexts. The evidence does not establish that the adapters collapsed,
that sampling is broken, or that a larger warm start would solve either shortage.

This is a post hoc, zero-generation analysis of the verified broader receiver
bundle and completed two-task training bank. It changes no labels, actor weights,
prompts, completed-run decisions or paper placeholders.

## Why natural repair is scarce

Count each task's clean private draw once. Clean and exchange use identical seeds
and produce identical raw text and completion arrays for all 72 private calls;
these paired conditions are not two independent draws.

| Initially correct agents | ARC tasks | LogiQA tasks | Total tasks |
|---|---:|---:|---:|
| 0 | 3 | 5 | 8 |
| 1 | 1 | 0 | 1 |
| 2 | 0 | 0 | 0 |
| 3 | 8 | 7 | 15 |

All three agents choose exactly the same answer on 23/24 tasks, including the
same incorrect answer on all eight all-wrong tasks. Of 26 initially wrong
receivers, 24 are on all-wrong tasks and have no correct natural peer. Only two
have helpful peers under clean delivery. Every LogiQA task is either all-correct
or all-wrong, so none supplies a natural repair context in this draw.

The single mixed task is `arc_challenge:Mercury_406916`, gold A. Agents 0 and 1
answer B; agent 2 answers A. Under clean delivery both wrong agents see agent 2's
correct packet and qualify for repair. The already frozen exchange assignment
corrupts sender 2 to answer B, removing that correct outgoing message from both
recipients. The sender retains its own correct private state, as required.
Therefore exchange has zero eligible repair contexts. This is a consequence of
the saved answers and declared delivery graph, not lost records or a parser bug.

This also illustrates why a receiver changing from wrong to correct is not
necessarily a helpful-peer repair event: agent 0 revises correctly under exchange
on this task despite receiving no correct peer. Eligibility must retain its
original definition; do not relabel this as helpful-message success.

## Why the receiver pools provide no contrasts

Of 32 hold contexts, 30 expose an initially correct receiver to one correct and
one wrong peer. Only two expose a correct receiver to two wrong peers. Those two
are the same agent on the mixed ARC task under clean and exchange: its incoming
peers are unchanged by corruption of its own outgoing message. They share the
same prompt but have different candidate seeds. The 34 scheduled eligible pools
therefore represent 33 distinct task/agent/prompt combinations and only 16 tasks
in total; their completions are not independent task-level observations.

All 34 original eligible main revisions are correct, as are all 136 fresh
candidates. Every pool lacks a valid-wrong completion. The main revision remains
outside the declared four-candidate pool; adding it retrospectively would still
produce no pairs and would violate the fixed candidate rule.

Sampling metadata is enabled, with four distinct seeds per pool and the pinned
temperature 0.7, top-p 0.8 and top-k 20. There is observed wording variation:

| Distinct raw completions among four candidates | Pools |
|---|---:|
| 1 | 14 |
| 2 | 8 |
| 3 | 7 |
| 4 | 5 |

Completion-token-array diversity gives the same distribution. Twenty of 34 pools
vary in wording, while every answer remains correct. Seventy-seven of 136
candidate strings equal the original main revision. Thus the archive does not
support a claim that all candidates are one duplicated cached result or that
generation was universally greedy. It also cannot establish the true probability
of a wrong completion, or isolate the effect of each sampling parameter.

The one main harmful revision occurs outside these eligible pools: on
`logiqa:train-4570`, all private answers are correct and clean delivery contains
no misleading peer, but one receiver abstains and the final readout abstains.
Exchange succeeds on that task. This accounts for the aggregate 15/24 versus
16/24 final-correct difference, and does not demonstrate a general benefit from
attack or justify changing which contexts count as hold.

## Comparison with the prior bank

Both bundles report the same actor/base snapshots, template, runtime, precision
and model revision. The prior two tasks were included in the tiny warm start;
the broader 24 explicitly exclude all 12 warm-start tasks. Their selections and
receiver contexts differ, so this is not a paired estimate of improvement.

| Run and stratum | Contexts | Correct | Valid wrong | Abstentions |
|---|---:|---:|---:|---:|
| Prior bank hold | 2 | 0 | 0 | 8 |
| Prior bank repair | 4 | 0 | 14 | 2 |
| Broader hold | 32 | 128 | 0 | 0 |
| Broader repair | 2 | 8 | 0 | 0 |

All prior eligible receiver contexts concern `logiqa:train-7374`. They are not a
representative estimate of receiver behavior. The broader task draw demonstrates
that missing correct answers is not universal under these actors, while its
all-correct pools demonstrate the opposite missing-class problem. Pooling those
old negatives with new positives would cross task/prompt boundaries and cannot
produce valid preferences. Neither run passes the bidirectional training gate.

## Next bounded question

Recommend a **single additional private-draw control on the same 24 tasks** before
changing training, attacks or sampling settings. It asks whether sparse natural
mixed correctness persists under another declared draw. It does not test receiver
pair availability or provide another completed training bank.

Proposed run `qwen3-private-support-control-001`: retain the exact selected tasks,
labels, actors, clean private prompts, runtime, temperature/top-p/top-k and limits.
Change only the global generation seed from 1729 to **1730**, with the existing
node-seed derivation. Generate one private packet per agent/task: **72 new calls,
at most 18,432 output tokens**, 4,096 total context per call. No revisions, readout,
attacks, private alternatives, scores, training or new receiver pools. This is a
separately named control, not a resume or extension of the completed experiment.

Record all 72 outcomes, per-agent answer/correctness transitions, task-level
0/1/2/3-correct counts, answer agreement and potential clean repair counts by
family. Keep the original and new private triples separate; do not select the
best seed per task or combine independently sampled packets into a purported
natural team. Invalid outputs remain failures and cannot serve as helpful peers.
Stop after this one draw regardless of support. There is no pair/readiness gate
on private-only outputs and no automatic receiver follow-up.

If support remains scarce, record that the additional draw does not resolve it;
this still does not prove scarcity across all seeds or tasks. If support changes,
record decoding-draw sensitivity and separately design any follow-on receiver
sampling before executing it. A second seed alone cannot establish population
rates or identify which training change would help. Preserve all outcomes rather
than searching seeds until mixed teams appear.

Implementation update: the [dedicated control runner](private-support-implementation-001.md)
now implements this proposal and passes CPU checks. The original 72-request
inventory is unchanged. Its [Colab guide](../private_support_control_colab.md)
documents the now [completed control](qwen3-private-support-control-001.md).
The additional draw found no mixed teams. The next
[curated helpful-peer design](../curated_repair_design.md) is a separately labeled
intervention, not another private-seed search.

Other changes are currently less diagnostic: more receiver draws cannot repair
zero helpful-context support; stronger wrong exchange messages cannot create a
correct peer on all-wrong tasks; higher temperature changes the policy; larger
warm starts change the actors; curated correct peers change the context source.
The proposal permits explicitly labeled same-task curated helpful packets, but
they are a separate intervention requiring genuine correct-packet provenance,
not manually attached gold labels. These are alternatives for a later design,
not established fixes or changes included here.

## Reproduction and limits

Run `PYTHONPATH=src python results_import/receiver-support-review-001/analyze.py`.
The checksum-verified inputs are the broader ZIP
`d61cb9bb82895f09f146a83ac52a26d4fdad18238585fb0bcf4bd13034996a9f` and prior-bank ZIP
`a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`.
Task-level and pool-level tables, the summary, proposed control inventory and
verification hashes are retained under `results_import/receiver-support-review-001/`.

Recorded outcomes establish the support counts, not a causal explanation of
weights or decoding. The archive does not independently demonstrate current
adapter tensor differences, logit entropy, tokenizer decoding or the user's Drive
contents. No external data, GPU inference, optimization or final-test access is
needed for this analysis. See the [completed raw audit](qwen3-receiver-feasibility-001.md)
and the proposal's training-data/preference-construction appendix for scope.
