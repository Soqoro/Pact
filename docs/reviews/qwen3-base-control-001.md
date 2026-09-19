# Completed fixed-context base control — 2026-09-19

The returned 54-call diagnostic passes the offline artifact audit. The unadapted
base also has zero correct receiver completions and zero hold/repair preference
contexts. This fulfills the prespecified diagnostic, but does not establish that
the warm start caused the receiver shortage. Full revision training remains gated
by missing actor preferences. No optimization or final-test evaluation occurred.

## Integrity and execution

Archive `qwen3-base-control-001-handoff-1789830893982847246.zip`: 165,411 bytes;
SHA256 `49bf59ceaeabcd917a91db4fef0ab0ed92fb05a367bd5233c05bc1fe3e1dc954`.
All 63 safe archive members, 62 payload checksums and 115 inventory entries pass.
The 54 omitted shard-marker hashes are reconstructed from the included raw bytes.
No archive code is executed. Originals are preserved under ignored
`results_import/qwen3-base-control-001-review/`.

Clean source commit `80992b48f9159c427d65e87cbd80849af295021b`, source hash
`8c36005865aec6f91af273e71e781f1a59dd816b88c16262c9def1901272c3b4` matches local
executable source. The plan reconstructs exactly from the previously verified
completed-bank ZIP, including the source hash, bank hash, all 54 requests and 12
groups. Selection digest remains
`31f2d542eb0d8cafb813d1cecb2b198ea605bc74f687b5d720d9f6b2cffe56b4`.

Every new call matches its saved actor prompt, messages, token prefix, node seed,
phase and complete sampling parameters. All use actor `base`, no adapters,
Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, BF16/SDPA and disabled
thinking. Model/tokenizer/template/weight hashes and runtime fingerprint match the
original bank. No label or stratum is added to the saved defender messages.
Token lengths, EOS, context limits and raw-output associations pass. The original
report is reproduced exactly from raw records; all groups are complete.

## Outcomes

Counts refer to sampled completions on the same fixed contexts, not independent
tasks. All receiver contexts concern `logiqa:train-7374`, official gold A.

| Context | Saved warm-start actors | Fresh base |
|---|---|---|
| ARC clean private, 15 calls | 0 correct, 15 wrong | 0 correct, 15 wrong |
| LogiQA clean private, 15 calls | 6 correct, 9 wrong | 7 correct, 8 wrong |
| LogiQA hold, 8 calls / 2 contexts | 0 correct, 8 abstentions | 0 correct, 8 abstentions |
| LogiQA repair, 16 calls / 4 contexts | 0 correct, 14 wrong, 2 abstentions | 0 correct, 16 wrong |

Private LogiQA correct counts by original agent are 3/5, 0/5, 3/5 for actors and
3/5, 1/5, 3/5 for the base. Both ARC and LogiQA retain their official labels.
The previously noted LogiQA wording concern remains a possible item confound,
not a reason to relabel or exclude this completed result.

Matched actor-to-base outcomes are six correct-to-correct, one wrong-to-correct,
37 wrong-to-wrong, eight abstention-to-abstention and two abstention-to-wrong.
Thirty-five of 54 raw strings and completion-token arrays are identical; the
remaining 19 differ. Both policies still yield zero receiver pairs. Abstentions
remain failures and do not become preference negatives. All 54 base calls end
at EOS, with no malformed, invalid-answer, length-limit or overflow output.

## Resource and persistence evidence

One recorded attempt, 54 fresh generations, zero cache hits: 16,995 input tokens
and 3,275 output tokens, below the 13,824-output-token cap. Summed generation time
is 226.624 seconds. Invocation time is 343.519 seconds (5.73 minutes), including
a 57.588-second model load and periodic snapshots, excluding final snapshot/ZIP
operations. Peak allocated/reserved bytes: 16,515,663,872 / 16,607,346,688.
Maximum prompt plus reserved output is 695 tokens. Compute units are unknown;
this does not establish full-context memory fit.

Status is `diagnostic_complete_local`, 54/54, exit zero. The handoff receipt reports
verified snapshot:

`/content/drive/MyDrive/PACT/diagnostics/qwen3-base-control-001/snapshots/1789830893946689797-d4fc812509bb`

The user supplied the final Drive bundle path and matching outer ZIP checksum.
Nested receipt path/hash/size identify the preceding local review ZIP; its
`persistent_bundle=null` predates final ZIP copying. The manifest's false
persistence flag likewise predates snapshot verification. These staged fields
are expected. Current Drive contents, diagnostic resume and post-reset restoration
are not independently verified by this archive. The metadata ZIP is not a resume
archive; preserve the durable object store.

## Decision and limits

Apply the prespecified no-correct-base-receiver branch: this comparison does not
support attributing the missing pairs to the small answer-only warm start. It also
does not prove that the warm start had no effect. One extra correct private base
sample on one item cannot establish a capability difference. The control receives
actor-produced peer contexts, so it is not an independently generated base team,
a held-out accuracy estimate, or evidence of PACT efficacy.

Close this bounded diagnostic. The next local task is to design and freeze a
broader training-only feasibility selection with fixed sample/query caps and
outcome-independent task selection. Review task wording, prompts and context
support before declaring the recipe; retain missing classes and report both
hold and repair denominators. Do not repeat this diagnostic, expand sampling
until pairs appear, manufacture positives, or launch full revision optimization.
GPU frozen-reference scoring and full PACT updates remain unverified/deferred.

Reproduce the offline audit against the recorded executable source:

```bash
PYTHONPATH=src python results_import/qwen3-base-control-001-analysis/audit.py
```

The audit, recomputed report and metrics are retained in that ignored analysis
directory. No executable source changes or suite rerun were needed for this review.
Model probabilities and tokenizer decoding were not recomputed locally; weights
and tokenizer assets are represented by recorded hashes, not included bytes.
