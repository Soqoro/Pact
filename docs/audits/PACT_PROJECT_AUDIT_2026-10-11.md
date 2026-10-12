# PACT project audit — 11 October 2026

**Status: a functioning research pipeline and several completed diagnostics, but no demonstrated full-PACT performance advantage.**

The project has executed real adapter preparation, a controlled receiver-learning comparison, private replay diagnostics and clean heterogeneous-team studies. Receiver SFT changed answer likelihoods without improving matched receiver correctness. Natural specialization stopped for insufficient support; controlled specialization was closed incomplete before training. Heterogeneous actors often provide more correct-answer coverage, but the tested communication/readout does not consistently turn that availability into a final-answer advantage.

The new benchmark breadth results extend this finding across MMLU-Pro, MuSR, MATH-500 and a separate GPQA cohort. MBPP+ remains partially generated and incompletely scored; LiveBench remains blocked under the frozen source requirements. No training occurred in the breadth studies.

This is a review document, not authorization for another experiment. The proposed GPQA Phase B extension was discussed but **not implemented or authorized**; the user requested this audit instead. Manuscript PACT result placeholders remain unfilled.

## 1. Scope, evidence and interpretation

Review cutoff: 11 October 2026, Asia/Singapore. This report supersedes the [6 October overview](PACT_PROJECT_AUDIT_2026-10-06.md) as the current summary, preserving historical reports.

Sources are the [experiment ledger](../experiment_ledger.md), [implementation status](../implementation_status.md), [implementation decisions](../implementation_decisions.md), [exposure ledger](../benchmark_exposure_ledger.md), historical per-run reviews and latest reconstructed breadth summaries. Historical audits are carried forward; this report does not claim to have rerun old GPU work, revalidated omitted checkpoint tensors or independently inspected today's Drive contents.

Important distinctions:

- **Coverage:** at least one private actor answer is correct. This is evaluated with labels; it is not a deployable answer selector.
- **Valid mixed support:** a task has valid correct and valid wrong private answers. Invalid/abstaining outputs do not supply valid wrong answers.
- **Synthesis:** common frozen readout on the initial private packets.
- **Post-exchange readout:** the same readout on revised packets after one synchronous exchange using only original peers.
- **Erasure:** initially covered tasks lose every correct revised packet.
- **Utilization / construction:** final success on initially covered / initially uncovered tasks.
- **Readout loss:** a correct revised packet exists but the final answer is wrong. Coverage minus final accuracy is not this event count.
- **Pending correctness:** missing evaluator evidence, distinct from a malformed output already scored as failure.
- **GPU verified:** evidence for the returned configuration, not every hardware/runtime combination.
- **Implemented:** code exists; it does not mean that every training objective or proposed experiment has been executed.

Task IDs/groups are the sampling units. Calls, actors, replay branches and attack conditions within a task are correlated. Cross-benchmark results are a vector of development findings, not a pooled causal estimate or official leaderboard.

## 2. What has been implemented

| Component | Current evidence |
|---|---|
| Three-agent private packets, synchronous delivery/revision, frozen readout | CPU tests and audited GPU traces |
| Early/exchange attacks and archive/control baselines | Real validation-pilot evidence |
| Private counterfactual continuation replay | Eligible natural cases and saved controlled payloads audited |
| Continuation-credit estimator, responsibility solver, specialization objectives | CPU/mock and tiny neural validation; no real specialization optimizer updates |
| Clean-answer adapter preparation | Two completed GPU recipes |
| Supervised receiver objective; frozen/task-SFT/receiver-SFT arms | Completed controlled focal-adapter comparison |
| Original DPO branch | Optional implementation retained; no demonstrated successful end-to-end DPO learning result |
| Official benchmark loaders, frozen splits, exposure tracking | CPU validation and audited returned cohorts |
| Heterogeneous Q/L/M inference with common Qwen3 readout | Completed exposed ARC/LogiQA study and breadth results below |
| Private/sanitized bundles, source/model provenance, resume guards | Exercised on returned runs; unsafe recovery remains blocked |
| Isolated code/native scoring | Implemented; local and Colab capability probes failed for MBPP |
| Joint full PACT refreshes, specialization efficacy, matched final evaluation | Deferred/unexecuted |
| Adaptive attacks, executable tool-transfer study, final-test results | Unexecuted |

The implementation follows the local CPU development → user review/commit/push → pinned Colab run → imported-bundle audit workflow. Labels and evaluator metadata remain outside defender inputs. Synthetic donors are explicitly labeled and never represented as natural trajectories.

## 3. Historical experiment inventory

The following distinct executions precede the benchmark breadth extension. Re-exported ZIPs, restored snapshots and smoke prefixes are not counted again.

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

These historical findings are detailed below and in the original per-run reviews. Totals through the heterogeneous diagnostic were 16,165 recorded generations plus up to 16 unaccounted controlled-child calls. Breadth adds 10,206, giving **26,371 recorded generation calls plus the unchanged up-to-16 historical unknown calls**.

Executed optimizer updates remain **147**: 9 small preparation + 90 fresh larger preparation + 24 task-SFT + 24 receiver-SFT. These are separate recipes, not 147 sequential updates to one model. No specialization or breadth optimizer update was executed.

## 4. Historical findings carried forward

The subsections below retain the previously audited results. They are not fresh model reproductions.

### Validation pilot

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

### Why we changed the receiver learning recipe

The original receiver preference recipe required both a correct and a valid incorrect completion under the same prompt. The small bank produced no correct receiver candidates; the broader screen produced only correct candidates. Neither supplied preference pairs. Helpful curated peers improved one task, but comparisons across different prompts cannot create same-prompt DPO pairs.

Receiver supervision removed that sampling prerequisite: an official label supplies the answer-bearing output prefix, while the full receiver prompt remains the input. No invented gold rationale is required. Hold and repair strata receive balanced loss, and missing support stops the study rather than silently reallocating weight.

The first natural source collection still failed a different prerequisite: legitimate contexts. Fit hold/repair support was 2/2 tasks against minima of 8/8; held-out support was 0/1 against minima of 4/4. An offline inventory found no same-task donors among 950 distinct retained historical call/raw identities. No training occurred in that run. [Collection audit](../reviews/qwen3-receiver-supervision-001.md).

The subsequent controlled child explicitly allowed offline answer-conditioned synthetic peer donors. It preserved original focal states and separate synthetic/natural claims. This enabled actual receiver training, with the results below.

### Completed controlled receiver comparison

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

### Preparation controls and precision history

Moving from the 12-task preparation to the fresh 120-task preparation did not improve matched private correctness: **45/72 → 45/72**. Fixed-history receiver correctness remained **8/32 → 8/32**. The answer-only prompt control also retained 45/72 correct. The earlier 46/72 baseline used a different seed and is not the valid matched comparison. The prompt diagnostic is complete and was not substituted into the main packet protocol.

The controlled receiver study exposed nonfocal adapter loading through FP32 → BF16 → FP32. Reported unchanged checks after loading did not prove preservation of original export values. Recovery explicitly matched the effective initialization and retained that history for subsequent GPQA and specialization studies; it did not silently restore original FP32 values or rerun training. Local audits checked receipts and available payloads, not omitted real checkpoint tensors. [Training and recovery audit](../reviews/qwen3-receiver-supervision-controlled-001-training.md).

### Original GPQA Diamond support — preparation adapters

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

### Specialization studies

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

## 5. Completed heterogeneous ARC/LogiQA diagnostic

Fresh Qwen2.5-7B-Instruct (Q), Llama-3.1-8B-Instruct (L), and Mistral-7B-Instruct-v0.3 (M) supplied three private samples each. QQQ/LLL/MMM and QLM reused the same nine-packet bank with fixed balanced bindings. The common unadapted readout was non-thinking Qwen3-8B. This study used 80 explicitly exposed pilot tasks: 40 ARC Challenge and 40 LogiQA. It did not reuse preparation adapters or evaluate untouched final-test data.

| Team | Initial coverage | Valid mixed support | Vote | Synthesis | Post-exchange |
|---|---:|---:|---:|---:|---:|
| QQQ | 45/80 | 2/80 | 44/80 | 46/80 | 45/80 |
| LLL | 49/80 | 14/80 | 39/80 | 42/80 | 44/80 |
| MMM | 34/80 | 7/80 | 32/80 | 32/80 | 31/80 |
| QLM | 63/80 | 47/80 | 36/80 | 43/80 | 40/80 |

Shared task-only readout: 41/80. QLM's extra coverage did not translate into a final advantage. Its synthesis-to-exchange change comprised three gains and six losses: −3.75 percentage points, reported paired stratified bootstrap interval [−11.25,+3.75].

QLM hold was 61/67 eligible receiver opportunities; repair 12/69; erasure 3/63 initially covered tasks; utilization 39/63; construction 1/17; revised readout loss 22/80. Surviving correct information can therefore still fail at final readout. These are descriptive mechanisms, not an identified training remedy.

Completed accounting: 2,400 calls, 476,160 reserved output tokens, zero unresolved and zero optimizer updates. The wrapper bug before the first attempted smoke was fixed with a recorded zero-call source transition; the completed run's source was 874b3b184c6cdcde6c27368621d7747fd6e01467. See the [6 October audit](PACT_PROJECT_AUDIT_2026-10-06.md) for exact hashes, task-level interpretation and earlier test limitations.

## 6. Benchmark breadth design and disposition

The breadth studies reuse pristine official Q/L/M/R identities, native tokenizers/templates, BF16/SDPA, one resident model at a time and no adapters. Packet sampling uses temperature 0.7, top-p 0.8 and top-k 20; readout is deterministic. Context/output caps are dataset-specific and frozen.

Phase A has nine private calls/task. Separately invoked Phase B for the four core datasets has twelve revisions, four initial syntheses, four revised readouts and one shared task-only readout/task. All tasks participate, not just those with positive support. Smoke calls are included prefixes, not extra examples.

| Dataset | Frozen characterization allocation | Current execution | Correctness status |
|---|---|---|---|
| MMLU-Pro | 140; ten per category | A/B complete, 4,200 calls | All scored |
| MuSR | 90; thirty per domain | A/B complete, 2,700 calls | All scored |
| MATH-500 | 100; subject/level quotas | A/B complete, 3,000 calls | All scored with pinned Math-Verify |
| New GPQA | 32; Biology 3 / Chemistry 15 / Physics 14 | A complete, 288 calls; B not authorized | All scored |
| MBPP+ | 100 allocated; only two smoke tasks generated | 18 calls; full A/B deferred | Six malformed failures, twelve pending |
| LiveBench | Planned 100-item release-locked slice | No generation; blocked | No scientific result |

New GPQA is distinct from the original 32-task frozen-preparation study. The new selection is disjoint from the original exposed 32, and comes from its former 164-task protected pool under the explicit new allocation. The original two source-integrity exclusions remain excluded.

MBPP+ and LiveBench limits were not reassigned to other datasets. The entire six-dataset portfolio is **not complete**.

### 6.1 Private correct-answer availability

All figures are counts on the dataset denominator; QQQ/LLL/MMM mean three sampled packets from the corresponding family.

| Dataset | Tasks | QQQ coverage | LLL coverage | MMM coverage | QLM coverage | QLM gain over its best member | QLM valid mixed support |
|---|---:|---:|---:|---:|---:|---:|---:|
| MMLU-Pro | 140 | 40 | 46 | 38 | 61 | 25 | 42 |
| MuSR | 90 | 50 | 53 | 41 | 62 | 17 | 38 |
| MATH-500 | 100 | 84 | 39 | 22 | 74 | 1 | 56 |
| New GPQA | 32 | 9 | 11 | 13 | 16 | 7 | 12 |

Heterogeneity improves observed coverage over each homogeneous team on MMLU-Pro and MuSR. On MATH-500, QLM is below QQQ by ten tasks and adds only one task beyond its own Q member. Thus plentiful valid mixed support is not equivalent to useful additional coverage. On new GPQA, QLM has the largest point estimate, but small-sample uncertainty prevents a general superiority claim.

GPQA majority voting succeeds on QQQ 9/32, LLL 4/32, MMM 10/32 and QLM 5/32. The mixed team's 16-task coverage does not imply a usable 16-task final accuracy. There is no synthesis or exchange measurement for this new cohort.

Reported QLM coverage difference intervals, in percentage points:

| Dataset | Versus QQQ | Versus LLL | Versus MMM |
|---|---|---|---|
| MMLU-Pro | +15.00 [8.57,22.14] | +10.71 [4.29,17.14] | +16.43 [10.00,22.86] |
| MuSR | +13.33 [6.67,21.11] | +10.00 [1.11,18.89] | +23.33 [13.33,33.33] |
| MATH-500 | −10.00 [−16,−5] | +35.00 [27,43] | +52.00 [44,60] |
| New GPQA | +21.875 [3.125,40.625] | +15.625 [−3.125,34.375] | +9.375 [0,21.875] |

These are stored paired within-stratum group-bootstrap intervals, not multiple-comparison-adjusted confirmation claims. MMLU/MuSR use the balanced category/domain aggregation; MATH/GPQA use the selected micro allocation. GPQA Biology has only three selected tasks.

### 6.2 Completed communication comparisons

Cells show **private synthesis → post-exchange readout**, correct tasks.

| Dataset | QQQ | LLL | MMM | QLM | Shared task-only |
|---|---|---|---|---|---|
| MMLU-Pro (140) | 42 → 43 | 42 → 38 | 32 → 32 | 40 → 43 | 35 |
| MuSR (90) | 48 → 47 | 46 → 46 | 38 → 35 | 45 → 46 | 52 |
| MATH-500 (100) | 79 → 80 | 73 → 74 | 64 → 59 | 81 → 77 | 74 |

There is one task-only control per task, reused across comparisons. QLM does not exceed QQQ's post-exchange point estimate in any of these three studies. This is not proof that heterogeneity is universally inferior.

For QLM's paired synthesis-to-exchange contrast:

| Dataset | Gains | Regressions | Net correct tasks | Difference pp, reported interval |
|---|---:|---:|---:|---|
| MMLU-Pro | 5 | 2 | +3 | +2.14 [−1.43,+5.71] |
| MuSR | 2 | 1 | +1 | +1.11 [−2.22,+5.56] |
| MATH-500 | 0 | 4 | −4 | −4.00 [−7,−1] |

On MATH, private QLM synthesis has the highest point estimate among the four teams (81/100), but exchange worsens four tasks without improving any. On MuSR, task-only exceeds all reported team synthesis/exchange arms. Neither observation establishes which intervention would improve PACT.

### 6.3 Preservation and readout: QLM

| Dataset | Initial / revised coverage | Erasure | New revised availability | Hold | Repair | Utilization | Construction | Revised readout-loss events |
|---|---|---|---|---|---|---|---|---|
| MMLU-Pro | 61 / 59 | 11/61 | 9/79 | 44/55 | 10/63 | 38/61 | 5/79 | 16/140 |
| MuSR | 62 / 57 | 5/62 | 0/28 | 50/58 | 6/55 | 46/62 | 0/28 | 11/90 |
| MATH-500 | 74 / 74 | 2/74 | 2/26 | 70/74 | 17/63 | 70/74 | 7/26 | 3/100 |

Hold/repair denominators are eligible receiver opportunities, not independent tasks. Construction here is final success without any initially correct actor. It differs from the final readout independently supplying a correct answer when no revised actor is correct.

This distinction is important in math: LLL and MMM have only 39 and 22 initially covered tasks but final accuracies 74 and 59. Final-readout construction with no correct revised packet occurs on 21 LLL tasks and 43 MMM tasks. The strong common readout contributes substantial independent solving; these counts cannot all be described as successful use of peer knowledge.

### 6.4 Output failures and missingness

| Dataset / observed scope | Parse ok | Abstention | Malformed | Invalid MCQ answer | Length-limited | Correctness pending |
|---|---:|---:|---:|---:|---:|---:|
| MMLU-Pro A/B | 3,701 | 390 | 66 | 15 | 28 | 0 |
| MuSR A/B | 2,540 | 112 | 23 | 25 | 0 | 0 |
| MATH-500 A/B | 2,311 | N/A | 446 | N/A | 243 | 0 |
| New GPQA A | 227 | 42 | 5 | 0 | 14 | 0 |
| MBPP+ smoke | 12 | N/A | 6 | N/A | 0 | 12 |

Pending overlaps with parse-ok in MBPP; it is not an additional generated response count. All malformed/abstaining/invalid/length-limited outputs remain failures under the frozen contract. They are not dropped from the task denominator. Infrastructure missingness is zero in the completed scored breadth runs.

MATH Phase A alone has Q 273/1/26, L 114/133/53 and M 235/56/9 responses in ok/malformed/length categories. Format failures therefore materially constrain interpretation of family comparisons. No post-hoc parser, larger output cap or replacement seed was applied to rescue outcomes.

## 7. Blocked work and recovery incidents

### MBPP+

All eighteen smoke calls are retained. Q and L each produced six valid-format responses, but validity is not correctness. M's six malformed responses are failures. The twelve valid-format programs await official base-plus-expanded EvalPlus tests.

The local host and Colab both failed the required isolation probe. The local trusted diagnostic reported that Bubblewrap could not create a namespace; the Colab returned safe_execution_unavailable without exposing the underlying cause. No generated program was executed outside the required boundary. The user accepted deferral; neither 882 remaining private calls nor 2,100 Phase B calls were launched.

The private scoring jobs are preserved. A capable dedicated Linux evaluator, passing the existing probe and official evaluator validation, is required to resume. No passing sandbox receipt or successful EvalPlus result is claimed.

### LiveBench

The existing pinned public inventories do not establish the requested 2026-06-25 slice. Several inspected category inventories contain older release dates; the first missing category blocks the intended slice. The loader's conservative proof rule may reject a legitimate retained-only category until authoritative release evidence is reviewed.

This audit does not assert that the requested release is unavailable everywhere today: no fresh upstream search was conducted. Under the frozen sources and proof requirements, the study remains blocked. No older release, mirror or fabricated membership date was substituted. Native isolated scoring is an additional prerequisite.

### GPQA parent-policy fix and final recovery

The breadth loader initially reconstructed the original parent using a minimal default exposure policy, while the original CLI had saved the full reviewed policy metadata. Exact manifest comparison therefore rejected preparation. The fix reconstructs with the recorded policy only when it matches the reviewed repository policy or historical minimal empty policy, and still requires exact partition equality and 32/164/2 accounting. Tests cover policy and selected/protected/excluded-ID tampering.

The user pushed the fix as 1ae086239f9b6a85fb3a0673715e68d425baf228 before freezing the new child. Completed earlier studies were not migrated.

A later Colab reset appeared to stop at call 267 in the visible output. The latest verified Drive snapshot instead had 288 intents, 288 results and 288 scores with recovery_safe=true, plus completed exports. The final imported bundle audit confirmed completion. No lost-call replay or budget expansion was required.

By contrast, the earlier controlled specialization recovery remains unsafe/incomplete. The successful GPQA recovery does not retroactively repair that history.

## 8. Accounting and experimental boundaries

Latest breadth returns, counting each dataset once:

| Dataset | Generation calls | Reserved output tokens | Actual input tokens | Actual output tokens | Updates |
|---|---:|---:|---:|---:|---:|
| MMLU-Pro | 4,200 | 1,585,920 | 2,223,136 | 228,833 | 0 |
| MuSR | 2,700 | 1,019,520 | 3,510,679 | 149,131 | 0 |
| MATH-500 | 3,000 | 3,072,000 | 3,523,618 | 1,343,727 | 0 |
| New GPQA | 288 | 73,728 | 94,338 | 32,827 | 0 |
| MBPP+ smoke | 18 | 18,432 | 2,742 | 2,886 | 0 |
| **Observed breadth total** | **10,206** | **5,769,600** | **9,354,513** | **1,757,404** | **0** |

Zero unresolved generation attempts in these returns does not mean zero missing correctness: twelve MBPP scores remain pending. Compute units/costs are not supplied, and reserved output tokens are ceilings, not billed tokens. These counts omit scoring CPU work and are not sample sizes.

Project-wide historical recorded generations are 26,371 plus up to sixteen unknown controlled-child calls. Historical updates remain 147 across separate training recipes. The original 14,088-call breadth portfolio ceiling was not fully consumed; unused blocked-study allocations are not transferable.

All selected benchmark cohorts are development-exposed. Confirmation/reserve allocations stay locked; no final-test evaluation was authorized. Official split names such as a benchmark's “test” split do not make the selected development cohort an untouched project final test.

Exact/source-hash and lexical grouping/exposure checks do not establish semantic decontamination or absence of pretraining contamination. Historical ARC/LogiQA, original GPQA and new GPQA configurations are not interchangeable causal controls.

## 9. Audit provenance

The latest archived views are paired PRIVATE/SANITIZED exports. PRIVATE files contain gated/raw task material, prompts, continuations, scoring jobs or decodable token arrays; keep them out of Git/public outputs. This report contains aggregates and hashes only.

| Dataset | Latest bundle suffix | Frozen plan |
|---|---|---|
| MMLU-Pro | 1791270113690429538 | 516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9 |
| MuSR | 1791278710347362192 | a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae |
| MATH-500 | 1791412685067931571 | e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6 |
| MBPP+ smoke | 1791443310313931697 | 72a10bbf296c6210cc5645ceeacc520dd15f6dfe8409e2d8217f8a890a3c0ae9 |
| New GPQA | 1791449632230724762 | 28798ee286711224cc311de51212dd3efce7074a944cb32c6bef7a3f291fdadf |

MMLU/MuSR/MATH/MBPP use source 7185b0c4bda278edabfbe45865d922844bf206d6; new GPQA uses the parent-policy fix at 1ae086239f9b6a85fb3a0673715e68d425baf228. Uncommitted audit documentation does not change those recorded run identities.

| Dataset | PRIVATE SHA256 | SANITIZED SHA256 |
|---|---|---|
| MMLU-Pro | 7e15746dbc7832dda3c5698e86737af66d806f25954ce1fc5910844e5b521bad | c6cf9b5a087ef4610a986e823d3d5dde6bb1353c66d40994bacdf1fb92f4b2e6 |
| MuSR | 1eaa5a5a04f4feb2405ae29ff17c90c831886691ea060ee69fe978025f44dd57 | 298082b20be17a51e40059a5281eb8f3625cca6bd6f0739b0ff010902a8ca4a6 |
| MATH-500 | 0cb8d640bf6b039df046fafdb7d1785fc0ef23dabedea082cd8d42f15c72f748 | b41f2624fd012dbf09282a3b83627803151f87b197b162fb7568efa17d8804d1 |
| MBPP+ smoke | dcb4f4c773535954302bd35722d70e0012d723d687bc5269a238651c0bc131ad | 5f6bcf971498b8ac79820707fac0385e14dc76388979991a06c4f436c4464aae |
| New GPQA | 4608b1f93fcf5024af0188360f462bbe04e7026672b51ea66fdc59b728bfcd05 | c7081743e994bdc37a55b4254cf7ba7f35393bc62f5971c25c436f996987c04f |

MBPP scoring_jobs.json SHA256: 7dd3a06259562aadbf4d5c5bc365e58ed4d2bbed329eb2a121a83d83e266401f.

At import, ZIP/internal hashes, frozen identities, request/dependency reconstruction, reports and private/sanitized summary agreement were checked. Smoke and Phase A artifacts were compared against later returns to ensure preservation. MMLU, MuSR and new GPQA MCQ scores independently reproduced. MATH A and B were independently rescored using the pinned Math-Verify source/dependencies; only cross-host timing/environment metadata were excluded from score equality. MBPP classifications and job identities reproduced, not program correctness.

These audits verify internal consistency and rescoring, not independent reproduction of model generations or authenticity beyond the supplied artifacts.

## 10. Software verification and limits

Historical validation evidence includes:

- Full breadth-era CPU suite: 265 tests, 248 passed, 17 optional skips, no failures/errors, with temporary fixtures outside Git. Earlier failed attempts are recorded rather than erased.
- Focused breadth validation with pinned math runtime: 25 tests, 23 passed, two isolated-runtime skips.
- GPQA parent-policy fix: 25 tests, 22 passed, three optional runtime skips; partition/policy tampering guards remain active.
- Actual returned GPU evidence now covers completed heterogeneous, MMLU, MuSR, MATH and new GPQA paths and MBPP smoke generation/export.
- Real isolated EvalPlus/native execution remains unverified.

For this report, historical findings were carried forward from linked audits and the ledger; latest breadth tables/accounting were checked against reconstructed summaries. No new GPU inference, training, generated-program execution, model download or full regression rerun was performed. Report links, arithmetic and repository whitespace checks are separate documentation validation, not scientific tests.

Storage deadline changes, local-first bundles and compact snapshots improved recoverability but do not permit unsafe replay. The controlled-child closure demonstrates the limits. Effective adapter precision history also remains part of the earlier trained comparisons and cannot be silently “fixed” by changing weights.

## 11. Findings for the audit decision

**Supported by current evidence**

1. The protocol, bounded training recipes and replay machinery operate on real data.
2. Same-prompt receiver preference pairs and natural specialization support can be scarce; controlled constructions enable engineering tests but change the estimand.
3. Receiver SFT changed answer-token likelihoods without an incremental matched receiver-correctness gain in its bounded comparison.
4. Heterogeneous families can add correct-answer coverage on several development cohorts, but not uniformly: QQQ beats QLM coverage on MATH.
5. Correct information can be erased or survive yet fail at readout. Communication did not deliver a consistent heterogeneous final-answer advantage.
6. Strong common readouts can solve tasks independently of correct peer packets, so terminal success alone does not prove useful communication.

**Not established**

- Full PACT efficacy or improved adversarial robustness from training.
- Successful real specialization learning or an advantage for continuation-credit assignments over simpler controls.
- A general superiority of heterogeneous teams, debate or receiver SFT.
- MBPP code correctness, the requested LiveBench result or untouched final-test performance.
- An independently confirmed causal remedy for the observed failure modes.

**Disposition**

Retain completed results, keep controlled specialization closed incomplete, and keep MBPP/LiveBench blockers explicit. New GPQA Phase B remains unapproved: the discussed 672-call / 116,736-reserved-token extension was only a proposal and has not been added to the plan. Do not rerun completed diagnostics, enlarge cohorts/seeds, alter output contracts or fill manuscript placeholders based on this report.

The review should decide whether the next scientific target is receiver repair, final readout selection or learned actor specialization. Each would require its own explicit comparison, exposure treatment and bounded budget. This document selects no intervention and authorizes no run.
