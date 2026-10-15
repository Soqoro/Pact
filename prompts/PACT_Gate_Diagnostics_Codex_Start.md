Update my EXISTING PACT repository according to:

docs/PACT_Codex_Gate_Diagnostics_and_Selector_Repair.md

Read it in full, then inspect AGENTS.md, Git status, the completed
pact-selective-correction-001 audit, original selective-correction design,
feature/model/threshold code and exposure ledger. Preserve unrelated work.

Implement two complete paths: OFFLINE gate diagnosis and a PROSPECTIVE,
matched selector-prompt correction. Do not stop at a plan or rebuild the
research framework.

## Parent and boundaries

Parent pair: 1791993400383124336.
PRIVATE SHA256:
b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449

The parent completed with all five CPU gates converged and KEEP_ONLY selected.
Its primary result was 44/64 with zero switches. Its selector had 202 malformed
outputs and only achieved anchor accuracy through fallback.

Keep that run closed. No refitting, new checking, threshold replacement,
transfer inference, new data, frontier calls, adapters, semantic review,
cue/sham experiment, or reopening old incomplete studies.

## 1. Offline diagnosis: zero LLM calls and zero new fits

Reconstruct the five saved models, original fit-only transforms, class order,
weighted objectives, probabilities, eligibility masks and tuning decisions.
Use trusted private artifacts; missing evidence is not a license to fabricate
scores or regenerate the parent.

Report:
- Raw versus actual task/view-weighted class support.
- p(improve), p(harm), u2=p(improve)-2*p(harm), and active score maxima.
- Improve/harm/neutral score separation on FIT and TUNING separately.
- Checker verdicts conditional on actual replacement outcomes.
- Full/restricted agreement AND disagreement by outcome.
- Runtime-disabled/no-op paths versus score-threshold suppression.
- Within-task selection among improving and neutral alternatives when the
  independent anchor is wrong.
- Exact feature collisions and limits of the fitted representation.

Explicitly distinguish a risk screen rejecting useful switches from the
primary gate making no switches even at tau=0. At zero threshold, verify
u2>0 iff logit(improve)-logit(harm)>log(2).

Compute the specification's fixed lambda/threshold sensitivity grid ONLY on
fit/tuning saved probabilities. This is diagnostic arithmetic, not a new
policy or validation result. Do not choose a winner, modify coefficients,
export a replacement policy or invoke transfer. Never tune on development.

Export private saved-trace dossiers for all fitting improvements, all tuning
rescue opportunities and the nine known LogiQA development opportunities,
plus the fixed harmful-fit comparison sample. These are retrospective cases,
not new training examples or independent human semantic reviews.

## 2. Implement prospective selector-contract correction

Child: pact-anchor-selector-contract-002, subject to collision checks.
Reuse exactly 64 development clean views plus 138 accepted variants = 202.
No new anchors, peers, rewrites, verifiers or independent reconsiderations.

Run TWO matched arms on every view:
- legacy_prompt_repeat: the exact old prompt, freshly measured.
- selector_contract_v2: change ONLY the ambiguous output-contract passage.

The corrected instruction must clearly say that the only JSON KEYS are
"decision_basis" and "candidate_id". "anchor" is a possible STRING VALUE of
"candidate_id", not an additional field. Derive permitted choices from public
source validity, never correctness labels.

Both arms retain identical strict parsing, fallback, source text, candidate
order, reasoning instructions, model, decoding and caps. No constrained JSON
decoding, extra defense prompt or field stripping. Preserve all old malformed
results; never rescore them as a corrected experiment.

Keep the exact pristine J8 identity: non-thinking, greedy, BF16/SDPA,
512 output tokens and 8192 total context. Pair corresponding request seeds
and freeze arm order before outcomes. A fresh legacy repeat cannot use a
parent cache hit; child resume must reuse its own completed calls normally.

Budget: 202 views x 2 arms = 404 attempts, 206848 reserved output tokens.
One hash-selected task per dataset forms a smoke of at most 16 INCLUDED
calls across clean/available variant views. Smoke exports and stops; no
prompt tuning or task substitution after seeing it.

Default is model-free planning. Real Colab smoke/full stages are separately
invoked. Implement the complete runner now, but do not execute GPU work here.

## Reports and tests

Separate strict format success, strict correctness, intentional anchor choice,
model-failure fallback and deployed accuracy. Report rescues/harms and attack
flips relative to each new arm's own clean results. Missing infrastructure is
never a successful fallback. Use task-clustered comparisons.

Run focused CPU/mock tests including score/class-order identity, original
tuning parity, saved fitting weights, forbidden development tuning, diagnostic
artifacts rejected as policies, exact two-key schema, prompt-only diff,
fresh-repeat versus resume identities, bounds/budgets and full mock round trip.

I develop locally, review/push to GitHub, run a pinned Colab stage and return
artifacts. No local pretrained downloads, model/GPU calls, commits, pushes,
credential use or unrelated dependency migrations.

Deliver actual implementation, first offline commands, private dossier,
source-specific findings only when bytes are present, exact Colab commands,
budgets, expected bundles, tests actually executed and remaining unverified
work. Preserve the exposure-inventory freshness guard and paper placeholders.

Begin by inspecting the repository and reading the full specification, then
implement the smallest complete path rather than another design-only report.
