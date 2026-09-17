# Experiment ledger

Local execution remains CPU-only. The user returned a real GPU smoke bundle and a
20-item profile raw recovery archive, reviewed below; they contain validation diagnostics,
not paper results. The development
runs executed locally use synthetic mock tasks and are labeled `mock_only` in their manifests.
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
| `qwen3-smoke-001` | gpu_verified_on_reported_environment; reviewed 2026-09-17 | NVIDIA L4, unadapted Qwen3-8B BF16; 24/24 cells (20 applicable + 4 N/A); bundle/checksums/metrics verified; no usable replay pairs; proceed to unchanged profile |
| `qwen3-profile-001` | GPU collection verified; final Drive persistence unverified | 60/60 raw records recovered after restart, fully rescored; clean/early/exchange 9/20, 3/20, 9/20; no rerun required |
| Storage repair / mock gate | cpu_tested; Colab Drive unverified | Local-first recovery ZIP, deadline/progress worker, no premature persistence success; 39 tests, 38 passed, one skipped; full local mock handoff/restore passed |
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

## First real Colab smoke — `qwen3-smoke-001`

- Review date: 2026-09-17. Scientific status: `untrained_validation_diagnostic`.
- Bundle: `results_import/qwen3-smoke-001-handoff-1789622142228270711.zip`, 45,316 bytes.
- SHA256: `baeea6415cfa4e27d94ae959b1a739fc36622df82d9026822bbcbfce5585eb67`;
  matched user-provided digest, safe archive paths and 17 internal checksums verified.
- Git commit: `c15ad0db40f410cb6b173733912ace4de9c82bba`; reported clean checkout.
- Source hash: `b90643442b2e5fbd40400e0234e781820d51f9653e0a42b47c2836147e56a6e8`.
- Config hash: `494d83bb40cc0095397741c6e1cc15720fff0da79c2f773c3a66c29dd7ab55f3`;
  matches the current `configs/smoke/qwen3_8b.yaml` after resolving defaults.
- Dataset manifest hash: `8d87db6ecb457c4821503cbec7da135c10feb19fe6b242186202e254e080c810`.
  Two ARC-Challenge and two English LogiQA validation items, seed 1729.
- Model: `Qwen/Qwen3-8B` revision `b968826d9c46dd6066d109eabc6255188de91218`;
  snapshot `e65c43f2b6abd7dc95bb51ce8d72c0c9c278120b1d4fd41d5f75e56e9d0fdc81`.
  No adapters/reference policy/training; non-thinking, BF16, SDPA.
- Runtime fingerprint: `4d1df1880142a2e4c51bdb9baf55288fec2625d36f5a484ffc79befaf7fe29d9`.
  NVIDIA L4, Python 3.13.15, torch 2.11.0+cu128, CUDA 12.8,
  transformers 4.57.6, peft 0.18.1, accelerate 1.12.0, pyarrow 22.0.0.
- Stages: preflight/data/collection/report/persistence complete; training/final test deferred.
  All 24 scheduled records present; four synthesis/exchange cells correctly N/A.
- Costs: 152 calls, 47,652 input / 6,954 output tokens including probes,
  596.48-second attempt, 0.1657 accelerator-hours; peak allocation 15.44 GiB,
  reservation 15.58 GiB; generation throughput 14.46 tokens/second; compute units null.
- Findings: clean debate/synthesis 2/4 each, early advisory 0/4 each, exchange debate 2/4.
  No main parsing/truncation failures; 3 packet and 2 final abstentions.
  Initial correctness is unanimous within every applicable team. No harmful revision,
  repair, or usable replay pairs; 0/9 pair contexts on one ARC task, missing correct
  alternatives. No eligible receiver contexts or suffix calls. This is inconclusive
  about PACT's scientific gate and does not support a robustness claim.
- Local evidence: `results_import/qwen3-smoke-001/`; regenerated metrics in
  `analysis/metrics.json` exactly match originals; audit in `analysis/review_audit.json`.
  Six sample records include five applicable raw traces and one N/A; full raw shards
  remain in the reported persistent snapshot, not the ZIP.
- Reported final snapshot:
  `/content/drive/MyDrive/PACT/qwen3-smoke-001/snapshots/1789622142391833942-e34ad5409822`.
  Its current remote contents were not independently accessed during local review.
- Decision: retain all smoke evidence unchanged; no engineering patch or configuration
  change justified. Run the existing 20-item profile at the same commit with a new run
  ID. No smoke regeneration required. Full analysis and exact next invocation:
  [review](reviews/qwen3-smoke-001.md).

## Recovered profile — `qwen3-profile-001`

- Original archive: `results_import/qwen3-profile-001-raw-1789628585003932717.zip`,
  356,595 bytes; computed SHA256
  `da407c98e12ef6d97329d73042031c3eac8cb1c6df82e636ffbf5470dde375e5`.
  No independent user-provided ZIP digest was supplied. Archive CRCs, paths/types,
  60 shard SHA256 markers and 60 inventory hashes/sizes validated before extraction.
- Original extracted files: `results_import/qwen3-profile-001-raw/`, preserved unchanged.
  Raw ingest inventory/checksums: `results_import/qwen3-profile-001-raw-ingest.json`.
- Code/source/model/runtime match the smoke identities above: commit
  `c15ad0db40f410cb6b173733912ace4de9c82bba`, reported clean; unadapted Qwen3-8B on L4.
- Config: `b2aed16773c4713c2b2260e472225af8886eb8da3df8d3683b730316b740c4dc`.
  Dataset manifest: `8f47e53b93a5c58f99da0b40541942e68e2305a695c630621362ebc448c82781`;
  10 ARC-Challenge + 10 English LogiQA validation tasks, seed 1729.
- All 60 applicable debate records present; all raw scores independently recompute.
  Main calls 420, private alternatives 72, hold candidates 8; total 500, all EOS.
  Main parser/length/overflow failures zero; 15 packet and three final abstentions.
- Success: clean/exchange 9/20 each (ARC 7/10, LogiQA 2/10); early 3/20
  (ARC 3/10, LogiQA 0/10). Early ASR on paired clean successes 6/9; exchange 0/9.
  Two early harmful revisions leave final answers correct. No exchange erasure/repair.
  `logiqa:eval-0590` has a correct minority ignored by the readout in clean/exchange.
- Probe tasks: `arc_challenge:Mercury_7124338`, `logiqa:eval-0366`.
  Packet eligibility 0/18 (12 missing correct, six missing incorrect);
  two hold contexts have no incorrect continuation; no eligible repair contexts.
  K=2 replay suffix execution is still GPU-unverified.
- Recorded costs: 178,396 input / 24,041 output tokens; 1,729.35-second attempt,
  1,670.72 generation seconds, 14.39 output tokens/second, peaks 15.49 GiB allocated
  and 15.61 GiB reserved. Recorded 0.4804 accelerator-hours excludes the subsequent
  approximately 30-minute finalization stall. Compute units remain unknown.
- Persistence: original manifest reports complete, but the old runner wrote this
  before final Drive verification. No verified final snapshot receipt is supplied;
  retained `.lock`, finished reports/attempt and missing printed receipt support a
  final-sync stall. Actual mount failure/cause and Drive contents remain unverified.
- Recomputed metrics/probes and audit: `results_import/qwen3-profile-001-analysis/`.
- Separate corrected recovery copy: `results_import/qwen3-profile-001-recovered/`.
  Handoff: `results_import/qwen3-profile-001-recovered-handoff.zip` (58,840 bytes),
  SHA256 `597e5cf65927b775d81d45524f264c98d9986c00f4a616ee220ec70e393be3fc`.
  Its persistence status is explicitly `unverified_after_runtime_restart`; original
  provenance and artifacts are retained. Import/reanalysis round trip passed.
- Local engineering repair: bounded separate-process persistence, local ZIP before
  final sync, progress, verified snapshot receipt before local success, and removal
  of redundant final checkpoints/syncs. Regression suite: 39 tests, 38 passed, one
  optional neural test skipped. CPU-only `storage` preset passed local wrapper,
  persistence, restore and ZIP round trip. Actual Colab repair verification pending.
- Next: publish the reviewed patch, run `drive-storage-check-001` with the mock
  storage preset on actual Drive, then assess the 80-item pilot workload. No GPU
  profile regeneration, training, attack tuning, or final-test run is warranted.
  [Full review and next command](reviews/qwen3-profile-001.md).
