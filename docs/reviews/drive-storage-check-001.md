# Colab storage check review — 2026-09-17

The repaired normal storage path completed on the reported Colab environment. All
12 mock records, final snapshot verification and handoff ZIP copy completed, with
exit code zero. The returned ZIP matches the user's printed checksum. Proceed to
the existing pilot after reviewing its substantially larger workload.

## Evidence and scope

- Original ZIP: `results_import/drive-storage-check-001-handoff-1789630392894382325.zip`,
  36,369 bytes; SHA256
  `8c23c8ffec31bd9ae54a733b5671a51920c4e19cfb109d363379ff7077c8bb17`.
- Safe archive paths/member types and all 17 internal checksums passed before import
  into `results_import/drive-storage-check-001/`. No imported text was executed.
- Clean commit `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`, source hash
  `071535868e299327e0d32cfc0740cfc26dc0d628c0a4c4bce221b28757bcbdfa`, matches local source.
- Resolved config hash `c1a04b28ea039139cbbe14a9ef783ad73ff557e40c555b481aeacf6dc8804d1c`
  matches `configs/smoke/storage.yaml`. The synthetic data manifest reproduces locally;
  seed 1729, four mock items × three conditions, ordinary debate only, no probes.
- All 12 expected unique cells are complete; none are missing or N/A. Recomputed
  metrics exactly match the exported report. Failure log empty; all active stages
  complete, with training and final test deferred. Original imported files remain unchanged.
- Backend `mock`, snapshot
  `deed3295893fee1e68b0f63f5547ccdac226fb0256ed2d539b0f8cda99142022`;
  all 84 calls are scripted fixtures. No actual model, adapters, replay pairs or training
  ran. Mock outcome rates have no scientific interpretation.
- Reported environment: Colab with NVIDIA L4, Python 3.13.15, torch 2.11.0+cu128;
  runtime fingerprint matches the preceding GPU smoke/profile. GPU presence is not
  evidence of GPU inference in this run; accelerator hours and model memory are null.
- Manifest `verified_snapshot` matches the printed receipt:
  `/content/drive/MyDrive/PACT/drive-storage-check-001/snapshots/1789630392726322043-f1bca5130909`.
  The log shows the local recovery ZIP before final sync, followed by the verified
  snapshot, local handoff ZIP and successful bounded ZIP persistence.

The returned handoff is the final ZIP, not the earlier recovery ZIP whose checksum
starts `8934cfa6`. These are intentionally different artifacts: the recovery ZIP is
created before final persistence verification. The selected run is established by
its manifest, invocation and snapshot receipt, not just its filename.

The reported attempt took 1.5738 seconds, but that counter excludes final reporting,
snapshot and ZIP-copy time. It is not a measured end-to-end Drive latency. Current
remote Drive objects were not independently reread during local review. The check
does not validate timeout behavior on an actually stalled Colab mount, interrupted
GPU restore, or large-run Drive throughput. Existing CPU regression tests cover the
deadline/failure paths; this successful Colab run covers the normal storage path.

Machine-readable audit and regenerated metrics are under
`results_import/drive-storage-check-001/analysis/`. No engineering fix or scientific
configuration change is justified by this result. Documentation only was updated;
the same published code commit remains suitable for the next stage. Earlier profile
Drive persistence remains unverified; this check does not retroactively certify it.

## Next run

Keep `GIT_REF="ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea"`. Set
`RUN_ID="qwen3-pilot-001"`, `PRESET="pilot"`, `STAGE="pilot"`, `RESUME=False`.
The complete parameter cell is in [the runbook](../colab_runbook.md). First inspect:

```bash
python -m pact pilot --config configs/pilot/validation_80.yaml --run-id qwen3-pilot-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT --dry-run
```

Then run the notebook execution cell, or remove `--dry-run` for the CLI collection
stage. The notebook includes final handoff ZIP copying. It uses 80 balanced validation
tasks, six methods and three conditions: 1,440 scheduled cells, 1,120 applicable and
320 N/A. Main calls are bounded at 5,760, plus up to 864 probe calls. The conservative
combined output-token ceiling is 1,542,144; this is not a forecast. Given the preceding
L4 profile, plan for hours rather than minutes; exact pilot runtime and compute units
are unknown. The pilot remains untrained diagnostic evaluation, not a final PACT result.

Preserve previous run IDs and outputs. No smoke, profile or storage-check regeneration
is needed. Return the new pilot handoff ZIP and printed checksum for local review.
