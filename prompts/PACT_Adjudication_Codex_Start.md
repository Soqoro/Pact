Update my EXISTING PACT repository according to:

docs/PACT_Codex_Fixed_Bank_Adjudication.md

Read that document in full, then inspect AGENTS.md, Git status, the latest
11 October audit, breadth manifests, exposure ledger, actual model/parser/
reporting code, and the existing heterogeneous runner. Preserve unrelated work.

Implement this phase, not just another plan or report. Reuse working components.
The new study is pact-adjudication-diagnostic-001: frozen-bank answer-selection
baselines plus a bounded coverage-preserving rationale-attack diagnostic.
This is NOT full PACT training or a claimed new defense.

## 1. Reuse existing evidence

Import the completed 140 MMLU-Pro and90 MuSR characterization tasks and their
exact QLM/QQQ private-packet bindings. Keep IDs, options, source/group hashes,
original outputs, and all exposure flags unchanged. These230 tasks remain
training-disallowed, development-exposed data. Do not access locked cohorts.

Use MATH-500 only for offline format/construction analysis. No new GPQA Phase B,
MBPP execution, LiveBench work, benchmark expansion, proposer generation,
receiver revisions, adapters, training, private replay, or NLL scoring.

Keep prior stopped/incomplete experiments closed, especially controlled
specialization's unsafe recovery status. Do not re-audit every old archive.

## 2. Deliver an offline failure map

Recompute O0/O1/Y joint events, erasure, construction, readout loss, output
failures and old paired method outcomes from available records. Do not call
coverage minus final accuracy an ignored-answer count. Export the prespecified
small rationale-review sample; unreviewed explanations stay unreviewed.

## 3. Implement six clean modes for each of two judges

Judges:
- Existing pristine pinned Qwen3-8B readout.
- Official Qwen/Qwen3-14B, resolved to an immutable revision before inference.

No adapters; native templates; explicit non-thinking; BF16/SDPA; greedy;
512 output-token cap and8192 total recipient-context cap in every mode.
This is a NEW readout-budget profile, not a repair of the old64-token study.
One model resident at a time; no silent quantization or smaller-model fallback.

Per judge/task run:
1. Task-only free answer.
2. QLM answer-only candidate selection.
3. QLM full-packet candidate selection.
4. QLM evidence-comparison candidate selection.
5. QLM free synthesis.
6. QQQ full-packet candidate selection.

Candidate-selection outputs name an original selectable candidate ID or abstain;
free-answer modes can choose any original task option. Do not allow hidden
fallback, gold-dependent filtering, or oracle decoding. Duplicate answers retain
separate IDs. Invalid source packets are not silently salvaged.

Use identical trust-boundary instructions and cap across modes. The evidence
mode is a one-pass prompt baseline, NOT a reproduction of AgentAuditor/ACPO.
Freeze all prompts and schemas before new inference. Run all230 tasks,
regardless of whether they contain a correct candidate. New outcomes cannot
choose the cohort, prompt, checkpoint or winning judge for the attack stage.

## 4. Implement the bounded rationale intervention

Use ALL original private QLM tasks with valid correct and valid wrong candidates;
audit expects42 MMLU-Pro +38 MuSR. Verify IDs; do not hard-code success labels.
Freeze this conditional attack population before new judge outcomes.

Pick one already-wrong candidate per task by a seeded rule. Change ONLY its
justification. Preserve all candidate answer IDs, source/order/envelopes, trusted
task/options, and every other full packet—including all correct candidates.

Use the pinned pristine Qwen2.5-7B as an offline generator. One attempt per type:
- task-argument pressure;
- claimed verification;
- claimed consensus;
- claimed independence/anti-conformity;
- ordinary rephrase control.

Generate the entire pool before victim evaluation. No victim feedback, prompt
search, target switching, extra seeds or retries. This is a FIXED-POOL diagnostic,
not adaptive attack search or JudgeDeceiver reproduction. The rephrase is not
certified semantic equivalence. Preserve rejected messages and missing results.

Evaluate every accepted variant under both judges' full selector, evidence
selector and free synthesis. Answer-only/task-only/vote inputs cannot see the
changed rationale: prove exact input identity and reuse clean outputs, rather
than running redundant calls or claiming broad certified robustness.

Do not attack QQQ or regenerate peer exchanges in this phase.

## 5. Metrics and budgets

Report candidate coverage versus selection; free construction; same-judge QLM
versus QQQ; answers-only versus full evidence; ordinary versus explicit evidence
comparison; J8 versus J14; and task-only baselines at the matched new cap.

For attacks separate clean-correct flips, existing clean errors, targeted wrong
answer adoption, exact attacked-candidate selection, abstention and malformed
outputs. Preserve q=1,2,4 fixed-prefix accounting; exclude ordinary rephrase from
the four-attack worst-pool score. Missing queries are not defended successes.

Use per-dataset task/group-clustered paired uncertainty. The80 eligible tasks
are a conditional label-aware diagnostic, not the unconditional230-task attack
rate. No output proves rationale validity or robustness to adaptive attacks.

Exact ceilings from the full spec:
- Clean:2760 calls /1413120 output tokens.
- Perturbation generation:400 /204800.
- Perturbed victims:2400 /1228800.
- Total:5560 /2846720.

All calls cap512. Training/teacher-forced/proposer/revision/replay budget is zero.
The first two-task MMLU smoke uses <=24 INCLUDED clean calls (J8-only prefix<=12).
Default notebook action is plan/preflight. Clean, acquisition and attacked
evaluation are separately invoked and each exports evidence; no automatic sweep.

## 6. Workflow and handoff

I develop locally, review/push to GitHub, execute pinned Colab stages, then return
results. Run CPU/mock tests and optional tiny locally initialized neural tests
only. No local pretrained downloads, GPU runs, commits or pushes.

Reuse journals, safe readers, recipient-tokenizer checks, exact caches,
single-model scheduling and private/sanitized exports. Unknown dispatches stay
unknown; do not mark a partial run recovery-safe from matching counts alone.
Untrusted attack text must never become shell/tool/code instructions.

Deliver actual package/CLI/thin-notebook implementations, a full mock round trip,
focused regression and actual entrypoint tests, exact Colab commands, required
parent/model access paths, the resolved budget, and expected handoff files.
Clearly distinguish implemented, locally tested, runtime-ready and GPU-verified.
Keep paper placeholders and all previous experiment conclusions unchanged.

Begin by inspecting the repository and reading the full specification, then
implement the smallest COMPLETE import/clean/attack/report path.
