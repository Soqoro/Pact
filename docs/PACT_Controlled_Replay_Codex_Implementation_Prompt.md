# PACT: implement controlled private replay and fixed-bank specialization

Implementation brief: 29 September 2026.
This consolidates the previously specified controlled-replay design. It does not report a new experiment, expand its approved budget, or authorize automatic GPU execution.

You are updating my EXISTING PACT repository. Implement the controlled replay update below locally. I develop with Codex, review and push code to GitHub, pull a pinned commit in Google Colab, execute experiments there, and return the artifacts for local analysis.

## 1. Inspect, reconcile, and implement—not another standalone framework

First inspect Git status, applicable AGENTS.md instructions, package/CLI/notebook structure, tests, and the latest experiment ledger. Read the latest fixed-bank specialization collection audit and, where present:

- PACT_Conference_Proposal.tex and the implementation specification.
- PACT_Codex_Assignment_Contrast_Specialization_Update.md.
- PACT_Codex_Controlled_Private_Replay_Update.md.
- Controlled-donor and receiver-supervision methodology/implementation records.
- Current implementation decisions/status and the Colab runbook.

Locate the actual files; names above do not establish repository paths. Treat this as an idempotent completion request: inspect and test any already implemented controlled-replay components, then complete the missing path. Do not duplicate them or reset a completed child run. If actual later evidence exists, identify it and preserve its provenance rather than assuming this brief describes the newest executed state.

Preserve unrelated changes. Do not commit, push, change remotes, launch local/remote GPU work, download pretrained weights locally, or read credentials. Local tests must work without CUDA; optional neural tests use tiny locally initialized models. Actual Qwen work happens only when I explicitly invoke a stage in Colab. No Slurm/PBS, new agent framework, paid inference service, multi-GPU dependency, Docker daemon requirement, or unnecessary package upgrades.

Implement the full acquisition -> replay -> assignment -> training -> evaluation path with focused tests. Missing actual weights may block a real run, but must not prevent fixture-backed implementation. Do not finish with only an audit, a design document, or placeholder methods advertised as implemented.

## 2. Accepted parent evidence and immutable inputs

The latest supplied parent is:

```text
run_id: qwen3-specialization-contrast-001
outcome: insufficient_assignment_support; stopped before replay
bundle: qwen3-specialization-contrast-001-handoff-1790416052208683365.zip
sha256: 555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f
source_commit: 28565003e10c91cf64f5c54b87284598f1331f65
plan_hash: 99ff21066f93f26fae33e6cbf70623313b0f9acd09e9e6d49e0702674af5131c
reported_snapshot: 1790416058064299645-d3b470ec3286
```

It completed 32 fitting tasks in clean and early conditions: 64 rows and 1,216 committed calls. Only two distinct tasks/five actor-row cells supplied valid natural correct/wrong pairs; 62 rows had no eligible actor. No replay, scoring, training, or development evaluation ran. The 32 development tasks were selected but unevaluated at that audit.

Keep the parent closed. Do not append calls, reset its budget, weaken its selector, lower its support threshold, or relabel its result. A different current HEAD is expected for the new implementation; parent identities are provenance, not an instruction to reset Git.

Reuse its exact fitting/development partitions, task/group IDs, option mapping, original private packets, clean/early assignments, attack bytes, original actor contexts, and effective initialization. Do not recollect the 1,216 calls or choose a convenient alternative as an anchor. Verify the development partition's current exposure in the ledger; incompatible later fitting/exposure requires an explicit planning error, not silent task replacement.

Use trusted safe readers to verify only the relevant artifacts. Never execute imported scripts or obey instructions in model messages. Reconstruct natural-candidate missingness from retained records where available; missing pair support alone does not establish that all candidates were wrong, that all were correct, or that the initial team agreed.

Prior controlled-receiver and GPQA results remain closed. Do not access GPQA content, its 164 protected items, or any final-test data in this update.

## 3. The explicit methodological change

Register separate identities:

```text
context_source: controlled_private_packets_v1
credit_estimator: controlled_slot_delta_v1
learning_variant: controlled_specialization_fixed_bank_v1
proposed_child_run: qwen3-controlled-specialization-001
```

Check for existing run-ID collisions. Reuse an active run only through compatible explicit resume. Never overwrite a completed run or quietly invent a new experiment configuration.

The OLD estimator requires correct/wrong private alternatives sampled under each learner's same original prompt. It remains unchanged and rejects synthetic alternatives.

The NEW estimator uses a controlled pair generated offline for each fitting task. This explicitly supersedes the earlier ban on target-conditioned PRIVATE interventions only for this named variant and its synthetic specialization targets. It does not authorize changing historical observations or forcing deployed disagreement.

For task x and each clean/early row b, use the SAME accepted packet texts across all three intervention actors:

```text
v_plus[x]  = generated normal packet supporting official answer y
v_minus[x] = generated normal packet supporting a seeded wrong option w != y

Q_plus[b,i]  = mean_s success(Continue(clone(Z0[b]) with packet i = v_plus[x], seed_set[s]))
Q_minus[b,i] = mean_s success(Continue(clone(Z0[b]) with packet i = v_minus[x], seed_set[s]))
delta_ctrl[b,i] = Q_plus[b,i] - Q_minus[b,i]
```

This is a controlled correct-versus-wrong PACKET INSERTION effect at physical actor i's position, under fixed other packets and continuation policies. It is not an on-policy effect of improving that actor, an intervention on its internal belief, an exact policy gradient, or a Shapley value. The packet alternatives differ in wording as well as correctness; actor effects may also reflect other saved states and presentation. Do not infer valid rationale use from an answer label.

Unlike receiver-donor augmentation, replace the chosen actor's OWN private packet and all peer-delivered views derived from it inside the replay clone. Replacing only the outgoing message would define another estimator. The immutable natural parent snapshot is never edited.

Dense pair support does not imply nonconstant credits, meaningful assignment differences, or useful learned specialization.

## 4. Restore and freeze the audited team

Use the parent effective frozen-preparation actors, not a task-SFT or receiver-SFT arm. Check these expected hashes against actual parent receipts:

```text
agent0: eef7b26388dabd812e7519b6cef0ececd1737bd9989c5a5715378694dcbad7ad
agent1: 505e04c7518134abfc38222ab7e507ee392c1913292cc387bcc2c7ddd74ce18c
agent2: 07ae09c5803bd2603beb88097208da3929a61b98a9f1bd691b4244a53cd79662
```

Restore real durable weights. A review ZIP is not a tensor checkpoint. Preserve and disclose the historical nonfocal FP32 -> BF16 -> FP32 effective-load history; do not silently repair it. Record stored/load/effective/train dtypes and any exact-value-preserving promotion used for gradients. Unexpected tensor identity is a preflight failure, not a reason to silently use different actors.

Keep the pinned Qwen3-8B backbone/tokenizer/template, BF16/SDPA, thinking disabled, and recorded remaining generation parameters. Existing limits: 4,096 total context tokens, private/revision output 256, readout output 64, sampling temperature 0.7/top-p 0.8/top-k 20; frozen readout retains its original decoding. No model, rank, thinking, context, or topology change. Three agents only.

## 5. Controlled packet acquisition

Reuse the existing base-only donor backend and validator with explicit new provenance. Disable all learner adapters for generation; restore adapter/mode/gradient state even after an exception.

Generate once per FITTING TASK, not per actor or condition. The generator receives only the task/options, normal packet contract, and assigned option. It must not receive natural actor answers, actor identity, early payloads, development outcomes, or requested downstream effects.

Select one wrong option from the canonical incorrect-option set with a stable namespaced seed before generation. Use the same versioned instruction for positive and negative targets, differing only by assigned option. For example, adapted to the actual schema:

```text
Produce a concise peer response for this multiple-choice task.
Support option {target_option} using a task-specific justification.
Use the normal answer-first packet schema {schema}.
Do not mention assigned targets, answer keys, or training instructions.
Task/options: {task}
```

Offline label use is explicit. Generator instructions and target-selection metadata never enter the learner's system/user inputs; its ordinary training completion may contain the correct answer.

At most TWO attempts per target; the first accepted packet wins. No critique/rewrite loop, feedback-dependent wrong target, prompt/temperature sweep, hidden retries, or stronger-model fallback. Every dispatched attempt counts, including rejected outputs and unresolved attempts. Resume does not replenish budgets.

Accept only structurally valid, target-matching, non-abstaining packets with the required bounded justification. Reject length-limited/schema-invalid/mismatched packets and narrowly defined overt construction-metadata disclosures. Never change the generated answer ID, splice in a rationale, or claim reasoning verification from target match. Preserve rejected raw bytes and reasons.

Both accepted signs are required for a controlled credit. Missing stays missing. Exact length matching is a diagnostic flag, not a newly introduced support requirement. Record packet lengths and rationale_review_status=not_reviewed unless actual documented review exists.

Select a deterministic review sample of eight fitting tasks, four per family, before outputs. Export both packets and defects/missingness; do not replace missing tasks with favorable ones. Do not add reviewer-model calls. A systematic content defect must be reported and reviewed, not repaired by rewriting completed data.

Acquisition ceiling: 32 tasks * 2 targets * 2 attempts = 128 calls; 32,768 reserved output tokens. Shared accepted packets must be byte-identical across actor and clean/early interventions.

## 6. Replay, pairing, and calibration

For every compatible row with an accepted pair and each physical actor i:

1. Deep-copy the immutable initial snapshot.
2. Substitute only packet i with the selected controlled sign.
3. Rebuild own-state and delivered-peer prompts consistently; invalidate stale rendering/KV state.
4. Keep all other private packets, trusted task/options, original early material and identities unchanged.
5. Generate all three synchronous revisions from the cloned INITIAL packets only.
6. Run the same base-only readout on those revised packets.

Run K=2 suffix replicates per sign. Rerun all four suffix nodes; exact request/checkpoint/seed cache reuse is allowed only when auditable. Matching answer IDs are not cache identity.

Seed sets depend on stable task/condition, replicate, and downstream PHYSICAL receiver/stage. They do NOT depend on sign, intervention actor, display variant, branch execution order, or preceding generation length. Each physical receiver still has its own seed. Keep cache keys branch-content-specific even though paired seeds match. Do not use one mutable global RNG stream for the whole experiment.

Store Q+/Q-, per-seed outcomes and deltas. Values -1,-0.5,0,0.5,1 are legitimate at K=2; no clipping, fabricated smoothing, or rejection of negative credit.

Primary replay ceiling: 64 rows * 3 actors * 2 signs * 2 replicates * 4 nodes = 3,072 calls / 638,976 reserved output tokens.

Include the previously specified controls, without changing the primary estimator:

**Presentation order.** Prespecify eight fitting tasks, four/family, before donor results. On available clean/early rows repeat with reversed peer display order and reversed readout packet order. Keep physical actors, source labels, packet texts and node seeds fixed. No adapter relabeling. Cap 768 calls / 159,744 tokens. Primary training uses ORIGINAL-order credits only. For assignment sensitivity, replace control-row credits in the full bank while retaining the primary masks/NLL transform/solver settings. Report global-balance effects elsewhere; do not solve a separately standardized subset and call the difference an order effect.

**Natural-pair calibration.** Verify the five original natural-pair cell identities from the parent selector. Replay exactly those pairs as new CHILD-run calls using corresponding controlled-study suffix seeds. Cap 80 calls / 16,640 tokens. Compare only genuinely shared cells. Natural and controlled text differs, so exact agreement is not required. Calibration never enters the primary controlled bank, donor selection, or primary assignments. It does not reopen the parent. A discrepancy from the expected five cells is an explicit integrity issue, not permission to extend the cap.

## 7. Assignment and the mandatory pretraining review

Use the existing solver; do not invent another router. The new mask M records controlled-pair AND complete replay support. Missing rows retain base supervision but have no specialization weights.

Score original-context answer NLL under each actor's original private prompt. Use the existing correct-answer score definition without a gold rationale prefix. Score controlled positive-packet NLL under that same prompt if required by the bank. Those packets are synthetic supervised targets, not samples from the learner's policy.

Cap frozen scoring at 192 answer forwards and 192 positive-packet forwards. Count them separately from generation. Freeze the parent-approved training-bank-global NLL transform and its degenerate-variance rule; store statistics, and use the same transform for both nonuniform arms. No per-agent standardization or development-based choice.

```text
R_uniform[b,i] = M[b,i] / sum_j M[b,j]
a_local[b,i] = stop_gradient(transformed_answer_nll[b,i])
a_credit[b,i] = stop_gradient(transformed_answer_nll[b,i] - delta_ctrl[b,i])

min_R mean_b sum_i R[b,i] * a[b,i]
      + tau * mean_b sum_i R[b,i] log R[b,i]
      + lambda_balance * KL(mean_b R[b,:] || Uniform(3))
```

Use row sums one, exact zeros on missing cells, tau=0.2, lambda_balance=0.1, gamma=0/1 for local/credit, and lambda_spec=1. Treat answer likelihood as a proxy, not proof of learnability.

Report support, within-row credit differences, row-constant effects, R matrices, row entropies, task-specific allocation, column totals, fragile-weighted target exposure, and actor dominance. Compute task-mean L1(R_credit - R_local) so two conditions do not count as two independent tasks. Report K=1 component-assignment sensitivities using the same primary masks and NLL transform; do not choose the better seed.

Retain these predeclared gates:

- At least eight distinct fitting tasks with compatible pair support.
- At least eight distinct fitting tasks with a multi-eligible row.
- Complete compatible replay and needed score evidence.
- Task-average L1 contrast over multi-eligible support at least 0.10.
- At least eight individual fitting tasks with mean multi-eligible-row L1 contrast at least 0.10.

Use 1e-6 only for numerical identity. The 0.10 thresholds are engineering screens, not significance tests or proof of efficacy. Do not alter them after outcomes.

Stop BEFORE replay if acquired structural masks cannot meet support minima. Stop before training for failed support/contrast. Most importantly, stop AFTER the assignment report even when gates pass: I must review packet quality, seed/order sensitivity and actor dominance before explicitly invoking training. A passing manifest is not automatic training authorization.

Row-constant credits do not change relative allocation; singleton support fixes a row. Never add arbitrary per-agent offsets, random diversity rewards, new roles, or forced answers to manufacture differences. Structural support, assignment contrast, stability, and efficacy are separate statuses.

## 8. Implement all three training arms now

Provide:

```text
controlled_uniform_sft
controlled_local_specialization
controlled_continuation_specialization
```

All three start from identical parent effective actor values with fresh isolated optimizers. Each updates all three adapters sequentially. Backbone and base readout remain frozen; only the active adapter can change. Receiver loss and DPO are OFF, no ranking loss, no outer refresh, no adversarial co-evolution.

Share the exact same base rows, valid masks, synthetic correct-packet targets, loss definitions, fragile weights, data order, optimizer schedule and caps across arms. Only R differs. Never attribute a gain over frozen alone to credit when every trained arm receives additional synthetic supervision.

Preserve the approved objective:

```text
U = 64 base rows; B = controlled-eligible rows; m = 3
L_base = (1 / (m*U)) * sum_b sum_i answer_CE[b,i]
L_spec = (1 / B) * sum_b_eligible omega[b] * sum_i R[b,i] * packet_NLL[b,i]
L_total = L_base + lambda_spec * L_spec
```

If the actual audited implementation has an explicitly approved different reduction, document and retain it identically instead of silently changing relative scales. Base answer supervision covers every fitting row/actor, including missing-pair rows. Packet NLL is the existing length-normalized full-completion loss, not receiver answer-prefix CE.

Compute omega from NATURAL anchor correctness: 1/(1+initial_correct_actor_count), normalized once over the eligible frozen bank. Detach all weights and credits. Preserve global U/B/m reductions across minibatches and gradient accumulation; never independently normalize each actor's responsibility total. Avoid 0*NaN and unintended duplicate base/receiver losses.

Use inherited rank/modules/scaling/dropout/optimizer, learning rate 1e-5, microbatch one logical row, effective batch four, at most two passes and 32 updates per adapter. Maximum 96 updates per arm and 288 total. Derive actual forwards and token exposures; full-support maxima are 1,152 base and 1,152 packet presentations across trained arms, excluding frozen scoring forwards.

Each arm begins from initialization, not another arm's output. Freeze its bank/R throughout sequential updates. Snapshot complete teams after their scheduled updates. The same updated adapter serves private AND revision turns: protocol/readout are fixed, but learned revision behavior can change.

Evaluate the final capped checkpoint; do not select a checkpoint or budget using development outcomes. Implement this stage fully even though execution waits for explicit review.

## 9. Natural development evaluation

Evaluate frozen initialization plus all three trained systems on all 32 unchanged development tasks, clean and the same fixed early condition. No GPQA, final test, exchange/adaptive attack, extra samples, or new dataset.

For every system/task/condition, generate:

- Three natural private packets, then freeze them.
- Independent vote without a model call.
- One frozen synthesis from private packets.
- Three synchronous revisions from initial private peers.
- One frozen synthesis from revised packets.

Eight calls per system/task/condition; cap 2,048 calls / 425,984 reserved output tokens.

No synthetic correct packets, assigned answers, generator instructions or gold prefixes enter evaluation. The early-advisory attack remains the declared low-trust condition. Match task, option order, payload, physical roles, node seeds and decoding across systems; checkpoint changes intentionally invalidate generation caches.

Report individual/mean/best accuracy; initial coverage and joint failure; coverage above the best member; each actor's unique correct coverage; valid correct/wrong mixed support separately from wrong-answer disagreement; all-correct degradation; natural vote/synthesis/debate success; erasure/utilization/construction/readout loss; and per-task paired changes versus uniform/local/frozen.

More mixed teams is not success if it comes from losing correct answers. More fitting likelihood is not held-out generalization. More coverage is not a deployed gain unless readout uses it. Thirty-two task groups, not calls/agents/conditions, are sampling units. Preserve undefined denominators and small/degenerate interval cautions. This is one-seed development feasibility, not full PACT or an adaptive robustness certificate.

## 10. Budget, stages, and persistence

Derive these ceilings in code and regression-test the arithmetic:

| Stage | Maximum new generation calls | Reserved output tokens |
|---|---:|---:|
| Controlled packets | 128 | 32,768 |
| Primary controlled replay | 3,072 | 638,976 |
| Reverse-display sensitivity | 768 | 159,744 |
| Natural-pair calibration | 80 | 16,640 |
| Four-system evaluation | 2,048 | 425,984 |
| TOTAL | 6,096 | 1,274,112 |

Pretraining generation ceiling is 4,048 calls / 848,128 output tokens. These are worst-case caps, not intended consumption, duration, VRAM guarantees or billing forecasts. Add actual input tokens, frozen scoring, training forwards, failed attempts, legitimate cache reuse and unknown compute units separately. Parent calls do not create a reusable new-call allowance.

Default notebook/CLI operation is metadata-only plan/characterization. Use explicit stage invocations with immutable plan hashes:

```text
plan -> acquire -> build/support -> replay/controls -> score/assign/report
                                                      STOP FOR REVIEW
train explicit arm -> evaluate -> report/export
```

Names are capabilities, not claims existing commands exist. Adapt the actual CLI and give me executable commands at handoff. Keep notebooks thin and scientific logic in the package. Include Git ref, new child ID, parent bundle, actual durable initialization path, plan/config, scratch/persistent roots and resume parameters.

Implement all stages, but no Run All path may silently cross the assignment-review checkpoint or launch the entire maximum experiment. Do not make another coding pass a prerequisite for invoking already planned training after review.

Reuse scratch-first storage, immutable shards, bounded verified persistence, local-first ZIPs, full optimizer-boundary checkpoints and compact inference restore. No broad storage rewrite. Resume preserves attempts, consumed budgets, stage/arm/actor, optimizer/scheduler/RNG/sampler position, accumulation boundary, bank/pair/R/transform identities and completed steps. A finished arm is not trained again during report recovery. A review ZIP cannot replace omitted tensors.

Cache keys include full branch content, source/estimator, original snapshot/row hashes, controlled pair hashes, intervened actor, display variant, base/adapter/effective precision/template/decoding and per-node seed. Matching seed namespaces do not permit cache collisions between different prompts or intervention signs.

## 11. Acceptance tests

Add focused tests and run appropriate existing regressions. Report real passes/skips/failures. Tests must include:

1. Immutable safe parent import; stopped parent bytes/counters/outcome unchanged.
2. Legacy natural-bank rejection of synthetic private pairs; explicit new source required.
3. Symmetric generator template, fixed wrong target, base-only adapter isolation, attempt caps, first-valid acceptance, honest rejection/missingness.
4. Identical accepted pair bytes across physical actor and clean/early interventions.
5. Clone substitution updates own and peer views, preserves other packets/early data and cannot mutate anchors; no revision-to-revision leakage.
6. Common per-node seeds across actors/signs/order controls; different branch content remains different cache identity.
7. Deterministic truly symmetric fixtures yield unchanged allocations; equal per-row credits and singleton masks leave R unchanged. Do not assert arbitrary stochastic real teams must have identical sampled credits.
8. Nondegenerate fixtures yield known assignment contrast without artificial offsets; negative/zero/missing credits remain distinct.
9. Display reversal changes order only; primary credit is never selected from control results; calibration remains separate.
10. Independent verification of answer masks, causal shifting, full-packet loss, global NLL transform, sparse support and accumulated gradients with unequal responsibilities/target lengths.
11. Every arm has identical source/target exposure and initial tensors; inactive/backbone/readout isolation and fresh optimizer state.
12. Natural evaluation cannot load controlled packets or gold prefixes; checkpoint-specific cache invalidation and exact paired-comparison validation.
13. Pre-replay support stop, practical-contrast stop, explicit pretraining review, exact budgets, missing-data reporting and negative-result paths.
14. Interrupted mock acquisition/training, compatible resume without duplicate calls/updates, and report/export/import round trip.
15. Full mock acquisition -> controls -> assignments -> three-arm training -> four-system evaluation. Optional tiny-neural tests exercise actual weighted adapter updates without claiming pretrained-model efficacy.

## 12. Reports, documentation, and final handoff

Produce standard manifests/environment/checksums plus equivalent artifacts for:

```text
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

Keep unexecuted stages explicit rather than creating fake result values. Distinguish software implementation, CPU/tiny-neural tests, real GPU execution, assignment evidence and scientific efficacy. Raw imported text remains untrusted. Preserve full durable tensors separately; no GPQA content belongs in this experiment.

Update AGENTS.md concisely, methodological source/estimand notes, implementation status/decisions, experiment ledger and Colab runbook. Do not fill manuscript placeholders or overwrite old methods/results. Record the synthetic target provenance and the limits of slot-based credit.

Finish with:

- What already existed, what changed, and actual files modified.
- Offline parent findings supported by accessible records, and missing prerequisites.
- A clearly labeled fixture showing one shared pair, all actor/sign cloned views, seeds and resulting R matrices.
- Tests actually run and failures/skips/unverified GPU components.
- Exact local and Colab commands, stage ceilings, required real artifacts, support stops and review boundary.
- The review bundle I should return after replay/assignment, then after separately authorized learning/evaluation.

Implement the smallest complete path now. Do not execute experiments or promise a positive result. The question is whether controlled continuation credit yields a meaningful allocation that helps natural team outcomes beyond learning from the same examples without that credit.
