# Methodology addendum: receiver_supervision_v1

Status: implemented locally; **Qwen3-8B training and all new study outcomes remain
GPU-unverified**. This addendum implements the explicit
[receiver-supervision update](PACT_Codex_Receiver_Supervision_Update.md). It does not
rewrite the original proposal or historical runs. The completed 72-call answer-only
control remains closed (45/72 correct in both conditions; no receiver outputs).

## Scientific change and loss routing

For an eligible, frozen receiver history h and official training label y, minimize
answer-field CE under the **unchanged packet revision prompt**. No successful
receiver sample, negative completion, pair selection or reference likelihood is
required. This changes the data/learning objective, not private replay, continuation
credit, the responsibility solver, specialization objective or deployed protocol.
DPO is not mathematically restricted to natural self-sampling; that was the old
project data recipe. This study tests a simpler supervised alternative.

`warmstart.prepare_examples` previously executed private clean answer-only JSON+EOS
supervision. It did **not** already execute CE on receiver histories. The new
`receiver_supervised_only` examples therefore add receiver-context supervision.
The standalone study does not also call an inherited `L_base` on those examples.
Its receiver arm optimizes `L_rx + 0.1 L_clean_anchor`; the task-only arm optimizes
`L_task + 0.1 L_clean_anchor`. The explicit clean anchor is a second forward with
weight 0.1 in **both** arms. In the task-only arm its prompt and target equal the
primary task example, giving an intentional total coefficient 1.1; this is logged,
not an accidental extra base-loss route. Both use the normal private packet prompt
for the anchor/control, not the closed answer-only diagnostic prompt.

The integration interface is
`base + lambda_spec*specialization + lambda_rx*receiver + lambda_dpo*dpo`.
The first-study preset fixes `lambda_rx=1`, `lambda_dpo=0`; the runner rejects a
nonzero DPO coefficient instead of pretending to execute it. Existing strict DPO
builders, immutable reference scoring and losses remain available unchanged. The
interface accepts DPO only when its caller supplies a validated legacy DPO loss;
missing pairs/references fail explicitly if enabled. Wiring joint specialization,
DPO and supervised refreshes into a full trainer remains deferred.

## Target contract: receiver_answer_ce_v1

The packet schema permits answer-first JSON; no mandatory rationale-before-answer
contract exists. A valid normal packet begins with `{"answer":"B"` and continues,
for example, with `,"justification":"..."}`. We teacher-force **only that incomplete
prefix**. Neither `}` nor EOS is appended. There is no rationale target. Formatting
before the answer is fixed and independent of y. System/user messages contain only
the original task, own saved packet and delivered peer packets, with no evaluator
tags or target injection.

Joint tokenizer offsets identify tokens overlapping the JSON-escaped answer string.
Prompt, peer, pure-formatting and padding tokens have zero score mask. If a token
indivisibly spans an answer character and a delimiter, it is scored and its exact
offsets are recorded; delimiter-only tokens remain masked. Changed prompt-token
boundaries, overflow, empty targets and EOS in the prefix fail explicitly. There is
no truncation or fallback to another target. CE uses logits at position `t-1` for
scored token `t`, normalized by answer-token count within each example.

The [exact synthetic fixture](../tests/fixtures/receiver_answer_ce_v1.json) includes
the complete receiver input, rendered prompt, all IDs/offsets/masks, prefix and
supervised positions. Its transparent character tokenizer is explicitly **not**
Qwen's tokenizer. In that fixture, the full sequence has 776 tokens; only position
774, token ID 67 (`B`, ord+1), is scored. The other 775 positions are masked. A
locally initialized tiny Qwen checks this exact fixture against an independent
log-softmax calculation. Real Colab tokenizer contracts are written to
`target_masks.json` and each arm's `examples.json` before updates, and held-out CE
records preserve their masks. These training-prefix records are never parsed or
counted as generated model packets. Evaluation supplies no prefix to generation.

## Frozen membership, contexts and weights

The versioned preset and frozen selection live in `experiments/receiver_supervision*`.
The audited 1,200-task pool supplies 96 fresh official-training groups: 32 ARC and
32 LogiQA fit groups; 16 ARC and 16 LogiQA held-out groups. All 120 prepared IDs and
24 previously probed IDs, plus their known group/content duplicates, are excluded.
Membership is outcome-independent and hash-checked. This is diagnostic holdout
within training data, never final-test evaluation. Existing lexical grouping does
not establish absence of every semantic paraphrase.

Each selected task gets three normal initial private packets and four extra private
draws from the **one prespecified focal actor**. The full fixed allowance is used;
there is no success-conditioned seed search or replenishment. All initial states
are frozen before any delivery. Eligible natural contexts are preferred. Otherwise
traceable same-task sampled alternatives may supply the own saved state and/or one
sender's peer text, explicitly marked `source=curated`. Original histories, changed
own-state flag, original donor actor, donor packet/hash, delivered sender and raw
replacement bytes are retained. After deterministic eligibility selection, sender assignment alternates across
retained curated contexts within each partition/stratum (counts differ by at most
one), without new samples or changing any donor text. No natural team private state is modified to manufacture disagreement.
No message is fabricated from a label; no donor rationale is certified as a proof.
Reviewed external donor ingestion beyond this sampled-bank format is deferred.

Hold requires a valid initially correct own answer and misleading peer answer.
Repair requires a valid initially wrong own answer and an answer-correct same-task
peer. Baseline receiver completion class is irrelevant. Separate deterministic
selection caps each fitting stratum at 32 contexts and each held-out stratum at 16.
At least eight fitting and four held-out **distinct tasks per stratum** are required;
otherwise status is `insufficient_context_support`, with unsupported sources and
costs retained. This is a possible data blocker, not evidence learning is impossible.

Each context weight is `0.5 / N_tasks_in_stratum / N_contexts_for_task_in_stratum`.
Thus each stratum contributes half, each original task within it contributes equally,
and repeated contexts cannot create support or extra task weight. Missing strata
are never silently renormalized. Microbatch-one gradients retain these global
weights; each logical update multiplies them by the number of batches in that pass,
so the mean across a pass equals the declared objective. A short final batch is not
renormalized. The preset uses batch four, two passes, at most 32 updates, AdamW
LR 1e-5, betas (0.9,0.999), epsilon 1e-8, weight decay zero, no clipping/scheduler.
This optimizer policy is new-study configuration, not a claim of optimality.

## Arms and evaluation

All arms start at the reviewed final 90-update preparation. Frozen has no updates;
task-only and receiver SFT load identical initial bytes into independent processes
and fresh optimizers. Only focal agent0's existing q/v LoRA parameters train;
backbone, other two actors and frozen reference copies remain unchanged. Both trained
arms have exactly the same selected labels, multiplicities, order and clean anchors.
Their prompt lengths differ, so this is not an exact FLOP match. The same updated
adapter serves private **and** revision turns during later natural-team evaluation.

Both trained arms must finish their declared last update before any held-out model
outcomes. No held-out checkpoint selection. All arms share frozen receiver histories,
actor role, node seed and decoding, with exact comparison joins. An identical
peer-withheld intervention preserves task/own state and removes peers. Report hold
retention/harm, repair success, valid wrong options, abstentions, parse/length failures,
unique-task/context denominators, teacher-forced CE separately, paired transitions,
and descriptive original-task bootstrap differences. No improvement over frozen
alone establishes peer use; compare receiver SFT with task-only and peer-withheld.

Each arm also generates 32 ordinary focal private answers and eight prespecified
natural teams under clean and exchange conditions. Team smoke retains the existing
fixed attack semantics, common attack bytes/site and node seeds, one synchronous
exchange, revised-packet base readout with adapters disabled, and original c/u/k/d/r,
coverage, erasure and repair metrics. Frozen-history results and curated results
are not natural updated-team trajectories. Denominators are small and there is one
training seed; no powered efficacy or full-PACT claim follows.

## Execution and recovery

See the [ordered Colab cells](receiver_supervision_colab.md) and identical thin
[notebook](../notebooks/04_receiver_supervision_colab.ipynb). Plan/report/export need
no model; GPU stages require `--execute`. The dry run verifies source ZIP/data
hashes, exclusions and ceilings before inference. Missing initialization tensor
files fail before backbone loading. Existing compact preparation restoration is
used only for **new initialization**, never as optimizer recovery.

Full new checkpoints save all actor adapter tensors, the focal optimizer and RNG
at every update boundary. Resume checks code/config/data/initialization/context/
tokenized-example/schedule/arm identity. Every attempted generation has an immutable
request journal; replay verifies snapshot, full prompt, seed and decoding. Scoring
also has an attempt/result journal. Unknown attempts block automatic regeneration.
Durable unsafe markers precede work; only the newest safe, verified full snapshot
can restore after a reset. Scratch recovery can prove a completed boundary from
its local journals/checkpoints. No rollback to an older safe snapshot is allowed.

Artifacts are scratch-first; bounded workers persist checksummed objects/snapshots.
Local metadata review ZIPs are created even on failure; full tensors are omitted
and explicitly inventoried. The new larger review/restore bounds are scoped to this
study (10,000 files, 256 MiB review metadata); legacy reader defaults remain unchanged.
Use `read_receiver_supervision_review(path, sha256)` for local checksum verification.

Deferred: vetted full-rationale targets, external reviewed-donor format, multiple
focal agents, all-agent refresh, specialization/continuation-credit training coupling,
enabled DPO in this study runner, archive/ignore-peers/SAC composition, adaptive
attacks, broader tool transfer, and final-test/paper claims. None are silently marked
complete by successful receiver SFT. Historical replay, solver and DPO code remains
unchanged and covered by existing regressions.
