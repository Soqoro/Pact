# PACT update: controlled private replay and fixed-bank specialization

Version: 2026-09-26
Proposed child run: `qwen3-controlled-specialization-001`
Context source: `controlled_private_packets_v1`
Credit estimator: `controlled_slot_delta_v1`
Learning variant: `controlled_specialization_fixed_bank_v1`
Status: implementation specification and proposed bounded experiment; no new GPU results.

## 1. Mission and workflow

Update the EXISTING PACT repository. Implement a complete local-testable path that obtains controlled private-packet interventions, measures whether they change specialization assignments, and, only after the declared checks pass, executes the existing three-arm fixed-bank training and natural evaluation.

Do not start a new repository or another experiment framework. Inspect Git status, AGENTS.md, actual package/CLI/test/notebook structure, the proposal, implementation specification, latest fixed-bank collection audit, the specialization update, controlled-donor implementation, and experiment ledger. Locate actual paths; proposed filenames/command names are capabilities, not evidence that those commands already exist.

My workflow is local Codex development and CPU tests -> my review/commit/push -> a pinned Git checkout in Google Colab -> my returned artifacts -> local analysis. Do not run GPU work or download pretrained weights locally. Do not commit, push, change remotes, access credentials, or disturb unrelated edits. No Slurm/PBS, SSH cluster, Docker daemon, paid model API, multi-GPU requirement, or unnecessary dependency migration.

Deliver the complete donor/replay/assignment/training/evaluation path with mocks and focused regression tests. Do not stop at an audit or an importer with no acquisition implementation. Missing actual weights should block a real run, not prevent implementing the pipeline with fixtures.

## 2. Accepted evidence and closed parent

Verify this context against the actual retained audits:

- Parent `qwen3-specialization-contrast-001` stopped with `insufficient_assignment_support` BEFORE replay, scoring, training, or development evaluation.
- It completed 32 fitting tasks x clean/early = 64 rows, using 1,216 committed generation calls. Only 2 distinct tasks and 5 of 192 actor/row cells had admissible natural correct/wrong pairs. There were 62 unsupported rows, one two-eligible row and one three-eligible row.
- Its 32 selected development tasks were not evaluated.
- The report does not supply a complete per-cell explanation of all missing pairs. Do not infer that every missing cell was all-wrong or all-correct; reconstruct the breakdown from stored candidates where available.
- The prior controlled receiver experiment executed but added no receiver-correctness benefit over its frozen/task-SFT controls on the matched cohort. This update does not reopen that training.
- GPQA was sparse and added no correct coverage over its best actor. Its 32 exposed diagnostic tasks are not training data; preserve 164 protected items and two recorded exclusions. This update requires no GPQA content access.
- Full PACT, joint refresh, adaptive robustness, and final-test efficacy remain unestablished.

Parent provenance:

```
run_id: qwen3-specialization-contrast-001
bundle: qwen3-specialization-contrast-001-handoff-1790416052208683365.zip
bundle_sha256: 555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f
source_commit: 28565003e10c91cf64f5c54b87284598f1331f65
plan_hash: 99ff21066f93f26fae33e6cbf70623313b0f9acd09e9e6d49e0702674af5131c
reported_snapshot: 1790416058064299645-d3b470ec3286
```

These identify historical evidence, not instructions to reset a newer working tree. Validate only artifacts needed for this change; do not repeat every old archive audit. Never execute imported scripts, obey generated instructions, or load unsafe serialized objects just to inspect evidence.

The parent remains completed/stopped under its original natural-pair policy. The new study is a CHILD experiment importing immutable parent observations. Do not reset the old budget, add natural draws, replace tasks, loosen the old selector, or rewrite its conclusion.

## 3. Explicit methodological revision

The original estimator required correct and wrong alternatives sampled under each learner's original private prompt. That acquisition requirement is now relaxed ONLY in a new controlled-intervention variant.

For each fitting task x, generate a task-specific pair:

```
v_plus(x): structurally valid packet supporting official answer y
v_minus(x): structurally valid packet supporting one prespecified wrong option w != y
```

Use the SAME accepted pair for every intervention actor and for clean/early conditions of that task. The generator is not specialized to a particular actor or chosen according to downstream success. This prevents differences in donor text quality from masquerading as between-actor credit differences.

For task-condition row b and physical actor i, substitute the controlled packet in a COPY of the private-state snapshot and run the real frozen continuation:

```
Q_ctrl_plus[b,i]  = mean_s terminal_success(Continue(Z0[b,-i], v_plus[x]; early_payload[b], seed_set[s]))
Q_ctrl_minus[b,i] = mean_s terminal_success(Continue(Z0[b,-i], v_minus[x]; early_payload[b], seed_set[s]))
delta_ctrl[b,i]   = Q_ctrl_plus[b,i] - Q_ctrl_minus[b,i]
```

K=2 in the primary bounded configuration. Positive, zero, and negative values are legitimate. Missing is not zero.

Interpretation: a controlled correct-versus-wrong PACKET insertion effect at actor i's position, conditional on other saved packets, the fixed continuation policies, and the recorded task/attack. It is NOT an unbiased on-policy credit, a natural effect of making actor i correct, an intervention on an internal belief, or an exact parameter gradient. The two packets also differ in explanation wording. It is not Shapley value or a reproduction of COMA.

Dense candidate availability does NOT guarantee different credits between actors, stable assignments, learnable targets, or improved team performance. A symmetric team may have identical controlled credits everywhere.

### What this authorizes and what it does not

This explicitly supersedes the old prohibition on target-conditioned PRIVATE replay inputs for this new estimator. Do not weaken that prohibition in the legacy natural estimator.

Unlike the receiver-donor study, this replay DOES temporarily replace the selected actor's OWN packet and the clean delivered views derived from it, inside a counterfactual clone. That is the declared intervention. The immutable parent packets and real deployment trajectories remain unchanged. Replacing only an outgoing message while leaving that actor's own packet untouched would be a different estimator and is not the primary design here.

The learner's original prompt is used for answer scoring and training. The offline target-conditioning instructions never enter it. Correct labels enter ordinary training targets/evaluator records, not privileged inference inputs. Natural evaluation uses no controlled packets, gold prefixes, or forced answers.

## 4. Reuse the parent; do not recollect anchors

Reuse exactly the parent's 32 fitting groups, 32 development groups, option mapping, two condition assignments, early attack bytes, original initial packets, and recorded protocol identities. Do not select a favorable alternative from the four candidates as a new natural anchor.

Import the three ORIGINAL private packets per row and existing anchor continuations read-only. Reconstruct a narrow source diagnostic from the old candidates: valid-correct, valid-wrong, abstention, malformed/invalid, length-limited, and selector rejection reasons. Report this as old collection analysis, not new generation or a changed selector.

Verify the 32 development groups have not subsequently been used for optimization or outcome-based choice. Record actual exposure; if incompatible later use exists, stop planning rather than silently substitute fresh tasks. Fit-support inspection remains training-data inspection, not held-out performance selection.

Preserve valid existing abstention handling in nonintervened packets. If the frozen continuation cannot represent a particular original packet, mark the row incompatible with its actual reason; do not relabel or repair source bytes.

Use the parent's effective frozen-preparation team, not a receiver-trained arm. Expected effective hashes, subject to the parent receipts:

```
agent0: eef7b26388dabd812e7519b6cef0ececd1737bd9989c5a5715378694dcbad7ad
agent1: 505e04c7518134abfc38222ab7e507ee392c1913292cc387bcc2c7ddd74ce18c
agent2: 07ae09c5803bd2603beb88097208da3929a61b98a9f1bd691b4244a53cd79662
```

Restore actual durable weights, not metadata-only review ZIPs. Verify effective identities and retain the recorded nonfocal FP32 -> BF16 -> FP32 history. No silent precision repair. Exact-value-preserving promotion for gradients must be recorded. Match pinned Qwen3-8B/base/tokenizer/template, BF16/SDPA backbone, non-thinking, 4,096-token total context cap, private/revision cap 256, readout cap 64, temperature 0.7, top-p 0.8, top-k 20 and remaining frozen decoding settings.

## 5. Controlled pair acquisition: small, symmetric and bounded

Reuse the real controlled-donor generator and validator with a new source type; do not build another model backend.

Generator: pinned UNADAPTED base with all learner adapters disabled. Restore previous adapter/mode after generation, including exceptions.

Generate once per FITTING TASK, not per actor or condition. The generator sees trusted task/options, normal packet schema and an assigned answer option. It does NOT see the actor identities, original answers, early advisory, desired credits, development outcomes, or optimization results. Excluding the early advisory is intentional: the same standardized probe is inserted into both task-condition histories. Report it as such; do not claim it was naturally produced under either original actor prompt.

Use one symmetric template for positive and negative targets, differing only in assigned option. Request a concise task-grounded answer/justification in the normal answer-first packet schema, without references to assigned targets, answer keys or training. The wrong target is selected from canonical wrong options with a new stable namespaced seed, BEFORE generation. Do not choose the most persuasive/worst-performing option after feedback.

At most two attempts per target. First accepted wins; later retries retain target, template and decoding. Every dispatched attempt counts. No seed/temperature search, response rewriting, stronger teacher fallback or retry-until-correct.

Maximum acquisition:

```
32 tasks * 2 targets * 2 attempts = 128 calls
128 * 256 = 32,768 output tokens reserved
```

Reject according to a frozen explicit validator: target mismatch, invalid/abstaining packet, missing required justification, length failure, unsupported schema, or overt construction-metadata disclosure. Never replace the answer label or graft a correct label onto an unrelated explanation. Preserve rejected bytes and reasons.

Do not require a pair to be length-bin matched to count as structurally eligible. Prefer neither target by length. Retain token-length differences and a prespecified bin flag as a confound diagnostic; the primary contrast remains a full-packet intervention.

An answer match does not verify a rationale. Retain `rationale_review_status=not_reviewed` unless actual review occurs. Export a deterministic fitting-only review sample of eight tasks (four/family where supported), both packets per task, chosen by fixed IDs before outputs; do not substitute better examples after inspection. A trusted local reviewer may record concrete defects with provenance. No automated 'verified reasoning' stamp and no new reviewer-model budget. A clear systematic content/metadata defect is a stop condition; fixing it creates a new source version, not rewritten old packets.

Unlike receiver SFT, a controlled credit requires BOTH accepted target packets. A single positive can remain in the archive but does not create a fake contrast. Invalid donor attempts and missing pairs remain explicit.

## 6. Primary replay and seed pairing

For each compatible row with an accepted task pair, run each of the three physical actor interventions, both signs and two suffix seeds. The maximum is 192 actor/row cells.

For each branch:

1. Deep-copy the immutable natural initial snapshot.
2. Replace only physical actor i's packet in that clone with v_plus or v_minus.
3. Rebuild all private/peer views from the clone using the original synchronous protocol.
4. Preserve all other original private packets, trusted task/options, fixed early material and model identities.
5. Regenerate all three revisions independently from initial peer packets only.
6. Regenerate the base-only readout from the three revised packets.

The chosen actor sees its substituted own packet; peers see its substituted outgoing content. Never restore the original own packet in one place while showing the substitute elsewhere, and never leave stale rendered prompts/KV state.

This study has clean/early conditions only, not exchange corruption. Do not add attacks, donors to the other agents, readout changes, or answer-only decoding.

Use seed sets indexed by stable task/condition, suffix replicate and downstream PHYSICAL receiver/stage. The seed namespace must NOT depend on the intervened actor, correct/wrong target, or generation order: all actor/sign comparisons use corresponding common random numbers. Different physical receivers still have distinct node seeds. Do not share a single mutable global RNG stream across branches.

K=2 is coarse. Store every per-seed success and failure, not just a mean. Raw credit values lie in {-1,-0.5,0,0.5,1}. No smoothing to manufacture nonzero differences. A negative value is not invalid.

Reuse only exact request/checkpoint/seed matches via the existing audited cache. Natural parent outputs are not substitutes for new counterfactual responses simply because answer IDs agree. Any replay output reused by exact identity is logged as reuse, not a new call. No hidden KV sharing across actors.

Primary replay cap:

```
64 rows * 3 actors * 2 signs * 2 seeds * 4 calls = 3,072 calls
64 * 3 * 2 * 2 * (3*256 + 64) = 638,976 output tokens
```

## 7. Two bounded interpretation controls

These are fitting-data diagnostics, NOT extra training arms or performance claims.

### 7.1 Presentation-order sensitivity

Before donor output, choose eight fitting task IDs, four per family, by fixed stable order independent of parent support/accuracy. Include both clean/early rows when eligible; no replacements if unsupported.

Repeat controlled replay with the SAME actor identities, own states, pair texts and per-node seeds, but reverse the presented order of the two peer packets for every receiver and reverse the readout packet list. Do not relabel or swap model adapters. Preserve source labels. This is an explicitly changed presentation protocol, not a rerun of the original protocol.

Maximum additional calls:

```
8 tasks * 2 conditions * 3 actors * 2 signs * 2 seeds * 4 = 768
output cap = 159,744
```

Primary training credit uses the ORIGINAL-order intervention only. Do not select or average the more favorable order after results. Report per-actor raw/centered credit changes and their actual support. For assignment sensitivity, keep the original full-bank NLL transform/settings fixed; solve a diagnostic full bank with only the control rows' credits replaced, preserving all masks. Report responsibility movement on those rows and any globally coupled change elsewhere. Do not compare separately standardized subset solvers as though only order changed.

If actor preference reverses with presentation order or is concentrated in one positional identity, label that ambiguity. This small control is not a universal proof of order invariance. No extra permutation sweep is authorized.

### 7.2 Calibration against the five retained natural pairs

The parent reportedly contains exactly five natural-pair cells on two fitting tasks, but has no replay. Verify the cell/packet identities using its original selector, without resampling. In this CHILD study, replay those retained natural pairs under the same original-order suffix seeds used for controlled pairs.

Cap: five pairs * two signs * two seeds * four calls = 80 calls / 16,640 output tokens.

Compare natural and controlled Q+/Q-/delta on shared cells. Different packet wording/length/source means exact equality is NOT required or expected. Two selected tasks cannot validate a population estimator. If controlled packets are missing for a cell, report no matched comparison rather than inventing an overlap; do not replace the cell.

No natural-pair result enters the primary controlled bank or changes which donor is selected. These calls do not reopen or alter the stopped parent's counters. If actual parent eligibility differs from five cells, stop with the discrepancy rather than expanding the cap.

## 8. Assignment: separate support, contrast and reliability

Use the existing solver with identical support and source data across arms. The mask is now explicitly CONTROLLED-pair/replay eligibility, not the natural pair mask. Legacy loaders continue rejecting synthetic pairs unless this estimator/source variant is explicitly selected.

Original-context answer NLL is scored under each actor's ORIGINAL private prompt, with no generator instruction or gold rationale in the input. Current answer likelihood is only a proxy for learnability, not a certificate that training will improve.

Score positive full-packet NLL under that original learner prompt if required by the bank/training audit. The positive packet is a SYNTHETIC SUPERVISED TARGET, not a sampled on-policy answer. This changes both replay source and specialization-target provenance. All arms must share it exactly to control for distillation/data effects.

Maximum frozen scores: 192 original-context answer forwards + 192 positive-packet forwards. They are not generation calls. No teacher-forced development sweep.

Keep the parent interpretation of the answer-NLL transform where resolved: training-bank-global standardization, saved mean/std/degenerate handling, identical for local/credit arms, no per-agent transform and no development data. Document an unresolved interpretation before GPU calls; do not choose raw/standardized according to which gives a desired result.

```
R_uniform[b,i] = M[b,i] / sum_j M[b,j]
a_local[b,i]   = stop_gradient(transformed_answer_nll[b,i])
a_credit[b,i]  = stop_gradient(transformed_answer_nll[b,i] - gamma*delta_ctrl[b,i])
```

Solve local/credit with the existing row-simplex/entropy/global-balance objective:

```
mean_b sum_i R[b,i]*a[b,i]
+ tau*mean_b sum_i R[b,i]*log(R[b,i])
+ lambda_balance*KL(mean_b R[b,:] || Uniform(3))
```

Primary settings: gamma=1 (credit), gamma=0 (local), tau=0.2, lambda_balance=0.1, lambda_spec=1. No tuning after development outcomes. Uniform uses the same valid cells.

Required report:

- Counts at task, row and cell levels; zero/singleton/multi-eligible rows.
- Q+/Q- and per-seed deltas; within-row actor differences; row-constant credits.
- R_uniform/R_local/R_credit and task-grouped mean L1 contrasts.
- Entropies, column totals, per-task allocation, fragile-weighted exposure.
- Whether one actor is favored on almost everything versus task-dependent allocations.
- Single-seed assignment sensitivities, using the SAME primary NLL transform and masks, without selecting a preferred seed or inflating sample size.
- Presentation-order and natural-pair calibration reports.

A row-constant credit cannot change an assignment; missing is not zero. A singleton cannot show a credit-driven choice. Symmetric policies may remain symmetric. Do not add arbitrary per-agent credit offsets, role prompts, hardcoded assignments, random diversity rewards, or answer corruption to force a nonuniform solution.

### Pretraining gates and explicit review

Retain minimum support: at least eight distinct fitting tasks with compatible pair support AND at least eight with a multi-eligible row. Stop before replay if structural masks cannot possibly meet these minima.

After replay/scoring, require complete valid evidence and numerical contrast as before. Add a declared practical screen for this NEW variant:

- Task-average L1(R_credit - R_local) over tasks with multi-eligible support is at least 0.10.
- At least eight distinct fitting tasks each have mean multi-eligible-row L1 contrast at least 0.10.

Compute task means first, so two conditions are not two independent tasks. L1=0.10 corresponds to moving 0.05 probability mass in a row. These are conservative engineering screens, NOT significance tests, optimal thresholds, or proof the credit is useful. They are fixed before new model outputs. Keep 1e-6 as numerical-identity tolerance; do not describe a 1e-6 difference as useful specialization.

If these gates fail, export `insufficient_controlled_support`, `no_assignment_contrast` or `insufficient_practical_contrast` as appropriate and do not run nominal credit training. Do not relax thresholds after observing the result or automatically fall back to a different method.

Replay/assignment commands must STOP after emitting the report, even when numerical gates pass. Training is a separately invoked Colab stage. The user reviews packet quality, seed/order sensitivity and actor dominance before deciding to spend the training budget. The UI must not label a gate pass as 'reliable causal credit' or PACT readiness. A completed implementation must allow the planned train/evaluate stages without another coding pass once that explicit review decision is made.

## 9. One-round training: shared synthetic targets, only weights differ

Reuse the specialization trainer; register source-specific arm names:

```
controlled_uniform_sft
controlled_local_specialization
controlled_continuation_specialization
```

All arms start from identical parent effective actor tensors with fresh independent optimizers. All three adapters update sequentially in each arm. Backbone and base readout remain fixed. No receiver loss, DPO, margin/ranking objective, attacker co-evolution or outer refresh.

For U=64 fitting rows, B eligible rows, m=3, retain the documented parent reductions:

```
L_base = (1/(m*U)) * sum_b sum_i answer_CE[b,i]
L_spec = (1/B) * sum_b_eligible omega[b] * sum_i R[b,i] * packet_NLL[b,i]
L_total = L_base + lambda_spec * L_spec
```

If the audited implementation uses another approved reduction, state the exact equation and preserve it identically across arms; do not silently rescale specialization.

- Base answer targets cover all fitting rows/actors, even missing-pair rows.
- All eligible positive targets are the SAME controlled correct packet for a task, trained under each actor's actual original context.
- Packet NLL is the legacy length-normalized complete-output loss. Do not silently substitute receiver answer-prefix CE.
- Report correct-target rationales as unreviewed unless actually checked. Synthetic target exposure is common across arms; a gain over frozen alone is not evidence for credit.
- omega=1/(1+original_correct_actor_count), normalized over the declared eligible frozen bank exactly once. It uses NATURAL anchor correctness, never the constructed positive branch.
- Maintain global B/U/m scaling across batches and gradient accumulation. Do not normalize each actor's weights separately, skip base supervision on missing rows, or produce 0*NaN.
- Compare accumulated gradients with an independent full-objective tiny fixture containing unequal responsibilities, sparse support, and unequal target lengths.

Keep inherited modules/rank/scaling/dropout/optimizer implementation, learning rate 1e-5, microbatch one logical row, effective batch four, at most two passes and 32 optimizer updates per adapter. Maximum 96 updates per trained arm, 288 total. Print actual base/packet forwards and target exposures; maximum 1,152 base presentations and 1,152 packet presentations if all cells are supported, excluding frozen bank-scoring forwards.

Only the active adapter may change; other adapters are immutable during its update. Every arm resets all three tensors/optimizer states before training. Snapshot all actors only after the arm's sequential updates complete. No source bank refresh halfway through.

The same updated adapter serves private and revision turns. Therefore PROTOCOL/readout are fixed, but revision behavior can change without a receiver loss. Do not claim receiver policies were frozen.

Do not select training duration/checkpoint using the development cohort. Evaluate the final capped checkpoint. Negative results are valid results.

## 10. Natural development evaluation and scientific interpretation

Reuse the original 32 development groups and clean/early condition plan. Evaluate frozen parent initialization and all three trained arms. Generate natural outputs with no label-conditioned donors, forced own packets, assigned answer targets, or changed output contract.

Per system/task/condition:

1. Three natural private packets, independently generated and frozen.
2. Independent vote with existing rules (no model call).
3. Independent base synthesis from those private packets.
4. Three synchronous revisions from original private peer packets.
5. Base synthesis from revised packets.

Eight calls per system/task/condition. Match task/options/early payload, physical actor IDs, node seeds, prompt versions and decoding across arms. Checkpoints intentionally differ: never reuse an old output just because its prompt/seed matches. Cache exact identity only.

Evaluation ceiling: 4 systems * 32 tasks * 2 conditions * 8 = 2,048 calls, 425,984 output tokens. No exchange/adaptive attacks, new GPQA calls, protected final evaluation or additional inference sampling. Avoid a separate fitting free-generation sweep.

Report clean and early separately:

- Individual accuracies, mean/best accuracy, initial joint failure and coverage.
- Coverage above best member and unique correct coverage per actor.
- All-correct/all-wrong/mixed state transitions, and whether extra disagreement came from losing correct answers.
- Natural vote/synthesis/debate final correctness, erasure, construction, utilization and readout loss.
- Per-task paired changes versus frozen, controlled-uniform and local-specialization.
- Clean-utility, input/output-token and training-exposure trade-offs.

Thirty-two groups, not calls/actors/conditions, are the sampling units. This is one-seed development feasibility. Degenerate empirical bootstrap intervals do not prove equivalence. Controlled credits do not establish causal use of a rationale or adaptive robustness.

Required interpretation ladder:

1. More accepted pairs is a data-source result, not useful credit.
2. More credit/assignment contrast is a signal result, not successful learning.
3. Better fitting likelihood is not held-out complementarity.
4. Better accuracy over frozen alone may be synthetic-data distillation.
5. Credit beating uniform AND local, with useful coverage at comparable individual strength, supports the tested allocation principle only.
6. Coverage lost by natural communication leaves preservation unresolved.
7. No advantage beyond common synthetic targets is a substantive negative result for this credit-based variant, not a prompt to automatically add steps/models/data.

## 11. Hard budget and stage stops

Derive all counts in the planner, test them, and retain actual/attempted/reused counts separately.

| Stage | Max new generation calls | Max reserved output tokens |
|---|---:|---:|
| Task-common controlled pair generation | 128 | 32,768 |
| Primary controlled replay, all 64 rows | 3,072 | 638,976 |
| Reversed-display control, eight fixed fitting tasks | 768 | 159,744 |
| Calibration, five retained natural-pair cells | 80 | 16,640 |
| Four-system natural development evaluation | 2,048 | 425,984 |
| **Total** | **6,096** | **1,274,112** |

Suffix cap=3*256+64=832 tokens. Natural evaluation per system/task/condition=3*256+64+3*256+64=1,664 tokens.

Before training the acquisition/replay maximum is 4,048 calls / 848,128 reserved output tokens. These are substantial worst-case ceilings, not expected consumption or time/cost forecasts. The first generator stage is only 128 calls; no notebook default may run the whole plan.

Separate non-generation ceilings: up to 192 answer-scoring and 192 positive-packet-scoring forwards; 288 optimizer updates; derive training target/input token accounting from the realized bank. No extra critic/reference model calls or development option-margin matrix.

The old 1,216 calls are reused evidence, NOT new calls and NOT an unused budget balance. No fresh anchor/candidate calls. Every failed/retried dispatch counts; resume does not replenish caps. Unknown compute units remain null. Do not sum unlike historical timers into claimed billed GPU-hours.

## 12. Implementation surface and persistence

Extend existing donor, bank, replay, assign, specialization and report interfaces with explicit source/estimator discriminators. Keep natural and controlled schemas distinguishable all the way to the trainer. Do not create an untyped generic 'pair' shortcut accepted by every loader.

Suggested capabilities, using actual project CLI naming at handoff:

```
controlled-specialization plan          # local metadata, zero model
controlled-specialization acquire       # 128-call source cap
controlled-specialization build-bank    # masks/support, no GPU unless declared scores
controlled-specialization replay        # primary and fixed controls; support-gated
controlled-specialization score-assign  # declared frozen scores + CPU solves/report; then stop
controlled-specialization train --arm ...
controlled-specialization evaluate
controlled-specialization report/export
```

Keep acquisition, replay/assignment review, training, and evaluation explicitly invoked stages with plan hashes. Implement all stages now. Use a thin Colab notebook with commit, parent artifact path, effective weight snapshot, new child ID, plan/config hash, scratch/persistent roots and resume/stage parameters. Never invent user filesystem paths beyond examples.

Resume must restore attempts, committed requests, bank/pair/assignment IDs, arm/actor state, optimizer/scheduler/RNG/sampler position and accumulation boundary. Preserve full tensor/optimizer checkpoints separately from compact inference initialization and lightweight review ZIPs. Reuse scratch-first I/O, versioned shards, local ZIPs and bounded verified copies. No new storage redesign or repeated whole-project archive inventories absent a concrete defect.

Cache identity includes intervention source and estimator, original row/private hashes, pair texts/targets, physical intervention actor, display variant, snapshot/precision/template/decoding and per-node seed. Seed derivation may omit the intervention sign to enable pairing; CACHE keys must still include the complete branch content. Do not confuse these requirements.

## 13. Tests

Default tests use invented tasks and no network/model downloads. Optional neural tests use tiny locally initialized models. Run relevant existing regressions and report passes/skips honestly.

Required new tests:

1. Safe immutable parent import; stopped parent remains stopped; original counters/bytes unchanged.
2. Missing pair reason reconstruction does not equate pair absence with wrong coverage or team agreement.
3. Legacy natural loader rejects controlled packets; new estimator requires explicit controlled provenance.
4. Correct/wrong target selection, one symmetric generator, base-only adapter isolation, two-attempt caps and first-valid policy.
5. Common pair bytes across actors and clean/early rows; no focal prompt/answer/credit information enters the generator.
6. Full cloned private-state replacement changes own and delivered views consistently, while nonintervened packets/early material remain exact and anchors stay immutable.
7. All suffix seeds match across actor/sign comparisons for each physical downstream node; rendering/seed state cannot depend on previous branch length.
8. Equal-policy symmetric fixture yields no systematic actor credit difference. Row-constant credits and singleton masks leave assignments unchanged. A nondegenerate fixture produces a known contrast without hardcoded diversity.
9. Reverse-display control changes order only, not actor identities or seeds; primary credit is never chosen after comparing orders.
10. Five-cell natural calibration stays separate, cannot become synthetic primary data or change donor selection.
11. Score masks, NLL transform and global loss/gradient reductions match independent toy calculations. Common positive targets and exposures are identical across training arms except R.
12. Controlled supervision never enters free-generation evaluation prompts; no gold targets/hidden metadata in actor/readout messages.
13. Support/practical-contrast stops, explicit review boundary, all call/token/update ceilings, checkpoint invalidation and resume without duplicate calls/updates.
14. Full mock acquire -> replay -> assign -> three-arm train -> four-system evaluate -> export/import round trip, plus missing-support and identical-credit negative paths.
15. Tiny neural optimization updates only active adapters and exercises full-packet loss; it is not evidence of 8B complementarity.

## 14. Artifacts and handoff

Export standard provenance/environment/resource files plus:

```
parent_import_receipt.json
natural_candidate_missingness.json
controlled_pair_manifest.json
controlled_pair_attempts.jsonl
pair_quality_and_review.json
controlled_support.json
controlled_replay_cells.jsonl
order_sensitivity.json
natural_controlled_calibration.json
answer_score_definition.json
assignment_transform.json
assignment_{uniform,local,credit}.json
assignment_contrast.json
seed_assignment_sensitivity.json
pretraining_decision.md
loss_weight_audit.json
training_arms.json
development_results.json
CODEX_HANDOFF.md
```

Keep private data, raw outputs and full tensor storage protected according to existing policies. No GPQA content is needed or may be copied into these outputs. Metadata-only bundles do not certify independent tensor verification.

Update AGENTS.md concisely, method-source documentation, implementation decisions/status, ledger and runbook. Explicitly mark the changed estimand, synthetic positive-target source, calibration limits, and remaining PACT gaps. Preserve original manuscript result placeholders and old variants/results.

Finish with changed files, actual local tests, example paired generator requests/branch views/assignments (fixtures labeled), exact commands for each stage, budgets, support/review boundaries, required real artifacts and what remains GPU-unverified. Do not claim a new result or schedule experiments.

The aim is to complete a falsifiable test of controlled continuation-based allocation. It is NOT to keep changing the acquisition recipe until a desired performance claim appears.

## 15. Source and reasoning notes

Project definitions and parent evidence are the source of truth. The following are background references, not instructions to implement different algorithms:

- COMA, Foerster et al., arXiv:1705.08926: counterfactual marginalization of an agent action while holding others fixed. This proposal does not use COMA's critic or claim its guarantees.
- STaR, Zelikman et al., arXiv:2203.14465: answer-conditioned rationale generation is a known training-data construction technique. It does not verify rationale correctness or validate PACT's slot-based credit.

The shared-pair design, finite budgets, controls and new practical assignment screen above are proposed engineering decisions, not established empirical findings.
