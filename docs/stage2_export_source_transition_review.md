# Export checksum source transition — CPU review, 14 November 2026

The recovered inactive plan remains
`5ff472604f74ed80cdbdecb574dc83c9306e6a912f0159249b1861a689fdd025`, pinned to
commit `995e814e0883414b1ed56c590faad2e240cdf9b1`. Job 1121664 reconstructed it
exactly and persisted snapshot `1794641113259988805-22b145006de1`. No source
transition has been applied to that plan.

## Reviewed change

The only runtime/configuration byte change against that commit is in
`src/pact/revival/allocation_v3/storage.py`:

```python
# Before
persist_bundle(path, destination/'bundles'/path.name, timeout_seconds=600)
# Proposed
persist_bundle(path, destination/'bundles'/path.name, out[kind]['sha256'], timeout_seconds=600)
```

The original call cannot satisfy the existing required checksum argument.
The proposed call supplies the hash of the ZIP just packaged, preserving the
existing verified-copy API rather than changing it. No protocol, sampling,
training, scoring, eligibility, graph, cohort, checkpoint, precision, budget,
resume validator or execution permission is changed. All other 206 files covered
by `code_identity` are byte-identical. Documentation, tests and tools are separately
versioned by the eventual commit; they do not alter the scientific source hash.

Local code-review hashes:

| Binding | SHA256 |
|---|---|
| Old runtime source map | `17465cd698c0c7e1bc1935c546e5614862b8df682bc0619f6c3eefe913f63d4a` |
| Proposed runtime source map | `c7dbf4bccc7501456ee96aed79e7897e638674fe22faf4fb27a2ef30e54a4719` |
| Old storage file | `1a09ce82e1d78c2737ea8aebee5fac18e8c59ea17f00e024028746b7c63258b9` |
| Proposed storage file | `21adb24366ed54d002302ebccfc6d5bf4045db9fb06b99b5b5f0c46a9b5a3496` |

The new commit does not yet exist locally; the user must commit/push and pin it
before a real transition proposal is produced. The local dirty-tree comparison is
code review only, never a usable execution identity.

## Implemented audit

`tools/aai_documented_source_transition.py` supports:

```bash
PYTHONPATH=src python tools/aai_documented_source_transition.py code-review --new-checkout "$PWD"
```

The CPU-only `propose` stage requires old and new clean checkouts, the exact old
plan and a new private output destination. It runs the original validator in a
separate process under the old checkout. It checks that the exact recovered child
has no execution/preflight/policy artifacts, then verifies the plan bytes remain
unchanged before and after writing the separate proposal. This narrow inactivity
check does not certify zero historical spending elsewhere.

```bash
python -B tools/aai_documented_source_transition.py propose \
  --old-checkout "$OLD_CHECKOUT" --new-checkout "$NEW_CHECKOUT" \
  --run-dir "$EXISTING_RUN" --output "$NEW_PROPOSAL_DIRECTORY"
```

Outputs are `proposal.sanitized.json`, checksums and COMPLETE. No candidate plan,
approval record, signature, active allowance or modified old plan is emitted.
The proposal includes the exact old plan, both source identities, frozen scientific
digests, unchanged conditional limits, and explicit unresolved historical spending.
Current tensor loading and GPU checks are not repeated or claimed.

`tools/aai_documented_source_transition.sbatch` prepares this packet on node01
using CPU only, the established offline container/runtime and `/local:ro`. It
requires `PACT_CHECKOUT` and `PACT_COMMIT` for the newly committed candidate,
reads the old checkout from the existing pointer file, and writes only to the new
`/dataset/$USER/PACT/stage2-export-source-transition-proposal-v1` directory.
It does not submit itself or apply the proposal. Return the sanitized receipt;
raw GPQA content and PRIVATE bundles are not needed for this review.

## Validation and next decision

Five CPU tests passed for exact-patch enforcement, unrelated scientific edits,
source additions/deletions, no-fix rejection, unresolved attempts, and activated
preflight/policy artifacts. The real filesystem export regression passed for
PRIVATE/SANITIZED/RECOVERY copies and a verified compact snapshot. Shell syntax
passed. No GPU/model execution, network download, training or cluster submission
was performed locally.

The next artifact is the CPU-generated proposal binding the user's new commit.
Its review must explicitly decide the source transition before any plan/source
binding is changed. GPU preflight and physical spending remain distinct later
decisions. Do not pull new source into the original pinned checkout or edit the
old plan's `source_code`/hash to bypass validation.

## Returned proposal — job 1121675

AAI returned COMPLETED 0:0 in six seconds, status
`SOURCE_TRANSITION_PROPOSED_NOT_APPLIED`. Proposal SHA256:
`6e217d91d3b00464013ad3734a4ee1d23a476c619237c93e303c0e6c4d376d6a`.
The clean candidate is commit `93b89ce38be743acd6a3aa38177237ce99a3eeeb`;
old/new source and storage hashes match the local review above. Tool SHA256
`43755973eb6a90dec0f277a305eb41f40c90625bb989c318bc8335402e570e67`
also matches the local committed file. Returned evidence validates the original
plan under its original checkout and reports its bytes unchanged, zero model
calls/forwards/updates, and inactive wallet. No new tensor or GPU check was run.
The proposal file itself has not been independently imported locally; its digest
is recorded from returned stdout.

Review recommendation: accept only the exact checksum-repair source transition,
bound to this proposal and commit, while preserving original plan evidence and
requiring a separately recorded resulting source/plan binding. This recommendation
is not user approval or permission to run a GPU preflight, train, infer, or activate
spending. Transition approval/application remain false pending the user's decision.

## Subsequent user approval and implementation

The user replied “proceed” to the explicit approval question binding proposal
`6e217d91…76d6a` and commit `93b89ce3…eeeb`, with GPU preflight, training,
inference and spending still disabled. This authorizes the exact storage-source
transition only. It is not a new physical allowance or a reviewer signature.

Implemented `tools/aai_apply_documented_source_transition.py` plus CPU-only
`tools/aai_apply_documented_source_transition.sbatch`. The helper is versioned
separately from the approved runtime checkout. Its Python imports come from the
unchanged approved `93b89ce3…` checkout, so adding this helper does not silently
advance the scientific code pin. Both original and target validators stay intact.

Before writing, it verifies the exact approved proposal bytes, clean old/target
identities, original plan bytes, original validator, absence of execution artifacts
in this child, and the exact latest original durable snapshot/receipt/archive. Any
changed latest boundary or pending marker stops the operation. This scoped check
does not resolve unknown historical execution outside this inactive child.

The output is a separate inactive successor at:

`/local/pact-stage2-documented-export-fixed-$USER/runs/pact-stage2-documented-execution-001`

Its separate persistence namespace is:

`/dataset/$USER/PACT/stage2-documented-execution-export-fixed-v1/pact-stage2-documented-execution-001`

The logical child owner is unchanged. Only the plan's `source_code` and
`scratch_root` fields change; all cohort/graph/training/checkpoint/analysis/limit
fields remain exact, including unknown historical spending and inactive execution.
The resulting plan hash necessarily changes and is printed for review. The old
plan and snapshot are retained. Separate transition provenance links both hashes
to the approved proposal; PRIVATE/SANITIZED/RECOVERY exports and a verified
snapshot use the corrected native persistence function. No approval for GPU work
is generated. A failed operation retains partial evidence and never auto-retries.

Four focused CPU tests passed: exact two-field copying with old-plan preservation,
rejection of activation/zero-history substitution, execution-artifact rejection,
and actual compact snapshot verification including pending/latest-only stops.
The AAI application has not yet been submitted or verified by this local work.
Commit/push the helper, then submit the CPU wrapper with `PACT_HELPER_CHECKOUT` and
`PACT_HELPER_COMMIT`. It uses the existing old checkout pointer and exact target
path `checkouts/export-fix-93b89ce38be7`; it never updates either checkout.
