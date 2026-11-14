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
