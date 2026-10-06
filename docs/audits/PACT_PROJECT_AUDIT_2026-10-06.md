# PACT project review

Review date: 6 October 2026. Scope: implementation and returned evidence through the completed heterogeneous complementarity diagnostic, including the earlier controlled specialization closure.

**PACT has an operational experimental pipeline and real training/replay evidence, but no demonstrated PACT performance advantage.** The latest mixed-model study supplies substantially more complementary correct private answers: 63/80 tasks have a correct member, compared with 49/80 for the best observed homogeneous team. That extra coverage does not translate into higher final accuracy: mixed-team synthesis solves 43/80 and post-exchange readout 40/80, versus 41/80 for the common task-only readout.

The completed receiver study changed answer likelihoods without improving matched receiver correctness. Natural specialization stopped for inadequate support; controlled specialization remains closed incomplete. These outcomes distinguish an operational implementation, useful natural information diversity, and a still-unproven ability to learn or use that diversity.

This report supersedes the [September 30 audit](PACT_PROJECT_AUDIT_2026-09-30.md) as the current project overview. It preserves their historical results. No new experiment is scheduled, and final-test data have not been evaluated.

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
| Heterogeneous clean inference and common readout | Completed A100 GPU run; 80 tasks, 2,400 calls; offline audit passed |
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
| Heterogeneous complementarity | 80 exposed pilot tasks, 2,400 calls; completed | QLM coverage 63/80; synthesis 43/80; post-exchange 40/80 |

The earlier consolidated audit records **8,646 generation calls** through natural receiver-supervision collection. Adding controlled receiver study 820, GPQA 256, natural specialization 1,216, and the controlled child's 2,827 saved calls yielded 13,765 recorded generation calls through September 30. The new heterogeneous run adds 2,400, giving **16,165 recorded generation calls**. Up to 16 additional controlled-child calls remain unaccounted for. This is recorded experimental accounting, not billed compute, independent observations, or a count of scoring/training forwards.

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

## Heterogeneous complementarity diagnostic

This separate inference-only study used fresh official Qwen2.5-7B-Instruct (Q), Llama-3.1-8B-Instruct (L) and Mistral-7B-Instruct-v0.3 (M), with a common unadapted Qwen3-8B readout. It did not reuse the older preparation adapters. All 80 original pilot tasks were reused as explicitly development-exposed data: 40 ARC Challenge and 40 LogiQA.

Three private samples per family formed a shared nine-packet bank per task. The prespecified QQQ, LLL, MMM and mixed QLM teams reused those packets with balanced family-to-slot bindings. Each revision saw only initial peers. Communication ran on every task, not only mixed or correct ones. Native templates/tokenizers, one resident model at a time, immutable model revisions and bounded generation were retained. The two-task smoke reused requests within the full plan. There was no training, attack, donor generation, replay, GPQA or final-test access.

| Team | Initial correct coverage | Valid correct/wrong mixed tasks | Independent vote | Initial-packet synthesis | Revised-packet readout |
|---|---:|---:|---:|---:|---:|
| QQQ | 45/80 | 2/80 | 44/80 | 46/80 | 45/80 |
| LLL | 49/80 | 14/80 | 39/80 | 42/80 | 44/80 |
| MMM | 34/80 | 7/80 | 32/80 | 32/80 | 31/80 |
| QLM | **63/80** | **47/80** | 36/80 | 43/80 | 40/80 |

Coverage means at least one private packet is correct, not that the system can identify it without labels. The common task-only readout achieved 41/80. Within QLM, individual correct counts were Q=44, L=37 and M=31. Coverage exceeded its best observed member by 19 tasks and the best homogeneous team's coverage by 14 tasks. The latter observed-cohort difference is 17.5 percentage points, with a stored task-bootstrap interval of [7.5,25.0] points; the homogeneous maximum is reselected inside each draw. This is descriptive selected-comparator evidence, not a prespecified deployment router or a population guarantee.

Initial QLM N0 counts for zero, one, two and three correct members were [17,28,21,14]. The 49 tasks with one or two correct packets are not all valid correct/wrong mixed teams: invalid or abstaining peers explain why valid mixed support is 47. Wrong-answer disagreement alone is not complementary correct coverage.

| Mixed-team measure | Result | Unit and interpretation |
|---|---:|---|
| Hold | 61/67 | Eligible actor opportunities retaining correctness |
| Repair | 12/69 | Eligible actor opportunities becoming correct |
| Team erasure | 3/63 | Initially covered tasks losing all correct revised packets |
| Utilization | 39/63 | Initially covered tasks with correct final readout |
| Construction | 1/17 | Initially uncovered tasks with correct final readout |
| Readout loss | 22/80 | A correct revised packet exists but final readout fails |

The final 40 successes decompose into 39 initially covered and one initially uncovered task. Readout loss is distinct from erasure: surviving correct information can still fail to determine the final answer. These observations point to limitations in using available information; they do not isolate a causal failure of a particular model or identify a proven training remedy.

Relative to initial synthesis, mixed-team exchange produced three gains and six losses: 37 tasks were correct under both, 34 incorrect under both. The difference is -3.75 percentage points, with a paired, dataset-stratified 1,000-draw bootstrap interval of [-11.25,+3.75]. The interval includes zero; this does not establish that communication generally harms performance or that methods are equivalent. Sampling units are the 80 tasks, not the 2,400 correlated calls.

| Mixed-team dataset | Coverage | Synthesis | After exchange | Task only |
|---|---:|---:|---:|---:|
| ARC Challenge | 33/40 | 26/40 | 25/40 | 24/40 |
| LogiQA | 30/40 | 17/40 | 15/40 | 17/40 |

The returned run records an A100-SXM4-80GB and completed 2,400/2,400 calls, exactly 476,160 reserved output tokens, 926,451 actual input tokens and 100,395 actual output tokens. There are zero unresolved calls and zero context overflows; recovery_safe is true. Completion does not mean every answer parsed successfully: abstentions, seven private length stops, two malformed private Q outputs and two malformed M revisions remain failures. No optimizer or teacher-forced forwards occurred.

The first smoke attempt hit a wrapper bug before generation: a four-value reconstruction result was unpacked into three variables. The fix added a CPU regression. The returned source-transition receipt records zero original attempts and an unchanged scientific plan under a new source identity; old evidence was preserved. That receipt is not a fresh independent audit of the old Drive snapshot.

**Conclusion:** on this cohort, model heterogeneity supplies useful natural correct-answer diversity, but the tested communication/readout does not turn it into higher final accuracy. This does not establish trained specialization or PACT efficacy. Comparisons to historical Qwen3/GPQA diagnostics are descriptive: tasks, actor families, effective weights and other conditions differ. No additional run or methodological change follows automatically.

## Latest evidence provenance

- Study: `pact-heterogeneous-complementarity-001`; variant `heterogeneous_natural_support_v1`.
- Clean source commit: `874b3b184c6cdcde6c27368621d7747fd6e01467`.
- Current plan hash: `b972e06e3b8e69f8e53053d238b7fa7f04c1ddb331654b7555262021d47a506f`.
- Original zero-call plan: `1bf11069721fb09169d10c1337112e5cef3dd92ebaec078110bb7ec392294331`.
- Returned bundle suffix: `1791189410949196090`.
- PRIVATE SHA256: `57cde0e55b4acf8443582b06205778a12f4b0214d5007932e23f1f0b102f89d4`.
- SANITIZED SHA256: `c96c04aa1303dec275f9f9db534786727ec75300d02da4fe71779a5c29b887d7`.

The October 5 import verified both ZIP hashes. The existing offline audit reconstructed private requests/results and regenerated the saved summary exactly; sanitized checksums and summary equality also passed. Private data remain in ignored archives and the ignored extraction `results_import/heterogeneity-return-1791189410949196090`. This report publishes aggregates and provenance only. Artifact validation supports internal consistency; it is not an independent reproduction of model generations. See [the ledger](../experiment_ledger.md) and [methodology](../heterogeneity_methodology.md).

## Engineering validation and evidence limits

The September 30 audit recorded a 221-test suite with 207 passes and 14 optional skips, followed by focused guards and tiny CPU neural checks. The more recent heterogeneous implementation ran 231 tests: 215 passed, 14 skipped and two existing GPQA privacy-guard tests errored because of the sandbox's /tmp Git marker. Those affected cases subsequently passed within a 20-test targeted run using /var/tmp; the full suite was not subsequently shown entirely green in one invocation. The final pre-fix heterogeneous suite had 17 passes. After the smoke-wrapper fix, all 18 heterogeneous CPU/mock tests passed in 48.490 seconds.

These tests validate software and selected numerical contracts, not scientific efficacy. The missed execution-wrapper unpack bug shows that earlier collector-level tests did not cover the real entry path sufficiently. The returned A100 run now supplies actual GPU evidence for that configuration; it does not validate all GPUs, versions or recovery situations. See [implementation status](../implementation_status.md) for the exact historical checks.

Repeated Colab resets and slow Drive operations exposed the cost of restoring thousands of small files. Local-first bundles, bounded persistence and compact inference restore improved recovery options. They did not guarantee recovery after unknown dispatches. The final incomplete study illustrates why matching saved intent and result counts is insufficient when a pre-dispatch unsafe snapshot may precede lost local work.

For this report, the previous consolidated audit, current ledger/status and the reconstructed heterogeneous summary were cross-checked. Earlier per-run findings are carried forward with their original audit links. No old GPU runs, scoring, training or regression suite were rerun. Report arithmetic and relative links were checked. Prior checksum/semantic audits are cited as historical work, not claimed freshly repeated here. Drive availability and omitted tensor bytes were not independently checked.

Data exposure remains explicit: repeatedly inspected training-development tasks are not untouched tests; GPQA's selected 32 tasks are development-exposed; the specialization development cohort was not evaluated. Exact/source-ID and lexical screening do not establish absence of semantic paraphrases. Calls, conditions and actors are correlated within tasks and cannot be treated as independent sample sizes.

## Review conclusions

Established: the protocol and bounded training paths execute; eligible private replay produces reproducible saved estimates; receiver SFT changes answer-token loss; natural same-prompt pair support can be scarce; and heterogeneous actors can supply substantial complementary correct coverage on the exposed cohort. Correct information can still be erased or unused by communication/readout.

Not established: a receiver-specific accuracy gain, useful learned specialization, an advantage from continuation-credit allocation over local or uniform training, improved natural robustness, or full PACT efficacy. No final-test claim or manuscript result placeholder is filled.

The completed controlled receiver result remains unchanged. Both specialization runs are stopped, with the controlled child explicitly closed incomplete. Any future experiment needs a separately reviewed scientific question, source/target contract and finite budget. This report authorizes no further runs.


## Decisions for the review

Accept the heterogeneous diagnostic as completed, with its coverage advantage and lack of final accuracy advantage both retained. Keep the original receiver result unchanged and controlled specialization closed incomplete. The unresolved questions are how to use available correct information, whether any bounded learning intervention improves held-out development outcomes, and whether replay-based allocation contributes beyond simpler controls. These are research questions, not approved next experiments.

Before authorizing further work, distinguish the intended target: receiver repair, final readout selection, or learned actor specialization. Each would require its own prespecified comparison, data-exposure treatment and budget. The current evidence does not select a winning intervention or justify filling manuscript PACT result placeholders.
