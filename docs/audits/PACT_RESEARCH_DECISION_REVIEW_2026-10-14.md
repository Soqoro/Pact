# PACT research decision review — 14 October 2026

## Decision summary

PACT now has an implemented research pipeline, executed adapter-training experiments, and completed development diagnostics of private-answer availability, communication and adjudication. **Full PACT efficacy has not been demonstrated.** The strongest current evidence is that correct peer information can be available and sometimes rescue a judge, while revision and final decision-making also cause enough regressions to offset those gains.

The immediate decision is which failure to target next, not whether to scale the existing training recipe. My recommendation is to prioritize a separately designed comparison of **preserving an independent answer while selectively using peer evidence**. This is a hypothesis for review, not an implemented remedy, approved experiment or claim of improvement. The current evidence does not justify proceeding directly to full joint PACT training.

Independent human semantic review and the optional cue/sham span intervention remain **deferred at the user's request**. This report does not reactivate them or authorize replacement work. No Colab execution is needed for this review.

## Scope and evidence basis

This is a synthesis of existing repository audits and recorded experiment status, not a fresh raw-archive audit or replication of model generation. Detailed provenance, hashes, methods and uncertainty are retained in:

- [Historical project audit, 30 September](PACT_PROJECT_AUDIT_2026-09-30.md).
- [Heterogeneity and earlier work, 6 October](PACT_PROJECT_AUDIT_2026-10-06.md).
- [Consolidated breadth audit, 11 October](PACT_PROJECT_AUDIT_2026-10-11.md).
- [Completed adjudication audit, 13 October](PACT_ADJUDICATION_COMPLETE_2026-10-13.md).
- [Offline semantic-forensics audit, 14 October](PACT_SEMANTIC_FORENSICS_2026-10-14.md).
- [Experiment ledger](../experiment_ledger.md) and [implementation status](../implementation_status.md).

All reported scientific outcomes are development findings. Selected tasks have been exposed; they are not untouched confirmation data. Different actors, prompts, caps and cohorts prevent pooling historical accuracies into a single effect estimate. Task groups, not calls or repeated variants, are the sampling units. Invalid outputs remain failures under their frozen contracts.

## 1. What has been done

| Workstream | Executed work | Current disposition |
|---|---|---|
| Protocol and early diagnostics | Smoke/profile/pilot, private packets, synchronous exchange, attacks and selected replay | Complete; infrastructure and descriptive evidence |
| Preparation training | Small 12-task recipe: 9 updates; larger 120-task recipe: 90 updates | Real training executed; matched probe correctness did not improve in the larger comparison |
| Receiver feasibility | Natural banks, base/private controls, curated repair and prompt diagnostic | Complete; same-prompt preference support was unreliable |
| Supervised receiver study | Natural context collection, then explicitly synthetic controlled donors; 24 task-SFT and 24 receiver-SFT updates | Natural branch stopped for support; controlled comparison complete with no incremental receiver-correctness gain |
| Original GPQA support | 32 tasks, effective frozen preparation actors, 256 calls | Complete; only two mixed-support teams |
| Natural specialization | 32 fit tasks, 1,216 collection calls | Support stop before replay/training |
| Controlled specialization | 75 acquisition calls and 2,752 saved replay calls | Closed incomplete; unsafe recovery and missing calibration remain recorded |
| Heterogeneous pilot | 80 exposed ARC/LogiQA tasks, 2,400 calls | Complete |
| Benchmark breadth | MMLU-Pro, MuSR and MATH A/B; new GPQA A | Complete for those authorized scopes |
| MBPP+ / LiveBench | MBPP two-task smoke only; no LiveBench generation | MBPP isolated scoring unavailable; requested LiveBench release not established under pinned proof rules |
| Fixed-bank adjudication | 230 existing tasks; clean judges and accepted wrong-rationale variants | Complete, 5,340 calls, zero unresolved |
| Offline forensics | Judge-relative rescue/regression census and private review packages | Numerical analysis complete; no actual semantic reviews |
| Human review / span intervention | Blank reviewer packages exported; optional child implemented and CPU-tested | Deferred; no real span inference; child GPU behavior unverified |

Recorded historical generations through breadth were 26,371. Adding the completed adjudication study gives **31,711 recorded generations**, plus up to 16 unknown calls from the closed controlled-specialization incident. This is carried-forward accounting, not an independent sample size or billing estimate. There were **147 optimizer updates across separate recipes** (9 + 90 + 24 + 24), not one 147-step trained model. Offline forensics added no model calls.

## 2. Does useful private diversity exist?

Coverage means at least one team member supplied a correct answer. Valid mixed support requires both a valid correct and a valid wrong answer. Wrong-answer disagreement alone does not establish complementarity.

The heterogeneous studies use Qwen2.5, Llama3.1 and Mistral private actors, denoted Q/L/M. QQQ, LLL and MMM are three packets from one family; QLM combines families. These differ from the earlier adapted Qwen3 preparation actors.

| Development cohort | Tasks | QQQ coverage | LLL coverage | MMM coverage | QLM coverage | QLM valid mixed support |
|---|---:|---:|---:|---:|---:|---:|
| ARC/LogiQA pilot | 80 | 45 | 49 | 34 | 63 | 47 |
| MMLU-Pro | 140 | 40 | 46 | 38 | 61 | 42 |
| MuSR | 90 | 50 | 53 | 41 | 62 | 38 |
| MATH-500 | 100 | 84 | 39 | 22 | 74 | 56 |
| New GPQA | 32 | 9 | 11 | 13 | 16 | 12 |

Heterogeneity added coverage on several cohorts, but not uniformly. On MATH, QLM covered ten fewer tasks than QQQ and only one more than its own best member. Its 56 mixed-support tasks therefore do not imply a large complementary advantage. New GPQA QLM majority voting was only 5/32 despite coverage of 16/32; Phase B is unapproved and unexecuted.

The **original** 32-task GPQA study is separate: individual accuracies were 9/32, 7/32 and 7/32; coverage was 9/32; only two teams had valid mixed support. Initial correct-count distribution N0=0/1/2/3 was 23/2/0/7. Both mixed teams lost their sole correct packet during exchange, and all four eligible repair opportunities failed. Voting, initial synthesis and final debate each scored 7/32. A harder benchmark alone did not supply useful diversity for those actors.

## 3. Does communication use or preserve that diversity?

These are matched initial-packet synthesis → post-exchange readout outcomes. The breadth common readout and adjudication judges below have different output contracts; they are not interchangeable controls.

| Cohort | QQQ | LLL | MMM | QLM | Task-only |
|---|---|---|---|---|---:|
| ARC/LogiQA /80 | 46 → 45 | 42 → 44 | 32 → 31 | 43 → 40 | 41 |
| MMLU-Pro /140 | 42 → 43 | 42 → 38 | 32 → 32 | 40 → 43 | 35 |
| MuSR /90 | 48 → 47 | 46 → 46 | 38 → 35 | 45 → 46 | 52 |
| MATH-500 /100 | 79 → 80 | 73 → 74 | 64 → 59 | 81 → 77 | 74 |

QLM exchange had 3 gains/6 losses on the pilot, 5/2 on MMLU, 2/1 on MuSR and 0/4 on MATH. The reported paired MATH change was −4 percentage points, interval [−7, −1]; the other three intervals included zero. These are exploratory development comparisons, not multiplicity-adjusted confirmation.

There are two distinct failure locations:

| QLM cohort | Initially covered tasks losing all correct revised packets | Final failure despite correct revised availability |
|---|---:|---:|
| ARC/LogiQA | 3/63 | 22/80 |
| MMLU-Pro | 11/61 | 16/140 |
| MuSR | 5/62 | 11/90 |
| MATH-500 | 2/74 | 3/100 |

The second column measures erasure; the third measures readout-loss events over all tasks. Neither is interchangeable with net accuracy change: new correct answers may also appear.

Final success also need not reflect useful peer information. On MATH, the common readout produced correct final answers without any correct revised packet on 21 LLL tasks and 43 MMM tasks. Independent solving by the readout is therefore a material contributor.

## 4. What did fixed-bank adjudication establish?

This study reused the completed 140 MMLU and 90 MuSR tasks and original private candidates. It changed adjudication, not proposer training or packet generation. J8/J14 were pristine, non-thinking judges with fixed 512-output/8192-context limits.

| Clean mode | MMLU J8 /140 | MMLU J14 /140 | MuSR J8 /90 | MuSR J14 /90 |
|---|---:|---:|---:|---:|
| Task-only free answer | 58 | 63 | 50 | 51 |
| QLM answers-only selection | 42 | 43 | 45 | 38 |
| QLM full-packet selection | 45 | 43 | 48 | 49 |
| QLM evidence selection | 42 | 37 | 47 | 43 |
| QLM free synthesis | 49 | 53 | 48 | 50 |
| QQQ full-packet selection | 34 | 30 | 48 | 47 |

Task-only had the highest point estimate in all four blocks. This does not establish every paired difference, and all reported clean J8-to-J14 intervals included zero. Larger judges did not consistently solve the selection problem.

### Rescue exists despite negative net effects

An opportunity is a task where that judge was independently wrong but QLM contained a selectable correct answer. Regression is failure on a task where that judge was independently correct.

| Full-packet selection | Peer rescues / opportunities | Regressions / independently correct | Structural losses within regressions | Net correct vs task-only |
|---|---:|---:|---:|---:|
| MMLU J8 | 15/25 | 28/58 | 22 | −13 |
| MMLU J14 | 12/24 | 32/63 | 26 | −20 |
| MuSR J8 | 13/19 | 15/50 | 7 | −2 |
| MuSR J14 | 10/17 | 12/51 | 6 | −2 |

Structural losses occur when the independently correct answer is absent from the selectable bank: a constrained selector cannot output it. Other losses occur even with correct candidate availability. Thus these results support examining preservation of an independent answer, but do not prove a deployable routing rule. Correctness-based oracle routing is unavailable at inference.

Free synthesis avoids that strict answer-space restriction but still regresses. Its net changes were −9, −10, −2 and −1 tasks in the four blocks, respectively. A preservation mechanism must address more than selector constraints.

### Rationale rewriting can change decisions

All 400 one-attempt rewrites were acquired before victim evaluation; 369 were accepted and 31 rejected. All 2,214 accepted victim calls completed. Rejected variants produce 186 unavailable slots, not work to retry. Together with 34 no-call empty-bank clean failures, this explains why the complete study used 5,340 of its 5,560-call ceiling.

Wrong-candidate justification edits preserved the correct candidate packets and coverage. In MuSR/J14 full selection, claimed-consensus rewrites flipped 17/25 clean-correct answers to valid wrong answers: 14 lost independent correctness and three lost a prior peer rescue. Ordinary rephrasing also caused losses.

On the 36 tasks available for both styles, consensus correctness was 12 tasks lower than ordinary rephrase (−33.3 points; exploratory unadjusted interval [−50, −16.7]). This supports sensitivity to the tested rewrites. It does **not** isolate a causal social cue: schema acceptance does not establish semantic equivalence, and actual independent semantic reviews have not been performed.

## 5. What has training shown?

The original receiver preference path required both correct and wrong completions under one receiver prompt. Feasibility failed in opposite ways: the small base control had 0/24 correct receiver candidates, while a broader screen had 136/136 correct candidates and no valid wrong alternative.

The supervised update removed that sampling prerequisite. Official training labels supplied answer-prefix targets under the unchanged receiver input, with DPO disabled. Natural context support still failed: fit hold/repair counts were 2/2 against required 8/8, and held-out counts 0/1 against 4/4. That branch correctly stopped without training.

The separately controlled donor study used explicitly synthetic, offline label-conditioned donors. It executed 24 focal-adapter updates per arm:

| Matched outcome | Frozen initialization | Task SFT | Receiver SFT |
|---|---:|---:|---:|
| Hold with wrong donor | 13/13 | 13/13 | 13/13 |
| Repair with correct donor | 1/6 | 1/6 | 1/6 |
| Repair with peers withheld | 0/6 | 0/6 | 0/6 |
| Private-answer checks | 20/32 | 21/32 | 21/32 |
| Natural-team clean | 5/8 | 5/8 | 4/8 |
| Natural-team exchange | 4/8 | 4/8 | 5/8 |

All 57 matched receiver responses retained the same correctness across arms: 40 correct, 17 wrong. Repair target NLL decreased from 11.3762 to 8.3008 to 6.3415, but correctness did not improve; peer-withheld loss also decreased. Training operated, but this is not demonstrated receiver efficacy. Six repair tasks and one seed cannot establish equivalence or impossibility.

Historical nonfocal FP32→BF16→FP32 rounding was detected and explicitly matched by effective-initialization recovery. It was not silently repaired. These effective identities remain part of the comparison.

Natural specialization found five eligible cells on only two supported tasks, below its eight-task requirement. Controlled replay had 125/132 zero primary cell effects, seven nonzero cells across six tasks, and only four of five calibration cells. Its unsafe interruption was closed incomplete. Missing scoring/global assignment evidence means **assignment contrast was not evaluated**, rather than shown ineffective. No specialization training or all-agent joint PACT refresh was executed.

## 6. Established findings and unresolved questions

**Supported within the recorded development settings:**

1. The real protocol, bounded adapter training and artifact/replay machinery operate.
2. Correct-answer diversity varies by actors and dataset; disagreement is an inadequate proxy.
3. Communication can repair answers and erase correct information; surviving information can still be lost at readout.
4. Peer rescue is real in the judge-relative census, even where regressions make net accuracy negative.
5. The tested wrong-rationale rewrites can redirect decisions without removing correct candidates.
6. Executed receiver SFT reduced target loss without incremental matched receiver correctness.

**Still unresolved:** whether a feasible preservation rule can retain rescue while reducing regression; whether rationale semantics or specific cues explain rewrite effects; whether specialization assignments deliver useful learning; whether any learned PACT method beats matched alternatives on fresh confirmation tasks.

No evidence here establishes full PACT efficacy, a successful trained defense, adaptive worst-case robustness, general superiority of heterogeneous teams, semantic decontamination, MBPP correctness or final-test performance. Paper result placeholders remain unfilled.

## 7. Options for the next decision — none authorized by this report

| Option | Why consider it | Required distinction before execution |
|---|---|---|
| Independent-answer preservation with selective peer use | Directly targets observed rescue/regression tradeoff and structural selector losses | Separately specified mechanism; task-only, independent reconsideration and existing peer baselines; matched compute and answer space; report rescue and regression separately |
| Another receiver-training study | A real training path exists | Identify adequate support and a learnable target contract first; retain task-SFT and peer-withheld controls; do not merely expand the failed bounded recipe |
| Learned actor specialization / full PACT | Closest to the proposal's eventual objective | Establish usable assignment evidence and complete calibration before training; closed incomplete replay is not sufficient |
| More benchmarks or larger judges | Could test generality | Current results do not make this the first priority; new exposure, access and budget need explicit review |
| Semantic cue/sham intervention | Could address a narrower causal question | Remains deferred; two actual independent reviews, reviewed edits and separate artifact-bound approval are still prerequisites |

My preferred direction for a future design is the first row. The evidence motivates it, but does not specify an effective gate or predict success. Existing cohorts can inform development design; repeatedly inspected tasks cannot become untouched confirmation data. A fresh bounded plan would need to state its cohorts, budgets, uncertainty, failure handling and acceptance criteria before generation.

MBPP+ remains deferred until the required isolation capability exists. LiveBench remains blocked under the recorded release-proof rules. New GPQA Phase B remains unapproved. Completed diagnostics and the closed controlled replay should not be rerun to fill gaps in this review.

## 8. Validation and handoff

This change adds a documentation synthesis only. Existing audits, runs and private artifacts are unchanged. Table arithmetic, relative links and whitespace were checked; no model generation, training, scoring, downloads, semantic annotation or regression suite was run for this report. Earlier CPU-test and returned GPU evidence stays attributed to its original implementation/study in the linked status records.

Review the scientific priority before commissioning another implementation or Colab run. The human-review deferral remains in force.
