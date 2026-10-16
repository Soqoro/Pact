Update my EXISTING PACT repository according to:

docs/PACT_Codex_Heterogeneous_Training_Revival.md

Read it fully. Inspect AGENTS.md, Git status, the original proposal, latest research/
gate/selector audits, actual training backend and exposure ledger. Preserve unrelated
work and immutable historical results. Reuse the current package and tested CLI.

This is an IMPLEMENTATION request to return to training the communicating agents,
not another judge, checker or KEEP/SWITCH gate.

## Build the complete next experiment

Implement pact-heterogeneous-receiver-training-001:
- Frozen Qwen2.5-7B / Llama-3.1-8B / Mistral-7B control.
- Independent adversarial SFT: train all three adapters with honest peers withheld.
- Uniform joint SFT: train all three adapters with natural delivered peer messages.
- Same pristine frozen Qwen3-8B readout for every arm.

The independent arm retains the SAME malicious incoming packet where applicable,
so it is not a weaker control denied attack exposure. At evaluation both trained
teams use the same full one-exchange protocol.

Use three LoRA adapters on their respective backbones, sequentially resident.
Same adapter for private and revision turns. Native tokenizers/templates, audited
FP32 adapter states, BF16 backbones/SDPA,512 output tokens and8192 total context.
Pin actual existing model revisions. No silent precision/model/mode changes.

Default LoRA r16/alpha32/dropout.05 on q/k/v/o projections; frozen other weights.
Use the full document's AdamW, masking, global weights and checkpoint contracts.

## Dense supervision and fair control

Supervise the correct answer-bearing assistant prefix under the actual receiver
input. Do not wait for same-context correct/wrong sampled responses or add DPO.
Do not invent gold rationales, train an empty justification, or teach a premature
EOS. Teacher-forced labels belong only in the masked target; evaluation generates
full packets without a gold prefix.

Implement native tokenizer-aware token masks, causal shift and boundary tests.
All wrong/clean/hold/repair tasks receive supervision. Stratum balancing is frozen
from the common fitting bank, clipped and globally normalized, shared across arms.
No gold/stratum/family labels enter defender prompts.

Update ALL SIX trained adapters from matched per-family initialization with fresh
optimizer states: two epochs,128 steps per adapter,768 main steps total. The first
scratch fit is disposable and bounded to48 total steps. Two epochs are NOT two
outer PACT refreshes. Fix epoch2 as primary; no accuracy-based checkpoint search.

## Source data and protocol

Freeze960 NEW groups using supported official ARC-Challenge training and ORIGINAL
English LogiQA training, equally by source:
512 fit /64 allocation probes /128 validation /256 source evaluation.

Exclude recorded prior uses, duplicate groups, protected items and the just-used
224 selective-correction tasks. Preserve the exposure-inventory freshness guard.
Report actual shortfalls, do not substitute or shrink after outcomes. Allocation
probes are training-use data, locked until the separately invoked probe stage.

Fit collection needs only three natural private packets per task; labels supply
revision targets. No unnecessary fitting readout/revision sampling. All private
packets freeze before synchronous delivery. The final readout sees only revisions.

One fixed malicious outgoing packet per task, same to both recipients, sender's
private state unchanged. One attempt, assigned wrong option chosen offline, no
victim feedback. Fit uses argument/verification styles; evaluation uses consensus/
independence styles. Preserve rejected attempts as missing attacked conditions.

Version an unambiguous answer-first two-key packet contract for this new study.
No parser salvage, force-disagreement or correct-answer fallback at evaluation.

## Evaluation and budget

Evaluate frozen/independent/joint final teams on all128 validation and256 evaluation
items under clean+exchange. Each team/task has3 shared privates +6 revisions +2
readouts =11 maximum calls.

Add the specified64-task fixed-history peer-present/peer-withheld diagnostic.
Its purpose is to distinguish actual peer-use learning from standalone improvement.
Keep on-policy team and off-policy receiver findings separate.

Stage I maximum:
-1536 fit private calls
-896 attack attempts
-12672 live validation/evaluation calls
-1920 additional fixed-history calls
-6 scratch post-update generations
=17030 calls /8719360 reserved output tokens.
Main supervised forwards<=18432 plus48 scratch forwards, separately counted.
First source smoke is SIX INCLUDED calls: two fixed fit tasks across three models.
Default notebook mode is plan/preflight; no automatic portfolio Run All.

## Implement the next allocation assay too, but gate its execution separately

Implement pact-update-allocation-probe-001 with24 temporary adapter branches:
eight64-task fitting blocks x three agents; eight disjoint probe tasks per block.
Start from the prescribed final uniform-joint snapshot, not the best-looking arm.

Each branch gets eight private-target optimizer steps with fresh temporary state.
Then run two paired seeds under clean/exchange, regenerate the updated actor's
private answer and all affected revisions/readouts, measure terminal correctness
and common-readout answer NLL changes, and restore EXACTLY before the next branch.
No probe labels/tokens enter training updates. No temporary state becomes committed
team training. Private and revision behavior can both change through one adapter.

Stage II maximum4928 generations /2523136 output tokens,192 temporary optimizer
steps,1536 supervised forwards and1792 diagnostic scoring forwards. This budget
is distinct and requires explicit invocation after review. Flat/negative scores
remain results; don't create differences through noise normalization.

Export uniform/local/terminal/shuffled allocation analyses with their limitations.
Implement a CPU/mock-tested two-round coupling orchestrator, static/refreshed and
split controls; actual coupled-training runs require a NEW finite MethodSpec and
budget. Do not auto-launch full PACT or call nonzero probe scores efficacy.

## Workflow and delivery

Local Codex -> my review/push -> pinned Colab -> returned evidence. Run CPU/mock
and tiny LOCALLY initialized neural tests only. No local pretrained downloads,
GPU/API calls, commits/pushes, secret reads or unrelated dependency migrations.

No new judge/gate,5-agent,GPQA/MATH,MBPP/LiveBench,frontier,semantic-review or old
replay run. Preserve deferred statuses and all prior negative findings.

Deliver actual collection/training/evaluation code, private/sanitized exports,
exact Colab commands, full mock round trip, gradient/reference and rollback tests,
entrypoint regression tests, budgets and recovery contracts. Missing real data
must not prevent fixture-backed implementation or become invented evidence.

Finish with changed files, tests actually executed, first six-call smoke commands,
per-agent training and evaluation commands, optional allocation-probe commands,
required access/artifact paths, expected handoff bundles and GPU-unverified limits.

Begin by inspecting the repository and reading the full specification, then build
the smallest COMPLETE three-agent training study and the separate update assay.
