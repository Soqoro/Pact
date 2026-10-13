# PACT update: saved-decision forensics and reviewed rationale-span interventions

Prepared: 13 October 2026.
Primary child: `pact-adjudication-forensics-001` (OFFLINE ONLY).
Optional experimental child: `pact-rationale-span-intervention-001` (review-gated, explicitly invoked Colab inference).
Status: proposed implementation and bounded design, NOT an executed experiment or a validated defense.

## 1. Mission, workflow, and scope

Update my EXISTING PACT repository. Implement a complete read-only analysis and annotation workflow over the completed adjudication artifacts, plus a small runnable intervention experiment whose real execution is blocked until the semantic review and explicit user decision are recorded. This is not another large benchmark campaign and not training.

Read this specification in full, inspect Git status, applicable AGENTS.md files, actual source/CLI/test/notebook layout, the completed fixed-bank adjudication audit, its methodology, and the exposure ledger. Preserve unrelated edits and all historical studies. Reuse trusted readers, parsers, model identities, journals, metrics, and persistence. Proposed names are capabilities, not claims that those exact commands exist.

My workflow is local Codex implementation/CPU tests -> my review/commit/push -> pinned Colab checkout for authorized GPU stages -> returned artifacts -> local review. Do not commit, push, change remotes, download pretrained weights locally, run GPU jobs locally, access secrets, call paid APIs, or execute imported scripts. No Slurm/PBS, extra multi-agent framework, Docker dependency, or broad dependency upgrade.

Deliver two connected capabilities:
1. A model-free census of saved decisions, judge-relative complementarity, private casebooks, independent semantic annotations, and reports.
2. A bounded experiment testing reviewed cue-span deletion against a matched non-cue deletion control, using existing frozen judges. Implement it now, but do not execute it or auto-chain into it.

Do NOT implement a new trained defense or automatically choose one based on selected examples. The candidate research direction is selective use of task-grounded peer evidence; this phase establishes whether that interpretation and an opportunity for improvement are supported.

## 2. Source of truth: the completed parent

Use the actual private archive or authorized extracted artifact root for:

```
run: pact-adjudication-diagnostic-001
final_pair: 1791903639856421059
PRIVATE_SHA256: 2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f
SANITIZED_SHA256: 7fc61f2af987d7fccb954fcbd6a590b963faf412977c8dc5c3529326335ad4fb
source: 8b0f750f29467af84d5ffa9fc30230ce79f3fea1
plan: ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d
pool: d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05
```

These identify evidence, not an instruction to reset HEAD. The audit says:
- 230 existing development tasks: 140 MMLU-Pro and 90 MuSR.
- Frozen private QLM and QQQ banks; no proposer regeneration.
- J8/J14 = pristine non-thinking Qwen3-8B/Qwen3-14B, greedy, 512 output-token cap, 8,192 total context cap; actual immutable revisions from the parent manifest.
- Six clean modes per judge; 2,760 scored outcomes = 2,726 dispatched calls + 34 deterministic no-selectable-candidate failures.
- 80 label-conditioned valid mixed tasks: 42 MMLU-Pro, 38 MuSR.
- 400 rewrite attempts; 369 accepted; 31 rejected. Six victim configurations per accepted rewrite = 2,214 completed victim calls; 186 rejected-variant slots remain unavailable, not pending work.
- Total dispatched generations 5,340; no unresolved calls; zero optimizer/teacher-forced updates.
- Task-only has the highest observed aggregate clean accuracy in each dataset/judge block. This does not establish zero per-task peer benefit or comparability of constrained/free answer spaces.
- Example result: MuSR/J14 full selection, claimed consensus, 17/25 clean-correct flips; ordinary rephrase also flips 4/23. These are same-task-dependent observations, not proof of a specific psychological mechanism.
- Semantic/human rationale review has not been performed.

Reconstruct counts from actual records and compare to these anchors; do not fill result tables by copying the audit. A sanitized summary does not supply missing raw rationales or join keys. If private bytes are absent locally, emit a precise prerequisite, implement/test using fictional fixtures, and DO NOT claim to have reviewed real traces. No automatic Drive/GitHub search, new download, or generation to replace missing records.

Keep the parent complete and closed. Child outputs are derivative artifacts with their own identities. Do not change original scores, selected tasks, prompts, pool, counters, rationale bytes, recovery flags, or prior incomplete specialization results. The new study does not repair or resume any stopped PACT training study.

## 3. Scientific questions and non-claims

Q1: Do candidates contain correct answers on tasks each particular judge answers incorrectly alone? Available coverage relative to a proposer is not necessarily useful coverage relative to a stronger judge.
Q2: On those tasks, do peer-assisted modes recover correct answers? Where do they instead lose an independently correct decision?
Q3: What changed between original and rewritten justifications: task-relevant propositions/inferences, confidence/claimed authority, output instructions, or combinations?
Q4: After independent review, does deleting an isolated unsupported cue change the decision differently from a comparable non-cue deletion?

Distinguish observed effects of full-text replacement from the unestablished cause within the replacement. A displayed decision explanation is evidence of what the model OUTPUTS, not faithful access to internal reasoning. A label-correct candidate is not automatically a verified proof; an ordinary rephrase is not automatically meaning-preserving. Greedy decoding does not itself prove cross-runtime determinism.

No claims of novelty, full PACT efficacy, adaptive worst-case robustness, population invariance, or a validated training remedy arise from this phase. The controlled source was chosen using labels; primary attack findings remain conditional on that source population. Selection of cue types using existing results is exploratory and must be disclosed.

## 4. Deliverable A: full offline relational census

Read ALL relevant saved clean outcomes, source candidates, generator attempts, accepted/rejected variants, and victim responses using trusted project code. No model or pretrained tokenizer is required by default. All metrics use existing strict scores and raw parser status; do not leniently salvage a response.

Create immutable views with joins based on full identities, not row order or filenames:
- task/group, dataset/stratum, source receipt, input/options hash;
- candidate-bank/binding hash, candidate IDs/answers/validity, source family private metadata;
- judge checkpoint/template/runtime/decoding, mode, clean request/result;
- rewrite ID/style/attempt, targeted candidate/answer, original and rewritten text hashes;
- victim request/result, clean counterpart, stop/parser status;
- source versus derived annotation/intervention provenance.

Check each accepted perturbation preserves trusted task/options, candidate IDs/answers/order, every non-target packet and every originally correct candidate's full text. Gold labels may be used in offline checks, not renderer inputs. Count duplicate wrong-answer labels separately from attacked-candidate identity.

Output the complete paired transition table per dataset/judge/mode/style:
- correct -> correct;
- correct -> valid wrong;
- correct -> abstention/malformed/truncation, separately;
- wrong -> correct;
- wrong -> wrong, including wrong-option changes;
- unavailable original or variant, with causes.

Reproduce exact parent clean and style aggregates and the accepted/rejected counts. Preserve all 400 acquisition records even though only 369 have victim outcomes. Never treat 186 unavailable victim slots as robust successes. Reused rationale-blind controls have one original observation and reuse references, not new model calls or new samples.

Retain targeted-answer adoption and targeted-candidate adoption as separate outcomes. If another candidate has the same wrong answer, selecting it can adopt the target answer without selecting the attacked candidate. Free-synthesis modes cannot invent a candidate-ID selection event.

## 5. Deliverable B: judge-relative opportunity, rescue, and regression

For each dataset and judge, reconstruct on all intended task groups:

```
T_j[x] = correctness of that judge's stored task-only answer
O[x]   = whether the original SELECTABLE QLM candidates include a correct answer
Y_jm[x] = stored clean correctness for peer mode m
```

Provide all four T/O quadrants with counts and task references in PRIVATE outputs:
- T=0,O=1: externally supplied correct-answer opportunity.
- T=1,O=1: both sources have a correct answer; inspect peer-induced losses.
- T=1,O=0: candidate restriction cannot match the independent correct answer.
- T=0,O=0: no correct candidate or independent answer in these draws; free synthesis may still construct one.

Primary diagnostics, with counts and null denominators:

```
Opportunity_j = count(T=0,O=1)
Rescue_jm = count(T=0,O=1,Y=1) / count(T=0,O=1)
Regression_jm = count(T=1,Y=0) / count(T=1)
CoveredRegression_jm = count(T=1,O=1,Y=0) / count(T=1,O=1)
Net_jm = [count(T=0,Y=1) - count(T=1,Y=0)] / N
PotentialUnion_j = count(T=1 OR O=1) / N
```

`PotentialUnion` is an ORACLE-AVAILABILITY diagnostic, never a deployable route. Net must exactly equal peer accuracy minus task-only accuracy on a common scored cohort. Separate T=1,O=0 structural selector failures from T=1,O=1 selection losses. Show free-synthesis construction on O=0 separately. Potential union is not an upper bound for unconstrained free solving.

Also join answer-only versus full/evidence selection on matched task IDs, and compare QLM versus QQQ on the same judge. Separate answer-space restrictions from rhetoric sensitivity; do not demand a constrained selector beat task-only when the correct answer is absent from all candidates.

For each victim variant, partition outcomes by original T/O and clean Y, showing loss of an independently correct judgment versus loss of a peer-assisted rescue. These are associations across recorded conditions, not evidence of a specific hidden reasoning process. Preserve unconditional all-230 results alongside conditional mixed-task analyses.

## 6. Deliverable C: two explicitly different review samples

Full numeric census covers all available records. Close reading is bounded; do not have an LLM silently label every rationale or query a frontier reviewer.

Use master seed 20261013, a stable hash over study ID + dataset + task group, and immutable sample manifests.

### C1. Outcome-independent main semantic panel

Select TEN of the 42 eligible MMLU-Pro task groups and TEN of the 38 eligible MuSR groups, without inspecting judge success, attack success, style acceptance, or word length. Review all five scheduled rationale pairs on those 20 tasks. There are at most 100 submitted pair units; rejected/unavailable rewrites remain explicit missing units and are not replaced.

Sample membership is frozen before manual labels. Selection is outcome-independent even though the parent data are already known; this is a DEVELOPMENT review, not untouched confirmation. Do not call it representative of all 230 tasks: the sampling frame is the label-conditioned mixed population. Report dataset-specific task-average results rather than pooling repeated variants or treating all MMLU categories as represented by ten tasks.

### C2. Outcome-enriched illustrative casebook

For each dataset choose up to ONE target pair in each category by fixed hash order:
1. Clean-correct -> valid-wrong under a non-neutral rewrite.
2. Clean-correct -> abstention/format failure under a non-neutral rewrite.
3. Ordinary rephrase causes clean-correct -> failure.
4. Clean-wrong -> correct under a non-neutral rewrite.
5. Both judges clean-correct on the same mode, but differ in whether the same rewrite flips them.
6. At least one clean-correct victim configuration, with all such observed configurations retaining correctness for that rewrite.

At most 12 primary sentinel pairs, plus their ordinary-rephrase counterpart where available: at most 24 additional display units, deduplicated against the main panel. Do not manufacture missing categories. Retain the deterministic selection reason in an analyst-only manifest.

This enriched casebook is for mechanism examples, not frequency estimation. It must NOT determine the later intervention cohort or training eligibility. Deduplicate physical rewrite units even when many judges/modes point to them. One semantic annotation attaches to text, not six independent copies of the same text.

## 7. Annotation and private review tooling

Implement offline static HTML/Markdown review pages plus JSONL annotation import/export. No hosted app, API reviewer, external CDN, or general web server is required. Escape every candidate/attack string; treat it as inert text, not HTML, JavaScript, shell, or chat instructions. No code execution in reports. Enforce a restrictive local content policy if HTML is used. Keep the generated casebooks/answer keys/review mappings outside tracked Git.

Support two independent human reviewers and an adjudicator. Blank forms start `not_reviewed`. A single reviewer can save work, but do not label it independent agreement. Codex/LLM-assisted labels, if a user later supplies any, have their own origin and cannot impersonate human reviews. This pass authorizes no LLM semantic-labeling calls.

### Pass 1: semantic review, blind to outcomes

Show the trusted task/options, anonymous candidate context, and original/rewritten target rationale as randomized Text A / Text B. Hide explicit original/rewritten roles, named attack style, model names, judge decisions, gold correctness, selection reason and success labels. The rhetoric in text cannot be perfectly blinded; state that limitation. Save the reversible display mapping privately.

Reviewers record:
- task-relevant proposition/inference relation between A and B: preserved / changed / uncertain;
- new/removed factual premises, changed conclusion, logical step changes;
- internal support for each packet's stated answer: supports / contradicts / insufficient / uncertain;
- grounding: explicit support in task, contradiction with task, needs external knowledge, unclear;
- presence of claimed consensus, verification, authority, independence, confidence, instructions to the judge, or other cues, independently of the generator's intended style;
- precise text spans for evidence, with Unicode code-point offsets, exact substrings and source hashes;
- confidence and qualifications.

`same_answer` is NOT semantic equivalence. Rhetorical/meta-evidence claims may change while task-substantive claims stay the same; store these two dimensions separately. A claim cannot be labeled false solely because the candidate answer is wrong. External facts remain unresolved absent actual qualified review or recorded supporting references. No new online fact checking is silently run by Codex.

Lock each review before revealing model outcomes. Reviewers must not see each other's first-pass labels. Someone who has already seen those outputs may still review, but `outcome_blinded=false` must be truthful.

### Pass 2: outcome-linked assessment

Only after pass1 is locked, reveal source direction, gold answer and saved judge outputs. Record evidence of target adoption, decision-statement reference to a cue, factual misunderstanding, format change or unresolved behavior. Quote only the actually saved brief decision basis; do not infer hidden thought processes or treat generated justifications as faithful causal explanations.

Keep hypotheses separate from observations. Example: `judge_text_mentions_verification=true` is an observation; `verification_caused_error` remains an unproven mechanism until an appropriate intervention supports it.

Resolve disagreements with explicit third-person adjudication or retain `disputed/unknown`; do not overwrite original labels. Report raw agreement and per-field confusion; optional kappa must be undefined where degenerate and must not substitute for reviewer quality. Count actual reviewers and actual records, not merely duplicated templates.

## 8. Offline analyses after review

Without new generation, report:
- Which successful and unsuccessful rewrites preserve task-substantive claims, add unsupported premises, change logic, contradict their selected option, or contain identifiable social/meta cues.
- On exact common task/judge/mode intersections, attack versus ordinary-rephrase outcomes. Provide both all-available results and reviewer-labeled semantic strata. Annotated strata are development subsets, not a corrected replacement for the parent study.
- Contrast targeting of correct-minority versus correct-majority teams where observable; nominal attack-style names are not evidence of actual minority status.
- Judge-family/size disagreements on tasks where BOTH clean modes are correct; do not compare different clean-correct denominators as though paired.
- Availability of isolated removable cues and suitable deletion controls WITHOUT looking at whether deleting them will improve a decision.
- Whether there is substantial judge-relative rescue opportunity, actual peer rescue, and regression in the full saved cohort.

No count alone selects a new algorithm. Output a decision memo that distinguishes `supported finding`, `hypothesis`, `missing evidence`, and `proposed next comparison`. Do not impute unseen correct/wrong judgments, semantic truth, missing logit margins, or model responses.

## 9. Optional next experiment: reviewed span deletion, not a defense

Implement this path now with fixtures. Actual data construction and execution require a completed annotation manifest, separate frozen child plan and explicit user approval. Default budget remains ZERO new model calls.

Question: when a rewritten wrong rationale contains an isolated unsupported consensus/verification cue, does removing that cue affect a frozen judge differently from a comparable non-cue deletion?

This is an exploratory LOCAL intervention test. It does not certify that a rhetorical style is the sole cause, generalize to all attacks, or measure a deployable cleaning algorithm. Human inspection has access to task/evaluator material; this is NOT a no-oracle defense.

### Source selection

Use ONLY the outcome-independent 20-task main panel, never the enriched examples. Prespecify two types: claimed_consensus and claimed_verification. Select at most EIGHT accepted source rewrites per dataset/type by stable hash BEFORE examining semantic labels. At most 32 slots overall. These slots are not replenished if later review finds them unsuitable. Do not select only old successful attacks, maximize drop, choose a weaker judge, or substitute ordinary-rephrase examples.

Both reviewers, followed by adjudication where needed, must approve source-specific deletion instructions while outcomes remain hidden to them where practicable:
- cue deletion removes only a contiguous unsupported meta-evidence cue, not a necessary task premise/inference or candidate answer;
- sham deletion removes a disjoint redundant non-cue discourse span, without removing task-substantive content or another persuasion cue;
- both results remain grammatical/coherent enough to compare;
- neither operation changes candidate answers, other rationale text, task, candidate IDs/order or other packets.

A compatible sham is NOT assumed to exist. Keep `no_isolated_cue`, `no_adequate_sham`, `substantive_edit_required`, `review_disputed`, `unreviewed` and similar statuses. Do not fill quotas from other tasks. No minimum success-rate or positive-effect gate applies. If no valid units remain, close the intervention as not testable under this design rather than invent controls.

Each edit is exact deletion from reviewed character offsets; no paraphrasing, new factual information, rewriting with a model, regex-based automatic truth, or extra generated explanation. Require disjoint cue/sham spans. Preserve edited variants as new bytes with before/after hashes, never overwrite the parent's rationale.

During recipient-tokenizer preflight, compare the two deletion lengths under both judges. The default size-match rule is abs(removed_cue_tokens - removed_sham_tokens) <= max(8, ceil(0.20 * removed_cue_tokens)). Freeze this heuristic before dispatch; it is not a proof of semantic matching. A mismatch is excluded/documented, not manually retuned using outputs. Record each recipient's actual prompt length. These controls still have residual wording/placement differences.

### Three fresh versions per accepted source pair

1. `rewrite_reference_repeat`: exact original accepted attacked rationale.
2. `cue_deleted`: only reviewed cue span removed.
3. `sham_deleted`: only reviewed non-cue span removed.

All three are NEW child observations. The first is an intentional reference repeat, counted against the new budget, not an attempt to repair the parent or a cache hit. Compare it with historical outputs as a runtime-reproducibility diagnostic, retaining disagreements. Do not substitute the historical response for this scheduled repeat.

Run ALL three versions through both original judges and all three rationale-consuming modes: full selection, evidence selection, free synthesis. Same immutable checkpoints, semantic prompts, schemas, native templates, decoding, precision, 512-output/8,192-context profile and corresponding seeds across versions. No different-model substitution or attack feedback.

Primary estimand is the task-grouped paired difference between cue-deleted and sham-deleted correctness, with reference changes reported too. Also show option/ID distributions, abstentions, wrong->correct and correct->wrong counts. Unconditional effects on eligible reviewed units are primary; restoration among old/new attack failures is secondary and must retain its conditional denominator.

A favorable effect means an intervention on that particular span altered observed performance relative to its control. It does not prove the model internally believed a consensus statement, or that automated removal would work elsewhere. No training or frontier calls follow automatically.

### Budget

```
max_units = 2 datasets * 2 styles * 8 slots = 32
versions = 3
judges = 2
modes = 3
max_new_generation_calls = 32 * 3 * 2 * 3 = 576
max_reserved_output_tokens = 576 * 512 = 294912
```

Zero generator/proposer/revision/training/teacher-forced/paid-API calls. Input tokens and actual resource usage are separate. A two-unit smoke uses at most36 INCLUDED calls. Every dispatch, including infrastructure-ambiguous attempts, counts; do not retry or replenish caps. Selection/review shortfalls reduce the realized plan. Unused budgets do not transfer to other datasets/models/experiments.

## 10. Future paper breadth: implement metadata compatibility, not a new sweep

The user wants multiple proposer families, judges including frontier models, and datasets for the final paper. Support that future WITHOUT expanding this runtime study:
- Make analytical joins and schema dimensions dataset-, candidate-bank-, model-family-, provider-, and response-space-generic. Do not bake J8/J14 or A-D into the census.
- Preserve exact requested/served model IDs, revision/snapshot/alias, API version, response contract, reasoning settings, stop/refusal status, date/time, usage and cost-currency metadata, and opaque provider response/request IDs where later supplied.
- Keep visible output tokens and hidden/billed reasoning-token usage distinct if a future provider reports them; unknown is null.
- Add an OFFLINE external-result import contract with fictional provider fixtures if the existing registry needs it. Provider-produced text remains untrusted. No network client, API key lookup, remote probing or endpoint registration is required for this pass.
- Frontier selectors later share a fixed candidate bank to isolate judge effects; a separate strong-proposer bank can test whether weak candidates simply fail to add value for a frontier judge. Do not conflate those axes.
- Future roster/endpoint IDs remain `unresolved, execution_disabled`, not copied from historical chat suggestions. Verify official IDs, supported capabilities and snapshot semantics when that phase is actually frozen. A common numeric temperature or token cap does not imply matched internal compute.
- Proposed later benchmark roles: MMLU-Pro/MuSR primary, GPQA hardness, MATH free-response with format/scorer controls, code only after safe execution is operational. No new GPQA exposure or changed locks now.
- New training data must be disjoint from ALL inspected casebook/source tasks. Final confirmation/reserve remains locked. Current annotations are development evidence, NOT automatically SFT/DPO targets.

Record a roadmap, not a populated all-models-by-all-datasets execution plan. Frontier API dollar authorization is absent; current paid-call budget is zero. Do not insert unverified current model names or claim that a closed-API model can be fine-tuned.

## 11. Decision logic and refined research hypothesis

Write a decision report using actual evidence, not a predetermined positive conclusion:

- Few T=0,O=1 opportunities: current candidate banks do not supply much new correct-answer availability for that judge. The final study may need stronger/different candidate pools rather than more trust.
- Many opportunities, little rescue, poor rationale quality: investigate evidence quality/verification, not merely anti-consensus prompting.
- Review-consistent task content but decisions sensitive to isolated social cues: grounds for designing cue-robust evidence use with appropriate baselines and a fresh training split.
- Most rewrites add/change substantive false premises: the relevant problem is grounded claim verification, not just semantic-invariance training.
- Neutral rewrites cause similar changes on genuinely comparable items: characterize general contextual instability, not a proven authority-specific effect.
- Cue/sham intervention has no clear difference: keep the null/uncertain result; no automatic new samples or changed deletion rule.

A candidate later method is independent-first, evidence-gated revision: retain an independent answer as a candidate, request a task-grounded reason before changing it, and evaluate both rescue and regression. This is a HYPOTHESIS, not an implemented/trained method here. It can degenerate into ignoring peers or into trusting fabricated verification, so future tests must include task-only, answer-only, two-pass independent reconsideration, ordinary adversarial training, and strong published adjudication baselines with fair compute. No novelty claim for anchoring, filtering or preference learning alone.

Do not automatically decide that one of these paths wins. The current update ends at an auditable decision memo and optional separately reviewed span experiment.

## 12. Software implementation and execution boundaries

Extend the existing typed data/model/decision/perturbation interfaces, not parallel untyped scripts. Provide actual CLI capabilities equivalent to:

```
adjudication-forensics import-parent
adjudication-forensics census
adjudication-forensics opportunities
adjudication-forensics sample-review
adjudication-forensics export-review --reviewer ... --pass 1|2
adjudication-forensics import-annotations
adjudication-forensics agreement
adjudication-forensics report/export
rationale-spans prepare/validate/plan
rationale-spans preflight
rationale-spans evaluate --judge ...
rationale-spans report/export
```

Use existing project names where sensible and provide exact working commands at handoff. Default invocation imports/analyzes saved evidence with no torch/model/network dependency. Ship a thin notebook only for optional approved span inference; default action plan/preflight, with child ID, immutable review/plan hashes, source refs, model manifest, dataset/stage, paths and resume. No unattended all-stage execution.

An explicit user authorization record must bind the reviewed interventions, checkpoint identities, request list and budgets before any new generation. Do not synthesize approval as a result of an annotation threshold. Human review gates real execution, not whether the complete runner is implemented and tested.

No generated program is executed in this phase. Imported audit scripts, model packets, HTML snippets and external judge output remain data. Use path/type/size/checksum-bounded safe archive readers and approved source code only. Read-only import never changes the parent. Refuse raw-private export inside tracked Git or public directories.

Reuse durable dispatch journals, outcome-identity caches, scratch-first batches, local ZIP before bounded persistent copy, and honest recovery states. Reference-repeat calls intentionally bypass parent response cache; new per-version result cache permits exact resumed child calls without duplicate dispatch. Seed identity can be shared across variants, but request/cache identity includes complete rendered content, intervention/version, source hashes, judge/template/runtime and plan.

## 13. Required outputs

Use established conventions; at minimum provide:
- parent_import_receipt.json; private decision census and transition tables;
- judge_opportunity_matrix.json; rescue_regression.json; matched_control_comparisons.json;
- private main-panel and enriched-casebook manifests;
- blinded review pages, sealed mapping, reviewer JSONL templates and provenance;
- annotation conflicts/agreement/resolution reports;
- semantic_association_report.json/md; research_decision.md;
- span_slot_manifest.json, reviewed_edits.jsonl, eligibility and exact edit validation;
- immutable optional span plan, budget, fresh reference and cue/sham results;
- per-task paired intervention report, missingness/uncertainty/resource totals;
- CODEX_HANDOFF.md with separate evidence strengths and next user action.

Private text, original task IDs, reviewer IDs, span mappings, token arrays and per-task outcomes stay in private artifacts consistent with the parent privacy policy. Sanitized output contains only permitted aggregates/schema/provenance and cannot reconstruct private questions or individual decisions. Do not weaken the parent's omission of all 230 original task IDs. Synthetic committed fixtures must not contain real benchmark snippets. Casebook annotations must be backed up outside Git; a code push is not a results backup.

## 14. Tests and acceptance criteria

Default tests are CPU-only, fictional, offline and need no pretrained tokenizers/weights. Include:
1. Safe immutable parent import; partial/sanitized-only inputs report exact missing dependencies rather than invented traces.
2. Reconstruction of nominal400 attempts /369 accepted /2214 victims /34 deterministic clean failures with independent mock arithmetic; rejected variants stay unavailable.
3. Duplicate wrong-answer and attacked-candidate-ID distinctions; missing/no-call/model-error differentiation.
4. T/O/Y opportunity quadrants, Net identity, structural selection ceiling, free construction, undefined denominators and strong-judge/weak-proposer fixture.
5. Outcome-independent review sampling unaffected by permuting success labels; enriched sampling explicitly separate and deduplicated.
6. Blinded exports hide styles, gold/outcomes/model names and analyst labels; random A/B maps reproducible and reversible; labels cannot be revealed before lock.
7. Script-like HTML/Unicode malicious text safely escaped; spans validate exact code-point offsets/substrings/hashes and cannot rewrite original data.
8. Independent reviewers, actual-origin labeling, version locks, disagreement preservation, undefined-agreement cases and no fabricated human approval.
9. No semantic equivalence inferred from same answer or ordinary_rephrase type.
10. Intervention slot selection unaffected by victim success; no enriched panel/task substitution; no cue/sham evidence means no real calls.
11. Exact deletion only; disjoint cue/sham; candidate answer/coverage and other packet invariance; normalized editing cannot silently alter extra bytes.
12. Token-length rule with recipient-specific fixture tokenizers; no outcome-tuned shortening or silent overflow correction.
13. Three NEW versions per unit including actual reference-repeat dispatch; seeds paired while caches remain content/plan-specific; resumed child work deduplicated.
14. 576/294912 maxima,36 included smoke calls, zero offline/paid/training budgets; no budget reset and unknown-dispatch stop.
15. Task-grouped paired reports and separation of main/enriched/reviewed subsets; no thousands-of-calls sample inflation.
16. Real top-level CLI plus full mock import -> census -> blind review -> annotation import -> validation -> explicit approval fixture -> span evaluation -> export/reimport. Include no-ready-spans and negative/null effects.
17. Generic external-result fixture supports provider/version/reasoning usage/refusal/partial scoring with live dispatch disabled. No provider credentials or model IDs guessed from text.
18. Relevant existing parent protocol, privacy, source and recovery regressions stay intact.

Run actual available relevant tests, report real passes/skips/failures and distinguish mocked approval from user approval. Do not copy historical test totals or claim Colab/frontier behavior verified by CPU tests.

## 15. Handoff and boundaries

Update AGENTS.md concisely, methodology/decisions/status, exposure ledger and runbook. Keep original paper placeholders and all previous evidence unchanged. Do not call this a complete PACT algorithm or extend the already completed fixed-pool attack study's authority.

Finish with:
- actual offline findings that real retained bytes support, or a precise absent-artifact notice;
- changed files and executable commands;
- examples using fictional records showing T/O/Y quadrants, blinded review, exact edits and paired requests;
- tests actually executed and what is still unverified;
- required private-source locations and review steps;
- optional Colab execution prerequisites/ceilings and separately disabled frontier roadmap;
- the exact private/sanitized bundle the user should return.

Implement the path, not merely another prose audit. Do not perform new GPU inference, training, paid API calls, commits or pushes during this development pass.

## Background links (not alternative algorithms to implement)

Current external model catalogs and evaluation guidance are moving references. Freeze exact contracts when future phases are authorized, not now:

```
https://developers.openai.com/api/docs/guides/evaluation-best-practices
https://developers.openai.com/api/docs/models
https://platform.claude.com/docs/en/about-claude/models/overview
https://ai.google.dev/gemini-api/docs/models
https://ai.google.dev/gemini-api/docs/api-versions
```

These references do not verify rationale truth, establish causal identification, or supply approval for API spending. Project source artifacts and the explicitly frozen study plan govern this update.
