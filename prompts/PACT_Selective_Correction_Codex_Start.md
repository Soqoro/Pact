Update my EXISTING PACT repository according to:

docs/PACT_Codex_Selective_Correction_Update.md

Read it in full, then inspect AGENTS.md, Git status, the latest14 October
research review, actual source/model contracts, exposure ledger and existing
inference/adjudication code. Preserve unrelated work and historical results.

Implement a COMPLETE bounded learning study, not another plan/support-only
report. Reuse current package/CLI/notebook/persistence components.

## Method and scope

Implement pact-selective-correction-001 / anchor_check_gate_v1:
- Save an independent J8 answer before peers.
- For each valid differing peer answer, extract a specific challenge.
- Check it in fresh J8 contexts.
- Train a lightweight CPU KEEP/SWITCH policy on replacement outcomes.
- Tune its threshold on a separate split, freeze it, then evaluate.

Use the same pristine pinned Qwen3-8B for anchor, extraction and checking.
Separate calls are not independent models or verified evidence. Keep Q/L/M
proposers and all LLM weights frozen. The ONLY learned parameters are the
small gates. No LoRA/DPO/specialization refresh, frontier API or extra judge.
Human semantic review and cue/sham intervention remain DEFERRED.

## Controlled comparison

For each alternative collect ONE common extractor, then:
- V_full: task, anchor, alternative, challenge/references AND raw peer rationale.
- V_restricted: same without the raw peer rationale.

Each deployed method uses two calls/alternative. Their collected union uses
three, not four. Preserve equal schemas/caps and exact source identities.
Check source spans mechanically; never call an exact quote a verified proof.
The restricted challenge can still be wrong or malicious.

Fit full_clean, full_augmented, restricted_clean, restricted_augmented and
metadata_augmented gates, using the exact objective/feature allowlists in the
specification. Target d=correct(c)-correct(b) is improve/harm/neutral and stays
outside generation inputs. Do not require same-prompt correct/wrong samples.

Use small regularized multinomial logistic models with real CPU optimization,
fixed fit-only transforms, plain-data coefficients, convergence reporting and
reference gradient tests. No labels, task IDs, option letters, attack style,
model family or raw-text embeddings in features. The metadata control uses
ONLY public answer counts/availability and has no hidden checker dependency.

For each usable candidate u=p(improve)-2p(harm). Jointly select the largest
score above a frozen threshold; otherwise COPY the immutable anchor. Do not
regenerate the final answer. Calibrate the whole max-over-candidates policy.
The32-task tuning split and5% screen give an EMPIRICAL operating point,
not a statistical/adaptive risk certificate. KEEP_ONLY is a valid negative
outcome; do not lower thresholds to manufacture successful switching.

## Data and attacks

Use224 NEW groups from official ARC-Challenge and original English LogiQA
TRAINING sources, equally allocated by dataset:
128 fit /32 threshold tuning /64 source-development holdout.
Exclude known previous uses and locked groups. Freeze IDs, options and all
contracts before generation. Do not train on the old230 MMLU/MuSR tasks.

Generate one natural Q/L/M packet and one independent J8 answer per new task.
No nine-sample bank, forced disagreement, or correct synthetic candidate.

Fit/tuning: one wrong-rationale rewrite attempt each for argument_pressure
and claimed_verification. Heldout: claimed_consensus, claimed_independence,
and an ordinary_rephrase control. Targets are fixed independent of judge
success; preserve anchor, answer labels, other packets and task exactly.
No retry, adaptive feedback or semantics-preserving claim. Reuse unchanged
checking paths only by exact identity. Missing variants remain missing.

Core evaluation controls: always KEEP, one-call anchor-inclusive selection,
six-call independent reconsideration without peers, the metadata gate,
and all four checking gates. Match public answer spaces and report strict
format outcomes separately from the explicit shared anchor-fallback rule.
Infrastructure missingness cannot be turned into a correct fallback.

After policies freeze, implement SEPARATELY INVOKED transfer on all existing
140 MMLU +90 MuSR tasks and369 accepted parent rewrites. Reuse exact J8
anchors/candidate banks; no original-response regeneration. These are
training-disallowed, development-exposed transfer records, not confirmation.
No GPQA, MBPP, LiveBench, locked confirmation/reserve, or new human review.

## Budgets and workflow

At512 new output tokens/call and8192 total recipient context:
- Fit/tuning bank:3360 calls /1720320 reserved output tokens.
- Source-development:2240 /1146880.
- Core:5600 /2867200.
- Optional fixed-bank transfer:5156 /2639872.
- Portfolio:10756 /5507072.

Five CPU fits max,500 solver iterations each. Zero LLM optimizer or
teacher-forced forwards. One resident large model at a time.
First source smoke: two FIT tasks,8 INCLUDED calls.
Default is offline plan; no notebook Run All launches this portfolio.

I develop locally, review/push, run pinned Colab stages and return artifacts.
Run only CPU/mock or tiny locally initialized tests locally. No pretrained
downloads, GPU calls, commits, pushes, credentials or paid services.

Deliver real source/feature acquisition, CPU fitting/tuning, frozen-policy
execution, baselines, core/transfer evaluation, reports, exact Colab commands,
full mock round trip and regression tests. Enforce fit/tune/eval separation,
feature/label boundaries, source span checks, gate/cost arithmetic and resume.
Do not stop before implementing training because actual weights are absent;
use fixtures and state the precise real-run prerequisites.

Finish with changed files, tests actually run, fixture KEEP/SWITCH example,
first8-call smoke commands, fitting/tuning/evaluation commands, budgets,
expected bundles and GPU-unverified limits. Preserve old safety flags,
negative findings and manuscript placeholders.

Begin by reading the full specification and inspecting the repository,
then implement the smallest complete gate-learning path.
