# PACT: next experimental phase — learn when to keep or switch

Prepared: 14 October 2026. This is a proposed design, not an experimental result.

## Decision

Move to a complete, small gate-learning experiment. Preserve an independent judge answer; use the same frozen LLM in fresh checking calls; train a lightweight decision model to predict the consequences of adopting a peer answer. Compare an ordinary full-context checking path against a restricted challenge-based path at the same deployed call budget.

Do not restart the old specialization loop, receiver SFT, human annotation, or cue/sham interventions. Do not start a frontier/API or dataset expansion campaign in this implementation. All LLM weights remain frozen; the decision gate is actually trained on CPU.

## Why this experiment

The 14 October review reports real peer rescue even where the overall score falls. For example, MMLU-Pro/J8 gained15 rescues but lost28 independent successes;22 losses arose because the independently correct answer was absent from the candidate-only output space. Free synthesis removes that restriction but still regresses. This motivates, but does not validate, explicit independent-answer preservation with selective correction.

The new experiment must separate four effects: adding the independent answer, extra inference compute, learnable rescue/harm signals, and robustness to changed peer explanations. A detector that ignores all peers is an essential baseline, not a successful complementarity result.

## The candidate method

1. Generate and save independent answer b before seeing peers.
2. For every valid different peer answer c, extract a short, specific challenge to b.
3. In a fresh context, check b against c using the trusted task and challenge.
4. A small learned classifier estimates improve/harm/neutral replacement outcomes.
5. Choose the highest-scored candidate only above a separately selected threshold; otherwise copy b without another generation.

For each comparison the model scores u=p(improve)-2p(harm). The choice is joint across alternatives, so tuning must evaluate the max-over-candidates policy, not isolated pairs. The class target is 1[c=y]-1[b=y], using the label only in the training/scoring module. No sampled correct/wrong completion pair or reviewed gold rationale is required.

## Critical equal-call control

Both paths use the same extractor:

- Full-context verifier receives the task, anchor, alternative, extracted challenge, task references and raw peer explanation.
- Restricted verifier receives the same input without the raw peer explanation.

Each deployed path uses two calls per alternative. The study collects their union in three calls per alternative because the extractor is shared. Model family, caps, prompts, source candidates and classifier labels stay matched. A restricted context is not a guaranteed security boundary or a proof that semantics have been preserved.

## Training and test matrix

Four principal learned arms: full_clean, full_augmented, restricted_clean, restricted_augmented. Same classifier family and fitting/tuning rules; only verifier context and fit perturbation exposure differ.

Additional controls: KEEP anchor; one-call anchor-inclusive selector; six-call independent critique/reconsideration without peers; learned answer-metadata-only gate; a simple rule based on the already collected verifier fields. Every raw generation/format failure and any deterministic anchor fallback is reported separately. Final method output includes its predeclared fallback; historic strict scores are not rewritten.

The first gate is L2-regularized multinomial logistic regression on categorical/numeric checker assessments and public answer metadata. No raw text embeddings, new LLM adapter, confidence oracle, family-ID lookup or answer-label lookup. Five CPU fits at most,500 solver iterations each. Class scarcity remains visible; no-rescue training support produces a documented KEEP-only fallback, not fabricated data or extra draws.

## Data design

New core:224 groups from official ARC-Challenge and original English LogiQA TRAINING sources, disjoint from known past uses and locked data:

-128 fit:64 per source.
-32 threshold tuning:16 per source.
-64 source-domain development evaluation:32 per source.

Freeze all group IDs and splits before generation. One Q/L/M draw and one independent J8 anchor per task. Three private draws from each family are unnecessary in this gate study. All tasks remain in the evaluation population, including no-alternative and all-wrong tasks.

The small tuning set provides an empirical operating point, NOT a low-risk certificate. A finite threshold grid maximizes clean gain subject to an observed5% unconditional harm screen on clean and accepted tuning perturbations. Evaluate the whole policy; KEEP_ONLY is an honest possible outcome. Do not tune on the64 heldout source tasks.

Optional, separately invoked transfer: freeze all parameters and thresholds, then use the existing230 MMLU-Pro/MuSR task groups, J8 anchors, QLM candidates and369 accepted rewrites. No regeneration of original candidates, anchors or attacks. They remain development-exposed, training-disallowed transfer evidence, not untouched confirmation.

## Attack design

Training/tuning uses one attempt each for argument_pressure and claimed_verification, only where a valid wrong peer exists. Source-development evaluation uses claimed_consensus, claimed_independence and a separate ordinary_rephrase control. Target selection is independent of judge success; no requirement that a correct peer exists. Only one wrong candidate's rationale changes; anchor and all answer fields remain fixed.

This is fixed-pool adversarial augmentation. It is not adaptive training or a claimed semantic-invariance test. Rejected variants are missing, not robust successes. No online generator gets victim feedback. Unchanged pair checks are reused only after exact identity checks.

## Budget: explicitly staged, not one automatic run

| Stage | New generation ceiling | Reserved output tokens |
|---|---:|---:|
| Fit + tuning data/features |3,360|1,720,320|
| Gate fitting + threshold selection |0 LLM calls|0 generated tokens|
| Source-domain heldout evaluation |2,240|1,146,880|
| Core total |5,600|2,867,200|
| Optional existing-bank transfer |5,156|2,639,872|
| Full implemented portfolio |10,756|5,507,072|

These are worst-case caps, not forecast runtime, billed units or expected tokens. Actual alternative counts, source validity and reuse reduce calls. No unused budget rolls into another task. Only one large model is resident at a time. Inference occurs in user-invoked Colab stages; fitting can be local CPU or Colab CPU. No LLM optimizer or teacher-forced scoring calls are needed.

First Colab smoke: two preselected FIT tasks' four source calls each; at most8 calls INCLUDED in the bank plan. Later checking/attack smoke is also a prefix of fixed requests. No prompt tuning on completed smoke while retaining a single scientific run identity.

## Success, failure, and decisions

The main identity is final accuracy=anchor accuracy+rescues-harms. Report both absolute R/H and conditional rates, whole-cohort accuracy, attempted-versus-completed denominators, candidate availability, strict/fallback outcomes, and cost.

The proposed path should beat anchor-inclusive judging, equally budgeted independent reconsideration, and the full-context gate trained with the same attacks at a defensible rescue/harm operating point. A lower attack-flip rate achieved only by always keeping b does not establish useful collaborative learning.

Possible outcomes:
- Anchoring alone accounts for gains: keep the simpler explanation.
- Full and restricted checking are equal: do not claim the restriction adds value.
- Gate sees no useful predictor or selects KEEP_ONLY: this is a negative learning result, not a reason to force nonuniform actions.
- Clean rescue improves but attack harm rises: robustness is unresolved.
- In-source improvement but MMLU/MuSR transfer fails: domain generalization is unresolved.
- A useful trade-off improvement: proceed to separately designed stronger published baselines, adaptive attackers, other judges/frontier models, and untouched confirmation.

Current studies and deferred human review stay closed. The generated specification authorizes implementation; actual GPU execution remains user-controlled. No manuscript PACT efficacy placeholders should be filled by this plan.
