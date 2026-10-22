# Stage I checkpoint verification and evaluation handoff

Implemented `python -m pact.revival.stage1`, using the existing native backend,
custom FP32 LoRA, protocol, seed policy, strict parser, journal shards, checksum
snapshots and task bootstrap. The module has no training or Stage-II entry point.

Start with [the methodology and blockers](docs/stage1_evaluation_methodology.md)
and [the complete fresh-Colab cells](docs/stage1_evaluation_colab.md).
Notebook: `notebooks/27_stage1_evaluation_colab.ipynb`.

Readiness is deliberately separated:

- Implemented: lineage resolver, actual adapter-file reader, effective activation/
  isolation checks, bounded synthetic sequence verification, staged native
  evaluation, canonical reuse, fixed attacks, paired reports and private exports.
- CPU-tested: locally initialized tensors and mock generation through all stages;
  actual uploaded metadata/archive inspection. No pretrained downloads.
- GPU-unverified: this new verification/evaluation path, real final tensor loads,
  synthetic forwards, throughput, full-context memory and Drive persistence.
- Real evaluation blocked: executed source-evaluation allocation is120 ARC/136
  LogiQA rather than the brief's128/128; original later generation ownership is
  not closed by the supplied pre-main-training milestone. No override is provided.
- Deferred: all real evaluation outcomes, StageII/III, gates/judge fitting, semantic
  review and full-PACT integration. No manuscript placeholders were populated.

## First user action

Review/push the code, then pin that new commit in notebook27. Supply the retained
continuation003 RECOVERY archive and its SHA sidecar, the two audited review ZIPs,
and a reviewed current exposure inventory. Cells1–5 perform CPU preparation and
export resolution. Cell6 defaults to inspect. Set only ACTION="verify" to invoke
at most16 synthetic no-generation forwards and export/stop. Use the exact original
runtime fingerprint; no dtype/hardware/version fallback. Return verification
PRIVATE and SANITIZED bundles. Keep all RECOVERY archives and parent snapshots.

Do not freeze or run smoke until the two real contract blockers are explicitly
resolved against evidence. This is a genuine contract prerequisite, not a request
to restart training or rerun past diagnostics. The six final step128 tensors are
selected by each fit's actual metadata and ancestor, not by a latest folder.

## Budget and historical uncertainty

Nominal evaluation components:4224 validation +8448 source evaluation +1920
fixed-history additional +384 attack acquisitions =14976 calls/7667712 tokens.
The actual supplied ancestor already spent384 of those attack acquisitions;
its full verified journal contains2438 calls. Conditional remaining evaluation
ceiling is14592 calls/7471104 tokens, subject to later-history closure. No original
wallet reset, new attack search or replacement for rejected attempts is permitted.
Synthetic verification has its own16-forward/128-input-token cap.

Training remains477 inherited +291 continuation =768 committed path updates;
unknown replacement step94 remains unknown, with at-most769 physical updates for
that amended lineage. Earlier original-run execution remains separate.

## Output and inspection

The child emits contract resolution, six-fit lineage mapping, checkpoint inventory
and verification receipt, inference identity manifest, reconciled budget, frozen
plan, immutable attempts/results/reuse links, source/attack availability, private
per-task and fixed-history records, paired metrics, peer-access interaction, and
runtime/cost summaries. PRIVATE contains raw audit evidence; SANITIZED uses an
explicit numeric-summary allowlist. Neither contains weights. Local audit uses
installed trusted code and reconstructs summaries; it never executes archive code.

Tests and exact outcomes are recorded in `docs/implementation_status.md`. Existing
unrelated documentation and uploaded archives were preserved. No commit, push,
credentials, GPU/Drive calls, external model download or final-test access occurred.
