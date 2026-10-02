# PACT: heterogeneous natural-complementarity phase

Prepared: 2 October 2026
Proposed study ID: `pact-heterogeneous-complementarity-001`
Variant: `heterogeneous_natural_support_v1`
Status: implementation specification and bounded study design, NOT executed evidence.

## 1. Mission, workflow, and scope

Update the EXISTING PACT repository. Implement a complete local-testable, Colab-runnable inference study of naturally occurring complementarity in a cross-family LLM team. Do not start a new repository, replace the framework, or stop after another design/audit document.

The scientific questions are:

1. Does a Qwen/Llama/Mistral team cover correct answers that its best individual member misses?
2. Does it outperform three independent samples from each constituent model, rather than merely a weak homogeneous reference?
3. Does one synchronous communication exchange preserve, repair, or erase useful answers, compared with independent voting and synthesis of exactly the same private packets?

This is a NEW CLEAN, INFERENCE-ONLY diagnostic. It is not training, PACT efficacy, a size-ladder experiment, adaptive robustness, or an exact reproduction of a published study. Natural heterogeneity is an alternative source of useful differences; it does not establish that PACT learned them.

My workflow remains: local Codex development/CPU tests -> my review and GitHub commit/push -> pinned checkout and real model execution in Google Colab -> returned reports for local analysis.

Do not launch local GPU work, download pretrained weights locally, commit, push, change remotes, access credentials, or disturb unrelated edits. No Slurm/PBS, SSH cluster, Docker-daemon, multi-GPU, hosted inference API, or paid model-service requirement. Do not broadly upgrade the working dependency stack without a demonstrated compatibility reason.

Implement actual model loading, generation, scheduling, team construction, evaluation, reporting, persistence, and a thin notebook. Missing credentials/weights may block a real run but must not block fixture-based implementation and tests.

## 2. Read first; preserve current evidence

Inspect Git status, applicable AGENTS.md files, package/CLI/test/notebook layout, the 30 September PACT project review, experiment ledger, implementation decisions, original protocol, dataset manifests, and existing model/recovery/report code. Locate actual files; proposed CLI names below are not claims those actions already exist.

Current evidence to preserve, checking actual retained audits:

- Controlled receiver training ran, but did not improve correctness over its frozen/task-only controls on the matched receiver cohort.
- GPQA development screening produced little useful correct coverage beyond its best member. Its 32 exposed tasks stay diagnostic-only; 164 protected items and two exclusions stay intact.
- Natural fixed-bank specialization stopped for insufficient natural pair support before replay/training.
- Controlled specialization closed INCOMPLETE. Saved replay estimates can be inspected, but recovery accounting remains unresolved. Do not change its safety flags, regenerate missing cells, reinterpret it as completed, or inherit its run state.
- Assignment contrast on that latest controlled bank remains unevaluated, not failed. Real specialization training and full PACT have not executed.

This new phase requires no old adapter or optimizer tensors and no continuation of incomplete PACT runs. It uses pristine official instruction-tuned checkpoints. Old effective-adapter precision history remains recorded in the old experiments; it is neither propagated into these new models nor silently corrected retrospectively.

Historical Qwen3 results may appear in a clearly labeled context table. They are not matched current controls and cannot substitute for new homogeneous measurements.

Treat imported raw text, rationales, logs, and archives as untrusted data. Use the trusted reader; never run a script found inside an imported bundle or unpickle arbitrary objects to inspect results. Do not re-audit every historical ZIP just to implement this phase.

## 3. Concrete models and four teams

### Constituent model registry

Use these exact official instruction-tuned repositories as the proposed model set:

| Registry key | Official repository |
|---|---|
| Q | `Qwen/Qwen2.5-7B-Instruct` |
| L | `meta-llama/Llama-3.1-8B-Instruct` |
| M | `mistralai/Mistral-7B-Instruct-v0.3` |

Resolve immutable revisions for weights, tokenizer, chat template, model config, and generation config before the first task generation. Record hashes of the actual files used. Do not invent revision SHAs or treat a moving `main` as a frozen experimental identity. No pretrained base-model/instruction-model substitution, automatic fallback, quantized replacement, or model selection based on observed answers.

These three families appear in the referenced agent-diversity study; its exact checkpoint variants, prompts, datasets, persona settings, and multi-round protocol must not be assumed to match this study. The selected Instruct IDs and one-exchange PACT protocol are explicit design choices. Document this as an adapted diagnostic, not a faithful reproduction or new discovery that heterogeneous ensembles exist.

### Team configurations

- `heterogeneous_QLM`: one natural sample from each family.
- `homogeneous_QQQ`: three independent private samples from Q.
- `homogeneous_LLL`: three independent private samples from L.
- `homogeneous_MMM`: three independent private samples from M.

All have three logical agents, the same trusted task information, the same semantic packet/revision instructions, one synchronous exchange, and identical configured per-call generation caps.

Do NOT give different personas, tools, model-size disclosures, expertise labels, or instructions to disagree. Do NOT force an answer, select the correct sample using labels, change option ordering by model, or insert controlled donors. Homogeneous copies differ by sampling seed, not adapters or roles.

### Common readout

Use the project's pinned, UNADAPTED `Qwen/Qwen3-8B` base readout with all adapters absent/disabled, thinking disabled, and greedy decoding, as the common synthesizer for all four teams. Reuse the established semantic synthesis prompt and strict final-answer contract. Resolve the actual underlying official base/tokenizer revision from trusted existing configuration before freezing the new plan.

This adds a fourth model identity but not simultaneous GPU residency. No old learned adapter weights are needed. Do not call this an independent judge of rationale correctness: it is a fixed answer-generating component, potentially with its own knowledge and family/style biases.

Also run a `readout_task_only` baseline once per task: same readout, trusted question/options, same final-answer output contract/cap, but no private or revised packets. It is an inference baseline, not a gold-assisted scorer. Its result helps identify gains that the readout could supply without a team. It is not a matched-total-token single-agent reasoning baseline.

## 4. Dataset: reuse the existing diagnostic population, not protected tests

Use the full original 80-item validation-pilot manifest: 40 ARC-Challenge and 40 original English LogiQA tasks from `qwen3-pilot-001`. This intentionally reuses development-exposed tasks; it does not create an untouched test or any training set.

- Recover exact task/group IDs, authoritative source revisions, canonical question/options, option mappings, and hashes from the retained manifest and authorized data artifacts.
- Use ALL 80 tasks, not a subset chosen for previous mixed outputs, successful donors, or interesting credits.
- Preserve original trusted inputs/option ordering after verifying them. Each model/team sees the same canonical options per task. No model-specific shuffling to create disagreement.
- Keep labels strictly outside defender/readout prompt objects. Separate task input and evaluation metadata in typed APIs.
- No GPQA source access, exposed or protected; no new benchmark, full test, or previously untouched specialization-development cohort is needed.
- Preserve training/validation/exposure provenance. Existing pretraining exposure is unknown; do not claim contamination-free generalization.
- If exact inputs cannot be recovered, report the actual missing prerequisites. Do not silently choose another 80 items or depend on an invented sandbox path.

The cohort is fixed by prior membership, not new outcomes. Derive only the new seed/order schedule from a frozen seed (proposed `20261002`) before new model generation. Record that this is a design constant, not evidence.

## 5. Private sample bank and controlled sharing across team configurations

For each task x, generate three private draws per family:

    P[x,Q,0], P[x,Q,1], P[x,Q,2]
    P[x,L,0], P[x,L,1], P[x,L,2]
    P[x,M,0], P[x,M,1], P[x,M,2]

This is nine NEW private calls per task, 720 across the study. All draws use the same task and common semantic private prompt; no peer information, team composition, family name, or desired answer is supplied. Distinct sampling seeds are keyed by stable task ID, family checkpoint identity, stage, and replica index. Do not claim statistical independence across task outcomes merely because seeds differ.

Freeze a balanced family-to-display-slot permutation for the heterogeneous team BEFORE generation. Within each dataset's 40 tasks, cycle a seed-shuffled list of the six permutations over a seed-shuffled task-ID order, with count imbalance at most one. This changes only which anonymous slot presents each family; it does not change task content or select outputs. Store the mapping in the plan.

Use the following deterministic coupling:

- Homogeneous family F occupies slots 0/1/2 with `P[x,F,0/1/2]` respectively.
- If family F occupies slot j in the heterogeneous permutation, the heterogeneous team uses `P[x,F,j]` in that slot.

Thus the mixed team's three packets are exact members of the nine-packet bank and share source records with the appropriate homogeneous arms. Never generate a separate favored heterogeneous response, choose among 27 combinations by correctness, or reuse a different prompt as an identical request.

All private prompts must be independent of recipient team configuration for this sharing to be valid. If legacy prompts contain actor/slot wording, explicitly create a common identity-neutral private-prompt version for ALL four arms, preserving task and packet instructions. Do not change one arm only. Native chat templates will differ by model; semantic prompt text need not be identical token sequences.

Record source packet references plus display bindings, rather than mutating source packet identities when forming teams. The same source packet can appear in different team views. No duplicate generation call should be counted for a reference reuse.

### Individual baselines without extra calls

- Report each family's designated single answer per task: the exact selected packet used in `heterogeneous_QLM`.
- Separately report per-replica accuracy and the pooled three-draw family accuracy with task clustering.
- Do not choose the best replica after observing results and label it a preselected single-model baseline.
- The homogeneous three-sample teams are the direct same-call-count comparison for the heterogeneous three-sample team.

## 6. Clean communication and aggregation on all four teams

In the normal model-major run, complete and durably save the private bank before revisions, then construct immutable three-packet views for every team. The explicitly authorized two-task smoke may complete these two tasks end-to-end early; it must first finish all nine private packets for each smoke task. No receiver ever runs with an incomplete private snapshot for its task.

For every task/team:

1. Compute independent voting from its three PRIVATE answers, using the prespecified existing tie/invalid policy. No model call and no gold tie breaking.
2. Run the common frozen synthesizer on the task and PRIVATE packets: independent synthesis.
3. Each agent revises once using its own saved private packet and the two other INITIAL packets, with that slot's designated family model.
4. Run the SAME frozen synthesizer on the task and REVISED packets: debate synthesis.
5. Optionally compute voting over revised packets without another model call, labeling it separately.

Never supply another agent's revision to a receiver. Do not feed the private synthesis result into debate. Both readouts must use the same semantic template, source envelopes, greedy decoding, model, and cap; only private-versus-revised content differs.

All team configurations and all 80 tasks proceed through communication, regardless of measured private diversity. There is NO positive-support/efficacy gate in this inference study. Sparse or zero support is a valid completed result, not a reason to keep sampling or to skip communication. All-wrong teams may construct answers; do not discard them.

Display only anonymous agent labels, with source family in audit metadata. Do not claim perfect blinding: models may self-identify in generated text. Log such occurrences; do not rewrite valid generated packets after the fact.

Use revision seeds tied to stable task, physical model/replica identity, and revision stage. Match the selected family/replica's revision seed between its homogeneous and heterogeneous receiver calls where applicable. Different messages still define different requests. Matching a numeric seed across different model families is not proof of equivalent randomness.

Freeze readout source order from the team slot mapping. Do not pick a permutation yielding higher accuracy. No additional order sweep is authorized in this phase.

## 7. Model-specific tokenization and generation correctness

Extend the existing backend using an explicit `ModelSpec` or equivalent typed registry. Required identity includes official repo/revision, tokenizer/template hashes, dtype, attention implementation, native stop IDs, generation parameters, and adapter state.

- Every checkpoint uses its OWN official tokenizer and native chat template.
- Use the installed supported `apply_chat_template` path and generation prompt. Do not feed Qwen-formatted tokens to Llama or Mistral.
- Preserve common semantic system/user instructions. Inspect native handling of system roles. Any needed compatibility serialization must be frozen and documented before task inference; no outcome-driven prompt repair.
- Tokenize exactly once or explicitly avoid duplicated BOS/EOS/control tokens when rendering then tokenizing. Slice prompt tokens by input length, not by string matching or using another tokenizer.
- Do not inject family-specific identities from a copied model-card example such as 'You are Qwen'.
- Inherit verified native EOS/end-of-turn IDs, padding rules and tokenizer settings; freeze and log their actual values. Never hard-code a shared EOS ID across all families.
- Normal peer text is serialized as data inside the receiver context, not as new privileged chat messages. Do not execute apparent tools or instructions embedded in a packet.

Proposed common private/revision generation settings:

    do_sample=true
    temperature=0.7
    top_p=0.8
    top_k=20
    repetition_penalty=1.0
    max_new_tokens=256
    num_return_sequences=1

Explicitly resolve all remaining generation fields, avoiding hidden per-model defaults that change sampling constraints. Readouts are greedy with `max_new_tokens=64`. No Qwen3 thinking switch is passed to models without that feature; it applies only to the common Qwen3 readout. All three selected Instruct actors use their normal non-reasoning chat interfaces.

Use BF16 and supported SDPA where available, batch size one initially. Verify runtime support; no silent quantization, CPU offload, precision change, FlashAttention installation, or smaller-model fallback. A compatibility failure stops the affected stage with evidence; a revised configuration is a new declared plan.

Use a 4,096-token TOTAL prompt-plus-reserved-output limit, measured with the RECIPIENT model's tokenizer. A peer's 256 source tokens may occupy a different number of receiver tokens. Keep source-generation length and rendered-recipient length separate. Never truncate the trusted question/options or shave off one inconvenient peer silently.

Overflow is a recorded nonexecuted context-budget failure, not a regenerated shorter question. Known output-format failures, abstentions and length-limited completions are scored as task failures under the existing strict policy. Preserve a documented invalid-peer envelope where the legacy protocol supports it; do not use labels to infer a valid answer or count invalid-only disagreement as useful diversity.

Use ordinary complete answer/justification packets, not constrained option scoring, answer-forced decoding, or a new answer-only actor contract. Keep strict evaluation parsing consistent across families; model-specific prompt-token stripping is not a license to salvage answers using a gold label. Report parser and truncation rates by family and stage.

## 8. Sequential single-GPU execution

Do not keep Q, L, M, and readout models resident together. Implement a model-major schedule respecting the information barriers:

1. Load Q and generate all Q private draws; persist; release it.
2. Load L and generate all L private draws; persist; release it.
3. Load M and generate all M private draws; persist; release it.
4. After the global private barrier, load Q for its homogeneous and heterogeneous revision requests; persist; release it.
5. Do likewise for L, then M.
6. Load the frozen Qwen3 readout for all private synthesis, revised synthesis, and task-only readout requests; persist; release it.

Log every load/unload, memory peak and stage duration. Use existing worker isolation, or release all model/cache references before loading the next model. Do not require all models in CPU RAM simultaneously either. Local disk caches may retain weights; preflight enough disk and host RAM as well as VRAM. Same-model grouping changes execution order, not the logical synchronous protocol.

The new models require their own official downloads in Colab. Gated access, notably Llama, must be confirmed for ALL required models before the first benchmark call. The user supplies any authorized access via a secret or existing login. Do not accept license terms for the user, log tokens, embed credentials in URLs, use an unreviewed mirror, or silently run a two-family replacement if access fails.

Local development tests must not download pretrained weights. Colab preflight may fetch tokenizer/config metadata and verify authorized repository access before large downloads. Record unresolved network/download prerequisites honestly.

A larger Colab GPU is welcome but not assumed. Sequential 7B/8B inference is the design target; actual fit/throughput on L4/H100/Blackwell is not established by this specification. Do not estimate a guaranteed number of subscription units from nominal VRAM.

## 9. Exact bounded plan and actual versus logical cost

For N=80 tasks and four teams:

| Stage | New generation requests | Output-token reservation |
|---|---:|---:|
| Private bank: N * 3 families * 3 replicas | 720 | 184,320 |
| Revisions: N * 4 teams * 3 slots | 960 | 245,760 |
| Private synthesis: N * 4 teams | 320 | 20,480 |
| Revised synthesis: N * 4 teams | 320 | 20,480 |
| Readout task-only: N | 80 | 5,120 |
| TOTAL | 2,400 | 476,160 |

Per task: 9 private + 12 revision + 8 synthesis + 1 readout-only = 30 calls; 21*256 + 9*64 = 5,952 reserved output tokens.

These are hard REQUEST/ATTEMPT ceilings, not expected tokens, durations, billing, or independent-task counts. Zero optimizer updates, teacher-forced scoring, donor calls, replay branches, attacks or extra sampling sweeps. Do not add optional study arms without a separately frozen budget.

Every dispatch, including failed attempts, counts. No unplanned stochastic retry. Committed exact requests may be reused; ambiguous attempts remain explicit and cannot be regenerated under the same completed identity. Budget exhaustion or missing evidence leaves a partial study. No automatic cap extension.

Voting and arithmetic summaries add no generation. Shared private packets are charged ONCE in actual collection totals; each logical team has its own deployment cost of 3 private + 3 revision + one final readout for debate, or 3 private + one synthesis for independent synthesis. The extra independent synthesis used alongside debate in this experiment is a comparison cost, not mandatory deployment overhead.

Team comparisons match logical counts and configured caps. They do NOT exactly match FLOPs, elapsed time, input tokens, or semantic text length across tokenizers. Measure these differences. Charge model loading/download separately from generation where timers permit; unknown compute units remain null.

Use the first TWO planned tasks as a real smoke, with their exact frozen identities, when I explicitly select that stage. The smoke comprises at most 60 calls and is part of the 2,400, not additional data. Later stages reuse committed smoke outputs. All private dependencies for these tasks must exist before their revisions. No post-smoke prompt tuning and still labeling the changed calls as one configuration. Default notebook action is plan/preflight, not a benchmark sweep.

## 10. Metrics: distinguish hierarchy, complementarity, and useful communication

Use the existing strict scorer. For team t, task x, slot i:

    C[x,t,i,s] = 1 if the stage-s packet is accepted and answer-correct else 0
    N_s[x,t] = sum_i C[x,t,i,s]
    O_s[x,t] = 1[N_s[x,t] > 0]
    Y[x,t,protocol] = final answer correctness

Invalid/abstaining/length-limited packets count as failures under the declared performance policy, while infrastructure-missing calls retain separate status. Report full intended-cohort coverage and missingness; do not silently shrink the denominator to favorable completed cases. Complete-valid-team sensitivity is secondary and includes its cohort size.

### 10.1 Natural private support

For EVERY team, separately by dataset and overall:

- N0 counts for 0/1/2/3 correct members.
- Individual, mean and best observed private accuracy.
- Initial coverage c=P(O0=1), joint initial failure=1-c.
- Useful mixed support: at least one valid correct AND one valid wrong answer in the SAME team; abstention-only contrast does not qualify.
- Exact option disagreement, all-wrong answer diversity, and invalid/abstention counts separately.
- Each member's unique correct coverage U_i=P(C_i=1 and all other C_j=0), plus a valid-peer sensitivity so parser failures are visible.
- Pairwise rescue counts P(C_i=1,C_j=0) with numerators/denominators and conditional variants where appropriate.
- G=c-max_i accuracy_i on the SAME designated member draws/cohort. G is oracle availability, not a deployable selector or a promise the readout can choose correctly.

For the heterogeneous team, aggregate members by underlying FAMILY, not anonymous display slot. Slot0 is not one fixed model across tasks. Report display-slot summaries separately for bias diagnostics.

Do not require every U_i to be positive to declare any complementarity: two weaker members can overlap in rescuing tasks that the strongest misses, yielding G>0 even if neither is uniquely correct alone. Report the joint pattern rather than imposing an incorrect equivalence between unique and additional coverage.

A larger G versus a weak single member is not enough. Compare mixed-team coverage and final outcomes with EACH homogeneous team, including the strongest observed homogeneous result. Do not only compare with their mean. Label any strongest-on-this-cohort selection as descriptive; it is not a preselected deployable model/router.

Report all nine draw-level private scores as auxiliary sampling evidence, but never select a best-of-nine oracle team or present its coverage as three-call performance.

### 10.2 Communication and readout

- Full N0 -> N1 transition tables, all tasks including initially all-wrong teams.
- Utilization u=P(Y=1 | O0=1), construction k=P(Y=1 | O0=0).
- Erasure d=P(O1=0 | O0=1), new availability r=P(O1=1 | O0=0).
- Revised-readout loss P(Y=0,O1=1), independently synthesized private-readout loss, and final success despite no answer-correct input packets.
- Hold opportunities: initially valid-correct receiver with a valid-wrong initial peer. Repair opportunities: initially valid-wrong receiver with an answer-correct initial peer. These are honest peer error contexts, not malicious attacks or certified helpful rationales.
- Retention and repair by receiver family, dataset, initial correct-member count, and unique original task count. Never treat two wrong receivers on one task as two independent tasks.
- Natural vote, independent synthesis, revised vote, debate synthesis, and readout-task-only outcomes with explicit paired gains/losses.

Check the exact identities P(Y=1)=c*u+(1-c)*k and P(O1=0)=(1-c)*(1-r)+c*d where defined. Undefined conditionals are null with support counts, not made-up zeros. A lost correct packet need not create terminal loss versus independent synthesis if synthesis already failed; distinguish both findings.

Readout improvement over the strongest member alone does not prove complementary private answers: synthesis can construct an answer absent from every private packet. Conversely, G>0 without terminal gains establishes available but unused extra coverage, not useful deployed robustness.

### 10.3 Inference and statistical boundaries

There are 80 task groups, not 2,400 independent observations. Use paired task-clustered bootstrap for team/protocol differences, stratified by dataset, keeping all models, replicas, team outputs and derived estimates for a task together. Recompute derived maxima inside each bootstrap draw and label selection bias appropriately. One seed schedule is diagnostic, not cross-seed stability evidence.

For all-zero/all-one events report an interval/method with boundary uncertainty or mark estimation inconclusive; a degenerate empirical [0,0] interval is not proof of equivalence. Do not apply an independent-identical-error formula to pooled average accuracy as a model of expected disagreement.

No hard success threshold authorizes training or selects a winning model. The study completes all planned valid inference paths and reports exact patterns. More mixed states alone do not establish PACT's gap, and a negative result does not permit seed/dataset/model fishing.

## 11. Interpretation and non-goals

Required final comparison table: each of QQQ/LLL/MMM/QLM with mean/best member accuracy, c, G, valid mixed count, unique/rescue coverage, vote accuracy, independent synthesis, debate accuracy, erasure, repair support/success and actual token/call cost. Readout-task-only is a separate baseline row.

Interpretation examples:

- QLM disagrees but G=0: the realized mixed team adds no correct availability beyond its best member; this is compatible with a capability hierarchy.
- QLM has G>0 but trails the strongest homogeneous team: natural complementarity exists in this sample but model mixing is not yet the best same-count choice.
- QLM has G>0, and debate loses useful answers or trails independent synthesis: a clean communication-preservation problem, not adversarial causation.
- QLM has coverage and terminal gains beyond strong controls: useful heterogeneous collaboration in this tested setting, not learned PACT complementarity.
- Synthesis gains with O0=0 or readout-only matches the result: generation by the readout may explain benefits; do not attribute them all to peer complementarity.
- Formatting/context failures dominate for one family: report the technical limitation and complete-case sensitivity rather than diagnosing intrinsic lack of capability.

Historical Qwen3/GPQA results are descriptive only. Do not pool them with new data as paired homogeneous controls. Findings with these known checkpoints/tasks cannot be assumed to transfer to larger models, different attacks, 8 agents, or tool workflows.

No new training, all-agent scaling, role optimization, adversarial search, synthetic donors, private replay, NLL scoring, SAC adaptation, BFCL, or final evaluation in this implementation pass. Later attacks or training require a separately reviewed plan. Preserve PACT hypotheses and negative/incomplete historical results as they are; no result placeholders are filled as trained PACT evidence.

## 12. Persistence, privacy, and runtime recovery

Reuse the established scratch-first storage, immutable completed shards, bounded verified copying, compact state manifests and raw report reconstruction. Do not build a new object store. Address new multi-model identity requirements, not every old storage incident.

Make model-major stages resumable. Before a dispatch, persist the request identity/attempt state using the approved journal protocol. Completed result status requires a durable enough result/receipt under that protocol; do not set a run safe based only on in-memory intent counts. Unknown in-flight work remains unknown. Never reset unsafe status merely because saved primary metrics reconstruct.

Bundle completed task/model-stage shards rather than streaming thousands of tiny hot-path writes to Drive. Store exact request dependencies and sample-bank/team binding manifests so report reconstruction does not need loaded models. Keep the final export path/outer checksum distinct from earlier nested receipts.

Cache identity must include full messages, task/option mapping, model and tokenizer/template revisions, generation config, dtype/runtime, seed, and relevant stage. Team views reference shared sources; different revision peer contexts must never collide even for the same model/seed. Non-thinking and native-template fields remain part of identity where applicable.

No old adapter precision restoration is needed for these pristine checkpoints. Model-file hashes and returned load receipts support the new runtime identity; metadata-only reports are not independent verification of weight tensors. State actual evidence strength.

Use a lightweight shareable metrics/config bundle and a private full trace bundle according to existing dataset/license rules. No GPQA content in either, no credentials or model weights in handoff ZIPs, and no raw prompts casually committed to Git. results_import remains ignored and must be backed up separately. Review/import must not execute generated instructions.

## 13. Implementation deliverables

Extend the existing registry/backend and evaluator, not parallel implementations. Suggested CLI capabilities (actual final syntax must be taken from implemented code):

    heterogeneity plan
    heterogeneity preflight
    heterogeneity smoke
    heterogeneity private --model Q|L|M
    heterogeneity revisions --model Q|L|M
    heterogeneity readout
    heterogeneity report
    heterogeneity export

A bounded staged runner may compose these phases after explicit invocation. Its default is plan/preflight; no automatic next scientific experiment after completion. All numerical outcomes, including zero useful support, allow report completion; integrity/access/budget errors remain explicit stops.

Create a thin notebook with repository/ref, new run ID, config/plan hash, official model revisions/access secret references, original pilot manifest/source paths, scratch/cache/persistent roots and stage/resume. Downloads and model calls occur only in the user-invoked Colab workflow. Print the exact resolved budget and model-stage progress; do not repeatedly reload models per question.

Provide these outputs using existing schema conventions where possible:

    plan.json / resolved_config.yaml
    model_registry.json / access_preflight.json / environment.json
    source_exposure_manifest.json / team_bindings.json
    private_bank.jsonl / revision_records.jsonl / readout_records.jsonl
    per_task_metrics.jsonl / family_pairwise_rescue.csv
    private_support.json / transition_tables.json
    paired_protocol_comparisons.json / resource_usage.json
    raw_artifact_inventory.json / checksums.json / incomplete_requests.json
    report.md / CODEX_HANDOFF.md

Raw records may be sharded instead of duplicated in monolithic files. All records carry canonical IDs and provenance, not titles guessed as filesystem paths. The handoff must clearly distinguish new findings, historical context, proposal decisions and unavailable evidence.

## 14. Focused tests and acceptance criteria

Use invented fixtures for default tests, no network/CUDA/downloads. Optional neural tests use tiny locally initialized architectures only and are explicitly marked; they do not establish real 7B/8B quality.

Required tests:

1. Official model identities/revisions, tokenizer association, empty/disabled adapters, and gated access errors.
2. Native chat-template generation, no duplicated special tokens, correct output slicing, family-specific EOS, and semantic input equivalence.
3. No answer label or model-family/capability hint in defender prompts; task serialization cannot turn peer strings into privileged roles.
4. Original 80-task mapping/exposure preservation; no GPQA/final-test selection or outcome-based item replacement.
5. Nine private requests per task with distinct replica identities; exact QLM/QQQ/LLL/MMM bindings; no best-answer selection; all six balanced family permutations fixed before inference.
6. Shared private packets do not mutate when referenced by multiple teams. Different receiver histories have different cache keys even when seeds match.
7. Global private barrier and synchronous revisions; no revised-peer leakage; independently synthesized answers never feed revisions.
8. Only one model resident at a time, including error cleanup; model-major scheduling reproduces fixture outcomes from a logically task-major schedule.
9. Correct 2,400/476,160 ceilings, per-stage counts, 60-call smoke inclusion, actual versus logical costs, no implicit retries.
10. Strict parser/failure accounting, receiver-tokenizer context checks, valid mixed support versus disagreement with abstentions.
11. Hierarchy fixture with G=0 despite disagreement; complementarity fixture with G>0; overlapping rescue fixture where G>0 but some U_i=0.
12. Erasure with and without additional terminal loss, synthesis construction from all-wrong private answers, undefined conditionals and paired identity checks.
13. Accuracy aggregated by family rather than display slot; baseline maxima and bootstrap clustering recomputed from whole tasks.
14. Safe interruption/resume across model phases, unknown-dispatch handling, secret-free exports, raw/sanitized report reconstruction and artifact round trip.
15. Complete mock end-to-end FOUR-team study plus standalone readout with both useful and zero-complementarity fixtures. No positive-support gate preventing completion.
16. Relevant legacy natural/controlled replay and receiver/specialization configuration regressions remain intact.

Run available tests and report actual passes/skips/failures, not copied historical totals. Preserve unrelated or knowingly failing tests with an explanation; do not weaken assertions to fit the desired result. Code can be implemented and CPU-tested while every new official-model generation is GPU-unverified.

Finish with implemented files, concrete frozen sample/team/prompt fixtures, local commands, exact per-stage Colab commands, model-access/data prerequisites, expected artifacts, budget arithmetic, tests, and remaining runtime/scientific limitations. Do not claim a result, schedule a run, or end after another plan if a runnable implementation can be completed.

## 15. Primary references and source discipline

Background and model contracts checked for this implementation brief; Codex should verify compatibility against the ACTUAL pinned versions it uses:

- Yang et al., Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity, arXiv:2602.03794v1: https://arxiv.org/html/2602.03794v1
- Qwen2.5-7B-Instruct official card: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
- Llama-3.1-8B-Instruct official card/access: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
- Mistral-7B-Instruct-v0.3 official card: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3
- Qwen3-8B readout: https://huggingface.co/Qwen/Qwen3-8B
- Transformers chat template documentation: https://huggingface.co/docs/transformers/chat_templating
- Colab resource limitations: https://research.google.com/colaboratory/faq.html

The paper's strongest summarized two-versus-sixteen comparison involves its diversity configurations and is not a guarantee for this model-only three-agent PACT protocol. Its persona table is not evidence for an isolated family-only comparison. Do not insert published scores as our baselines or infer exact Instruct checkpoint variants from family names alone. No upstream code execution or remote-code trust is required to implement this study.

BEGIN by inspecting the existing repository and source instructions, then implement this bounded phase.
