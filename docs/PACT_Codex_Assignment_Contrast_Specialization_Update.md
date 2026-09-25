# PACT codebase update: assignment contrast and one-round specialization

Version: 2026-09-25
Scope: local implementation, offline analysis, CPU tests, and a bounded Colab-ready study. This document does not report a new experiment.

You are updating my existing PACT research repository. Implement the smallest COMPLETE path that tests whether communication-conditioned responsibility assignment creates useful specialization. Do not start a new repository or replace the existing package.

## 1. Read first; preserve the completed evidence

Inspect Git status, relevant AGENTS.md files, the actual source tree and existing tests before editing. Read the proposal, implementation specification, implementation decisions/status, experiment ledger, completed controlled-receiver audit, and completed GPQA-Diamond support audit. Locate actual paths; titles and suggested command/module names in this document are not proof those paths exist.

My workflow is:

    local Codex development and CPU tests
      -> my review, GitHub commit/push
      -> pinned checkout and actual GPU runs in Google Colab
      -> returned artifacts for local Codex analysis

Do not launch GPU experiments, download pretrained models locally, commit, push, change remotes, or disturb unrelated work. No Slurm/PBS, SSH-to-cluster workflow, Docker daemon, paid inference API, or multi-GPU dependency. Use the working dependency stack unless a concrete defect requires a documented change.

### Current scientific state

Use the actual retained audits to verify this context:

- Full PACT, including jointly refreshed specialization and receiver learning, has NOT run.
- The controlled receiver study ran 24 updates per trained arm. Frozen, task-SFT, and receiver-SFT arms had identical correctness on all 57 controlled receiver responses. Likelihoods changed; extra receiver repair was not demonstrated.
- Real private counterfactual replay has executed. Selected validation examples produced positive and zero continuation credits. A small two-task TRAINING bank also produced valid pairs. Neither proves that the credits change responsibility assignments or that specialization improves generalization.
- GPQA support run `qwen3-gpqa-diamond-support-001` completed 32 development tasks and 256 calls. It had two valid mixed-support tasks, initial coverage 9/32, best-member accuracy 9/32, and vote/synthesis/debate accuracy 7/32 each. All correct coverage was already in agent0. Both minority-correct cases lost the correct answer during revision; independent synthesis also failed on both, so terminal accuracy did not fall relative to synthesis.
- The GPQA partition is 32 development-exposed items, 164 protected items, and two recorded repeated-option exclusions. Do not revert to an assumed 166 protected items.
- Dataset difficulty did not resolve useful coverage in that configuration. Close that run. Do not increase its draws, alter its prompts, add attacks, enable thinking, or consume its protected remainder.

Provenance anchors from the latest supplied audit:

    GPQA clean source: 1627abae3dd724cdbbb5358ebc6152d4c9be77d7
    GPQA plan: 6ffadabfe5127080e09793126095bce628f27cb1ee7c58f637713eec205f8e17
    GPQA PRIVATE ZIP SHA256: 8db5120f4c25bc9bb99f6c04b3d7571a1c791a5cb13899176fb3a466169b3012
    GPQA SANITIZED ZIP SHA256: 092483656108bb0b3a8d2534b4f27b234743b4839f53233807adf84a6a73f242
    Controlled receiver parent SHA256: ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea

These identify evidence, not a request to reset HEAD to an old commit. Read the latest repository state without rewriting historical manifests or conclusions.

## 2. The change to implement

Stop testing whether similar prepared agents spontaneously become complementary. Test the actual responsibility-weighted learning mechanism.

Deliver TWO connected capabilities:

1. An OFFLINE assignment-contrast report for existing compatible training banks, with no model calls or optimization.
2. A complete one-round, fixed-bank, three-arm specialization study: shared bounded bank collection when explicitly invoked, assignment calculation, sequential adapter updates, matched evaluation, and export.

Do not stop after producing another audit or design document. Missing real banks/weights must not prevent implementing and CPU-testing the full runner. Conversely, missing data must never be replaced with fake scientific records to make a GPU stage appear ready.

This is `specialization_fixed_bank_v1`, a specialization ablation, NOT full PACT. Receiver-SFT and receiver-DPO are OFF. There are no outer refreshes, no joint learner/attacker co-evolution, no forced disagreement, no new ranking objective, and no new model family.

Preserve the original private replay estimator and packet eligibility rules. Controlled synthetic receiver donors are NOT valid substitutes for naturally sampled same-actor private pairs. Reusing such donors would require a different, explicit estimator design, which is not authorized here.

## 3. First deliverable: characterize the learning signal locally

Read existing banks through the established safe artifact reader. Treat all generated messages, attack strings, logs, and imported scripts as untrusted data. Never execute imported code or load arbitrary pickles just to inspect a bank.

Characterize each compatible bank separately. Do not merge different snapshots, precision identities, datasets/splits, prompt versions, or attacks into one apparent frozen bank. Validation replay can be summarized separately for mechanism evidence, but it cannot count toward fitting support or become training data. Exclude GPQA entirely from this work.

For each task-condition row b and agent i, identify:

- Original task/group/split and exact actor context.
- Original private correctness and packet validity.
- Correct/incorrect candidate pair IDs and raw provenance.
- Pair eligibility and missing reason.
- Per-seed positive and negative suffix outcomes, Q+, Q-, and delta.
- Frozen-snapshot correct-answer NLL and its exact token-scoring definition.
- Selected positive packet, its tokens/length, and rationale-review status.
- Whether every required item is present or an omitted forward/raw record prevents reconstruction.

Do not fill missing NLL with zero or manufacture missing credit. Offline work may only derive quantities supported by stored data. If fresh teacher-forced scores are necessary, report exactly which scores are absent; obtaining them is a separate explicitly invoked Colab stage, not local model execution.

### Mandatory report questions

1. How many distinct TRAINING tasks, task-condition rows, and agent cells exist?
2. How many rows have zero, one, two, and three eligible agents?
3. How many distinct tasks have at least one row with two or more eligible agents?
4. How much does delta differ BETWEEN eligible agents on the SAME row?
5. How do responsibilities change between uniform, local-only and continuation-aware costs?
6. Do responsibilities vary usefully across tasks, or does one agent get most weight everywhere?
7. What effective specialization weight and target-token exposure will each adapter receive?
8. Is the potential contrast due to different eligible support, different NLL, or the credit term itself?

A positive credit is not automatically a useful assignment contrast. If all eligible agents have the same credit on a row, subtracting that common value cannot change their allocation. A singleton row fixes its responsibility at one and cannot establish a credit-driven selection effect.

Export at least:

    bank_characterization.json
    assignment_rows.jsonl
    assignment_contrast.json
    assignment_contrast.md
    provenance_and_missingness.json

Use actual project conventions rather than introducing a redundant reporting framework. Include task-level and cell-level views without inflating repeated conditions into independent tasks.

## 4. Assignment definitions: identical masks and frozen costs across arms

Let M[b,i] identify a valid natural private pair AND complete matching replay evidence. B is the count of eligible rows; rows with no valid cell have no specialization assignment and still receive base supervision.

Calculate the three responsibility matrices on the SAME support:

    R_uniform[b,i] = M[b,i] / sum_j M[b,j]

    a_local[b,i] = stop_gradient(answer_nll_transformed[b,i])

    a_credit[b,i] = stop_gradient(answer_nll_transformed[b,i] - gamma * delta[b,i])

Solve the existing masked problem for the latter two arms:

    mean_b sum_i R[b,i] * a[b,i]
      + tau * mean_b sum_i R[b,i] * log R[b,i]
      + lambda_balance * KL(mean_b R[b,:] || Uniform(3))

subject to row sum one, nonnegative weights, and exact zero on unavailable cells.

Use the existing numerical solver and tests; do not create a second approximate router. Freeze solver settings before outputs from the development evaluation are inspected.

Primary proposed hyperparameters, inherited from the original design:

    gamma = 1.0 for continuation-aware; 0.0 for local-only
    tau = 0.2
    lambda_balance = 0.1
    lambda_spec = 1.0

These are starting design settings, not known good values. No search over gamma/tau after observing the evaluation result.

### Answer-loss scaling

Inspect the already recorded implementation decision on raw versus standardized answer NLL. Reproduce historical analyses under their declared transform. For the new bank, resolve and freeze the transform in its plan. If still unresolved, explicitly adopt training-bank-global standardization over valid cells as the new preset's interpretation of the proposal appendix; save its mean/std/degenerate-variance handling. Do not normalize separately per agent or use development/test data. Both local and credit arms use the identical transform. Raw-NLL contrast can be reported as a separate offline sensitivity, not selected post hoc for a better result.

### Contrast diagnostics

Report, at minimum:

    D_credit_local = mean_b ||R_credit[b,:] - R_local[b,:]||_1
    D_local_uniform = mean_b ||R_local[b,:] - R_uniform[b,:]||_1

Provide both all-eligible-row and multi-eligible-row values, plus task-grouped summaries. Also report row entropies, column sums, fragile-example-weighted column sums, unique-task support per agent, and singleton counts. A changed argmax alone is not sufficient; quantify the mass moved.

State the numerical comparison tolerance. For the default use 1e-6 for reporting numerical identity, not as a scientific effect-size threshold. A tiny nonzero contrast is technically different but may be practically uninformative.

### Required symmetry tests

- With full support and identical costs, the symmetric solution is uniform.
- Adding/subtracting a row-constant cost does not change the solution.
- Equal per-row credits leave local and credit assignments unchanged, even if those credits are all positive.
- A singleton row has identical responsibilities in all arms.
- An unavailable cell remains exactly zero and cannot be made eligible through a numeric floor.
- At equal local costs, an isolated positive credit perturbation changes allocation in the expected direction, under a suitable nondegenerate fixture.
- A large global preference for one actor is reported rather than relabeled complementary specialization.

## 5. Readiness: do not confuse executability with research evidence

Maintain separate fields for:

    artifact_integrity
    split_and_snapshot_compatibility
    pair_support
    assignment_contrast
    training_executed
    evaluation_executed
    scientific_efficacy

A two-task historical bank can characterize mechanics. It does not become an adequate learning experiment because its credits are nonzero.

For the proposed bounded NEW study, predeclare engineering support minima:

- At least eight distinct fitting tasks with eligible private pairs.
- At least eight distinct fitting tasks with at least one multi-eligible row.
- Complete needed NLL/pair/replay records for cells used in the assignments.
- Credit-versus-local mean L1 contrast over multi-eligible rows greater than the numerical-identity tolerance.

These are feasibility checks only, not power calculations or sufficient evidence of useful credit. Report how many tasks and how much responsibility mass actually differ. Do not claim a tiny effect is scientifically meaningful merely because it exceeds 1e-6.

If a gate fails, retain all evidence, export the reason, and do not quietly train a base-only model under a PACT name. Do not lower minima, change seeds, or add tasks after seeing support. Still finish implementing the complete runner and mock end-to-end validation locally. The correct result may be `insufficient_assignment_support` or `no_assignment_contrast`.

No receiver hold/repair minimum and no DPO-pair minimum applies to this specialization-only study. Do not import the receiver study's readiness veto.

## 6. New-bank preset: bounded and declared BEFORE GPU work

If existing compatible TRAINING banks cannot support the comparison, provide the following explicitly NEW acquisition preset. It must be fully specified, dry-runnable and frozen before inference; it must not start automatically during a local audit or notebook Run All.

Suggested identity:

    study: qwen3-specialization-contrast-001
    bank source: natural_private_replay_bank_v1
    method variant: specialization_fixed_bank_v1

These are proposed names. Reconcile with actual repository conventions without reusing a completed run ID.

### Tasks and exposure

- Pinned ARC-Challenge and original English LogiQA TRAINING sources only.
- Select 64 source groups before outcomes: 32 fitting (16 per family) and 32 held-out development (16 per family).
- Use the existing eligible training pool where available. Exclude prior preparation-fitting IDs, receiver-fitting IDs, repeatedly inspected development IDs, and their known duplicate groups. Inspect the actual exposure ledger rather than inferring exposure from filenames. Clearly report remaining limitations of lexical rather than semantic screening.
- No official test items, no GPQA items, no selected validation replays as training, and no synthetic controlled donors.
- If declared fresh groups are unavailable, stop planning with the actual count. Do not silently relax exclusions or shrink the cohort.
- Freeze the two partitions, option mapping, task order, seeds, exposure tags and two-condition assignments before any generation. These are development data, not final-test evidence.

### Conditions

Use clean and ONE fixed early-advisory condition. Both are applicable to every inference comparison. Do not add exchange attacks, adaptively search attacks, or introduce new attack-generation models in this first ablation.

Use the existing audited fixed-pool attack registry and envelope. Name the exact existing strategy/version, seeded task-to-payload rule and length cap in the frozen plan. Use the same task-payload assignments across arms. Labels used offline by the existing attack builder remain outside trusted defender metadata. Do not silently replace the audited attack semantics.

This makes 32 fitting tasks x 2 conditions = 64 bank rows. Every task-condition appears exactly once as a natural anchor; additional replay branches are not additional task samples.

### Frozen initialization

Use the same effective frozen-preparation team identity used by the completed GPQA support study, not task-SFT or receiver-SFT weights. Expected effective actor hashes from its receipt are:

    agent0: eef7b26388dabd812e7519b6cef0ececd1737bd9989c5a5715378694dcbad7ad
    agent1: 505e04c7518134abfc38222ab7e507ee392c1913292cc387bcc2c7ddd74ce18c
    agent2: 07ae09c5803bd2603beb88097208da3929a61b98a9f1bd691b4244a53cd79662

Verify against actual recorded receipts and real durable weights. Preserve the disclosed nonfocal FP32 -> BF16 -> FP32 history; do not pretend a reload from an older preparation file has identical effective values. Do not repair historical precision silently. Record tensor values/hashes, stored/load/train dtypes and any exact-value-preserving promotion needed for training. A numeric mismatch fails preflight or requires a distinct explicitly approved configuration.

Review ZIPs are not weights or optimizer checkpoints. Use the established full/compact initialization restore. Every trained arm resets all three actors to the same declared initial tensor values with fresh independent optimizer state. No arm starts from another arm's output.

Keep the pinned Qwen3-8B base/tokenizer/template, non-thinking mode, BF16/SDPA backbone, 4,096-token total cap, temperature 0.7 / top-p 0.8 / top-k 20 for private and revision calls, 256-token private/revision caps, and 64-token frozen readout caps. Preserve other current decoding fields. No model, mode, context, rank, or attention changes to force diversity.

### Collection per fitting row

1. Generate three natural initial packets and freeze all of them.
2. Complete the existing synchronous three-revision/one-readout anchor trajectory.
3. Generate four ADDITIONAL private candidates per actor under that actor's exact unchanged private prompt and frozen snapshot: 12 alternative calls per row. Use the existing audited candidate-selection policy; do not substitute a different-context completion or use the anchor as an uncounted extra candidate.
4. Select at most one valid label-correct/valid-wrong pair per actor according to the prespecified rule. Abstentions, invalid and length-limited candidates are not valid wrong packets. Do not repair labels or invent rationales. Keep length-match flags.
5. Missing pairs remain missing. With no support, keep ordinary base-label supervision but no specialization cell.
6. For every supported pair, execute K=2 positive and K=2 negative suffixes. Rerun all three revisions and final readout per suffix. Fix the other private packets, early payload, snapshot and corresponding per-node seeds.
7. Score correct-answer NLL under each original private context with the existing precise answer-token definition. No gold rationale may precede the scored answer. Cache selected-positive packet NLL where the existing bank format requires it.

The primary bounded implementation reruns full short suffixes. Tested identical-request reuse may reduce ACTUAL calls, never change the logical estimator or hide attempts. Do not rank rows by observed credit and collect only favorable ones.

### Stage-level stop

After candidates, if even the candidate masks cannot meet the declared task-support minima, export and stop before spending the suffix budget. If that gate can pass, execute the frozen replay plan, compute assignments and export contrast. Training is a separate explicit stage. No implicit retry-until-success or replacement task acquisition.

## 7. Three training arms: vary weights, not data or infrastructure

Implement:

    uniform_supported_sft
    local_specialization
    continuation_specialization

The first name matters: this is uniform allocation over the SAME eligible packet support, not a claim to reproduce every possible independently adversarially trained baseline.

Every arm receives:

- Ordinary private correct-answer supervision on ALL 64 fitting bank rows for every actor, including rows with missing replay pairs.
- Exactly the same eligible positive packet targets and source masks.
- The same fragile-example weights omega[b] = 1/(1 + initial_correct_actor_count[b]), normalized to mean one over the declared eligible assignment bank.
- The same task/condition multiplicities, base loss, lambda_spec, optimizer settings, batch order and update cap.

Only the responsibility matrices differ.

Use the whole eligible frozen bank as one assignment batch for this small study; solve once per arm and keep assignments fixed through the round. Record this precise interpretation of the proposal's assignment minibatch. Do not recompute assignments after actor0 updates while actors1/2 are still at initialization.

The supervised correct packet loss remains length-normalized full COMPLETION NLL on the selected sampled packet as specified in the original specialization method. Prompt/peer/padding tokens are masked. Audit EOS inclusion, truncation and token shifts explicitly. Do not silently replace this with the recently introduced receiver-answer-only target. Label-correct rationales are not automatically verified explanations; record that limitation consistently across arms.

Base supervision uses the current audited private answer-token target and mask. Do not add or double-count receiver supervision.

### Objective and normalization

Define one explicit team objective and implement its per-adapter summands faithfully. For example, with U=64 base rows, B eligible rows and m=3:

    L_base = (1 / (m*U)) * sum_b sum_i ell_answer[b,i]
    L_spec = (1 / B) * sum_b_eligible omega[b] * sum_i R[b,i] * ell_packet[b,i]
    L_total = L_base + lambda_spec * L_spec

Use the already approved base reduction if different; document the exact resulting equation and apply it identically across arms. Do not silently change effective lambda_spec through a reduction change.

When batching over all U rows, implement the corresponding B-versus-U denominator adjustment for sparse specialization cells. Skipping missing cells must not replace the global denominator with a per-agent or per-minibatch weight sum. Test the accumulated gradient against an independently computed full-bank fixture objective.

Do NOT normalize each actor's specialization weights to sum one separately: doing so can erase the intended difference in total responsibility. Do NOT add a floor to unavailable cells. Avoid `0 * NaN` from missing scores. Responsibilities, omega, NLL transforms and credits are detached labels, not differentiated estimators.

### One round, all three actors

- One frozen collection bank; one assignment solve per arm; no outer refresh.
- Each arm updates all three adapters sequentially. The same adapter serves an actor's private and revision turns at evaluation.
- Only the active adapter has gradients/optimizer state resident where practical. Assert backbone, inactive adapters and base readout do not change during its update.
- Microbatch one logical bank row, effective batch four, learning rate 1e-5, at most two complete passes and at most 32 optimizer updates PER ADAPTER, whichever cap is reached first.
- With 64 base rows and two passes this is 32 updates per adapter, 96 per arm, at most 288 across the three trained arms. Count base and eligible packet forwards separately; they are not separate optimization steps.
- Inherit rank, target modules, scaling, dropout and optimizer implementation from the audited prepared initialization/working trainer. Do not reinitialize adapters or migrate trainers because the original paper had a different nominal effective batch.
- Freeze the actual schedule in the plan. Do not stop/restart or select checkpoints after inspecting held-out outcomes. Evaluate final capped checkpoints, even when results are negative.

Because the adapters are shared across turns, specialization can alter revision behavior even with receiver loss disabled. Call the PROTOCOL and READOUT fixed, not the learned receiver policy fixed.

## 8. Matched evaluation: natural outputs, no constructed diversity

Evaluate FOUR systems: frozen initialization plus the three trained arms.

Use all 32 held-out DEVELOPMENT tasks in clean and the same fixed early condition. No training or bank selection uses these outcomes. These tasks are held out from optimization but become development-exposed after this study.

For every system/task/condition:

1. Generate three natural private packets, then freeze them.
2. Compute independent vote with the existing declared rule.
3. Run independent synthesis from those private packets.
4. Run the three synchronous revisions from original private peers only.
5. Run the same frozen base readout on revised packets.

Eight generation calls per task-condition: 3 private + 1 independent synthesis + 3 revision + 1 debate synthesis. No forcing answer choices, correct donors, per-actor option reshuffling, extra candidate draws, exchange attacks, adaptive search or GPQA evaluation.

Match task, input/option order, payload, sender envelope, node seeds, decoding and role across arms. Checkpoints intentionally differ, so generation caches must invalidate on actor identity; paired comparison is not cache identity. Do not reuse a frozen actor output for a newly trained actor just because prompts/seeds match.

### Primary scientific reports

For clean and early separately, report:

- Each actor's initial accuracy, mean and best initial accuracy.
- Initial coverage c and joint failure 1-c.
- Coverage gain over the best member: c - max_i accuracy_i.
- Valid correct/wrong mixed-support task count, separately from answer disagreement and abstentions.
- N0=0/1/2/3 counts, unique correct coverage per actor, and pairwise error-overlap denominators.
- Whether increased diversity is actually fewer all-wrong teams or merely loss of all-correct teams.
- Independent vote/synthesis and debate terminal success.
- N0 -> N1 transitions, utilization u, construction k, erasure d and readout loss.
- Per-task paired changes versus frozen, uniform and local arms.
- Clean utility and individual-strength trade-offs, not just a larger mixed-team count.

Use the existing exact metric identities and explicit null/zero-denominator handling. All 32 task groups are sampling units; their clean/attacked trajectories, three members and both protocols are clustered, not independent tasks. Single training seed and small cohorts support a feasibility conclusion, not a full paper claim or equivalence test.

Report assignment changes together with learning changes. Larger D_credit_local alone is not successful complementarity. Higher fitting likelihood alone is not held-out efficacy. A coverage gain alone is not a deployable robustness gain; the final protocol must use it.

Fitting-loss diagnostics can be exported from executed training and any already recorded scores. Do not add an unplanned fitting free-generation sweep or teacher-forced development-scoring matrix.

## 9. Hard budget: planner-derived, not an invitation to consume the cap

The proposed fresh-bank preset has these worst-case ceilings:

| Stage | Calls | Reserved output tokens |
|---|---:|---:|
| 64 fitting anchor trajectories, 7 calls each | 448 | 102,400 |
| 64 x 3 actors x 4 private alternatives | 768 | 196,608 |
| Up to 192 pairs x 4 suffixes x 4 calls | 3,072 | 638,976 |
| Evaluation: 4 systems x 32 tasks x 2 conditions x 8 calls | 2,048 | 425,984 |
| TOTAL | 6,336 | 1,363,968 |

Formula checks:

    anchor tokens = 3*256 + 3*256 + 64 = 1,600
    suffix tokens = 3*256 + 64 = 832
    paired-suffix tokens per pair = 4*832 = 3,328
    evaluation tokens per system/task/condition = 3*256 + 64 + 3*256 + 64 = 1,664

The initial anchor/candidate stage alone is capped at 1,216 calls / 299,008 output tokens. Replay scales with actual valid pair count, not the maximum. Default local characterization costs ZERO model calls. Existing exact compatible artifacts may reduce work only through explicit logged reuse; do not count old calls as new or claim stale banks are current.

This is larger than prior support-only screens. Print stage ceilings and require explicit Colab stage invocation with the frozen plan hash. Notebook defaults are `plan`/offline characterization only, never an automatic all-stage run. Do not present these caps as time, memory, subscription-credit or billing forecasts.

Additional non-generation work:

- At most 192 original-context answer-NLL scoring forwards for the new bank.
- At most 192 positive-packet scoring forwards if required by the existing bank schema.
- At most 288 optimizer updates across trained arms.
- Derive and print base-target forwards, packet-target forwards, presentations and token counts from the realized masks and exact batching plan. Teacher-forced tokens are not generated tokens.

There are no receiver scoring/reference forwards, no attacker-model calls, and no extra smoke examples. GPU smoke, if used, is an outcome-independent prefix of the planned requests and is reused thereafter. No separate throwaway fitting updates alter the declared initialization.

Every dispatched retry/failed attempt counts. An ambiguous in-flight call is not silently free. If the budget is exhausted or an integrity error occurs, preserve partial results and stop. Do not silently shorten context or change precision to finish a run.

## 10. Required implementation surface

Adapt the existing CLI conventions. Provide capabilities equivalent to:

    characterize-assignment-bank    # local, no model dependency
    specialization-plan             # source/split/initialization + exact budgets
    specialization-collect          # anchors, four alternatives per actor
    specialization-replay           # only eligible cells, bounded paired suffixes
    specialization-assign           # three matrices + contrast + support verdict
    specialization-train            # explicit arm, all three actors, guarded resume
    specialization-evaluate         # four systems, exact paired natural protocol
    specialization-report
    specialization-export

These names are proposed, not commands to advertise before they exist. Deliver exact ACTUAL commands/cells at handoff. Prefer extending existing collect-bank/replay/assign/train/evaluate components to parallel implementations.

Provide a thin notebook with Git commit, plan hash, new run/bank IDs, declared initialization snapshot, raw source paths, scratch/persistent roots, stage and resume mode. Actual code lives in the package.

Preserve scratch-first writes, immutable shards, checksums, bounded persistence, complete-marker semantics, compact initialization versus full optimizer resume, and local-first export. A completed arm must not be retrained during report recovery. Resume must restore actor/arm, optimizer/scheduler, RNG/sampler position, accumulation boundary, bank and responsibility hashes, base reduction and initialization identity.

Do not reopen historical recovery work or inventory every old ZIP merely to implement this module. Read only the evidence needed for the bank/identity/exposure checks.

GPQA raw material remains outside Git/private. This study's outputs must not copy GPQA questions, labels, prompts or decodable tokens. No full GPQA source access is required by this update.

## 11. Tests and acceptance criteria

Use deterministic invented tasks and optional tiny LOCALLY INITIALIZED neural models. Default tests need no network, pretrained weights or local GPU.

Required tests include:

1. Bank characterization rejects cross-snapshot/split/precision mixing and reports missing NLL without inventing it.
2. Validation/GPQA/synthetic-donor private records cannot become fitting bank pairs.
3. Assignment symmetry, row-constant invariance, identical-credit invariance, singleton invariance, masks, solver convergence and numerical reference agreement.
4. R_credit/R_local differ on a deliberate nondegenerate fixture and not on a shared-credit fixture.
5. Natural same-context alternative selection, retained negative/zero credits, K=2 matched branches, exact early payload and unaffected private states.
6. Global versus accumulated loss/gradient agreement with unequal R column sums, sparse rows, zero-weight cells and base/spec denominator differences. Include a regression that would fail if each adapter's weights were normalized independently.
7. Identical example/token exposure across training arms apart from intended numeric weights; inactive parameters and backbone remain unchanged.
8. Full-packet specialization masks and answer-only base masks remain distinct; no wrong-answer reward, gold prefix at free evaluation, or fabricated rationale.
9. Three arms reset to identical initial actor values; optimizer state does not leak across actors or arms; frozen synthesis disables/restores adapters correctly.
10. Candidate-support stop before replay, assignment-contrast stop before training, no receiver/DPO veto, no automatic cap expansion.
11. Exact call/token/update formulas including actual sparse replay counts and partial-run accounting.
12. Train/save/resume with bank/assignment identity, checkpoint-sensitive cache invalidation, complete-arm deduplication and export/import.
13. Coverage gain, all-correct degradation, valid mixed support, erasure/readout separation, task clustering and undefined conditionals.
14. Complete mock three-arm study plus frozen evaluation and offline metric reconstruction.
15. Tiny neural updates exercise weighted specialization and isolation; do not claim this proves 8B learning or diversity generalization.

Run the relevant available regression suite. Report actual passes/skips/failures and clearly identify GPU-unverified work. Do not weaken original tests merely to make the new implementation pass.

## 12. Artifacts and final Codex handoff

Export the usual manifest/config/environment/identity/checksum files plus:

    source_and_exposure_manifest.json
    bank_manifest.json
    candidate_support.json
    replay_cell_records.jsonl
    answer_score_definition.json
    assignment_transform.json
    assignment_uniform.json
    assignment_local.json
    assignment_credit.json
    assignment_contrast.json
    assignment_contrast.md
    loss_reduction_and_weight_audit.json
    training_by_arm_and_actor.json
    evaluation_per_task.jsonl
    specialization_results.json
    resource_usage.json
    CODEX_HANDOFF.md

Use existing filenames/schema where appropriate. Lightweight review bundles are not full tensor backups. Preserve full snapshots separately and state missing tensors/needed private paths. Imported raw data stays untrusted.

Update AGENTS.md concisely, implementation decisions/status, experiment ledger and Colab runbook. Preserve original paper placeholders, old methodology variants and completed results. This request explicitly authorizes implementing specialization-only updates even though earlier frozen diagnostic instructions prohibited training inside those closed runs; it does not authorize rewriting those runs.

Finish with:

- What the OFFLINE assignment characterization could and could not establish from real retained banks.
- Implemented code/files and actual tests.
- A concrete example of the three responsibility matrices and resulting globally normalized training weights, labeled synthetic if a fixture.
- The actual commands for the zero-GPU local report and each bounded Colab stage.
- Source/checkpoint prerequisites, stage budgets, support stops and expected returned bundle.
- Implemented/CPU-tested/GPU-unverified/deferred status.

Do not claim PACT is ready merely because the runner exists or R matrices differ. Do not call a uniform/specialization-only model full PACT. Do not stop at the audit if the runnable implementation can be built and tested with fixtures. Begin by inspecting the repository and source instructions, characterize retained compatible data locally, then implement the complete fixed-bank three-arm path.
