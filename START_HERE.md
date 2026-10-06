# PACT benchmark expansion — Codex handoff

This pack contains prompts and a validated arithmetic design, not an implemented PACT code patch or completed experiment.

1. Copy `docs/` and `prompts/` into the EXISTING repository, checking for name collisions and preserving local edits.
2. Paste `prompts/PACT_Benchmark_Expansion_Codex_Start.md` into local Codex.
3. Codex reads the full specification and implements/testss the dataset, scorer, runner and reporting extensions. Local tests use invented fixtures; real model work stays on Colab.
4. Review the patch, commit/push it yourself, and run the explicit pinned per-dataset Colab stages. Default is planning; a large all-suite run is not implied.
5. Bring back the private or sanitized handoff appropriate to the next audit. Never commit raw GPQA, hidden code tests, generated programs with secrets, tokens, or model weights.

First runtime milestone: a fixed two-task MMLU-Pro Phase-A smoke, at most18 calls included in the eventual140-task dataset plan. The other datasets have separate source/evaluator/readiness checks. Characterization and confirmation are disjoint; this pass authorizes no locked confirmation/reserve generation.

Important source note: LiveBench2026-06-25 is the requested release, not a verified downloadable question bundle in the source material inspected for this brief. The implementation must verify official content/scorers or keep that dataset blocked without substituting a different release.

Code scoring must be isolated. A plain subprocess or EvalPlus reliability_guard is not a security sandbox. The generation pipeline may export scoring jobs when the runtime lacks an enforceable boundary; unscored code is not a benchmark result.

Files:
- `docs/PACT_Codex_Benchmark_Expansion.md`: complete implementation instructions.
- `docs/PACT_Benchmark_Expansion_Plan.md`: experiment scope and interpretation.
- `docs/benchmark_breadth_design.json`: proposed caps and source/phase metadata; not an application config.
- `docs/verify_budget_design.py`: standard-library-only arithmetic self-check; no model/data access.
- `prompts/PACT_Benchmark_Expansion_Codex_Start.md`: starter instruction to paste.
