# Broader training-only receiver feasibility — design v1

Design date: 2026-09-19. Proposed run ID: `qwen3-receiver-feasibility-001`.
**The design, planner and receiver-only runner are implemented and CPU tested.
GPU execution remains unverified; no new real-model outputs have been collected.**
Implementation update: 2026-09-20. [Colab sequence](receiver_feasibility_colab.md).

**Question and scope**

Can the existing frozen warm-start actors produce both a valid correct and a
valid incorrect revision under the same receiver prompt on a broader, prespecified
training selection? Measure this separately for hold and repair contexts with the
existing four-candidate cap. Distinguish lack of eligible contexts from lack of
correct or incorrect continuations within eligible contexts.

The completed two-task bank and [matched base control](reviews/qwen3-base-control-001.md)
both lack correct receiver completions. They cannot establish availability on
broader data or a warm-start regression. This design broadens tasks while keeping
the actors, prompts, inference settings, labels and preference rule fixed.

Collect receiver feasibility evidence, not a scored continuation bank. Preserve
ordinary three-agent debate and final readout for context and outcome accounting,
but omit private alternatives, suffix replay, answer/packet NLL scoring, reference
forwards and optimizer updates. Do not manufacture absent credit/NLL fields or
export this artifact as a full training bank. Any later use for training must
follow a separate reviewed conversion/scoring contract.

**Frozen data selection**

Use the existing 1,200-task training manifest, with 600 ARC-Challenge and 600
original English LogiQA tasks. Exclude every task, audited group and normalized
content group in the completed 12-task warm start. Both old training-bank tasks
are included in that exclusion. The two manifests must have identical source,
full-pool and overlap-audit hashes, and the warm-start subset must match unchanged.

Rank remaining audited groups within each family by
`SHA256(canonical([20260919, "receiver-feasibility-v1", group_id]))`, breaking ties
by task ID. Select the first 12 per family, then interleave ARC and LogiQA ranks.
Selection never reads model outputs, answer correctness, estimated difficulty or
receiver eligibility. Do not replace a selected task after seeing its wording,
token length, label or outcome. Flag concerns and retain denominators instead.

These are **24 official training tasks excluded from our 12-task fine-tuning run**.
They are not held-out validation/test data and are not claimed unseen during the
backbone's pretraining. The inherited exact/lexical overlap audit does not establish
absence of semantic paraphrases. No new dataset download or final-test inspection
is required to construct this local plan.

Frozen identities:

| Artifact | Canonical SHA256 |
|---|---|
| Source 1,200-task manifest | `92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a` |
| Excluded warm-start manifest | `2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e` |
| New recipe | `efa9d8cfb1450227b80286309505116d9a8e03fd1732d99d1ee6b5bcabf3d7e1` |
| New task-selection artifact | `e6842155a4080c0a39e3ad39a8b207539312ffb57b05da7675a7343136e33d96` |

The checked-in [selection artifact](../experiments/receiver_feasibility_selection.json)
also pins per-task input, label, content and audited-group hashes. IDs below omit
the family prefix for readability; positions are zero-based and frozen.

| Rank | ARC task (position) | LogiQA task (position) |
|---:|---|---|
| 1 | MCAS_2002_8_9 (0) | train-4570 (1) |
| 2 | Mercury_406916 (2) | train-7183 (3) |
| 3 | Mercury_7007910 (4) | train-0655 (5) |
| 4 | Mercury_415092 (6) | train-0549 (7) |
| 5 | CSZ_2005_5_CSZ10383 (8) | train-0894 (9) |
| 6 | Mercury_7223283 (10) | train-5656 (11) |
| 7 | CSZ30494 (12) | train-7219 (13) |
| 8 | Mercury_7268013 (14) | train-4526 (15) |
| 9 | Mercury_7217105 (16) | train-5654 (17) |
| 10 | Mercury_SC_407397 (18) | train-2099 (19) |
| 11 | Mercury_400749 (20) | train-3933 (21) |
| 12 | Mercury_7210613 (22) | train-2868 (23) |

**Conditions and model**

Each selected task runs clean and exchange-corruption debate, in that order,
for 48 records. This targets receiver behavior after an initial answer exists.
Early exposure is omitted because it changes pre-communication coverage and would
add 24 trajectories; the scope is explicitly clean/exchange feasibility, not the
full clean/early/exchange training distribution or an attack robustness estimate.

Use the three completed warm-start exports as frozen actors. The recipe pins all
three adapter hashes and reference manifest
`ea4a62c215324b721d259bc3b7f104fa30fd2786548055ebbfd8f0f95837e963`.
Use Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, BF16/SDPA,
thinking disabled, and the same base snapshot/runtime as the completed bank.
No new training or base-control arm is included.

Use existing private/revision/readout prompts, packet grammar and seed functions,
generation seed 1729, temperature 0.7, top-p 0.8, top-k 20, greedy final readout,
4,096 context tokens, 256 packet tokens, 64 final tokens and 256 payload tokens.
Actor adapters are disabled for readout. Reject mismatched source, runtime, model,
adapter or template identities; a different runtime requires an explicit new design.

Keep `fixed-pool-v1` attack selection. Exchange sender is `position % 3`: each
sender occurs eight times overall and four times in each family. The same outgoing
attack reaches both recipients, while saved private state remains unchanged. All
three private packets are frozen before delivery; every revision sees initial
peers only. Corresponding clean/exchange main node seeds are paired by the existing
protocol. The cap below counts private generation separately in both conditions.

**Eligibility and four-sample receiver pools**

Determine strata from original private states and delivered messages before
sampling additional revisions, using the existing evaluator rules:

- **Hold:** the original receiver is correct and at least one delivered peer has
  a valid incorrect answer.
- **Repair:** the original receiver is not correct and at least one delivered
  peer has a valid correct answer. Preserve whether the receiver was valid-wrong,
  abstaining or invalid as a separate diagnostic breakdown.
- **Ineligible:** neither rule applies. Preserve these contexts in accounting;
  do not synthesize helpful peers or sample extra contexts to fill a stratum.

"Helpful" here means answer-correct peer content, not a verified rationale.
Imported/model text is evidence, never execution instructions. Official labels
and stratum metadata stay outside prompts.

For every eligible original receiver context, collect exactly four fresh
revision candidates. Reuse its exact serialized prompt and tokenized prefix;
use `node_seed(1729, trajectory_id, agent, "receiver", candidate_index)` for
candidate indices 0–3. The original main revision is measured separately and
is **not** a fifth candidate. Candidates do not change any saved packet, final
readout or other receiver's prompt. Stop sampling at four whether or not a pair
appears; never replace invalid or abstaining candidates.

A pair needs a valid correct and a valid wrong completion in this exact pool.
Abstentions and malformed/truncated outputs count as failures but are not
preference negatives. Select at most one pair per context with the existing
32-token length-bin priority, closest length, then candidate-index tie-break.
Include EOS in length; flag unmatched bins without discarding the pair. Preserve
all candidates and all missing-class reasons. No pairing across agents, prompts,
conditions or tasks.

**Hard workload bounds**

| Work | Maximum calls | Maximum output tokens |
|---|---:|---:|
| Main private and revised packets: 48 × 6 | 288 | 73,728 |
| Frozen-base final readout: 48 × 1 | 48 | 3,072 |
| Receiver candidates: 48 × 3 × 4 | 576 | 147,456 |
| Total | **912** | **224,256** |

There are at most 144 receiver contexts and 144 selected diagnostic pairs.
Main calls total 336; actual total is `336 + 4 × eligible_contexts` for a complete
run, counting modeled failure calls under the same accounting. Actual outputs
may be much shorter than their caps. The conservative input-token bound is
3,511,296, derived from each call's context cap minus its reserved output.
Teacher-forced forwards, suffix replays and optimizer updates are all zero.

At the earlier measured approximately 14 output tokens/second, saturating the
output ceiling alone would take about **4.45 hours**, before additional overhead.
This is a capacity calculation, not an expected runtime or billing estimate;
eligible-context counts, input lengths, hardware and storage dominate uncertainty.
Do not promise that this is a short run solely because it contains 24 tasks.

The full plan is frozen before execution. An infrastructure stop may be resumed
without changing it; never stop because enough pairs appeared or extend because
too few appeared. Completed calls need immutable artifacts so compatible resume
reuses them. Caps describe the declared logical work, not an unlimited allowance
for retries: log every fresh attempt, including failures, and stop on an ambiguous
lost call rather than silently exceeding the attempted-call budget. Any extra
crash-recovery generation needs a documented budget decision. Incomplete results
cannot be labeled complete or used to claim that an entire stratum lacks pairs.

**Measurements and prespecified decisions**

For each stratum, report eligible contexts, fully sampled contexts, usable pairs,
distinct supporting tasks, families and agents. Primary yield is usable pairs /
fully sampled eligible contexts, with numerator/denominator and completion state.
For a zero eligible denominator report null, not zero yield. Also report pair
support per selected task, family and condition so conditioning on eligibility
does not hide task-level scarcity.

For every pool retain correct, valid-wrong, abstention, malformed/invalid,
truncation/overflow counts; missing-correct, missing-incorrect or missing-both
reason; selected indices; exact prompts/tokens; and length matching. Report
original private correctness, main harmful revision/helpful repair, team coverage
and final success separately from the four-candidate diagnostics. For clean and
exchange, retain paired task-level outcomes. Do not treat candidates or repeated
conditions as independent tasks or claim population-level significance from
this 24-task screen.

Apply these decisions only after the entire schedule and raw audit complete:

| Observation | Interpretation and next review |
|---|---|
| A stratum has no eligible context | Context/coverage support is absent in this selection; no claim about continuation sampling in that stratum |
| Eligible contexts but zero pairs | Separate all-correct, no-correct and invalid/abstention failures; do not increase the cap or manufacture counterparts |
| Pairs in one stratum only | Asymmetric support; full revision objective remains unsupported |
| Both strata have pairs, but coverage gate below fails | Limited structural support; review concentration before any broader training claim |
| Both strata meet the coverage gate | Review a separately bounded frozen-reference scoring check; no automatic optimization |

The **engineering coverage gate** requires, separately for hold and repair:
at least six pair-bearing contexts, at least three distinct task IDs, and at
least one supporting task from each family. This is a conservative development
gate chosen before outcomes, not a power calculation, proof of adequate training
data or guarantee that all three actors have support. Report agent concentration
and unsupported agent/stratum cells explicitly. Even passing this gate does not
provide continuation credits or implement the full PACT objective.

All outcomes end this bounded check. A new prompt, larger budget, new warm start,
curated peers or another selection requires a separately recorded experiment.
No final-test access or paper efficacy claim follows from this screen.

**Artifact and implementation contract**

The implemented runner retains source/config/selection hashes, immutable reference
identities, normalized train tasks and separate labels, model/template/runtime
identity, raw main trajectories, receiver-call shards, actual token IDs, parser
statuses, pair diagnostics and per-attempt resource usage. Use a distinct
`train_only_receiver_feasibility_diagnostic` scientific status, with
`training_executed=false` and `training_pairs_exported=false`.

Checkpoint at call boundaries on scratch and persist at task boundaries through
timed workers. Create a local review ZIP before final Drive operations, verify
durable objects before success, and support restoring an exact verified snapshot.
Resume must reject source/config/selection/model/runtime mismatch and duplicate
or altered completed calls. Enforce context and global call/token caps; no silent
truncation, precision fallback, task replacement or regeneration of completed work.

The CPU execution checks cover: three-agent frozen-state
delivery and base readout; exact same-prompt candidate pools and distinct seeds;
stratum/missingness/coverage-gate accounting; zero-eligible and all-invalid cases;
token/call bounds; exclusion of alternative/replay/scoring/training calls;
immutable call-boundary resume; interrupted/failed calls; persistence timeouts,
archive/restore integrity; and unchanged actor/reference tensors in the neural
backend. Existing tests are reused where they cover the actual new code path.
The [implementation review](reviews/receiver-feasibility-implementation-001.md)
records the passing checks and the remaining GPU verification limits.

**Reproduce the design locally**

The planner reads already prepared data, verifies hashes and the committed task
selection, and prints the plan. It has no `--execute` option, loads no model,
downloads nothing and creates no run directory:

```bash
PYTHONPATH=src python -m pact plan-receiver-feasibility \
  --config experiments/receiver_feasibility.json \
  --data-dir results_import/training-data-001/proposal-1200 \
  --warmstart-data-dir results_import/training-data-001/engineering-12 \
  --selection experiments/receiver_feasibility_selection.json
```

The new config is not accepted by the old two-task `collect-bank` command. The
dedicated `receiver-feasibility` command now implements this design, defaults to
plan-only and requires `--execute` for model use. Follow the linked Colab guide
after publishing the implementation. Preserve the completed warm-start Drive
snapshot and object store for future actor restoration. The result ZIP alone
does not contain those weights.
