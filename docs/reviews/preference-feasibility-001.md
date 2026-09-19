# Preference-feasibility implementation — 2026-09-19

The local source analysis and bounded base-control runner are complete. The default
suite passes 92 tests with five optional neural skips; with the existing CPU neural
opt-in, all 97 pass. No GPU/model-weight download, new bank, optimizer update,
training-pair construction or final-test access occurred in this increment.

The actual completed bank has no correct receiver candidates. All six eligible
contexts are one LogiQA task; its clean private pool has six correct answers out
of 15, while its receiver pools have zero out of 24. ARC clean private samples
are all wrong. Stored reasoning identifies possible task-wording and communication
confounds but cannot attribute the outcome to the warm start without a control.

The new recipe selects all six original eligible receiver contexts and all clean
private initial/alternative calls for the two tasks: 54 existing actor outputs
paired with at most 54 new unadapted-base outputs. It preserves exact prompts,
seeds, source task labels, sampling and model/runtime identity. Cap: 13,824 new
output tokens, no teacher-forced or optimizer calls. The source archive and bank
hashes are pinned; selection is deterministic and isolated from training output.

Retained local evidence under `results_import/preference-feasibility-001/` includes
the complete plan, source-only group analysis, suite logs, environment/source
identity and verification record. Plan construction makes zero model calls.
The tested uncommitted source hash is
`8c36005865aec6f91af273e71e781f1a59dd816b88c16262c9def1901272c3b4`,
based on Git HEAD `12861a1ca4dce794a1f4daaa27e02618fed2956e`.
The CPU-only torch build is asserted; dependency checks pass and all four
documented Colab Python cells compile. `verification.json` pins evidence hashes.
`source_analysis.json` has zero completed base-control results; its actor counts
come from the returned bank, not from a new experiment.

Seven new CPU tests use explicitly invented training-shaped fixtures. They verify
archive hash/path/checksum rejection, exact selection bounds, plan-only CLI,
same-prompt/token-prefix control, task-label separation, immutable partial resume,
invalid completion handling, independent actor/base outcome pools, no training-pair
export, runtime mismatch before generation, diagnostic failure ZIPs, deadline
recovery, verified snapshot/ZIP/restore, source copying with scratch control files,
no overwrite and zero-generation repeated completion. The generic restore changes
also pass the existing warm-start and collection tests.

Remaining limits: no GPU execution of this diagnostic; no inference of an adapter
regression from the original failures; no representative performance estimate from
two selected training tasks. Base outputs on actor-produced contexts are a fixed
context control, not an independently generated base team. Even a base preference
pair would not make the actor bank ready or become a training pair automatically.
GPU frozen-reference scoring and full PACT optimization remain unverified/deferred.

Review/publish the increment before using the [exact Colab sequence](../preference_feasibility.md#colab-sequence-after-review-and-publication).
The prior completed bank remains immutable and need not be rerun.
