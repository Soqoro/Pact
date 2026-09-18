# Selected replay-feasibility check

Implemented and CPU-tested; **GPU-unverified**. This is the next bounded diagnostic
after the [full pilot audit](reviews/qwen3-pilot-001-raw.md), not PACT training.
The new code must be reviewed, committed and pushed before Colab can use it.
The old `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea` commit does not contain this preset.

## Fixed scope

Preset: `replay-check`; config: `configs/pilot/replay_check_3.yaml`.
Config identity: `415be5290ccccc58ad15672a0a33d7693519155d6482a878884fba423c57c611`.
New run ID: `qwen3-replay-check-001`; six debate trajectories, clean/exchange only.

| Task | Original 80-item position (zero-based) | Exchange sender (zero-based) |
|---|---:|---:|
| `arc_challenge:Mercury_180058` | 41 | 2 |
| `arc_challenge:LEAP_2012_8_10441` | 61 | 1 |
| `logiqa:eval-0590` | 70 | 1 |

These tasks were selected after observing mixed initial correctness. They are not
a balanced or representative performance sample. Manifests, metrics, diagnostics
and handoffs carry that limitation. Ordinary smoke/profile/pilot configurations
retain their balanced-item rules and previous configuration identities.

The loader reconstructs the original 80-item validation selection, verifies its
manifest hash, then checks each selected task's position and input/label hashes.
It does not need a restored raw pilot or model outputs in Colab. The model snapshot
and all six original attack IDs are checked before the first generation. Attack
IDs bind the payload bytes and sender site; shrinking the task list cannot reassign
senders. Main-generation node seeds stay unchanged. Probe seeds belong to this new
configuration and are logged; corresponding positive/negative suffix nodes share
their seeds. This is a new diagnostic, not an exact continuation of old records.

Generation settings stay fixed: unadapted Qwen3-8B, original revision/snapshot,
BF16/SDPA, thinking disabled, temperature 0.7, top-p 0.8, top-k 20, seed 1729;
256-token packets, 64-token finals, 4,096 context. Four private candidates and four
receiver candidates where eligible, K=2 paired suffix seeds. Nothing increases
sampling caps or changes settings when pairs are missing. Runtime/library/hardware
identity is recorded; matching seeds do not promise identical outputs on a changed
runtime. Exact resume still rejects changed runtime/code/configuration.

For one uninterrupted collection, the ceilings are **474 calls / 106,368 output
tokens**: 42 main, 72 private candidates, up to 72 receiver candidates and up to
288 suffix calls. Input tokens, loading, storage and interrupted uncommitted work
are additional costs. Actual calls can be much lower when pairs are unavailable.
These are bounds, not elapsed-time or compute-unit forecasts. Progress counts six
completed trajectories; each includes its probes before the counter advances.

## Colab steps after publication

After reviewing and publishing this change, obtain the new full SHA locally:

```bash
git rev-parse HEAD
```

Open `notebooks/01_pilot_colab.ipynb` from that published version and select a single
GPU runtime. Replace the complete parameter cell with:

```python
REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "PASTE_NEW_REVIEWED_40_CHARACTER_COMMIT_SHA_HERE"
RUN_ID = "qwen3-replay-check-001"
PRESET = "replay-check"
STAGE = "pilot"
SCRATCH_ROOT = "/content/pact-scratch"
PERSISTENT_ROOT = "/content/drive/MyDrive/PACT"
RESUME = False
MOUNT_DRIVE = True
PRIVATE_REPOSITORY = False
```

Run parameters, checkout, dependency installation and preflight/CPU-check cells in
order. After setup, this optional new cell prints the budget without loading weights
or generating outputs:

```python
from pact.cli import main

status = main([
    "pilot", "--config", str(CHECKOUT / "configs/pilot/replay_check_3.yaml"),
    "--run-id", RUN_ID, "--scratch", SCRATCH_ROOT,
    "--persistent", PERSISTENT_ROOT, "--dry-run",
])
if status:
    raise RuntimeError("Configuration validation failed; stop here.")
```

Then run the notebook's existing execution cell once. It uses the same bounded
storage and local recovery ZIP path already verified by the pilot. Equivalent CLI:

```bash
python -m pact pilot --config configs/pilot/replay_check_3.yaml --run-id qwen3-replay-check-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
```

The notebook additionally persists the handoff ZIP. Bring back the printed
`persistent_bundle` (or local fallback) and SHA256. Successful output should report
six completed records and `scientific_status=selected_validation_feasibility`.
Unlike the 80-item pilot, all six raw records, candidate packets and any eligible
suffix branches fit the existing six-record sample export and are included in the
standard handoff. There should be no need for a second raw export.

Stop on a provenance/preflight mismatch and return the error. Do not change hashes,
precision, model or lengths to bypass it. After an interruption, preserve the
diagnostic ZIP and use the recorded identical-config resume command; do not rerun
the previous 80-item pilot. The completed pilot remains reusable and unchanged.

## Review criteria and local evidence

The result to inspect is eligible pair/hold/repair coverage and the invariants of
any actually executed suffix branches. A zero-pair outcome is valid and does not
trigger automatic extra sampling or training. Three selected tasks cannot establish
representative accuracy, a preservation advantage or training-seed stability.

CPU suite: 43 tests, 42 passed, one optional tiny neural test skipped. New regression
checks cover changed task/label/manifest/model/attack rejection, original senders and
main seeds, eligible paired branches with fixed attacks, preserved other-agent
packets, interruption/resume, budget bounds, and complete six-record handoff/import
with selection metadata. Notebook syntax/defaults also pass. A separate CPU audit
matches all six selected assignments against the verified real pilot's raw records.
Evidence is in `results_import/replay-check-implementation/` (ignored by Git).
No new model download, GPU inference, training or final-test evaluation ran locally.
