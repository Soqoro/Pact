# PACT next update: a bounded GPQA-Diamond natural-support and clean-communication study

Version: 24 September 2026
Proposed run ID: `qwen3-gpqa-diamond-support-001`
Status: authorized implementation specification; no new experiment has been executed by this document.

## 1. Mission and workflow

Update the EXISTING PACT codebase. Implement one small, complete, inference-only study that asks:

1. Does GPQA-Diamond produce naturally mixed correct/incorrect private answers under the current three-agent setup?
2. Does one clean communication exchange preserve, erase, or use the answers that are present?
3. Does debate do anything useful beyond independent voting or frozen synthesis of exactly the same private packets?

Do not assume harder questions cause more useful diversity. Different wrong answers are not complementary correct coverage. Lower average accuracy does not establish proximity to a decision boundary. This screen can support a dataset/protocol decision; it cannot establish learned complementarity, adversarial robustness, or PACT efficacy.

My workflow remains: local Codex development and CPU tests -> my review and GitHub push -> pinned checkout and actual inference on Google Colab -> private results back to local Codex. Local CUDA is not assumed. Do not launch GPU work, download pretrained model weights locally, commit, push, or change remotes. Do not introduce Slurm, PBS, paid model APIs, another agent framework, Docker requirements, or multiple-GPU dependencies.

Implement a runnable vertical slice, not only a new audit/design document. Reuse the package, model backend, protocol, loaders, persistent artifacts, checkpoint restoration, metrics and notebooks. Preserve unrelated changes and historical experiment evidence. Do not broadly refactor or upgrade the working dependency stack to implement this study.

## 2. Read first and preserve the current result

Inspect Git status, `AGENTS.md`, project instructions, the original proposal and implementation specification, latest implementation decisions/status, experiment ledger, receiver-supervision methodology and the latest actual completed audit. Locate files by inspection: names below identify runs, not guaranteed local paths.

Latest completed run:
- `qwen3-receiver-supervision-controlled-001`
- Returned ZIP: `qwen3-receiver-supervision-controlled-001-handoff-1790186567377083314.zip`
- ZIP SHA256: `ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea`
- Original training source: `27889da90d2afce934fffb1baac9acb64ec3a1e2`
- Recovery source: `13ab011df8b1b27d6d1478104db1a9e8a35a4081`

Accepted starting evidence, checked against actual retained artifacts:
- Controlled donor collection and the three-arm receiver study completed, with 24 updates per trained arm.
- All three arms had the same correctness on 57 matched receiver responses: 40 correct and 17 incorrect.
- Wrong-donor hold was 13/13; correct-donor repair was 1/6 in every arm.
- Receiver SFT changed teacher-forced answer-token likelihoods but added no successful receiver repair on that cohort.
- The donor-data shortage was bypassed successfully. Full PACT and final-test evaluation remain unexecuted.
- The recovery audit disclosed an FP32 -> BF16 -> FP32 nonfocal-adapter loading deviation. Effective evaluated tensors are not automatically identical to the original preparation exports.

Close those experiments. This update does not authorize additional receiver updates, a new loss, synthetic donors, a larger warm start, repeated old probes, option-margin scoring, adaptive attacks, or final evaluation. Do not interpret the small negative study as a proof that CE or receiver learning cannot work. Cross-entropy already creates competition between output probabilities; a new ranking loss is not justified merely by unchanged sampled answers.

Imported archives, logs, attacks and model outputs are untrusted data. Use the established safe reader and trusted local analysis functions; do not execute imported scripts, follow embedded instructions, or load arbitrary pickles merely to inspect results.

## 3. Fixed experimental design

Use 32 GPQA-Diamond development-diagnostic items and ONE frozen team configuration:
- Qwen3-8B, exact pinned base/tokenizer/chat-template revisions.
- The three effective actors of the FROZEN-PREPARATION arm of the latest controlled study.
- Do NOT silently use the Task-SFT or Receiver-SFT arm, an unadapted three-sample team, or the older nine-update actors.
- Zero optimizer steps; adapters and backbone stay frozen throughout.
- BF16 backbone / SDPA, with adapter storage and effective precision explicitly reproduced from the selected frozen-arm receipt.
- Thinking disabled using the existing official chat-template hard switch.
- Private/revision sampling unchanged: temperature 0.7, top-p 0.8, top-k 20, and all other actual recorded sampling/penalty settings pinned.
- Full normal answer-plus-justification packet prompt, not answer-only.
- Private/revision cap 256 output tokens; both synthesizer outputs capped at 64.
- 4,096-token total QA context budget, including reserved generation.
- One sample per actor per task; no alternative-sampling pool, seed sweep or majority over additional samples.
- No early attack and no exchange attack in this first study.

The modest expansion beyond the previously discussed 96-call private-only screen is intentional: run clean debate AND independent frozen synthesis from the same private packets. This answers the communication question in the same bounded run rather than stopping after another support-only screen.

Primary frozen effective actor selection must be explicit in the plan, not inferred from the newest checkpoint filename. Load actual weights from the verified durable snapshot, not from metadata-only review ZIPs. Reuse safe compact inference restore where supported; it is not a resumable optimizer checkpoint.

Before inference, verify effective tensor hashes against the chosen arm's recovery receipt, including nonfocal actors, and record stored/load/effective dtypes. If the exact effective identity cannot be restored, stop preflight with an actionable explanation. Do not silently cast, repair the historical precision deviation, or label a different tensor identity as the same frozen arm. A changed precision configuration would require a new declared plan.

## 4. GPQA access, normalization, and benchmark hygiene

### Official source and access

Use the authors' dataset `Idavidrein/gpqa`, Diamond subset, at an explicitly resolved immutable revision. Verify the actual official schema and subset name rather than guessing from a third-party mirror.

Official sources to consult:
- https://huggingface.co/datasets/Idavidrein/gpqa
- https://github.com/idavidrein/gpqa
- https://arxiv.org/abs/2311.12022

The official Hugging Face dataset is gated and requests that questions not be published in plaintext or images online. Support a user-provided secret/token or an already authorized local official file. Never accept terms on the user's behalf, expose tokens, fetch an unreviewed mirror, or scrape around an access failure. Fail with `dataset_access_required` and the exact user action when access is absent. A legitimate downloaded official file needs recorded origin, revision and checksum.

Do not blindly execute an old dataset loading script or set `trust_remote_code=True`. Prefer the current official CSV/data-file access through existing installed tools. Pin source content and parser behavior without replacing the Colab stack.

### Data contract

Normalize the official final question and its four answer texts into the existing `TaskInput`/`TaskLabel` separation. Inspect official fields such as `Question`, `Correct Answer`, and the three `Incorrect Answer` fields; do not accidentally use pre-revision questions, validator feedback, explanations, or alternate revisions.

- Only the question and four uniformly formatted options enter defender/readout prompts.
- Dataset field names revealing correctness, official explanations, author/validator annotations, difficulty/accuracy metadata, and gold labels do not enter prompts.
- Correct answer text is naturally one of the four visible options; this alone is not leakage.
- Deterministically shuffle the options ONCE per task before any generation and record the source-to-canonical mapping. The correct answer must not always occupy A.
- Use the identical option order for all actors and both protocols on that task. Never shuffle separately per actor to create disagreement or reinterpret letters without mapping them back.
- Use official stable record IDs where present, otherwise a content-derived stable ID with an explicitly documented algorithm. Avoid process-randomized Python hashes and subset-index IDs.
- Preserve mathematical notation and Unicode. Validate nonempty fields, exactly four distinguishable options, consistent answer mapping and unique IDs. Unexpected schema/count changes fail preflight rather than silently changing subsets or dropping difficult questions.
- Preserve upstream canary/licensing metadata in the private dataset receipt. It is not a learner prompt instruction.

### Selection and evaluation exposure

GPQA-Diamond's published size is 198. This study deliberately uses 32 items for DEVELOPMENT DIAGNOSIS, not training and not untouched final testing.

- Resolve and record the actual official count and revision first; unexplained disagreement with 198 is a preflight issue.
- Choose 32 task groups using seed 20260924, before any model output or score.
- Stratify proportionally by the official high-level domain using largest-remainder allocation with stable tie breaking. Publish counts and algorithm. Missing/unexpected domain metadata must be addressed explicitly before freezing the selection, not silently inferred from gold/explanations.
- Use content/group screening for known repeated/exposed tasks. Review the existing project ledger for prior GPQA use. Do not claim no overlap merely because this is a new run ID.
- Known exact/near-duplicate groups must not straddle the diagnostic and protected remainder. A protected remainder is nominally 166 items, and may be smaller after documented known-group exclusions.
- Do not replace selected items based on answers, agreement, presumed ease, context length observed after collection, or post-hoc inspection.
- The selected 32 have `usage=development_diagnostic`, `training_allowed=false`, and `eligible_for_untouched_final=false` after this study.
- Protect the remainder from model generation and per-item exploratory inspection in this pass. Loading metadata to construct a partition is not model evaluation; log precisely what was accessed.
- An upstream split named `train` is a storage label, NOT permission for PACT SFT/DPO/replay-bank training.
- Block these examples, their continuations and their labels from all training and donor-preference exports.
- Later GPQA-main/extended use must exclude ALL Diamond content/groups reserved for evaluation; this pass authorizes no GPQA training.
- A later full-198 score must disclose development exposure; do not label it fully untouched. A protected-remainder result must name that nonstandard subset and denominator.

## 5. Protocol and exact budget

For every one of the 32 selected tasks:

1. Generate all three natural private packets independently and freeze them.
2. Compute the existing prespecified independent vote from those packets without another model call. Use the documented tie/invalid policy; never resolve a tie with the answer key.
3. Run the unadapted frozen synthesizer on the question and these three private packets: independent-synthesis baseline.
4. Run one clean synchronous exchange. Each actor revises from its own original packet plus the other two ORIGINAL private packets, never another revision.
5. Run the SAME frozen synthesizer on the question and revised packets: clean-debate outcome.

Existing synthesis prompt/template/decoding must be shared across the two readout branches except for the private-vs-revised packet contents. The private-based synthesis output may not feed into actor revisions. Keep agent/order/source-envelope settings fixed or use the existing declared deterministic scheme; do not add roles or encourage disagreement.

Disable all adapters for synthesis and restore the prior adapter/mode reliably. No model/adapter update or train-mode dropout. Distinct node seeds must be derived from immutable task ID + stage + agent + fixed study seed, not dependent on execution order, response length or subset position. Match readout settings, including deterministic decoding, across the two readouts.

Worst-case budget:

| Stage | Calls | Max output tokens |
|---|---:|---:|
| Private proposals | 32 * 3 = 96 | 96 * 256 = 24,576 |
| Clean revisions | 32 * 3 = 96 | 96 * 256 = 24,576 |
| Independent synthesis | 32 | 32 * 64 = 2,048 |
| Debate synthesis | 32 | 32 * 64 = 2,048 |
| TOTAL | 256 | 53,248 |

Vote/single-actor summaries require zero additional generations. There are 32 independent task IDs, not 96 or 256 tasks. These ceilings exclude input tokens and setup; log their actual costs separately. Zero optimizer updates, zero donor calls, zero private suffix replays, zero teacher-forced option-scoring forwards.

Implement plan/private/complete/report stages with safe resume, but predeclare full collection on ALL 32 tasks. Do not run communication only on mixed teams or stop for lack of disagreement; all-wrong-to-correct construction is a possible outcome too. Outcome-free integrity failures may stop safely. Inapplicable or incomplete conditional metrics remain null.

A real-model smoke can be the first two selected tasks using the exact frozen study requests, then reuse those completed calls. Do not add separate GPQA smoke questions, change the prompt after seeing their answers, or regenerate them. Use fictional CPU fixtures for local tests.

Count every actual dispatched inference attempt against the hard budget. Committed records are reused, not regenerated. Ambiguous in-flight attempts must remain explicit and cannot be retried invisibly. A run that loses records or exhausts its attempt budget stays partial; never manufacture completion or lower its denominator.

## 6. Context and parsing safeguards

Use the existing strict packet parser and answer grammar. Do not soften parsing on GPQA to improve its apparent score. Preserve raw completion, token IDs, parsed answer, stop reason, context lengths, source and effective actor hashes, node seed and decoding parameters.

Preflight all private prompts without revealing solutions. Check each actual revision/synthesis prompt before dispatch. Do not truncate the trusted question/options, trim scientific notation, introduce longer context, enable thinking, or raise output caps automatically. A future reasoning-budget sensitivity is a different experiment.

Handle completion failures and infrastructure failures separately. Abstentions, invalid answers and length-limited packets follow the recorded task-scoring policy; infrastructure-incomplete tasks are explicitly missing. Store sufficient raw status to report sensitivity to incomplete justifications even if an answer ID was parsed before a token limit.

A label-correct packet is not a verified rationale. Natural peer opportunities are defined from answer correctness and valid packet provenance, not certified scientific evidence.

## 7. Required scientific metrics

Reuse existing PACT metrics. Add only missing transparent task-level views.

### Private support

For each task define `C_i0` from the prespecified scorer and `N0 = sum_i C_i0`.

Report:
- Per-agent initial accuracy; mean and best agent accuracy.
- Counts `N0=0,1,2,3`, both conservative full-cohort and complete-valid-team views.
- Initial coverage `c = P(N0>0)` and joint initial failure `1-c`.
- Coverage gain `c - max_i A_i0` on the SAME complete cohort, labeled an oracle-availability diagnostic rather than deployable accuracy.
- Primary useful mixed support: at least one valid correct AND at least one valid wrong option packet. A correct packet alongside an abstention is not automatically useful complementary disagreement.
- Answer disagreement separately: distinct option IDs can ALL be wrong. Do not equate answer diversity with useful coverage.
- Pairwise disagreement and joint error rates with explicit denominators; mark invalid-only patterns separately.
- Natural repair opportunities: initially valid-wrong receiver with an initially answer-correct peer.
- Natural hold opportunities: initially correct receiver with a valid-wrong peer. No malicious attack is implied by an honest wrong peer.
- Count distinct task IDs supporting each stratum, total agent-context counts, and agent0-specific counts separately.

### Communication outcomes

For debate define `N1`, `O0 = 1[N0>0]`, `O1 = 1[N1>0]`, `Y = terminal success`.

Report:
- The 4x4 `N0 -> N1` count/row-conditional transition table.
- Utilization `u = P(Y=1 | O0=1)`.
- Construction `k = P(Y=1 | O0=0)`.
- Erasure `d = P(O1=0 | O0=1)`.
- New availability `r = P(O1=1 | O0=0)`.
- Readout loss `P(Y=0, O1=1)`.
- Hold retention/harmful revision and repair success with actual denominators.
- Private vote, independent-synthesis and debate terminal success.
- Per-task paired transitions between independent synthesis and debate.
- Input/output token and time overhead by protocol, counting shared private collection only once in actual-study totals but charging each protocol its logical use when reporting deployment cost.

Check `P(Y=1) = c*u + (1-c)*k` and the availability identity on complete cohorts, respecting undefined conditionals. Initial availability is not proof that a particular packet causally supplied the final answer. Natural before/after changes do not isolate adversarial causation.

All rates must contain numerator/denominator. Use task-clustered paired resampling for protocol differences; 32 items and one draw/actor are diagnostic, not an equivalence trial. For rates with zero/all events, provide an appropriate nondegenerate interval or explicitly flag boundary uncertainty; never treat an empirical [0,0] paired bootstrap as proof of equality.

Do not estimate expected useful disagreement as `1-pbar^3-(1-pbar)^3` using the average benchmark accuracy. Task-dependent difficulty and concentrated per-task policies make that inference invalid. One sample per actor does not estimate within-actor answer support or PACT pair yield.

## 8. Historical comparison and interpretation

An offline context table may show already completed ARC/LogiQA private-support results. Inspect raw metadata before including it. State dataset, task exposure, actor effective hashes, option handling, decoding and sample counts. Do not regenerate closed cohorts in this pass.

Historical datasets are not paired tasks and may have precision/checkpoint differences. Their comparison is descriptive. Even exactly matched models across two datasets do not isolate a causal effect of difficulty, because content/domain changes too. Do not present an independent 32-GPQA vs 24-ARC/LogiQA difference as a matched significance result.

Predeclare a practical screen flag (NOT a scientific efficacy gate):
- At least 8/32 distinct tasks with valid correct/wrong mixed support: sufficient observed support to DESIGN a bounded attacked-communication follow-up.
- 1-7: sparse, preliminary support; no broad claim and no automatic bigger sampling run.
- 0: no observed mixed support in this one configuration; not proof that GPQA or homogeneous teams can never supply it.

Missing calls, dominant invalid/truncated outputs, or unreproduced tensor identity prevent an uncomplicated support verdict and require their own qualification. The flag does not authorize any next experiment automatically.

Interpret communication separately:
- More mixed support plus erasure/readout failure: a plausible setting for the next clean-vs-attack preservation study.
- More mixed support but independent synthesis/voting is equally useful: diversity exists, but the need for communication remains unestablished.
- Mostly all-wrong teams: greater difficulty has not solved useful coverage under this protocol.
- Construction from all-wrong teams: analyze it explicitly instead of discarding those cases.

This clean study tests no adversarial attack. It also trains nothing on GPQA. Do not label it a PACT result or official full GPQA-Diamond leaderboard score. Do not adjust loss, temperature, context length, model, seeds or samples after reviewing outcomes without a new design.

## 9. Privacy, resumability and audit artifacts

Retain the existing scratch-first storage, immutable shards, bounded persistence workers, local recovery ZIP, verified snapshots, checksums and guarded resume. Do not redesign the storage system unnecessarily.

GPQA raw question/option text, explanations, rendered prompts, token arrays (which decode to text) and model responses that reproduce questions must remain in private access-controlled artifacts. Do not commit them in fixtures, public notebooks, reports, issues, logs, or public GitHub artifacts. Preserve upstream notices. Avoid printing them in Codex output that may be shared. No external inference service is needed.

Provide two explicit output views:
1. A private full audit bundle with necessary raw prompts/calls, mapping/labels, identities and manifests, stored outside Git and marked not for public redistribution.
2. A sanitized summary containing IDs/hashes, configuration, counts, metrics, costs and missingness, with no benchmark text, full option strings or recoverable token arrays. A sanitized bundle is not sufficient for a full raw-prompt audit and must say so.

Cache keys include exact task/input and option order, base/tokenizer/template and effective adapter identity, precision/runtime fingerprint, stage, seed, decoding and prompt version. No cross-agent state or KV reuse unless exact inputs and actor identity permit it under tested existing behavior. A dataset label must never change decoder settings or answer selection.

Expected outputs (adapt names to the existing schema):
- Frozen plan, source/config/request manifest and dataset revision/access receipt.
- Diagnostic/protected-remainder ID/group manifests and exposure ledger.
- Environment, checkpoint/effective identity and parser/prompt versions.
- Raw private/revision/readout shards (private bundle only).
- Per-task/per-agent scores, private-support report, transition counts.
- Protocol comparison and descriptive historical-context table.
- Resource totals, attempt/completion/missing counts, errors and checksums.
- `CODEX_HANDOFF.md` explaining what was executed, what was not, small-sample limitations, and a recommendation that requires review rather than scheduling another run.

Unknown compute units stay null. Reported wall time is not automatically billed GPU time. No tensors in a review ZIP means that ZIP cannot reconstruct missing weights.

## 10. Tests and first Colab run

Implement focused tests with invented QA fixtures; no GPQA examples in the test repository and no gated/network access in default tests.

Required checks:
- Official-shaped row normalization, four options, stable IDs, shuffled gold mapping and metadata exclusion.
- Option order identical across actors/stages; row ordering or subset iteration does not change identities/seeds.
- Stratified selection and group isolation; attempted training/final export of diagnostic items blocked.
- Access refusal is actionable; no silent third-party fallback, token leaks or remote-code execution.
- Raw/private vs sanitized export boundaries, including token arrays and error messages.
- Natural private packets frozen and byte-identical across independent synthesis/debate branches.
- No readout answer or prior revision enters revision prompts.
- Checkpoint/effective precision mismatch rejection and adapter disable/restore.
- A correct-plus-abstaining team is not a valid correct/wrong mixed-support example.
- Several different wrong options do not count as correct coverage.
- Metrics, denominator handling, zero-cell intervals, exact identities and task-level paired comparisons.
- Exact 256-call / 53,248-output-token budget; zero training/scoring/donor/replay calls.
- Smoke subset reuses the same requests, interruption/resume deduplicates committed calls, and incomplete runs do not silently shrink denominators.
- Mock full run, private and sanitized export/import, and CPU metric reconstruction.

Run the relevant existing regression suite and record actual passes/skips/failures. Optional tiny locally initialized model tests do not prove pretrained Qwen behavior. Do not download weights or launch GPU inference locally.

Provide thin CLI/notebook steps for:
1. Parameters: repository/ref, run ID, frozen-arm full/compact snapshot, authorized dataset source/token, scratch/persistent roots.
2. Dataset/checkpoint access and identity preflight BEFORE starting expensive work where possible.
3. Freeze plan and 32-item manifest.
4. CPU validation and two-task real smoke using the exact planned requests (GPU execution by me only).
5. Complete the 32-task private/clean-debate/independent-synthesis study under the same plan.
6. Export private/sanitized bundles and show durable paths plus checksums.

Use actual CLI syntax after implementation; do not claim illustrative commands already work. Default Run All must never train, attack, evaluate protected items, or expand the sample budget. The requested study may complete all 256 planned calls without a separate code change, then stops for human review.

## 11. Final handoff to me

Update the experiment ledger, decisions, status, GPQA exposure policy and Colab runbook. Keep `AGENTS.md` concise. Mark original experiments closed and the new GPQA study as implemented/CPU-tested/GPU-unverified as warranted.

Finish with:
1. What changed and which files changed.
2. Chosen dataset access method, normalization and shuffled-answer schema on a fictional fixture.
3. How the exact frozen effective actor identities are restored.
4. Tests actually run and outcomes.
5. Exact Colab commands/cells and path/credential prerequisites.
6. Frozen budget and planned reports.
7. Explicit deferred work and interpretation limits.

Do not manufacture benchmark results, a GPQA access grant, tensor verification, new loss efficacy, or a publication claim. Do not change manuscript result placeholders. Leave a complete usable local implementation ready for my review and Colab execution.
