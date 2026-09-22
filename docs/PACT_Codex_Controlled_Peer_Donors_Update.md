# PACT codebase update: controlled peer donors for receiver supervision

You are updating my EXISTING PACT repository. Implement the smallest complete local-to-Colab path for a new, explicitly versioned receiver-context source. Do not start a new repository, redesign the project, or stop after writing a plan.

## 1. Read first, then implement

Inspect Git status, AGENTS.md, package layout, existing tests, notebooks, and current CLI. Preserve unrelated changes. Read the original proposal, implementation specification, receiver-supervision update/methodology, latest consolidated project audit dated 22 September 2026, the completed receiver collection audit, and donor inventory. Locate their actual paths rather than assuming the example paths below exist.

The latest supplied audit identifies the executed receiver collection source as:

- Git commit: `fd38b5e90bf6e5c648922405d46094abbc2449b2`.
- Executable hash: `b179e7d109cef2533c87466c43de1bb3df612dca1118b5078b71cfbc14990cc7`.
- Parent run: `qwen3-receiver-supervision-001`.

These identify historical evidence; they are NOT instructions to reset a newer working tree. Verify the actual parent manifests and record the new implementation commit when it is available.

Starting position, subject to those retained artifacts:

- `receiver_supervision_v1` and `receiver_answer_ce_v1` are implemented, including a focal-adapter trainer and frozen/task-only/receiver-SFT comparison arms.
- The parent collected 672 source generations on 96 tasks: 64 fitting and 32 diagnostic held-out groups.
- Support was insufficient: fitting hold/repair support was 2/2 distinct tasks; diagnostic held-out support was 0/1. No receiver optimizer updates or new receiver evaluation ran.
- The historical donor inventory found no same-task matches for the 96 tasks. Do not repeat that search without new material.
- Private counterfactual replay has run on eligible cases. Receiver learning, complementary specialization, full PACT, and final-test superiority have NOT been demonstrated.
- The 120-task preparation is a separate completed recipe initialized from fresh adapters, not a continuation of the earlier 12-task recipe.

Close the old studies. Do not append generations to them, reopen the answer-only diagnostic, recollect the 672 parent calls, repeat clean preparation, or run final-test data.

My workflow remains: local Codex development and CPU tests -> my review/commit/push to GitHub -> pinned checkout and actual GPU execution in Colab -> returned results bundle for local analysis. Do not commit, push, launch GPU jobs, download pretrained weights locally, access Drive credentials, or call paid inference services for me. No Slurm, PBS, multi-GPU, SSH, or Docker-daemon dependency.

## 2. Authorized methodological change and its boundaries

Add a context-source variant named `controlled_peer_donors_v1`, feeding the existing `receiver_supervision_v1` objective. Keep source variant and objective separate in schemas/configuration.

The explicit change is:

    frozen NATURAL focal private packet
    + one OFFLINE TARGET-CONDITIONED synthetic peer packet
    + the other unchanged saved peer packet
    -> full receiver context
    -> existing supervised answer-field target

This authorizes instructing the OFFLINE DONOR GENERATOR to support a selected correct or incorrect option. It supersedes the earlier prohibition on answer forcing ONLY for this new donor source. Target-conditioned donor text is deliberately synthetic; it is not a natural alternative from the focal policy.

Preserve all other scientific boundaries:

- Never overwrite, relabel, or resample the focal actor's initial answer to manufacture disagreement.
- Do not force the three deployed actors to produce different answers.
- Do not claim that synthetic donors establish natural agent complementarity.
- Do not insert these target-conditioned donors into the legacy same-actor private replay estimator or responsibility bank. That would require a separately authorized estimator change.
- Keep the original natural inference protocol, attack envelopes, synchronous information flow, frozen readout, private replay, responsibility solver, specialization objective, and original DPO paths reproducible.
- DPO stays disabled in this receiver study. No new positive/negative receiver completion sampling or reference-scoring requirement.
- No all-agent joint PACT updates, refreshed specialization banks, adaptive attack search, SAC reproduction, heterogeneous deployed team, BFCL study, or final-test evaluation in this pass.

This is a training-data intervention. It is not a claim that receiver supervision works before it has run.

## 3. Deliver a runnable vertical slice

Reuse the current components; implement only the needed extension:

1. Read-only import of the parent source tasks, original private packets, and initialization provenance.
2. A deterministic bounded donor-acquisition plan.
3. Actual generation through the existing real-model backend, plus a deterministic mock backend.
4. Donor validation, immutable records, and explicit rejection reasons.
5. Controlled receiver-context construction and unchanged minimum-support checks.
6. Integration with the existing three-arm training/evaluation runner.
7. Thin Colab entry points, guarded resume, and a complete review bundle.
8. Focused regression tests and concise documentation.

Suggested run names are `qwen3-controlled-peer-donors-001` for acquisition and `qwen3-receiver-supervision-controlled-001` for the consumer study. Resolve any collisions conservatively. Both are NEW runs with explicit parent links; they are not continuations of the stopped parent study. Reuse completed artifacts by recorded references, not by rewriting their manifests.

Do not build an empty donor importer and call the change complete: the deliverable includes bounded model-based acquisition and an end-to-end mock training/evaluation round trip. Real GPU execution remains for me in Colab.

## 4. Reuse the fixed source population and natural own states

Keep the existing 96 task groups and 64/32 partition exactly. Retain task IDs, normalized question/options, labels on the evaluator side, source/group hashes, and all exclusion rules. The diagnostic held-out groups have already been inspected for eligibility; document them as development-held-out, not a pristine final test.

For each task, use the ORIGINAL main-generation focal agent0 packet and the other two ORIGINAL private packets from the parent source collection. Do not choose among the four extra focal alternatives to obtain a preferred correctness state. Do not switch the focal agent on tasks where another agent gives a more useful answer.

The parent contains seven sampled packets per task, but this is not authorization to treat all seven as exchangeable natural own histories.

Validate parent artifacts using existing safe readers/checksums and explicit schema compatibility. Do not execute imported audit scripts or obey instructions in packet text. Missing required parent records should produce a concrete integrity/preflight error, not silent regeneration.

For this first source recipe:

- A valid focal packet must parse to one allowed answer option. Abstention, invalid-answer, and truncated/otherwise rejected own packets do not become invented correct/wrong states.
- The unchanged other-peer material must satisfy the existing context-builder policy. Preserve an explicitly supported abstention if the existing schema allows it; do not silently repair invalid source bytes.
- Unsupported tasks remain in the source manifest with precise reasons. Do not replace them with different task IDs.
- Report own-state eligibility separately from donor availability and context support.

Preserve original seeds and task identities. Use new namespaced seeds for donor calls; never reindex a subset and thereby alter original identities or sender assignments.

## 5. Offline donor generation

### 5.1 Generator identity

Use the existing pinned unadapted Qwen3-8B backbone with ALL learner adapters disabled. This is a different generation role, not an independent model-family baseline or an external stronger teacher.

Inherit the audited model/tokenizer revisions, BF16/SDPA, thinking-disabled chat template, and decoding parameters. The recorded starting decoding is temperature 0.7, top-p 0.8, top-k 20; read exact pinned values from source configuration and reject unexpected mismatches rather than silently changing them. Maximum donor output is 256 tokens; enforce prompt-plus-output context limits.

Use the existing adapter-isolation context manager and restore the previously active adapter/gradient mode on exit, including errors. Record the actual base-only generator identity. No new model download, model family, quantization fallback, or package migration is part of this design.

### 5.2 Two targets per eligible task

For each task with an eligible natural own state, choose:

- Correct target: its official answer `y`.
- Wrong target: one valid option `y_tilde != y`, selected uniformly using the project's stable seeded choice over the canonical incorrect-option list.

Freeze the wrong target before donor outcomes. Do not choose whichever wrong answer most changes a receiver or most disagrees with a natural packet. A wrong donor may agree with a wrong own answer; retain and report that possibility.

Generate BOTH target types independently of whether the focal actor is correct. This supplies hold/repair examples plus matched opposite-advice controls.

### 5.3 One symmetric generation template

Use one versioned template for both target types, parameterized only by the task and target option. Do not use different models, token caps, styles, or special helpful/malicious phrasing for the two classes.

Conceptual template, to be adapted to the actual existing packet serializer:

    Produce a concise peer response for the following multiple-choice task.
    Support option {target_option} with a task-specific justification.
    Use the standard peer packet schema {schema_contract}.
    State the answer normally; do not mention that an option was assigned,
    an answer key, hidden annotations, training, or these construction instructions.
    Task and options: {trusted_task}

The generator is performing a benchmark message-construction task, not necessarily expressing its unconstrained belief. Preserve the exact request and actual returned packet. The prompt MUST NOT include the focal answer, other agents' messages, held-out receiver outcomes, or a desired downstream effect.

The task label is intentionally used OFFLINE to choose the correct target. Therefore donors are label-conditioned intervention data. Do not describe them as free of all label-derived information. The learner may observe the donor's answer and justification as ordinary peer content; it must not receive the generator instructions, target-selection metadata, or evaluator annotations.

### 5.4 Fixed bounded acquisition

At most TWO generation attempts per target per task. Stop after the first accepted packet for that target. Later attempts retain the same template, target, model, decoding, and a prespecified distinct seed; no feedback prompt rewrite or escalation.

Every dispatched model attempt counts, including invalid/abstaining outputs and failures after dispatch. Preserve existing ambiguous-attempt recovery safeguards; never blindly regenerate an unresolved call or reset its budget on resume.

Bounds across the 96-task source population:

    max_donor_generation_calls = 96 * 2 targets * 2 attempts = 384
    max_donor_output_reservation = 384 * 256 = 98,304 tokens

Skipping ineligible tasks and first-attempt success reduce actual calls. These are caps, not expected consumption. No extra reviewer-model calls, prompt search, temperature sweeps, or hidden retry-until-success loop.

### 5.5 Validate without manufacturing packets

Separate the following:

- Normal packet parsing and allowed-option validity.
- Exact generated-answer match to the assigned target.
- Required nonempty bounded justification and existing length/context policy.
- Overt construction-metadata leakage or malformed privileged-role delimiters.
- Reasoning review status.

A target mismatch is a failed attempt; never change its answer label. Never graft a correct option onto a wrong explanation, replace its rationale, or silently rewrite the raw text. Store both raw bytes and the ordinary parsed view under the same established rules used for other packets.

For metadata-cue checks, reject explicit disclosures such as 'the assigned target is', 'the answer key says', or 'this is a repair training example'. Do not ban ordinary peer assertions such as 'option B is correct'. Keep the validator narrow, deterministic, versioned, and inspectable; structural acceptance is not proof of persuasive realism.

Call a packet `answer_correct` when its option matches the official label. Do not call its rationale verified merely because the answer matches. Wrong-target rationales are intentionally misleading examples; they are not trusted factual explanations.

Export a deterministic review sample of up to 16 accepted donors, stratified where available by task family, partition, and target type, plus rejection examples. Include exact question/options and provenance in that OFFLINE review. Do not require a new evaluator model or fabricate human-review status. This bounded engineering study may use structurally accepted, answer-checked donors with `rationale_review_status=not_reviewed`, reported explicitly. Substantive reasoning review remains necessary before broad claims about helpful evidence quality.

If a genuine systematic generation/content defect is identified, stop and record it; changing the prompt or acceptance rules creates a new version, not a silent repair of this run.

## 6. Record provenance and construct one-slot interventions

Extend the existing schemas rather than maintaining a parallel artifact framework. Each donor record must retain at least:

- Source variant and schema version; parent run/artifact references.
- Task/group/partition and exact trusted-input hash.
- Generator/base/tokenizer/template/runtime identities and adapter-disabled identity.
- Target kind, target option, wrong-target selection seed, candidate attempt/seed.
- Exact generation prompt/messages and hash, actual raw completion, parsed option.
- Target-match status, answer-correctness status, acceptance/rejection reasons.
- Input/output token counts, stop reason, output reservation, actual attempt status.
- Raw-packet/content hashes and rationale-review status.

Correctness, target kind, and stratum are analysis/training metadata, not receiver input fields.

Choose one nonfocal sender slot per task using a fixed seeded rule independent of target type, donor success, and receiver outcomes. Keep that slot identical for correct-target and wrong-target variants. Preserve peer order and original sender identities; record realized position balance rather than reassigning after outcomes.

Each receiver context contains exactly:

1. The unchanged trusted task.
2. The unchanged original focal own packet.
3. The unchanged packet from the other, nonreplaced peer.
4. One accepted synthetic donor in the selected peer slot.

Use the normal source envelope with no correctness marker or generator identity cue. Preserve the original replaced packet in the audit record. Do not edit the sender's saved private state. If this controlled delivery is ever materialized for multiple recipients, the same replacement bytes must reach all declared recipients; do not accidentally create a per-recipient attack.

Register this as a controlled training/diagnostic intervention, not a naturally occurring message or an unlabeled clean trajectory. Correct-target and wrong-target contexts receive distinct hashes. They are NOT a same-prompt DPO pair.

## 7. Training support versus diagnostic completeness

Eligibility depends on the NATURAL focal answer and the accepted donor:

| Natural focal answer | Donor | Use |
|---|---|---|
| Correct | Wrong target | Primary HOLD supervision |
| Wrong | Correct target | Primary REPAIR supervision |
| Correct | Correct target | Agreement diagnostic control |
| Wrong | Wrong target | Misleading-advice diagnostic control |

For this first experiment, train only the primary balanced hold/repair strata using the already implemented objective. Keep the opposite-advice conditions as evaluation controls.

IMPORTANT: do NOT require both donor types to succeed before allowing an otherwise valid primary supervised context. A valid wrong-target donor supports hold when the focal answer is correct even if correct-target generation failed; a valid correct-target donor supports repair when the focal answer is wrong even if wrong-target generation failed. Report missing opposite-advice controls and paired-comparison denominators separately. Do not recreate a mandatory-pair bottleneck in the new context builder.

Count distinct original task groups, not attempts, repeats, or donor variants:

- At least 8 fitting tasks per primary stratum.
- At least 4 diagnostic held-out tasks per primary stratum.
- At most 32 fitting primary contexts per stratum: 64 total.
- At most 16 diagnostic primary contexts per stratum: 32 total.

Select among eligible tasks by a frozen deterministic ordering, never by receiver success, final-team gain, likelihood, or a hand-selected convenient explanation. Keep all acquired and rejected donors in the immutable bank. Use no held-out model outcomes for selection.

These inherited minima are engineering feasibility gates, not statistical-power guarantees. Retain them. If they are not met, export `insufficient_context_support`, with no optimizer updates. Do not lower the gate, add tasks, append more attempts, switch the focal state, or claim the method failed at learning.

Report staged yields: source tasks -> valid original focal states -> donor attempts/accepted targets -> primary hold/repair tasks -> opposite-advice completeness. Give causes for every exclusion.

## 8. Reuse the existing receiver loss and comparison arms

Once the frozen donor/context manifest passes the declared support checks, feed it to the current trainer. Do not introduce a new learning algorithm.

Keep `receiver_answer_ce_v1`: score only answer-bearing output tokens under the full unchanged receiver prompt. Use a genuine prefix of the normal complete packet, e.g. the established serializer's prefix through its answer field. Do not append EOS to an incomplete prefix, fabricate a rationale target, provide a gold prefix at evaluation, or change the inference instruction to answer-only.

The donor justification is input context, not an automatically trusted full-output training target.

Keep the three arms:

1. Frozen 120-task preparation: no new updates.
2. Task-only SFT: same task labels, answer-token supervision, example multiplicities, and update schedule; no peer input.
3. Receiver SFT: full saved hold/repair contexts.

Train only prespecified focal agent0. Both trained arms start from the EXACT SAME prepared adapter bytes with fresh optimizer states; neither continues from the other. Restore actual durable weights, not review-ZIP metadata. Compact final inference exports may initialize a new training job with a fresh optimizer but cannot masquerade as optimizer-state resume.

Keep backbone, nonfocal adapters, and base readout frozen. Use the updated focal adapter for both its private and revision turns in natural-team evaluation. Keep inherited rank/module/precision settings and the existing audited training machinery.

Retain:

    L_receiver = 0.5 * task_average_hold(answer_CE)
               + 0.5 * task_average_repair(answer_CE)

and the same 0.1 clean-anchor coefficient/schedule for both trained arms. Do not add a duplicate receiver base loss or silently renormalize a missing stratum. Task-only and receiver arms must have identical target exposure, task multiplicities, clean anchors, and optimizer-step caps; report different input/context costs honestly.

Starting schedule remains learning rate 1e-5, microbatch 1, effective batch 4, at most two data passes or 32 optimizer updates per trained arm, whichever limit is reached first. Freeze the actual schedule before held-out model evaluation. No search across checkpoints against this reused diagnostic slice.

## 9. Evaluate content sensitivity and natural behavior separately

All three arms use matched tasks, context hashes, seeds, packet order, decoding, and checkpoint-specific cache keys. Generate complete normal packets; do not supply teacher-forced answer prefixes during generation.

### 9.1 Fixed-history controlled receiver diagnostic

For each selected diagnostic task, evaluate the available versions:

- Correct-target donor.
- Wrong-target donor.
- Peer-withheld control: same trusted task and original own packet, with BOTH peers' information removed/neutralized using the same explicit policy for every arm.

The peer-withheld prompt changes context/length. Label it as an intervention, not an exactly identical prompt or perfect isolation of one linguistic factor. Missing donor versions remain missing, not synthetic failures/successes. Compute correct-versus-wrong donor comparisons only on tasks with both versions; report that support separately from primary hold/repair support.

Report primary hold retention/harmful revision and repair success, agreement behavior, misleading-advice outcomes, peer-withheld correctness, abstention/wrong-option/format failures, and paired transitions. Report answer-only correctness as a proxy, not certified reasoning or proof the receiver causally used a specific justification.

The teacher-forced answer CE is a separate diagnostic from free-generation success. DPO remains disabled; no reference-model pairing gate returns.

This evaluation uses label-conditioned synthetic donor content. Call it a CONTROLLED receiver diagnostic, not natural robustness, an adversarial worst-case certificate, or an untouched final benchmark. Its own states came from the old initialization snapshot, not natural rollouts of the newly trained actors.

### 9.2 Natural private and team diagnostics

Evaluate the focal private answer on all 32 diagnostic tasks for each arm.

Also evaluate a prespecified slice of at most eight tasks from that same 32-task partition, chosen by a seeded outcome-independent rule, with three-agent natural private generation under clean/exchange conditions. Use the existing bounded fixed attack procedure for exchange. Freeze the attack assignment/reference-generation policy before comparing arms, retaining the existing common-pool semantics and provenance.

Do not insert correct synthetic donors, force disagreement, condition own answers on labels, or select only tasks with accepted donors. The new focal checkpoint serves both focal turns; the other actors and base synthesizer stay fixed. Other-agent generations may be reused only when complete requests/checkpoints/seeds match.

Report original terminal success, individual correctness, initial coverage, answer erasure, and readout failure with denominators. Eight tasks are a smoke diagnostic, not a statistical efficacy claim.

A receiver-SFT gain over the frozen actor alone is insufficient: compare against task-only SFT and peer-withheld behavior. If both trained arms gain equally or the gain survives unchanged without peer information, do not attribute it automatically to communication learning.

## 10. Freeze an explicit total budget

The following conservative ceilings describe this authorized bounded recipe. The plan command must reconstruct exact stage counts from the resolved configuration before any GPU call, rather than accepting totals typed into a report.

| Stage | Maximum generation calls | Output-token reservation |
|---|---:|---:|
| Donors: 96 tasks x 2 targets x 2 attempts | 384 | 98,304 |
| Controlled receivers: <=32 tasks x 3 versions x 3 arms | 288 | 73,728 |
| Natural private probe: 32 tasks x 3 arms | 96 | 24,576 |
| Natural team: 8 tasks x 2 conditions x 3 arms x 7 calls | 336 | 76,800 |
| TOTAL | 1,104 | 273,408 |

A natural team trajectory has three private, three revision, and one readout call, with output caps 256/256/64, hence at most 1,600 generated tokens. Controlled receivers/private probes use 256-token caps.

These ceilings count worst-case donor attempts and do not assume cache savings. Actual missing controls, early accepted donors, smaller supported cohorts, and legitimate reuse can reduce counts. Training forwards/updates, clean-anchor presentations, teacher-forced diagnostics, input tokens, and persistence overhead are separate; the planner must derive and log their schedules/bounds too. Maximum optimizer updates across both trained arms is 64, not 64 per arm.

No extra GPU model smoke calls outside this plan: use the first scheduled calls as the real-model smoke path, or make any required extra preflight calls explicit within the fixed caps. CPU mocks are separate.

Do not reuse the stopped parent's full-study budget as permission for additional work. Parent calls are imported historical artifacts, not newly executed calls. If the existing orchestration would exceed these ceilings, fail the dry-run with the exact discrepancy. Do not silently discard evaluation arms, reduce token caps, or expand the budget.

On insufficient support, only acquisition/context artifacts are completed; downstream stages are `not_executed`. If the normal trainer reaches a different legitimate failure, retain it separately from data-support failure.

## 11. Local implementation, persistence, and Colab interface

Adapt the existing package/CLI/notebooks; suggested capabilities, not fictional existing commands:

- plan/preflight parent import and bounded donor study;
- acquire donors;
- build/freeze controlled contexts and check support;
- train the two declared arms;
- evaluate frozen/trained arms;
- report/export.

Give me exact runnable commands/cells using the ACTUAL implemented CLI at handoff. Notebook parameters must include explicit Git ref, new run IDs, parent source archive/root, prepared full-weight or compact-initialization snapshot, scratch/persistent roots, config, and stage/resume choices. Do not embed private tokens or paths guessed from this conversation.

Default notebook execution must not start unbounded training or rerun the parent collection. Acquisition and training/evaluation are explicit bounded stages; the latter refuse to run without a compatible passed support manifest. No additional implementation should be needed merely to invoke the planned learning stage once its data gate passes.

Reuse scratch-first writes, immutable shards, local ZIP before Drive copy, verified completion receipts, full optimizer-boundary training snapshots, and guarded recovery. Keep compact initialization exports distinct from full resume snapshots. No new persistent-storage redesign unless this extension exposes a concrete defect.

Cache keys and stable IDs include source variant, target option, generator template/model/adapter state, context bytes, actor snapshot, seed, decoding, parser/validator versions, and appropriate runtime fingerprint. A changed generator template or receiver checkpoint must invalidate relevant cache entries. Preserve original attempts, committed calls, and budgets on resume. Do not re-audit every closed run to proceed with this update.

If local real artifacts are missing, use fixture-backed tests and identify the required Colab input path. Do not substitute synthetic data for a real parent run or let local absence of GPU weights prevent implementing the runnable pipeline.

## 12. Reporting and acceptance tests

Export enough raw evidence for offline reconstruction without model weights:

- frozen plan, parent references, source/context manifests, exact donor requests and responses;
- attempt journal, target selection, validation results, rejection/unsupported reasons;
- accepted controlled contexts, donor review sample, and leakage/isolation checks;
- per-partition/family/stratum support with distinct-task denominators;
- training arm initial/final checkpoint identities, target masks, loss roles and schedules;
- per-task receiver/private/team outputs, explicit paired joins and missing-control counts;
- resource usage with actual versus reserved tokens/calls and unknown compute units as null;
- hashes/receipts, errors, omitted-tensor locations, and CODEX_HANDOFF.md.

Track readiness independently: acquisition complete; structural donor validity; rationale-review status; context support; supervised training executed; evaluation complete; optional DPO disabled; specialization integration deferred; full PACT efficacy unestablished. Never label the study ready merely because software tests pass.

Add focused tests using fixtures and tiny locally initialized models, without pretrained downloads:

1. Parent own packet is byte-identical in every intervention; alternatives cannot silently replace it.
2. Wrong-target selection excludes the gold option, is deterministic, and does not depend on focal outcomes or task reindexing.
3. Correct/wrong targets use the same generator template and base-only policy; adapter mode restores on success and exception.
4. At most two attempts per target, first accepted wins, all failures count, resume does not reset budgets or repeat committed calls.
5. Invalid/abstaining/target-mismatched donors are retained as rejected and never relabeled.
6. Generator target metadata is allowed only in its acquisition request/audit record; receiver inputs contain only normal task/own/peer content. Ordinary answer text is not falsely treated as metadata leakage.
7. Only the designated peer slot changes; both target variants use the same slot and unchanged other peer. Controlled contexts cannot masquerade as natural trajectories or same-prompt DPO pairs.
8. Valid hold/repair can proceed without the opposite donor; primary support and paired-control completeness have different counts.
9. Split/group boundaries, distinct-task minima, fixed task ordering, no replacement on failure, exact acquisition/evaluation budget derivation.
10. Existing answer-prefix/masking loss works with synthetic-context provenance and zero DPO pairs; no EOS supervision, duplicated base loss, or fake rationale target.
11. Both trained arms initialize from identical bytes with fresh isolated optimizers; backbone/nonfocal parameters unchanged; optional tiny-neural answer loss can improve without implying real 8B efficacy.
12. Controlled evaluation keeps saved histories fixed; natural evaluation generates fresh own states and cannot load label-conditioned donors. Seed/checkpoint/context mismatches fail explicit comparisons.
13. Mock end-to-end acquisition -> support -> both training arms -> evaluation -> interrupted resume -> export/import. Include insufficient-support and missing-opposite-control branches.
14. Legacy replay, original source recipe, disabled-DPO behavior, and reporting regression tests remain intact.

Report actual passes/skips/failures; do not reuse historical test totals as this patch's test results. GPU-unverified behavior must be labeled as such.

## 13. Documentation and final handoff

Update methodology/implementation decisions to state exactly why target-conditioned peer generation is now authorized, which old restriction is superseded, and which natural-state/evaluation protections remain. Preserve old reports and configs unchanged. Source changes do not retroactively turn synthetic donors into natural evidence or old supervised preparations into PACT runs.

Update AGENTS.md briefly, implementation status, experiment ledger, and Colab runbook. Keep paper result placeholders unfilled.

Finish with:

1. A concise implemented delta and changed-file list.
2. Exact example of both generator requests and resulting receiver contexts, clearly marked as a fixture unless real source data are shown; demonstrate that the own packet is unchanged.
3. Actual tests run and deferred/GPU-unverified items.
4. Exact plan/acquisition/training/evaluation/export commands and required artifact paths.
5. The resolved worst-case budgets and support-stop behavior.
6. The bundle I should return after Colab, including a useful report when support fails.

Implement the path, not only another design/audit. Do not run GPU work, commit, push, relax the support gates, or fabricate positive results. I will review the code, publish it, and execute the pinned bounded study in Colab.
