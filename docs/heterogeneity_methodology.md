# Heterogeneous natural complementarity implementation

This implements the [2 October specification](PACT_Codex_Heterogeneous_Complementarity_Phase.md) as `heterogeneous_natural_support_v1`, run `pact-heterogeneous-complementarity-001`. It is a fresh, clean inference diagnostic using official frozen checkpoints. No training, attacks, donors, replay, scoring forwards, GPQA or final tests. Earlier results and the closed incomplete controlled child remain unchanged.

## Frozen model contracts

| Key | Official repository | Immutable revision |
|---|---|---|
| Q | Qwen/Qwen2.5-7B-Instruct | a09a35458c702b33eeacc393d103063234e8bc28 |
| L | meta-llama/Llama-3.1-8B-Instruct | 0e9e39f249a16976918f6564b8830bc894c89659 |
| M | mistralai/Mistral-7B-Instruct-v0.3 | c170c708c41dac9275d15a8fff4eca08d52bab71 |
| R | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 |

Constituent revisions were verified against the official [Qwen API](https://huggingface.co/api/models/Qwen/Qwen2.5-7B-Instruct), [Llama API](https://huggingface.co/api/models/meta-llama/Llama-3.1-8B-Instruct), and [Mistral API](https://huggingface.co/api/models/mistralai/Mistral-7B-Instruct-v0.3); R inherits the existing trusted ModelConfig revision. No weights or tokenizer files were downloaded locally. Native files are verified during explicit Colab preflight/load, with hashes recorded in receipts. Llama access requires the user's authorization.

Every model uses its own native template. Qwen receives an explicit common system message, avoiding the template's default identity text. Llama's template date is explicitly fixed to `02 Oct 2026`; native knowledge-date text remains. Mistral v0.3 natively folds the system content into the first user instruction. No manual Qwen-format conversion is used. Only R receives `enable_thinking=False`. Rendered text is tokenized with `add_special_tokens=False`; completion slicing uses the actual input token length. This follows the [Transformers chat-template guidance](https://huggingface.co/docs/transformers/v4.57.1/chat_templating).

Native EOS/end-of-turn IDs come from each pinned generation config; missing pad IDs use its first stop ID for batch-one inference. A fresh GenerationConfig plus explicit shared sampling fields prevents inherited checkpoint-specific forced/suppressed-token behavior. Library/runtime identity is frozen. BF16/SDPA, no adapters, no offload or quantization; actual parameter devices/dtypes are checked. Receipt metadata, file hashes and recorded runtime are evidence, not an independent later reload of omitted weights.

## Source and exact team binding

The trusted reader verifies the original raw pilot ZIP and its full checksum inventory, then imports only task inputs, separate labels, and source manifest. Frozen content digests additionally reject changes to the 80-task order, source metadata, labels, canonical option mapping or benchmark text. All 80 tasks remain development-exposed. No source record is replaced.

Within each 40-task dataset, a seeded permutation schedule balances the six family-to-slot permutations (counts differ by at most one). For example, if slots 0/1/2 are M/Q/L:

| Team | Slot 0 | Slot 1 | Slot 2 |
|---|---|---|---|
| QLM | P[M,0] | P[Q,1] | P[L,2] |
| QQQ | P[Q,0] | P[Q,1] | P[Q,2] |
| LLL | P[L,0] | P[L,1] | P[L,2] |
| MMM | P[M,0] | P[M,1] | P[M,2] |

The source packets are never mutated or selected using labels. Display envelopes are `peer-1`, `peer-2`, `peer-3`; source family remains audit metadata. The common private prompt contains task/options and an empty advisory, with no actor/team wording. A fictional output is `{"answer":"A","justification":"Fixture only."}`. All completion tokens are generated; there is no supervised target or scored-token mask in this study.

Revision prompts reuse `revision_prompt`: own saved packet plus the two initial peers, ascending anonymous slot order. Readouts reuse the existing semantic readout instruction and task/packet serialization, with the same fixed source order for private and revised synthesis. This explicitly frozen order differs from the legacy per-task shuffled display; no outcome-driven order selection is performed. Task-only uses the same readout with an empty packet list. Voting preserves the existing tie/all-invalid abstention policy. Strict length/parser failures remain failures; context overflows remain separate infrastructure missingness and do not get shorter retries.

Revision seeds are coupled by task, family checkpoint and replica, so the selected mixed sample has the same revision seed in its homogeneous team. Different peer contexts remain different cache requests. The nine-private-packet per-task barrier and normal global private-bank barrier are enforced. The two-task smoke has exactly the same identities and exceptions stated in the specification.

## Analysis and interpretation

Reports aggregate QLM members by family, with slot summaries separate. They include per-replica and pooled private accuracy, designated single-family baselines, N0 distributions, coverage gain above the best observed member, unique coverage and pairwise rescue, valid mixed support versus wrong-answer diversity, strict parsing rates, transitions, natural hold/repair, utilization/construction/erasure/readout loss, and paired protocol outcomes. Missing observations retain support counts; optional conservative full-cohort terminal lower bounds are labeled separately. Complete-valid-team sensitivity never replaces primary results.

Paired bootstrap resamples whole task records within dataset, retaining team/replica dependence. Derived best-member and best-homogeneous maxima are recomputed in each draw. Best observed models are descriptive selections, not a deployable router. Boundary estimates retain uncertainty; degenerate intervals are inconclusive. Logical deployment costs reuse shared private calls; actual experiment costs charge each source request once. Cross-tokenizer counts and equal caps do not establish matched FLOPs or billed compute.

No positive-support gate skips communication. Readout construction is separated from useful private coverage. No outcome authorizes another run or supports a trained-PACT claim. This is an adapted model-diversity diagnostic, not an exact reproduction of the paper cited by the user.

[Exact Colab instructions and recovery boundaries](heterogeneity_colab.md).
