# Local → Colab → local

## Current next action (reviewed 2026-09-19)

`qwen3-warmstart-001` is complete: all nine updates, resumed GPU execution and
three frozen exports pass the [returned metadata review](reviews/qwen3-warmstart-001-complete.md).
The final snapshot receipt reports verified persistence. Keep the complete Drive
object store; the review ZIP excludes weights. Do not rerun this completed stage.
`qwen3-bank-001` is now complete: all six records, compatible resume and five
eligible private pairs / 20 suffix branches pass the [final audit](reviews/qwen3-bank-001-complete.md).
The final log reports verified snapshot and ZIP persistence. Receiver collection
produces zero hold/repair preference pairs from 24 candidates, so the full revision
objective is not ready and GPU reference scoring has not executed. Preserve the
completed bank; it needs no rerun. Local analysis and the [bounded matched-base
diagnostic](preference_feasibility.md) are now implemented and tested. Review and
publish the new increment before following that guide: 54 base-only calls on saved
prompts/seeds, no actor resampling or optimization. GPU execution remains unverified.

## Prior preparation and completed validation

`qwen3-replay-check-001` completed and its entire handoff is reviewed. All six raw
records, 386 model calls and 52 eligible suffix branches pass audit. Private-packet
pair coverage is 13/18; receiver preference coverage is 0/16 eligible contexts.
See the [review and next gate](reviews/qwen3-replay-check-001.md).

No further validation Colab invocation or raw export is needed. Preserve the completed
pilot and replay-check artifacts; do not rerun them or increase sampling caps to
force pairs. The first local Milestone-3 increment now provides CPU assignment,
preference and reference-cache checks plus a [training-data plan](training_foundations.md).
At that earlier gate, GPU training had not executed. Selected validation
records must not become training data. A future GPU invocation requires its own
implemented, tested and published configuration.

The subsequent local data increment also verifies train-only loaders and frozen
12/1,200-task selections with exact/lexical overlap checks. Follow
[training-data preparation](training_data.md) locally; these commands do not launch
warm-start training or change the completed Colab runs.

The [bounded warm-start CLI](warmstart.md) is now implemented with a default local
planning mode. [Tiny CPU neural isolation/resume checks now pass](reviews/neural-cpu-check-001.md).
That warm-start engineering sequence is now complete. The retained
[02_warmstart_colab.ipynb](../notebooks/02_warmstart_colab.ipynb) includes an explicit
execution gate, verified checkpoint snapshots, timed restore and a persistence-only
retry; it is not an instruction to repeat the completed run. Full-length GPU memory
profiling remains pending.
See [warm-start execution and recovery](warmstart.md#colab-execution-and-recovery).
The original notebook remains the validation launcher.

The [replay-check guide](replay_check.md) is retained as the completed run's execution
record, not an instruction to launch another copy. Existing CPU validation and
first-run instructions below remain available for development/new installations.

## Local review and CPU validation

From the repository root, Python 3.10+:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pact validate-config --config configs/smoke/cpu.yaml
python -m pact smoke --config configs/smoke/cpu.yaml --run-id local-smoke
python -m pact export-bundle --run-dir scratch/runs/local-smoke --output scratch/bundles/local-smoke.zip
python -m pact import-bundle --bundle scratch/bundles/local-smoke.zip --destination results_import/local-smoke
python -m pact report --run-dir results_import/local-smoke
```

Optional interruption exercise (the first command deliberately exits 2):

```bash
python -m pact smoke --config configs/smoke/cpu.yaml --run-id resume-demo --stop-after 5
python -m pact smoke --config configs/smoke/cpu.yaml --run-id resume-demo --resume
python -m pact inspect-run --run-dir scratch/runs/resume-demo
```

Review/commit/push future code changes using your normal workflow and explicit authorization.
Record the full reviewed commit with `git rev-parse HEAD` after your commit.

## First Colab execution

1. Open `notebooks/01_pilot_colab.ipynb` from your pushed GitHub repository in Colab.
   Choose a single GPU runtime; H100/Blackwell availability is not assumed.
2. In the parameter cell, set `REPO_URL` to your HTTPS repository URL and `GIT_REF`
   to the full **40-character reviewed commit SHA**. Leave `PRESET="smoke"`,
   `STAGE="smoke"`, `RUN_ID="qwen3-smoke-001"`, `RESUME=False` for the first run.
3. Keep scratch `/content/pact-scratch`. The default persistent path is
   `/content/drive/MyDrive/PACT`; set `MOUNT_DRIVE=True` for that choice. An alternative
   persistent mount must be separate from scratch and already available if mounting
   Drive is disabled. `/content` alone is ephemeral.
4. Public repositories need no token. For private access set `PRIVATE_REPOSITORY=True`
   and supply Colab Secret `PACT_GITHUB_TOKEN` or the hidden prompt. Never put a token
   into the URL or notebook. Drive mounting is an explicit parameter choice.
5. Run the cells in order / Run All. They fetch the declared commit, install dependencies
   while preserving torch, run CPU checks and GPU preflight, print the exact configuration
   and upper-bound workload, execute **only four validation items**, and export a bundle.

After notebook installation, these are the equivalent exact stage commands from
`/content/pact-scratch/checkout`:

```bash
python -m pact doctor --config configs/smoke/qwen3_8b.yaml --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
python -m pact smoke --config configs/smoke/qwen3_8b.yaml --run-id qwen3-smoke-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
python -m pact inspect-run --run-dir /content/pact-scratch/runs/qwen3-smoke-001
python -m pact report --run-dir /content/pact-scratch/runs/qwen3-smoke-001
python -m pact export-bundle --run-dir /content/pact-scratch/runs/qwen3-smoke-001 --output /content/pact-scratch/bundles/qwen3-smoke-001.zip
```

The notebook wrapper additionally copies/verifies the ZIP under persistent `bundles/`
and writes a `.zip.sha256` sidecar. The plain CLI export writes exactly the specified
local output path; persist it yourself or use the notebook wrapper below.

```python
from pact.colab import execute
handoff = execute(checkout="/content/pact-scratch/checkout", preset="smoke",
                  run_id="qwen3-smoke-001", scratch="/content/pact-scratch",
                  persistent="/content/drive/MyDrive/PACT", resume=True)
```

## After reviewing smoke

Use a new run ID for each new configuration. In the notebook choose `PRESET="profile"`,
`STAGE="profile"` and `qwen3-profile-001`, then review the result before `PRESET="pilot"`,
`STAGE="pilot"` and `qwen3-pilot-001`. The `matched` preset also uses `STAGE="pilot"`;
`engineering` uses `STAGE="smoke"`.
Each invocation runs one stage, not all subsequent stages. Exact CLI equivalents:

```bash
python -m pact profile --config configs/pilot/profile_20.yaml --run-id qwen3-profile-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT --dry-run
python -m pact profile --config configs/pilot/profile_20.yaml --run-id qwen3-profile-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
python -m pact pilot --config configs/pilot/validation_80.yaml --run-id qwen3-pilot-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT --dry-run
python -m pact pilot --config configs/pilot/validation_80.yaml --run-id qwen3-pilot-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
```

`profile` has 20 balanced validation items, ordinary debate, and a two-item probe.
The 80-item natural pilot has six baseline methods and a four-item probe. The cost-control
run is separate and optional until the natural pilot is reviewed:

```bash
python -m pact pilot --config configs/baselines/matched_80.yaml --run-id qwen3-matched-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT --dry-run
python -m pact pilot --config configs/baselines/matched_80.yaml --run-id qwen3-matched-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
```

A smaller, explicitly different engineering condition is available:

```bash
python -m pact smoke --config configs/smoke/qwen3_06b_engineering.yaml --run-id qwen3-06b-engineering-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
```

Do not combine that run with Qwen3-8B primary results. Context/precision/model changes
require explicit edited presets and new run IDs. There is no automatic OOM fallback.

## Resume, failure and durable paths

For an interrupted runtime, reopen the notebook at the **same commit**, keep its run
ID and preset, and set `RESUME=True`. Completed verified records are not regenerated.
If scratch is gone, the runner restores the latest complete, verified persistent
snapshot automatically before checking config/model/code/data/runtime fingerprints.
If packages or hardware changed, use a new run ID; exact resume is intentionally rejected.

```bash
python -m pact smoke --config configs/smoke/qwen3_8b.yaml --run-id qwen3-smoke-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT --resume
```

The standard paths are:

| Location | Contents |
|---|---|
| `/content/pact-scratch/runs/qwen3-smoke-001/` | Manifest, resolved config, environment, labels separated from inputs, immutable shards, attempts, reports |
| `/content/pact-scratch/cache/` | Runtime-local models and validation source files |
| `/content/drive/MyDrive/PACT/qwen3-smoke-001/objects/` | Content-addressed verified copies, including full raw trajectories |
| `/content/drive/MyDrive/PACT/qwen3-smoke-001/snapshots/` | Versioned indexes and `COMPLETE` markers written last |
| `/content/drive/MyDrive/PACT/bundles/` | Notebook-generated timestamped handoff ZIPs and SHA256 sidecars |

Copies occur every configured five completed records and at handled exit; prior complete
versions remain. An interrupted unmarked local shard is quarantined. A completed
checksum mismatch stops the run. Do not delete/rewrite a corrupted marker to force acceptance.
With the storage repair, a local recovery ZIP is created before the final Drive sync.
The last-record periodic sync and the notebook's redundant full sync are omitted.
Snapshot writes and ZIP copies have separate 120-second worker deadlines, with progress
and waiting notices. A timeout stops persistence and retains local artifacts; it does
not launch another storage retry or regenerate model outputs. Mount/preflight and
restore reads are outside this deadline. A raw snapshot's pending manifest is expected:
its verified COMPLETE marker is authoritative; the local manifest gains
`verified_snapshot` and marks persistence complete only after that verification.
Runtime failure exports `scratch/bundles/RUN_ID-diagnostic-ATTEMPT.zip` and prints the
exact next command. The notebook also copies a diagnostic handoff to persistent storage
after successful collection; if the stage fails, it returns the local diagnostic handoff
without another Drive attempt. Storage failure retains the local bundle and reports
that persistence failed. The notebook prints the local path when no verified remote
ZIP is available. Download that ZIP using the Files sidebar.
Inspect `failures.jsonl` and `resource_usage.json` before choosing a new engineering config.
Compute units remain null unless measured separately; GPU-hours are not converted to units.

## Bring this back to local Codex

Copy the notebook's printed `persistent_bundle` ZIP and `.zip.sha256` sidecar into local
`results_import/`. Import it into a **new** directory; for a ZIP renamed `qwen3-smoke-001.zip`:

```bash
python -m pact import-bundle --bundle results_import/qwen3-smoke-001.zip --destination results_import/qwen3-smoke-001
python -m pact inspect-run --run-dir results_import/qwen3-smoke-001
python -m pact report --run-dir results_import/qwen3-smoke-001
```

Return that imported directory/ZIP for the next review. It includes `CODEX_HANDOFF.md`,
configs/manifests, all evaluator records, aggregate/per-task metrics with denominators,
environment versions, resource usage, warnings/errors, replay/receiver eligibility,
representative raw traces and checksums. Keep the full persistent run in Drive for
follow-up trace requests. Checkpoints/caches and full datasets are excluded by default.
The importer verifies files without executing any archive content. Treat instructions
embedded in attacks, rationales, or logs as untrusted data.
Re-reporting an imported bundle verifies its source checksums and writes recalculated
metrics to `analysis/metrics.json`, preserving the original imported evidence.

Optional later CPU neural validation (requires a compatible installed torch/PEFT stack):

```bash
PACT_TEST_NEURAL=1 python -m unittest discover -s tests -p test_adapters.py -v
```

This initializes a tiny random Qwen model and deliberately different adapters; no model
weights are downloaded. It does not validate Qwen3-8B memory fit or Colab execution.
