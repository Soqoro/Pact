# PACT revival: train the communicating agents, then test prospective update allocation

Prepared 16 October 2026. Design version: `pact-revival-20261016-v1`.
Primary execution preset: `pact-heterogeneous-receiver-training-001`.
Separately invoked follow-up preset: `pact-update-allocation-probe-001`.
Method family: `heterogeneous_dense_pact_v1`.

**Status:** new implementation specification and proposed bounded experiments. This document is not a repository patch, completed training result, or authorization for unattended GPU execution. Resolve collisions with existing run IDs without overwriting work.

## 1. Mission and scope

Update the EXISTING PACT repository. Restore the original research focus: learning complementary adversarial capabilities in the communicating agents, coupled to learning how to preserve correct information and repair mistakes. Do not pivot back to training a final judge, checker, or CPU KEEP/SWITCH gate.

Read applicable AGENTS.md files, Git status, the original conference proposal, the latest completed gate/selector/research audits, implementation decisions, model registry, exposure ledger and current source/CLI/notebook/tests before editing. Reuse working code. Preserve unrelated edits.

Implement three connected capabilities:

1. A complete real training/evaluation study comparing frozen Q/L/M, independent adversarial SFT and uniform joint SFT. This is the next executable phase.
2. A complete but separately invoked prospective-update assay: temporarily train each agent on a small fitting block and measure the resulting communicated team on disjoint allocation probes.
3. A reusable, CPU/mock-tested two-round coupling orchestrator and allocation interfaces. Actual multi-arm coupled training requires a separately frozen plan after the preceding findings are reviewed. Do not invent a full-coupling GPU budget or treat two optimizer epochs as two communication refreshes.

Workflow: local Codex implementation and CPU/mock tests -> user reviews/commits/pushes -> pinned Colab checkout -> explicitly invoked GPU stages -> returned private/sanitized evidence -> local audit. No local pretrained downloads, GPU jobs, paid APIs, automatic commits/pushes, secret access, Slurm, SSH, multi-GPU requirement, or unrelated framework/dependency migration.

The first deliverable must include actual adapter training, loss masking, evaluation and recovery code. Do not stop at another support-only screen. Missing real artifacts should not prevent fixture-backed implementation.

## 2. Historical boundaries and scientific interpretation

Preserve every original completed/stopped/incomplete run. In particular:

- Original same-agent correct/wrong packet sampling was sparse; controlled replay closed incomplete. Do not resume it, repair its recovery flags, or relabel missing credits as zero.
- Receiver SFT previously changed likelihoods without incremental matched receiver correctness.
- `pact-selective-correction-001` genuinely fitted five CPU gates but selected KEEP_ONLY. Its trained gates are not the agents being trained here.
- The corrected selector has a functioning prospective baseline, not a replacement score for historically malformed outputs.
- Human semantic annotation, cue/sham interventions, judge transfer, MBPP isolated execution, LiveBench, new GPQA communication and five-agent work remain deferred/out of scope.
- Existing 230 MMLU-Pro/MuSR characterization tasks, MATH/GPQA cohorts, previous 224 selective-correction tasks and all recorded related groups remain excluded from the new fitting material. Preserve original fit-only permissions separately; do not silently reclassify used data as fresh.

The original hypothesis is retained; these mechanisms CHANGE:

- three heterogeneous backbones replace three shared-Qwen3 adapters;
- dense answer supervision replaces the prerequisite for naturally sampled DPO pairs;
- actual short training-update effects replace correct-versus-incorrect message insertion as the proposed allocation assay.

A positive Stage I is evidence for the tested receiver-training recipe, not full PACT. A nonzero Stage II score is not proof that its allocation improves later training. Uniform joint SFT is not team-reward RL, COMA, or a reproduction of any published MARL method.

## 3. Fixed models, roles and execution profile

Use immutable official revisions from the current verified registry:

- Q: `Qwen/Qwen2.5-7B-Instruct`.
- L: `meta-llama/Llama-3.1-8B-Instruct`.
- M: `mistralai/Mistral-7B-Instruct-v0.3`.
- R: pristine `Qwen/Qwen3-8B`, frozen readout, explicitly non-thinking.

Q also generates attacks in its PRISTINE, adapter-disabled role. The three trainable agents have distinct LoRA adapters, each used for BOTH private and receiver turns. R never receives an adapter, gradient, gold label or training update.

Load one large model at a time, grouped by model/stage. Native tokenizer, chat template, EOS/end-of-turn handling, padding, attention configuration and context lengths belong to every model contract. A Qwen tokenizer is not valid for Llama/Mistral. Resolve model access before generation; do not accept gated-model terms for the user or log tokens.

Default new profile: BF16 backbone, SDPA, batch one, maximum total recipient context 8,192 tokens and 512 maximum generated output tokens. Proposers/revisions and attack generation use the repository's pinned sampling fields (temperature .7, top_p .8, top_k 20); R is greedy. Explicitly record all inherited fields. These limits do not guarantee fit on any Colab GPU. No silent quantization, shorter input, switched reasoning mode, model substitution or hidden retry.

LoRA initial preset: rank 16, alpha 32, dropout .05, bias none, targets `q_proj,k_proj,v_proj,o_proj`, frozen embedding/lm_head/backbone. Inspect actual module paths/shapes for each family; fail preflight rather than targeting a nonexistent module. Use no-op B-zero initialization. FP32 adapter and optimizer state, explicit audited compute casting, BF16 base. Verify round-trip effective values; never route FP32 saved adapters through an unrecorded BF16 cast.

Training: AdamW, lr 5e-5, betas (.9,.999), eps 1e-8, weight decay 0, gradient norm clip 1; eight warmup optimizer steps then constant LR for Stage I. Microbatch one prompt at a time, accumulation over EIGHT TASK GROUPS, including their weighted contexts. Gradient checkpointing may be used with supported frozen-embedding gradient handling. Disable generation KV cache while training, restore for inference. Pin compatible dependencies rather than upgrading to latest.

All numeric settings are prespecified experimental choices, not claimed optimal values. Stage II uses the same LR but no warmup, for eight temporary steps.

## 4. Split plan and block construction

Freeze 960 new eligible groups from the already supported official ARC-Challenge TRAINING and original English LogiQA TRAINING sources:

| Role | ARC | LogiQA | Total |
|---|---:|---:|---:|
| main_fit | 256 | 256 | 512 |
| allocation_probe | 32 | 32 | 64 |
| validation | 64 | 64 | 128 |
| source_evaluation | 128 | 128 | 256 |

Use seed 20261016 with stable group/role namespaces. Preserve official source revision and original option mapping. Exclude all recorded prior uses, duplicate/content groups, protected allocations and cross-source duplicates under the existing reviewed policy. Refuse a ledger newer than the exposure inventory's reviewed coverage. This is lexical/source grouping, not semantic decontamination.

If exact quotas cannot be met, emit the actual shortfall before LLM calls. Never quietly use official test items, shrink the population, replace data based on outcomes, or train on old characterization cohorts. Implement/test all modules with fixtures despite data shortfalls.

Allocation probes are TRAINING-USE meta-data: no direct gradient on their tokens, but their labels select responsibilities. They are not test/validation examples. Validation is never used for gradients/probe allocation. For this first preset, epoch 2 is the fixed primary checkpoint; validation describes behavior, not prompt/LR/checkpoint search. Source evaluation requires frozen model/method hashes and is run once per declared arm. It is a bounded source-domain research evaluation, not the project's final confirmation benchmark.

Predefine eight allocation blocks: four per source, 64 fitting groups each, paired with eight distinct same-source allocation-probe groups. Hash partition within each source without seeing responses/labels beyond source eligibility. These are training batches, NOT asserted semantic specialties. All probe groups are distinct across blocks. No clustering or expert-model semantic labeling is introduced in this preset.

Stage I uses main_fit/validation/source_evaluation only (896 tasks); allocation_probe text/generation stays locked until Stage II is explicitly invoked.

## 5. Communication protocol and unambiguous answer-bearing output

Each task has three natural private packets. Freeze all private packets before constructing delivery. Each receiver sees the trusted task, its own private state, and the other agents' ORIGINAL delivered packets. Revisions are synchronous; none sees another receiver's revision. R sees trusted task and revised packets only, not an independent judge answer or an archive of private drafts.

Clean and exchange conditions share the same private bank. The exchange attack overwrites one sender's outgoing packet identically for both recipients. The sender's private state remains unchanged, and it does not receive its own malicious replacement. Final readout still receives that sender's actual revised packet. This is message-integrity corruption, not poisoned model weights.

New output contract, versioned and fixed before generation: exactly two JSON keys, `answer` first and `justification` second. `answer` is an allowed task option or `ABSTAIN`; `justification` is concise text. Examples explicitly distinguish KEYS from VALUES. Use the same semantic contract for all actors, stages and arms. R also uses answer-first output for this NEW experiment so its answer likelihood can be scored before any generated rationale. This readout-prompt change is explicit; historical different-format readout numbers are not matched controls.

A strict completion must finish within cap and parse; no stripping extra keys, lenient option extraction from prose, forced answer selection, retries or fallback to a previously correct answer. Invalid/abstaining outputs are scored as failures, with reason codes. Infrastructure missingness is incomplete data, not a failed neural answer. Malformed peer outputs have frozen public unavailable envelopes; do not synthesize valid answers from them.

Gold labels, hold/repair strata, correctness flags, source-family names and adversarial-style tags never enter defender inputs. Anonymous slot assignments are balanced and frozen before outcomes. The visible provenance is the task-defined sender slot, not a claimed ability hierarchy.

## 6. The dense training target: no fabricated gold reasoning

At training time use the SAME generation prompt but supervise only the answer-bearing prefix, for example the assistant prefix ending after the correct answer string and its closing quote. Do not append an empty justification, an invented rationale, a false EOS or a claim that a sampled explanation is a verified proof.

Default scientific loss is the mean NLL of the token span encoding the official answer (including only unavoidable boundary pieces). The canonical JSON opening/prefix is teacher-forced, masked; do not accidentally reveal answer characters before their scored positions. Text after the scored answer is neither trained as a gold rationale nor used to condition its loss. Evaluation is full autoregressive packet generation with no gold prefix.

Implement a model-native PrefixTarget/mask builder. Do not assume the option is one token. Validate causal shift, token merging at string boundaries, fast/slow tokenizer compatibility, special tokens and target boundary recovery. Score every token required to distinguish the correct answer, not just a convenient final character. Reject ambiguous mask construction; do not substitute a target-containing user prompt.

This provides answer supervision even when no generated completion is correct. It does NOT establish rationale correctness or a learned semantic mechanism. Report answer-prefix loss, generated answer correctness, strict format completion, rationale length and generation-cap effects separately.

Small gradient/format sanity check: the first TWO fixed fitting tasks per source ordering overall (one per dataset) are included in the source bank. For EACH family, use a temporary adapter, 16 private-prefix optimizer steps at microbatch one, then two post-update private generations. Baseline private outputs are reused by exact identity. Restore starting adapters and discard temporary optimizer state. Maximum 48 scratch steps/48 training forwards and six new generations. The purpose is engineering responsiveness; do not claim these memorized tasks generalize, select later examples by success, or increase its budget. Failed finite/nonzero gradients or checkpoint restoration stop technically; a lack of post-update answer flips is reported, not hidden.

## 7. Shared attack acquisition

Primary Stage I threat: fixed exchange corruption only. Early common exposure, combined attacks, recipient-specific payloads and adaptive query search are later plans.

Acquire at most ONE attack packet per task from pristine Q before defender evaluation/training-context use. Q sees task/options, a seeded assigned wrong target option and the style instruction. It does not see actual defender responses, successful attacks, the gold as privileged metadata or a chosen honest correct peer. Offline target selection excludes y; do not claim this proves black-box targeting without labels.

Fitting styles alternate by predetermined hash between `argument_pressure` and `claimed_verification`. Validation/source-evaluation use the held-out style names `claimed_consensus` and `claimed_independence`, balanced by source. These names describe generator requests, not semantically certified contents. Only one attempt per task. Select sender independently of success/correctness; balanced by source/split. All arms use the SAME task/payload/sender pool, not arm-specific attacks picked after outcomes.

Payload acceptance requires the exact packet schema, the designated wrong option and bounded serialization/context. Keep rejected raw attempts and reasons; no manufactured replacement or correct-packet donor. A rejected payload leaves the attacked condition unavailable, not equivalent to clean and not a defended success. Clean processing continues, and attacked reporting uses actual support and missingness-aware bounds. No budget moves from rejected attempts to new examples.

## 8. Stage I: two actual training arms plus frozen control

Names:

- `frozen_qlm`: no adapter updates.
- `independent_adversarial_sft`: all three adapters trained, with no honest peer information during receiver-style training.
- `uniform_joint_sft`: all three adapters trained with natural delivered peer information.

The starting weights, LoRA initialization, task order, answer targets, attack exposure, receiver-stratum weights, optimizer schedule and number of task-group updates are matched within family. Fresh independent optimizer states per arm. Do not update just focal Q or reuse a trained adapter as the other's initialization.

Collect exactly three pristine private packets per FIT task (1,536 calls). Fitting receiver prompts are built from these natural packets; do NOT generate revisions merely to obtain correct training targets. Labels provide those targets. No fitting readout or correctness-conditioned alternative sampling is needed. All groups remain in training/accounting, including all-correct/all-wrong and malformed-source states.

### The independent control must receive the attack too

For `uniform_joint_sft`, use normal clean and attacked receiver inputs.

For `independent_adversarial_sft`, use the same trusted task and saved own private state, but replace honest incoming peer contents with explicit withheld envelopes. In the attacked view, retain the SAME corrupt sender packet in precisely the slot seen by that receiver; do not expose the corrupt sender to its own overwritten message. This tests learning under the same misleading text and labels, without learning from honest peers. It is a matched no-honest-peer supervised control, not a claim of identical prompt length or global-reward MARL.

Private-task input is identical across arms. Both arms receive the same number of supervised contexts and target answers. Under the shared live evaluation protocol, both trained teams communicate normally; only training exposure differs.

### Loss and weights

For agent i:

    L_i = 0.5 * (1/N) sum_x ell_private_i(x,y)
          + 0.5 * sum_(x,c) w_i,x,c * ell_revision_i(h_i,x,c,y),

where N=512, c is clean/accepted exchange, and sum w=1 for compatible revision training contexts.

Compute weights from the FROZEN common fitting bank, not per-arm outcomes. Conditions receive equal aggregate mass when both exist. Within each condition classify receiver states into hold-conflict, repair-available, wrong-without-correct-peer, and remaining retention contexts. For four disjoint supported categories, use inverse-frequency multipliers n_condition/(K_present*n_category), clip to [0.25,4], then normalize within condition. Missing categories remain missing. The same weights apply to the independent control, despite honest peer text being withheld. Report distinct-task support per receiver/category and achieved mass after clipping, including invalid-original-answer cases separately.

HOLD requires initially correct own answer and an actually delivered valid wrong message. REPAIR requires initially incorrect/unavailable own answer and at least one actually delivered correct peer. A correct packet overwritten in delivery is NOT available evidence to its recipient. Strata affect training sampling/weights only, never prompt text.

All-answer-wrong contexts still receive label supervision. Do not institute a positive-pair or 100-task support gate. Low per-stratum support limits the claim; it does not justify indefinite resampling. Context/token incompatibility is an explicit prerequisite failure, not a reason to remove unfavorable tasks.

Accumulate by eight task groups. For a minibatch M of groups use the globally normalized importance coefficients (N/|M|) for revision weights, not a separate per-microbatch denominator. Test loss and gradients against an independent full-batch reference, including unequal strata and unavailable attack conditions. Do not renormalize each agent's later specialization weights so their relative effect disappears.

Run exactly TWO EPOCHS, 64 updates/epoch/adapter =128 updates per adapter. Total six fitted adapters and 768 committed main optimizer updates, plus at most 48 scratch sanity steps. At most 18,432 main supervised sequence forwards (6 adapters *2 epochs *512 tasks *3 contexts), plus 48 scratch forwards. Report actual counts separately. TWO EPOCHS ARE NOT TWO PACT OUTER REFRESHES.

Save epoch checkpoints, but fixed primary is epoch2, with no checkpoint selection by evaluation accuracy. Do not add more epochs, alter LR or relabel a low-loss result as efficacy. Main Stage I specialization weight is ZERO; it tests learnability of the preservation/repair ingredient first.

## 9. Stage I evaluation: behavior and peer use, not just NLL

Run all 128 validation and 256 source-evaluation tasks for frozen/IAT/joint checkpoints, both clean and fixed exchange conditions. Each team/task uses three shared private calls, six revision calls, two R calls: 11 maximum. Fresh private/revision outputs come from the actual method checkpoint. Generation seeds are paired by task/node/condition, not a mutable RNG stream. Changed prompt/checkpoint is always a new cache identity.

Keep validation and evaluation separate. Freeze method/epoch/weights before evaluation; a negative valid validation result does not quietly change the preset or select tasks.

Primary: final team correctness under exchange, with clean correctness also primary for utility. Secondary: individual private correctness, coverage beyond best member, N0->N1 transitions, hold/repair, erasure, final readout loss and construction. Report task-group uncertainty and all conditional support counts; calls/receivers/payloads are not independent samples. No trained-defense guarantee or clean noninferiority certificate from a few zero harms.

### Fixed-context peer-use diagnostic

Select 64 validation tasks (32 per source) by hash BEFORE outcomes. Use FROZEN team's exact original private histories for all checkpoints, not each trained model's own new history. Evaluate every receiver at frozen/IAT/joint weights with:

1. normal delivered peers;
2. honest peers withheld, corrupt slot retained where it was actually delivered.

Both clean/attack conditions. The frozen present-peer calls are exactly reusable from live frozen evaluation (384 calls). New fixed-context present-peer calls for IAT/joint:768. New withheld calls for three checkpoints:1,152. Total extra=1,920 generations.

This measures change in peer-use behavior on common histories; those are off-policy receiver diagnostics, not natural team accuracy. Analyze training-arm x peer-access interaction. A loss decrease or better task-only accuracy does not establish improved use of peer evidence. Keep raw output failures; do not substitute correct anchors as fallbacks.

## 10. Stage I execution and exact ceiling

| Component | Calls maximum |
|---|---:|
| Three FIT private packets | 512*3 = 1536 |
| Shared attacks for fit/validation/evaluation | 896 |
| Three teams' validation+evaluation, clean/exchange | 3*384*11 = 12672 |
| Extra common-history peer-use diagnostic | 1920 |
| Optional bounded scratch sanity outputs | 6 |
| **Stage I total** | **17030** |

Output reservation at512: **8,719,360 tokens**. Attack rejections/exact reuse can reduce calls; they do not replenish budgets. Training/scoring forwards, input tokens, loading, storage and compute-unit billing are separate counters. No time/billing forecast is implied.

First Colab smoke: TWO predetermined fitting tasks, three pristine actors each =SIX calls included in1536. Source-only smoke first; export and stop. The first training milestone is the bounded scratch check, then the complete two-arm six-adapter study. A notebook Run All must not launch17,030 calls. Every collect/train/evaluate stage is explicit and resumable with the plan hash.

There is no need to open the original PRIVATE adjudication archives to execute this new source study; source models, supported dataset access, reviewed exclusions and repository contracts are the prerequisites.

## 11. Stage II: prospective training-update contribution (separately invoked)

Implement now; do not auto-start after Stage I. Base snapshot is the final epoch2 `uniform_joint_sft` TEAM, pinned independent of which arm looks best. The user reviews the Stage I report before invoking the frozen Stage II plan. This is execution sequencing, not an automatic positive-result test or permission to substitute a favored checkpoint.

Use the64 allocated probe groups and eight predetermined fitting blocks. Generate one new fixed attack per probe group, same exchange semantics and a prescribed balanced style allocation. Freeze it before scoring any candidate update.

For each block B and agent i:

1. Restore the identical starting full-team snapshot, adapter tensors and relevant runtime state.
2. Create a temporary copy of adapter i; fresh temporary AdamW state.
3. Train it on B's64 private supervised contexts ONLY for eight optimizer steps (8 groups/step), one pass, lr5e-5 without warmup. No receiver loss in this temporary update. Never train on probe inputs/labels. This approximates the value of allocating extra PRIVATE capability training, not a mixed intervention with extra receiver training.
4. Evaluate its assigned eight disjoint probe tasks under clean/exchange for TWO paired generation seeds.
5. Regenerate that actor's private packet and ALL affected receiver revisions/readouts. Reuse the other two private packets ONLY by exact identity. The trained actor's changed receiver behavior is part of the total update effect because its adapter is shared across turns.
6. Record outcomes, freeze temporary evidence, then restore the source snapshot. No temporary parameters/optimizer state leak into other branches or become a committed PACT update.

24 temporary fits *8 steps =192 temporary updates, 1536 supervised sequence forwards. Different backbones have different compute; equal steps/examples are not equal FLOPs. Report memory and wall/accelerator usage, not assumed cost equality.

### Scores

For block B, agent i, condition c, seed s, compute actual generated final correctness and teacher-forced answer-prefix NLL from the SAME frozen R on the resulting revised packets. Gold scoring is offline and never enters generation.

    v_terminal[B,i] = mean_c,s,x ( L_R(before) - L_R(after update i) )

Equal task, condition and seed weighting. Also store clean/exchange separated values, paired accuracy deltas, private correctness/coverage changes, receiver errors and readout-loss events. Keep negative/zero values and missingness. Never equate nonzero NLL change with improved generated accuracy, or certify model rationales from the label.

A local comparator records before-after private answer NLL under that actor and actual private correctness changes. Raw cross-family NLL calibration is not matched, so label this limitation; report it alongside common-readout terminal effects rather than asserting all scales are intrinsically comparable.

Optional CPU assignment matrices for review can use the terminal NLL gains in the existing soft balanced solver with costs -v, tau=.2, balance=.1, a row-simplex and uniform fallback for genuinely unsupported rows. Do not convert missing scores to measured zero or amplify nearly flat scores via data-dependent normalization. Equal per-row contributions must cancel. Provide uniform, local-only, terminal, and a fixed source-stratified row-shuffle control preserving column totals. No matrix is promoted to a deployed training policy by this assay alone.

Compare mean agent-wide effects with within-block differences: an allocation always favoring one model may be a capability/learning-rate hierarchy, not learned complementarity. With eight probe tasks/block and two seeds, assignment uncertainty remains large. Seeds are repeated measurements, not extra independent tasks.

### Stage II exact ceiling

Per seed, baseline probe bank:64*11=704 generations.
Per seed, update branches:64*3*(1 updated private +2 conditions*4 continuation calls)=1728.
Two seeds:2*(704+1728)=4864.
Attack acquisition:64. Total **4928 generations**, **2,523,136 reserved output tokens**.

Teacher-forced diagnostic sequence forwards:1024 terminal R scores (64*2 conditions*4 snapshots*2 seeds) plus768 private scores (192 base+192 updated per seed), maximum **1792**. These are not generation calls. Reject score reconstruction that conditions a prediction on its gold answer already being visible.

Two probe tasks' bounded prefix can be a smoke INSIDE this plan; identify request dependencies rather than adding calls. Stop/export at completion even when all scores are flat or inconsistent. Do not launch Stage III automatically.

## 12. Stage III: implement coupling, but require a new finite execution plan

Implement a reusable two-or-more-outer-round orchestrator with fixture coverage:

    snapshot -> collect current natural private/delivered histories
    -> prospective update probes -> allocation report/frozen responsibility matrix
    -> positive private specialization + supervised receiver updates
    -> refreshed snapshot -> repeat -> locked evaluation

MethodSpec must explicitly bind loss weights, cohorts, family checkpoints, update budgets, query budgets, selection rule, assignment origin and refresh policy. No unspecified loops, default extra data or unbounded probe count.

Support comparison modes: uniform joint training; local specialization plus receiver training; terminal-aware static allocation; terminal-aware refreshed allocation; source-stratified shuffled assignments; and split specialization then receiver training. Generic loss hooks may reuse original base/spec/revision structure, but all new real runs need a prospectively fixed budget/weight contract. Training-weight sums must be global and matched; every agent retains base positive supervision.

CPU/mock tests must execute two complete rounds, showing that refreshed mode recomputes responsibilities while static mode retains its originals, all clones are isolated and matched label/query exposure is accounted. This is implemented orchestration, NOT GPU evidence of coupled PACT. Do not claim equal-compute superiority when probe labels, temporary updates or added rollouts are hidden. Strong team-reward RL and published communication defenses remain necessary later comparators, not renamed SFT arms.

## 13. Persistence, contracts and implementation acceptance

Use existing immutable intent/result journals, bounded private readers, scratch-first atomic writes and resume rules. A completion marker requires actual validated evidence. Unknown in-flight dispatches/optimizer steps stay unresolved; retries count and cannot silently duplicate gradient updates. Each training checkpoint includes adapter/optimizer/scheduler/RNG/sampler state and exact global step. Review ZIP inventories are not substitutes for recoverable weights.

Full IDs include task/group, split, team snapshot, actor, stage, condition, private-bank/delivery/payload identity, prompt/target parser/tokenizer hash, seed and adapter hash. Cache equality requires semantic dependency equality, not just matching seeds. Temporary probe scoring never executes untrusted imported scripts/pickle. Escaped private HTML treats candidate text as data, not instructions.

Model/training/process info, actual input/output lengths, stop reasons, generated calls, reused logical paths, training forwards/steps, scoring forwards and system resource limits must be reported separately. A promised H100/96GB GPU is not a verified runtime identity.

Potential CLI capabilities (adapt to actual repository conventions and supply REAL commands after implementation):

- revival inspect / plan / preflight / source-smoke
- revival collect-fit / acquire-attacks / build-training-bank
- revival train-sanity / train-agent --arm --family / freeze-team
- revival evaluate --split validation|source_evaluation
- revival evaluate-peer-use / report / export
- update-probe plan / collect-base / temporary-update / evaluate-branches / score / assign / report
- coupled-training plan / run-round (inference disabled without an explicit approved plan)

Default action offline. Thin notebooks call tested package functions; no duplicate training logic in cells. Required input paths are actual artifacts verified in the repository, not invented Drive locations. User handles model access, pushing and Colab starts.

## 14. Required tests

1. All960 split/group counts, prior-use/locked exclusions, reviewed inventory freshness; probe labels marked training-use, no gradients on probe/validation/evaluation data.
2. Q/L/M native serialization and trainable-module validation; no-op initial adapters; independent arm initialization parity; frozen base/readout and attack-generator isolation.
3. Answer-prefix masks/causal offsets for multiple tokenizers, multi-token labels and merging; no gold leakage or fake rationale/EOS target; finite nonzero adapter gradients.
4. Full-batch versus accumulated weighted gradient parity, condition/stratum clipping/normalization, missing attack cases and per-agent shared weights across controls.
5. Independent training retains exactly visible adversarial text while withholding honest peers. Sender cannot see its overwritten outgoing message as its own private state.
6. Natural synchronous delivery; clean/exchange shared private calls; no revised-peer chaining, automatic anchor fallback or post-hoc parser repair.
7. All three adapters actually update; correct own adapter used at private and revision turns; no focal-only shortcut; train/eval dropout/cache switching.
8. Checkpoint save/reload/resume with exact global step and optimizer state, FP32 adapter preservation, interrupted step handling and no budget reset.
9. Fixed epoch2 selection; all evaluation tasks kept; no generated-success gate or heldout routing. Peer-withheld diagnostic uses identical frozen histories across weights.
10. Prospective probes change only one actual adapter, use disjoint targets/probes, rerun every affected stage, restore exactly before every branch, use fresh temporary optimizer state.
11. Paired two-seed update scores, before-after sign, NLL versus correctness distinction, private/terminal scale caveat, no fake credit for absent score.
12. Equal-credit invariance, uniform fallback, fixed source-stratified shuffle with preserved total exposure, and no noise-rescaling to force differences.
13. Two-round fixture coupling vs static mode; assignment weights affect private training without being separately renormalized away.
14. Exact Stage I17030 /Stage II4928 ceilings, six-call source smoke inclusion, training/temporary/teacher-scoring counters, safe incomplete exports.
15. End-to-end tiny local randomized causal-LM fixture runs a real differentiable adapter update, source -> context -> both training arms -> eval -> temporary probe -> assignment -> two mock rounds -> export/import.
16. Actual CLI/notebook entrypoints, key relevant legacy tests and attack/report-text privacy. Report real passes/skips/failures; don't copy old test totals.

## 15. Outputs and handoff

Provide actual source code and tests, plus plans/model/optimizer contracts, split/exposure manifests, immutable private banks, attack inventory, supervised target/mask records, per-agent stratum counts, loss/gradient/format diagnostics, adapter/checkpoint recovery receipts, live and fixed-context per-task outputs, training/resource accounting, and private/sanitized reports.

Stage II additionally exports all branch restores, temporary-update IDs, paired score tables, uncertainty/sensitivity, proposed allocation matrices and label/query-exposure ledgers. No raw benchmark texts, decodable tokens, answers or reasoning in sanitized Git summaries.

Finish with changed files, exact first SIX-CALL source smoke instructions, per-agent training/freezing/evaluation commands, expected bundles, required access/source availability, actual CPU tests, what remains GPU-unverified and the Stage I review boundary before allocation probes. No new scientific result, codebase implementation or test execution may be claimed merely because it appears in this prompt.

References for implementation checks (not permission to update dependencies/download during CPU tests): official model cards for Q/L/M/R; PEFT LoRA and checkpoint documentation; existing original English LogiQA and ARC sources. Use the repository's compatible pinned versions. This brief retains the original proposal's coupling goal; its concrete losses, update assay and budgets are proposed design choices.

BEGIN by reading the repository and this specification, then implement the smallest COMPLETE Stage I training study, the separately executable Stage II assay and fixture-backed coupling orchestration.
