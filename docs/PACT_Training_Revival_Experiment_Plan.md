# PACT training revival — experiment plan

16 October 2026. Proposed design, not executed evidence.

## Decision

Return to training three communicating heterogeneous agents, with a frozen final readout. Start by establishing that supervised receiver training changes useful behavior. Then measure the value of actual short adapter updates for choosing future specialization responsibilities. Do not resume the checker/gate project or the closed original replay experiment.

The original PACT question is retained: does complementary capability training need to co-adapt with the communication process that makes those capabilities useful? Its implementation changes: heterogeneous backbones, dense answer-prefix supervision, prospective training-update probes instead of waiting for natural correct/wrong packet pairs.

## Architecture

Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, and Mistral-7B-Instruct-v0.3 each receive one trainable LoRA adapter. An agent's adapter is used for both its private and revision turns. Qwen3-8B remains a frozen, non-thinking readout. One large model is resident at a time. Model revisions and native tokenizer/template identities come from the repository's verified registry.

The trusted task and original private states are immutable during exchange. One fixed malicious outgoing packet replaces one sender's delivered message; both recipients receive the same replacement. The sender retains its own original private state. This is not a compromised model-weight or arbitrary malicious-policy experiment.

## What starts now: Stage I

Compare three teams:

| Team | Updates |
|---|---|
| Frozen QLM | None |
| Independent adversarial SFT | Correct-answer supervision, own draft, same malicious incoming packet when applicable, but honest peers withheld |
| Uniform joint SFT | Same targets/budget plus real helpful and misleading peer contexts |

Both training arms update all three adapters from identical per-family initialization. Their private loss and receiver-example weights are matched. Both teams use the same full communication protocol at evaluation.

The target is the correct answer prefix, not a fabricated correct rationale. All tasks can supply answer supervision without sampling a correct revision or a same-prompt preference pair. Full packet generation remains the behavioral evaluation. Report answer-loss changes, answer accuracy, output-contract validity and rationale length separately.

Two epochs per adapter; 128 optimizer updates per adapter, 768 committed main updates over six fitted adapters. This is not two PACT outer refreshes. A small disposable engineering overfit check has an additional maximum48 optimizer steps; its outputs are not generalization evidence.

## Data boundaries

| Split | ARC train | Original English LogiQA train | Total |
|---|---:|---:|---:|
| Main fitting | 256 | 256 | 512 |
| Allocation probes, locked until Stage II | 32 | 32 | 64 |
| Validation | 64 | 64 | 128 |
| Source evaluation | 128 | 128 | 256 |

Freeze all IDs and group exclusions before generation. Previously exposed tasks, the prior224 selective-correction groups, old230 MMLU/MuSR characterization groups and all protected groups retain their existing restrictions. Report a source shortfall rather than substituting benchmark test data or relaxing exclusions.

The allocation-probe labels influence training responsibility and therefore are training-use data, even though their tokens receive no gradient. Existing and new source-development findings are not final benchmark confirmation.

## Stage I outcomes

Primary: clean and fixed-exchange final team correctness. Also measure initial coverage, private accuracy, correct-packet erasure, receiver hold/repair, readout loss and construction.

Use a fixed64-task validation panel to compare receiver outputs with versus without honest peers, on identical pristine histories at each trained checkpoint. This separates receiver learning from simply becoming a better standalone solver. These common-history tests are not on-policy team rollouts.

Keep all negative results. No minimum correct/wrong pair gate, threshold relaxation, indefinite sampling or extra epochs to manufacture a gain. Numerical/access/recovery problems are technical stops; low improvement is a scientific result.

## Stage I budget

| Component | Maximum new calls |
|---|---:|
| Fitting private packets, three per task | 1,536 |
| One attack attempt for each fitting/validation/evaluation task | 896 |
| Three final teams,384 validation/evaluation tasks,11 calls per clean+exchange pair | 12,672 |
| Extra fixed-history receiver comparisons | 1,920 |
| Scratch sanity post-update generations | 6 |
| **Total** | **17,030** |

At512 output tokens per call, the ceiling is **8,719,360 reserved output tokens**. Actual input tokens, training forwards, loading and compute-unit usage are separate. These are not expected consumption or time estimates.

Maximum main supervised sequence forwards:18,432, plus48 scratch forwards. Generation calls and gradient-bearing forwards must never be merged into an independent-observation count.

The first Colab action after plan/preflight is a SIX-CALL source smoke: one fixed fitting task per dataset, answered by all three pristine models. It is included in the budget and exports before continuing. All subsequent training/evaluation stages are explicitly invoked; Run All does not launch the portfolio.

## Stage II: actual learning-value assay

Implemented in the same update, but not automatically executed after Stage I.

Starting snapshot: the fixed final uniform-joint team, not whichever checkpoint appears best. Eight64-task fitting blocks (four per source), each paired with eight disjoint same-source allocation probes. These blocks are hash-defined batches, not claimed semantic specialties.

For each block and each agent:

1. Restore the identical source snapshot.
2. Train only that agent's temporary adapter on the block's private targets for eight steps.
3. Evaluate the corresponding probe tasks under clean/exchange, using two paired generation seeds.
4. Regenerate its private answer and all affected revisions/readouts; reuse only unaffected private packets by exact identity.
5. Measure terminal correctness and frozen-readout answer NLL changes.
6. Restore and discard temporary learning state before the next branch.

The same adapter changes private and revision behavior, so the observed effect is the total consequence of that private-training update. It is not pure message influence, a derivative, or an estimate of future long-run training gain.

24 temporary updates,192 optimizer steps total. The generational ceiling is4,928 calls /2,523,136 output tokens, including64 attack attempts and two paired suffix/source draws. Up to1,792 additional teacher-forced scoring sequences and1,536 temporary supervised forwards are separately counted.

Proposed responsibility matrices are analysis products only. Equal/negative/noisy scores remain such; no agent differences are fabricated or artificially magnified. Compare uniform, local and terminal matrices with a source-stratified row shuffle. Subsequent actual training is needed to validate their usefulness.

## Stage III: coupling interfaces, not an automatic experiment

Implement/mock-test at least two outer refresh rounds, static versus refreshed responsibilities, local and terminal scores, uniform and shuffled controls, and split versus coupled scheduling. A new finite plan must specify loss weights, arm/data/query exposure, checkpoint rule and budgets before any real coupled-training run.

The first positive result must be receiver learning. The second must be useful allocation beyond equal training. The third must be useful refresh beyond static/split training. Partial successes support only their corresponding claim.

## What not to do

No extra judges, frontier APIs, five-agent expansion, new MATH/GPQA runs, MBPP execution, LiveBench sourcing, original replay recovery, semantic reviewer/spans, CPU gate tuning, or automatic full-PACT result claims. No raw private task data in Git. The next result should concern trained agents, not another trained decision gate.
