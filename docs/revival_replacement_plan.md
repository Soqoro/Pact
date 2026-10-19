# Revival replacement attempt — review proposal

Status: **replacement proposal reviewed; executable child implemented and CPU-tested**.
The user approved proceeding with this separate attempt after the artifact-bound
review. No GPU execution has occurred locally. The existing interrupted run remains
historical evidence with unresolved later optimizer execution.

## Exact proposed attempt

Proposed ID: `pact-heterogeneous-receiver-training-replacement-002`.
Use a distinct scratch and Drive root; never write into the parent run's root.
Start all six adapters at their original per-family seeded B-zero FP32 LoRA
initialization, with the same pinned BF16 backbones. Do not initialize from step28
or the disposable trained scratch weights. Verify initialized adapter hashes against
the original scratch restoration receipts before any new optimizer step.

Reuse the exact completed fixed bank, source/split allocation, context/weight
records, malicious packets, rejection decisions and original sampling provenance.
Do not regenerate packets, attacks, source smoke or scratch sanity. Preserve the
parent's 2,438 completed generation records and their original plan-bound identities;
never rewrite them to impersonate new calls under the child plan.

Verified PRIVATE prerequisite:
`pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip`
SHA256 `f9a78141d0c662c06be903b49318f0235f6253d11e42f5bb17b2dd8adf9f2793`.
The local review builder rechecked the archive SHA, inventory, every member hash,
parent plan identity and bank bytes without executing or extracting archive code.
`training_bank.json` SHA256:
`66d5233b247aec6d6f833cbe31c845818caecde2094035e9ca6cf9ebdad3bf6c`.

The exact machine-readable proposal is [revival_replacement_review.json](revival_replacement_review.json).
This original review artifact remains immutable, including its historical
review-required status; current execution authorization is recorded here. Its SHA256 is `a67a7000801c4c96d19cd3b6d8521ee9d5fa9f5b2305c101eded1e11b4a066a3`.
It contains hashes and aggregate accounting, no benchmark text or token arrays.

## Accounting and interpretation

| Work | Status / proposed additional budget |
|---|---|
| Historical fixed-bank/scratch generations | 2,438 confirmed; reused, not repeated |
| Historical disposable scratch training | 48 confirmed updates |
| Historical main training | At least 28 confirmed updates; later actual total unknown |
| Replacement main training | 768 additional updates; 18,432 training forwards |
| Replacement generation / scratch repetition | 0 / 0 |
| Replacement evaluation | Deferred; 0 calls authorized here |
| Stage II / final tests | Not authorized |

The replacement is a new engineering attempt, not exact continuation and not a new
independent scientific seed. It repeats earlier learning from the same initialization;
report its added cost. If completed, confirmed main updates across attempts would
be **at least 796**, plus unknown later historical work. Do not reset end-to-end
cost to 768 or claim the original study stayed within its initial compute allowance.
No new efficacy conclusion follows from training completion alone.

## Retention policy under review

`revival_tensor_retention_v1` must be embedded in a future child's frozen plan.
Existing plans without it retain all objects. A policy cannot be enabled by merely
editing an existing plan: identity guards and persistence receipts reject migration.

After verifying the new snapshot, retain all tensor objects referenced by the latest
**two snapshots**, including latest, step-zero and all declared epoch checkpoints.
Keep all metadata, receipt objects, snapshot directories, bundles, unknown objects
and any object also referenced as non-tensor data. Only obsolete
`checkpoints/step-NNNNNN/tensors.safetensors` objects become deletion candidates.
Every snapshot must belong to this policy and plan; legacy/mixed/incomplete stores
are rejected. Each deletion manifest and per-object receipt is durable; only
completed audited deletions explain missing historical objects. Interrupted pruning
leaves `SNAPSHOT_PENDING.json` and blocks restore/retry. This never turns an older
unsafe optimizer boundary into a resumable state.

Admission still reserves enough space for the incoming snapshot **before** pruning.
The 32 GiB object cap remains. Protected data plus staging can still exceed it; no
silent cap increase or eviction of the newest recovery data. Metadata and explicit
ZIP bundles are outside the object cap. Capacity must be profiled against actual
checkpoint sizes before a long run. The CPU test demonstrates bounded *obsolete
tensor* retention; it is not a measured Colab capacity or throughput guarantee.

## Implemented execution path

`python -m pact.revival.replacement` exposes import-parent, inspect, preflight,
repair-tokenizer-cache, train-agent, report, export and latest-child restore.
The original runner rejects child plans, and the child journal refuses generation.
`contracts.RUN` and historical plans remain unchanged.

Import verifies the exact reviewed PRIVATE ZIP, every member checksum, all original
journal records, bank reconstruction and scratch initialization restoration receipts.
It stores the original ZIP verbatim, copies only bound operational inputs, and
creates a new plan with separate source identity/budget. It does not copy any
trained tensors or update attempts. Before real import, the checkout must be clean
and pinned. The CLI requires the reviewed proposal SHA and a distinct child root.

The source bank's exact bytes always supply the coefficients. A supplementary
reconstruction check allows roundoff only in weight/support-mass fields (relative
1e-12 / absolute 1e-15) because Python summation versions differ. Contexts, labels,
structure and other fields must match exactly; this tolerance never rewrites bank
bytes or relaxes the pinned archive/bank SHA checks. GPU runtime identity remains
strictly matched to the parent, not changed to the CPU audit environment.

Preflight loads the three actual pristine models sequentially, checks native
identities and recreated FP32 adapter hashes against the parent, and computes a
storage projection from the pinned projection shapes. The actual reviewed parent
projects 5,183,897,600 bytes (~4.83 GiB), including checkpoint staging/metadata margin;
this is not measured Drive usage or a GPU memory guarantee. The 32 GiB cap remains.
The known Mistral pointer discrepancy has an explicit local-cache repair stage
bound to its official revision, raw Git blob hash and payload SHA/size.

Training uses the existing optimizer/masking/objective implementation. One included
step can be exported/inspected; remaining steps use explicit compatible resume.
Reports separate inherited calls and historical unknown work from new committed
updates/forwards and pending optimizer attempts. Obsolete local scratch tensors
are also pruned only after successful durable persistence; keep two latest local
steps plus initial/epochs and an audit manifest. Explicit exports retain real
latest/epoch tensors in RECOVERY, never in PRIVATE/SANITIZED.

Run the [eight exact Colab cells](revival_replacement_colab.md) or
`notebooks/25_revival_replacement_colab.ipynb` after pushing the reviewed patch.
No evaluation, collection, scratch rerun, Stage II or final-test commands are exposed.
GPU/Drive performance is unverified pending actual returned evidence.

Offline reproduction (CPU, no downloads or Drive writes):

```bash
PYTHONPATH=src python -m pact.revival.replacement_review \
  --parent-private pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip \
  --output /tmp/pact-revival-replacement-review.json
```

Use an absent output path. This proposal-reproduction command still makes no model
calls. The separate child notebook is the reviewed training entry point.
