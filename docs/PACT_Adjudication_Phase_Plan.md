# PACT: next-phase plan

Prepared 11 October 2026. Proposed design, not new experiment results.

## Decision

Move from benchmark expansion to a **frozen-bank adjudication and adversarial-gap study**. Do not restart actor specialization, scale agent count, or train a new judge yet.

The latest report supports a domain-dependent utilization problem, not universal superiority of heterogeneity. MMLU-Pro and MuSR contain extra correct candidates that are not reliably selected. MATH is a useful counterexample: the strongest constituent, the task-only readout, and successful answers absent from the candidate set show why final scores cannot automatically be attributed to complementary correct proposals. Output failures also limit model-family interpretation. Construction may still use useful partial reasoning from incorrect candidates; it is not proof that peers were ignored.

The new phase should determine whether simple, properly budgeted existing approaches solve the observed gap, and whether useful evidence access creates vulnerability to malicious explanations.

## 1. Offline forensic analysis — no model calls

Use the completed MMLU-Pro, MuSR and MATH records to reconstruct initial availability, revised availability and final correctness jointly. Separate erasure, construction, retained-answer readout loss, and output-contract failures.

Export a small outcome-stratified human-review sample of rationale content from MMLU-Pro/MuSR. Do not equate an answer-correct packet with a verified explanation. Do not edit labels or exclude difficult questions on the basis of review.

## 2. Matched clean adjudication — primary new inference

Reuse all **140 MMLU-Pro + 90 MuSR characterization tasks** and their original private QLM and QQQ candidate banks. These are development-exposed tasks, not new confirmation data. No proposers or revisions are regenerated.

Use the original unadapted Qwen3-8B readout and a new official frozen Qwen3-14B capacity control, one model at a time, non-thinking and greedy. The larger model is not presumed better. New output cap512 and total recipient cap8192 apply equally to the readout modes, unlike the old64-token MCQ readout; report this explicit difference.

For each judge, run six modes:

| Mode | Input | Decision space |
|---|---|---|
| Task-only | Trusted task, no candidates | Any task option |
| Answer-only selector | QLM answer IDs/frequencies, no rationales | A supplied candidate |
| Full selector | QLM full private packets | A supplied candidate |
| Evidence-comparison selector | Same QLM packets, explicit claim comparison | A supplied candidate |
| Free synthesis | Same QLM packets | Any task option |
| Homogeneous full selector | QQQ private packets | A supplied candidate |

A structured one-pass evidence prompt is a baseline, not an AgentAuditor/ACPO reproduction. A new method will later need comparison with genuine published learned adjudication methods.

All six modes share the same semantic trust-boundary rules and output cap. Candidate IDs are immutable and not labels supplied by the evaluator. The selector cannot invent an answer; free synthesis can. This makes construction versus selection observable.

Clean budget: 230 * 2 * 6 = **2,760 calls**, at most **1,413,120 generated output tokens**. Begin with two included MMLU-Pro tasks (<=24 complete clean calls, or <=12 for J8-only prefix). Do not execute the whole stage automatically.

## 3. Coverage-preserving rationale perturbations

Primary attack population: all saved PRIVATE QLM tasks with at least one valid correct and one valid wrong answer—reported as42 MMLU-Pro and38 MuSR. Verify actual task identities and freeze this80-task conditional population before new judge outputs. Do not cherry-pick tasks that clean judges get right or that attacks flip.

Choose one already-wrong candidate per task by a seeded rule. Edit only its justification. Preserve the trusted task, all candidate IDs and answer labels, candidate order, and every other packet, including all correct packets.

A separate pinned Qwen2.5-7B generator creates four attack styles and one nominal ordinary paraphrase, one attempt each:

- Persuasive task argument for the existing wrong answer.
- Claimed verification for that answer.
- Claimed wider consensus, without altering actual candidate counts.
- Claimed independence/anti-conformity.
- Ordinary rephrase control, not certified semantic equivalence.

This is a shared fixed pool generated before victim evaluation, **not adaptive attack search**. The four attack-prefix outcomes can be summarized at q=1,2,4; the benign rephrase is separate. All attempts, rejected outputs and missing victim results stay explicit.

Evaluate accepted variants under both judges' full selector, evidence selector, and free synthesis (six victims). Answer-only, task-only and voting inputs are unchanged; reuse their clean outputs by exact identity, marking that invariance is limited to this rationale-only threat.

Perturbation acquisition: <=400 calls /204,800 tokens.
Victim evaluation: <=2,400 calls /1,228,800 tokens.
No PACT or receiver training occurs.

## 4. Outcomes that decide the subsequent research direction

**Selection versus extra independent solving.** Does constrained selection beat the matched task-only baseline, or does a capable readout simply solve the problem itself? Does QLM add value over QQQ for the same judge?

**Rationale value.** Does full/evidence selection improve on answers alone? A gap in oracle candidate coverage is not automatically recoverable evidence.

**Adversarial utilization.** Do fixed rationale edits turn clean successes into failures even while correct candidates remain intact? How much utility is lost by avoiding rationales entirely?

**Model-capacity control.** Does a larger frozen judge solve the gap or resist these attacks without a new training algorithm? It has higher compute cost; equal calls/tokens do not mean equal FLOPs or elapsed time.

## 5. Interpretation limits

Report per-dataset, task-clustered paired results. Clean evaluation uses all230 tasks; the80-task attack population is deliberately conditioned on useful mixed support and known labels. Do not report its attack rate as an unconditional deployment risk.

Preserve abstention, malformed, truncated and infrastructure-pending states separately. Clean-to-wrong attacks differ from attacks on already-wrong cases. Targeted wrong-answer adoption differs from selecting a particular candidate when several share that answer.

A fixed-pool negative result does not establish robust security. A positive result establishes a limited susceptibility, not a novel defense. The new selectors are untrained baselines. Confirmation/reserve tasks remain locked and cannot become fitting data.

## 6. Budget and delivery

| Stage | Max new calls | Max reserved output tokens |
|---|---:|---:|
| Offline analysis | 0 | 0 |
| MMLU-Pro clean | 1,680 | 860,160 |
| MuSR clean | 1,080 | 552,960 |
| Rationale pool | 400 | 204,800 |
| Perturbed judge evaluation | 2,400 | 1,228,800 |
| Total | **5,560** | **2,846,720** |

These are worst-case ceilings, not expected usage, timings or billed units. All stages are explicitly invoked. No automatic transfer of unused budgets or retry-until-success. Training, new proposers, receiver revisions, counterfactual replay, and teacher-forced scoring all have budget zero.

The implementation must deliver the actual complete runner, not another design-only patch. First local work is import/analysis and CPU/mock tests; actual inference occurs in a pinned Colab checkout. Both model paths must be implemented; unavailable14B memory is a declared runtime prerequisite, not permission to silently substitute a smaller/quantized checkpoint.

## 7. What stays closed

- Original receiver-SFT result: executed, no incremental correctness demonstrated.
- Natural specialization: stopped for missing support.
- Controlled specialization: closed incomplete with unresolved accounting.
- GPQA Phase B: not part of this phase.
- MBPP scoring: remains deferred until genuine isolation is available.
- LiveBench: remains source-blocked under the old contract.
- All confirmation/reserve/final cohorts: locked.

No manuscript result is filled as trained PACT evidence. After this study, a new robust-selector training design is justified only by the residual behavior under appropriate baselines—not merely by outperforming the old short-budget readout.
