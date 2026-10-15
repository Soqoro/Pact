# PACT next-phase plan: identify why switching is suppressed, then fix the missing control

Prepared: 15 October 2026.
Status: proposed design. No new gate has been fitted, no saved raw evidence analyzed in this pack, and no GPU experiment executed.

## Decision

Do not retrain the gates, change the checker, lower the deployed threshold, or invoke cross-domain transfer yet. First use the saved fitting/tuning data to distinguish score quality from decision conservatism. Separately repair the anchor-inclusive selector prospectively, because its reported 44/64 was entirely fallback.

This phase provides a runnable next experiment, not a new PACT algorithm or another attempt to obtain more natural pairs.

## What the latest audit supports

All five CPU models converged and selected KEEP_ONLY. The primary restricted-augmented policy copied the anchor on all 64 source-development tasks: 44 correct, zero switches, rescues or harms. It did not exploit the nine LogiQA rescue opportunities; ARC offered no additional correct peer answers beyond its anchor on the recorded development cohort.

The parent also reports 202 malformed selector outputs: 198 extra-key JSON outputs and four non-JSON outputs. Therefore, its fallback accuracy does not evaluate a functioning selector. The ambiguity in the prompt is a plausible explanation, not yet a demonstrated causal explanation.

These facts come from the supplied completed selective-correction audit. Codex must reconstruct the raw quantities from the actual private parent rather than fill new tables from this summary.

## Stage 1: offline diagnosis, zero model calls

Reconstruct all five saved classifiers using the original FIT-only transforms and coefficient/class ordering. Do not refit.

For each candidate, retain:

    predicted improve probability
    predicted harm probability
    u2 = p(improve) - 2*p(harm)
    extraction/checker validity and disable reasons
    original threshold and whole-task selected alternative

Then answer four questions.

### A. Was switching never proposed, or did the risk screen reject it?

The primary tuning policy reportedly made zero switches even at the lowest original threshold, zero. That differs from a useful switching policy being rejected by the 5% screen. Check active score maxima and masks, not only the selected KEEP_ONLY name.

The exact zero-threshold identity is:

    p(improve) - 2*p(harm) > 0
    iff logit(improve) - logit(harm) > log(2).

Convergence is numerical evidence, not a guarantee of predictive signal.

### B. Are improving examples distinguishable?

Compare improve/harm/neutral score distributions, rank separation, model-assessed checker verdicts, and task-level top-alternative choices on FIT and TUNING separately. Use actual task/view weights rather than raw augmented counts as class priors.

A useful hypothetical contrast is:
- Improving candidates score -0.05 and harmful ones -1.0: useful ranking might exist, but the original nonnegative threshold suppresses every switch.
- Both classes score around -0.5: the fitted representation/model may not distinguish them well.

Those are illustrations, not measured results. Neither justifies retrospective threshold tuning on development data.

Within one wrong-anchor MCQ task, the competition is between improving and neutral alternatives. Harm and improvement arise on different anchor-correctness tasks; cross-task classifier accuracy does not automatically imply good within-task candidate selection.

### C. Is the cost preference responsible?

On saved FIT/TUNING scores only, report a fixed explanatory grid of harm costs and thresholds, including costs 0, 0.5, 1 and 2, and negative thresholds. Keep masks, probabilities and candidates unchanged.

This is OFFLINE diagnostic arithmetic. It does not select a new policy, relax the original 5% screen, or create a new held-out result. The original policies remain KEEP_ONLY.

Report both R-H (accuracy gain) and R-lambda*H (the cost preference). They are different objectives when lambda differs from one.

### D. Where did genuine opportunities get lost?

Export all clean fitting improvements, all tuning rescue-opportunity tasks, and the nine known LogiQA development opportunities as private case dossiers. Include the saved peer/anchor text, extractor/checker outputs, features and candidate scores. Add a prespecified harmful-fitting comparison sample.

Distinguish no correct peer, disabled checker, unfavorable checker verdict, negative gate score, wrong top-ranked alternative, and final KEEP_ONLY retention. These are observed pathway descriptions, not proof of psychological or semantic causes.

This does not reactivate independent human semantic review or cue/sham interventions. No fabricated reviewer labels or new explanatory LLM calls.

## Stage 2: prospective selector-contract comparison

Implement and then separately invoke a new child using exactly the original 64 development tasks and their 138 accepted rationale rewrites. Sources, anchors and all checking outputs are reused; no new proposers or attacks.

There are 202 views. Each is evaluated under two prompts:

1. **Legacy prompt repeat:** the old wording, measured afresh in the same child runtime.
2. **Corrected contract v2:** only the response-format passage is clarified. `anchor` is a VALUE of `candidate_id`, never an extra field.

The strict parser, permitted choices, final fallback, model, decoding and output/context caps stay identical. The corrected prompt is not given a stronger reasoning method. Neither arm uses constrained decoding.

Both prompts require exactly:

    decision_basis: string
    candidate_id: permitted string value

The selector still includes the independent answer and valid peer candidates. Empty/invalid source handling follows the parent's public contract. Candidate options are never removed using correctness labels.

The fresh legacy repeat controls for comparing two different inference sessions. It is a deliberate new measurement, not a reopening of the old run. It cannot be satisfied by a cache hit on the old output; resume reuses the child's own committed records normally.

### Budget

| Stage | Maximum new LLM calls | Reserved output tokens |
|---|---:|---:|
| Offline analysis | 0 | 0 |
| Legacy prompt repeat: 202 views | 202 | 103,424 |
| Corrected prompt: same 202 views | 202 | 103,424 |
| **Total** | **404** | **206,848** |

Use the pinned pristine J8: non-thinking, greedy, BF16/SDPA, 512 output tokens, 8,192 total recipient-context tokens. No gate fits, LLM updates or teacher-forced forwards.

Choose one task per dataset by fixed hash for the smoke. Evaluate both prompts on those tasks' clean and already accepted variant views: at most 16 INCLUDED calls. Do not revise the prompt inside the frozen plan after seeing the smoke.

No notebook default launches these calls. Plan, smoke, continuation and export are explicit stages.

## What we will measure

A valid selector is not necessarily a good selector. Report:

- Exact output-contract compliance and failure types.
- Strict correctness versus deployed original-anchor-fallback correctness.
- Intentional anchor choices versus forced fallback.
- Peer rescues, harms, switching and net accuracy versus the exact original anchor.
- Attacked accuracy and clean-to-attacked flips against each NEW arm's clean outputs.
- Paired corrected-versus-legacy outcomes in the same child runtime.
- The new legacy reference's agreement with the historical legacy outputs.

No retrospective field stripping or silent rescoring. A repaired selector can still harm accuracy; that is a valid result. Candidate-constrained final answers cannot exceed the anchor-plus-peer oracle in the fixed bank. The old six-call independent-reconsideration baseline has a different free-generation answer space.

## Decision after the phase

| Evidence | Implication |
|---|---|
| Fit discrimination, weak tuning discrimination | Investigate generalization, data/feature coverage or model expressiveness in a separately designed learning experiment. |
| Useful ranking but scores below the original cost boundary | Reconsider the cost/calibration policy prospectively, not by publishing a best hindsight threshold. |
| Weak checking/classifier signal | Improve what is checked or how information is represented before simply running more optimizer steps. |
| Correct alternatives repeatedly disabled | Investigate the exact upstream response contract prospectively. |
| Repaired selector yields useful corrections | It is the new simple baseline a gate must outperform. |
| Repaired selector is valid but harmful | Retaining the answer option alone does not solve selective correction. |
| Repaired selector remains invalid | The baseline is still technically untested; preserve that limitation. |

Do not automatically change models, thresholds, tasks, risk tolerances or training recipes based on this report. The next learning study will need its own frozen design and data-exposure treatment.

## Final-paper scope stays intact

Multiple proposer families, independent/open/frontier judges and multiple domains remain the intended eventual evaluation. They are not part of this narrow execution budget. A better-calibrated gate, a different checker or a broader source pool is not selected in advance of the diagnostic findings.

All historical results, incomplete-run flags, training prohibitions, locked cohorts, and human-review deferrals remain in force.
