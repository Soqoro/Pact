# PACT heterogeneous-complementarity phase: experiment plan

Prepared 2 October 2026. New design; no results are claimed.

## Why this phase

The current shared-backbone experiments did not establish useful learned
complementarity, and controlled specialization remains closed incomplete. This
phase tests a different, well-defined source of variation: existing cross-family
instruction-tuned models. It does not replace the PACT algorithm or reopen any
closed study.

The two questions are: (1) do different models naturally add correct coverage
beyond the best individual, and (2) does communication preserve and use it?

## Models and controls

Constituents:
- Qwen/Qwen2.5-7B-Instruct
- meta-llama/Llama-3.1-8B-Instruct
- mistralai/Mistral-7B-Instruct-v0.3

Teams: QLM, QQQ, LLL, MMM. All are frozen, three-member teams. A common pinned
unadapted Qwen3-8B supplies independent and post-debate readouts; a task-only call
from that same readout is also a control. No prior adapter tensors are loaded.

Official revisions, native chat templates and stop-token behavior must be pinned.
The user must have authorized Llama access; the code cannot accept terms for them.

## Tasks and protocol

Use the entire original 80-task validation-pilot population, 40 ARC-Challenge and
40 English LogiQA. This is reused development material, not untouched final data.
No GPQA or new protected data are consumed.

For each task, draw three natural answers from each constituent family (9 calls).
Form the four teams with prespecified exact shared-packet bindings. Family-to-slot
permutations for QLM are balanced before outcomes; no best-of-pool selection.

For every team, compare independent voting, frozen synthesis of private packets,
and one synchronous exchange followed by the same frozen synthesis of revised
packets. An additional readout-only call measures what the synthesizer can do
without peer answers. Complete all tasks even when none have useful disagreement.

## Single-GPU execution

Load one model at a time. Generate each family's private bank in one phase, then
run revision requests grouped by family after the private barrier. Load the common
readout for the final readout phase. Text and immutable records bridge stages.

This avoids simultaneous residency and excessive per-question swapping. Actual
memory/throughput must be measured on the allocated Colab device. Token counts are
model-specific; equal caps are not identical FLOPs or exact text-length matching.

## Fixed budget

| Stage | Calls | Reserved output tokens |
|---|---:|---:|
| Nine private draws per task | 720 | 184320 |
| Four teams x three revisions per task | 960 | 245760 |
| Private synthesis for four teams | 320 | 20480 |
| Revised synthesis for four teams | 320 | 20480 |
| Task-only common readout | 80 | 5120 |
| Total | 2400 | 476160 |

The maximum is 30 calls and 5952 output tokens per task. The first-two-task smoke
uses 60 of these calls, not an extra budget. There are no training updates,
teacher-forced scoring, attacks, donors or counterfactual replays.

## Key reports

Initial coverage c = probability any member is correct.
Coverage gain G = c minus the best designated member's measured accuracy.
G is oracle answer availability, not automatically achieved team accuracy.

Report N0=0/1/2/3, individual accuracy, unique coverage, pairwise rescue, valid
correct/wrong mixed support, and different-wrong-answer disagreement separately.
Also report the N0-to-N1 transition matrix, erasure, construction, utilization,
readout losses, correct-repair counts, and final vote/synthesis/debate outcomes.

Compare QLM with all three homogeneous controls, not only their mean. Keep family
identity separate from display slot. Aggregate uncertainty by the 80 task groups;
replicas, readouts, and team views are not independent new examples.

## What results would mean

- G=0 despite disagreement: no observed added correct availability over the best
  member in this sample. A strength hierarchy can explain this pattern.
- G>0 but no final gain: available complementarity is not being used reliably.
- G>0 but QLM trails a strong homogeneous team: mixed capabilities exist, but
  mixing is not the best observed three-call strategy.
- QLM gains coverage and natural terminal performance over strong controls:
  useful heterogeneous collaboration in this setting, not learned PACT efficacy.
- More correct answers emerge only at readout: separate synthesis/construction
  from private complementary knowledge.
- Many parser/context failures: a technical limitation, not automatically a
  model-capability finding.

No outcome automatically launches training, adds models, increases samples or
starts an attack study. The next phase is a user-reviewed decision based on these
results. This study is itself a diagnostic baseline, not a new publication claim.

## Reading basis

The model-family pool is motivated by Yang et al., arXiv:2602.03794v1. Their
protocol and precise checkpoint details are not assumed identical. The official
model cards and Transformers chat-template documentation govern implementation.
See the full Codex specification for sources and exact tests/provenance rules.
