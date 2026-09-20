# Private-support control implementation — 2026-09-20

The proposed second-seed control is implemented and CPU tested. It makes exactly
one additional clean private draw on the same 24 training tasks and frozen actors:
72 calls, at most 18,432 output tokens, global seed 1730. It changes no prompts,
sampling settings, actor weights, selection or labels. No GPU execution, new
training data or optimizer update occurred locally.

`private-support-control` defaults to plan-only; model use requires `--execute`.
The planner checks the pinned completed receiver ZIP and its selection, validates
all baseline private prompts/calls against the trusted task serializer and
reconstructs the 72 new seeds. The real offline plan matches every request in the
previously recorded proposal inventory. Baseline labels remain evaluator-only.

Config hash: `da15b8979e5142e82b55e74f49e453773bb2c9bcb72f8011de47190d606dbab8`.
Full executable request hash:
`98e749e8b4d2c3fe20f8a3643af7fc8e362febff4a4ae7dae1450cbbf5333571`.
Projection onto the original proposal's fields remains
`b5fef80b43f796ae4cbe89d2d40826093ea3657da2b37369307b9299825e77a0`.
The new hash includes full task/prompt/token data and does not change the 72 requests.

The runner uses the existing frozen-actor backend and immutable call journal.
It verifies the original rendered prompts, token prefixes and sampling parameters
for every new call. Only private calls are scheduled; no base readout, receiver
revision, replay, score or training-pair export occurs. Tensor-version guards and
reference verification remain active. Runtime mismatch stops before model loading.

The report keeps the two triples separate per task. It includes agent answer and
correctness outcomes, correctness transitions, family-level correct-agent counts,
valid-answer unanimity and potential clean-repair contexts. Incomplete triples do
not enter new-draw team summaries; invalid outputs remain failures. Potential
repair is a private-support measure, not evidence of receiver preference pairs.
`full_pact_ready` remains false regardless of the control's result.

Resume checks source/config/model/runtime identity and reuses verified logical
calls. An unresolved attempt cannot silently regenerate. Task-boundary persistence
uses the same strict budget policy as the receiver screen: publish an unsafe
marker before fresh calls, a safe snapshot after all three private calls or a
handled pause, and restore only the latest safe snapshot. A runtime loss with
unaccounted calls can require an explicit recovery-budget review. Local ZIP
creation precedes final timed persistence; snapshot and bundle status are distinct.

The full default suite passes **114 tests with six optional neural skips (120 total)**
in 49.062 seconds. Seven new tests cover source/selection/label/prompt/seed rejection,
plan-only CLI, a pause after two calls, immutable resume and zero-call repeated
completion, separate-draw reporting and invalid failures, verified restore,
stale-snapshot rejection, unresolved attempts and failure ZIPs, and runtime/storage
failure before generation. Existing tests cover the shared journal's unsafe
snapshot and budget enforcement. Five documented Colab cells compile locally.

The earlier temporary CPU neural environment no longer exists, so its six optional
checks were not rerun in this increment; no replacement model packages were
downloaded. Prior tiny-neural verification of the shared generation backend is
historical evidence, not execution of this new full control. GPU collection,
private-control GPU pause/resume and post-reset Drive restore remain unverified.

Evidence: `results_import/private-support-implementation-001/` contains the actual
non-executing plan, suite log, environment, proposal-inventory comparison and
verification hashes. The attempted optional-suite command's unavailable-environment
error is retained separately. Tested uncommitted executable source hash:
`8b5eb9a5af5c2b9dfb4f6d3e42b4ccb30193bf75cfef03bf49607f9f0fba3d44`,
based on Git HEAD `b3951fde181bb216130cb206fdf87e39fca87632`.

Next: user review/commit/push, then the [fresh-runtime Colab guide](../private_support_control_colab.md)
pinned to the new full commit. Return the ZIP and checksum. This separate control
does not reopen the completed receiver screen or authorize sampling further seeds
until mixed teams appear.
