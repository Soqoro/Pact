# PACT project audit — 20 November 2026

### 21 November checkpoint lock

Job 1125084 completed in 10m05s with exit 0:0. The operator-supplied receipt records 11 locked teams, 30 verified trained adapter hashes, three verified S0 adapters and 12,834 verified prior events. The lock added zero generations, diagnostic scores, optimizer updates and training forwards. The job reported all 56 persistent files verified. The lock SHA256 is `50f2aaa21f9716eb2b85999a9b5045ab9c1a6be1ec703c4944c3da27d74fa387` and the RECOVERY bundle SHA256 is `9fc6268f6d44f28f92ec2c3fbf306606d8b96f650258040847a6615ef6d342b5`. Prospective accuracy remains unmeasured. The next decision covers the two-task evaluation smoke only.

### 21 November training completion update

Slurm job 1124778 completed in 17h57m38s with exit 0:0. Its receipt reports all 30 actor fits verified and durable exports complete. The final batch added 1,440 optimizer updates and 11,520 supervised forwards to the 1,440 updates verified at fit 15. Cumulative policy training totals are 2,880 updates and 23,040 supervised forwards. The continuation added zero generations and zero diagnostic scores. All five policies now have two trained teams. The next decision is checkpoint lock; prospective accuracy remains unmeasured.

The plan and policies hashes match the recorded freeze. The final SANITIZED archive is 8,730 bytes, SHA256 `a5049c02ef339b4ff3538fc43abe7d631b89ca0b9ed6e5230bf6db02ef94bad9`. The completion evidence reviewed here is the operator-supplied job output. The sections below describe the 20 November audit boundary.


**The strongest completed result is a Stage I clean-accuracy gain.** Joint receiver training improved equal-source final-answer accuracy by 5.98 percentage points over independent training on 256 development tasks. The attacked comparison also favored joint training, but its interval included zero. Holding private histories fixed showed that much of the clean advantage persisted when peers were withheld. We have evidence that the training choice mattered on this cohort. How much of the gain came specifically from learning to use peers remains unresolved.

**Stage II has produced a testable prediction.** Short updates to Mistral helped the team on accepted ARC attacks and hurt it on accepted LogiQA attacks. The frozen primary allocation consequently gives Mistral 20 of 36 extra ARC updates and only 2 of 60 extra LogiQA updates. Whether that allocation improves performance on different questions is the experiment still ahead.

**Latest verified execution boundary:** Slurm job 1124774 restored 15 of 30 actor fits and 1,440 of 2,880 policy updates. A continuation from fit 16 has been prepared. No later job output was available for this audit. There is no prospective policy accuracy result yet.

## 1. What has been built and tested

PACT investigates whether training an actor for its contribution to the final team decision can improve a communicating team's performance under misleading peer messages. Three actors first generate private answers. Their initial packets are frozen before exchange, each actor revises using its initial peers, and a common readout makes the final decision. The exchange intervention changes one outgoing message seen by both recipients. This design allows private-answer quality, revisions and the team answer to be measured separately.

| Workstream | What happened | What we learned |
|---|---|---|
| Pilot and replay | An 80-task pilot, paired replay infrastructure, warm start, training-bank collection and base controls were completed. | Early natural receiver-preference sampling yielded insufficient usable pairs. |
| Receiver supervision and specialization | Frozen, task-SFT and receiver-SFT arms were compared on 57 matched receiver responses. Natural and controlled specialization were also investigated. | All three receiver arms got 40/57 correct despite better repair-target loss. Natural specialization had support on only two tasks. Interrupted controlled replay left the assignment contrast unresolved. |
| Heterogeneous teams and benchmark breadth | Qwen, Llama and Mistral were compared across development cohorts. | Initial synthesis to final exchange readout moved from 43 to 40 correct on the 80-task ARC/LogiQA pilot, 40 to 43 on 140 MMLU-Pro tasks, 45 to 46 on 90 MuSR tasks, and 81 to 77 on 100 MATH tasks. Communication could help or hurt depending on the source. |
| Adjudication and selective correction | The fixed-bank adjudication study completed 5,340 calls. Wrong-rationale sensitivity, five CPU correction gates and a paired 404-call selector clarification were studied. | Peer-based selection rescued some answers and regressed on others. All five gates chose KEEP_ONLY. Selector clarification improved format compliance but produced only one clean rescue. Independent semantic review was deferred. |
| Heterogeneous training and Stage I | Independent adversarial SFT and uniform joint SFT were completed for Qwen, Llama and Mistral. Each of six fits reached 128 committed updates on the amended path. | This supplied both a matched comparison and the three joint-trained adapters, collectively S0, from which every Stage II fit starts. |

Earlier cohort sizes, models and prompts differ. A single pooled accuracy across these studies would have no common denominator. [Earlier project audit](PACT_PROJECT_REVIEW_2026-11-02.md) · [Stage I training completion](../revival_continuation_completion_audit.md)

## 2. Stage I results and their limits

The amended evaluation completed 13,467 generation calls. Its validation, source evaluation and fixed-history diagnostic answer different questions. The validation clean joint-minus-independent difference was zero. On the separate 256-task source cohort (120 ARC and 136 LogiQA), joint training produced 35 paired clean gains and 19 losses. The net gain was two answers on ARC and fourteen on LogiQA. Equal-source weighting gives each source half the weight.

| Source-evaluation comparison, joint minus independent | Paired groups | Equal-source final accuracy difference | Descriptive bootstrap interval |
|---|---:|---:|---:|
| Clean | 256 | +5.98 pp | +1.17 to +11.77 pp |
| Accepted exchange attack | 205 | +4.56 pp | −2.39 to +12.37 pp |

The exchange estimate covers attacks that were accepted. Across all 256 intended groups, missing-outcome bounds extend from −16.27 to +23.58 points. The data therefore leave the direction of the unconditional robustness effect open. [Source-evaluation audit](../stage1_amended_source_evaluation_audit.md)

The fixed-history diagnostic held the private histories constant and compared receiver answers with peers present or withheld. Clean receiver correctness was 69.27% versus 61.46% for joint training and 53.13% versus 47.40% for independent training. The difference between the two peer-access gains was **+2.08 pp** (interval −5.73 to +9.38). On the 53 accepted exchange groups it was **+5.67 pp** (−1.60 to +13.83). Both intervals include zero. These are receiver measurements across matched groups; the source-evaluation table measures final team answers. [Fixed-history audit](../stage1_amended_fixed_history_audit.md)

## 3. Why the Stage II cohort changed

The executed training split contained three ARC and five LogiQA fitting blocks, with 24 and 40 shared allocation probes respectively. The original plan's fresh ARC evaluation requirement could not be met under the recorded exclusions: at most six fresh ARC groups remained. The blocked plan was preserved. An OpenBookQA alternative was explored, followed by a separately versioned GPQA Main / original English LogiQA development child.

Under the approved documented-exclusion standard, the real CPU audit found **249 screened GPQA Main groups and 5,995 screened LogiQA groups**. The child froze 64 groups per source, with GPQA Diamond protections and historical exclusions retained. These are prospective development questions. Project-wide exposure coverage is incomplete, semantic overlap has not been exhaustively reviewed, and model pretraining exposure is unknown. Missing historical execution also leaves historical spending and remaining historical budget unknown. The current child's ledger can still be reconciled exactly. [Exposure review](../stage2_exposure_review_2026-11-03.md) · [Implementation evidence](../implementation_status.md)

## 4. What the completed contribution assay found

For each of eight fitting blocks, one actor at a time received eight temporary updates from S0, with eight fitting examples per update. Each of the resulting 24 branches was evaluated on its own source's shared probes, with a common pristine readout. Rollback checks protected the next branch's starting state. Probe tasks supplied no training gradients. The allocation signal used the change in capped correct-answer-prefix negative log likelihood (NLL). A positive gain means the readout assigned the correct answer prefix lower loss after the update. Generated-answer correctness was scored separately.

| Source and actor updated | Mean correct, clean | Mean correct, accepted attack | Mean attack NLL gain |
|---|---:|---:|---:|
| ARC S0 baseline | 17/24 | 9/17 | reference |
| ARC Qwen | 18.00/24 | 10.67/17 | +1.421 |
| ARC Llama | 18.33/24 | 9.67/17 | +1.203 |
| ARC Mistral | 16.67/24 | 11.33/17 | +1.994 |
| LogiQA S0 baseline | 24/40 | 19/32 | reference |
| LogiQA Qwen | 24.00/40 | 20.80/32 | +0.074 |
| LogiQA Llama | 23.60/40 | 20.40/32 | −0.041 |
| LogiQA Mistral | 22.00/40 | 17.40/32 | −0.856 |

Fractional numerators are averages across three ARC or five LogiQA blocks. The same 24 or 40 probes recur. The attack denominators reflect 17/24 and 32/40 accepted interventions. All prescribed available score pairs were present.

- **ARC:** eight branches improved attacked correctness, and one tied. All nine had positive attack NLL gains. Mistral's attacked results were strongest on average, while its clean mean was slightly below S0.
- **LogiQA:** Qwen improved attacked correctness in all five branches. Llama improved in four and tied in one. Mistral declined in all five, with one to three fewer correct attacked answers per block. Llama illustrates why the surrogate and generated answers both matter: its mean attacked correctness rose even as its mean attack NLL gain was slightly negative.
- **Format failures:** the assay recorded 7,118 valid packets, 169 invalid packets and 33 abstentions across 7,320 generations. In the original probe collection Qwen produced 30 invalid private packets out of 64. Invalid completions remained failures. Packet validity alone cannot establish answer correctness.

[Detailed scored-assay review](../stage2_scored_assay_review_2026_11_17.md)

## 5. Frozen policy comparison and accounting

Five policies use seeds 113 and 227. Each team gets 288 optimizer updates: 64 base updates per actor, plus 96 extra slots spread across eight blocks. The primary terminal-block policy combines clean and accepted-attack terminal gains with equal condition weights. Uniform assigns four extra slots per actor per block. Source-family preserves source-level actor totals while smoothing the block allocations. Private-bank uses private-stage gains. Shuffled reassigns primary allocation rows within source. The freeze found ten distinct policy/seed contracts and no unsupported terminal rows.

| Primary policy extra slots | Qwen | Llama | Mistral |
|---|---:|---:|---:|
| Three ARC blocks | 3 | 13 | 20 |
| Five LogiQA blocks | 34 | 24 | 2 |
| **Total including base, per seed** | **101** | **101** | **86** |

At the verified boundary, both seeds of terminal-block and uniform have completed, along with source-family seed 113. This is five complete teams. The remaining five are source-family seed 227 and both seeds of private-bank and shuffled. Training completion records checkpoint availability. Comparative policy performance requires the prospective evaluation.

| Work | Verified through fit 15 | Frozen ceiling or schedule |
|---|---:|---:|
| Assay generations, including collection and smoke | 7,320 | 8,112 |
| Assay diagnostic forwards | 2,442 | 2,640 |
| Temporary assay updates / supervised forwards | 192 / 1,536 | 192 / 1,536 |
| Policy updates / supervised forwards | 1,440 / 11,520 | 2,880 / 23,040 |
| Prospective policy generations | 0 | 15,616 including smoke |

The generation count reconciles as 708 collection calls + 9 ARC branches × 188 + 15 LogiQA branches × 328. Diagnostic scoring reconciles as 177 S0 views + 585 ARC branch views + 1,680 LogiQA branch views. Across both stages the conditional generation ceiling is 23,728. Skipped or unavailable views confer no extra allowance. [Frozen design and analysis contract](../../src/pact/revival/allocation_v3/design.py)

## 6. Recovery and integrity audit

| Evidence | Finding |
|---|---|
| Stage I lineage and migration | Interrupted original and replacement history was retained separately. The amended continuation reached 768 committed updates across the six fits. AAI reproduced the recorded GPU/runtime fingerprint and verified transferred checkpoint tensors. The missing physical history remains explicitly unresolved. |
| Job 1124194, fit 10 interruption | Nine fits were durably exported. Scratch had 77 matched update events for uniform/227/Q; the latest original durable snapshot contained step 76. The reported OSError did not identify a root cause. |
| Jobs 1124403, 1124405 and 1124415 | Step 77 was preserved, its adapter hash recomputed, 224 AdamW states checked and the first 76 log entries matched. A new durable snapshot was verified before proceeding at step 78. |
| Job 1124418 | Recovery reached 15 verified fits and 1,440 updates. The capacity check stopped fit 16 before its first update. |
| Jobs 1124722–1124773 | Inventory found 135 local handoff ZIPs with matching durable copies. The subsequent cleanup job failed before deletion. A later check found the scratch root absent and 418 GiB free; the evidence does not identify what removed it. |
| Job 1124774 | Restore verified snapshot 1795085568012921921-215202ff7324, the 15 fit identities, final checkpoint files, and the policy ledger. The Stage I parent files and scratch model cache still required rebuilding. This is the latest supplied receipt. |

**Audit provenance.** For this report the local scored SANITIZED ZIP was rehashed, its declared payload digests checked, its 48 clean/exchange branch rows read, and the source/family correctness patterns recomputed. Stage I estimates come from the existing completed audits. Remote checkpoint and fit counts come from supplied Slurm outputs and the repository status journal. This review had no live access to node01. The last recorded targeted local test run passed 14 CPU tests; that is software evidence for the continuation wrapper.

| Reproduction anchor | Identifier |
|---|---|
| Repository revision inspected | `2e4dc2304a8e02902d6fcff098cba99cb4462929` |
| Stage II execution plan | `024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9` |
| Scored SANITIZED ZIP SHA256 | `cbf23e81ba8d81362471089c0839c17f1467caf101b3c91d89bade3c0abd0e7d` |
| Frozen policies file SHA256 | `4a45e3ddfea573566fd31383b2530d14757640278060c30e143d25dd5b437896` |

## 7. What happens next and how to judge the outcome

1. **Finish policy training.** The prepared continuation rebuilds the exact Stage I parent, checks Q/L/M model receipts and S0 adapters, and starts source-family/227/Q. The first expected milestone is 16 fits and 1,541 cumulative policy updates. Full completion is 30 fits, 2,880 policy updates and 23,040 policy supervised forwards. The first outstanding evidence is the continuation job output.
2. **Review and lock checkpoints.** After training, verify each final adapter against its frozen schedule, family, seed and starting state. Bind all ten trained teams, S0 and the prespecified analysis to a reviewed policy lock before opening prospective questions.
3. **Run the separately approved prospective evaluation.** Begin with the included source-specific smoke, review its receipt, then evaluate the frozen 64 GPQA Main and 64 original English LogiQA groups. Keep prompts and attack rules fixed, allow generated messages to differ across teams, and report acceptance, missingness, invalids and abstentions.
4. **Judge the primary comparisons.** Compare terminal-block against uniform and against source-family on attacked final-answer accuracy. The first asks whether the learned allocation helps at equal total compute. The second asks whether knowing the individual block adds value beyond knowing its source. Report each source and an equal-source estimate; keep paired seeds and views together in the source-stratified task-group bootstrap (10,000 replicates, 95% and 97.5% intervals). Report clean performance alongside the prespecified two-percentage-point tolerance and disclose how missing attacks affect interpretation.
5. **Write the conclusion at the level the data support.** Improvement over uniform alone would leave the value of block-specific credit open. A favorable attack result with poorer clean performance would be a trade-off. An inconclusive interval, a null result, or divergent science-transfer and reasoning results are all reportable outcomes. The current development study cannot settle pretrained-model exposure or full PACT efficacy.

The next substantive result is the paired policy comparison on the frozen cohort. Until those predictions are scored, the defensible conclusion is a positive Stage I clean development effect and source-dependent Stage II allocation evidence, with the central prospective comparison still open.

**21 November decision.** The operator approved the CPU checkpoint lock after fit 30. The next evidence is its durable lock receipt covering ten trained teams and S0. The prospective smoke requires its own approval after review of that receipt.
