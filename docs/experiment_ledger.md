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
| Unit/integration suite | cpu_tested | Current storage repair: 39 tests, 38 passed, one opt-in tiny neural test skipped; original implementation had 34 tests; details in `docs/implementation_status.md` |
| Authoritative data audit | cpu_tested | Actual pinned ARC validation (299) and original English LogiQA Eval (651) parsed; balanced 80 selected; zero exact duplicate groups within validation |
| Pinned Qwen tokenizer audit | cpu_tested | `/tmp/pact-source-audit/tokenizer_audit.json`; no weights; 80 private prompts, max 738 tokens including 256 reserved, zero overflows |
| `qwen3-smoke-001` | gpu_verified_on_reported_environment; reviewed 2026-09-17 | NVIDIA L4, unadapted Qwen3-8B BF16; 24/24 cells (20 applicable + 4 N/A); bundle/checksums/metrics verified; no usable replay pairs; proceed to unchanged profile |
| `qwen3-profile-001` | GPU collection verified; final Drive persistence unverified | 60/60 raw records recovered after restart, fully rescored; clean/early/exchange 9/20, 3/20, 9/20; no rerun required |
| Storage repair / mock gate | cpu_tested; small-run Colab Drive path verified | 39 tests, 38 passed, one skipped; returned `drive-storage-check-001` confirms normal snapshot and ZIP verification on reported environment |
| `drive-storage-check-001` | mock_only; Colab storage verified | 12/12 records, zero failures; returned SHA256 and all 17 file checksums match; current repaired commit `ede29d6`; proceed to pilot workload review |
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

## Returned Colab storage check — `drive-storage-check-001`

- ZIP: `results_import/drive-storage-check-001-handoff-1789630392894382325.zip`,
  36,369 bytes; SHA256
  `8c23c8ffec31bd9ae54a733b5671a51920c4e19cfb109d363379ff7077c8bb17` matches the user log.
  Archive paths, membership, size bounds and all 17 internal checksums passed before import.
- Code: clean `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`; source hash
  `071535868e299327e0d32cfc0740cfc26dc0d628c0a4c4bce221b28757bcbdfa`, matches local source.
- Config: `c1a04b28ea039139cbbe14a9ef783ad73ff557e40c555b481aeacf6dc8804d1c`;
  synthetic data manifest `ce36f318e01a2bb8728ef72c0aad44c923d4ca192cae3d7f6d084e1585df88dd`.
  Both match local reconstruction of the unchanged `storage` preset; seed 1729.
- Mock identity: `deed3295893fee1e68b0f63f5547ccdac226fb0256ed2d539b0f8cda99142022`.
  Scientific status `mock_only`: 84 scripted calls, not neural inference or benchmark evidence.
- Runtime fingerprint remains `4d1df1880142a2e4c51bdb9baf55288fec2625d36f5a484ffc79befaf7fe29d9`;
  reported Colab runtime has NVIDIA L4, Python 3.13.15 and torch 2.11.0+cu128.
  No GPU inference, model-load memory or accelerator-hour measurement for this mock run.
- All 12 unique applicable records complete; no missing records or recorded failures.
  Metrics reproduce exactly. Collection/data/preflight/report/persistence are complete;
  training/final test deferred. The 1.5738-second attempt excludes final export/persistence.
- Verified snapshot receipt in the manifest and user log:
  `/content/drive/MyDrive/PACT/drive-storage-check-001/snapshots/1789630392726322043-f1bca5130909`.
  Notebook ZIP persistence returned exit code zero and matching SHA256. Remote objects
  were not independently reread from local Codex. Timeout paths were not induced in Colab.
- Imported evidence: `results_import/drive-storage-check-001/`; reanalysis and audit under
  `analysis/`. No original artifacts modified, no source patch needed, no tests rerun for
  these documentation-only updates. Archive/config/data/metric checks and pilot dry-run passed.
- Decision: small normal-path storage gate passed. Existing smoke/profile evidence remains
  reusable; nothing needs regeneration. Next is `qwen3-pilot-001` at the same published
  commit, after reviewing its 1,440-cell workload. [Review](reviews/drive-storage-check-001.md).

## Returned 80-item Colab pilot — `qwen3-pilot-001` (2026-09-18)

- ZIP: `results_import/qwen3-pilot-001-handoff-1789651277912634037.zip`, 216,362 bytes;
  computed SHA256 `7b183fe47987ead3209ec209838b64cd0f3147d0103d46f3038990bf82849b99`.
  No independent transport checksum supplied. Archive validation and 17 internal
  checksums passed; imported originals preserved, derived audit under `analysis/`.
- Clean commit `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`; source hash
  `071535868e299327e0d32cfc0740cfc26dc0d628c0a4c4bce221b28757bcbdfa` matches local source.
  Config `92d66df5ede5d68cefed7f347290872aa36cbfe0ce0414e0b0295888d531db5a`;
  data manifest `8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495`.
- Untrained Qwen3-8B diagnostic, seed 1729, 40 ARC/40 LogiQA validation tasks.
  Same pinned model snapshot/runtime fingerprint as previous real runs; BF16/SDPA
  on L4. No adapters trained, no final-test evaluation, no reference scores.
- All 1,440 unique cells present: 1,120 applicable plus 320 N/A. Recomputed metrics
  exactly match; all joint identities pass. Six raw traces rescore exactly; 28
  sampled calls pass checks. Raw probes and other trajectories remain omitted.
- Final correct counts (clean/early/exchange, denominator 80): single 45/13/N/A;
  vote 45/12/N/A; synthesis 47/12/N/A; debate 47/10/46; ignore-peers 48/11/N/A;
  archive 47/12/47. Natural archive uses additional context, not matched cost.
- Three clean teams have mixed correctness. Debate clean/exchange erasure 1/47;
  early 3/13. Exchange loses one final answer while preserving coverage
  (`LEAP_2012_8_10441`); `Mercury_180058` loses its sole correct packet in both
  clean and exchange. No trained PACT benefit or population equivalence established.
- Probe: four tasks, 0/36 packet pairs, 30 missing correct and six missing incorrect;
  two hold contexts lack pairs, 34 other receiver contexts ineligible. Credits null,
  no eligible suffix replay or repair sampling. Full raw probe audit pending.
- Cost: 5,912 calls; 2,009,332 input / 285,294 output tokens; 20,443.64-second
  collection attempt (5.6788 accelerator-hours), excluding final reporting/storage
  and notebook setup. Generation 19,706.45 seconds, 14.48 output tokens/second;
  peak 15.56/15.83 GiB allocated/reserved. Compute units unknown.
- Reported verified snapshot:
  `/content/drive/MyDrive/PACT/qwen3-pilot-001/snapshots/1789651274145846633-95d5c6020ac8`.
  Normal pilot-size persistence succeeds in supplied evidence; Drive not accessed
  locally and actual Colab timeout failure remains untested.
- Next: CPU-only export of existing full raw traces, then local probe/mechanism audit.
  Reuse all completed artifacts; no inference regeneration, sampling change or
  training authorized by this review. No executable patch or source test rerun.
  [Full review](reviews/qwen3-pilot-001.md) and [export cell](colab_runbook.md#current-next-action-reviewed-2026-09-18).

## Full raw pilot recovery — `qwen3-pilot-001` (2026-09-18)

- Archive `results_import/qwen3-pilot-001-raw-1789668883200154407 (1).zip`,
  5,401,994 bytes; SHA256 `7a2d96d48e805718d138da03f651dfbaca02adc7d95d2a02cdf5191f4c6e94f4`
  matches user output. All 2,902 members safely checked and all 1,440 raw-shard
  hashes/sizes/markers match the previous handoff inventory. Extracted originals
  preserved in `results_import/qwen3-pilot-001-raw/` and rechecked after analysis.
- All 80 task/label hashes and all 1,440 raw scores verified. Metrics/probes exactly
  reproduce. All 5,912 calls checked: 5,760 main, 144 private alternatives, eight
  hold candidates. EOS throughout; 5,788 answer parses, 124 actual-generation
  abstentions, no malformed/length-limit completions. Maximum context plus reserved
  output 1,307; recorded token counts checked for consistency, not retokenized.
- Full prompts, attack assignments, frozen-state delivery, synchronous peer inputs,
  readout visibility, seeds and model/template identities pass. All 144 private
  alternative seeds are distinct; all 36 sets have a single answer class, despite
  wording variation in 33. Recomputed pair selections confirm 30 missing-correct
  and six missing-incorrect contexts, two missing hold pairs, no eligible suffix.
- Full debate contexts contain 97 hold and ten repair opportunities; only two hold
  opportunities were probed. These are context strata, not usable pair counts.
- LEAP_2012_8_10441's sole additional exchange terminal failure is ABSTAIN with two
  correct revised packets; Mercury_7017990's extra harmful revision is ABSTAIN with
  correct final answer. Mercury_180058's minority erasure occurs in clean/exchange.
  Original success metrics are unchanged.
- Snapshot metadata retains pre-verification pending persistence; the handoff carries
  the later successful receipt. Complete data recovery after reset is verified by
  returned bytes, not independent access to Drive's COMPLETE/index files.
- Audit/evidence: `results_import/qwen3-pilot-001-raw-analysis/`. Source/config and
  reported collection costs unchanged; no new inference or training, no code patch.
- Next proposal: local preparation of selected replay-feasibility diagnostic on
  three mixed-initial tasks, clean/exchange, unchanged settings/original attack
  assignments, at most 474 calls. Not yet implemented or launched; not a population
  performance estimate. No further export or full pilot rerun is needed.
  [Full raw review](reviews/qwen3-pilot-001-raw.md).

## Local selected replay-feasibility implementation — 2026-09-18

- User authorized the proposed local increment after the full raw pilot review.
  New preset `configs/pilot/replay_check_3.yaml`, Colab name `replay-check`, stage
  `pilot`; planned new run ID `qwen3-replay-check-001`. No GPU run launched.
- Config hash: `415be5290ccccc58ad15672a0a33d7693519155d6482a878884fba423c57c611`.
  Three post-hoc mixed-initial validation tasks, source positions 41/61/70, two
  conditions, debate only. Source data/model/task/label/generation and attack pins
  match the reviewed pilot. Old ordinary config identities remain unchanged.
- Exact dry-run ceilings: 42 main + 432 probe calls = 474 calls; 106,368 generated
  tokens for uninterrupted collection. No elapsed-time/compute-unit forecast.
- CPU suite: 43 tests, 42 passed, one optional neural test skipped. New checks
  exercise eligible paired suffixes, immutable other-agent packets/fixed attacks,
  preserved main seeds, changed-provenance rejection before generation, interrupted
  resume and full six-record export/import with selected-scope metadata.
- Real-data CPU cross-check uses verified imported normalized task/label/manifest
  records and original six attack records; all assignments and main seeds match.
  No fresh dataset or model download; this does not execute real inference.
- Evidence: `results_import/replay-check-implementation/tests.log`, `dry_run.json`,
  `real_selection_audit.json`. New executable source needs review/commit/push before
  the next Colab checkout. Current status: implemented, cpu_tested, gpu_unverified.
  [Exact next execution steps](replay_check.md).
