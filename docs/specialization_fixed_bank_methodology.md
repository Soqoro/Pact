# Assignment contrast and fixed-bank specialization v1

Implements the authorized [update](PACT_Codex_Assignment_Contrast_Specialization_Update.md).
The existing receiver and GPQA runs remain closed; no GPQA data is read by this
study. This is an all-actor specialization ablation, not full PACT. Receiver CE,
DPO, outer refreshes, synthetic donor alternatives and final tests are absent.

## Real offline evidence

The sole retained complete natural training bank inspected is
`qwen3-bank-001-handoff-1789804954424856576.zip`, SHA256
`a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`.
Safe archive checks, original-context scores, pair selection, branch attack/private
state, paired node seeds, target tokens and per-seed differences reconstruct.
Two tasks, six condition rows,18 cells: four zero-eligible rows, zero singleton,
one two-eligible and one three-eligible row. Five supported cells; both supported
rows belong to one LogiQA task. Four credits are zero; exchange agent2 has+1.
18 original-context answer scores and five positive-packet scores are present.
No missing model score was filled, and no model ran locally.

Historical all-cell population-standardized NLL is retained for this report.
Mean L1 credit-versus-local is0.7705078615 across both eligible/multi rows;
local-versus-uniform is0.1122392611. Raw-NLL sensitivity yields0.7784436707 for
credit-versus-local. Both eligible rows change because the balance term couples
rows, even though only the exchange row has within-row credit variation.
The bank establishes actual assignment contrast, not learning efficacy. Only one
supported task is far below the eight-task minima, and its older nine-step actor
snapshot is not the new effective preparation identity. It cannot be a new-study
fitting bank. Validation replay remains separate diagnostic evidence, unused here.

Responsibilities (agent0/1/2), from actual retained data:

| Row | Uniform | Local | Continuation |
|---|---|---|---|
| LogiQA clean | .5 / 0 / .5 | .510404 / 0 / .489596 | .609919 / 0 / .390081 |
| LogiQA exchange | .333333 / .333333 / .333333 | .288292 / .435169 / .276539 | .009983 / .042486 / .947532 |

Both eligible rows have omega=1 and B=2, so their global packet-loss coefficients
are these responsibilities divided by2. Base coefficients are1/(3*6)=1/18 on
ALL historical rows. This is an offline illustration, not training of that bank.
A row-constant credit across the whole bank leaves the solution invariant;
a singleton row is fixed at responsibility one. A balance-mediated change on a
zero-credit row is not independent causal evidence for that row's continuation.

## New opt-in preset

`qwen3-specialization-contrast-001` uses32 fitting and32 development groups,
16 of each family in each partition. It uses the existing pinned1200-task
ARC-Challenge/original-English-LogiQA training pool. The local dry plan found240
excluded task IDs from preparation120, repeatedly inspected probe24, receiver96
selections (including earlier warm-start/engineering tasks). Exclude their known
groups/content as well. Fresh selection is seed20260925, stable SHA256 group rank;
no outcome filtering.64 fresh groups are available. Existing lexical overlap
screening cannot certify semantic paraphrase absence. No GPQA/test import exists.

All64 fitting condition rows receive one natural7-call anchor plus four ADDITIONAL
private samples per actor. Existing `choose_pair` selects correct/wrong samples by
32-token length-bin, distance, then indices; anchor excluded. Existing `probe`
executes K=2 matched positive/negative suffixes, receiver candidates set to zero.
The same original peers, early payload, snapshot and matched node seeds are used.
Negative and zero credits remain valid. Exact request/identity reuse can lower
actual dispatches; budgets count all attempted new dispatches, including ambiguity.

Clean and early only; the existing fixed-pool-v1 registry, seed-to-payload rule and
256-token payload cap are fixed. Plan records exact bytes; actual tokenizer counts
are checked and recorded on execution, not guessed during local planning.

Initial real weights are restored using the existing compact90-step preparation
restore and completed controlled frozen-arm receipt. Loader verification preserves
agent0 exactFP32 and agent1/2 FP32→BF16→FP32 effective values. The imported receipt
is not permission to train a closed receiver run. Each NEW arm reloads this same
initial team, with fresh per-actor optimizers. Final evaluation restores exact
in-memory training checkpoint tensors into that architecture, avoiding another
lossy PEFT export reload. The fixed BF16 backbone and references remain protected.

## Assignment and loss

New preset standardizes original-context answer NLL globally over eligible cells,
using population std; zero std uses scale1 and records the degeneracy. This is an
explicit versioned change from historical all-cell scaling. Uniform, local gamma0
and continuation gamma1 share masks, targets and transforms. Existing masked solver
uses tau.2, balance.1; nonconvergence stops. Assign once over the complete frozen
bank; no recomputation as actors update. Mean multi-row L1 must exceed1e-6;
this is a numerical nonidentity gate, not a scientifically sufficient effect size.
At least8 distinct fitting tasks must have pairs and at least8 must have a
multi-eligible row. Candidate support is checked before any suffix dispatch.
Missing required score/target/replay records prevent training. No receiver veto.

With U=64 and B eligible rows:

    L = sum(base_answer_NLL)/(3U)
        + sum_b,i(omega_b * R_bi * full_packet_NLL_bi)/B

omega is inverse(1+initial-correct-count), mean-normalized on eligible rows only.
Missing cells contribute no spec term, with no floor or0*NaN; their base targets
remain. Prompt/padding excluded; answer base is canonical answer JSON plus EOS,
no gold rationale; specialization is the original sampled full correct packet
including its terminal EOS. Both use shifted, mean completion-token NLL.

One microbatch row, four rows/update, global coefficients multiplied by U/4=16.
Averaging the16 fixed-parameter minibatch gradients recovers the full-bank gradient.
No per-actor weight normalization. Every supported packet forward executes in each
arm even if its numerical responsibility is zero, preserving target exposure.
Two passes,32 updates/actor,96/arm,288 total. AdamW lr1e-5,betas(.9,.999),eps1e-8,
weight_decay0,foreachFalse; constant LR, no scheduler; global active gradient clip1
inherited from preparation. Only active LoRA parameters have gradients. Resume
stores all actor values, active optimizer, RNG, global schedule position, masks,
examples and plan/bank/assignment hashes at optimizer boundaries. Unknown attempts
stop. All three learned adapters still serve BOTH private and revision turns;
receiver loss off does not mean a frozen revision policy.

## Evaluation, recovery and interpretation

Frozen plus three trained systems see the same32 development tasks in clean/early.
Per system/task/condition: three private packets, vote, base synthesis, synchronous
three revisions, base synthesis. Eight calls. Each system uses its own packets;
cache keys include actual effective snapshot, task/prompt/seed. No cross-arm reuse.
Reports reconstruct stored calls with trusted code, summarize each condition,
and pair outcomes by task with clean/early clustered. Report coverage over best
actor, all-correct degradation, unique coverage, valid mixed support, N0→N1,
u/k/d/readout loss, terminal protocols, and strength/utility trade-offs. More
wrong-answer diversity or larger assignment L1 alone is not efficacy.

Stages default to no model execution. Explicit plan hash and --execute required
for collect/replay/train/evaluate. Explicit arm required for train/evaluate.
No Run All loop launches the maximum budget. Pauses reuse known calls; uncertain
attempts cannot retry. Durable unsafe marker precedes fresh work; safe snapshots
follow checked boundaries. Restore only the latest verified snapshot; review ZIPs
omit tensors and cannot resume optimization. Local export precedes Drive writes.

The bounded budgets are1216 collection calls/299008 reserved tokens, at most3072
replay calls/638976 tokens,512 evaluation calls/106496 tokens per system;6336 total,
1363968 tokens. At most192 answer and192 packet scoring forwards. Realized masks
produce exact per-arm base/packet forward and target-token counts before training.
These are caps, not timing or subscription-cost estimates. No outcome automatically
permits another run, more candidates, new hyperparameters or full PACT refresh.
