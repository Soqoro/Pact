# Heterogeneous complementarity Colab execution

Implementation date: 2 October 2026. No new official-model inference has been run.
Use [notebook 09](../notebooks/09_heterogeneity_colab.ipynb), whose default is plan/access preflight only. Review, commit and push locally yourself; set its `GIT_REF` to that full reviewed SHA. Keep that SHA for all stages and resets. Do not reuse any old experiment run directory or adapters.

## Prerequisites

- A Colab runtime with exactly one visible BF16-capable CUDA GPU and supported SDPA. Actual L4/H100/Blackwell fit and speed are unverified. No quantization/offload fallback.
- Enough free cache disk for all missing official weight shards plus an 8 GiB reserve, and at least 12 GiB host RAM. Preflight derives missing bytes from official weight metadata and accounts for already cached shards. These are conservative setup screens, not a proof of model fit. Four models remain on disk but only one is resident in GPU/host model memory at a time.
- User-authorized access to all four official models, particularly Llama. Accept any terms yourself at the official repository; put the authorized token in Colab secret `HF_TOKEN`. The code does not accept terms or access local credentials during development.
- The original raw pilot archive: `qwen3-pilot-001-raw-1789668883200154407 (1).zip`, SHA256 `7a2d96d48e805718d138da03f651dfbaca02adc7d95d2a02cdf5191f4c6e94f4`. The local retained copy is under ignored `results_import/`. Upload it once to `/content/drive/MyDrive/PACT/sources/qwen3-pilot-original-raw.zip`, or edit `PILOT_DRIVE` to its actual location. This destination is a setup instruction, not a claim the file already exists there.
- No preparation, actor, optimizer or controlled-specialization checkpoint path is required. The exact 80 tasks, labels, options and source manifests are restored from that verified pilot archive. No benchmark download or GPQA access is needed.

The notebook uses the existing installer to preserve Colab's PyTorch build while installing the repository's pinned model extras. It does not upgrade the dependency recipe. Its Git checkout helper assumes the repository is accessible without a new private-repository credential; if it is private, use your already-authorized checkout procedure and verify the same clean pinned revision.

## Cells to run in order

1. Parameter cell: set `GIT_REF`, `PILOT_DRIVE` and, after a reset, `RESUME=True`. Keep `STAGE="preflight"`, `EXECUTE=False` for setup.
2. Mount Drive, clone/fetch the pinned checkout and install dependencies.
3. Copy/verify the pilot ZIP and create the plan, or restore the latest compact snapshot. Save the printed `PLAN_HASH`.
4. Retrieve your authorized secret and run all-model access/native-tokenizer preflight. This downloads metadata/tokenizers, checks access to every weight shard with HEAD requests, and generates no benchmark answers.
5. Default final cell prints that no benchmark inference was dispatched. Subsequent stages are explicit selections, not Run All defaults.

After those cells define `study`, `COMMON`, `RUN`, `CACHE`, and `PLAN_HASH`, execute these individually in this order:

```python
# Optional first two planned tasks; 60 requests INCLUDED in the total.
study("smoke", *COMMON)
```

```python
study("private", "--model", "Q", *COMMON)
```

```python
study("private", "--model", "L", *COMMON)
```

```python
study("private", "--model", "M", *COMMON)
```

```python
study("revisions", "--model", "Q", *COMMON)
```

```python
study("revisions", "--model", "L", *COMMON)
```

```python
study("revisions", "--model", "M", *COMMON)
```

```python
study("readout", *COMMON)
```

```python
study("report")
```

```python
study("export")
```

`COMMON = ["--execute", "--plan-hash", PLAN_HASH, "--cache-dir", CACHE]`.
The notebook's `study` supplies `--run-dir` and `--persistent`. Equivalent CLI:

```bash
python -u -m pact.studies.heterogeneity private \
  --run-dir /content/pact-heterogeneity/runs/pact-heterogeneous-complementarity-001 \
  --persistent /content/drive/MyDrive/PACT/heterogeneity/pact-heterogeneous-complementarity-001 \
  --cache-dir /content/pact-heterogeneity/cache \
  --plan-hash YOUR_PRINTED_PLAN_HASH --model Q --execute
```

`python -m pact heterogeneity` routes to the same CLI. For an intentional smaller invocation, append `--stop-after 30` to a single private/revision/readout stage. This pauses after committed requests, persists a safe boundary, and reuses those requests when the same stage is invoked again. It changes neither the plan nor the ceiling. It adds model reload cost; it is not a new sample schedule. Do not use this option for smoke.

## Budgets and completion

| Stage | Calls | Reserved output tokens |
|---|---:|---:|
| Private Q/L/M, 240 each | 720 | 184320 |
| Revision Q/L/M, 320 each | 960 | 245760 |
| Private synthesis | 320 | 20480 |
| Revised synthesis | 320 | 20480 |
| Task-only common readout | 80 | 5120 |
| Total | 2400 | 476160 |

Every attempted request consumes its reservation, including failures; context overflow is recorded without a generation forward and conservatively retains its request reservation. No stochastic retries. Zero optimizer and teacher-forced scoring steps. Communication is run on all tasks regardless of diversity or correctness. Exact smoke requests are reused.

## Reset and failure recovery

After a reset, rerun setup with the SAME Git revision and `RESUME=True`. `restore` chooses the latest snapshot only, verifies both compact files and the private archive, rejects unsafe state, and reconstructs saved requests. Re-run preflight in the restored environment, then select the interrupted model stage. Exact committed requests are reused; incompatible source/runtime/model identities reject resume.

Durability uses existing bounded snapshot/copy operations on two compact files (`state.zip`, `receipt.json`). Before each model-stage dispatch window, an unsafe snapshot is verified on Drive. After successful completion or an intentional `--stop-after` boundary, the accumulated results are bundled and a safe snapshot is verified. Hot journals remain on scratch. There is no per-call tiny-file stream to Drive.

A runtime loss inside a dispatch window can therefore still leave unsafe state. It is deliberately rejected even if saved call counts match. Do not select an older snapshot, delete an intent, toggle `recovery_safe`, or regenerate an unknown call. Preserve scratch and export forensic evidence if possible. Model-stage boundaries favor fewer Drive operations; use explicit bounded invocations if more frequent durable boundaries are needed. Storage deadlines do not change scientific budgets.

## Returned artifacts

Scratch run: `/content/pact-heterogeneity/runs/pact-heterogeneous-complementarity-001`.
Local bundles: `/content/pact-heterogeneity/runs/bundles/`.
Durable root: `/content/drive/MyDrive/PACT/heterogeneity/pact-heterogeneous-complementarity-001`.

Return the final **PRIVATE** and **SANITIZED** ZIPs with the exact SHA256 values printed by `export`. Preserve the private archive separately from Git/public outputs. Neither ZIP contains weights or credentials. The public summary cannot replace raw request auditing.

Private artifacts include plan/resolved configuration, model registry, access preflight, environment, exact task exposure and team bindings, immutable call/token shards and their dependencies, load/resource records, per-task metrics, family pairwise rescue CSV, support/transitions/comparisons, missing requests, inventory/checksums, report and handoff. Shards replace duplicated monolithic private/revision/readout records. Sanitized output contains allowlisted numeric summaries, model identities, registry and report; no questions, answer keys, prompts, continuations or token arrays.

Local audit after returning the private ZIP:

```bash
python -m pact.studies.heterogeneity audit \
  --bundle results_import/RETURNED-PRIVATE.zip --sha256 PRINTED_SHA256 \
  --run-dir results_import/heterogeneity-return-audit
```

The audit output directory must not already exist. This validates the bounded archive and regenerates the report without models or imported code. Unknown requests remain unknown; metrics reconstruction cannot confer recovery safety.
