# PACT benchmark expansion plan

Prepared: 6 October 2026. This is a design and implementation handoff, not new results.

## Purpose

Test whether naturally heterogeneous LLM answers provide useful additional coverage across task types, then whether synthesis and communication use that coverage. The previous ARC/LogiQA observations motivate the study, but do not guarantee its generality. No new training algorithm or attack evaluation belongs to this phase.

## Keep the team fixed

Reuse the exact clean checkpoints and native templates from the completed Qwen2.5-7B-Instruct / Llama-3.1-8B-Instruct / Mistral-7B-Instruct-v0.3 study, with the common unadapted Qwen3-8B readout. Keep QQQ, LLL, MMM and QLM comparisons. Every task provides three private draws per family; QLM uses predesignated members, not a best-of-nine selection. Run one model at a time on Colab.

## New characterization cohorts

| Dataset | Characterization tasks | Why it adds breadth | Scoring / special concern |
|---|---:|---|---|
| MMLU-Pro | 140: ten per 14 categories | Broad academic and professional reasoning | Variable-choice MCQ, including up to ten options; correct source mapping. |
| MuSR | 90: thirty per three domains | Long-narrative multistep reasoning | Preserve complete stories, safe list parsing, related-variant grouping. |
| MATH-500 | 100 | Free-response mathematics | Pinned symbolic/numerical verifier; never convert to MCQ. |
| MBPP+ | 100 | Executable program synthesis | Official expanded tests in a genuinely isolated runner; no judge-based correctness. |
| GPQA Diamond | 32 newly allocated | Hard-science stress test | Reuse authoritative loader and old exposure/exclusion policy; do not treat old32 as new. |
| LiveBench | Target 100: twenty per five categories | Release-aware, varied recent-source stress test | Verify official question availability and native scorer for requested2026-06-25; not assumed accessible. |

These counts are proposed fixed ceilings. The public source pool and group availability are checked before model calls. LiveBench includes reasoning, math, data analysis, language and coding; it excludes agentic coding/instruction-following in this first slice. Missing source/scorer access is explicit, not a reason to use older data under a new date label.

## Protect confirmation and reserve data

For each core dataset, reserve a disjoint confirmation cohort of the same target size using group-level selection; remaining eligible groups stay reserved. Do not execute confirmation in this phase. All characterization data remain evaluation/development, not training.

GPQA's existing198-source accounting is32 exposed +164 protected +2 exclusions. The proposed child allocation is32 old exposed +32 new characterization +32 locked confirmation +100 reserve +2 exclusions, subject to compatible actual group/exposure checks. This is an explicit reallocation, not a retrospective alteration of the old manifest.

For LiveBench, reserve twenty per category for confirmation only if the requested official pool supports it. A release name alone does not establish either public availability or lack of contamination.

## Two stages

**Phase A, all six additions:** collect the nine private packets per selected task, score them, and construct the four teams offline. This establishes private answer availability and error overlap, not downstream utilization. No synthesis or discussion calls occur.

**Phase B, four cores only:** separately invoke communication/synthesis for all selected MMLU-Pro, MuSR, MATH-500 and MBPP+ tasks. Reuse their exact private packets. Add twelve revisions, eight synthesis calls and one task-only readout per task. Do not select only datasets/tasks where Phase A looks promising. GPQA/LiveBench communication is not in the initial budget.

Both phases are implemented now. Neither is automatically launched by opening a notebook. Default is plan/preflight. The experiment can be completed one dataset/model-stage at a time; the entire portfolio is not one Colab session.

## Response formats and fairness

MCQ keeps answer/justification packets with a generalized label set. Math uses an explicit final boxed expression. Code returns a complete Python solution, including after revision/readout. LiveBench keeps task-native formatting. Each response can be stored in the common typed packet envelope without pretending every output is an answer letter.

Proposed new caps:
- MMLU-Pro/MuSR:512 private/revision tokens;64 final tokens;8192 total context.
- MATH-500/MBPP+:1024 private/revision and final tokens;8192 total context.
- GPQA:256 private/revision;64 final;4096 context.
- LiveBench:1024 private/revision and final;16384 context.

All comparisons within a dataset share those caps. They are not identical compute across datasets/tokenizers. Prompt length is measured with each recipient's own tokenizer. No silent truncation, changed mode or extra retries.

## Exact proposed budget

| Dataset | Phase A calls | Phase A output reservation | Phase B additional calls | Phase B output reservation |
|---|---:|---:|---:|---:|
| MMLU-Pro | 1260 | 645120 | 2940 | 940800 |
| MuSR | 810 | 414720 | 1890 | 604800 |
| MATH-500 | 900 | 921600 | 2100 | 2150400 |
| MBPP+ | 900 | 921600 | 2100 | 2150400 |
| GPQA | 288 | 73728 | 0 | 0 |
| LiveBench target | 900 | 921600 | 0 | 0 |
| TOTAL | 5058 | 3898368 | 9030 | 5846400 |

Combined maximum:14088 generation calls and9744768 reserved output tokens. Counts assume all selected data are available; blocked allocations cannot be repurposed. Actual input tokens, evaluator CPU work, model loads and compute units are recorded separately. No time, billing or sufficiency guarantee is implied.

## Implementation priorities

1. Extend the registry and generalized task/evaluation contracts while preserving old MCQ behavior.
2. Complete MMLU-Pro and MuSR loader->private bank->score->communication->report with fixtures.
3. Complete free-response math and gold-free vote semantics.
4. Complete MBPP+ evaluation adapter and isolated execution/score-import path.
5. Reuse GPQA with the new explicitly allocated partition, and implement verified release-specific LiveBench adapters.
6. Test top-level CLI/notebook entrypoints, exact budgets, safety/locked-data stops and resumability.

A missing LiveBench release or unavailable code sandbox must not block working MCQ/math datasets. It must remain clearly visible as unready/unscored—not a fabricated result or a reason to run unsafe code.

## Interpretation

Report each dataset separately: private correct coverage, best member/homogeneous controls, useful mixed success/failure support, and later actual terminal accuracy. Include all negative findings. A correct answer somewhere is not an oracle available to the readout; the readout can also construct a new solution absent from all peers. Count erasure, readout loss and construction separately rather than interpreting coverage minus accuracy as a literal number of ignored answers.

Passing code tests means passing finite benchmark tests, not universal program correctness. Correct math answers do not verify every rationale sentence. Native partial scores are not binary successes. Calls/models/conditions are not independent sample units. The characterization cohort informs development and is not an untouched final benchmark.
