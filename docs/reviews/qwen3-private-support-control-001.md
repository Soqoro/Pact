# Completed private-support seed control — 2026-09-20

The returned 72-call control passes the offline artifact audit. The second draw
has **24/24 unanimous private teams and zero potential clean-repair contexts**.
Changing the seed did not resolve the observed support shortage. This closes the
prespecified single additional draw; it does not authorize searching more seeds
until mixed teams appear.

## Integrity

Archive `qwen3-private-support-control-001-handoff-1789909726537323854.zip`:
434,491 bytes; SHA256
`f67045fc3f2bc102e7345ba3337c5406796360e76f437355dd849302cb33bc06`.
All 225 safe archive members, 224 payload checksums and 367 inventory entries
pass; 144 omitted checksum markers reconstruct from the original JSON bytes.
Imported artifacts are read as data, never executed.

Clean published source `91655a83503a466c4f773a49053d86b54fb71cab`, executable hash
`8b5eb9a5af5c2b9dfb4f6d3e42b4ccb30193bf75cfef03bf49607f9f0fba3d44`, matches the
reviewed implementation. The plan reconstructs exactly from the pinned completed
receiver ZIP, with request hash
`98e749e8b4d2c3fe20f8a3643af7fc8e362febff4a4ae7dae1450cbbf5333571`.
Task selection, labels and frozen actor/base identities match the parent run.
Model/tokenizer/template metadata, BF16/SDPA, disabled thinking and the reported
L4 runtime fingerprint also match.

All 72 intents have verified results and derived records. Offline journal replay
reconstructs every private request without new generation. Prompts, messages,
actual prompt-token prefixes, sampling parameters and source identities match
the original draw; seeds follow the declared 1730 derivation. Token lengths,
context caps, terminal EOS and raw-output associations pass. The full report
recomputes exactly. No revision, readout, reference score or optimizer step ran.

## Paired results

| Measure | Original seed 1729 | Control seed 1730 |
|---|---:|---:|
| All three correct | 15/24 tasks | 15/24 tasks |
| Mixed correctness | 1/24 | 0/24 |
| All three wrong | 8/24 | 9/24 |
| Unanimous valid answer | 23/24 | 24/24 |
| Potential clean-repair contexts | 2 | 0 |
| Correct private answers | 46/72 | 45/72 |

ARC changes from eight all-correct, one mixed and three all-wrong tasks to eight
all-correct and four all-wrong tasks. LogiQA remains seven all-correct and five
all-wrong tasks. All 72 control outputs parse successfully and end at EOS; none
abstains or overflows. Unanimous wrong teams select the same wrong answer.

The only answer change is agent 2 on `arc_challenge:Mercury_406916`: A (correct)
to B (wrong). Its two teammates already answer B. The private correctness
transitions are 45 correct-to-correct, 26 wrong-to-wrong, one correct-to-wrong and
zero wrong-to-correct. Agents 0 and 1 each remain 15/24 correct; agent 2 changes
from 16/24 to 15/24.

Eighteen of 72 raw strings and completion arrays are identical across draws;
54 differ, while 71/72 answer IDs remain unchanged. This is observed wording
variation with highly stable answers, not evidence that the output was simply
copied from the parent cache. The run reports zero cache hits.

These are two paired draws on the same 24 training tasks, not 48 independent tasks.
The additional draw supports the narrow conclusion that it did not produce more
natural mixed correctness. It does not prove adapter collapse, identify a causal
training defect, establish scarcity for all seeds/tasks, or estimate held-out
efficacy. Potential repair is derived from private answers; this control has no
receiver outcomes and cannot measure hold/repair preference availability.

## Resources and persistence

One invocation, 72 new private generations, no unresolved attempts or missing
records. Input/output tokens: 16,755 / 3,863, within the 18,432-output-token ceiling.
Invocation time: 411.096 seconds (6.85 minutes), including 55.511 seconds loading
the model and periodic snapshots; final persistence is outside this timer.
Summed generation: 274.984 seconds. Peak allocated/reserved memory:
16,666,484,224 / 16,733,175,808 bytes. Compute units remain unknown.

The handoff reports verified snapshot
`/content/drive/MyDrive/PACT/private-support/qwen3-private-support-control-001/snapshots/1789909726482309183-c1ebb2f50100`.
The user supplied the final Drive ZIP path and matching outer checksum. Nested
receipt path/hash/size describe the preceding local review ZIP, and the null
bundle field predates final copying. The manifest's false persistence flag also
predates verification, consistent with the staged exporter. This is not evidence
that persistence failed. Current Drive contents and GPU reset/resume remain
independently unverified; preserve the full durable object store.

## Decision

Close the fixed seed control. There is no new receiver support to promote into a
preference or scoring stage; full revision training remains gated. Do not combine
packets across draws into a purported natural team, change labels, select a best
seed per task, or run additional seeds without a separately declared design.

The next design review should address context construction or actor preparation
explicitly, rather than repeating unchanged receiver sampling. The proposal's
same-task, provenance-preserving curated helpful-peer diagnostic is one option,
but this control does not establish that it will supply preference pairs. Any
such intervention must be distinguished from naturally occurring communication,
retain genuine sampled packet provenance, and receive a separate budget and
review before implementation. No new GPU experiment is scheduled by this audit.

Original bytes are retained in `results_import/qwen3-private-support-control-001-review/`;
the reproducible audit, recomputed report, metrics and evidence hashes are under
`results_import/qwen3-private-support-control-001-analysis/`. No local model or
tokenizer numerical reproduction, independent tensor verification, new GPU run,
model download or final-test access occurred. This is a documentation-only review;
no application test-suite rerun was necessary.
