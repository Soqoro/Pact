# PACT next phase: from observed flips to a testable mechanism

Prepared: 13 October 2026. Proposed design only; no new model work executed.

## Decision

Complete saved-decision forensics first. Implement a small reviewed span-intervention experiment so it can run after the user reviews the casebook. Do not start a new large evaluation matrix, training recipe, or frontier-API campaign yet.

The refined hypothesis is: a useful decision policy must accept task-grounded corrections while resisting unsupported assertions of reliability. This is stronger than 'trust the minority' or 'ignore peer explanations.' It also needs demonstrated headroom: peers must sometimes supply correct answers the judge misses alone.

## What the current evidence says

The completed `pact-adjudication-diagnostic-001` audit reports 230 development tasks, 400 rewrite attempts, 369 accepted rewrites, six victim configurations per accepted rewrite, and 5,340 total dispatched calls. No training occurred. Task-only has the highest observed aggregate score in every clean block, and some rationale edits overturn correct decisions even though correct candidate packets remain intact. Ordinary rephrases also cause changes, and semantic review has not yet been performed.

Those facts motivate this phase. They do not establish an authority-specific causal mechanism, the adequacy of correct candidates' explanations, or a successful PACT defense.

## A. Full offline census — zero new model calls

Read the actual private artifacts, not only the summary. Reconstruct every original/edited decision and rejection. Join by immutable task, candidate bank, judge, mode and rewrite identities.

For each judge compute:
- opportunity: independently wrong, but a correct candidate exists;
- rescue: a peer-assisted mode solves one of those opportunity tasks;
- regression: an independently correct task becomes incorrect with peers;
- structural conflict: task-only is correct but no selectable candidate is correct;
- free construction: final generation succeeds even though no candidate is correct.

Example: a judge can score worse in a forced selector simply because its own correct answer is not among the candidates. Do not attribute that structural restriction to persuasion. Conversely, a correct candidate can rescue a task the judge misses, even if other regressions cancel the gain in the aggregate.

Outputs: complete private decision matrix; opportunity/rescue/regression tables; exact same-task attack/rephrase comparisons; private review samples and annotation forms. No new logits, model calls, 'human' labels, or semantic judgments are fabricated.

## B. Semantic review — inspect saved text before choosing a loss

Main panel: 20 task groups, ten per dataset, selected without victim outcomes from the existing mixed-support population. Review all five scheduled original/rewritten pairs per task: at most 100 units, with failed acquisitions retained as missing.

Illustrative casebook: up to12 outcome-enriched examples and their ordinary-rephrase counterparts, at most 24 additional units before deduplication. Include harmful flips, beneficial flips, ordinary-rephrase flips, resistant cases, model disagreement, and output-format failures. This casebook is not a prevalence sample.

Two independent reviewers first see randomized Text A/B without gold labels, model identities, attack names or success outcomes. They annotate task-substantive meaning changes, internal contradictions, task support, unsupported claims, rhetorical cues, uncertainty and exact supporting spans. Their reviews are locked before model outcomes are revealed.

A second pass records what the judge output actually says. That is not a faithful trace of hidden cognition. Disagreements and unresolved external-knowledge claims remain visible. Code creates forms and joins; it does not claim to perform independent human review.

## C. Small optional mechanism experiment — only after review

Prespecify at most 32 slots from the main panel: up to eight source pairs per dataset for each of claimed-consensus and claimed-verification. Select them independently of old attack success and do not replace rejected slots after review.

For a pair where both reviewers can isolate an unsupported cue and an adequate non-cue control, construct:
1. The accepted rewritten rationale unchanged, evaluated again as a fresh reference.
2. That rationale with only the reviewed cue span deleted.
3. That rationale with only a comparable redundant non-cue span deleted.

Keep the question, answer labels, candidate order and every other packet fixed. No LLM rewrite or generation of new factual claims is required. Exact deletion spans and the control's semantic limitations are recorded. Where no adequate control exists, report the item as not testable rather than invent one.

Run all three versions under J8/J14 and full selection/evidence selection/free synthesis. Compare cue deletion against the sham deletion on identical task/judge/mode cells, not only among examples that the old attack broke. All failures and negative results remain in the report.

This is a local human-assisted intervention, not a deployable no-oracle defense. Even a positive finding would support the causal contribution of a specific span under the tested context, not prove a universal persuasion mechanism.

Maximum budget: 32 pairs x3 variants x2 judges x3 modes =576 new judge calls and 294,912 reserved output tokens. A two-unit smoke uses at most36 included calls. Human review, original artifacts and offline arithmetic consume zero model calls. Paid APIs, generation of new attacks, training and teacher-forced scoring all have zero budgets.

## D. Decide on the algorithm after observing these analyses

Candidate future direction: independent-first, evidence-gated revision. Preserve an independent answer, then change it only when peer evidence supplies a grounded reason. This is a hypothesis, not an original algorithm established by the present request. It must later be tested against independent answering, answer-only selection, an equally budgeted self-reconsideration control, existing adjudication methods and ordinary adversarial training.

If there is little judge-relative rescue opportunity, improve the candidate-bank design before trying to make a stronger judge trust weaker peers. If rewritten arguments mostly add false premises, emphasize grounded claim verification rather than rhetoric stripping. If cue deletion is no better than control deletion, preserve that negative result and do not increase the budget automatically.

## E. Final-paper breadth, without an immediate factorial sweep

Use two separable evaluation axes later:
- A frozen candidate bank served to multiple judge families, including frontier APIs, to isolate judge robustness.
- Separate proposer-bank comparisons, including stronger cross-family proposers, to determine whether peers add value relative to each judge.

Retain MMLU-Pro/MuSR, use GPQA for hardness and MATH for free-response transfer with output-validity controls, and add code only when safe scoring is operational. All confirmation/reserve data remain locked now. Current review examples remain disallowed as optimization data.

Future frontier roster: one independently sourced model per OpenAI/Anthropic/Google provider plus open-weight cross-family controls, subject to official endpoint verification, supported modes and budget approval. Do not copy historical endpoint names or assume reasoning settings match. Record served model, snapshot/alias, API version, time, usage, visible/hidden reasoning tokens where returned, refusals and actual costs. No provider API dispatch is implemented or activated in this phase; only metadata/import compatibility is needed.

## What Codex should deliver now

A complete offline source importer, decision census, review/annotation workflow, reviewed-edit validator, optional bounded Colab runner, reports, privacy-preserving exports and actual tests. The first usable output is the real private casebook and judge-opportunity matrix when raw evidence is available locally. If only summaries exist, Codex reports the absent raw artifact and demonstrates the implementation on invented fixtures instead of inventing findings.

The optional inference stage stays locked until the user approves the actual annotation/intervention manifest and its finite request budget.
