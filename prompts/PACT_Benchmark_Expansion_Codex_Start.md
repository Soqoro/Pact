Update my EXISTING PACT repository according to:

docs/PACT_Codex_Benchmark_Expansion.md

Read that document in full. Also inspect AGENTS.md, Git status, the latest
6 October project review, the completed heterogeneous runner and its actual
model/data manifests. Preserve unrelated changes and all historical results.

This is an IMPLEMENTATION request. Add runnable loaders, evaluators, phase
runners, reports, tests and thin Colab notebooks—not just another dataset list
or a set of placeholder adapters. Reuse working code and complete existing
partial implementations rather than creating a parallel framework.

## Scientific scope

Implement these six additions:
- MMLU-Pro.
- MuSR.
- MATH-500.
- MBPP+.
- A separately allocated new GPQA-Diamond characterization subset.
- A release-locked LiveBench subset targeting 2026-06-25, subject to actual
  official question/scorer availability.

This is CLEAN, INFERENCE-ONLY benchmark breadth characterization. There are
no training updates, adversarial attacks, synthetic donors, private replay,
new judge training, forced disagreement, or model/seed search.

Keep the exact pristine Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct,
Mistral-7B-Instruct-v0.3 and common unadapted Qwen3-8B readout identities
from the completed heterogeneous manifest. No old PACT adapters.

Use each model's native tokenizer/template. Preserve the model-major,
one-resident-model-at-a-time execution strategy and existing decoding.
New task-specific output/context caps are explicit in the full document;
do not silently apply the legacy 64-token answer-letter readout to code.

## Two implemented phases, separately invoked

Phase A: nine natural private packets per task (three per family).
Form QQQ, LLL, MMM and QLM from the same bank using the existing balanced,
preselected family/slot binding. No best-of-nine selection. Score offline
and report coverage/diversity only.

Phase B: only the four predesignated cores—MMLU-Pro, MuSR, MATH-500, MBPP+—
in this initial budget. Reuse the exact Phase-A private packets. Add 12
synchronous revisions, four private syntheses, four revised syntheses,
and one task-only readout per task: 21 additional calls.

Run all planned tasks in an invoked phase, regardless of whether useful
mixed support appears. No positive-result/support gate. Access, evaluator,
safety, integrity and resource failures remain explicit and dataset-local.
Phase A alone cannot be reported as measuring communication utilization.

Default notebook action is plan/preflight. No automatic all-suite run.

## Dataset and evaluator contracts

Read the full source-specific instructions; in particular:

- MMLU-Pro: use official TIGER-Lab data; support variable option counts,
  including A-J. Keep answer metadata and cot_content outside prompts.
  Characterize 140 tasks, ten per category; separately reserve confirmation.

- MuSR: preserve the entire narrative, question and choices; use all three
  native domains and safe CSV list parsing. Characterize 90 tasks,
  thirty per domain. Domains are not official train/test splits.

- MATH-500: free-response math, not invented multiple choice. Characterize
  100 tasks. Keep solutions/answers evaluator-side; use a pinned, tested
  mathematical parser/equivalence scorer. No LLM judge or gold-guided
  extraction of whichever expression happens to be correct.

- MBPP+: characterize 100 tasks from the pinned official EvalPlus release.
  Generate complete Python programs. Full expanded-test success is primary;
  syntax checks or the small base tests are not substitutes. Keep hidden
  tests/reference implementations out of model inputs. Code voting is N/A
  by default; do not use hidden-test results to choose a candidate.

- GPQA: preserve the parent 32 exposed / 164 protected / two exclusions.
  The new design explicitly allocates 32 new development items from the
  protected set, then locks 32 confirmation and nominally 100 reserve.
  Preserve exact parent provenance, official access, option policy and
  privacy. Do not regenerate the old cohort or use any GPQA item for SFT.

- LiveBench: target 100 single-turn items, twenty in each of reasoning,
  math, data analysis, language and coding. Verify actual official release
  membership, public question content, task scorers and quotas first.
  A leaderboard label is NOT proof those questions are downloadable.
  If unavailable, report requested_release_unavailable; do not silently
  use 2024 data under a 2026 label. Use native task scoring/output formats,
  preserve partial scores, and distinguish full success from nonzero score.
  Exclude agentic coding and instruction-following from this initial slice.

Freeze all source revisions, option mappings, response formats, scorer
versions, task groups and characterization/confirmation/reserve partitions
before inference. Use seed 20261006 with stable namespaces. No outcome-based
task replacement. All new benchmark cohorts are evaluation material for
this phase, never training data; locked confirmation/reserve generation is
not authorized. An upstream split named test or train is not our exposure policy.

## Safe execution and honest readiness

Implement real native scorer adapters. Generated code must run only behind
an enforced OS-isolation boundary with no network, user secrets, Drive or
workspace access, plus process/time/memory limits. EvalPlus's reliability
guard or a bare subprocess is NOT a security sandbox.

Use a capability-checked non-Docker isolated worker where supported.
Provide exact hash-checked score export/import for an isolated evaluator
when the inference runtime cannot enforce that boundary. Never silently
run unsafe code, replace tests with an LLM judge, or invent code scores.
Missing sandbox/scorer/access blocks that dataset's evaluation, not the
other datasets or the implementation work. Report pending scores as pending,
not zero accuracy or completed complementarity evidence.

## Budgets and reports

Implement planner-derived dataset caps from the full specification:
- Phase A: at most 5,058 calls / 3,898,368 reserved output tokens.
- Core Phase B: at most 9,030 additional calls / 5,846,400 tokens.
- Total portfolio: 14,088 calls / 9,744,768 tokens, NOT one automatic job.

Each dataset/stage is explicitly invoked. A two-task Phase-A smoke is at
most 18 calls INCLUDED in that dataset plan. Scoring CPU work, input tokens,
loading and execution limits are counted separately. No cap reset on resume.

Report per-family accuracy, QLM versus EACH homogeneous team, correct
coverage above the best member, joint failure, valid mixed support and
wrong-answer disagreement separately. Phase B adds erasure, repair,
construction, utilization, readout loss and paired protocol outcomes.

Use task/group-clustered uncertainty and task-native scores. A synthesized
solution may be newly constructed; coverage minus accuracy is not automatically
an ignored-answer count. No unqualified cross-benchmark or official leaderboard
average. Keep legacy ARC/LogiQA results read-only and clearly separate.

## Implementation and handoff

Use local CPU/mock tests and optional tiny locally initialized models only.
No pretrained downloads or GPU experiments locally. Do not commit or push.
I review/push to GitHub, execute the pinned code in Colab, and return results.

Implement full entrypoint tests, nine-packet/four-team bindings, native
scoring fixtures, quota/exposure guards, safety/refusal paths, token budgets,
resume, and private/sanitized exports. Do not weaken existing tests or
repeat whole-project audits instead of coding.

Finish with changed files, all six adapter/scorer statuses, tests actually
run, explicit unresolved source/sandbox prerequisites, exact first MMLU-Pro
smoke commands, per-dataset Colab commands, and required return artifacts.
Keep implemented, CPU-tested, runtime-ready, GPU-verified, and scientifically
demonstrated states distinct. No new empirical results are assumed.

Begin by inspecting the repository and reading the full implementation
specification, then implement the smallest complete path and extend it.
