# Stage I verification and evaluation implementation

This implements `stage1-evaluation-review-v2` as an evaluation-only descendant.
It does not amend frozen task allocation, training, historical uncertainty or budgets.
Entry point: `python -m pact.revival.stage1`. Run ID reserved locally:
`pact-revival-stage1-evaluation-001`; an existing local run cannot be replanned.
Parents and RECOVERY archives are read-only. No training entry point exists.

## Contract inspection findings and real-stage blockers

The audited PRIVATE hash is the full 64-character
`2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959`.
The SANITIZED hash is
`9a34de7cb4d5602b1fa4beeaa735ca14d9418f47fc08cdc14b4b11e2dbf72d1a`.
These are audit bindings, not independent authentication. Six final tensors are
not present locally. Verification must read explicitly supplied tensor files or
extract the six exact step-128 tensors from the user-supplied RECOVERY archive.
The expected file hashes, adapter-content hashes, shapes, configs and ancestry
come from each fit's bound metadata, not a latest-directory search. Independent
fits retain replacement-002 provenance; joint finals retain continuation-003.

Two discrepancies currently block real plan freezing, but not checkpoint verification:

1. Executed `arc400_logiqa560_v2` supplies source evaluation ARC120/LogiQA136,
   not the new prompt's ARC128/LogiQA128. Preserve every original ID. The approved
   allocation addendum remains authoritative; the discrepancy is surfaced for an
   explicit reconciliation rather than silently treating the prose as a new split.
2. The exact embedded original archive proves 2,438 resolved attempts: 1,536 fit
   private, 896 attacks (512 fit,128 validation,256 source evaluation), six scratch.
   All 384 evaluation-pool acquisitions already exist. Replacement and continuation
   forbid new generations, but their lineage explicitly leaves original-run later
   execution unresolved. The available archive is a pre-main-training milestone,
   not a closure of the original run. Real remaining-budget ownership therefore
   needs a reviewed closure of that later generation history. Unknown optimizer
   step94 stays separate; it is not itself a reason to reject this safe descendant.

No override flag clears either blocker. Export `contract_resolution.json` and
`reconciled_generation_budget.json`; a subsequent evidence-bound resolution must
preserve historical contracts. Do not hand-edit these frozen child files. This
implementation does not invent missing evidence or silently approve more work.

| Component | Nominal cap | Proven earlier attempts | Conditional remaining ceiling |
|---|---:|---:|---:|
| Validation live | 4224 | 0 in supplied milestone | 4224 |
| Source evaluation live | 8448 | 0 in supplied milestone | 8448 |
| Fixed-history additional | 1920 | 0 in supplied milestone | 1920 |
| Shared evaluation attacks | 384 | 384 | 0 |
| Total | 14976 | 384 | 14592 |

The conditional remaining ceiling reserves 7,471,104 output tokens. The nominal
components reserve 7,667,712. Neither is a newly authorized wallet. The original
17,030 total minus the verified milestone's 2,438 equals14,592, but that arithmetic
alone is explicitly insufficient to close later unknown generation history.
Distinct physical attempts remain charged; canonical exact reuses do not spend
again. No transfer between components. The synthetic allowance is separate:16
sequence forwards, at most128 input tokens each, no generation or scoring.

## Verification contract

The trained modules are the repository's custom LoRA modules, not PEFT adapters.
The new activation controller reuses `neural.attach` and `restore_parameters`,
explicitly installs/removes the wrappers, freezes every parameter, sets eval mode,
checks FP32 adapter content and underlying pristine parameter identities/version
counters at each arm change. No adapter merge or BF16 round-trip occurs. Native
backend checks pinned BF16 base/SDPA/tokenizer/runtime identities on every load.
One backbone is resident. R cannot receive adapters; attack Q is always pristine.
Only adapter references are read with safetensors; no pickle or optimizer restore.

Receipt fields distinguish structural validity, historical expected-file binding,
new canonical content fingerprint, effective loaded identity and optimizer tensor
availability. Availability is not recovery readiness. A missing optimizer alone
need not block inference; changed full-file hashes still fail historical binding.
Missing expected historical hashes produce weaker assurance, never an automatic
scientific-ready receipt. Missing/corrupt adapters export partial valid inventories
and a not-ready receipt before any synthetic forward.

Q/L/M each execute pristine, independent, pristine-restored, joint, pristine-restored
using the same synthetic native input. R executes once. Base restoration tolerance
is predeclared `atol=0, rtol=0` within this exact runtime; no claim of cross-runtime
bitwise equivalence. Adapter influence need not alter that synthetic output. Every
forward is inference-only, eval/dropout-off and batch1. Interrupted verification
is not automatically retried. Later loads validate identity without extra probes.
The existing exact runtime fingerprint policy is preserved; GPU behavior is unverified.

## Evaluation contract and analysis

Existing `contracts.prompt`, `parse`, `delivered`, `stratum`, native requests and
`study.seed` implement the unchanged answer-first packet contract, task/options
inclusion, label separation and synchronous protocol. All three teams generate
their own private packets and communicate normally. Frozen private histories are
shared only for the diagnostic. A corrupt sender keeps its own packet; its outgoing
replacement reaches both other receivers identically. R reads actual revisions.

Frozen-P diagnostic reuses require equal model/active-state identity, native input
IDs, full generation parameters, phase, seed and cap. Logical IDs are not physical
request IDs. Any failed frozen-P match stops instead of spending an extra384 calls.
Other exact reuses can lower actual spending. Previously rejected attacks are never
regenerated; unresolved attempts stop. Context overflow stops without truncation.
Strict invalid/abstaining/length outcomes count as observed failures. Unavailable
attacks and infrastructure gaps remain missing with planned-population bounds.

Fixed-history P/W strata are computed once from frozen own and delivered P peers,
including the actual corruption; honest means unmodified, not correct. Report four
trained-arm accuracies, present and withheld gains, their interaction, frozen
comparisons and common supports. A positive interaction due only to worsened
joint-withheld performance is not efficacy. On-policy strata have arm-specific
supports and are not treated as matched causal populations.

Primary differences are joint minus independent, separate clean/exchange and
validation/source evaluation. Per-source counts and equal-source estimates are
reported. Existing dataset-stratified task-group bootstrap uses500 replicates,
seed20261015; values are scaled to equal-source weight without splitting receiver
observations into independent samples. Diagnostic receiver values are averaged
within task before bootstrap. All paired views stay together. Full-population
bounds and incomplete paired-intersection warnings remain visible. Results do not
select prompts/checkpoints, suppress a negative source evaluation or authorize StageII.

## Persistence, privacy and staged interface

The child uses existing immutable shards and checksum snapshots with a child-only
pending marker, latest-only restore and explicit unresolved-attempt checks. No
retention or deletion touches parents. Tensor files are external to the run and
must be remapped to the same scratch locations after reset. Review exports contain
metadata and raw audit traces, never tensor bytes. SANITIZED uses a numeric-summary
allowlist; it contains no source IDs, prompts, tokens, labels or private paths.
Partial evidence can always be exported with `--export-stage inspect`.

Each stage is a separate CLI invocation. Verification exports and stops. Smoke is
one outcome-independent validation task/source and exports/stops. Later stages
require the preceding export. There is no automatic portfolio loop in the notebook.
The mock pipeline exercises all stages with locally initialized tensors and invented
source data; no result from it is scientific evidence.

Generation persistence uses at most32 pending call IDs per batch, with a verified
Drive intent marker before every dispatch and a full checksum snapshot after each
32 committed calls and stage export. It does not rewrite/check every prior Drive
object twice per generation. A lost scratch batch remains unsafe: all listed
attempts stay reserved, restoration stops, and no automatic retry is allowed.
Snapshots never clear a marker containing attempts absent from scratch. This is
an engineering batching choice, not a guarantee of Colab speed or crash recovery.
Synthetic verification keeps its own per-forward durable boundaries.

Fresh-Colab verification includes the existing explicitly pinned Mistral tokenizer
cache repair (Git blob and payload hashes verified, no model calls). No dependency,
model revision or tokenizer content substitution is introduced. Initial-versus-final
adapter hashes are compared when the historical contract supplies an initialization
identity; initial tensor bytes are not claimed verified without their own artifact.

## Compact storage maintenance (2026-10-23)

After the inspected zero-attempt return, Stage I snapshots use
`stage1_compact_snapshot_v1`: all run files are packed and checksum-verified on
scratch, then the existing bounded storage worker persists only `state.zip` and
`receipt.json` as content-addressed objects. COMPLETE still follows verification;
weights remain external. Latest-only restore supports both historical per-file
snapshots and the compact format. Pending/unsafe dispatch still blocks restore.
No parent objects or snapshots are deleted. Packing repeats the metadata archive
per snapshot; it is not a storage-retention policy or a measured Drive speedup.

`recover-inspection` is a one-time storage-only recovery bound to PRIVATE SHA256
`3f0d2c8b0b85a8e56b62bfd41cdd7cc8c109563d30ed69cae7f06bcc603aecc3`
and resolution `1a201309fe4b4e3d518eec18e754c294dae6b3ecf316d5865bd7aedeeae93f28`.
It requires the exact pending marker, no inflight marker, no snapshot entries and
an absent active scratch destination. It verifies all 8,845 archived files and
zero child attempts. The pending marker is cleared only after a verified compact
snapshot. Failure preserves it and never automatically retries.

The original resolution and source identity remain byte-for-byte unchanged.
`storage_transition.json` separately binds the clean execution revision and a
protected-code hash: all src/configs/experiments/pyproject files except the four
explicit storage/CLI/guard maintenance files must match the inspected revision.
The guard verifies that receipt on every operation. This is an explicit storage
maintenance transition, not a general source-migration switch. Both scientific
blockers remain. Recovery neither verifies tensors nor resumes model forwards.
