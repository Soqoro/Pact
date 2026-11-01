# PACT Stage II — reviewed GPQA Main / LogiQA source amendment and Slurm implementation

Prepared: 28 October 2026. Planning version: `gpqa-logiqa-slurm-review-v2`.
Status: implementation, CPU source audit, and runbook preparation only. No source acquisition, model execution, training, submission, human approval, or scientific result is implied.

This supersedes the preceding GPQA/Slurm **planning prompt**, not an executed study, source manifest, checkpoint, budget ledger, or protection rule. Preserve the preceding prompt and all historical evidence. The purpose is a narrow evaluation-source amendment, not another redesign of PACT or cluster migration.

## 1. Task, authority, and contract resolution

Update the EXISTING PACT repository. Read AGENTS.md, Git status, the executed-source Stage II v3 design, subsequent source-amendment reviews, latest Stage I source/checkpoint receipts, exposure ledger, actual Stage II consumption history, existing GPQA/LogiQA loaders, and CURRENT SLURM runbook before editing. Actual executed manifests and explicit amendments govern facts; earlier narrative counts are not substitutes.

The proposed prospective evaluation is **64 eligible GPQA Main groups + 64 eligible original English LogiQA groups**. GPQA replaces only the prospective science-evaluation source. Do not replace ARC fitting material or allocation probes. Preserve the original ARC-cohort infeasibility record and OpenBookQA proposal/preview-exposure history.

Local authority: inspect authorized available artifacts, edit source, run CPU/hash/parser/mock tests and tiny randomly initialized local-model tests, and prepare actual commands. No pretrained downloads, automatic data downloads, real model inference/scoring/training, SSH/cluster queries, sbatch/srun submissions, credential inspection, commits, pushes, remotes changes, or cleanup. Existing permissions may be reused only within their documented scope.

Produce a compact contract-resolution record for inherited and changed fields with artifact references. Use a collision-checked PROPOSED child identity, with old parents immutable. A missing real artifact may block the dependent real stage, but does not prevent completing independent modules with fixtures. Do not invent eligible counts, execution history, site settings, approvals, or code entrypoints.

Keep three readiness questions separate:
1. Can the code and proposed contract be implemented? CPU/mock evidence answers this.
2. Does a real eligible cohort exist? Actual source bytes and exclusion evidence answer this.
3. May a GPU stage run? Source freeze, relevant consumption reconciliation, actual checkpoint/runtime checks, a finite remaining budget, and existing explicit user execution approval answer this.

Do not add ceremonial review stages beyond the existing workflow or repeatedly demand evidence already valid for the same scope. Do not weaken actual blocking prerequisites.

## 2. Invariants — no silent change to training

Verify and retain these executed-source identities, not only the counts:

| Component | ARC-Challenge | Original English LogiQA |
|---|---:|---:|
| Fitting blocks | 3 | 5 |
| Fitting groups | 192 | 320 |
| Shared same-source allocation probes | 24 | 40 |

All blocks remain 64 tasks. All 24 ARC probes serve each ARC block/agent branch; all 40 LogiQA probes serve each LogiQA branch. These are training-use probe labels, not prospective evaluation data.

Retain:
- S0: exact final epoch-2 `uniform_joint_sft` Q/L/M team, not an outcome-selected alternative.
- Qwen2.5-7B, Llama-3.1-8B, Mistral-7B native model/tokenizer/template and effective adapter identities.
- Pristine non-thinking Qwen3-8B readout R; pristine adapter-disabled Q attack generator.
- 24 temporary branches, 8 private-answer updates per branch, one paired assay rollout seed, fresh temporary optimizer and exact S0 rollback.
- Same frozen-R initial-private-bank and terminal scoring instruments, answer masks, raw/capped NLL contract, and cap 10.0 where inherited.
- Eight-row mean solver with tau=0.2 and balance=0.1: allocation weighting remains 3/8 ARC and 5/8 LogiQA, not equal-source.
- `terminal_block` primary; `uniform`, `source_family`, `private_bank`, and `shuffled` controls.
- Eight base updates per block/family plus 12 extra slots per block; 288 updates/team; all examples and optimizer ordering as specified.
- Joint integer allocation with row totals 12 and exact source/family margins, deterministic floor/ceil source-family redistribution, pre-frozen within-source 3/5 derangements, full-execution alias detection.
- Two continuation-training seeds; persistent per-family optimizer state; no checkpoint/seed selection after evaluation.
- One synchronous clean/exchange revision round and frozen readout; unchanged prompt templates, parser semantics, decoding, caps, dtypes and model roles.

Do not introduce new semantic specialties, uniform loss scaling in place of extra steps, more agents, judge/gate training, private-answer fallback, early/combined attacks, adaptive attacks, refreshed Stage III, or another benchmark sweep.

### Source-change invariance test

Replacing the future OpenBookQA cohort with GPQA, changing a Slurm job ID, or moving a file root must NOT silently change:
- ARC/LogiQA fitting/probe memberships or rendered task/option maps;
- S0, training-example order, batch sampling, temporary-update RNG, assay rollout seeds;
- solver tie breaks, source derangement, continuation-seed values or update-schedule rules.

Resolve and preserve any already frozen numeric seed manifest. Separate scientific RNG/dependency inputs from administrative child IDs, whole-portfolio hashes, evaluation-cohort filenames and scheduler metadata. Do not seed training or the assay from a whole plan hash that includes the replacement evaluation population. If the actual inherited contract couples these, report the exact conflict and its proposed correction; never claim unchanged methodology while silently reseeding an executed run.

A new authorization/plan binding is mandatory, but does not turn unchanged scientific inputs into different experiments. Explicit audited reuse may link truly identical requests across lineage; never silently migrate or relabel prior execution. The raw source, answer maps and evaluation task IDs DO belong in the identity of their own evaluation requests.

Implement a CPU fixture that swaps only the evaluation-source descriptor and scheduler metadata and confirms unchanged assay/training payloads and RNG values. Use the project's existing canonical serializers and identity implementation rather than introducing a parallel one.

## 3. GPQA source, access, and item identity

Use official `Idavidrein/gpqa`, config `gpqa_main`, backed by `gpqa_main.csv` according to the official card. Resolve the actual file/split layout at an immutable full revision. A library calling this a `train` split does not authorize using the selected cohort for fitting.

Reuse the existing reviewed GPQA loader and official source pin if they support Main. Do not assume a cached Diamond file contains Main or claim a new raw file was verified merely because the loader exists. If a revision change is necessary, make it an explicit source pin and reconcile identities across revisions before selecting anything. No mutable latest reference, arbitrary mirror, translated/converted cohort, or automatic Main/Extended/Diamond substitution.

The official card identifies CC BY 4.0 and an access commitment against revealing examples online. Reuse applicable existing access/terms evidence for the same dataset/account; do not invent human acceptance or require a new license ceremony where existing evidence suffices. Source availability and provenance are separate from access evidence. Missing access identifies a concrete prerequisite, not permission to bypass gating.

### Obtain real bytes without accidentally launching work

1. Prefer available authorized local or cluster-staged raw files; hash and parse them read-only.
2. If missing, implement/document an explicit user-invoked acquisition command for only necessary official files at the full pinned revision. Do not execute it during this task. Use the existing HF authentication mechanism without manually reading, printing, copying or logging secret values.
3. If files exist only remotely, provide the existing cluster-side CPU audit command; do not assert they were inspected locally.
4. Acquisition must not be an import/test/loader/worker side effect. No dataset-provided Python execution, trust_remote_code, arbitrary pickle, whole-repository downloads by default, or modification of shared cached files.
5. Use official HF metadata/download functions appropriate to the pinned installed version. A newly computed checksum proves content identity locally; it is not an independently recorded expected checksum unless such evidence exists.

### Reconcile Main, Diamond and previous use

Audit underlying item/content groups across Main, Diamond, relevant old revisions and other recorded project sources using the established reviewed grouping policy. Row indices, split names, and A/B/C/D letters alone are insufficient identifiers. Preserve both raw-byte hashes and normalized group provenance.

Exclude:
- both historical 32-task GPQA cohorts by their actual manifests, not by subtracting 64 from a public count;
- every still-protected/reserve group, including Diamond records that also occur in Main;
- historical integrity exclusions, previews/manual exposures/model uses under the existing policy;
- duplicate aliases and unresolved mappings that cannot satisfy freshness rules.

If two records share question/choices but disagree on the correct answer or relevant revision content, report a source conflict; do not merge inconsistent keys into a newly eligible record. Apply the existing Unicode/case and duplicate-option rules, not a permissive new normalization.

Do not assert `448 - 64` eligible items. Public total, known exposed, protected, invalid, duplicate, unresolved and currently eligible are distinct counts. Exclusions should be deduplicated in the accounting and reported with multi-reason metadata privately.

Mechanically importing/hashing an entire file is not automatically model or human exposure to every item. Conversely, a protected reservation does not become releasable because it was never generated. Apply the same existing policy consistently. Keep real question text out of the Codex conversation during the mechanical audit.

Audit original English LogiQA at its preserved official revision with CURRENT exclusions. The old 6,045 capacity bound is not a certification. Exclude fitting/probe/Stage I evaluation and other recorded uses and duplicate groups. Do not silently switch to LogiQA2 or a mirror.

## 4. Explicit label boundaries and deterministic options

GPQA stores a correct answer separately from distractors. The rendered order must follow the existing reviewed stable permutation, keyed by item identity and a fixed seed namespace. Do not present correct-first source order, reshuffle by model/policy/training seed, force answer balance, or reroll options after observing behavior.

Freeze exact display text, order and gold-label map before generation. Test field-role stripping and source-to-display-to-score round trips with synthetic records; labels may be multi-token for native tokenizers. Validate four nonempty distinct options without changing historical integrity rules. Do not include expert rationales, validation statistics, difficulty/domain fields, correctness tags or model-family hints in defender prompts.

Use separate data interfaces, not one source-row dictionary passed everywhere:
- **Source audit / evaluator record:** may read gold and metadata for mapping, overlap, validity and scoring only. It may not select items by model difficulty, success or desirable complementarity.
- **Defender input:** trusted question/options, allowed own/peer packets and frozen protocol fields; no gold/evaluator metadata, source answer-field names or target-correctness indicators.
- **Attacker input:** question/options, predeclared style and one assigned wrong displayed option. Offline selection may use the label to choose a wrong option; this is explicitly label-aware benchmark attack construction, NOT a fully label-blind threat. Do not pass the gold key, expert explanation, defender responses or success feedback. The target indirectly constrains the answer space; do not claim it conveys zero label-derived information.
- **Training / allocation processes:** fitting material and authorized ARC/LogiQA probe metadata only; no future GPQA/LogiQA evaluation task or label objects, not even for tuning learning rate, quotas, score caps or checkpoint choice.

The attack-target algorithm/seed is frozen before the assay. Actual evaluation targets/payloads are materialized only after policy schedules are frozen, through the existing isolated evaluator/attacker path. This removes the ambiguity in “no gold in generation”: defender leakage is forbidden; explicitly scoped wrong-target construction is allowed.

## 5. Freeze the cohort and analysis before exposing allocation probes

Require exactly 64 eligible GPQA Main groups and 64 eligible LogiQA groups. Prepare a candidate only from real bytes with verified source and exclusion evidence. Freeze revision, source files, identity rules, source-specific selection seed, hash ordering, option maps, cohort IDs, fresh-source embargo, analysis, attack recipe and request ceiling before any Stage II assay inference.

Use outcome-independent selection. GPQA domain composition can be reported descriptively, but do not introduce unreviewed quotas, choose by expert-validation score, test for a favorable rescue rate, or reroll for parser success. A real shortfall is a source-readiness failure; no protected release, dropped source, smaller population, new revision sweep, or automatic fallback dataset.

Static CPU preparation may inspect native tokenizer lengths using available staged tokenizer assets, without loading a model or contacting the hub. Check trusted question/options and fixed scaffolding under each relevant tokenizer. This does not establish full dynamic context fit: at runtime validate every actual rendered receiver/readout request, including cross-family tokenization of peer text and output reservation. Unexpected context overflow is an explicit compatibility blocker, not permission to truncate, salvage an answer, replace that task or enlarge caps. Inherit the current documented cap; do not silently set a new one.

Cohort and MethodSpec readiness do not require another independent human performance review. Use the existing explicit plan-review/seal mechanism; do not create an execution-approved plan automatically or fabricate an approval signature. Distinguish candidate construction, review/freeze and executable authorization.

Prospective evaluation is **project-filtered GPQA-Main science transfer + new within-source LogiQA generalization**. It is not the old ARC population, full GPQA, Diamond, proof against pretraining contamination, or final confirmation. Report whether remaining eligible/selected Main records are non-Diamond; an intentionally filtered subset may not reflect the published full benchmark.

Do not require a positive baseline accuracy or minimum number of rescue opportunities on the new cohort. These are diagnostic findings to report, not selection gates. Sixty-four questions per source may give wide intervals. This amendment neither promises power for small improvements nor authorizes outcome-triggered expansion.

## 6. Explicit prospective comparisons

Preserve `terminal_block` as primary and controls as declared; no best-method/seed selection. Define the main contrast against control j from both continuation seeds on identical task groups.

For source s and condition c with eligible task set E[s,c]:

    d[s,c,x] = 0.5 * sum over k in {1,2} (Y[terminal,k,c,x] - Y[j,k,c,x])
    D[s,c]   = mean over x in E[s,c] d[s,c,x]
    D[c]     = 0.5 * (D[GPQA,c] + D[LogiQA,c])

For clean, E has all 64 planned tasks per source once inference is complete. For exchange, E is the shared accepted one-attempt attack set defined independently of defender success. Do not pool by accepted-call counts: unequal acceptance must not silently alter the 50/50 source weighting.

Show both seed-specific comparisons and their fixed mean, every policy, unchanged S0, per-source results, clean utility and costs. S0 is one unchanged team, not two independent baseline replicates. A repeated S0 term in paired calculations does not create new samples.

Use the inherited source-stratified task/group bootstrap, keeping all arms, seeds and clean/attacked outcomes for a task together. If a bootstrap recipe or comparison setting was never frozen, expose that missing field before real execution instead of choosing after results. Two seeds share S0 and allocation estimation; intervals do not cover all training/probe-generation uncertainty. Preserve the exploratory interpretation and existing descriptive clean-utility tolerance; no unreviewed hypothesis-test threshold or risk certificate.

A pooled gain cannot be reported as a gain on both sources. Negative or floor-level GPQA results stay in the report. The private-bank control and terminal score differ in communication/attack context as declared; their contrast is not by itself a complete causal mediation result. No claim of semantic specialization from eight arbitrary fitting blocks, adaptive robustness, or refreshed full PACT.

### Missingness and failure rules

- An actually generated malformed/truncated/abstaining answer is a strict model failure under the inherited contract.
- Rejected attack generation means an unavailable exchange intervention, not a success, clean copy or unfinished defender response.
- An unresolved dispatch, missing checkpoint or context incompatibility is technical incompleteness, not a wrong neural answer.
- Do not define the primary accepted-attack population using which policies completed or were correct. Complete required calls or label the primary contrast incomplete; any common-completion description is explicitly secondary with full-cohort accounting.
- Report accepted/source counts and intended-population paired bounds. For each missing task, an unknown correctness difference lies in [-1,1]; use the tighter valid partial evidence when available. Do not fabricate point estimates.
- If either source has no accepted attacks, the two-source exchange endpoint is undefined. Report the supported single-source result separately without substituting a new primary endpoint.

Natural receiver hold/repair strata can differ across policies; retain denominators and do not call those an identical-context mechanism test. Do not add new fixed-history generation in this source amendment.

## 7. Slurm: reuse the deployment, preserve experimental identity

The user has already migrated to Slurm. Inspect and reuse the actual partition/account/QoS, resource profiles, container/runtime, staged models/tokenizers, persistent private roots, job-local scratch, checkpoint receipts and tested launchers. Do not ask for known settings or infer them from unrelated projects. List only genuinely missing values.

Workflow: local code/CPU tests -> user review/push -> pinned cluster checkout -> explicit user submission of bounded authorized stages -> restricted artifacts and sanitized/local audit return. No active Colab notebooks, Drive mounts, `/content` dependencies, runtime pip upgrades or forced migration of already verified checkpoint copies. Preserve old Colab history.

Only implement missing thin wrappers around the existing package. Source import/audit, candidate freeze, future preflight, assay smoke, assay segments/scoring, policy schedule freeze, continuation training, policy smoke/evaluation, and reporting remain separate invocations with export/stop. Do not auto-submit a dependency chain across approval boundaries. `afterok` is scheduler ordering, not an authorization receipt or scientific completeness check.

Use the existing one-GPU/one-resident-backbone contract, serial state-mutating jobs by default, immutable S0 and isolated branch/policy/seed roots. Independent arrays may run only where already permitted and with protected shared counters; never parallelize updates of the same optimizer stream. Native template, dtype, attention, numeric seeds, dropout/eval mode and adapter activation must follow verified model contracts. A Slurm migration is not permission to change numerical behavior silently.

**Requeue protection is application-level:** a Slurm job can restart its batch script from the beginning with the same scheduler ID. On every launch/requeue, resolve the pinned plan/commit/role, validate durable journals and load the exact committed model/optimizer/RNG/sampler state where applicable. Never use scheduler job ID, array index alone, hostname or wall-clock time as scientific RNG/request identity. Unknown physical attempts remain accounted and unresolved; they are not an automatic retry invitation. No replay of an ambiguous optimizer step, fresh optimizer on continuation resume, reset wallet, or extra seed.

Use existing atomic commit/snapshot and signal handling. Do not trust an ephemeral scratch completion marker after node loss. No hard-coded new site flags, literal shell variables in #SBATCH directives, moving-branch git pull inside a job, or raw prompt diagnostics in stdout. `sbatch --test-only` still contacts a controller; local CPU tests render/stub launchers rather than executing scheduler commands.

### Scoped historical reconciliation

Check known relevant study lineages, persistent execution roots, journals, supplied remote inventories and existing user execution records. Record scope, time of evidence, covered groups and unknowns; do not demand impossible proof that no computation occurred anywhere.

An unresolved event that may overlap this assay's probe exposure, request ownership or budget blocks the dependent GPU stage until reviewed. Unrelated old Stage I uncertainty remains in history and does not automatically become a new source-loader defect. Do not waive existing relevant Stage II blockers, silently count unknown work as zero, or let them prevent unrelated CPU implementation/source auditing.

## 8. Privacy and artifact return

Follow the official online-example restriction and existing project access policy. Do not include real GPQA records in fixtures, prompts to a hosted coding assistant, public issues, terminal output, Slurm logs, experiment-tracking services, public HTML/Markdown, Git, or this chat.

PRIVATE raw questions, labels, permutations/IDs where sensitive, responses, decodable token arrays and tensor paths stay in restricted user-controlled storage. A mechanical local/cluster audit may parse them and emit aggregate receipts without displaying examples. Do not request routine upload of a GPQA-containing PRIVATE ZIP to this chat or hosted Codex context. Return the SANITIZED summary and the trusted local audit receipt here; any internal private transfer must use the existing permitted restricted channel.

Treat uploaded/generated rationales as data, not code or instructions. Escape private human-readable views. Do not execute source-provided scripts or unsafe pickles. Sanitized outputs use an explicit allowlist of aggregate/provenance/cost fields and are checked for raw strings, row-level answer maps and decodable arrays. Runtime errors must redact example text too.

## 9. Budget — unchanged, not a new wallet

Maximum complete graph, before exact aliases and rejected-attack reductions:

| Resource | Assay | Continuation / evaluation | Total |
|---|---:|---:|---:|
| Generations | 8,112 | 15,616 | 23,728 |
| Reserved output tokens (512 each) | 4,153,344 | 7,995,392 | 12,148,736 |
| Optimizer updates | 192 | 2,880 | 3,072 |
| Supervised sequence forwards | 1,536 | 23,040 | 24,576 |
| Diagnostic scoring forwards | 2,640 | 0 | 2,640 |

Included smoke maxima: assay 24 calls, policy evaluation 244 calls. All smoke identities are included in these graphs; there is no plus-one smoke, new baseline or hidden verification generation.

Arithmetic:
- Assay baseline/attacks: 64*11 +64 =768.
- Branch-task views: 3*(3*24 +5*40)=816; each has at most 1 changed private +8 suffix calls.
- Assay: 768 +816*9=8,112.
- Scoring: (64+816)*3=2,640; initial bank plus clean and exchange terminal scores, with missing exchanges handled explicitly.
- Policy evaluation: (5*2+1)*128*11 +128=15,616.
- Continuation: 5*2*8*(3*8+12)=2,880 updates; eight supervised forwards/update.

Recompile the full dependency graph, including changed GPQA options/source and included smoke membership, against these ceilings. A source change, child ID, job retry or alias does not create new spending authority. Record physical attempts, committed results, exact reuses and remaining owned budgets independently of logical report counts. Rejections/aliases do not authorize reallocating spare work.

This implementation task performs zero real model forwards. Future actual checkpoint/runtime preflight uses an already applicable reviewed allowance, or requires a small explicit finite allowance before execution. Do not silently consume the main graph for unplanned preflight or ban necessary verification while claiming GPU readiness.

Equal total steps are not equal training tokens, FLOPs or GPU time across backbones. Preserve per-family exposure/cost accounting and the estimator overhead; this is not an efficiency guarantee.

## 10. Deliver actual code, tests, and a short runbook

Do not build a new framework or recreate already implemented allocation mathematics. Reuse loaders, serializers, prompts, strict scorer, split ledger, constraints, journals, receipts, Slurm profiles and exporters. Finish the source-amendment path even if real source acquisition or a separate execution review is pending.

Required focused CPU/mock tests (plus relevant existing tests):
1. Invariant fitting/probe IDs and seeds under evaluation-source substitution and scheduler/plan administrative changes.
2. Immutable source revision/file mapping; actual/cached/missing states; no hidden network/model/scheduler calls.
3. Cross-Main/Diamond/revision matching; protected, exposed, integrity and unknown-mapping exclusions; conflicting gold keys not silently merged.
4. Stable option permutation and source-role stripping; question/choices are allowed, gold/metadata are not defender fields; label-aware wrong targets handled only by the isolated attack-preparation interface.
5. Real 64+64 eligibility versus fixture-only implementation; candidate IDs/analysis frozen before assay; future evaluation data denied to fitting/assignment interfaces.
6. Native tokenizer static checks and runtime full-context checking without truncation or task replacement.
7. Inherited five policies, integer margins, 3/5 shuffle, source weighting, aliases and exact temporary rollback unchanged.
8. Seed-mean and source-equal paired metrics under unequal attack acceptance; S0 not counted as repeated samples; missing/invalid/undefined endpoints distinct.
9. Rendered Slurm scripts and pinned paths, no Colab dependencies, resume from durable state, single writer, signal/requeue simulation, no silent extra attempts/optimizer steps.
10. Exact graph and included smoke arithmetic, prior consumption and no automatic budget resets.
11. GPQA privacy including logs/errors/export allowlists; no real examples in tests or assistant handoff.
12. Full synthetic import -> overlap audit -> candidate -> proposed graph -> mocked assay/policy reports -> sanitized export -> local reconstruction.

Use synthetic fixture questions only. A tiny randomly initialized local model can test mechanics but is not pretrained/GPU evidence. No actual Slurm controller contact even for test-only submission.

Final response from Codex must include:
- files changed, test commands and actual passes/failures/skips;
- contract differences and explicit unchanged-method regression test results;
- actual source/access/revision/hash/exclusion evidence, or precise missing inputs; no invented availability;
- whether a real candidate exists, whether it is frozen, and whether execution is authorized, as separate fields;
- exact already-supported local/cluster CPU and Slurm commands, not guessed flags/paths;
- relevant historical-consumption and checkpoint/runtime blockers with finite scope;
- original, spent and remaining budget ownership;
- sanitized return requirements and restricted PRIVATE storage location;
- one shortest next user action supported by the actual readiness state.

Do not stop with another design memo. Implement the minimal complete GPQA/LogiQA amendment and Slurm wrappers without launching acquisition, model work, jobs or changing completed records.

## Reference documentation checked during this planning review

Metadata/documentation only; no benchmark rows were accessed in this review. These links are not immutable dataset pins or execution approval.

- Official GPQA card: `https://huggingface.co/datasets/Idavidrein/gpqa/blob/main/README.md`
- Pinned-file downloads: `https://huggingface.co/docs/huggingface_hub/en/guides/download`
- Dataset gating: `https://huggingface.co/docs/hub/en/datasets-gated`
- Slurm sbatch, including requeue and directive behavior: `https://slurm.schedmd.com/sbatch.html`
