# GPQA Main / LogiQA CPU source review on the existing AAI deployment

Use this after local review and the user's commit/push. These commands were
prepared, not submitted. No Colab/Drive setup or migration is needed. CPU source
review does not authorize future assay/training/evaluation.

## Local synthetic checks

From the repository, using its existing local Python:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_gpqa_source_amendment.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_allocation_v3.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_evaluation_source.py -v
PYTHONPATH=src python -m pact gpqa-source inventory
```

A complete invented-content audit/graph/assay-policy report/export/reconstruction:

```bash
PACT_FIXTURE="$(mktemp -d /tmp/pact-gpqa-fixture-XXXXXX)"
PYTHONPATH=src python -m pact gpqa-source mock --run-dir "$PACT_FIXTURE/review"
PYTHONPATH=src python -m pact gpqa-source validate --run-dir "$PACT_FIXTURE/review"
```

`mock` returns filenames and hashes. To reconstruct, supply that exact PRIVATE
fixture filename and its reported SHA256 to:

```bash
PYTHONPATH=src python -m pact gpqa-source reconstruct \
  --bundle "$PACT_FIXTURE/review/bundles/EXACT_PRINTED_PRIVATE_FILENAME.zip" \
  --sha256 EXACT_PRINTED_SHA256 --run-dir "$PACT_FIXTURE/reconstructed"
```

The uppercase values are deliberately supplied by the actual preceding receipt,
not guessed hashes. Fixtures establish mechanics, not real source eligibility.

## Existing cluster prerequisites

Keep the recorded deployment: `NA100q`, `node01`, Apptainer module `apptainer/1.24`,
`$HOME/pact-aai-preflight/compat-probe/ubuntu24.04.sif`, and
`$HOME/pact-aai-preflight/runtime-v1/venv`. The CPU wrapper validates the recorded
container hash and existing install receipt. No installation, GPU allocation,
CUDA probe, model staging or environment migration occurs.

Use private `/dataset/$USER/PACT`, never `/dataset/common`. Existing Stage I
artifacts under `stage1-execution-v1` and `stage1-migration-v1` remain untouched.
The precise current **raw source and reviewed exclusion file locations are not
known locally**. Reuse them if present; do not create empty substitutes or claim
that old caches contain GPQA Main.

The CPU audit config is private JSON with these keys:

| Key | Required value |
|---|---|
| `run_dir` | New absent private directory, e.g. `/dataset/suaq0001/PACT/stage2-gpqa-source-review-v2` |
| `parent_dir` | Existing extracted final Stage I parent, with authoritative members and summary |
| `parent_bundle` | Exact final PRIVATE Stage I archive, SHA256 `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`; alternatively valid existing import receipt if omitted |
| `gpqa_dir` | Authorized pinned Main/Diamond/README/license bytes and existing acquisition receipt; omit only to obtain an explicitly blocked inventory |
| `data_dir` | Original official ARC/LogiQA training AND validation source cache used by `training.data.load_training_sources(download=False)` |
| `exposure` | Current reviewed exposure JSON, all prior used/protected groups and preserved preview exclusions; exact current experiment-ledger hash and parent-source hash |
| `inventory` | GPQA historical partition inventory described below |
| `history_roots` | Actual relevant local execution/journal roots to inspect; omitting them does not certify absence of remote computation |
| `history` | Existing scoped reviewed Stage II consumption receipt, if available; omit to record unresolved execution authority |

The GPQA inventory is an object with `scope` equal to
`both_gpqa_cohorts_all_protections_and_revisions`, `unresolved_mappings` set to the
actual audited count, and `files`: entries containing `role`, `path`, `sha256`.
Required roles are `original_diamond` and `breadth_diamond`. Each points to the
existing private prepared dataset object with `receipt` and `manifest`, not a
handwritten replacement list. Full protected/reserve/excluded partitions and
revision consistency are checked. A genuinely unreviewed mapping cannot be marked
zero to bypass the check.

Exposure validation reuses `evaluation_source.sources.exposure_status` and
`selective.data.validate_exposure`. Historical consumption reuses
`allocation_v3.evidence.reviewed_history`: exact parent/source hashes, reviewed
scoped external evidence receipts, no unresolved relevant probe consumption.
If evidence shows overlapping spent/unknown work, stop for owned-budget resolution;
this command cannot convert it into an unconsumed-wallet receipt.

## Submit the CPU audit only

On the Jupyter terminal after the user has pushed the reviewed change:

```bash
cd "$HOME/Pact"
git pull --ff-only
export PACT_CHECKOUT="$HOME/Pact"
export PACT_COMMIT="$(git rev-parse HEAD)"
export PACT_CONFIG="/dataset/$USER/PACT/stage2-gpqa-source-audit.json"
test -f "$PACT_CONFIG"
mkdir -p "$HOME/pact-aai-preflight"
cd "$HOME/pact-aai-preflight"
export PACT_STAGE=audit
sbatch "$PACT_CHECKOUT/tools/aai_gpqa_source_audit.sbatch"
```

Record the returned job ID. Inspect its `pact-source-audit-JOBID.out/.err` and use
`sacct -j JOBID --format=JobID,State,ExitCode,Elapsed` with the actual numeric ID.
No `srun`, dependency chain, controller test submission or moving-branch pull
inside the job. A repeat validates the same committed config/audit; changed inputs
or a partial audit require a new reviewed destination, never overwriting evidence.

After the CPU audit has completed, export separately:

```bash
export PACT_STAGE=export
sbatch "$PACT_CHECKOUT/tools/aai_gpqa_source_audit.sbatch"
```

Return **only the SANITIZED ZIP and `local-audit-receipt.json`**. PRIVATE source
and export data stay restricted on the cluster. The receipt provides both bundle
hashes/byte lengths without raw examples or row maps. Preserve errors privately;
stdout intentionally omits raw exception messages.

## Optional source acquisition — separate user action, not run by audit

If authorized official bytes are missing, the implemented command is:

```bash
python -m pact gpqa-source acquire \
  --directory /dataset/suaq0001/PACT/sources/gpqa-main-83022cefff93 \
  --source-access-approved
```

Run only when separately approved, in the existing authenticated environment;
use the actual username if different. The destination must be absent. This uses
HF's existing authentication, four bounded official pinned files, and upstream
content verification. It does not read a token file, print credentials, download
weights, fetch the whole repository or execute dataset code. It is **not** an
allowed stage in the offline CPU batch wrapper. Existing account access/terms
are reused; absent access remains a concrete blocker. Never disable gating.

## Candidate static checks and explicit seal

After a real candidate exists, the implemented offline tokenizer command is:

```bash
python -m pact gpqa-source static-context --run-dir "$REVIEW_ROOT" \
  --assets "$TOKENIZER_ASSETS_JSON"
```

`TOKENIZER_ASSETS_JSON` contains `access_file` (the exact audited parent
`evidence/access.json`) and `directories` mapping Q/L/M/R to their already staged
native metadata/tokenizer directories. Hashes/template/revisions must match the
parent. No hub calls or pretrained model load; dynamic context fit remains a
future runtime prerequisite.

After explicit review of the exact MethodSpec, freeze a separate proposed plan:

```bash
python -m pact gpqa-source seal --run-dir "$REVIEW_ROOT" \
  --review-hash "$REVIEWED_METHOD_SHA256" --destination "$NEW_CHILD_ROOT"
```

The hash is `pact.util.digest` of `method.private.json`, not the ZIP SHA. The
command refuses absent candidates, wrong review hashes and destination collisions.
It freezes `plan.json`, `training.private.json`, and
`sealed/prospective.private.json`. It grants no execution permission and starts
no wallet. Do not submit the old v3 CLI with this plan; the versions differ.

## Future GPU boundary

No executable GPU command is issued by this CPU amendment. Remaining integration
is the guarded connection of the sealed GPQA child to the existing allocation
runner, with the new two-source report and exact owned budgets. It must retain
separate checkpoint/preflight, assay smoke/segments/scoring, policy freeze,
continuation, policy lock/smoke/evaluation and export/stop invocations. Relevant
history, real source freeze, current S0/runtime verification and explicit bounded
execution approval remain prerequisites. The existing `recovery-check --run-dir
... --plan ...` validates owned durable journals; it does not restore a missing
wallet or grant approval. Unknown attempts, pending persistence and locks stop.

## 2026-11-01 — authorized source-only acquisition on AAI

The user explicitly approved pinned official GPQA and original ARC/LogiQA source
acquisition after historical partition verification. Job1112946 reported matching
parent partitions, disjoint32+32 historical cohorts,32 confirmation-locked and100
reserve-locked breadth records, and2 original exclusions. Inventory receipt:
`/dataset/suaq0001/PACT/stage2-gpqa-history-v1/historical-inventory.json`, SHA256
`1f013791c6995cf9f6419d29ddfa92098f1ad69aa82e393357ea67fd8a8be9ad`.
This user-returned evidence does not certify current project exposure or eligibility.

After reviewing/committing/pushing the current source amendment and the new
`tools/aai_stage2_source_acquisition.py` and `.sbatch` helpers:

```bash
cd "$HOME/Pact"
git pull --ff-only
export PACT_CHECKOUT="$HOME/Pact"
export PACT_COMMIT="$(git rev-parse HEAD)"
test -f tools/aai_stage2_source_acquisition.py
test -f tools/aai_stage2_source_acquisition.sbatch
test -f src/pact/revival/gpqa_source/sources.py
cd "$HOME/pact-aai-preflight"
JOB_ID=$(sbatch --parsable "$PACT_CHECKOUT/tools/aai_stage2_source_acquisition.sbatch")
JOB_ID=${JOB_ID%%;*}
echo "$JOB_ID"
squeue -j "$JOB_ID"
```

Once finished, inspect `pact-source-acquire-${JOB_ID}.out/.err` and
`sacct -j "$JOB_ID" --format=JobID,State,ExitCode,Elapsed`.

The CPU-only job reuses the container/runtime and trusted CA bind. HF reads the
existing private token file through `HF_TOKEN_PATH`; no shell expansion or print
of its contents. Scratch is a new private `/local` directory. Destination is
`/dataset/$USER/PACT/stage2-source-acquisition-v1`; existing destination/scratch
is rejected rather than cleared. GPQA Main/Diamond/README/license use the pinned
upstream verification, and four original training/validation files use existing
repository hashes. No parser dependency installation is required to acquire bytes.
Only those eight source files and the GPQA receipt are durably copied and hashed.
`VERIFIED.json` follows verification; on failure the pending marker and evidence
remain. No automatic retry, eligibility selection, model fetch or follow-on job.
Return the aggregate stdout/receipt only, not raw source files.
