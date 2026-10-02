# PACT project review

Review date: 30 September 2026. Scope: implementation and returned evidence through closure of `qwen3-controlled-specialization-001`.

**The pipeline works, real adapter training and counterfactual replay have been exercised, but we have not demonstrated a PACT performance advantage.** The completed controlled receiver study changed answer likelihoods without improving receiver correctness over its controls. GPQA supplied little complementary correct coverage. Natural specialization stopped for insufficient pair support; controlled specialization is now closed incomplete, with sparse observed replay effects and unresolved recovery accounting.

This report supersedes earlier audits' descriptions of what is currently pending. It preserves their historical results. No new experiment is scheduled, and final-test data have not been evaluated.

## What we built

The implementation supports a three-agent protocol: generate and freeze private packets, deliver initial peer messages, revise synchronously, then use a frozen base model to read revised packets. Fixed early and exchange attacks, private counterfactual replay, continuation-credit calculation, a masked responsibility solver, globally weighted specialization objectives, and the original optional DPO components are present.

We added bounded clean-answer adapter preparation; a supervised receiver objective that uses official answer targets under the unchanged receiver prompt; matched frozen/task-SFT/receiver-SFT arms; synthetic donor controls; an official gated GPQA loader with private and sanitized exports; and natural and controlled fixed-bank specialization paths. These are versioned experiments, not an executed joint full-PACT refresh loop.

The engineering includes pinned source/model identities, separate labels and defender inputs, immutable request journals, explicit missingness, call/token ceilings, guarded resume, optimizer checkpoints, and thin Colab entry points. Actual use exposed both storage scaling problems and an adapter precision-history deviation; neither is erased from the evidence.

| Capability | Evidence now |
|---|---|
| Protocol, parser, attacks, metrics, request reconstruction | CPU tests and audited real traces |
| Private continuation replay | Real eligible natural cases and controlled replay payloads audited |
| Clean-answer preparation | Two completed GPU recipes |
| Supervised receiver learning | Completed controlled three-arm GPU study |
| Responsibility solver and specialization training implementation | CPU/mock and tiny neural validation; real specialization training unexecuted |
| Full joint PACT updates, refreshes, matched final study | Deferred |
| Adaptive attacks, tool-transfer study, final-test evaluation | Unexecuted |

## Experiment history

Counts below refer to distinct run executions, not ZIP versions. Cached recovery and imported parent calls are not new generations.

| Study | Scope and disposition | Main finding |
|---|---|---|
| Smoke and profile | 4 and 20 validation tasks; 152 and 500 calls | Protocol exercised; profile debate clean/early/exchange success 9/20, 3/20, 9/20 |
| Validation pilot | 80 tasks, 5,912 calls; completed | Early attacks substantially reduce success; no trained PACT comparison |
| Selected replay check | 3 post-selected validation tasks, 386 calls | 13/18 eligible private pairs; 52 replay branches; no receiver preference pairs |
| Small warm start | 12 training tasks, 9 optimizer updates | Training and compatible continuation completed |
| Small training bank | 2 tasks × 3 conditions, 218 calls | 5 private pairs; all 6 main trajectories fail; no receiver pairs |
| Matched base control | 54 calls | Base also produces 0/24 correct receiver candidates |
| Broader receiver screen | 24 tasks, 472 calls | All 136 receiver candidates correct; no valid-wrong counterparts |
| Private-seed control | 24 tasks, 72 calls | 15 all-correct teams, 9 all-wrong, no mixed teams |
| Curated repair diagnostic | 2 selected ARC tasks, 32 calls | Helpful peers change 0/16 to 8/16 correct, confined to one task |
| Larger preparation and probe | 120 training tasks, 90 updates; 104 probe calls | Matched private and fixed-history receiver accuracy unchanged |
| Answer-only prompt control | 72 calls; completed and closed | Correctness unchanged at 45/72 |
| Natural receiver-supervision collection | 96 source tasks, 672 calls | Insufficient hold/repair context support; no training |
| Controlled receiver supervision | 217 donor + 603 evaluation calls; 48 updates across two arms | No incremental receiver correctness improvement |
| GPQA Diamond support | 32 development tasks, 256 calls; completed | 2 mixed teams; no coverage gain over best actor; no terminal communication gain |
| Natural fixed-bank specialization | 32 fit tasks, 1,216 calls | Only 2 supported tasks; stopped before replay |
| Controlled private specialization | 75 acquisition + 2,752 saved replay calls | Sparse effects; 4/5 calibration cells; closed incomplete |

The earlier consolidated audit records **8,646 generation calls** through natural receiver-supervision collection. Adding controlled receiver study 820, GPQA 256, natural specialization 1,216, and the controlled child's 2,827 saved calls yields **13,765 recorded generation calls**. Up to 16 additional controlled-child calls remain unaccounted for. This is recorded experimental accounting, not billed compute, independent observations, or a count of scoring/training forwards.

Executed optimizer updates total **147**: 9 small-preparation + 90 fresh larger-preparation + 24 task-SFT + 24 receiver-SFT. These recipes are separate; they are not 147 sequential updates to one model. No specialization optimizer updates were executed.

Historical sources: [September 22 audit](PACT_PROJECT_AUDIT_2026-09-22.md), [experiment ledger](../experiment_ledger.md).

## Validation pilot

Correct terminal answers out of 80 validation tasks:

| Method | Clean | Early attack | Exchange attack |
|---|---:|---:|---:|
| Single | 45 | 13 | N/A |
| Vote | 45 | 12 | N/A |
| Frozen synthesis | 47 | 12 | N/A |
| Debate | 47 | 10 | 46 |
| Ignore peers | 48 | 11 | N/A |
| Archive | 47 | 12 | 47 |

This is unadapted Qwen3-8B under one selected task/seed configuration. N/A means no relevant exchange surface. Archive receives extra context, so these numbers do not establish matched-compute superiority. Debate did not beat synthesis on clean accuracy. [Raw pilot audit](../reviews/qwen3-pilot-001-raw.md).

The selected natural replay check produced five +1, two +0.5 and six zero continuation credits among 13 eligible pairs. That demonstrates that the estimator executes on real cases; post-selection and two suffix replicates do not establish a population benefit. [Replay audit](../reviews/qwen3-replay-check-001.md).

## Why we changed the receiver learning recipe

The original receiver preference recipe required both a correct and a valid incorrect completion under the same prompt. The small bank produced no correct receiver candidates; the broader screen produced only correct candidates. Neither supplied preference pairs. Helpful curated peers improved one task, but comparisons across different prompts cannot create same-prompt DPO pairs.

Receiver supervision removed that sampling prerequisite: an official label supplies the answer-bearing output prefix, while the full receiver prompt remains the input. No invented gold rationale is required. Hold and repair strata receive balanced loss, and missing support stops the study rather than silently reallocating weight.

The first natural source collection still failed a different prerequisite: legitimate contexts. Fit hold/repair support was 2/2 tasks against minima of 8/8; held-out support was 0/1 against minima of 4/4. An offline inventory found no same-task donors among 950 distinct retained historical call/raw identities. No training occurred in that run. [Collection audit](../reviews/qwen3-receiver-supervision-001.md).

The subsequent controlled child explicitly allowed offline answer-conditioned synthetic peer donors. It preserved original focal states and separate synthetic/natural claims. This enabled actual receiver training, with the results below.

## Completed controlled receiver comparison

The study acquired 217 donor calls and trained only focal agent0, with 24 updates per trained arm. Fit support covered 45 tasks; evaluation support covered 19 tasks, including only six repair tasks. All three arms completed 201 evaluation calls and 57 answer-scoring forwards each. Total generation: 820 committed, zero unresolved. DPO was off.

| Outcome | Frozen preparation | Task SFT | Receiver SFT |
|---|---:|---:|---:|
| Hold with wrong-target donor | 13/13 | 13/13 | 13/13 |
| Repair with correct-target donor | 1/6 | 1/6 | 1/6 |
| Repair with peers withheld | 0/6 | 0/6 | 0/6 |
| Private answers | 20/32 | 21/32 | 21/32 |
| Natural-team clean success | 5/8 | 5/8 | 4/8 |
| Natural-team exchange success | 4/8 | 4/8 | 5/8 |

All 57 matched receiver correctness outcomes were identical across arms: 40 correct and 17 incorrect. The one repair from correct-target advice already occurred in frozen initialization. Both trained arms gained the same single private answer. Each arm totaled 9/16 team successes across eight paired tasks and two conditions.

Teacher-forced repair answer-token NLL with correct-target advice decreased from **11.3762 → 8.3008 → 6.3415** for frozen, task SFT and receiver SFT. This is evidence that scoring changed, but it did not translate into additional correct receiver outputs. Loss also decreased without peers, so it cannot all be attributed to learned peer use.

**Conclusion:** supervised receiver training is operational, but this bounded study did not demonstrate an incremental repair or correctness benefit. Six repair tasks and one training seed do not establish impossibility or population equivalence. Synthetic rationales remain unreviewed. [Completed evaluation audit](../reviews/qwen3-receiver-supervision-controlled-001-evaluation.md).

## Preparation controls and precision history

Moving from the 12-task preparation to the fresh 120-task preparation did not improve matched private correctness: **45/72 → 45/72**. Fixed-history receiver correctness remained **8/32 → 8/32**. The answer-only prompt control also retained 45/72 correct. The earlier 46/72 baseline used a different seed and is not the valid matched comparison. The prompt diagnostic is complete and was not substituted into the main packet protocol.

The controlled receiver study exposed nonfocal adapter loading through FP32 → BF16 → FP32. Reported unchanged checks after loading did not prove preservation of original export values. Recovery explicitly matched the effective initialization and retained that history for subsequent GPQA and specialization studies; it did not silently restore original FP32 values or rerun training. Local audits checked receipts and available payloads, not omitted real checkpoint tensors. [Training and recovery audit](../reviews/qwen3-receiver-supervision-controlled-001-training.md).

## GPQA Diamond support

All 32 prespecified development tasks completed the same private, synthesis, clean exchange and revised-readout plan: 256 calls, exactly 53,248 reserved output tokens. No training or teacher-forced scoring occurred. The official-source option policy excluded two exact repeated-option rows; 164 remaining source tasks were protected. Raw GPQA material remains outside public repository outputs.

| Measure | Result |
|---|---:|
| Individual accuracy, agents 0/1/2 | 9/32, 7/32, 7/32 |
| Initial correct coverage | 9/32 |
| Coverage gain over best actor | 0/32 |
| Valid correct/wrong mixed teams | 2/32 |
| Any answer disagreement | 6/32 |
| All-wrong answer diversity | 4/32 |
| Vote / synthesis / debate success | 7/32 each |

Initial correct-actor counts N0=0,1,2,3 were **23,2,0,7**. Both mixed teams lost their sole correct packet during revision. There were no successful repairs in four opportunities on those two tasks. Initially all-wrong teams stayed all wrong. Initial synthesis also failed on both mixed tasks, so paired synthesis-versus-debate correctness did not change despite internal erasure.

**Conclusion:** harder questions did not supply useful complementary coverage in this configuration. The screen was `sparse_preliminary`, not a full-Diamond leaderboard result. Two mixed tasks are too few for a population preservation claim. [GPQA audit](../reviews/qwen3-gpqa-diamond-support-001.md).

## Specialization studies

The natural fixed-bank study completed 32 fit tasks under clean and early conditions, producing 64 rows and 1,216 calls. Only **5/192 actor/condition cells on 2/32 tasks** supplied eligible natural correct/wrong pairs, below the eight-task gates. It stopped before replay, scoring, assignments, training or development evaluation. Missing support does not mean the initial team had no correct coverage. [Natural bank audit](../reviews/qwen3-specialization-contrast-001.md).

The controlled child reused immutable parent anchors and generated one shared positive/negative synthetic packet pair per supported task. Its 75 acquisition calls yielded pairs for 22/32 tasks and 132 eligible actor/condition cells. This passed structural support; it did not certify donor reasoning or reliable credit. Sampled negative rationales sometimes contradicted their chosen answer. [Acquisition audit](../reviews/qwen3-controlled-specialization-001-acquisition.md).

Recovered replay evidence:

| Stage | Saved cells | Estimated effect distribution |
|---|---:|---|
| Primary | 132/132 | 125 zero, 3 at +0.5, 3 at +1, 1 at −1 |
| Reversed order | 36/36 | 35 zero, 1 at +1 |
| Natural calibration | 4/5 | 1 zero, 2 at +1, 1 at −1 |

Here the effect is the difference in terminal success after inserting the positive versus negative full packet, averaged over two corresponding suffix seeds. It includes wording changes and is not natural on-policy credit.

Primary positive branches succeeded in 112/264 continuations versus 105/264 negative branches. Seven nonzero cells occupy six tasks; 38/44 rows have identical effects across actor slots. Reversed order changes three of 36 matched estimates, including one strict pairwise slot-rank reversal. Natural calibration has no matching supported controlled cells, so estimator agreement cannot be assessed.

The forensic audit reproduced **688 saved branches and 2,752 embedded call records**, with exact saved credit calculations. However, the latest snapshot remains `recovery_safe=false`. The fifth calibration cell is absent, and up to 16 subsequent calls may be unrecorded. Full dispatch journals, tokenizer recounts and omitted weights were not independently reconstructed by this partial archive.

The user accepted closure as **incomplete**. No specialization training occurred. Assignment contrast is **unevaluated, not failed**: likelihood scores are absent, and the global balance penalty couples rows, so six tasks with varying credit alone cannot determine the eight-task L1 gate. No safety flag, budget or historical artifact was changed. [Ledger and forensic findings](../experiment_ledger.md).

## Engineering validation and evidence limits

The latest recorded full suite ran 221 tests: **207 passed, 14 optional skips, zero failures**. Subsequent focused guards passed 12 tests; three opt-in tiny CPU neural tests also passed. Mock round trips cover acquisition through assignment, training schedules, evaluation and export; tiny neural checks exercise actual gradients, isolation and resume. These are software evidence, not real-model specialization outcomes. [Validation handoff](../controlled_replay_completion.md).

Repeated Colab resets and slow Drive operations exposed the cost of restoring thousands of small files. Local-first bundles, bounded persistence and compact inference restore improved recovery options. They did not guarantee recovery after unknown dispatches. The final incomplete study illustrates why matching saved intent and result counts is insufficient when a pre-dispatch unsafe snapshot may precede lost local work.

For this report, existing consolidated/per-run audits, ledger, decisions and latest forensic summaries were cross-checked. No old GPU runs, scoring, training or regression suite were rerun. Report arithmetic and relative links were checked. Prior checksum/semantic audits are cited as historical work, not claimed freshly repeated here. Drive availability and omitted tensor bytes were not independently checked.

Data exposure remains explicit: repeatedly inspected training-development tasks are not untouched tests; GPQA's selected 32 tasks are development-exposed; the specialization development cohort was not evaluated. Exact/source-ID and lexical screening do not establish absence of semantic paraphrases. Calls, conditions and actors are correlated within tasks and cannot be treated as independent sample sizes.

## Review conclusions

Established: the protocol and bounded training paths execute; eligible private replay produces reproducible saved estimates; receiver SFT changes answer-token loss; natural support can be scarce even with high parser validity; and correct private information can be erased or unused by communication.

Not established: a receiver-specific accuracy gain, useful learned specialization, an advantage from continuation-credit allocation over local or uniform training, improved natural robustness, or full PACT efficacy. No final-test claim or manuscript result placeholder is filled.

The completed controlled receiver result remains unchanged. Both specialization runs are stopped, with the controlled child explicitly closed incomplete. Any future experiment needs a separately reviewed scientific question, source/target contract and finite budget. This report authorizes no further runs.
