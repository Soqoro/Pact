# Completed training-bank review — 2026-09-19

The six-record engineering collection passes the returned-artifact audit. Resume
preserved the first record, and the complete bank and preference accounting
reconstruct from the raw traces. This stage is complete; no further Colab run is
requested. The bank has no usable receiver preferences, so the full revision
objective is not ready. No adapter optimization occurred in this collection.

## Archive, resume and persistence

Archive `qwen3-bank-001-handoff-1789804954424856576.zip` is 149,828 bytes with SHA256
`a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`, matching the
user's receipt. All 19 safe archive members and 18 payload checksums pass. All 23
inventory entries match included bytes or the six excluded shard-marker hashes,
recomputed from the corresponding shard files and marker newline convention.

The clean source remains `12861a1ca4dce794a1f4daaa27e02618fed2956e`, source hash
`17a43e51f98f28f5e01ec96f85ee4054bcdefb5a035f265bdf1fbe3217dc1e52`. Recipe, data,
model, reference and runtime identities match the first reviewed run. The first
shard and first resource-attempt record are byte-identical. Data manifest, plan,
model identity and package inventory also remain byte-identical. Continuation
generates exactly the five remaining records: 199 new calls, with no regenerated
first-record calls. This verifies fresh-process collection continuation; it does
not verify post-reset restoration from Drive.

Status is `collection_complete_local`, six of six, exit zero. Both the archive
receipt and supplied log report the final verified snapshot:

`/content/drive/MyDrive/PACT/collection/qwen3-bank-001/snapshots/1789804954384930583-a1a797f59f54`

The supplied log additionally reports successful handoff ZIP copying. The archive
receipt was created before that copy and retains the previous local-review ZIP's
path/hash plus `persistent_bundle=null`. The local manifest's false persistence
flag also predates final verification. These staged fields are expected. Current
Drive contents cannot be independently checked here. Preserve the whole durable
run directory, including `objects/`; the review ZIP excludes shard markers and
tensor files and is not a resume archive.

## Audited behavior

The CPU audit reconstructs every scheduled task/attack identity, all 218 generated
calls and their exact defender messages, templates, seed assignments, generation
parameters and raw answer parses. It checks actual stored token arrays against
call lengths, EOS, prompt associations and context limits. Both early and exchange
attack assignments match the fixed pool. Every revision sees initial packets;
every final readout sees only revised packets and is assigned to the base actor.
No evaluator label or hold/repair tag is inserted into defender inputs.

| Training task | Condition | Initial answers | Revised answers | Final | Private pairs |
|---|---|---|---|---|---|
| ARC MCAS_2004_5_13, gold B | clean | C / C / C | C / C / C | C | 0/3 |
| ARC MCAS_2004_5_13, gold B | early | D / D / D | D / D / D | D | 0/3 |
| ARC MCAS_2004_5_13, gold B | exchange | C / C / C | C / C / C | C | 0/3 |
| LogiQA train-7374, gold A | clean | A / B / B | abstain / abstain / B | abstain | 2/3 |
| LogiQA train-7374, gold A | early | B / B / B | B / B / B | B | 0/3 |
| LogiQA train-7374, gold A | exchange | A / B / B | abstain / abstain / B | abstain | 3/3 |

All six main trajectories fail. Correct initial coverage occurs in the two
LogiQA clean/exchange records and disappears during revision in both. These are
two selected training tasks already used in the warm start, not a held-out
effectiveness estimate or evidence of regression against a matched control.

Five of 18 private contexts produce usable, length-bin-matched pairs; 13 lack a
correct candidate and retain null credit. All 20 suffix branches (80 calls) pass
attack-byte/site, other-private-state and paired node-seed checks. Four credits
are zero. LogiQA exchange agent2 has credit +1: both positive branches succeed and
both negative branches fail. The exchange sender is agent1; substitutions for
that corrupted sender also preserve the same outgoing attack to both recipients.
This reproduces the estimator at K=2, not a robust effect-size estimate.

Receiver accounting has two hold contexts, four repair contexts and 12 ineligible
contexts. All 24 sampled receiver candidates lack a correct answer: 14 valid wrong
answers and 10 abstentions. The two hold contexts each produce four abstentions;
the repair contexts produce 14 wrong answers and two abstentions. Thus both
preference counts are zero and `full_revision_ready=false`. No reference-cache
entries or frozen-reference forwards exist; this is the correct empty outcome.

Eighteen actor answer-NLL forwards and five selected positive-packet NLL forwards
execute across both invocations. Their prompt/target/actual-token provenance,
terminal EOS, finite sums, counts and mean reductions check out. All bank rows
and contexts reproduce, as does complete preference accounting. Bank hash:
`30586d9503f0cab543c24d9ec0259c88561fa8a7180172ad63a0edec98f36e4b`.
The GPU numerical probabilities are not independently recomputed locally; actual
weights/tokenizer files are absent from this metadata archive.

## Resources and warnings

Across both invocations: 218 generation calls, 76,067 input / 10,588 output tokens,
23 teacher-forced forwards with 5,814 combined input tokens. All 218 generations
end at EOS: 165 valid answer parses and 53 abstentions; no malformed, length-limit
or context-overflow completion. Maximum prompt plus reserved generation length is
723 tokens. Summed generation time is 767.484 seconds.

Continuation takes 775.588 seconds, including a 9.695-second bare-model load and
periodic snapshots. Both invocations total 956.451 seconds (15.94 minutes), excluding
their final ZIP/snapshot operations and time between notebook commands. Continuation
peak allocated/reserved memory is approximately 15.593/15.939 GiB. Compute units
are unknown. The runtime fingerprint matches the prior reported L4 environment;
there is no fresh hardware-name report or full-context memory profile in this ZIP.

The supplied `torch_dtype` deprecation and TensorFlow startup notices did not
prevent successful execution. Stored actor calls retain sampling parameters and
the final readout has `do_sample=false`; the generation-flags warning alone is
not evidence that actor sampling was disabled. Separate stdout/stderr display
order should not be treated as proof of a second run after the completion receipt.

## Evidence and next step

Original archive files are preserved in `results_import/qwen3-bank-001-complete-review/`.
The audit script, report and derived metrics are in
`results_import/qwen3-bank-001-complete-analysis/`. Reproduce the CPU audit with:

```bash
PYTHONPATH=src python results_import/qwen3-bank-001-complete-analysis/audit.py
```

No executable source repair or suite rerun was needed for this artifact review.
The executed GPU path now includes frozen-team generation on all six cells,
paired suffix replay, positive-packet scoring and compatible collection resume.
GPU frozen-reference scoring, post-reset bank restoration, full revision
optimization and PACT efficacy remain unverified.

The next local task is a bounded, training-only preference-feasibility design:
inspect the failed receiver contexts and specify how to test correct-completion
availability while preserving same-prompt pairing and both strata. Do not silently
expand sampling, manufacture positive answers, reuse validation traces, substitute
base scores for frozen references, or start a reduced objective as full PACT.
Another GPU invocation needs a concrete reviewed recipe; repeating this completed
bank is not the next step.
