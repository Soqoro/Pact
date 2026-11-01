# PACT Stage II — crossed update probes and prospective allocation validation

Prepared 27 October 2026. Design revision: `stage2-allocation-reviewed-v2`.
Status: revised implementation specification and proposed bounded experiments; NOT an executed study, repository patch, or authorization for automatic GPU work.

This supersedes the preceding next-phase PLANNING recommendation. It does not amend a completed run, rewrite Stage I results, or spend an old budget. The original Stage II proposal was unexecuted according to the supplied audit. If repository evidence instead shows execution has started, preserve it and report the conflict before using this replacement design.

## 1. Mission and the actual claim being tested

Update the EXISTING PACT repository. Implement a complete, bounded experiment asking whether downstream measurements of actual short agent updates produce a useful allocation of further private-capability training. Keep the three heterogeneous communicating agents and the frozen readout. Do not return to checker/gate training, add a frontier judge, or implement another framework.

Read AGENTS.md, Git status, the original proposal, heterogeneous-training revival specification, executed Stage I training/evaluation plans and amendments, checkpoint-verification receipts, exposure ledger, real CLI/backend, and tests. Preserve unrelated changes and all completed/stopped/incomplete history.

Implement three separately invoked parts:
A. Read-only Stage I synthesis using existing evidence; zero model calls.
B. Crossed prospective update assay with actual temporary adapter updates and rollback.
C. Matched continuation-policy experiment on a fresh common evaluation population.

This is one static allocation-learning experiment. It is NOT full PACT, a two-round coupling test, an adaptive defense evaluation, or a final benchmark confirmation. Stage III remains deferred. Positive Stage I peer-access significance is not a prerequisite to investigate allocation; absence of that significance is not proof of no effect. Stage II cannot retroactively establish the Stage I mechanism.

Only local CPU/mock/tiny locally initialized neural tests may run during Codex implementation. The user reviews/pushes and explicitly invokes pinned GPU stages in the existing single-GPU Colab/AAI workflow. Do not start jobs, access credentials, accept model licenses, download pretrained weights locally, commit, push, change remotes, clean up recovery data, or migrate dependencies merely to latest versions.

## 2. Preserve evidence and resolve actual contracts

Supplied completed Stage I evaluation:
- run: `pact-revival-stage1-evaluation-amended-002`
- PRIVATE SHA256: `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`
- SANITIZED SHA256: `1c4474a57bb28bd228040a32c496b6426e21531112e493b06be47dca0741047a`
- recorded 13,467 committed calls; zero unresolved new attempts; fixed history complete.
- Joint-minus-independent peer-access interactions: clean +2.08 pp (interval -5.73,+9.38); accepted exchange +5.67 pp (-1.60,+13.83). These do not establish positive additional peer utilization.
- The supplied synthesis does not include the entire on-policy attacked source-results table. Reconstruct it if current artifacts contain the evidence; do not infer it from the clean +5.98 pp finding.
- Prior source ZIP is unavailable locally for a new cross-archive byte comparison. Preserve that limitation.

Starting snapshot S0: the SAME fixed final epoch-2 `uniform_joint_sft` Q/L/M team, not whichever arm or checkpoint looks best. Bind actual final tensor hashes, per-family native model revisions, tokenizer/templates, precision policy, and parent lineage from the verified serving receipts. Historical unknown work, including replacement-002 step 94 and later unknown generation history, remains separate and unknown. Do not replay, certify, or retroactively zero it.

Expected families remain Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3; R is pristine non-thinking Qwen3-8B. The pristine Q attack generator must never carry the trained Q adapter. Use actual executed contracts over obsolete prose defaults and report material conflicts.

The new plans must enumerate differences from old proposed Stage II: shared within-source probes; one paired rollout seed; added common-reader private-bank scores; executable slot allocation; separate prospective policy evaluation; new budgets. Never alter an old manifest in place.

Candidate new IDs, subject to collision checks: `pact-update-allocation-crossed-002` and `pact-allocation-policy-evaluation-001`. These are proposed names, not assertions that CLI entries or artifact paths already exist.

## 3. Data boundaries: freeze before outcomes

Retain the existing 512 fitting groups and eight immutable 64-task blocks (four ARC, four original English LogiQA). Do not recluster them using results. These are arbitrary source-stratified training blocks, not asserted semantic specialties.

Retain all 64 originally locked allocation-probe groups, 32 per source, after confirming they have not already been consumed in another experiment. Explicitly unlock ONLY for this approved new assay. Their labels influence allocation and therefore are TRAINING-USE meta-data, not test data. No direct training loss or optimizer update may use probe tokens or labels.

Replace old one-block/eight-probe matching with a crossed design:
- Every ARC training block/agent branch is scored on the SAME 32 ARC probes.
- Every LogiQA training block/agent branch is scored on the SAME 32 LogiQA probes.
- Use one prespecified paired generation seed, not two draws on eight different questions.
- The 64 probe groups remain 64 independent sampling groups; branch evaluations are correlated repeated measurements.

Before seeing any probe outputs, freeze 128 new prospective evaluation groups: 64 per source from the authorized original training sources. Exclude all recorded prior exposures, fit/probe/Stage I validation/source-evaluation groups, protected final-test allocations, lexical/content duplicates and cross-source groups under the reviewed policy. Do not silently relax exclusions or substitute benchmark test material if quotas fail. Report actual availability first. Implement using fixtures even if a real source shortage blocks execution.

The new 128 groups are prospective source-domain development evaluation, not a final-test set. Seal their labels and task contents from training/allocation selection until policies, hyperparameters, checkpoints and analysis rules are frozen. Loading canonical source rows for split validation does not authorize generation or policy selection on them. The evaluator may access them for its later scoring and the declared offline attack-target selection. No validation pilot that can modify the scientific method is taken from these tasks.

Use seed 20261027 with fixed stage namespaces, probe-update seed 17, probe rollout seed 29, continuation seeds 113 and 227, evaluation rollout seed 31. Derive node seeds through the existing stable hash scheme; no mutable stream whose call order changes the comparison. Freeze block permutations and shuffle controls before model outcomes. These are proposed choices, not optimal hyperparameters.

## 4. Part A: finite read-only synthesis, not another search for a favorable story

Reconstruct from current committed Stage I evidence:
- final clean and attacked on-policy outcomes for frozen/independent/joint, source separated;
- private accuracy and coverage, revised coverage, erasure, construction, readout loss;
- common-history HOLD/REPAIR transitions and all four peer-access accuracies;
- strict format/abstention transitions and accepted-attack missingness.

Distinguish on-policy task results from off-policy receiver diagnostics and task clusters from receiver/call counts. Reproduce the original summary before adding derived tables. Treat the analysis as retrospective descriptive decomposition, not mediation or new confirmation. Keep independent semantic annotation deferred.

No new models, fitting, forward scoring, or generation for Part A. Missing underlying records must be marked, not reconstructed from invented per-task outcomes. Part A may block on integrity/contract failures, not on disappointing valid scientific results, and cannot choose a different S0.

## 5. Part B: temporary-update intervention

For each of eight blocks B and each family i:
1. Restore exactly S0, including the saved adapter values, and clear previous temporary adapters/optimizer state.
2. Create a temporary adapter copy; fresh AdamW state. Use original Stage II private-answer objective, eight task groups/update, eight updates over all 64 fitting tasks, fixed LR 5e-5 without warmup, zero weight decay, existing Adam betas/epsilon and clip contract unless an executed compatible amendment specifies otherwise. Resolve discrepancies before freezing. No receiver loss or reference-model changes.
3. Generate changed-family private packets on all 32 same-source probes. Reuse only the other two families' exact S0 private requests.
4. For clean and accepted exchange conditions, regenerate ALL three receiver revisions and R. The changed adapter affects private AND revision turns; the effect is not pure private-capability mediation.
5. Store outputs, exact model/prompt/seed dependencies, scoring inputs and physical costs.
6. Restore S0 effective parameter hashes before the next branch. Temporary optimizer/weights must never become a policy continuation checkpoint.

Thus 24 temporary fits, 192 optimizer updates, 1,536 gradient-bearing sequence forwards. Each branch uses one fixed training RNG stream; later continuation seeds do not replicate this credit-estimation experiment. Record that limitation.

Base probe bank: 64 tasks, three private answers, two sets of three revisions, two readouts = 704 generation calls maximum. One fixed exchange payload per task = 64 maximum attack attempts. Each temporary branch needs 32*(one changed private + two conditions*(three revisions+one R)) =288 calls. All branches:6,912. Assay maximum:7,680 generations.

No early attack, new DPO pairs, correct-answer donor generation, forced disagreement, or extra sampling after a flat result. Fitting labels supply temporary-update gradients, even when natural candidates are all wrong. Probe labels score outcomes only.

## 6. Scoring: comparable instruments, not mismatched surrogate units

Use answer-prefix NLL from the SAME pristine R with its inherited answer-first contract. Score only answer-bearing tokens with native boundary/masking checks. No gold-bearing user prompt, no generated explanation conditioning the answer score, and no inference-adapter update. The score is a teacher-forced diagnostic, not generated correctness or a verified rationale.

Store raw answer-token mean NLL and a prospectively capped score ell=min(raw_NLL,10.0) nats. This fixed cap limits domination by one extreme loss; do not choose it from results or present it as optimal. No batch standardization, min-max scaling, z-score amplification or per-family rescaling. Nonfinite loss is a technical scoring failure, not something to clip silently.

Terminal score for branch B,i:
D[B,i] = 0.5*mean_clean(ell_R(S0)-ell_R(branch))
       + 0.5*mean_accepted_exchange(ell_R(S0)-ell_R(branch)).

Use common task/attack support across all branches of a source. The attack mean uses accepted source probes, with its denominator explicit. Both terms must exist for a usable terminal score. If a source has zero accepted attacks, do not silently turn the method into clean-only allocation; report the prerequisite and uniform unsupported rows if the frozen analysis contract permits partial execution. Missing infrastructure/scoring cannot be treated as a scientific zero or used to select favorable support.

Add a matched precommunication comparator:
P[B,i] = mean_same_probes(ell_R(x, initial private bank at S0)
                        -ell_R(x, initial private bank after updating i)).

Use R's SAME packet-input renderer/answer-prefix target contract, substituting initial private packets for revised packets; no new R generation. This scorer sees the uncorrupted initial bank and has no exchange channel. Keep invalid private packets' unchanged public unavailable envelopes. It measures precommunication ensemble informativeness, not the updated model's own calibrated knowledge. There is no longer an apples-to-oranges policy comparison using binary own-agent accuracy versus terminal NLL or different models' raw NLL.

Terminal scores: (64+24*32)*2=1,664 maximum forwards.
Private-bank scores:64+24*32=832 maximum forwards.
Total diagnostic scoring forwards:2,496. Actual generated private correctness remains a secondary descriptive measure without extra calls.

Compare D_clean to P as a descriptive communication-related contrast; D includes both communication and attack effects. Beating the P-derived policy is not proof of a particular causal receiver mechanism.

The isolated eight-step update is a surrogate for a longer interleaved continuation. Do not sum branch credits to predict final policy accuracy: simultaneous agent updates and persistent-optimizer histories can interact. That mismatch is tested by the prospective whole-policy experiment, not assumed away.

Strict invalid/abstaining final packets remain task failures even when their prompt's gold NLL is low. Never filter them from generated-accuracy evaluation. Score original unmodified source/runtime contracts; an incompatible prompt is a technical stop, not permission to truncate or change wording.

## 7. From credits to an ACTIONABLE training allocation

### Do not rely solely on multiplying losses

A constant positive scale applied to all gradients of one separately optimized adapter can largely cancel under Adam's first/second-moment normalization (exact under simplified conditions, not generally with epsilon/clipping/time-varying gradients). Mixed-example weighting can still matter; the problem is assuming every apparent responsibility change produces the intended optimization change. Use explicit training-slot scheduling here instead.

For either D or P solve the existing small soft balanced problem, with fixed tau=.2 and balance=.1:
min_r mean_B sum_i[-r_Bi*s_Bi + .2*r_Bi*log(r_Bi)]
      + .1*KL(mean_B r_B || uniform3),
subject to r_Bi>=0 and row sum1. Missing rows remain declared unsupported with uniform fallback rather than zero measured credits. Test convex objective/gradients, convergence, equal-row-score invariance and uniform behavior. No tuning these constants on validation, probes, or prospective evaluation.

Convert each supported row to EXACTLY 12 extra optimizer slots using deterministic largest-remainder rounding of 12*r_Bi. Hash tie-breaks are fixed before scores. Quantization is intentional: tiny differences may yield equal quotas. No normalization or search to force asymmetry. Unsupported rows use 4/4/4 and retain unsupported status.

Let e[B,i] be these integer quotas. For each trained policy continuation:
- Base supervision: every family gets all64 fitting examples in EACH block once =8 updates/block/family. Thus192 base updates/team.
- Allocated extra supervision: exactly12 extra updates/block across families =96 extra updates/team.
- Each update contains eight fitting examples; actual loss has ordinary unit-weight task mean.
- Total:288 optimizer updates and2,304 supervised forwards/team; at least64 updates/family, at most160/family. This REPLACES the old one-extra-epoch/192-step continuation proposal.

Precompile the complete per-family batch schedules. Interleave base and extra slots using a fixed data-independent global schedule rather than choosing the order from outcomes. Ensure each mandatory base example is seen once. For an agent's extra slots in a block, draw deterministic shuffled eight-example batches, without replacement within each64-example cycle and with explicitly recorded repeat cycles if necessary. All policies share base permutations, extra-pool permutations and RNG namespaces within a seed; only quota assignment changes exposure. No mean-loss renormalization that converts different slot schedules back to equal exposure.

Use one persistent fresh AdamW optimizer per family/policy/continuation seed, not a fresh optimizer for every block. Learning rate fixed5e-5 with no continuation warmup, all other compatible settings inherited. No gradients on probe/evaluation records. Inference adapters may be loaded one backbone at a time; reorder execution only when compiled per-family training order and RNG identity are preserved. Terminal evaluation waits for all three policy adapters.

## 8. Five prespecified policies and their controls

Primary: `terminal_block` (D-derived quotas). Comparators:
1. `uniform`: e=4 for every block/family.
2. `source_family`: preserve EXACT source-by-family column totals of terminal_block, distribute them as evenly as possible across that source's four blocks. Every row still sums12. For each family entries are floor(column_total/4) or ceil(...). Choose a feasible balanced matrix using a prespecified hash tie-break independent of task/credit outcomes beyond those column totals. No block-specific score information enters this redistribution.
3. `private_bank`: P-derived quotas, SAME loss scale, solver, rounding and slot budget.
4. `shuffled`: apply one frozen within-source block derangement to terminal_block quota ROWS. Preserve family/source totals. Freeze the permutation before scores; never try many permutations to obtain a weak comparator.

Also evaluate unchanged S0.

Train all five policies from S0 with continuation seeds113 and227. Do not reuse temporary branch weights or choose the best continuation seed. Policy selection is fixed: terminal_block remains primary, even if another wins.

Controls are source-stratified because ARC/LogiQA differences could otherwise masquerade as block-level specialization. Blocks are arbitrary; a win is block-dependent allocation efficacy, not evidence of named semantic experts.

Before any continuation/evaluation, detect EXACT identity of full schedules plus initialization/RNG/prompt contracts. Identical policies under a seed are aliases and should be executed once, with shared evidence and declared zero contrast. Equality of quotas alone is insufficient if complete schedules differ. Do not force a new permutation or increase update budget merely to create different arms. Skips do not replenish wallets.

Freeze policy matrices, integer quotas, optimizer schedules, checkpoint IDs and analysis spec before unsealing the prospective evaluation. CPU leave-one-probe-out quota stability reports may be exported, but cannot select a different matrix/hyperparameter. No best-probe or best-validation policy.

## 9. Fresh common policy evaluation

128 new fixed groups; all five policies x two continuation seeds plus S0 =11 possible distinct teams. Each task/team uses three natural private calls and clean/exchange continuations, maximum11 calls. Use one paired evaluation rollout seed by task/node across checkpoints; different training seeds are different teams, not fresh independent task samples. S0 is generated once, not duplicated for each policy seed.

All policies share the exact fixed attack pool on these tasks. Allow one attempt/task from pristine Q with offline chosen wrong target and predetermined consensus/independence style allocation and sender. Acquire/freeze the pool after policy lock but before victim outputs. Do not expose actual team outputs to the generator. Rejections are missing attacked conditions, never defended successes. No retries or additional attacks after seeing results.

Retain the executed one-synchronous-exchange protocol, output contract,512 max output tokens,8192 total recipient context, native decode settings, frozen R and trained-adapter activation/precision. Sender's private state stays immutable; corrupt outgoing packet is delivered to both other receivers, never to sender; no revised-message chaining; readout sees revisions only. No new parser, anchor fallback, archive, or stronger judge.

All new data is evaluated once per specified dependency. Missing infrastructure is incomplete, not a failed model packet. Invalid/abstention/length failures remain failures. There is no oracle restriction to rescue opportunities. Report support counts and accepted-attack population separately from all128 intended groups.

Evaluate a newly trained team only after all three final adapters validate. Do not quietly replace an unsuccessful family with S0. Preserve all checkpoint/model identities in the result table.

## 10. Endpoints, uncertainty and decision rules

Primary comparisons on attacked final generated correctness:
- terminal_block minus uniform;
- terminal_block minus source_family.

Report clean differences for the same comparisons and all arms, including S0. Clean tolerance of2pp is a descriptive prespecified utility target, not a certified bound. Local/private-bank and shuffled differences are secondary mechanism tests. A gain vs uniform alone does not establish communication-aware, task-specific specialization.

Use equal source weights; under accepted attacks first average tasks within each source, then sources. For point estimates average both continuation seeds. Report each seed's effect separately. Preserve paired task/condition/model/seed rows and predeclare10,000 source-stratified task-cluster bootstrap replicates. Do not resample receiver cells or seed-task rows as independent. Report95% descriptive intervals and97.5% per-comparison intervals for the two primary contrasts as a Bonferroni-style multiplicity caution, not a finite-sample guarantee. If a source has no accepted attacks, the equal-source attacked target is undefined; do not replace it by the other source.

This experiment conditions on one historical Stage I seed/snapshot, one assignment-estimation training stream and one probe-generation stream. Two continuation seeds do not measure variability of the entire training pipeline. Small panels may leave modest effects unresolved; no claim of equivalence from intervals crossing zero and no sequentially extending evaluation until favorable.

Report also private accuracy, initial coverage/gain over best family, revised coverage, erasure, repair, harmful revision, final construction/readout loss, strict validity and actual input/output/training costs. Natural hold/repair cohorts change with model outputs, so their conditional percentages are descriptive, not automatically matched mechanisms. A decrease in erasure or NLL is not proof of useful final correction.

Interpretation ladder:
- Flat/equal scores and identical schedules: allocation distinction unsupported at this resolution.
- Gains over uniform only: could be source-family budget redistribution.
- source_family matches terminal_block: no demonstrated fine block-level allocation need.
- private_bank matches terminal_block: downstream scoring not shown necessary under these controls.
- shuffled matches terminal_block: block correspondence not shown useful.
- Positive attacked effects plus acceptable clean behavior and convincing controls: supports this static allocation component only.
- Wide/inconsistent effects: inconclusive, not permission to tune the evaluated run.

Uniform does not need probe collection in deployment. Report full incremental assay cost attributable to allocation, and distinguish matched continuation-budget comparisons from practical cost-efficiency. Equal optimizer steps/example counts are NOT equal FLOPs/tokens across families. No claim that this beats strong collective RL or that any fixed attack pool provides adaptive robustness.

## 11. Exact new ceilings and safe execution

These wallets are NEW proposed limits, not recycled Stage I unused calls.

Part B:
-64 attack attempts +64*11 base trajectories +24*32*9 update trajectories =7,680 generations.
-192 temporary updates;1,536 training forwards.
-1,664 terminal +832 private-bank scoring forwards =2,496 diagnostic forwards.

Part C:
-128 attack attempts +128*11 teams*11 generations =15,616 generations.
-5 policies*2 seeds*288 =2,880 continuation optimizer updates;23,040 training forwards.

Portfolio maximum:
-23,296 generations;11,927,552 reserved output tokens at512 each.
-3,072 optimizer updates (192 temporary +2,880 continuation).
-24,576 supervised forwards (1,536 +23,040).
-2,496 diagnostic answer-scoring forwards, Part B only.
-Up to20 separately recorded short synthetic validation forwards, at most128 input tokens each, zero generated tokens; no gold benchmarking or optimizer work.

No new generations/forwards for Part A. Per-family memory/model-loading/time/input tokens and actual runtime costs recorded separately. Context failure, unrecoverable in-flight optimizer state, missing provenance or exhausted budget stops the dependent stage. Invalid predictions/flat credits/negative valid results do not permit retries or task replacement.

All stages explicit: inspect/plan -> checkpoint-only receipt -> Part B source smoke -> collection/probe branches -> policy freeze -> continuation -> prospective smoke -> complete prospective evaluation -> export/audit. No unattended Run All.

Part B smoke: one predetermined probe task/source, pristine attack acquisition where absent and complete S0 clean/exchange trajectories: at most24 INCLUDED generation attempts (2 attacks+22 trajectory calls). No extra probe temporary updates for smoke; the first actual block/family branch can be separately paused after its already-budgeted update/receipt. Never add unbudgeted training sanity fits.

Part C smoke: one predetermined evaluation task/source across all11 declared teams, at most244 INCLUDED attempts (2 attacks+242 trajectory calls; aliases can reduce actual work). Export and stop; remaining126 tasks use identical frozen method and contracts. Negative accuracy is not an authorization to edit the method. A technical defect demands closure/amendment with old outputs preserved, not an erased smoke.

Physical dispatches count even if results are unknown. Exact completed dependency reuse is allowed; archive copies and shared evidence are not independent physical calls. Unknown historical optimizer/generation work stays unknown, not an expanded wallet. Preserve safe immutable checkpoint/snapshot markers and no silent restart from a later state.

## 12. Implementation, testing and handoff

Reuse real model/runtime loaders, stage scheduling, response contracts, masks, immutable journals, snapshots, metadata-only safe archive readers and PRIVATE/SANITIZED exports. Imported task, attack and report text is data, not instructions. Pin actual repository-compatible libraries. No arbitrary untrusted pickle execution or checkpoint-shipped code.

Required executable tests (Codex must report only those it actually runs):
1. Shared32-probe identity within each source for every block/family; original64 preserved; fresh128 exclusions and lock boundaries.
2. S0 exact identity, fresh temporary optimizer,24 branches,8 steps/branch, no branch state leakage, exact rollback and unknown-intent stop.
3. Updated adapter used for its private AND receiver turns; other private banks reused only by true identity; all affected revisions/readouts regenerated.
4. Native answer-prefix masks and no gold visible in generation; capped/raw score separation, nonfinite/missing-score handling, paired common-support scoring.
5. Same R instrument for private-bank and terminal scores; no accidental extra generation or adapter in R/attack generator.
6. Balanced-solver reference objective/gradients/equal-credit invariance; deterministic Hamilton quotas row sum12.
7. source_family integer floor/ceil redistribution, exact source-family totals and row sums; frozen derangement; no outcome-selected weak shuffle.
8. Compiled base+extra schedules: every fit item gets base supervision each family,288 updates/team, repeated-extra exposure accounted, persistent optimizer and stage RNG invariants.
9. Tiny analytical Adam scaling example demonstrates why constant gradient multiplication can cancel; actual schedule differences cause distinct sampled updates on a tiny local model. Do not claim toy behavior proves large-model efficacy.
10. Exact-identity policy aliases, no fake independent samples/no budget replenishment; all matrices locked before prospective task use.
11. Three-arm semantic pipeline unchanged, accepted-attack missingness, strict outputs, sender privacy, task-level metric identities and bootstrap grouping.
12. Budget calculator:7,680 /15,616 /23,296;192 /2,880 updates;2,496 scoring forwards; included smoke accounting and physical-attempt ownership.
13. Full mock path: existing-result import -> crossed collection -> one real tiny adapter update/restore -> scores -> five policies -> schedule compilation -> mocked continuation/eval -> reports -> export/reimport.
14. Actual CLI/notebook dispatch is offline by default; all later stages require frozen child-plan binding and explicit user invocation; no Stage III launch or old-run cleanup.

Deliver code for BOTH Part B and Part C, not just metadata stubs, even if actual data/model access is absent. Use fixtures and identify precise real execution prerequisites. Do not interpret scientific uncertainty as an implementation blocker.

Outputs: source/lineage resolution, selected IDs and exposure receipts, all natural sources/attacks, branch checkpoints and update logs, rollback receipts, task-level raw/capped score arrays, support/stability summaries, policy matrices and integer quotas, immutable training schedules, per-family final adapters, primary/secondary result tables with uncertainty, distinct physical/logical cost accounting, PRIVATE/SANITIZED bundles and reproducible CPU audits.

Finish with changed files; tests actually executed including skips/errors; exact existing-or-implemented commands for plan/preflight/collection/branch/score/policy-freeze/continuation/smoke/evaluation/export; required real artifact paths; source shortages or identity conflicts; full and remaining budgets; implemented vs GPU-verified status. Never invent remote paths, repo commits, new results or runtime readiness.

## 13. Sources and boundaries

Project basis: user-supplied 27 October Stage I audit; original PACT proposal; heterogeneous-training revival Stage II/III specification; v2 checkpoint/evaluation safeguards. Use actual executed manifests for source facts.

External methodological caution: Kingma & Ba, Adam: A Method for Stochastic Optimization, arXiv:1412.6980 (gradient-rescaling property); Ren et al., Learning to Reweight Examples for Robust Deep Learning, ICML2018/PMLR80 (training-weight selection using separate meta-data). These are precedents, not validation or novelty evidence for this experiment.

BEGIN by resolving source contracts and implementing the smallest complete crossed-probe -> scheduled-allocation -> prospective-evaluation pipeline. Do not execute model work automatically.
