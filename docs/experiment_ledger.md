# Experiment ledger

Only software validation has run locally. No GPU measurements or paper results exist.
All local runs use synthetic mock tasks and are labeled `mock_only` in their manifests.
The Git baseline during development is `d99793858375ce7f60d72c9574c88d8ff723067b`
(the user's initial commit); dirty-source hashes distinguish the uncommitted implementation.

| Run / check | Status | Evidence and next action |
|---|---|---|
| `dev-check` | deliberately interrupted | Initial two-record interruption exercise under `/tmp/pact-dev`; diagnostic bundle exported; superseded by final round trip |
| `full-baselines-check` | cpu_tested, mock_only | `/tmp/pact-validation-full/runs/full-baselines-check`: 240/240 scheduled cells, including N/A; no scientific interpretation |
| `cpu-handoff-20260916` | cpu_tested, mock_only | Final interruption after 5 records → resume to 240/240, including 56 N/A cells; original five shard hashes preserved; verified persistence and immutable import reanalysis passed |
| Unit/integration suite | cpu_tested | 34 tests: 33 passed, one opt-in tiny neural test skipped; detailed evidence in `docs/implementation_status.md` |
| Authoritative data audit | cpu_tested | Actual pinned ARC validation (299) and original English LogiQA Eval (651) parsed; balanced 80 selected; zero exact duplicate groups within validation |
| Pinned Qwen tokenizer audit | cpu_tested | `/tmp/pact-source-audit/tokenizer_audit.json`; no weights; 80 private prompts, max 738 tokens including 256 reserved, zero overflows |
| `qwen3-smoke-001` | gpu_unverified, not run | First Colab gate; four validation items using the pinned Qwen3-8B base |
| `qwen3-profile-001` | gpu_unverified, not run | Twenty validation items after smoke review; inference profiling only |
| `qwen3-pilot-001` | gpu_unverified, not run | Eighty validation items after profile review; fixed pool, six natural baseline paths and bounded probes |
| `qwen3-matched-001` | gpu_unverified, not run | Separate matched-output/context controls on the same task/attack assignments |

## Final local handoff

- Bundle: `results_import/cpu-handoff-20260916.zip` (51,853 bytes), with `.zip.sha256` sidecar.
- SHA256: `09038aac0a5fbc1b1628bdbb4cd6c1b6146fd3d3f80c2531dd834336c3e2f731`.
- Source hash: `b90643442b2e5fbd40400e0234e781820d51f9653e0a42b47c2836147e56a6e8`.
- Config hash: `0a6537c2413c71a26cda90554e22c2c2cba3befad472dccb1ff4520711642341`.
- Imported evidence: `results_import/cpu-handoff-20260916/`.
- Recomputed metrics: `results_import/cpu-handoff-20260916/analysis/metrics.json`;
  equal to original metrics, with original imported checksums still valid.
- Test logs, tokenizer/data audit, doctor/config/dry-run outputs and machine-readable
  validation summary: `results_import/m0m2-20260916-audit/`.
- Full scratch run: `/tmp/pact-final-scratch/runs/cpu-handoff-20260916/`.
- Verified local persistence simulation: `/tmp/pact-final-persistent/cpu-handoff-20260916/`.

`/tmp` evidence is ephemeral. The ZIP and imported directory under ignored
`results_import/` are the retained local review artifacts. Earlier development
round trips are superseded by this handoff. It demonstrates software behavior only.

Commands executed for this final round trip (the first deliberately returned exit 2):

```bash
python -m pact smoke --config configs/smoke/cpu.yaml --run-id cpu-handoff-20260916 --scratch /tmp/pact-final-scratch --persistent /tmp/pact-final-persistent --stop-after 5
python -m pact smoke --config configs/smoke/cpu.yaml --run-id cpu-handoff-20260916 --scratch /tmp/pact-final-scratch --persistent /tmp/pact-final-persistent --resume
python -m pact export-bundle --run-dir /tmp/pact-final-scratch/runs/cpu-handoff-20260916 --output results_import/cpu-handoff-20260916.zip
python -m pact import-bundle --bundle results_import/cpu-handoff-20260916.zip --destination results_import/cpu-handoff-20260916
python -m pact report --run-dir results_import/cpu-handoff-20260916
```

When importing a Colab run, add its run ID, commit, source/config/data/model hashes,
stage statuses, hardware, complete/missing counts, measured costs, warnings and next
diagnostic action. Preserve negative or inconclusive findings. Never execute trace text.
