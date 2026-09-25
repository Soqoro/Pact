# PACT: immediate experiment plan

Prepared: 24 September 2026. This is a new proposed study, not a report of completed experiments.

## Decision

Do not add receiver-training steps, switch losses, replace the primary models, or collect more synthetic donors yet. The completed controlled-receiver study solved data acquisition and exercised training, but did not produce incremental receiver correctness. It remains closed.

Run one 32-item GPQA-Diamond development diagnostic using the frozen-preparation arm's effective evaluated team. The scientific question is not whether GPQA is harder; it is whether the current team supplies useful natural correct/wrong variation, and whether clean discussion uses it.

Hardness does not imply useful disagreement. Three agents can simply become wrong together. Changes between datasets also mix domain/content with difficulty, so the result will not isolate a causal effect of difficulty.

## Immediate study

Name: `qwen3-gpqa-diamond-support-001`.

Keep the existing Qwen3-8B, three preparation adapters, precise effective weights/precision receipt, non-thinking configuration, prompt, one-exchange protocol, temperature 0.7, top-p 0.8, top-k 20, 4,096 total context limit, and 256/64 output limits. Do not select among frozen/task-SFT/receiver-SFT arms using GPQA performance. Use frozen preparation only.

Select 32 questions before outcomes using fixed seed 20260924 and proportional high-level-domain stratification. These become development-diagnostic examples, not optimization data or an untouched final benchmark. The nominal remaining 166 Diamond items remain protected, subject to known duplicate-group handling. Do not assume a source split called `train` makes GPQA suitable for PACT training. Preserve dataset access terms and prevent public redistribution of raw benchmark text or decodable token arrays.

For each task generate three independent private packets. Reuse these exact packets in independent voting, independent frozen synthesis, and one clean synchronous debate followed by the same frozen synthesizer. Do not force disagreement or inject correct donors. Run all 32 tasks, not just mixed cases.

| Stage | Calls | Maximum generated tokens |
|---|---:|---:|
| Private answers | 96 | 24,576 |
| Clean revisions | 96 | 24,576 |
| Independent synthesis | 32 | 2,048 |
| Debate synthesis | 32 | 2,048 |
| Total | 256 | 53,248 |

Independent voting requires no extra model calls. This explicitly extends the earlier private-only 96-call idea so one bounded run can examine communication as well. All quantities above are ceilings, not measured costs. No optimizer, donor, attack, alternative-sampling, replay or option-scoring calls are included.

## Required answers from the report

1. Counts of initially zero/one/two/three correct agents, initial coverage, individual accuracy, and valid correct/wrong mixed-task support.
2. Different wrong options versus genuinely useful correct/wrong disagreement; parsing/truncation/abstention status reported separately.
3. Natural hold and repair opportunities, by distinct task, agent-context and focal-agent support.
4. Before/after communication transition counts, erasure, utilization, construction, readout loss, harmful revision and helpful repair.
5. Paired terminal outcomes for independent synthesis versus debate; voting as a simple additional baseline.
6. Actual cost and provenance. Historical ARC/LogiQA comparison is descriptive, not paired or a causal difficulty study.

## Decision after this one study

A prespecified practical screen of at least eight valid mixed tasks out of 32 is enough to design an attacked-communication follow-up; it is not statistical power or proof of PACT's motivation. A smaller positive count is sparse evidence. Zero mixed tasks means no observed support in this bounded configuration, not universal impossibility.

More mixed support with communication losses would motivate a bounded clean/exchange follow-up on development data and a separately chosen training source. More mixed support with no useful communication advantage makes independent synthesis/voting a serious alternative. Mostly shared wrong answers means GPQA has not resolved the underlying issue at the current budget. All-wrong teams that construct the answer still matter and must remain in the analysis.

No outcome automatically authorizes extra questions, seeds, reasoning budget, training or final evaluation. Do not make a new loss change solely because this screen or the prior small receiver study is negative. Correct-target donor rationale quality and learning-signal behavior remain separate questions.

## Delivery workflow

Codex implements and CPU-tests the bounded pipeline locally. The user reviews and pushes. Colab runs the pinned plan after access and effective-weight preflight. The returned private audit bundle contains raw evidence; the sanitized summary contains only safe metadata/counts. Codex analyzes it without reopening closed experiments.

For the complete implementation instructions, use `PACT_Codex_GPQA_Support_Study.md`.
