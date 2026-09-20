# Curated helpful-peer runner implementation — 2026-09-20

The fixed [32-call design](../curated_repair_design.md) now has an executable
runner, default planning CLI, within-arm reports and a
[five-cell Colab procedure](../curated_repair_colab.md). No new real model outputs
were collected. GPU execution and the actual tokenized context lengths remain
unverified.

## Preserved design

Reconstructing both checksum-pinned source ZIPs still selects the same two ARC
tasks, source packets, four recipients and eight prompts. Config hash remains
`ac29ebf94ee954729923ed7d72c8e474cf165e48a289a545fe0e8b6a002587d4`;
contexts hash remains
`66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab`.
The executable plan adds separate task/label and actor-recipe metadata; it does
not change defender messages. Source phases and post-selection remain explicit.

All eight prompts are rendered and tokenized before any generation attempt. An
oversized context stops the whole diagnostic without truncation or case deletion.
Each generated or cached call must match its recorded prompt and token prefix,
actor, seed, template and sampling recipe. Labels are used only for reporting.
The cap stays 32 revision calls / 8,192 reserved output tokens; there are no
private generations, final readouts, teacher-forced scores or optimizer steps.

Reports retain every sample, parsing failures, abstentions and length failures.
A preference diagnostic requires a fully sampled four-output pool containing
both valid classes under one exact arm prompt. Pair selection prefers the same
32-token length bin, then closest length and sample indices. Cross-arm pairs
are prohibited. Separate comparisons report corresponding seeds, missing pairs,
correctness transitions and counts by recipient and task. Partial runs stay
incomplete. No training pairs are exported and `full_pact_ready` is always false.

## Recovery and verification

Calls use the existing durable intent/result journal. An unresolved attempt
cannot be silently regenerated. Before a recipient's new calls, a verified
unsafe snapshot records that an abrupt reset may lose charged work. After its
eight calls, or a handled pause, a safe snapshot is published. Restore accepts
only the latest safe snapshot and compatible source/recipe/model identity.
Local review ZIP creation precedes final Drive operations; each storage operation
has a 120-second default deadline. A completed rerun uses cached calls only.

Eight new runner tests cover two-call pause/resume to exactly 32 calls, immutable
results and zero-call completion repeats; all-context overflow/runtime preflight;
ambiguous-call rejection; verified restore and stale snapshot rejection; storage
failure before sampling; changed recipe/token-prefix rejection; valid within-arm
length-bin pairing versus cross-arm single-class pools and invalid outputs; and
plan-only CLI behavior. These are synthetic CPU fixtures, not scientific evidence.

Full default suite: **126 passed, six optional neural tests skipped (132 total)**.
No optional neural environment, weights download or GPU run was used. Local
source reconstruction, fixed hashes, Colab cell syntax/imports and documentation
links are checked separately. Evidence is retained in
`results_import/curated-repair-implementation-001/` (git-ignored local artifacts).

Next: user review, commit/push, then pin that new SHA in the Colab guide. The
published private-control commit `91655a8...` lacks this command. Return the new
ZIP and checksum for audit; any observed outcome closes this bounded diagnostic.
It cannot establish natural-team benefit, hold support, LogiQA coverage, terminal
accuracy or full revision-training readiness.
