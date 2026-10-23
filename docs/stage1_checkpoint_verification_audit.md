# Stage I checkpoint verification audit — 2026-10-23

## Outcome

The returned real Colab verification reports ready=true and is internally
consistent with the historical checkpoint metadata and the inspected run.
Six final inference adapters have recorded historical file/content-hash matches;
16/16 bounded synthetic forwards completed. No benchmark generation, training,
optimizer update or teacher-forced scoring occurred in this verification child.
This establishes returned GPU verification evidence, not scientific improvement
or authorization to run the blocked evaluation portfolio.

## Evidence and local checks

Run: `pact-revival-stage1-evaluation-001`.

- PRIVATE: `pact-revival-stage1-evaluation-001-PRIVATE-1792766354718085784.zip`
  SHA256 `6836c626fbfb502c7da4f59db2f70280669db84611ef155280fcc73f8626efda`.
- SANITIZED: `pact-revival-stage1-evaluation-001-SANITIZED-1792766360489575398.zip`
  SHA256 `86b29cf813b729e3af57fe7726cecbd33c15e86a811831154c438fe1fcf7d687`.

Both outer hashes match the user-reported values. Exact archive inventories,
path/size bounds, symlink exclusions and every declared payload checksum passed.
PRIVATE has 8,883 payloads. All 8,845 payloads from the previously audited
inspection archive remain byte-identical. Its evidence inventory also matches.
SANITIZED has no scientific payload files: only HANDOFF.json and checksums.json.
That is expected before evaluation reports exist; its handoff agrees with PRIVATE
except for the PRIVATE/SANITIZED kind. No raw benchmark content was extracted or
added to Git, and no archive-provided code was executed.

Local assertions independently cross-checked the receipt's inventory digest,
six lineage entries, step-128 metadata/contracts, historical expected file and
adapter hashes, inference identity manifest, all intent/result hash links,
prescribed state order, shared input hash within each model, token caps, runtime
fingerprints, finite-result flags, base-restoration flags, pristine exits, absence
of child generation artifacts and zero-call/update accounting. All passed.
These were artifact audits, not locally rerun neural tests.

## Checkpoints and activation

| Arm | Model | Adapter tensors | Recorded saved dtype | Historical hash binding |
|---|---|---:|---|---|
| Independent adversarial SFT | Q | 224 | FP32 | Passed |
| Independent adversarial SFT | L | 256 | FP32 | Passed |
| Independent adversarial SFT | M | 256 | FP32 | Passed |
| Uniform joint SFT | Q | 224 | FP32 | Passed |
| Uniform joint SFT | L | 256 | FP32 | Passed |
| Uniform joint SFT | M | 256 | FP32 | Passed |

The executed verifier checks finite FP32 adapter values, exact keys/shapes, historical
file/content hashes and effective active values without a BF16 adapter round-trip.
All six metadata entries identify the prescribed final step 128. Historical
assurance remains archive-bound expected hashes, not independent authentication.

Q/L/M each ran pristine → independent → pristine → joint → pristine on identical
synthetic input within that model. R ran pristine once. All outputs were recorded
finite; all six restored-base checks passed with declared atol=rtol=0. All four
models ended with no active adapter. Native input lengths were Q30, L52, M24 and
R34 tokens, all below the 128-token limit. Total physical synthetic forwards: 16.

The receipt is from real execution (fixture=false). Actual tensor bytes and logits
are not included in these review ZIPs: this local audit verifies the returned
execution records and their bindings, not a second independent reading of GPU
weights or recomputation of logits. Initialization hashes differ from final hashes
for all six fits, but initialization tensor bytes were not verified. Optimizer
metadata/tensor availability is recorded; optimizer recovery was not validated.

## Provenance and persistence

Original resolution is unchanged:
`1a201309fe4b4e3d518eec18e754c294dae6b3ecf316d5865bd7aedeeae93f28`.
Original source remains `03f2319cb2fc2a962f728e18064ed507d48c9c29`.
The explicit storage transition records clean execution revision
`6acf5ae4a40e66351c91f25957dae9ce76bb45ff`, with the protected-code hash and
zero model calls at transition. No scientific contract was changed by recovery.
Runtime fingerprint equals all four recorded model-access fingerprints:
`e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0`.

The user returned successful compact persistence/recovery and verified matching
Drive copies of both final exports. The archive recovery receipt is safe. Local
review does not independently access Drive or establish ongoing cloud durability.
The compact transport now has user-returned Colab execution evidence; it is not a
claim of comprehensive interruption/recovery testing for every failure window.

## What remains blocked

1. The executed source-evaluation allocation is ARC120/LogiQA136, whereas the new
   brief says ARC128/LogiQA128. Keep the frozen task IDs; resolve the contract
   discrepancy explicitly rather than reallocating tasks.
2. Later original-run generation ownership is not closed by the available
   pre-main-training milestone. The known 384 evaluation-pool attack acquisitions
   already exist, but the remaining generation budget cannot be treated as a fresh
   wallet without the reviewed historical closure.

The receipt explicitly says evaluation_authorized_by_receipt=false. No freeze,
smoke, validation, source evaluation, fixed-history evaluation or new study is
implicitly authorized by this successful verification. Historical unknown optimizer
step94 and earlier original-run uncertainty remain separate and unchanged.
