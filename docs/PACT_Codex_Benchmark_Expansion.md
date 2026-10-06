# PACT codebase update: benchmark breadth, native evaluators, and staged heterogeneous experiments

Prepared: 6 October 2026
Suite variant: `heterogeneous_breadth_v1`
Proposed study namespace: `pact-breadth-001`
Status: implementation specification and bounded experiment design; NOT executed benchmark evidence.

## 1. Mission and scope

Update the EXISTING PACT repository to add MMLU-Pro, MuSR, MATH-500, MBPP+, a new explicitly allocated GPQA-Diamond characterization cohort, and a release-locked LiveBench slice. Extend the completed heterogeneous natural-complementarity runner; do not start another framework.

The questions are:
1. Across different task families, do heterogeneous private responses contain correct solutions not covered by the best constituent or homogeneous team?
2. On the four prespecified core additions, how much of that availability becomes final task success through synthesis or communication?

Implement dataset access, normalization, split/exposure manifests, task-appropriate response contracts, real evaluator adapters, private-bank collection, optional separately invoked communication, reports, durable export, tests, and thin Colab notebooks. Adding six loader stubs while scoring everything as A/B/C/D does not complete this request.

This phase is CLEAN and INFERENCE-ONLY. There is no PACT training, receiver training, specialization, synthetic donor acquisition, counterfactual replay, attack search, model selection, or new adjudicator. Do not claim that more benchmarks establish adversarial robustness or that heterogeneity will necessarily help.

Workflow: local Codex development and CPU/mock tests -> user review/commit/push to GitHub -> pinned checkout and actual model work in Google Colab -> results returned for local analysis. Do not run pretrained models or download their weights locally, launch GPU jobs, commit, push, modify remotes, change permissions on private files, or disturb unrelated work. No Slurm/PBS/SSH-cluster dependency, required Docker daemon, paid inference API, or multiple-GPU requirement. Use the existing generation backend rather than benchmark scripts that call external APIs or silently install vLLM/replace PyTorch.

Inspect Git status, AGENTS.md, actual package structure, latest 6 October audit, prior heterogeneity implementation and dataset manifests first. Proposed names below are capabilities, not claims that commands already exist. Reuse existing working code, adapting only what the new task types need.

## 2. Preserve the completed study and experimental identities

The parent is `pact-heterogeneous-complementarity-001`, variant `heterogeneous_natural_support_v1`.
Recorded completed source: `874b3b184c6cdcde6c27368621d7747fd6e01467`.
Plan: `b972e06e3b8e69f8e53053d238b7fa7f04c1ddb331654b7555262021d47a506f`.
Private bundle SHA256: `57cde0e55b4acf8443582b06205778a12f4b0214d5007932e23f1f0b102f89d4`.
Sanitized bundle SHA256: `c96c04aa1303dec275f9f9db534786727ec75300d02da4fe71779a5c29b887d7`.

Verify actual retained manifests, without resetting newer code to an old commit. The study completed 80 exposed ARC/LogiQA tasks and 2,400 calls. QLM initial coverage was 63/80, initial synthesis 43/80, revised readout 40/80. These remain historical observations; do not copy them into new dataset result rows or imply a new reproduction.

Earlier controlled specialization remains closed incomplete, with its recovery flag unchanged. This benchmark phase needs no old learned-adapter or optimizer tensors and must not reopen stopped experiments. GPQA has a prior partition with 32 exposed development items, 164 protected items, and two recorded repeated-option exclusions. Preserve it exactly before creating the new explicitly allocated child partition below.

New per-dataset runs have immutable child IDs, for example `pact-breadth-mmlu-pro-001`. Existing completed IDs must not be reused. Confirm actual collisions and later exposure before planning. Historical ARC/LogiQA runs remain read-only context. Do not recollect their 80 tasks in this phase.

## 3. Models, teams, and logical protocol stay fixed

Use the official pristine instruction checkpoints and EXACT immutable revisions from the completed heterogeneity manifest:
- Q: `Qwen/Qwen2.5-7B-Instruct`.
- L: `meta-llama/Llama-3.1-8B-Instruct`.
- M: `mistralai/Mistral-7B-Instruct-v0.3`.
- Common readout: pinned unadapted `Qwen/Qwen3-8B`, no learner adapters, thinking disabled.

Do not resolve newer model weights merely because dataset code is new. If a parent revision is absent, identify the missing prerequisite rather than silently selecting another checkpoint. Use each recipient's native tokenizer, chat template, generation boundary, and EOS/end-of-turn rules. Keep the inherited semantic private/revision instructions except for the explicit task-output contracts below. Do not give identities, personas, expertise claims, or instructions to disagree.

Private/revision generation remains sampling at temperature 0.7, top-p 0.8, top-k 20, repetition penalty 1.0, one result per request. Preserve the other resolved parent fields. Readout generation is greedy. BF16 and SDPA remain requested; no silent quantization/offload/attention changes. Dataset-specific output/context caps below are new design choices, not evidence that the previous 256-token/4k profile generalizes.

For each task generate nine private packets:
`P[task, family Q/L/M, replica 0/1/2]`.
Form QQQ/LLL/MMM from the corresponding three family replicas. For QLM use the existing balanced anonymous-slot permutation rule: when family F occupies slot j, select `P[task,F,j]`. Fix all bindings before outputs. No oracle/best-of-nine team selection. Balance permutations within declared dataset strata where feasible; report residual imbalance for small strata.

All nine private responses precede any receiver response for that task. Independent synthesis never feeds a revision. Each revision sees its own saved private packet and the other two INITIAL packets only. Both synthesis stages use the SAME readout and task-output contract, once on private and once on revised packets. Source family stays audit metadata, not a prompt label. All stages can be served sequentially by model without changing this information flow.

## 4. Two phases; implement both, invoke separately

### Phase A: private natural-complementarity screen
For each selected characterization task, generate ONLY the nine private packets, score offline with the appropriate evaluator, form four teams without new generation, and report coverage/diversity. Cost: 9 model calls/task. No readout, revisions, hidden feedback, or outcome-triggered alternative sampling.

Phase A cannot establish a utilization gap by itself. Phase-B metrics must be `not_executed`/null, not copied from legacy data or filled with zero.

### Phase B: utilization on the four prespecified cores
Core datasets: MMLU-Pro, MuSR, MATH-500, MBPP+.
After separate explicit user invocation, reuse their EXACT Phase-A private packets and run all four teams through:
- 12 revisions/task (three per team).
- Four private-packet synthesis calls/task.
- Four revised-packet synthesis calls/task.
- One common readout task-only call/task.

Additional cost: 21 calls/task. Voting where meaningful adds no model calls. Run ALL planned tasks regardless of private correctness/disagreement; no positive-support gate. Do not choose only complementary tasks or drop negative datasets. Model/evaluator access, source integrity, safety and resource failures remain legitimate explicit stops.

GPQA and LiveBench are Phase-A stress tests in this initial budget. The general runner can support Phase B there, but no such execution is included in this design. Later activation requires a new budgeted plan, not a hidden "all datasets" sweep.

Default CLI/notebook is metadata-only `plan`/`preflight`, not Phase A or B. Each dataset and stage is independently invokable and resumable. One gated dataset or unavailable scorer must not prevent implementing/running the supported others. Failed readiness must remain visible in the suite report.

## 5. Official dataset sources and native semantics

Resolve immutable data revisions/checksums and evaluator code/dependency revisions BEFORE any benchmark generation. Use actual schemas, not assumptions from repository names. Do not invent SHAs, dataset sizes, official split semantics, test functions or release dates. Retain licenses/notices. Normal loaders use data files, not automatically executed remote dataset scripts.

### 5.1 MMLU-Pro
Official source: `TIGER-Lab/MMLU-Pro`; primary repository `TIGER-AI-Lab/MMLU-Pro`.

Use the official evaluation pool (typically named `test`); do not silently use validation examples intended for demonstrations. This study uses zero-shot PACT orchestration, not an official 5-shot leaderboard reproduction.

Preserve trusted question text and options. Typical fields include question_id, question, options, answer/answer_index, category, source, and cot_content; inspect the pinned schema. Only the question/options enter inference. Answer metadata, cot_content and reference material are evaluator-side. Check index/letter consistency independently.

Support variable option counts, including up to ten A-J labels and less-than-ten reviewed questions. Do not assume four or exactly ten. Keep native option ordering by default, with exact source-to-canonical mapping; this avoids corrupting position-dependent options such as "all of the above". Every model sees the same order. Do not strip meaningful case/Unicode or use answer-dependent whitespace repair. Pin an official maintained revision; record its upstream corrections (the card documents a leading-space correction in January 2026).

Stratify across the actual 14 category names. Proposed characterization: 10 questions/category = 140. Reserve a separate 10/category = 140 confirmation cohort, all remaining eligible groups reserved. Missing expected categories or insufficient groups are explicit plan errors, not invitations to silently rebalance to easy subjects. Balanced-domain sampling means primary overall score is macro-by-domain; show micro score too and do not call it a full-distribution official result.

### 5.2 MuSR
Official source: `TAUR-Lab/MuSR`; source repository `Zayne-sprague/MuSR`.

The published domain splits are `murder_mysteries`, `object_placements`, and `team_allocation`. They are task domains, not train/validation/test divisions. Preserve the full narrative, question, and choices. Check zero-based answer_index against answer_choice and the chosen canonical mapping.

The official CSV may encode choices as a literal list string. Parse via bounded safe literal/list parsing, never eval; validate type, length, and entries. Preserve entity names, narrative order, contradictions, and uncertainty. Do not summarize the story to fit a budget. Do not put answer_choice, answer_index, hidden reasoning graphs, or reference explanations into agent prompts.

Group author variants or near-duplicate narratives conservatively before local partitioning; variants with different legitimate answers must be GROUPED, not deleted as labeling errors. Record actual grouping limits rather than promising semantic decontamination.

Characterization: 30/domain = 90. Reserve 30/domain = 90 for confirmation; remainder reserved. Retain official choice ordering and original labels. It is not necessarily a four-option task. Report each domain separately.

### 5.3 MATH-500
Official hosted source: `HuggingFaceH4/MATH-500`, linked by its card to PRM800K's MATH split. This is an existing 500-item evaluation set, not a new training dataset. Expected fields include problem, solution, answer, subject, level, unique_id.

Show only `problem` to actors/readout. `solution` and `answer` remain evaluator-side. Keep original LaTeX, units, domains, set/tuple structure, and embedded text such as Asymptote descriptions; do not use the worked solution as missing diagram content. Do not generate distractors or convert mathematics into MCQ.

Characterization: 100; confirmation: 100; remainder nominally 300 before group/exposure checks. Stratify by subject and level using deterministic largest-remainder allocation, with documented handling of small strata. Any genuine unavailable-input modality must be identified by source-only rules before selection, not by low model scores. Counts after such rules remain explicit.

Use a pinned `Math-Verify` parser/equivalence adapter (or retain an already verified equivalent only if documented before generation). This is the chosen scorer, not an assertion that MATH-500 has one universally canonical grader. Lock parser configuration, symbolic/numeric tolerances, tuple/set conventions, string-answer handling, extraction policy and resource limits. Never use an LLM judge or Python eval on response text.

Independently validate the parser on fixture fractions, roots, signed expressions, intervals, sets, ordered tuples, variable expressions, plain text answers and genuinely inequivalent cases. Gold parse/scorer installation failures are evaluator errors, not model failures. A parseable but wrong prediction is a model failure. Timeout/unknown equivalence must remain diagnosable; no outcome-selected fallback grader.

Raw final-answer extraction must not use the gold answer to pick which expression in a response to score. Prefer one explicit final boxed answer under a versioned format. If contradictory final answers occur, follow a frozen ambiguity policy. Do not search all intermediate expressions and accept whichever equals gold.

### 5.4 MBPP+
Official data source: EvalPlus's pinned MBPP+ release through `evalplus` and/or `evalplus/mbppplus`. Inspect and reconcile actual task IDs, data version, hidden-test suite and source checksums. The official repository documents v0.2.0 removing broken tasks (399 to 378); do not hard-code an older 399-task population or silently change versions.

Characterization: 100 task groups; confirmation: 100; remainder nominally 178 at a 378-task release, subject to group checks. Record actual population rather than assuming full independence across copied programming tasks.

Trusted input is the official public instruction plus explicitly permitted signature/scaffold/imports/public examples. Gold solution (`code`/canonical_solution), additional tests, hidden test inputs/results, and evaluator annotations MUST NOT enter model prompts. Some official public examples are legitimate prompt information; document the exact public/evaluator boundary rather than hiding required function names or leaking all tests.

Use full Python solution generation, not answer letters or program IDs. Revisions/readout must return complete runnable replacement solutions, not a critique, diff, or a pointer to another packet. For each generated program, compute base and full expanded-test results through the pinned official evaluator; full MBPP+ result is primary. Do not substitute the small base test set, Mini tests, or syntax checking and call it MBPP+.

The safe-execution adapter is mandatory for running real generated code; see section 9. Reuse our own inference, NOT EvalPlus's model-generation CLI with separate defaults.

Program correctness means passing the finite benchmark tests under the declared limits. It is not a proof of universal semantic correctness or safe code. Distinct program text is not necessarily different functionality. Hidden-test fingerprints cannot be used as a deployable voting rule.

### 5.5 GPQA Diamond
Reuse the existing authorized official `Idavidrein/gpqa` loader, source revision/option policy and complete parent partition receipts. Parent accounting: 198 source IDs, 32 already exposed, 164 protected, two exact repeated-option exclusions. Do not regenerate old calls or silently move those old 32 into confirmation.

This phase explicitly allocates 32 NEW characterization task groups from the previously protected 164, using a fixed domain-stratified selection before model outcomes. Of the remaining nominal 132, designate 32 as locked confirmation and 100 as reserved, conditional on genuine duplicate/exposure checks. Preserve historical classification in a parent->child exposure ledger; do not rewrite the parent manifest.

Use the existing case-sensitive, Unicode-preserving option validation and stable once-per-task shuffle. All actors use the same shuffled options. Keep the native question, not author explanations or validation feedback, in prompts. Do not use a mirror, accept access terms on the user's behalf, or publish GPQA plaintext/images/prompts/decodable tokens.

Selecting IDs or reading needed metadata is not model generation; disclose it. These new 32 are breadth-development data when executed, not training and not untouched final data. GPQA-main/extended must not be used for training by this update. Access failures block GPQA only.

### 5.6 LiveBench: requested release is a contract, not a guessed download
Requested release label from the plan: `2026-06-25`. Verify that the complete requested question content for the selected categories AND matching official scorers are actually publicly/authoritatively available. A leaderboard/date/CSV of model results is not the question dataset.

Source family: official `LiveBench/LiveBench` and official `livebench/*` Hugging Face datasets. Needed categories: reasoning, math, data_analysis, language, coding. Verify their actual repository names and scorer registration; do not fabricate task names. Exclude agentic coding, instruction-following, multi-turn/tool environments and unprovided modalities from this first subset by declared task-type rules.

IMPORTANT VERIFICATION NOTE: primary sources inspected while preparing this brief did not establish full downloadable 2026-06-25 questions. Retrieved repository documentation warns that some newer releases are not fully public, and retrieved public reasoning data exposes older release dates. Do not call a current Hugging Face snapshot the 2026-06-25 dataset simply because the leaderboard uses that label. If unavailable, implement the correct adapter and emit `requested_release_unavailable` with evidence, allowing other datasets to proceed. No automatic fallback to an older release or an unreviewed mirror. A user-authorized official export with checksums can satisfy access.

Preserve question_id, category, task, turns, release/removal metadata and the exact official temporal filter. Typically membership depends on addition AND removal dates, not equality to the requested date. Inspect the actual scorer/loader predicate, freeze it, and test its boundary behavior. Old questions retained in a new release are not newly authored questions. Log both release membership and each question's source/date provenance where available.

Characterization target: 20/category = 100, plus a separately locked 20/category confirmation target where available. Within category, stratify by selected single-turn scorer task using deterministic allocations. Every supported scorer task with eligible source items should be represented where the quota permits. If the release cannot supply these quotas, report the exact shortfall; do not silently substitute categories or top up from an older release.

Use the authoritative per-task objective scorers, with dependency and code hashes. Preserve native expected output instructions (e.g. solution tags, tables, lists, code) and score the NATIVE response text. Do not wrap every answer in A/B/C/D JSON or send it to a generic LLM judge. Reuse our inference and import only reviewed scorer functions; upstream API defaults/retries must not alter our budgets.

If a scorer provides fractional/structured scores, retain them. Define binary `full_success` only through the documented full-credit condition, not bool(score) or an arbitrary threshold. For pure graded tasks with no meaningful full-success predicate, report native/oracle-graded scores separately and mark binary metrics N/A. No average across incomparable raw scoring scales.

Coding tasks use the same isolated evaluator boundary as MBPP+. Tasks requiring unsupported dependencies or Docker-dependent agentic execution are explicitly outside this subset; do not shorten them into another task and retain an official score label.

Do not claim contamination-free evaluation. At most, report version/date provenance and the limits of what is known about the model/data timeline. Release date alone is not evidence that all tasks postdate model training.

## 6. New data contracts: input, response, and evaluation are separate

Extend existing typed records and discriminated task kinds rather than weakening the old MCQ schema:
- `mcq`: MMLU-Pro, MuSR, GPQA.
- `math_free_response`: MATH-500.
- `python_program`: MBPP+.
- `native_livebench`: exact task-specific scorer/output contract.

A `BenchmarkAdapter` should provide capabilities equivalent to: source receipt, schema validation, deterministic task/group ID, safe TaskInput, private EvalSpec, grouping/strata, response-format instructions, prediction parsing, offline scoring, and optional gold-free voting key. Existing names may differ; avoid a parallel registry if the package already has one.

Separate three states:
1. Response syntactic validity.
2. Task success under a named evaluator.
3. Evaluation/infrastructure availability.

A model syntax error, wrong option, abstention, wrong program, and a missing grader are NOT interchangeable. Return explicit statuses and score/reason fields, not a single bool coercion. A missing hidden-test runner cannot produce false program failures or successful paper scores.

Keep raw text and tokens immutable. Internally normalized parsed views retain their parser version and transformation details. Do not edit peer messages using the evaluator's answer. Gold is permitted in offline evaluation, not generation, voting, peer displays, revision prompts or readout inputs.

## 7. Response contracts and budgets for the new datasets

These are explicitly NEW task-appropriate profiles. They replace a uniform 256-token answer-letter assumption ONLY for these new runs, not legacy experiments. Within a dataset every team/family uses the same configured cap and semantic requirements.

| Dataset | Private / revision max new tokens P | Synthesis / task-only max new tokens F | Total recipient context cap |
|---|---:|---:|---:|
| MMLU-Pro | 512 | 64 | 8,192 |
| MuSR | 512 | 64 | 8,192 |
| MATH-500 | 1,024 | 1,024 | 8,192 |
| MBPP+ | 1,024 | 1,024 | 8,192 |
| GPQA Diamond | 256 | 64 | 4,096 |
| LiveBench selected native tasks | 1,024 | 1,024 | 16,384 |

MCQ uses the existing answer-plus-justification format with a generalized allowed-option set. Math uses a concise free-form derivation with one explicit final boxed answer (`math_final_boxed_v1`), not fake options; all generated text is the packet. Code uses exactly one complete Python program under a frozen extraction contract (e.g. a single fenced python block); explanatory text is bounded but never mistaken for runnable code. Preserve native LiveBench format expectations; outer peer envelopes remain typed metadata plus uninterpreted response text.

A readout that must return code cannot be capped at the old 64 answer-token budget. For math/code, the readout may produce a new complete solution, not merely select an existing packet. This allows construction and must be reported.

Check prompt plus reserved generation under EACH actual recipient tokenizer. A 1,024-token source packet may be longer for another tokenizer. Preflight selected source inputs before generation, and check actual rendered revision/readout prompts at dispatch. Do not truncate the question, narrative, code, options, or peers; do not change caps, summarize inputs, switch mode/precision or drop difficult items to finish a run. Unsupported budgets get explicit status, actual counts and fixed-denominator sensitivity, not hidden replacement.

Finite output caps are diagnostic constraints, not a proof that they suffice for every task. Report length-stop rates by dataset/family/stage. Large truncation rates limit conclusions; extending a cap requires a new version, not a retrospective repair.

Private request identities include the intended later-phase response contract so Phase B can legitimately reuse Phase A. Changing the private format later cannot be disguised as exact reuse. Same model family does not imply identical token cost or FLOPs across datasets.

## 8. Split discipline, sampling, exposure, and source preflight

Use master design seed `20261006`, namespaced by dataset, partition, group and stratum. Persist the actual resolved selection before inference. Store source row count, eligible group count, expected quota, realized counts, exclusions and their non-outcome reasons. Never silently shrink a planned sample, move one row to another stratum, or pick alternatives after seeing predictions.

Three local partitions: `characterization_dev`, `confirmation_locked`, `reserve_locked`.
- All are EVALUATION source material for this project phase: `training_allowed=false`.
- Generation is authorized only for `characterization_dev` with explicit stage invocation.
- Confirmation/reserve IDs may be fixed from needed source metadata now, but no model calls, manual answer-based selection or report of their model performance occurs.
- User review of characterization outcomes is allowed and makes those examples development-exposed. Do not subsequently call them untouched tests.
- This implementation does not authorize confirmation/final execution. The CLI must refuse a broad wildcard invocation that reaches locked partitions.

Use exact source IDs and stable hashes. Group known duplicate/near-duplicate tasks and parent benchmark links (e.g. MATH-derived tasks, copied coding tasks, repeated narratives) before local splits. Cross-dataset duplicates need joint group IDs/exposure flags; do not count the same problem as independent evidence twice. Preserve meaningful math case/Unicode and don't collapse different options/problems into false duplicates. State limits of lexical rather than semantic checks. If groups reduce feasible quotas, stop/record for a new explicit plan; no user-answer request should be necessary to implement remaining components.

Do not read or regenerate every older private archive just to add loaders. Use the latest exposure ledger and only source records necessary for exclusions. Dataset access, text/source validation, prompt-format validation and scorer availability should happen before spending thousands of model calls.

## 9. Code and expression execution safety: real evaluation without exposing the workspace

Generated Python is untrusted even on an apparently benign code benchmark. EvalPlus's `reliability_guard` explicitly says it is NOT a security sandbox. A subprocess, timeout, stripped environment, or AST blacklist alone must not be called a secure evaluator.

Implement a separate code-evaluation interface with an actual OS-isolated backend (reuse an existing trusted one; a non-Docker Linux namespace/seccomp backend such as a capability-checked bubblewrap/nsjail worker is acceptable). Do not design a new security product. Preflight must prove the enforcement properties in the actual evaluator environment, not merely find an executable name.

Required boundary for real generated code: no network, no access to mounted Drive/Git/HF tokens/SSH keys/model caches/parent directories, nonprivileged identity, restricted read-only runtime/dependencies plus a disposable work directory, process/CPU/wall-time/memory/output limits, child-process cleanup, and a structured result channel. Use only pinned trusted test harness code. Generated source must not be shell-expanded, imported into the notebook/kernel, or passed to parent-process eval/exec. Trusted harness execution inside the isolated worker is distinct from unsafe notebook execution.

Use the official evaluator's task tests, entrypoints and timeout/memory semantics within this boundary. Compare a tiny set of invented and trusted fixture programs with direct official scoring. Do not rewrite expected answers or loosen limits until a model passes. Ground-truth calibration used by EvalPlus, if required, occurs only evaluator-side. Hide result/test details from all generation stages.

If the current Colab cannot enforce isolation, stop REAL code scoring with `safe_execution_unavailable`. Keep generation and other datasets usable through explicit per-stage choices, export complete code-evaluation jobs, and support import of scores from an independently run isolated evaluator with matching task/source/program/evaluator hashes. Do not auto-run unsafe code, install a new external paid service, or substitute static/LLM scoring. Clearly report that a pending code bank cannot yet establish MBPP+ complementarity. A separate trusted evaluator capability is a runtime prerequisite, not evidence that the dataset adapter was fully GPU-validated.

Provide two thin notebooks if needed: inference and secret-free isolated CPU scoring. Do not mount Drive in the code execution worker. Moving a ZIP out of the model runtime does not itself create a sandbox; still enforce the backend boundary. Windows local development can run mock safety-contract tests and metadata analysis without pretending a Linux kernel sandbox was validated there.

For symbolic math/native parsers, use resource-isolated workers and bounded parsers; never evaluate arbitrary expressions as Python. Kill pathological parser jobs and preserve their status. Code/runtime safety probes use harmless local sentinels, never real user secrets or internet targets.

## 10. Scoring, voting and nonbinary measures

Run scoring offline after generation or as an isolated evaluator side channel. Generation requests must not depend on correctness feedback. Identical program/response bytes can reuse exact evaluator results only with matching task/test/evaluator/version/environment identities; record original versus reused work.

MCQ vote: existing deterministic majority/tie/invalid policy, no label tie-breaking.
Math vote: optional conservative, declared gold-FREE canonical answer grouping. Do not use equality to the reference to combine correct candidates. If equivalence is ambiguous or nontransitive, abstain/no-majority under a frozen rule rather than infer an oracle cluster. Report the chosen normalization limits.
Code vote: default `not_applicable`, because identical code text is not semantic equivalence and hidden-test behavior is unavailable to inference. An eventual exact-source vote can be a separately labeled secondary control, not a semantic-majority score. Do not force this module to return a wrong/success value for N/A.
LiveBench: vote only for registered tasks with an unambiguous gold-free key. Other tasks get N/A, not an invented implementation of majority semantics.

For continuous native scores s in [0,1], keep native mean, normalization and task-level details. `max_i s_i` can be reported as oracle best-candidate score, clearly different from binary correct-answer coverage. Do not convert partial credit to success simply because it exceeds zero. A full-success predicate must be task/evaluator-defined and recorded before outputs.

MBPP+ coverage is whether at least one program passes all required tests. This is not classical iid pass@k for one policy, because the QLM samples come from different policies. Report empirical team pass-any/coverage, not a misleading unbiased pass@k estimator.

## 11. Required metrics and attribution

For every dataset and team, with valid binary evaluator semantics, reuse:
`C_i0`, `N0=sum C_i0`, `O0=any C_i0`, per-family/member accuracy, c, 1-c,
`G=c-max_i accuracy_i`, unique coverage, pairwise rescue, and valid success/failure mixed support.

Measure QLM against EACH of QQQ, LLL, MMM, not only their average or a weak reference. A cohort-selected best model/team is descriptive, not a deployable oracle selector. Aggregating QLM by anonymous slot conflates family and display order; report primarily by true family.

Do not require each model to have unique-only correct cases before recognizing coverage gain: two models may jointly rescue the best member on overlapping tasks. Wrong-option disagreement, different equivalent math expressions and different passing programs are not interchangeable evidence of complementarity.

Phase B adds N0->N1 transitions, hold/repair opportunities and outcomes, task-level erasure, construction, utilization, readout loss for private and revised input, and final success despite no correct proposed solution. Check both exact availability/outcome decompositions. No decoder gets evaluator labels.

A synthesizer that can invent a new answer is not mathematically upper-bounded by private coverage. Therefore c-final_accuracy is descriptive only; do NOT interpret it automatically as a count of ignored correct answers. Count the joint event `O0=1 and Y=0` or `O1=1 and Y=0` explicitly, while separately counting construction. Finite passing-code evidence and label-correct rationales are not general proof validity.

Hold/repair in this phase describes honest model error, not an adversarial attack. Nothing here identifies a causal reason for a wrong readout. Compare natural before/after changes and refrain from saying every change is persuasion.

Use per-dataset task/group-clustered paired bootstrap, stratified by predeclared domains/categories, keeping all families, replicas and protocols together. Recompute selected maxima in each resample. Conditions/calls are not independent observations. Preserve boundary uncertainty; an empirical [0,0] difference is not proof of equivalence. One seed schedule is descriptive characterization.

MMLU-Pro equal-category sampling: primary macro-category estimate. MuSR: domain-stratified aggregate. MATH/GPQA: report actual stratum weights. LiveBench: native task/category aggregation on selected tasks only, never its official full global score. Cross-benchmark summary is a vector/table first. A macro average, if useful, needs a fixed definition and eligible-dataset denominator; do not pool incomparable scores or hide a failed dataset.

No new success/support gate: every planned, executable case is processed and reported regardless of mixed-rate results. Phase-B selection of the four core datasets was made before results and must not be revised to favor positives. Stress datasets remain separately labeled.

## 12. Failure and missingness policy

Retain at least these independent fields: schema_compatible, access_ready, response_contract_ready, scorer_ready, runtime_ready, partition_locked, generation_completed, scoring_completed, communication_completed, and scientific_result.

Model failures: malformed generated answer/program, valid wrong answer, abstention, length-limited completion, official program timeout/test failure. They count according to the prespecified strict performance policy and remain broken down.
Infrastructure/evaluator failures: absent scorer, scorer crash, access denial, missing snapshot, unsafe sandbox, unresolved dispatch, invalid gold reference. These are unavailable observations, not fabricated model successes/failures. A partial run cannot be marked scientifically complete.

For partial outputs provide intended, generated, scored and paired-cohort denominators, lower/upper score bounds where appropriate, and a clearly secondary complete-case summary. Do not show an ordinary binary accuracy table that silently drops unscored code or truncations. With 0 valid observed support, conditional metrics are null plus numerator/denominator/reason, not misleading zeros.

Dataset schema/access issues stop only that dataset. A scientific zero effect does not stop collection. No silent task replacement, cap expansion, official-test-to-train conversion or resuming through `recovery_safe=false`.

## 13. Exact budgets and execution schedule

Let N be characterization tasks, P private/revision output cap, F readout cap.
Phase A: `9*N` calls and `9*N*P` reserved generated tokens.
Phase B: `21*N` additional calls and `N*(12*P+9*F)` reserved generated tokens.
Full A+B: `30*N` calls and `N*(21*P+9*F)` tokens.
These formulas include all four teams and one task-only readout, but not duplicate private generation. Voting and scoring cost zero LLM generations; actual scorer executions/CPU time are separate.

| Dataset | N | A calls | A token cap | B calls | B token cap |
|---|---:|---:|---:|---:|---:|
| MMLU-Pro | 140 | 1,260 | 645,120 | 2,940 | 940,800 |
| MuSR | 90 | 810 | 414,720 | 1,890 | 604,800 |
| MATH-500 | 100 | 900 | 921,600 | 2,100 | 2,150,400 |
| MBPP+ | 100 | 900 | 921,600 | 2,100 | 2,150,400 |
| GPQA Diamond | 32 | 288 | 73,728 | 0 | 0 |
| LiveBench target slice | 100 | 900 | 921,600 | 0 | 0 |
| TOTAL | 562 | 5,058 | 3,898,368 | 9,030 | 5,846,400 |

All implemented initial phases together: at most 14,088 generation attempts and 9,744,768 reserved output tokens. These are LARGE portfolio ceilings, not one Colab-session request, time estimates, compute units, or expected consumption. Missing official LiveBench release reduces actual runnable work; never consume its reserved calls on another dataset.

Plan dataset-by-dataset. Recommended execution order: MMLU-Pro A, MuSR A, MATH-500 A, then MBPP+ once safe scoring is ready, and independently ready GPQA/LiveBench A. Core Phase B is predesignated but separately invoked, not selected based on positive A outcomes. No automatically chained all-suite execution on Run All.

A smoke is an outcome-independent prefix of exactly TWO already selected characterization tasks with unchanged request IDs; Phase-A smoke is at most 18 INCLUDED calls. For a B smoke, reuse private packets and include only the already budgeted requests. No toy model call or real-model schema probe outside the frozen call plan unless separately reserved. Local fixtures add no real model calls.

Expose attempt/reserved/actual-token totals; every dispatch counts, including failed/unknown attempts. Never replenish budgets on resume. Successful calls cached from A are inherited observations for B, not new expenses. Actual input tokens, evaluator invocations, model loading, wall time and GPU stage time are recorded separately. Compute units remain null unless the user provides a measured value.

Model-major scheduling within an invoked dataset/stage (or an explicitly budgeted batch of datasets) loads one family at a time. Do not require simultaneous Q/L/M/readout GPU or host residency. Use the established cleanup and access preflight. No dataset script may bring a second hidden model into memory for grading.

## 14. Implementation structure and practical delivery

Extend the existing dataset/model/protocol registries. Suggested CLI capabilities, not fictional command names:

- `benchmarks list/status` — per-dataset implementation/access/scorer readiness.
- `benchmarks inspect-source` — explicit online/user-authorized source inventory, revisions, schemas and quotas, no model calls.
- `benchmarks prepare --dataset ...` — partition/group/mapping manifests.
- `breadth plan/preflight --dataset ... --phase A|B` — exact budget, model contract and evaluator readiness.
- `breadth private --dataset ... --model Q|L|M`.
- `breadth score --dataset ...`.
- `breadth revisions --dataset ... --model Q|L|M`.
- `breadth readout --dataset ...`.
- `breadth report/export`.
- `code-eval plan/probe/run/export/import-scores` — safe, separate execution where supported.

Reuse actual command naming. Supply exact implemented commands at handoff. Do not build a manifest-only proof of concept; implement real data-file loading, real native-scoring adapters, and runnable generation/communication paths. If an external prerequisite is unavailable, implement and test the rest with fixtures and record the specific runtime blocker.

Separate lightweight audit/test dependencies from mathematical/code/native-scoring extras. Pin compatible releases/commits and the actual working environment without inventing a "validated" GPU lock. Prefer evaluator-only virtual environments/processes if their dependencies conflict with generation; don't broadly replace the working PyTorch/Transformers stack. The code API should support offline reporting without importing torch or downloading data.

Use thin notebooks: `benchmark_breadth_colab` for explicit source preparation/inference/report stages and, where appropriate, `isolated_code_scoring_colab` for the isolated CPU evaluation route. Every stage takes repository commit, per-dataset config, plan hash, data/evaluator revision, artifact roots, stage, and resume state. No secrets in notebook outputs or URLs.

All six adapters must have working unit fixtures and explicit status. Deliver in vertical increments with a complete MCQ path first, then long-context/free math, then executable code, then release-specific native scorers/GPQA allocation. Do not spend the whole development pass writing audit prose while leaving all adapters unimplemented. If genuinely unable to finish, leave tested runnable pieces, list precise missing functions, and don't mark placeholders as implemented.

## 15. Persistence, privacy, and replay of evidence

Reuse scratch-first writes, versioned shards, local-first ZIPs, bounded copy workers, and verified completion receipts. Do not create a new object store. Preserve generation and scoring attempt journals separately. A score import must match raw program/response hash, task/test checksum, parser/scorer version and runtime limits; never accept filenames alone as identity.

All request/cache keys include dataset/subset/release/revision, original task/group ID, option mapping, response/prompt contract, recipient model/tokenizer/template, cap/decoding, seed, role/stage and full content. Phase B references exact Phase A sources, not new random samples. Scorer identity changes require rescoring as a new derivative artifact, not overwriting old outcomes.

Do not let a sanitized report imply it supports raw prompt reconstruction. Keep raw dataset/prompts/programs/reference/test artifacts private and outside tracked Git; GPQA restrictions are strict. Shareable outputs contain aggregate scores, hashes, source references, manifests where policy permits, resource counts and missingness—not benchmark examples or decodable token arrays. No model/font/weight files in the prompt or review pack. Retain full raw evidence separately for authorized audit.

A code push does not back up ignored results. State exact persistent output locations and omitted artifacts. Recovery safety requires the existing durable journal criteria, not simply an equal number of intended and saved results. Historical incomplete runs remain incomplete.

## 16. Tests required before handoff

Default tests use small INVENTED tasks without network/CUDA/model weights. Do not download benchmark examples into committed fixtures. Optional online schema/evaluator integration checks are opt-in and report actual revision/access. Optional neural tests use tiny locally initialized models.

Required tests:
1. All six adapter registrations, distinct task types, lazy dependencies, and meaningful unsupported-access/release errors.
2. Variable MCQ label counts (including J), source index/letter consistency, same options for all actors, no label/cot fields in generation.
3. MuSR CSV safe list parsing, full narrative preservation, zero-based mapping, grouping of near-identical author variants without deleting legitimate label differences.
4. MATH final-expression extraction without gold-guided selection; fractions/roots/sets/tuples/text answers, inequivalence, malformed output, scorer errors and bounded pathological parsing.
5. MBPP official ID/version mapping, public prompt/hidden test separation, complete code extraction, no code execution during load/parse/report.
6. Real isolated-worker probe tests for blocked file/network/process escape using harmless sentinels, time/resource cleanup, and a test proving unsafe backend fallback is refused. Mark unavailable OS tests skipped, not passed.
7. Code-fixture parity with the pinned official expanded-test scorer; base pass versus plus failure; score import identity mismatch; test feedback never reaches inference.
8. LiveBench addition/removal boundary filtering, missing 2026 release, native task format/scorer dispatch, full-success versus fractional scores, no generic judge fallback, unavailable categories.
9. GPQA exact parent exposure partition, new32/confirmation32/reserve100 allocation where eligible, legacy32 preserved, locked generation/training rejection, sanitized export privacy.
10. Deterministic group-disjoint characterization/confirmation/reserve manifests, quota shortfalls, cross-dataset duplicate flags, no outcome-based replacement.
11. Exact nine-packet bank and QQQ/LLL/MMM/QLM binding, family-to-slot balance, no best-of-nine selection, all private barriers.
12. Phase B reuses private sources and never sees other revisions; same readout contract across branches; no correctness feedback.
13. Per-recipient token preflight, dataset-specific P/F limits, code/math readout not constrained to64, overflow accounting, no silent input trimming.
14. Gold-free vote/N/A semantics, code syntactic difference versus functional success, graded-score aggregation and constructor outcomes beyond coverage.
15. Conditional metrics identities, undefined rates, task clustering, selected maxima, missing-scorer partial report, intended denominators.
16. Exact budget formulas/table/JSON parity, 18-call smoke inclusion, scoring counters distinct from generation, no budget reset on resume.
17. Full mock A->score->B->score->report/export->offline-reconstruction for representative MCQ/math/code/native LiveBench tasks, including zero-complementarity and evaluator-unavailable paths.
18. Actual top-level CLI/notebook entrypoint tests, not only collector functions; preserve the smoke-wrapper regression that earlier missed tuple arity.
19. Relevant legacy protocol/dataset/controlled-replay tests still pass; don't weaken privacy or recovery guards to get a green suite.

Report actual test passes/skips/errors. A collection of targeted passes is not an unexecuted all-green suite. Real GPU evaluation, source access, sandbox enforcement and benchmark behavior remain separately unverified until the corresponding returned evidence exists.

## 17. Output artifacts and acceptance

Use existing naming where sensible; include:
- `benchmark_registry.json`, `source_access_receipts.json`, data/scorer/package revisions.
- `dataset_group_exposure_manifest.json`, partitions, quotas and exclusions.
- `response_contracts.json`, public/evaluator field allowlists, format fixtures.
- `budget_plan.json`, model identities, environment, readiness by dataset/phase.
- Private packet bank, exact four-team source bindings, revision/readout records.
- Offline score records, parser/scorer errors, code sandbox receipts and execution counters.
- Per-task/per-family metrics, complementarity tables, transitions, paired comparisons, native-score details.
- Per-dataset and suite reports clearly distinguishing A/B, supported/missing, and legacy/new.
- Exact actual-versus-reserved resource use, stage attempts, checksums, `CODEX_HANDOFF.md`.
- Separate private full-trace and sanitized public summaries; no hidden tests/raw restricted data in Git.

Update AGENTS.md concisely, implementation status, decisions, benchmark methodology, exposure ledger and Colab runbook. Make clear that Phase A can establish private answer availability, not utilization or trained robustness. All prior PACT result placeholders remain unchanged.

Final Codex response must include: changed files; verified source/schema/scorer choices and unresolved ones; actual local tests; six concrete format/evaluator fixtures; exact commands for first MMLU-Pro smoke and each dataset/stage; budget table; sandbox/LiveBench/GPQA prerequisites; expected return bundles; implemented versus GPU-unverified/deferred items. Do not claim this prompt creates the codebase itself or that new scores exist.

BEGIN by inspecting the existing repository and relevant source contracts, then implement the smallest complete multi-benchmark path and expand it without changing the frozen science silently.

## 18. Primary-source pointers and limits

These are reference pointers, not permission to blindly run upstream installers or code. Resolve actual compatible pins at implementation time, record what was checked, and preserve licenses. Source checks performed for this brief on 6 October 2026 do not certify future availability or a working runtime.

- MMLU-Pro card/schema: https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro
- MMLU-Pro official code: https://github.com/TIGER-AI-Lab/MMLU-Pro
- MuSR source/card: https://huggingface.co/datasets/TAUR-Lab/MuSR
- MuSR official code: https://github.com/Zayne-sprague/MuSR
- MATH-500 source/card: https://huggingface.co/datasets/HuggingFaceH4/MATH-500
- Math-Verify scorer: https://github.com/huggingface/Math-Verify
- EvalPlus code/data handling: https://github.com/evalplus/evalplus
- Official MBPP+ hosted data: https://huggingface.co/datasets/evalplus/mbppplus
- EvalPlus execution semantics: https://github.com/evalplus/evalplus/blob/master/docs/execution.md
- EvalPlus warning that reliability_guard is not a sandbox: https://github.com/evalplus/evalplus/blob/master/evalplus/eval/utils.py
- GPQA authorized source: https://huggingface.co/datasets/Idavidrein/gpqa
- LiveBench official repository: https://github.com/LiveBench/LiveBench
- LiveBench changelog: https://github.com/LiveBench/LiveBench/blob/main/changelog.md
- LiveBench official data organization: https://huggingface.co/livebench

The previous planning response described the June 2026 LiveBench label as a readily available freshness test. Current checked public documentation does not establish that full release's downloadable content. This implementation must verify availability or expose the blocker rather than silently filling that gap with older questions. A benchmark release is not a contamination guarantee.
