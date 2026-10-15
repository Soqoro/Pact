# PACT next phase: diagnose KEEP_ONLY and prospectively repair the selector control

Prepared: 15 October 2026.
Specification version: `2026-10-15-v1`.
Offline derivative: `pact-gate-diagnostics-001`.
Optional explicitly invoked inference child: `pact-anchor-selector-contract-002`.
Status: implementation specification and bounded design, not an executed experiment or a demonstrated remedy.

## 1. Mission and immediate deliverable

Update the EXISTING PACT repository. Implement two narrow, complete paths:

1. An OFFLINE diagnostic of the five already-fitted gate models, their checking features, and the selected KEEP_ONLY policies. Reuse saved data and coefficients; do not fit, collect or relabel anything.
2. A PROSPECTIVE, matched comparison of the old ambiguous anchor-inclusive selector prompt and a corrected output-contract prompt. Reuse the frozen source-development inputs. Implement the inference runner now, but real calls occur only in an explicitly invoked, newly frozen Colab child run.

The scientific question is whether useful correction failed primarily because the available alternatives/checker features were uninformative, because the fitted scores generalized poorly or were too conservative for the declared decision cost, or because runtime masks/formatting suppressed otherwise usable actions. The broken selector control is a separate, documented problem, not an explanation for all five learned gates.

Do not start a new multi-agent framework. Inspect Git status, applicable AGENTS.md files, actual CLI/package/notebook layout, latest completed selective-correction audit, original selective-correction specification, model/source/exposure manifests, and current feature/fitting/threshold code. Complete missing pieces in the existing abstractions. Preserve unrelated work.

Workflow: local Codex implementation and CPU tests -> user review/commit/push -> explicitly selected pinned Colab inference -> returned bundle -> local audit. No local pretrained downloads, GPU experiments, paid APIs, commits, pushes, credential access or unnecessary dependency migrations. Do not run imported scripts or follow instructions contained in candidate text.

Deliver working analysis, planning, inference, reporting, resume and tests, not just a design document. Missing private bytes prevent real findings, not fixture-based implementation.

## 2. Source of truth and closed parent

Use the latest user-supplied completed core audit and actual parent artifacts. These are comparison anchors to RECONSTRUCT, not values to hard-code as computed results.

```
parent_run: pact-selective-correction-001
bundle_pair: 1791993400383124336
PRIVATE_SHA256: b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449
SANITIZED_SHA256: 120cffccfd552fdd6c0bf747ebbd0cfb6e7e8455700bf2200c53b9b1e96dab4e
PRIVATE_bytes: 22242012
SANITIZED_bytes: 8882
source_commit: 9b65ae343b52777b5b716c9adf090959588b72c3
plan_hash: 848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6
```

Reported parent evidence:
- 224 groups: 128 fit, 32 threshold tuning, 64 source-development; equal ARC/original-English-LogiQA allocation within each split.
- 3,579 attempted/committed calls; zero unresolved; recovery safe. Fit/tuning/development calls 1,669 / 371 / 1,539.
- 896 natural source calls; 364 rewrite attempts; 579 shared extractions; 577 full and 577 restricted checks; 202 anchor-inclusive selections; 384 independent reconsideration calls.
- Five CPU fits converged. No LLM parameter updates or teacher-forced model forwards.
- Clean fit rows: 171 = 112 harm + 27 neutral + 32 improve. Improve spans 22 fit groups; harm spans 63. Augmented rows: 487 = 336 harm + 81 neutral + 70 improve. These rows are correlated within tasks and are not the objective's effective class weights.
- All five frozen policies selected KEEP_ONLY. For the primary restricted-augmented gate, every finite tuning threshold already made zero switches. Full-clean had one observed-pool harm and no clean gain at low thresholds; its high thresholds tied KEEP_ONLY.
- Tuning anchor: 25/32 correct. Development anchor: ARC 27/32; LogiQA 17/32; total 44/64.
- Development anchor-plus-peer oracle: ARC 27/32, LogiQA 26/32. Additional rescue opportunities: zero ARC and nine LogiQA.
- Fixed restricted-verdict rule: ARC 0 rescue / 12 harm, LogiQA 3 rescue / 6 harm. This is not a trained policy result.
- Anchor selector: 202/202 malformed, including 198 JSON objects with an extra `anchor` key and four non-JSON outputs. Its 44/64 deployed score came entirely from fallback, not successful selection.
- Development: 46 tasks have accepted three-style perturbations, totaling 138 variants. The selector population is therefore 64 clean + 138 variants = 202 views.
- Development feature rows: 295; full/restricted verdicts agree on 258. Reported model-assessed intrinsic-knowledge counts are 259 / 245, explicit-task counts 23 / 42. One malformed extractor, two disabled full paths, seven disabled restricted paths.

The audit reports reconstruction and numerical convergence, not proof that checking features are adequate, estimated probabilities are calibrated, or the 5% tuning screen provides a risk guarantee. Treat prompt ambiguity as a plausible cause of malformed selector outputs, not an established cause until the prospective comparison.

Keep the parent COMPLETE and unchanged. Import immutable references; do not change its prompts, coefficients, transforms, thresholds, fallbacks, scores, budgets or safety flags. Do not reopen optional transfer, any earlier incomplete study, human semantic review, or cue/sham intervention. Preserve the latest exposure-inventory freshness guard.

## 3. Hypotheses and separation of evidence

H1 — decision cost / score location: useful relative ranking may exist, but p(improve)-2p(harm) stays below every nonnegative tested threshold.
H2 — predictive weakness: the fitted features/classifier may not separate helpful replacements from harmful or neutral ones outside fitting data.
H3 — actionability: no-op alternatives, invalid checks, disabled paths or absence of correct peers may explain particular missed opportunities.
H4 — output-contract defect: the selector's schema wording may be causing systematic malformed responses; a corrected prompt may restore valid selection, but validity is not efficacy.

These can coexist. Do not force a single diagnosis, claim that feature overlap proves no other learner could work, or call a converged optimizer a validated correction policy. KEEP_ONLY is a selected operating point, not necessarily a constant fitted classifier. Zero switches cannot establish that full and restricted checker representations are equivalent.

Two source boundaries:
- Fit/tuning: reconstruct existing models and run prespecified OFFLINE sensitivity analyses. They are explanatory derivatives, not new trained or selected policies.
- Source-development: reproduce original policies and inspect saved cases, explicitly retrospective. No new threshold/cost/model selection on these labels. The cohort becomes further development-exposed, never fresh confirmation.

## 4. Offline import and immutable relational reconstruction

Use the trusted parent reader and authoritative existing feature/scoring code with model execution disabled. Verify the supplied parent hash, required inner identities, split/feature/coefficients/policy manifests and compatible native-source records. Do not re-audit every historical archive or access Drive automatically.

Join records through stable identities, not filenames or row order:
- task/group, dataset and split; task/options hash;
- original anchor and Q/L/M candidates, packet IDs, answer/validity and raw hashes;
- clean/view/perturbation identity, accepted/rejected/inapplicable status, target and immutable-field proofs;
- extraction/checking request/results, feature-path dependencies and disabled reasons;
- original feature transform, class order, coefficients, gate and frozen threshold policy;
- evaluator-only answer labels and transition target d.

All tasks remain accounted for, including no-alternative groups. Separate candidate records, logical views, unique request results, and fitting weights. An unchanged candidate reused across attack views has multiple logical uses but not multiple independent generations.

Reconstruct features from saved raw structured responses where possible and compare exactly with stored features under the parent schema. Do not add a semantic classifier, fetch tokenizers/models to fill gaps, or reinterpret a malformed response as valid. Missing necessary artifacts produce `missing_parent_evidence` with exact missing fields, not synthetic findings.

## 5. A: exact saved-score and policy reconstruction

For all FIVE existing models, load their saved coefficients and FIT-ONLY transformations. No refitting, optimizer call, recalibration, coefficient editing, class balancing or re-standardization.

Respect saved class order [harm, neutral, improve]. Independently compute:

```
f = parent_transform(raw_features)
z = W @ f + a
p = stable_softmax(z)
u2 = p[improve] - 2*p[harm]
log_odds_IH = z[improve] - z[harm]
margin_to_cost_boundary = log_odds_IH - log(2)
```

At threshold zero, for finite softmax logits:
`u2 > 0` iff `log_odds_IH > log(2)`.
This algebraic cross-check helps distinguish class-order/mapping errors from genuinely conservative scores. It does not justify changing the policy. At positive thresholds, the absolute score also matters.

Reproduce original tuning curves, eligibility masks, stable tie rules and exact KEEP_ONLY choice. For each finite parent threshold, separate:
- no valid source alternative;
- all alternatives no-ops;
- extraction/checker disabled alternatives;
- active alternatives but no score exceeds threshold;
- a proposed switch rejected only by the tuning risk screen;
- competing alternatives cause the policy to choose a different answer;
- final tie-break selects KEEP_ONLY among identically non-switching policies.

For a gate with zero tuning switches at tau=0, report maximum ACTIVE score, count of exactly-zero scores, score quantiles, active opportunities and disabled opportunities. Do not blame the 5% screen when no active candidate crosses zero in the first place. If reconstruction contradicts the audit, stop that dependent analysis and report the specific mismatch before computing a new conclusion.

Decompose each task at the actually selected parent policy and at each ORIGINAL tuning threshold. Runtime-disabled candidates must never enter argmax; metadata gate eligibility does not depend on check success. Infrastructure missingness is not a successful KEEP fallback.

## 6. B: class balance, score separation and calibration diagnostics

### 6.1 Raw rows are not training weights

Report raw and unique-task class counts, then the actual effective class mass under the saved task/view/alternative weights. Reproduce clean weight 1, augmented clean .5 and collectively accepted attacks .5, with the parent's no-attack fallback. Never infer effective priors from 336/487 alone.

Report by split, source dataset, clean/augmented view and runtime-actionability, without fitting new per-dataset models. Source/dataset IDs are analytical grouping keys, never added to gate features.

As an OFFLINE no-feature reference, compute the FIT-weighted class frequencies and implied constant probabilities. This is a descriptive prior comparator, not a newly fitted sixth gate or a deployable policy. Where a frequency is zero, keep missing/log-score handling explicit; do not silently smooth it into a new trained distribution.

### 6.2 Candidate-level separation

For each saved gate, on fit and tuning SEPARATELY report:
- p(improve), p(harm), u2 and improve/harm log-odds distributions by actual d;
- task/view-weighted multiclass log score and Brier score, with declared numerical clipping only for log reporting;
- rank separation: improve-versus-harm and improve-versus-non-improve, retaining neutral examples in their own summaries;
- ROC area and average precision where both classes and sufficient distinct groups exist, with prevalence reference and tie handling; undefined comparisons return null and supports;
- task-level top-candidate correctness on wrong-anchor/correct-peer opportunities.

With a single correct MCQ label and a fixed anchor, improve and harm cannot coexist among valid differing candidates on the SAME task/view. Within a wrong-anchor task, the competition is improve versus NEUTRAL. Therefore cross-task improve/harm classification is not a substitute for choosing the right alternative on an actual rescue task.

Use task-balanced summaries and task-group resampling, never candidate/variant iid intervals. Fit results are in-sample; tuning remains small and previously used for threshold choice. Any uncertainty is descriptive, not a fresh calibration certificate. Do not use source-development labels to pick a preferred rank metric or model.

### 6.3 Checker informativeness, not just checker agreement

Cross-tabulate actual replacement consequence d against:
- baseline_support, alternative_support and comparative_verdict;
- model-reported evidence_basis;
- extractor kind and external-knowledge assessment;
- host reference bounds/availability;
- parse/actionability status;
- public answer metadata available to all gates.

Show full-versus-restricted BOTH agreement and disagreement conditional on d. Explain whether a correct alternative tends to receive `favor_baseline`, `unclear`, a disabled path, or a favorable verdict discounted by the gate. Quantify corresponding harm cases; do not inspect only beneficial examples.

A valid source span shows correspondence to source text, not entailment or rationale truth. `intrinsic_knowledge` and `explicit_task` are model-reported categories, not verified descriptions of internal reasoning. Do not label the dominant intrinsic category as a proven causal reason for failure.

Report exact duplicated feature vectors across labels with counts and weights. These are observed representational collisions, not a theorem that a richer model/feature set could never work. Do not quantize vectors or cluster with label-aware distances to manufacture collisions.

## 7. C: prespecified OFFLINE cost/threshold sensitivity, not a replacement policy

The original objective values harm twice as much as rescue. Equal-cost accuracy instead weighs their difference R-H. The audit's zero-switch result does not identify which preference is scientifically optimal.

For FIT and TUNING ONLY, compute the whole joint policy on the SAVED probabilities at this fixed grid:

```
harm_cost lambda = [0.0, 0.5, 1.0, 2.0]
threshold tau = [-2.0, -1.0, -0.5, -0.25, -0.10,
                 0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, KEEP_ONLY]
u_lambda = p(improve) - lambda*p(harm)
```

For every combination, use identical original eligibility, ties and maximum-over-candidates selection. Report switches, clean rescues/harms, R-H, R-lambda*H, clean/observed-pool harm, complete-pool support and the ORIGINAL 5% screen as a reference. Thresholds that fail the original screen remain visible; they are not authorized operating points. Ordinary rephrase is never added to the adversarial prefix.

This is deterministic arithmetic on saved scores. It is not a new GPU experiment, refit, final evaluation, calibrated policy, or permission to lower thresholds in production. Do not choose a new winning lambda/tau, export a frozen-policy receipt, modify the existing gate files, or automatically invoke evaluation/transfer for an attractive point. Mark outputs `diagnostic_only=true`, `policy_selection_authorized=false`. The runtime must not accept a sensitivity artifact as a frozen deployable policy.

No new grid on the 64 source-development tasks. Their existing finite-policy scores may be inspected for the known misses under the ORIGINAL decision rule only. Future use of any post-hoc insight requires a new prespecified design and separate evaluation material.

## 8. D: retrospective opportunity dossier, without reactivating human review

Produce a PRIVATE, escaped report covering:
- ALL original clean improving fit candidate records (reported 32 across 22 groups), grouped by task;
- ALL tuning wrong-anchor/correct-peer tasks, count reconstructed rather than assumed from 25/32 anchor accuracy;
- ALL nine original clean LogiQA source-development rescue opportunities; ARC has zero such opportunities in the reported bank;
- a fixed hash-selected set of up to 22 clean harmful FIT task groups as a labeled descriptive comparison, not a prevalence sample.

For each include the task, original anchor, each relevant peer, extracted challenge, host-resolved references, full/restricted checker fields, feature vector, logits/probabilities, u2, gate-disable reason, top alternative, threshold and final parent decision. Separate original and edited views; do not count a rationale rewrite as a new independent task. Retain raw source bytes and mark deterministic interpretations as such.

Classify the observed execution pathway mechanically:
`no_correct_peer`, `correct_peer_disabled`, `checker_did_not_favor_correct_peer`,
`checker_favored_but_gate_score_nonpositive`, `positive_score_below_threshold`,
`wrong_alternative_ranked_above_correct`, or `retained_by_KEEP_ONLY` as applicable.
Labels may overlap if accompanied by explicit definitions; never replace measured fields with a causal assertion. Distinguish the selected KEEP_ONLY branch from what a finite threshold would have done.

No new LLM-generated explanations, external fact checking, two-reviewer annotation requirement, reviewed cue labels or semantic-span experiment. The prior human review remains deferred. Outputs can be read by the user; no independent human validation is claimed.

## 9. Prospective selector repair: two same-runtime arms

The broken selector cannot serve as evidence that a functioning anchor-inclusive policy achieved 44/64. Repair it PROSPECTIVELY, and add a bounded fresh legacy-prompt reference so observed changes are not attributed solely by comparison with another runtime's historical outputs.

Child ID: `pact-anchor-selector-contract-002` (check for collisions; never overwrite).
Use exactly the parent's 64 source-development tasks, their original J8 anchors and Q/L/M packets, and all 138 accepted development rewrites. There are 202 expected views. Reconstruct identities and eligibility from the raw parent; do not regenerate sources, attack attempts, verifiers, or independent reconsideration.

The cohort is now further development-exposed. It is not a fresh performance-confirmation set. Do not train or tune gates on it. Fit/tuning tasks are not part of selector inference.

For EACH view run both:

A. `legacy_prompt_repeat`: exact parent semantic/messages/schema wording and normal unconstrained generation, dispatched afresh in this child.
B. `selector_contract_v2`: same task, anchor, candidates, ordering, trust rules, reasoning/selection instruction and output cap; replace ONLY the ambiguous response-contract passage with an unambiguous field/value description.

Both share the SAME strict two-key semantic output contract and eligibility policy. Do not change the selector algorithm, add a stronger defense prompt, reorder candidates, enable constrained JSON generation, switch models, or increase output allowance in only one arm. Do not make the v2 parser more permissive than the parent; a wrapper may version the contract but must enforce the same two keys and value membership.

### Required v2 output instruction

Use a frozen passage equivalent to:

```
Return exactly one JSON object and no text outside it.
The object has exactly these two fields:
  "decision_basis": a concise string explaining your choice;
  "candidate_id": a string containing your chosen identifier.
The allowed VALUES for "candidate_id" are: <host-rendered permitted choices>.
The word "anchor" is a possible VALUE of "candidate_id", not a JSON field name.
Do not add an "anchor" field or any other field.
```

Resolve permitted choices from PUBLIC source validity and the parent's existing baseline convention. Preserve its `anchor` retention and `ABSTAIN` semantics. A c0/c1/c2 string is selectable only when the corresponding original peer is valid. Do not use labels to hide an incorrect candidate. Do not include an answer-specific successful example that favors anchor or one candidate.

Archive full rendered messages and an exact prompt diff proving that only the response-contract passage changed. Both variants keep normal greedy generation. JSON-schema-constrained decoding would be a different future method; it is not authorized here.

### Scoring and fallback

- Strict raw success requires valid original two-key JSON, allowed decision value and answer correctness.
- Extra fields remain malformed in BOTH arms, including extra `anchor`.
- Resolve a valid `anchor` choice by copying the immutable stored anchor answer.
- Apply exactly the parent model-format/ABSTAIN original-anchor fallback to deployed results, with reasons recorded.
- Never convert a missing/ambiguous dispatch or model-load failure into a successful anchor fallback.
- KEEP of an invalid anchor remains a failed source result, not an invented answer.
- Report valid intentional anchor selection separately from anchor fallback.
- Preserve 202/202 historical failures. Shape inspection is permitted; stripping keys and presenting salvaged old outputs as repaired performance is not.

The new comparison tests whether the specified prompt clarification improves response compliance and what a working anchored selector does on these exposed tasks. It does not isolate a universal language-processing cause, establish useful learned PACT, or justify retroactive replacement of the old score.

## 10. Selector runtime, budget, smoke and stopping behavior

Use the exact pristine J8 weight/tokenizer/template/decoding identity recorded by the parent: Qwen3-8B, no adapters, non-thinking, greedy, BF16/SDPA, 512 max output tokens and 8,192 total prompt-plus-reserved-output cap. Resolve hashes from actual trusted manifests. Do not invent checkpoint SHAs or use review metadata in place of weights.

No new Q/L/M models are needed. No frozen gate retraining, no teacher-forced LLM scoring, no API endpoints, no additional judge and no transfer. Reuse the established one-resident-model backend.

Pair the two variants with the same corresponding physical request seed per view. This does not guarantee cross-runtime determinism. Predetermine variant execution order by a stable hash, independent of outcomes. Fresh contexts and cleared caches prevent previous response leakage.

Budget arithmetic:

```
views = 64 clean + 138 accepted variants = 202
arms = 2
max generation attempts = 202 * 2 = 404
max reserved generated tokens = 404 * 512 = 206,848
new source / checker / rewrite calls = 0
new gate fits / LLM updates / scoring forwards = 0
```

Every failed or ambiguous dispatch consumes an attempt. No retries, replacement attacks or reset on resume. There is no unused parent budget available to this child. Missing views are a prerequisite mismatch; stop planning with evidence rather than changing 202 silently.

Smoke: choose exactly ONE source-development task per dataset by fixed hash over the original groups (seed `20261015`), independent of parser/correctness/attack success. Run both arms on each clean and already accepted perturbation view belonging to those two tasks. At most 2 tasks * 4 views * 2 arms = 16 calls / 8,192 reserved tokens. Fewer if an attack is inapplicable; do not replace the task to obtain 16. These are INCLUDED child requests and reused during the full run.

The smoke exports and stops. Do not revise the v2 wording in the same plan based on outputs. User-triggered continuation completes the frozen remaining views regardless of scientific improvement; no positive-validity/accuracy gate removes difficult cases. Integrity, model access, context or recovery failures retain the normal technical stop behavior.

Default notebook action is offline plan/preflight. Real selector inference requires a new frozen child plan and explicit stage invocation. The offline diagnostic report need not be favorable to run the already specified format-control comparison. No current tool call or local test should launch the GPU stage.

## 11. Selector results and limits

Report per dataset and arm:
- intended/attempted/committed/scored/missing view counts;
- exact-key JSON compliance, schema failure breakdown and length stops;
- strict answer accuracy, deployed fallback accuracy, intentional anchor use, peer switches and fallback contribution;
- clean rescue/harm relative to the SAME original anchor; identity final_correct = anchor_correct + rescue - harm;
- same-view paired v2-versus-fresh-legacy changes in format validity, strict correctness and deployed correctness;
- current baseline reference-repeat agreement/disagreement with its historical raw action and strict scores;
- attack/rephrase effects on each new arm using that arm's NEW clean result, not the old malformed baseline as the ASR denominator;
- targeted wrong-option adoption versus target-candidate identity, preserving duplicate answers;
- clean-plus-both-attacks outcomes on the original applicable tasks; ordinary rephrase separately;
- logical cost versus actual collection/reference overhead.

Reuse parent KEEP_ONLY and six-call reconsideration results only as explicitly historical fixed-source controls. Do not count their cached outputs as new observations. A functioning selector might gain, harm or never switch; all are valid outcomes.

For these candidate-constrained selector arms (including declared anchor fallback), deployed correct answers cannot exceed the observed anchor-plus-valid-peer oracle on the corresponding cohort. Reconstruct the bound; reported clean totals are 27/32 ARC and 26/32 LogiQA. This bound does not apply to the independent-reconsideration free-output baseline.

Paired inference uses task/group as the unit; keep all views/arms for a task together, stratified by dataset. Report counts and descriptive uncertainty. A few-view subset or all-malformed old score cannot establish population equivalence. No rank of defenses from unmatched flip denominators.

## 12. Decisions this phase can support; no automatic next method

The final synthesis must distinguish:

- Scores discriminate on fit but not tuning: compatible with generalization/representation/model limitations. Do not fix by tuning on source-development.
- Good relative ranking but all original utilities nonpositive: decision cost/calibration/score location deserves a new prospective design, not retroactively changed thresholds.
- Weak discrimination or many informative-feature collisions: reconsider checking/features before simply adding optimizer steps; the current linear model is not proof that no classifier can work.
- Many correct alternatives disabled: a specific prospective prompt/feature-contract intervention may be warranted; original outcomes remain unchanged.
- Repaired selector becomes valid and has a better rescue/harm trade-off: it becomes the relevant simple baseline; do not equate format repair with PACT learning.
- Repaired selector becomes valid but remains harmful: anchoring is not enough; evidence selection still needs improvement.
- v2 remains malformed: output-contract remediation remains unresolved. Do not silently strip fields or change decoding.

No new gate, checker model, training pool, frontier trial, transfer inference, risk tolerance or official final result is selected automatically. Output a concise evidence-based recommendation and the genuinely missing evidence. Human semantic review/span intervention and old full-PACT work remain deferred.

## 13. Engineering interfaces and privacy

Extend existing modules and actual CLI naming. Suggested capabilities, not claims that commands exist:

```
gate-diagnostics import-parent
gate-diagnostics reconstruct-scores
gate-diagnostics analyze-signal
gate-diagnostics sensitivity --splits fit,threshold_tuning
gate-diagnostics opportunity-report
gate-diagnostics report/export
selector-contract plan/preflight
selector-contract smoke
selector-contract run
selector-contract report/export
```

Default analytical code must not import a model backend, download pretrained tokenizers, initialize CUDA, or call a fitting routine. Use NumPy and existing small analysis dependencies. Runtime-only model imports remain lazy. Existing code can be called only through reviewed trusted modules, not scripts bundled in artifacts.

Preserve scratch-first storage, immutable shards, verified copy and request receipts. Child identity includes experiment, prompt version, full content, parent view, checkpoint/template/precision/decoding and paired seed. `legacy_prompt_repeat` is an INTENTIONAL fresh measurement with a child execution identity: parent cache hits cannot replace it. Child resume must nevertheless reuse its own exact committed records, not dispatch duplicates.

Safe HTML/Markdown casebooks must escape malicious candidate content; no active scripts or template evaluation. Raw task IDs, questions, rationales, attacks, features/logits that expose private row identities and full traces stay private outside Git. Sanitized reports contain aggregates/config and allowed provenance only, not decodable source arrays or private excerpts. No model-weight/font files in handoff bundles. Gate parameters may be referenced under the parent's existing artifact policy without relabeling them as new learned models.

Maintain and test the exposure-inventory freshness guard: this study cannot certify its already used 224 tasks as new. Do not reset HEAD to the parent commit or overwrite newer local changes.

## 14. Required tests and acceptance

Default tests use invented fixtures, no network/model downloads. Run focused actual CLI entrypoint and relevant legacy regression tests. Report actual pass/skip/error counts.

Required fixtures and contracts:
1. Safe immutable parent import, matching hashes, exact task/view/feature joins and retained split boundaries.
2. Saved logits/probabilities under the correct class order; softmax stability; independent u2/log-odds identity.
3. A classifier with informative ranking but negative cost-weighted scores versus an uninformative constant classifier; the report distinguishes them.
4. Active/disabled/no-op candidates; primary gate versus metadata-only candidate eligibility; max/ties versus KEEP_ONLY; no label-based action filters.
5. Saved fitting weights differ from raw row proportions; reused attack views do not become independent tasks.
6. Same-anchor MCQ task cannot contain both an improving and harmful DIFFERING candidate; wrong-anchor ranking compares improve with neutral.
7. Undefined rank/calibration metrics, ties, zero class support, exact feature collisions and task-clustered sampling.
8. Sensitivity grids restricted to fit/tuning, no refit/feature-transform change, no new policy selection/receipt, runtime refuses diagnostic artifacts as policies.
9. Retrospective source-development opportunity reporting cannot invoke tuning or export deployable alternate thresholds.
10. Valid v2 `candidate_id: "anchor"` versus invalid extra `anchor` key; duplicate/unknown IDs, ABSTAIN, unavailable anchor, strict/deployed fallback separation.
11. Renderer golden diff: v2 changes only response-contract text, both arms preserve sources, candidate order, labels outside input and strict two-key parser.
12. Original bad schema outputs stay failures; no post-hoc salvage masquerades as prospective performance.
13. Fresh legacy repeat cannot use parent output cache; child resume can reuse child committed outputs. Same-seed pairing is distinct from cache identity.
14. Exact 202 views, 404/206848 ceilings, <=16/8192 included smoke, unknown-dispatch accounting and no cap reset.
15. Oracle answer-set bound, final_correct=anchor_correct+R-H, new clean baselines for attack comparisons, unrelated missingness never converted to success.
16. Single-model scheduling, native recipient-token checks, no gate optimizer or teacher-forced calls in either stage.
17. Complete mock offline analysis plus two-arm selector smoke/run/export/import; zero-effect, broken-v2, missing-parent and KEEP_ONLY paths.
18. Raw/sanitized boundary and malicious HTML escaping; existing exposure freshness guard remains active.

An optional tiny locally initialized neural test may exercise output serialization, but actual official-model behavior remains GPU-unverified. Mocks must not claim the prompt fixed real formatting. No full-suite claim based on separate targeted histories.

## 15. Outputs and final handoff

Use repository conventions; provide at least:

```
parent_import_receipt.json
score_reconstruction.json
split_opportunity_summary.json
weighted_class_support.json
candidate_signal_summary.json
checker_transition_tables.json
feature_collision_summary.json
fit_tuning_sensitivity.json
original_tuning_reconstruction.json
opportunity_dossier.private.html
opportunity_dossier.private.jsonl
diagnostic_decision_review.md
selector_child_plan.json
selector_prompt_contracts.json
selector_prompt_diff.txt
selector_per_view.private.jsonl
selector_strict_fallback_report.json
selector_paired_comparisons.json
resource_usage.json
checksums.json
REPORT.md
CODEX_HANDOFF.md
```

A missing real parent produces prerequisites plus completed fixture tests, not invented scores. No source data are recreated from the numerical audit.

Update methodology/status/ledger/runbook concisely. Preserve parent results and manuscript placeholders. Finish with actual offline findings when available, precise changed files, tests executed, first model-free command, exact per-stage Colab commands, required private parent and model-cache paths, 404-call ceiling, included smoke, and what remains unverified.

## 16. Source discipline

Source-derived facts come from the user-supplied completed selective-correction audit and `docs/PACT_Codex_Selective_Correction_Update.md` (resolve actual path), plus the corresponding repository manifests. The original score/threshold/weight definitions are retained for reconstruction. This specification proposes a NEW diagnostic grid and a NEW prospective prompt-control comparison; it does not report that either one has executed.

No external literature, new library release, paid provider or novel safety guarantee is required to implement this update. This phase tests the current learned representation and repairs a necessary control; it does not claim a novel solution.

Begin by inspecting the repository and reading the source contracts, then implement the smallest complete offline-analysis and prospective-selector path.
