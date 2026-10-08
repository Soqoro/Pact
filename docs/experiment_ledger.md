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

## Returned selected replay check — `qwen3-replay-check-001` (2026-09-18)

- ZIP `results_import/qwen3-replay-check-001-handoff-1789714612508117841 (1).zip`,
  179,664 bytes; SHA256 `21e5133daa634a894357f09658c2a78c5b6bef1bf3d701bcd8d454f7532899cb`
  matches user output. All 17 member checksums and six raw inventory hashes pass.
- Clean commit `e79a9ab0da7b3801ba1ff488ddd974302768da2a`; source hash
  `c1284a3bcd899fd112f6e63ad856a8a0d64c0dcc0505be0926806864fc84cd8f` matches local code.
  Config `415be5290ccccc58ad15672a0a33d7693519155d6482a878884fba423c57c611`;
  data manifest `43da504ec1e407835be486b273dbd578be43e97ad76db38d71a809bde1a70cbb`.
  Same unadapted Qwen3-8B snapshot, L4 runtime fingerprint, decoding and seed as pilot.
- Six complete applicable records, no failures/missing data. Full metrics/probes and
  386 calls independently audited. All main texts/prompts/attacks/seeds match the
  original pilot, excluding new IDs/timing and dependent artifact hashes.
- Private packet pairs: 13/18, four missing correct and one missing incorrect. Credits:
  five +1, two +0.5, six zero; five missing remain null. Three pairs unmatched by the
  32-token length-bin rule (two have positive credit). Post-hoc three-task selection
  and K=2 preclude population/efficacy claims.
- All 52 suffix branches / 208 calls verify paired node seeds, frozen other-agent
  private packets, fixed attack bytes/site and revised-only base readout. Two eligible
  corrupted-sender substitutions execute the same malicious delivery in both branches.
  Neural suffix execution is now verified on the reported environment.
- Receiver sampling: eight hold/eight repair contexts, 64 calls, zero same-context
  correct/incorrect pairs. Hold sets: six all-correct/two all-wrong; repair sets:
  one all-correct/seven all-wrong. Two further contexts ineligible, no calls.
- Main success 1/3 clean, 0/3 exchange, reproducing the selected original cells.
  All 386 calls end at EOS, 380 answer parses/six abstentions, no malformed or
  length-limit completions. Maximum prompt plus reserved output: 830 tokens.
- Cost: 42 main + 72 private candidates + 208 suffix + 64 receiver = 386 calls;
  148,080 input / 18,046 output tokens. Recorded attempt 1,380.995 seconds,
  0.38361 accelerator-hours; generation 1,266.26 seconds, 14.25 output tokens/sec.
  Peak allocated/reserved 15.41/15.53 GiB. Final report/storage/setup excluded from
  attempt timing; compute units unknown. Reported persistence receipt is complete.
- Original imports preserved; derived audit in `results_import/qwen3-replay-check-001/analysis/`.
  No source patch or regression-suite rerun; CPU artifact audit passes completely.
- Next: no Colab rerun/export. Propose local Milestone-3 scope and training-split
  data plan, keeping receiver pair feasibility open and validation data out of
  training. No training, new sampling sweep, or final evaluation was launched.
  [Full review](reviews/qwen3-replay-check-001.md).

## Local learning foundations — CPU only (2026-09-18)

- Implemented scored-bank validation, masked exponentiated-gradient assignment,
  global loss coefficients, same-prompt hold/repair preference construction,
  immutable reference-score caching, and causal completion/DPO numerical functions.
  CLI: `training-check`, `assign`, `build-preferences`. No model training launched.
- Final full suite: `PYTHONPATH=src python -m unittest discover -s tests -v`:
  59 tests, 57 passed, two optional neural checks skipped, exit 0 (11.138 seconds).
  The new 16 tests include an independent coordinate-bisection assignment reference,
  same-prompt/split rejection, invalid/empty candidate accounting, masks/reductions,
  cache corruption/invalidation and a complete synthetic CLI round trip.
- The initial solver comparison exposed numerical oscillation near the optimum.
  Capping the mirror step by `1/(tau + balance)` resolved it; final independent
  solution comparison and convergence/feasibility checks pass. No tolerance relaxation.
- Saved synthetic round trip: `results_import/training-foundations-001/cpu-roundtrip/`.
  Assignment converges with two eligible rows and one all-missing base-only row;
  synthetic preferences contain one hold and one repair pair. All scores/candidates
  in this fixture are invented software-test values, never empirical results.
- Evidence: `results_import/training-foundations-001/tests.log` and
  `verification.json` record test outcome, dirty working-tree source identity, missing
  torch dependency and fixture summary. No model/data download or GPU use.
- Real training-source verification, neural warm-start/reference scoring, adapter
  update isolation and optimizer resume remain outstanding. Existing validation
  bundles remain evidence only. [Training contract and next gates](training_foundations.md).

## Train-only loaders and frozen selections — CPU (2026-09-18)

- Downloaded only pinned ARC-Challenge train/validation parquet and original English
  LogiQA Train/Eval text. SHA256 and byte counts recorded in
  `results_import/training-data-001/source_audit.json`; validation hashes match the
  previous audit. Used PyArrow 22.0.0 installed under `/tmp/pact-training-data-deps`
  for this explicit real-source check; no base-environment changes or model downloads.
- Parsed all 1,119 ARC / 7,376 LogiQA train records and 299 ARC / 651 LogiQA validation
  records. Fixed exact-content/source-ID and word-trigram Jaccard >=9/10 screening
  removes 59 redundant train rows (1 ARC, 58 LogiQA), leaving 1,118 / 7,318 eligible.
  Audit contains 58 train duplicate components, 15 exact-content links, 44 additional
  lexical links, no label conflicts, and no train–validation matches under these rules.
  Semantic paraphrases and final-test overlap remain unaudited.
- Frozen 12-item engineering manifest (6/family), seed 20260918:
  `2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e`.
  Frozen 1,200-item proposal manifest (600/family), same seed:
  `92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a`.
  Nested selection verified. The latter preparation/verification took 15.32 seconds
  locally, excluding downloads/dependency setup. Neither launches training.
- Refactored validation parsers reproduce the returned 80-item pilot manifest exactly:
  `8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495`.
  Stored comparison in `validation_compatibility.json`; original imports untouched.
- `PYTHONPATH=src python -m unittest discover -s tests -v`: 68 tests, 66 passed,
  two optional neural tests skipped, exit 0 (8.364 seconds). New tests cover split
  discipline, reordered options/conflicting duplicates, transitive lexical matching,
  deterministic balance, immutable/checksummed data, explicit downloads and marker order.
  Evidence: `results_import/training-data-001/tests.log`, `verification.json`, and
  both prepared directories with all tasks, separate labels, audits and checksums.
- No final-test access or model training. Next local work is warm-start optimization,
  frozen adapter/reference snapshots and checkpoint/resume.
  [Preparation guide and limitations](training_data.md).

## Bounded warm-start implementation — control-path CPU checks (2026-09-18)

- Added clean-answer warm-start recipe, sequential adapter optimizer engine,
  safetensors/typed JSON checkpoint-resume and separate frozen adapter exports.
  Default CLI only plans; no model loading, parameter update or GPU call executed.
- Real-manifest dry run uses the reviewed 12 tasks, three distinct agent seeds,
  microbatch 1 / effective batch 4, three updates per adapter (nine total).
  Recipe hash `631ab416524276da3798db7b2edecfe231d5f197d3fd54d886779acce4faf579`.
  Plan hash `5a15cf4679764c446bd562ffa9ea9783e732b32ba3e5bdb82cd20a95fcdf420d`.
  Full task orders are in `results_import/warmstart-implementation-001/plan.json`.
- Final default suite: 76 tests, 73 passed, three optional neural tests skipped,
  exit 0 (11.248 seconds). Seven new control tests validate bounded recipes, exact
  manifest binding/orders, prompt/target separation and overflow rejection, typed
  state round trips, checkpoint integrity/publication, early incompatible-resume
  rejection and plan-only CLI behavior. No dependency/model downloads for these tests.
- New opt-in tiny random Qwen test covers sequential adapter updates, actual base/
  inactive parameter equality, nonzero-dropout interruption/resume, and frozen
  export/reload. **Not executed:** explicit model-test opt-in is pending and torch/
  PEFT are absent. Do not report neural checkpoint equivalence or Qwen training fit
  as tested based on the control-path fixtures.
- Evidence: `results_import/warmstart-implementation-001/tests.log`, `plan.json`,
  `verification.json`; dirty executable source hash
  `5762a58971732b16bb1729c7a70f8a5aaad3753ab0209627a2965068f8ed684b`.
  `git diff --check` passes. No commit/push, final-test access, trained checkpoint,
  frozen reference scores or scientific result produced.
- Next gate: opt-in tiny neural tests, then a reviewed/published bounded Qwen memory
  profile. Scored-bank collection and full PACT updates remain unimplemented.
  [Warm-start guide](warmstart.md).

## Authorized tiny CPU neural verification — `neural-cpu-check-001` (2026-09-18)

- User explicitly approved the tiny CPU model tests. Created `/tmp/pact-neural-cpu`
  without modifying the base environment. Installed torch 2.9.1+cpu from the official
  CPU wheel index, Transformers 4.57.6, PEFT 0.18.1 and Accelerate 1.12.0; `pip check`
  passes. Full dependency versions are preserved in `requirements-lock.txt`.
- `PACT_TEST_NEURAL=1`, CUDA hidden, HF/Transformers/dataset hubs offline, OMP/MKL
  threads one. Asserted no CUDA build/device availability. Models initialized locally;
  no pretrained model weights, datasets, final tests or GPU training were accessed.
- Full suite: **76 tests passed, zero skipped**, 12.707 seconds (12.797 with evidence
  bookkeeping), zero errors/failures. The three previously skipped tests verify
  adapter/base readout separation, differentiable masked completion/DPO scores, and
  tiny warm-start update/isolation/resume/export behavior.
- Warm-start fixture: one-layer Qwen3, hidden width 16, vocabulary 32, rank-2 q/v
  adapters, LoRA dropout 0.2, attention dropout 0.1, four synthetic token sequences.
  Six optimizer updates (two per agent). Interruption after update one and restoration
  into fresh objects produces exactly equal final parameters and loss/progress logs.
  Backbone and inactive adapters stay unchanged; all three agents update. All frozen
  exports match their actors, agent0 reload matches, and actor mutation is rejected
  on repeated reference verification.
- Evidence: `results_import/neural-cpu-check-001/{tests.log,verification.json,requirements-lock.txt,pip-check.txt}`.
  Log SHA256 `be34118f9ca10d5eaaf5b8aa5a78f0ea0b413e4b5e989e8ac3e2d8e42813ea7b`.
  Tested executable source hash remains
  `5762a58971732b16bb1729c7a70f8a5aaad3753ab0209627a2965068f8ed684b`;
  no executable patch, commit or push was needed. Documentation now distinguishes
  verified tiny CPU behavior from pending real Qwen3-8B GPU execution.
- Next: review/publish a pinned revision and prepare the bounded Colab training
  memory/persistence handoff. Activation checkpointing, BF16/GPU training and GPU
  resume remain unverified; full PACT collection/training remain unimplemented.
  [Detailed review](reviews/neural-cpu-check-001.md).


## Warm-start Colab preparation — `warmstart-colab-check-001` (2026-09-18)

- Added the explicit, one-update-default training notebook, redacted subprocess
  logs, small review ZIPs, complete checkpoint persistence, exact-snapshot restore
  and a persistence-only retry. No GPU training was launched.
- Extended the authorized tiny neural test to use non-reentrant activation
  checkpointing; uninterrupted and fresh-object resumed weights/logs still match
  exactly with dropout, frozen backbone/inactive adapters and valid reference exports.
- All **81 neural-enabled CPU tests pass**, zero skipped, 17.782 seconds. Default
  dependency-free suite: **78 passed, three expected skips**, 11.685 seconds.
- New fixture tests verify checksummed review archives, full checkpoint restore via
  the deadline worker, corruption/traversal rejection without partial publication,
  persistence timeout/retry, preserved training failure status and notebook execution
  opt-in. Actual training on GPU, GPU resume and Drive checkpoint performance remain
  unverified. No pretrained models, new datasets or final-test data were downloaded.
- Source hash: `22b9dd8ed1662cd6ebd487a26445d46fa0b7ef90dace4eaae2ac3b1d94949eb1`.
  Evidence: `results_import/warmstart-colab-check-001/{tests.log,default-tests.log,verification.json}`.
  Neural log SHA256: `94f59d48f58c53e2db954c7adb8e572bc2cfb5f2a6f7089952b633f5d97ae977`.
  Default log SHA256: `578fcc066255cc40cb3eb08a496d7dce2b57cdf0c1680458c00aae9a05592dae`.
- Next execution: publish/pin this revision, run one Qwen3-8B optimizer update using
  `02_warmstart_colab.ipynb`, return the small review ZIP, and preserve the complete
  verified checkpoint object store in Drive before resetting the runtime.


## Returned first GPU warm-start update — `qwen3-warmstart-001` (2026-09-19)

- ZIP SHA256 `060d1a115631a785c85749cd53f4fa1ca0f190d919e6b95d9ceeb2e5a73034ab`,
  34,280 bytes; all 11 archive members and ten payload checksums verified. Raw import
  preserved under `results_import/qwen3-warmstart-001-review/`; CPU-only audit script
  and report under `results_import/qwen3-warmstart-001-analysis/`.
- Clean code `a277794d271720665d57308cc15f3122f1934e27`; source/config/data pins match.
  All 12 training prompts/targets/masks and three sample orders reproduce. Recorded
  tokenization checked structurally, not rerun. Same Qwen base/runtime fingerprint.
- One agent0 AdamW update, effective batch four, 24 completion tokens; mean NLL
  1.0178536289, pre-clipping gradient norm 11.9798793793. Checkpoint metadata for
  steps zero/one is consistent, 432 adapter tensors each and 144 optimizer states
  after the update. Full tensor bytes excluded from the review ZIP.
- 124.263 seconds invocation including 55.798-second model load; final persistence
  excluded. Peak allocated/reserved 15.777/16.010 GiB on executed lengths
  320/449/127/139. Not a full-cap memory or length-sensitivity profile; units unknown.
- Deliberate optimizer-boundary stop; exit zero. Enclosing receipt reports verified
  Drive snapshot `1789795816767143719-d1a84cb6fab7` and the user reports ZIP copy
  success. Drive objects not independently accessed locally. Nested false flags
  are earlier local training status, not contradictory copy failures.
- Gate passed for same-recipe resume of eight remaining updates and frozen exports.
  GPU resume and final exports stay unverified until returned evidence. No full PACT
  learning or efficacy claim, no final-test access, no executable patch or new GPU run
  by the local reviewer. [Full review and next cell](reviews/qwen3-warmstart-001.md).

## Completed GPU warm start — `qwen3-warmstart-001` (2026-09-19)

- Final ZIP `qwen3-warmstart-001-handoff-1789796424401226566.zip`, 126,895 bytes;
  SHA256 `417682b7868231c4103ae4a324d4213263b9308aaf97dfecc7c178191ad587be`
  matches the supplied log. All 32 safe members and 31 payload checksums verified.
  Raw import: `results_import/qwen3-warmstart-001-complete-review/`; reproducible
  CPU audit and report: `results_import/qwen3-warmstart-001-complete-analysis/`.
- Identical clean code `a277794d271720665d57308cc15f3122f1934e27`, source/config/
  data/model/runtime pins, run metadata and 12 example records. Checkpoints zero
  and one preserve metadata bytes and recorded tensor hashes/sizes. All ten
  checkpoint records contain the expected identities, optimizer agents/settings,
  tensor references and cumulative logs. No tensor payloads were imported.
- Fresh-process GPU continuation logs exactly 32 new microbatches for updates 2–9,
  in the fixed order. Final nine updates / 36 examples / 216 completion tokens;
  three updates per agent. Status complete, exit zero; no numerical failure reported.
- Three rank-16 q/v warm-start reference exports at step nine. Configs and combined
  hashes reproduce from inventory; distinct weight hashes. Runtime exporter verifies
  actual exported tensor equality; that comparison is not independently repeated
  locally. Full adapter hashes and limits are in the linked review.
- Resume invocation 103.988 seconds, including 10.036-second model load, excluding
  final copy/ZIP generation. Both invocations total 228.251 seconds. Resume peak
  allocated/reserved 15.891/16.254 GiB, executed sequences 112–449 tokens. Compute
  units unknown. Different-batch loss values are not an improvement measurement.
- Enclosing receipt reports verified final snapshot `1789796424349439412-7eeb6af87200`
  and the user log reports verified handoff persistence. Inventory totals
  1,565,774,671 bytes. Preserve the whole Drive object store; the review ZIP cannot
  resume weights. Post-reset restore and uninterrupted GPU equivalence unverified.
- Bounded warm-start engineering gate complete. Next is local frozen-reference
  reload/scoring and train-only replay-bank collection implementation; no further
  GPU invocation, raw export, sampling expansion or full-study launch is requested.
  No PACT efficacy claim or final-test access. [Full review](reviews/qwen3-warmstart-001-complete.md).


## Frozen reference / collection implementation — 2026-09-19

`collection-implementation-001` is a local CPU implementation check, not a research
experiment. The default suite passes 85 tests with five optional skips; the full
neural opt-in suite passes 90/90 using CPU torch 2.9.1, Transformers 4.57.6,
PEFT 0.18.1 and Accelerate 1.12.0. Random tiny-model scoring verifies frozen-policy
separation and actual-token causal log probabilities. Synthetic collection checks
exercise paired raw replays, interrupted resume, empty preferences, immutable
cache, timed storage failure, verified snapshots/bundles and exact restore.

The actual frozen training-data plan selects `arc_challenge:MCAS_2004_5_13` and
`logiqa:train-7374`; it makes no model calls. The complete warm-start tensor exports
remain on Drive and are not represented by synthetic fixture tensors. Retained
logs, dependency/source identity and plan are in ignored
`results_import/collection-implementation-001/`. No GPU run, optimizer update,
paid API, final-test access or paper-result change occurred. Review/publish the
increment before the first one-record Colab collection check.
[Review](reviews/collection-implementation-001.md); [recipe and commands](collection.md).


## First GPU training-bank record — `qwen3-bank-001` (2026-09-19)

- ZIP: `qwen3-bank-001-handoff-1789803598490756574.zip`, 25,657 bytes;
  SHA256 `ceba32531b82864d694020ac29dce8e612b887c031da198cc644e5982697a7c3`.
  Ten safe members, nine payload checksums and recorded shard-marker hash pass.
- Clean source `12861a1ca4dce794a1f4daaa27e02618fed2956e`; recipe, training data,
  Qwen base, three warm-start hashes and runtime match the reviewed identities.
- One clean `arc_challenge:MCAS_2004_5_13` record, intentional boundary stop,
  exit zero. All 19 outputs parse correctly but answer C against gold B; three
  private candidate pools lack correct samples, zero suffix branches, zero eligible
  receiver contexts and zero reference forwards. Three actor answer scores execute.
- 3,826 generation input / 892 output tokens; 522 teacher-forced input tokens.
  Invocation 180.863 seconds; summed generation 64.664 seconds; bare model load
  56.551 seconds; peak allocated/reserved 15.517/15.619 GiB. Final persistence/ZIP
  time is outside the invocation timer; compute units unknown. Runtime fingerprint
  matches prior L4 but this archive has no fresh hardware-name report.
- Receipt reports verified snapshot `1789803598420081006-9645623d1b3e` under
  `PACT/collection/qwen3-bank-001`. No independent current-Drive/ZIP-copy or
  post-reset restore verification. Metadata ZIP is not a resume archive.
- Original extraction: `results_import/qwen3-bank-001-first-review/`; reproducible
  audit and derived accounting: `results_import/qwen3-bank-001-first-analysis/`.
  No executable source change or test-suite rerun for this artifact-only review.
  Next: same-commit resume for the remaining five fixed records, then return the ZIP.
  [Full review](reviews/qwen3-bank-001-first.md).


## Completed GPU training bank — `qwen3-bank-001` (2026-09-19)

- Final ZIP `qwen3-bank-001-handoff-1789804954424856576.zip`, 149,828 bytes;
  SHA256 `a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`.
  Nineteen safe members, 18 checksums, 23 inventory entries verified. First shard
  and resource attempt preserved byte-for-byte; code/config/data/model pins unchanged.
- Six records complete on clean `12861a1ca4dce794a1f4daaa27e02618fed2956e`.
  Resume adds 199 calls to the prior 19. All 218 call contexts/seeds and raw parses
  audited; five private pairs / 20 suffix branches pass paired continuation checks.
  Credits: four zeros, one +1 (LogiQA exchange agent2); 13 missing-correct pairs stay null.
- Two hold / four repair contexts generate 24 receiver candidates: 14 valid wrong
  answers and ten abstentions, zero correct. Zero preference pairs and reference
  forwards; `full_revision_ready=false`. Eighteen answer and five positive-packet
  NLL forwards execute. All six main trajectories fail; two initial-correct LogiQA
  records lose coverage during revision. No effectiveness estimate from this pool.
- Total generation: 76,067 input / 10,588 output tokens, 767.484 seconds; 218 EOS
  completions, 165 valid answer parses / 53 abstentions, zero other parse/length
  failures. Max prompt plus reserved output 723 tokens. Teacher-forced inputs 5,814.
  Continuation invocation 775.588 seconds; both invocations 956.451 seconds, excluding
  final snapshots/ZIP operations. Continuation peak allocated/reserved 15.593/15.939
  GiB. Compute units unknown. No new hardware-name report; prior L4 fingerprint matches.
- Final snapshot receipt `1789804954384930583-a1a797f59f54`; supplied log reports
  successful snapshot and ZIP persistence. Current Drive contents and post-reset
  restore unverified. Bank hash `30586d9503f0cab543c24d9ec0259c88561fa8a7180172ad63a0edec98f36e4b`.
- Original: `results_import/qwen3-bank-001-complete-review/`; derived audit/metrics:
  `results_import/qwen3-bank-001-complete-analysis/`. CPU audit passes; no executable
  source change or suite rerun. Stage complete. Next is local training-only
  preference-feasibility design, not another invocation or full revision training.
  [Review](reviews/qwen3-bank-001-complete.md).


## Receiver feasibility / base-control implementation — 2026-09-19

`preference-feasibility-001` is a local analysis and CPU implementation check.
Actual bank selection is frozen at digest
`31f2d542eb0d8cafb813d1cecb2b198ea605bc74f687b5d720d9f6b2cffe56b4`;
config hash `1ae482c52879ac3a37f7e596b8d54eb142ce2c526a3b76c75def00dd04cb66da`.
Source: completed bank ZIP SHA256 `a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`,
bank hash `30586d9503f0cab543c24d9ec0259c88561fa8a7180172ad63a0edec98f36e4b`.
Selection reuses 54 actor outputs; zero new base outputs have been collected locally.
The next explicit GPU recipe caps new base generation at 54 calls / 13,824 tokens.

All 97 tests pass with tiny CPU neural opt-in; default passes 92 with five skips.
New synthetic checks cover plan-only operation, source/prompt/runtime identity,
independent diagnostic pairing, resume and verified source-copy/snapshot/ZIP/restore.
Retained plan, source counts, test logs and environment/source verification are in
`results_import/preference-feasibility-001/`. No GPU execution, model-weight download,
optimizer step, training-pair export or paper result was produced. The diagnostic
requires review/publication and a returned handoff before promoting its GPU status.
[Review](reviews/preference-feasibility-001.md); [exact next Colab sequence](preference_feasibility.md).


## Completed fixed-context base control — `qwen3-base-control-001` (2026-09-19)

- ZIP `qwen3-base-control-001-handoff-1789830893982847246.zip`, 165,411 bytes;
  SHA256 `49bf59ceaeabcd917a91db4fef0ab0ed92fb05a367bd5233c05bc1fe3e1dc954`.
  All 63 safe members, 62 payload checksums and 115 inventory entries pass.
- Clean commit `80992b48f9159c427d65e87cbd80849af295021b`; executable source hash
  `8c36005865aec6f91af273e71e781f1a59dd816b88c16262c9def1901272c3b4`.
  Original source ZIP/bank, all 54 requests and 12 groups reproduce. Prompts,
  actual token prefixes, seeds, full sampling parameters and model/runtime match.
- 54/54 base generations complete, one attempt, no training. ARC private: base
  0/15 correct, actors 0/15. LogiQA private: base 7/15, actors 6/15. Hold: both
  0/8 correct, eight abstentions. Repair: base 0/16 (16 wrong), actors 0/16
  (14 wrong, two abstentions). Zero hold/repair pairs. All 54 EOS, no malformed
  or length failures; 35 raw strings/completion arrays unchanged from actors.
- 16,995 input / 3,275 output tokens, summed generation 226.624 seconds,
  invocation 343.519 seconds, model load 57.588 seconds; final persistence outside
  invocation timer. Peak allocated/reserved 16,515,663,872 / 16,607,346,688 bytes.
  Zero cache hits; compute units unknown; prior L4 runtime fingerprint matches.
- Receipt reports verified snapshot `1789830893946689797-d4fc812509bb` under
  `PACT/diagnostics/qwen3-base-control-001`. User reports final Drive bundle.
  Current Drive and post-reset diagnostic restore remain independently unverified.
- Originals: `results_import/qwen3-base-control-001-review/`; audit and recomputed
  report/metrics: `results_import/qwen3-base-control-001-analysis/`. Artifact audit
  passes; no executable source change or suite rerun. Close the diagnostic; next
  is local broader train-only feasibility design. No warm-start regression or
  PACT efficacy claim follows. [Full review](reviews/qwen3-base-control-001.md).


## Broader receiver-feasibility design — `receiver-feasibility-design-001` (2026-09-19)

- Offline design/planner only. Proposed GPU run `qwen3-receiver-feasibility-001`
  has not executed and its dedicated runner is not implemented.
- Recipe hash `efa9d8cfb1450227b80286309505116d9a8e03fd1732d99d1ee6b5bcabf3d7e1`;
  selection hash `e6842155a4080c0a39e3ad39a8b207539312ffb57b05da7675a7343136e33d96`.
  Checked-in config and 24 exact task IDs/input/label/group hashes reconstruct from
  the pinned proposal-1200 and engineering-12 artifacts. Warm-start exclusions,
  12-per-family balance and four occurrences per sender/family pass.
- Planned clean/exchange only, 48 records, at most 144 eligible receiver contexts
  with four samples each: maximum 912 calls / 224,256 output tokens. Zero replay,
  teacher-forced or optimizer calls; no training-pair export. Fixed existing
  actors and runtime; all outcome rules recorded before collection.
- Six new planner tests pass; full suite 103/103 with CPU neural opt-in and
  98 passed/five skipped by default. No model/data download, GPU execution or
  new scientific outcome. Evidence: `results_import/receiver-feasibility-design-001/`.
- Next: implement the receiver-only runner and its required recovery/accounting
  checks, then review/publish before Colab. [Design](receiver_feasibility_design.md).


## Receiver-only runner implementation — `receiver-feasibility-implementation-001` (2026-09-20)

- Implemented the frozen 24-task/48-record diagnostic with the same recipe and
  selection hashes as the preceding design entry. Ceiling: 912 generation calls,
  224,256 output tokens, zero teacher-forced forwards and optimizer steps.
- Call intents, immutable raw results, partial-pool reconstruction, reports and
  local/Drive handoffs are CPU tested. Restore rejects unresolved attempts and
  older or unsafe snapshots to prevent unaccounted re-sampling after runtime loss.
- Ten added tests pass. Full suite: 113/113 with tiny CPU neural opt-in; default
  107 passed/six skipped. Tiny initialized Qwen/PEFT checks preserve actor/reference
  tensors and restore adapter state after base readout. Six guide cells compile.
- Evidence: `results_import/receiver-feasibility-implementation-001/`. The actual
  offline production plan still executes zero model calls. Synthetic fixture
  outcomes are not receiver-support evidence and do not fill paper placeholders.
- No GPU experiment, pretrained download, new optimization or final-test access.
  GPU collection/recovery is unverified. Next: review/commit/push, then the pinned
  [Colab sequence](receiver_feasibility_colab.md) and returned ZIP audit.
  [Implementation review](reviews/receiver-feasibility-implementation-001.md).

## Completed broader receiver screen — `qwen3-receiver-feasibility-001` (2026-09-20)

- ZIP `qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip`,
  2,068,798 bytes; SHA256
  `d61cb9bb82895f09f146a83ac52a26d4fdad18238585fb0bcf4bd13034996a9f`.
  All 1,004 members, 1,003 payload checksums and 1,522 inventory entries pass.
- Clean published source `b3951fde181bb216130cb206fdf87e39fca87632`, executable
  hash `57e1b6bf2a469e15bb7dcafde8f22126fb454c660b661ae9107eda8f2602a964`.
  Frozen plan reconstructs; all 48 records and 472 logical calls replay offline
  from saved results with exact protocol/request/seed/label accounting.
- Hold: 32 contexts/16 tasks, 128 correct candidates, zero wrong, zero pairs.
  Repair: two contexts/one ARC task, eight correct, zero wrong, zero pairs.
  Remaining 110 contexts ineligible. All candidate pools complete; every missing
  pair is missing-incorrect. Main clean final 15/24, exchange 16/24.
- One invocation, 472 fresh generations, no cache hits/unresolved attempts;
  168,842 input and 22,390 output tokens. All EOS. Invocation 1,812.534 seconds,
  generation sum 1,620.704 seconds, model load 56.691 seconds. Peak allocated /
  reserved 16,739,545,600 / 16,890,462,208 bytes; compute units unknown.
- Handoff reports verified snapshot `1789837104902108384-c21c9fca326b` under
  `PACT/receiver-feasibility/qwen3-receiver-feasibility-001`. User reports Drive
  ZIP. Current Drive, independent tensor checks and GPU reset/resume unverified.
- Close with prespecified `no_pairs`; neither gate passes. No scoring, training,
  final-test access or efficacy claim. No extension/retry to obtain negatives.
  Originals and reproducible audit retained in corresponding `-review` and
  `-analysis` directories under `results_import`. Documentation-only review;
  no executable change or suite rerun. [Full review](reviews/qwen3-receiver-feasibility-001.md).

## Offline support diagnosis — `receiver-support-review-001` (2026-09-20)

- Re-read the checksum-verified broader receiver ZIP and prior training bank.
  No new data/model download, generation, optimization or final-test access.
- Count each paired private draw once: 15/24 tasks all-correct, eight all-wrong,
  one mixed; 23/24 unanimous answer IDs. All 72 clean/exchange private outputs,
  token arrays and seeds match, as expected for paired branches.
- Only two of 26 initially wrong receivers have a correct clean peer. Both lose
  it when the frozen exchange assignment corrupts the mixed task's sole correct
  sender. Thirty of 32 hold contexts also retain another correct peer. The 34
  scheduled pools represent 33 distinct task/agent/prompt combinations.
- Four distinct candidate seeds per pool, sampling enabled; 20/34 pools vary in
  raw text/tokens, yet all candidates remain correct. No cause attributable to
  adapter weights or sampling settings is identified from these observations.
- Recorded proposed second-seed private-control inventory: same 24 tasks, seed
  1730, 72 requests, at most 18,432 output tokens. Unimplemented/unrun; no training
  gate on private-only outcomes. This does not extend the completed receiver run.
- Reproducible script, task/pool tables, summary and evidence hashes are in
  `results_import/receiver-support-review-001/`. Actual-artifact assertions pass;
  documentation-only change, no application test-suite rerun.
  [Review and next design](reviews/receiver-support-review-001.md).

## Private-support control implementation — `private-support-implementation-001` (2026-09-20)

- Implemented plan-only-by-default `private-support-control`, frozen config,
  72-call actor collection, separate-draw report, call-boundary resume and timed
  local/Drive handoffs. Proposed run: `qwen3-private-support-control-001`.
- Actual parent ZIP reconstructs the exact 72 previously recorded requests.
  Config hash `da15b8979e5142e82b55e74f49e453773bb2c9bcb72f8011de47190d606dbab8`;
  full request hash `98e749e8b4d2c3fe20f8a3643af7fc8e362febff4a4ae7dae1450cbbf5333571`.
  One new seed (1730), max 18,432 output tokens, no additional receiver or training calls.
- Seven new tests; full default suite 114 passed/six optional skips, 120 total.
  Prior temporary CPU neural environment absent; optional rerun unavailable.
  Five Colab cells compile; actual offline plan makes zero model calls.
- No pretrained/model/data download, GPU inference, optimization or final-test
  access. GPU execution/recovery unverified. Evidence retained in
  `results_import/private-support-implementation-001/`.
  [Review](reviews/private-support-implementation-001.md); [Colab guide](private_support_control_colab.md).

## Completed private-seed control — `qwen3-private-support-control-001` (2026-09-20)

- ZIP SHA256 `f67045fc3f2bc102e7345ba3337c5406796360e76f437355dd849302cb33bc06`,
  434,491 bytes. All 225 members, 224 payload checksums and 367 inventory entries
  pass; exact plan and 72 saved requests reconstruct, and report recomputation agrees.
- Clean commit `91655a83503a466c4f773a49053d86b54fb71cab`; source hash
  `8b5eb9a5af5c2b9dfb4f6d3e42b4ccb30193bf75cfef03bf49607f9f0fba3d44`.
  Same 24 tasks, prompts, actors and runtime; one new seed, 1730.
- Original → control: mixed tasks 1 → 0; all-correct 15 → 15; all-wrong 8 → 9;
  unanimous answers 23 → 24; potential clean-repair contexts 2 → 0. Only agent 2
  on `arc_challenge:Mercury_406916` changes answer, A/correct → B/wrong.
- 72 new calls, all EOS and valid, zero cache hits/unresolved attempts/scoring.
  16,755 input / 3,863 output tokens; invocation 411.096 seconds, generation sum
  274.984 seconds, model load 55.511 seconds. Peak allocated/reserved bytes
  16,666,484,224 / 16,733,175,808; compute units unknown.
- Receipt reports verified snapshot `1789909726482309183-c1ebb2f50100` under
  `PACT/private-support/qwen3-private-support-control-001`; user reports final
  Drive bundle. Current Drive, independent tensor checks and GPU resume unverified.
- Close this fixed control. No receiver calls or new preference evidence. No
  further seed sampling scheduled; next requires a separate design review.
  Original bytes and audit retained under corresponding `-review` / `-analysis`
  directories in `results_import`. [Full review](reviews/qwen3-private-support-control-001.md).

## Curated repair design — `curated-repair-design-001` (2026-09-20)

- Offline design/planner only, proposed run `qwen3-curated-repair-001`.
  Inputs are the checksum-pinned broader receiver and private-control ZIPs.
- Inventory all nine all-wrong tasks: two ARC tasks have a stored correct main
  packet; seven lack donors, including all five LogiQA tasks. Selected donors:
  `Mercury_406916`, agent 2 clean private; `Mercury_7210613`, agent 0 exchange
  revision. The original actor, raw text and phase remain recorded.
- Freeze the saved private states. Two recipients per task, original/curated
  arms, four matched samples per arm: eight pools, 32 calls max, 8,192 output
  tokens. No new private packets, readout, reference score or optimization.
- Config hash `ac29ebf94ee954729923ed7d72c8e474cf165e48a289a545fe0e8b6a002587d4`;
  contexts hash `66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab`.
- Four added tests; full default suite 118 passed/six optional skips, 124 total.
  Actual source reconstruction and context invariants verified locally, zero
  model calls. Evidence: `results_import/curated-repair-design-001/`.
- No GPU execution or available execution command. Next is runner/recovery/report
  implementation, local checks, user publication and pinned Colab execution.
  [Scope, limitations and fixed decisions](curated_repair_design.md).

## Curated runner — `curated-repair-implementation-001` (2026-09-20)

- Implements the existing 32-call / 8,192-output-token recipe; config and context
  inventory hashes match the preceding design exactly. No new real model calls.
- Adds all-context tokenized preflight, fixed revision requests, per-arm reports,
  paired-seed comparisons, durable call budgets and latest-safe-snapshot restore.
- Eight new runner tests; full default suite 126 passed/six optional skips,
  132 total. Actual source plan reconstruction, Colab syntax/import and doc links
  checked. Evidence: `results_import/curated-repair-implementation-001/`.
- User review/publication precedes the [pinned Colab run](curated_repair_colab.md).
  GPU execution, actual context fit and GPU reset/resume remain unverified.
  No hold/LogiQA coverage or training-readiness claim. [Review](reviews/curated-repair-implementation-001.md).

## Completed curated diagnostic — `qwen3-curated-repair-001` (2026-09-20)

- ZIP SHA256 `c06a1cff473841c7271f2c07e61f6e0a61b31c76b982361f4ddeb029917ea3b4`,
  217,060 bytes; 106 members, 105 payload checksums and 168 inventory entries pass.
- Clean source `43151280b2b4c01a1461445878c3a544dad397db`, executable hash
  `5070895320fa98c4bb44ffbf673ba525aadc4f0bb414406f641983ae9c9399bb`.
  Exact plan, all 32 requests and full report reconstruct; all eight prefixes fit.
- Original peers: 0 correct / 8 wrong / 8 abstentions. Curated help: 8 correct /
  8 wrong. Moon task 0/8 → 8/8; thermal task 0/8 → 0/8. All 32 outputs end at EOS.
- Zero within-arm pairs, including zero curated repair pairs. No missing calls,
  cache hits, scoring, training or readout. Fixed diagnostic closed.
- 12,392 input / 1,787 output tokens; invocation 249.594 seconds, generation sum
  129.298 seconds, model load 55.911 seconds. Peak allocated/reserved bytes
  16,685,571,072 / 16,770,924,544. Compute units unknown.
- Receipt reports verified snapshot `1789919214806955396-1edfd59d13d4` under
  `PACT/curated-repair/qwen3-curated-repair-001`; final Drive path supplied by user.
  Current Drive and GPU reset/resume independently unverified.
- Original bytes/audit retained under corresponding `-review` / `-analysis`
  directories in `results_import`. [Review](reviews/qwen3-curated-repair-001.md).
  No new GPU run or training stage is scheduled.

## Actor preparation design — `actor-preparation-design-001` (2026-09-20)

- Proposed training `qwen3-preparation-120-001`, probe `qwen3-preparation-probe-001`.
  No execution. Select 120 tasks, 60/family; retain twelve old warm-start tasks,
  exclude 24 probe task/component/content IDs. No outcome-dependent task ranking.
- Selection hash `57fb394c7aee9be6569fd12c48819bec9f06086d5cc022ee65510c7fa30a15fe`;
  config hash `ec1ba60de4b4a904e278282b5e34dd79803110fa0ee4079bf6757e74aec15dc5`.
- Fresh adapters, same seeds/settings, one pass/agent: 360 example presentations,
  90 optimizer steps. Final checkpoint only; no checkpoint selection on probes.
- Private probe 72 calls plus fixed old-context receiver probe 32 calls; maximum
  104 generations / 26,624 output tokens. No new natural rollout or final readout.
- Actual source reconstruction and selection/order/budget checks pass offline.
  Three new tests; default suite 129 pass/six optional skips, 135 total.
  Evidence: `results_import/actor-preparation-design-001/`.
- Larger training/probe runner unimplemented; no new Colab command. Next is its
  bounded implementation and CPU recovery validation. [Design](actor_preparation_design.md).

## Actor preparation execution — `actor-preparation-implementation-001` (2026-09-21)

- Implements the frozen 120-task / 90-update training stage and separate 104-call
  probe without changing config, selection, training recipe or request/context hashes.
- Adds final-reference gating, ten-update durable training snapshots, attempted-example
  accounting, old-prefix probe validation, matched checkpoint comparisons and latest
  safe probe restore. No model downloads, GPU updates/calls or new research outcomes.
- Six new CPU tests; full default suite 135 passed/six optional skips, 141 total.
  Optional neural tests were not rerun. Local source reconstruction, frozen hashes,
  Colab cell syntax/imports and documentation links checked.
- Evidence: `results_import/actor-preparation-implementation-001/`. Larger training
  context fit, full checkpoint storage, GPU execution and GPU reset/resume unverified.
- Next: user review/commit/push, then [seven Colab cells](actor_preparation_colab.md)
  pinned to the new SHA; return both stage bundles. [Review](reviews/actor-preparation-implementation-001.md).

## Preparation storage recovery — `preparation-restore-repair-001` (2026-09-21)

- User receipt reports 90 updates / 360 examples complete, verified training ZIP
  SHA256 `a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388`,
  final snapshot `1789930640656395583-479df47c14d9`. ZIP audit pending.
- Full training restore exceeded 600 seconds. Probe completion is not established;
  do not infer 104 calls from training-file progress counters or rerun training.
- Implement compact final-export restore, selected-object checksums, training
  prohibition and exact-source, journal-preserving probe migration. Four new tests;
  full suite 139 pass/six optional skips, 145 total. No new GPU work.
- Evidence: `results_import/preparation-restore-repair-001/`. Next user publication
  and [inference-only recovery](preparation_probe_recovery.md); actual Drive/GPU
  path remains unverified. [Review](reviews/preparation-restore-repair-001.md).

## Imported preparation and probe — `qwen3-preparation-120-001` (2026-09-21)

- Training SHA256 `a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388`;
  probe SHA256 `ae6a0268d66af76319f5206f04fbb070f34e5283bdde4efe5c344ec70256528f`.
- CPU audit reconstructs design, verifies included checksums, 90 updates/360 examples,
  recorded final adapter identities, and exactly recomputes the 104-call probe report.
- Original probe completed 104 calls; recovery had 104 cache hits, zero new calls.
  No unresolved attempts. Review ZIPs omit tensors; local byte verification unavailable.
- Private correctness 46/72 to 45/72; potential clean-repair contexts 2 to 0.
  Receiver original peers 0/16, curated help 8/16, unchanged from old actors.
  Within-arm and curated-repair pairs both zero. Full PACT not ready.
- Evidence: `results_import/qwen3-preparation-120-001-analysis/`.
  [Review and next decision](reviews/qwen3-preparation-120-001.md). No new model run,
  tensor download, final-test use or scientific-method change.

## Objective review — `preparation-objective-review-001` (2026-09-21)

- Corrected primary private comparison: seed-1730 old/new actors 45/72 versus 45/72;
  45 correct-to-correct, 27 wrong-to-wrong, 71 identical answers. The earlier 46/72
  comparator is seed 1729 and is not a matched preparation contrast.
- Offline checks join 72 records with equal seeds, prompt bytes and token prefixes.
  Evidence: `results_import/preparation-objective-review-001/`.
- Next design: `qwen3-preparation-prompt-control-001`, 72 answer-only generations,
  same prepared adapters/tasks/seeds, zero training, no receiver generation or pairs.
  Request hash `69059c28cc3f9ab6558124c65c250814cc1e864c392ae816b67fef5857c9ad63`.
- Runner unimplemented, GPU unverified; no additional run executed.
  [Objective review](preparation_objective_review.md).

## Consolidated project audit — `project-audit-20260921`

- Consolidated all completed stages and current unimplemented proposals in
  [the audit report](audits/PACT_PROJECT_AUDIT_2026-09-21.md), including the seed-baseline
  correction, missing receiver-pair support, metadata-only tensor limits and recovery history.
- Reread/hash/CRC-check all 19 top-level retained ZIPs; archive inventory under
  `results_import/project-audit-20260921/`. This does not replace historical semantic audits.
- Fresh default suite: 145 tests in 84.606 seconds; 139 passed, six optional neural skips.
- No additional GPU calls, optimization, final-test access, commit or push.

## Prompt-control implementation — `prompt-control-implementation-001` (2026-09-21)

- User authorized the frozen 72-call diagnostic. Added its own command and restore
  kind; no historical run or scientific budget changed.
- Actual training/probe ZIPs reconstruct all 72 requests with unchanged hash
  `69059c28cc3f9ab6558124c65c250814cc1e864c392ae816b67fef5857c9ad63`.
- Six new CPU tests cover accounting/recovery, invalid schema, overflow, ambiguous
  attempts, persistence failure, plan-only CLI and Colab cells. Evidence:
  `results_import/prompt-control-implementation-001/`.
- No GPU calls or optimizer updates executed locally. Next: user publication and
  [six Colab cells](preparation_prompt_control_colab.md), return the new review ZIP.

Prompt-control validation: full default suite **151 tests: 145 passed, six optional
neural skips**, 92.010 seconds. Actual archived requests reconstruct byte-for-byte
under canonical serialization; six notebook cells compile. GPU run remains pending.

## Completed prompt diagnostic — `qwen3-preparation-prompt-control-001` (2026-09-22)

- ZIP SHA256 `a48bfe31276a58479d80780db48226ef55d3d1d85526f530e435bc497535db34`;
  all 226 members, 225 payload checksums and 368 inventory entries reconciled.
- Frozen plan and all 72 journaled calls reconstruct offline. No missing/unresolved
  calls; no cache hits, training, receiver generations or teacher-forced scoring.
- Packet versus answer-only correctness unchanged: 45/72 overall, ARC 24/36,
  LogiQA 21/36. All 72 parse. Answers unchanged 68/72; four wrong-to-wrong changes.
  Teams remain 15 all-correct/nine all-wrong, with zero mixed correctness.
- 14,235 input / 432 output tokens; invocation 161.158s including model load54.615s;
  summed generation36.562s. Receipt reports verified persistence; current Drive and
  tensor bytes not independently inspected. No run-specific reset/resume test.
- Evidence: `results_import/qwen3-preparation-prompt-control-001-analysis/`.
  [Review](reviews/qwen3-preparation-prompt-control-001.md). Close the diagnostic;
  no automatic follow-up GPU run. Documentation-only update, no suite rerun.

## Planned: qwen3-receiver-supervision-001 (2026-09-22)

- Variant `receiver_supervision_v1`, target `receiver_answer_ce_v1`; GPU **not executed**.
- Initialization: completed 120-task preparation, final step 90; original provenance
  ZIP `a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388`.
- Frozen 96-group selection hash `7c8c4319439c1cb29345961496b2e74a2713a3b0d2714489957be17af2e907fc`;
  64 fitting / 32 diagnostic held-out training groups, both families balanced;
  excludes 120 preparation and 24 prior probe task IDs plus known duplicate groups.
- One focal adapter, frozen / task-SFT / receiver-SFT arms; DPO disabled.
  Context support not yet measured. No new receiver or team accuracy results.
- Hard planned maximum: 1,296 calls / 322,560 reserved generated tokens;
  512 training forward/backward microbatches, 192 teacher-forced evaluation forwards,
  32 updates per trained arm. No private replay recollection, final-test data or sweep.
- [Methodology](receiver_supervision_methodology.md), [commands](receiver_supervision_colab.md),
  `experiments/receiver_supervision_v1.json`. The 72-call prompt control stays closed.

## Returned: qwen3-receiver-supervision-001 — support stop (2026-09-22)

- Verified ZIP SHA256 `93332881dbe83bd6dd975beaad6a678094c7f1164f9aa044674e1c06593f783b`;
  source `fd38b5e90bf6e5c648922405d46094abbc2449b2`, clean.
- 96/96 source tasks; 672/672 committed private/donor calls, zero unresolved;
  159,313 input / 34,766 output tokens. No receiver generations or optimizer updates.
- Recomputed fit hold/repair support 2/2; held-out 0/1. Five contexts across three
  unique tasks. `insufficient_context_support`; weights correctly remain empty.
- No rerun, increased draws, relaxed gate or subsequent GPU stage authorized by this
  result. [Full audit](reviews/qwen3-receiver-supervision-001.md). Study efficacy remains untested.

## Offline follow-up: receiver donor inventory 001 (2026-09-22)

Eight checksummed retained training-generation reviews, 950 distinct private/revision
call records, **zero matching tasks or known duplicate groups** for the receiver
study's frozen selection. Zero new model calls and updates. No donor packets imported
and no new GPU run scheduled. Reproducible audit and source requirements:
[receiver-donor-inventory-001](reviews/receiver-donor-inventory-001.md).

## Consolidated review checkpoint — project-audit-20260922

Compiled [the updated project audit](audits/PACT_PROJECT_AUDIT_2026-09-22.md):
completed experiments, corrected matched comparisons, original DPO and new context
support bottlenecks, verified preparation versus unexecuted receiver training,
recovery limitations and open donor-source decisions. Fresh SHA256/CRC checks pass
for all 21 retained top-level ZIPs; donor inventory reproduces exactly. No new model
calls, training, final-test access or methodology choice. Historical tests are reported
as previously executed, not rerun. Listed real inference runs total 8,646 recorded
calls; two clean-answer preparations total 99 updates/396 presentations, not PACT updates.

## Implemented, not GPU-executed: controlled peer donors child study — 2026-09-22

`qwen3-controlled-peer-donors-001` acquisition feeds
`qwen3-receiver-supervision-controlled-001`, initialized from the existing completed
120-task preparation. Parent ZIP SHA256 `93332881dbe83bd6dd975beaad6a678094c7f1164f9aa044674e1c06593f783b`
is imported read-only. Same 64/32 groups, original focal0 own packets; no new parent
calls. Offline target conditioning is explicitly authorized only for this synthetic
source. Actual donor yield, receiver learning and evaluation remain unmeasured.
Ceiling 384 acquisition / 1,104 total calls, 273,408 reserved output tokens; 32 updates
per trained arm. Missing primary support stops before updates. Historical results
remain unchanged. [Runbook](controlled_peer_donors_colab.md).

## 2026-09-23 — controlled-001 training returned; evaluation blocked

Bundle SHA256 `ce9f97aca8a24e7a15b890d5e557c3da7af8331f944847b8d4036feb152ae993`
verifies. Acquisition: 217 committed calls, zero unresolved; 154 accepted donors,
63 target mismatches. Contexts: fit45 (hold17/repair28), held-out19 (hold13/repair6),
all opposite controls available. Task and receiver SFT each completed24 updates;
returned metadata audited, tensor payloads omitted from review archive.
Evaluation made zero calls: nonfocal export hashes differ from preparation.
User diagnostics identify exact BF16 rounding, reproduced with a tiny CPU model.
Explicit evaluation-only recovery implemented; real GPU recovery and all efficacy
comparisons pending. No completed diagnostics rerun, final-test access, or full
PACT updates. [Detailed audit](reviews/qwen3-receiver-supervision-controlled-001-training.md).

## 2026-09-24 — controlled-001 bounded evaluation complete

Returned handoff1790186567377083314, SHA256
`ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea`.
All603 evaluation calls and171 CE forwards complete; with217 donors, total820 calls,
200704 reserved output tokens. Three arms share primary hold13/13 and repair1/6;
zero correctness changes on57 matched receiver conditions. Private accuracy20/32
frozen vs21/32 both trained arms; natural clean/exchange5/8,4/8 frozen/task SFT vs
4/8,5/8 receiver SFT. Lower receiver answer NLL is not a demonstrated repair gain.
Study closed at original bounds; no extra training, acquisition or final-test work.
[Full audit and limitations](reviews/qwen3-receiver-supervision-controlled-001-evaluation.md).

## Implemented / CPU-tested / GPU-unverified: qwen3-gpqa-diamond-support-001

Authorized24 September2026 inference-only development screen. Prespecify32 official
GPQA-Diamond groups at seed20260924 with domain largest-remainder allocation and one
shared option shuffle. Actual selected IDs/domain counts await authorized CSV access;
protected remainder is nominally166 (known-group exclusions may reduce it).
No prior GPQA run found in the inspected ledger; this is not a contamination claim.

Frozen effective preparation arm from completed bundle
`ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea` only.
Actual original90-step weights restored privately; historical effective rounding must
reproduce. No task-SFT/receiver-SFT checkpoint substitution.256 generation calls /
53248 reserved output tokens; zero training/scoring/donor/replay forwards.32 tasks
receive three private packets, vote, independent synthesis, clean synchronous revision,
and base readout. Two-task smoke reuses16 planned calls; all32 complete regardless
of initial correctness. Private source CSV, manifests and raw results stay outside Git.

No real GPQA access, loaded-tensor verification or outcomes yet.16 focused CPU tests
passed on invented fixtures; mocks are software evidence only. Historical receiver
result remains closed/unchanged. [Methodology](gpqa_support_methodology.md),
[Colab sequence](gpqa_support_colab.md). Every follow-up requires a new reviewed design.


### GPQA preflight blocker — 2026-09-25

User-returned Colab aggregate diagnostic reports verified official pinned files,
198 rows, zero missing options, two rows with exact stripped-string option
collisions (also two under whitespace-only and NFKC/whitespace comparison), and
three under the current NFKC/casefold/whitespace comparison. No raw benchmark
content was returned or inspected locally. Dataset preparation stopped before
selection was frozen or any study generation occurred. This is data-contract
evidence, not a GPQA performance result. Historical completed runs are unchanged.
The four-distinguishable-options contract cannot be satisfied across the source
by correcting case folding alone. No rows dropped, options edited, labels changed,
or selection regenerated. A source-integrity exclusion policy requires explicit
review before continuation.


2026-09-25 amendment authorized by user and implemented locally: exact scientific
option strings retained; malformed-option groups excluded before seeded32-item
selection. Source remains the same pinned198-row file. Two malformed singleton
rows imply196 eligible groups and164 protected items absent other group/exposure
exclusions; these are conditional expectations, not a completed real partition.
19 fictional CPU tests pass; no generation calls or GPU evidence. Next: user
review/commit/push, new pinned Colab checkout, repeat dataset preflight on the
already downloaded source, then the unchanged fixed study if all guards pass.


### GPQA completed return — qwen3-gpqa-diamond-support-001

Source1627abae3dd724cdbbb5358ebc6152d4c9be77d7;32/32 complete,256/256 calls,
0 unresolved;53248 reserved output tokens. Both returned ZIP checksums verified;
private report reconstructed and identical to sanitized summary. Historical frozen
contract and returned environment identities match. Partition32 selected/164
protected/2 malformed exclusions; domains3 Biology/15 Chemistry/14 Physics.
Mixed support2/32; N0=[23,2,0,7]; coverage9/32 equals best agent9/32. Both mixed
teams transition1→0; hold0/2, repair0/4 across2 tasks. Vote/synthesis/debate all7/32;
paired synthesis/debate25 wrong→wrong and7 correct→correct. Screen sparse_preliminary.
GPU-executed evidence audited; no PACT efficacy/final-test claim or follow-up
authorized. [Full sanitized audit](reviews/qwen3-gpqa-diamond-support-001.md).

## Assignment characterization / fixed-bank implementation — 2026-09-25

The checksum-verified completed qwen3-bank-001 training bank was characterized
without a model or optimizer. Two tasks,6 rows,18 cells; eligible-row histogram
{0:4,1:0,2:1,3:1};5 valid cells but only1 distinct supported/multi-eligible task.
Historical standardized mean credit/local L1=0.7705078615; local/uniform=0.1122392611;
raw-NLL credit/local sensitivity=0.7784436707. Thus actual continuation credit
changes assignment on this bank, but it is not adequate new-study fitting support
and does not establish learning efficacy. No missing score filled; validation
replays not promoted into fitting data. Outputs:results_import/assignment-contrast-001/.

New qwen3-specialization-contrast-001 dry planning selects64 fresh groups after240
known task-ID exclusions;32fit/32development,16/family/partition. No GPU call or
optimizer update executed on these real tasks. New-stage upper bounds1216collection,
3072replay,2048evaluation calls,6336total/1363968reserved output tokens,288updates.
Stage hash/explicit opt-in and candidate/assignment gates are implemented; this is
specialization only, receiver/DPO off. Completed GPQA and controlled results remain
unchanged. [Full methodology](specialization_fixed_bank_methodology.md).

Implementation validation completed:204 default tests,191 pass/13 optional skips;
2 separately executed tiny CPU neural tests pass. The complete mock round trip
covers all four evaluation systems and safe bundle reconstruction. Mock optimizer
status remains explicitly synthetic; optional real tiny optimization validates
sequential actor updates and exact resume, not8B efficacy. Actual new-study GPU
stages have not been launched. Commands:[specialization Colab/local runbook](specialization_colab.md).


## Fixed-bank collection return — 2026-09-26

qwen3-specialization-contrast-001: uploaded SHA256
555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f verified.
Trusted report reconstruction and separate complete collection/pair-mask
reconstruction pass. All32 fitting tasks/64 condition rows complete;1216 calls
attempted/committed,0 unresolved,299008 reserved output tokens. Five eligible
cells across2 supported tasks and2 multi-eligible tasks; required minima8/8 fail.
Row eligibility histogram:62 zero,1 two,1 three. Status
insufficient_assignment_support. No replay, scoring, optimization or held-out
evaluation executed. Collection is now GPU-executed/audited; no learning efficacy
claim. Stop before downstream stages; no automatic draws/task replacements or
method changes. [Full audit](reviews/qwen3-specialization-contrast-001.md).

## qwen3-controlled-specialization-001 — implementation, no GPU execution

2026-09-26. Authorized child of the stopped natural collection, source
controlled_private_packets_v1, estimator controlled_slot_delta_v1. Reuses original
32fit/32development groups,64 clean/early anchors, early bytes and effective frozen
preparation actors. Real parent import and missingness reconstruction passed:
768 candidates=361 valid-correct+405 valid-wrong+2 length-limited;100 missing-correct,
87 missing-incorrect,5 eligible cells. Historical parent status unchanged.

New ceilings128 donor/3072 primary/768 order/80 natural-calibration/2048 evaluation
calls =6096;1274112 reserved tokens;384 frozen scores;288 optimizer updates.
Zero new real generation/scoring/training calls locally. Implementation/mock and
tiny CPU tests are software evidence only. Planning requires later-development-use
review. Each GPU stage needs the frozen child plan hash and explicit invocation;
training also needs passed practical gates and an artifact-bound user review.
No outcome automatically authorizes another run. [Method](controlled_private_specialization.md).

Local validation completed:215 default tests (201 pass,14 optional skips),7 final
guard tests pass,3 optional tiny CPU neural tests pass. The full fictional
controlled pipeline and review ZIP reconstruction pass; actual-parent plan-only
export/import passes with zero new model calls. First full-run test fixture Path
error was fixed and verified. Training initialization and final evaluation have
separate immutable environment receipts; frozen actor mismatches stop before
replay/scoring. Next authorized implementation handoff is user review/push and
pinned plan-only Colab setup, not an automatically scheduled GPU experiment.


## 2026-09-27 — controlled-specialization acquisition imported

CPU-only returned-bundle audit passed for SHA256
`4e5e522894f8a67d6486c7ddc769e70843c3110000f0f6a9386e3af371378c52`.
Real Colab acquisition: 75 committed calls, zero unresolved, 22/32 complete
synthetic pairs (11 per family), 132 eligible cells across 44 clean/early rows.
Both eight-task support gates pass; replay/scoring/training/evaluation remain
unexecuted. Fixed-sample inspection identifies answer/rationale contradictions
in some negative packets; structural acceptance is not reasoning verification
or human training approval. Parent and original results unchanged; no new run
authorized. See [acquisition audit](reviews/qwen3-controlled-specialization-001-acquisition.md).


## 2026-09-29 — controlled child implementation completion (no new experiment)

Reconciled the consolidated brief with the existing all-stage implementation and
actual acquisition. Only the previously audited 75-call acquisition ZIP is present;
no new replay, scoring, training or development outcomes have been imported.
Preserve the existing child ID, source/plan, exposure attestation and all artifacts.
New local guards/fixture/handoff/restore options do not authorize extra calls or
source migration. Parent remains stopped at 1,216 calls/five cells/two tasks.
See [completion handoff](controlled_replay_completion.md) for tests and commands.

Completion validation: 221 default tests (207 pass,14 optional skips),12 final guard
tests and3 tiny CPU neural tests passed; existing acquisition re-audit passed.
These are software checks, not additional experiment calls or learned outcomes.


## 2026-09-30 — controlled replay recovery receipt audited

Receipt SHA256 `e1df0d2818306cf5cdd384ac42f178c06a27dd6e15399962cb57ab5a0f70cc51`.
Latest indexed snapshot `1790455158060324752-c824b049ff36` has recovery_safe=false.
Verified index/COMPLETE/state hashes and compared frozen acquisition hashes against
its previously audited ZIP. Plan, pairs, support, parent receipt and indexed
acquisition/donor artifacts are unchanged. Reconstructed expected replay cell IDs:
132/132 primary,36/36 order,4/5 calibration indexed. Missing calibration cell is
arc_challenge:MCAS_2004_8_8 / early / agent2 (zero-based), record key
`dd97205b8e8b3ed83c19648126dabca933eaf866e52422ffb5603d76f55529ad`.

The receipt contains inventory hashes, not replay object payloads; actual outcomes
and credit values have not been reconstructed. Saved call counts are75 acquisition,
2112 primary,576 order,64 calibration (2827 total); this is not a bound on calls
that may have occurred after the unsafe marker. Up to16 calls of the last calibration
cell may be unrecorded. No safety flag was changed, older snapshot selected, call
reissued, source migrated, or training authorized. The original80-call calibration
cap and complete-evidence gate remain in force. Recovery requires additional
retained evidence or an explicitly reviewed amendment, not implicit budget reset.
Machine-readable local audit: results_import/controlled-recovery-receipt-audit.json.


## 2026-09-30 — saved controlled replay payloads forensically reconstructed

Forensic ZIP SHA256 `2ad3152c12d7215a421e35e68325cb98cd541c36d769ede3a6da7b4b9c6d736b`;
latest snapshot remains `1790455158060324752-c824b049ff36`, recovery_safe=false.
This supplements the earlier inventory-only receipt audit; it does not supersede
its unsafe-resume finding. All 177 selected payload hashes match the full snapshot
index and COMPLETE hash; the index equals the previously audited recovery receipt.
The pinned plan hash remains
`fb554a12c60da2d354606f8fb1f5d5c6894321adb47df4de96940e51256432af`.

Offline verification reconstructed all 688 saved continuation branches (2,752
embedded generation call records), validating exact planned cell identities,
slot substitutions, immutable initial peers, attack bytes, corresponding seeds,
display orders, prompt messages, recorded checkpoint/template identities, decoding
parameters, parsed packets and terminal outcomes. All saved Q+/Q-/delta values
recomputed exactly. No generation or teacher-forced scoring was executed. This is
payload reconstruction, not an independent full dispatch-journal audit, tokenizer
recount or physical weight reload. Forty final outputs were abstentions and 648
parsed successfully; abstentions count as failures.

| Saved stage | Cells | Tasks | Delta distribution |
| --- | ---: | ---: | --- |
| Primary controlled | 132/132 | 22 | 125 zero, 3 at +0.5, 3 at +1, 1 at -1 |
| Reversed order | 36/36 | 6 | 35 zero, 1 at +1 |
| Retained natural calibration | 4/5 | 2 | 1 zero, 2 at +1, 1 at -1 |

Primary positive-packet branches succeeded in 112/264 continuations versus
105/264 negative-packet branches. Within the 264 matched seed comparisons,
150 were both wrong, 103 both correct, 9 positive-only correct and 2 negative-only
correct. Mean cell delta is 0.026515; these correlated continuations are not 264
independent task observations. Seven nonzero cells occupy six tasks; 38/44 task /
condition rows have identical delta across all three slots, six rows vary. Three
primary cells disagree between their two replicate differences. Clean rows have
one nonzero cell (+1); early rows contain the other six. These are controlled
packet intervention results, not natural credit or learned accuracy improvements.

Reversed order changes delta in 3/36 matched cells and changes the best-slot tie
set in 2/12 matched rows, with one strict pairwise slot-rank reversal. No control
order was selected post hoc. Natural calibration has no exact row/actor overlap
with supported controlled cells, so estimator agreement cannot be computed.
Saved calibration values: ARC MCAS_2004_8_8 early agent0=-1, agent1=0;
LogiQA train-0903 clean agent0=+1, agent2=+1 (agents zero-based).
The fifth cell remains missing: ARC MCAS_2004_8_8 early agent2.

This evidence is sparse and incomplete. No likelihood scoring, responsibility
assignment contrast, optimizer update, trained evaluation or scientific efficacy
claim follows from this audit. Up to 16 calls after the unsafe snapshot remain
unaccounted for; rerunning them is not authorized under the original 80-call
calibration cap. No recovery flag, source revision, budget or historical run was
changed. Complete-evidence and explicit training-review gates remain closed.

Reproducible local audit (ignored, no raw text in these summaries):
`results_import/controlled-replay-forensic-audit/audit.py`, `summary.json`,
`cells.json`. Executed with `PYTHONPATH=src python
results_import/controlled-replay-forensic-audit/audit.py`; all assertions passed.
These are evidence checks, not new CPU/mock or GPU experiment results.


## 2026-09-30 — post-forensic continuation review

Recommendation: close `qwen3-controlled-specialization-001` as an incomplete
feasibility study with retained descriptive replay evidence, rather than spend
additional compute recovering its final calibration cell. This is a recommendation
pending the user's decision, not a completed-run marker or a methodological amendment.
The archive and all historical artifacts remain unchanged.

Reasons: primary effects are zero in 125/132 cells, nonzero effects occupy six
of 22 supported tasks, order changes three of 36 matched estimates, and retained
natural calibration has no matched controlled cells. The unsafe latest snapshot
also leaves up to 16 post-snapshot calls unaccounted for. Completing calibration
alone would not resolve sparse credit, packet-quality concerns, or establish
learning benefit. These observations support stopping expenditure, not a claim
that the prespecified assignment screen has formally failed.

The practical assignment gate is **not evaluated**: frozen answer NLL and
responsibility matrices are absent. The global column-balance penalty couples
rows, so six tasks with within-row credit variation does not by itself prove that
fewer than eight tasks would meet the L1 threshold. Do not substitute invented
NLL, per-row softmaxes, or mock weights for missing scoring evidence.

No further Colab command is authorized by this review. Recovering the existing
study requires retained evidence that resolves unknown dispatches, or a separately
reviewed amendment identifying the one missing calibration cell, worst-case
consumed calls, any additional reservation, handling of duplicate requests, and
source/provenance treatment. It must preserve the original run as incomplete and
cannot silently set recovery_safe=true, reset the 80-call cap, waive complete
controls, change thresholds, or authorize training. A new scientific study also
requires its own explicit design and budget; none is proposed for automatic launch.

Review used the audited saved payload summaries and the actual assignment solver.
No model execution, scoring forward, optimizer update, new experiment, commit or
push occurred. Existing completed studies and manuscript placeholders are unchanged.


## 2026-09-30 — controlled specialization closed as incomplete

The user accepted the preceding closure recommendation with “proceed”.
`qwen3-controlled-specialization-001` is administratively **closed — incomplete**;
no further execution is scheduled or authorized. This disposition supersedes the
pending-decision wording above, without declaring scientific completion or a
failed assignment-contrast test.

Retained evidence: 75 acquisition calls, 132/132 primary replay cells, 36/36
order-control cells and 4/5 natural calibration cells. The saved inventory contains
2,827 committed calls; up to 16 subsequent calls remain unaccounted for. The missing
cell is arc_challenge:MCAS_2004_8_8 / early / agent2 (zero-based).
The forensic archive remains bound to SHA256
`2ad3152c12d7215a421e35e68325cb98cd541c36d769ede3a6da7b4b9c6d736b`.

Assignment contrast remains unevaluated; scoring, training and trained development
evaluation were not executed in this child. Sparse controlled replay effects are
descriptive evidence, not demonstrated PACT efficacy. The latest snapshot retains
recovery_safe=false. No COMPLETE marker, missing cell, likelihood, assignment,
checkpoint or outcome has been manufactured. Existing archives, source/plan hashes,
budgets and completed historical studies are preserved. No new study or recovery
amendment is authorized by this administrative closure.


## 2026-09-30 — consolidated project review

Created [the September 30 project audit](audits/PACT_PROJECT_AUDIT_2026-09-30.md),
covering historical diagnostics, preparation, completed controlled receiver training
and evaluation, GPQA support, and both stopped specialization studies. Reconciled
13,765 recorded generation calls plus up to 16 unresolved subsequent calls, and
147 optimizer updates across distinct preparation/task-SFT/receiver-SFT recipes.
No specialization training or full PACT efficacy is claimed. The controlled child
remains closed incomplete. Report links and aggregate arithmetic passed; no model
execution, regression-suite rerun, commit or push occurred for this consolidation.

## 2026-10-02 — pact-heterogeneous-complementarity-001 implemented, not executed

New `heterogeneous_natural_support_v1` diagnostic implements QLM, QQQ, LLL, MMM
using fresh frozen official Instruct models and common unadapted Qwen3 readout.
Exact original 80 validation-pilot tasks stay development-exposed. Recovered their
original input/label/manifest hashes from the pinned raw ZIP; no outcome filtering.
Plan pins immutable model commits, model-native templates/tokenization, shared
packet bindings, balanced family display, clean synchronous revision and budgets.

Hard ceiling: 720 private + 960 revision + 640 synthesis + 80 task-only = 2,400
attempts / 476,160 reserved output tokens. Optional two-task smoke is 60 included
requests. All tasks communicate regardless of measured support. Zero training,
scoring forwards, attacks, donors, private replay, GPQA or final-test use.

CPU evidence: final 17-test heterogeneous suite passed, including all 2,400 mock
requests and export/reconstruction; 20 targeted regressions passed. Full-suite
231-test invocation had 215 passes/14 skips/two environment-specific GPQA errors,
then both affected tests passed with temporary files outside the /tmp Git marker.
These are software fixtures, not new research outcomes. All new GPU behavior is
unverified. Exact Colab steps: [heterogeneity runbook](heterogeneity_colab.md).
No run is scheduled automatically and no model result is claimed. Earlier study
closures, safety flags, precision history and manuscript placeholders are unchanged.


## 2026-10-05 — Heterogeneous diagnostic completed; imported GPU evidence

Imported `pact-heterogeneous-complementarity-001` bundles with suffix
`1791189410949196090`. PRIVATE SHA256:
`57cde0e55b4acf8443582b06205778a12f4b0214d5007932e23f1f0b102f89d4`;
SANITIZED SHA256:
`c96c04aa1303dec275f9f9db534786727ec75300d02da4fe71779a5c29b887d7`.
Both outer hashes matched. The existing offline audit returned passed/complete;
private records regenerated the saved summary exactly. The sanitized archive
passed read_review checksum validation and its summary equals the reconstruction.
Raw archives and extracted audit remain ignored, outside tracked documentation.

Source: clean commit `874b3b184c6cdcde6c27368621d7747fd6e01467`.
Plan: `b972e06e3b8e69f8e53053d238b7fa7f04c1ddb331654b7555262021d47a506f`.
Returned transition receipt records the original zero-call plan and the source
fix, with scientific plan unchanged; it is provenance evidence, not a separate
local audit of the old Drive snapshot. Recorded GPU: NVIDIA A100-SXM4-80GB.

Completed 80/80 development-exposed tasks, 2,400 attempted/committed calls,
476,160 reserved output tokens, zero unresolved calls and zero context overflows.
Recovery-safe state is true. Actual output tokens: 100,395; input tokens: 926,451.
Optimizer updates and teacher-forced forwards: zero. GPU execution is now evidenced
for this returned run; other runtimes remain unverified. Completion includes
abstentions and invalid answers, which remain failures rather than missing calls.

| Team | Initial correct coverage | Valid correct/wrong mixed tasks | Vote correct | Initial synthesis correct | Post-exchange readout correct |
|---|---:|---:|---:|---:|---:|
| QQQ | 45/80 | 2/80 | 44/80 | 46/80 | 45/80 |
| LLL | 49/80 | 14/80 | 39/80 | 42/80 | 44/80 |
| MMM | 34/80 | 7/80 | 32/80 | 32/80 | 31/80 |
| QLM | 63/80 | 47/80 | 36/80 | 43/80 | 40/80 |

Common task-only readout: 41/80. QLM individual accuracies: Q=44/80,
L=37/80, M=31/80. Initial N0 distribution (0,1,2,3 correct):
[17,28,21,14]. QLM coverage exceeds its best observed member by 19 tasks,
but post-exchange readout solves fewer tasks than initial synthesis (40 vs 43).
Paired synthesis-to-debate outcomes: 3 gains, 6 losses, 37 both correct,
34 both incorrect. Difference -3.75 percentage points; stored paired stratified
1,000-draw task-bootstrap interval [-11.25,+3.75] percentage points.
These are 80 sampling units, not 2,400 independent observations.

QLM hold=61/67 eligible actor opportunities; repair=12/69. Team erasure=3/63
initially covered tasks. Utilization=39/63, construction=1/17; readout loss
occurs on 22/80 tasks. Correct coverage and valid mixed support are distinct:
N0=1 or 2 includes invalid/abstaining peers and is not automatically valid
correct/wrong support. Invalid and abstention rates remain part of interpretation.

Interpretation: heterogeneous actors provide more natural complementary correct
answers on this exposed cohort, but the tested communication/readout pipeline
does not turn that coverage advantage into higher final accuracy. This is a
clean inference diagnostic, not trained PACT or demonstrated PACT efficacy.
One seed schedule, small exposed sample, differing family strengths/tokenizers,
and observed-best selection limit generalization. No next experiment is
implicitly authorized. Historical closures and manuscript placeholders unchanged.


## 2026-10-06 — Consolidated audit report

Created [the October 6 project audit](audits/PACT_PROJECT_AUDIT_2026-10-06.md),
extending the September 30 overview with the completed heterogeneous GPU evidence.
Cumulative recorded generations: 16,165, plus the unchanged up-to-16 unknown
controlled-child calls. Executed optimizer updates remain 147 across separate
recipes; no specialization training occurred. Reviewed current ledger/status and
reconstructed heterogeneous summary, checked report links and aggregate arithmetic.
Historical audits were carried forward, not represented as freshly re-executed.
No model run, full regression rerun, commit or push was performed for this report.

## 2026-10-06 — Benchmark breadth implementation, not experimental results

Added six official-source/native-evaluator adapters and separately invoked
heterogeneous Phase A/B development runners under new `pact-breadth-*-001` IDs.
No new benchmark generation or optimizer update occurred. Historical cumulative
generation/update counts above are unchanged; source inspection and CPU fixtures
are not scientific outcomes. No confirmation/reserve/final-test generation occurred.

MMLU/MuSR/MATH source normalization and grouping were checked on official public
files; MBPP's canonical official 378-record expanded-test asset was verified.
Pinned Math-Verify ran invented equivalence cases. GPQA new32 allocation is tested
with an invented parent fixture; real authorized source/parent verification is a
Colab prerequisite. LiveBench 2026-06-25 is unavailable in the checked public
inventories and is explicitly blocked. Real OS-isolated EvalPlus execution and all
new GPU paths remain unverified; pending scoring exports cannot be called failures.

Final focused validation: 25 tests, 23 passed/two isolated-runtime skips. Full
CPU/mock regression rerun: 265 tests, 248 passed/17 skips, no failures/errors;
initial errors and their environment/source-stability causes are preserved in
[implementation status](implementation_status.md). Latest small scorer/report
changes passed the focused rerun. Exact pins, exposure policy, budgets, commands,
runtime prerequisites and private/sanitized return artifacts are documented in
[benchmark methodology](benchmark_breadth_methodology.md) and its linked runbook.
Implementation does not authorize an automatic portfolio run or imply efficacy.

## 2026-10-06 — MMLU-Pro included smoke return audited

Run `pact-breadth-mmlu-pro-001`, export timestamp `1791253131407744749`.
Both submitted archive SHA256 values matched:

- PRIVATE: `f0900fd38127b12686b4b4eff80fe9158aa53cd231fb234266f09bd560c94cac`
- SANITIZED: `5a9ab08d71cdc4e40412180eb8a5b4f3cb10bfdb03a0a6144b019efc162b0f87`

Pinned clean source `7185b0c4bda278edabfbe45865d922844bf206d6`, source hash
`9411820ecbc65b069665cd4ef4999b746be04f8cef814160b6d512dae1eee43f`;
plan `516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9`.
Recorded GPU: NVIDIA A100-SXM4-80GB. Q/L/M identities retain BF16, SDPA and no
adapters. R access was preflighted; no R generation was exercised by this smoke.

The real offline `breadth audit` CLI passed outside Git. Internal archive checksums
passed, sanitized summary equaled private/reconstructed summary, and all 18 scores
agreed exactly with independent strict-MCQ rescoring. The observed calls are
exactly the two planned smoke IDs, six per family, all private Phase A. All 18
parsed successfully and stopped at EOS; zero unresolved attempts; recovery_safe=true.
Sanitized inventory contains only summary/report/handoff, with no selected question,
raw completion or rendered prompt found in the public summary/report.

| Team | Private coverage, tasks | N0 counts (0/1/2/3 correct) | Mixed support | Vote correct |
|---|---:|---|---:|---:|
| QQQ | 0/2 | 2/0/0/0 | 0/2 | 0/2 |
| LLL | 1/2 | 1/1/0/0 | 1/2 | 0/2 |
| MMM | 0/2 | 2/0/0/0 | 0/2 | 0/2 |
| QLM | 1/2 | 1/1/0/0 | 1/2 | 0/2 |

Across all nine-packet banks: Q 0/6, L 1/6, M 0/6 correct. QLM's one correct
candidate is the same saved Llama draw used by LLL, not independent evidence.
All teams have zero observed gain over their best member. The two task strata are
`other` and `philosophy`; these are smoke observations, not a representative
14-category estimate, evidence of model ranking or a complementarity conclusion.
No communication/utilization/repair outcome was measured.

Accounting: 18 attempted/committed/scored calls, 9,216 reserved output tokens,
4,368 input tokens and 765 actual output tokens; zero optimizer updates. Full Phase A
is correctly partial (18/1,260 calls); Phase B is not executed (0/2,940). Remaining
planned A work is 1,242 calls / 635,904 reserved output tokens, reusing these 18 calls.
This return adds 18 to the prior ledger's 16,165 recorded generations: 16,183 total,
plus the unchanged up-to-16 unknown controlled-child calls; optimizer updates stay
147. Historical entries were not re-audited for this increment.

Only this observed MMLU private-smoke GPU path is now verified. Full A/B, common
readout and other benchmark GPU behavior remain unverified. No local model calls,
new experiment, commit or push was performed. No outcome automatically authorizes
continuation or methodological change.

## 2026-10-06 — Complete MMLU-Pro Phase A return audited

Run `pact-breadth-mmlu-pro-001`, export `1791264819488214146`. Uploaded archives
matched the submitted SHA256 values and their internal inventories/checksums:

- PRIVATE: `199ebcffd076671ddb20d026614d1c78296d1fca763f5ad90952a4ce594fcfb0`
- SANITIZED: `ba45c8f71363126dbc72ec8bbf560bd4bcca72672a484628edf7aee64241ad10`

The plan is unchanged from the smoke:
`516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9`, clean source
`7185b0c4bda278edabfbe45865d922844bf206d6`, source hash
`9411820ecbc65b069665cd4ef4999b746be04f8cef814160b6d512dae1eee43f`.
Recorded GPU is A100-SXM4-80GB; runtime fingerprint matches the smoke. The real
offline audit CLI passed outside Git. All 1,260 scores independently reproduced
under the frozen strict MCQ contract. All 72 old smoke intent/call/dependency/score
records are exactly preserved, and the entire frozen plan equals the earlier plan.

Phase A is complete: 140 tasks, ten in each of 14 categories, nine private calls
per task (420/family), 1,260 attempted/committed/scored, zero unresolved attempts,
recovery_safe=true. No locked-cohort or Phase B generation is present. All actual
responses, including invalid/abstaining/length-limited responses, retain the intended
denominator; there are no omitted tasks. Parser counts: ok 1,106, abstention 81,
invalid_answer 9, malformed 43, length 21. Stop reasons: EOS 1,239 and length 21.

| Team | Coverage | Best member | Gain over best member | Valid mixed support | Majority vote | N0 (0/1/2/3) |
|---|---:|---:|---:|---:|---:|---|
| QQQ | 40/140 (28.57%) | 35/140 | 5/140 | 7/140 | 35/140 (25.00%) | 100/6/5/29 |
| LLL | 46/140 (32.86%) | 37/140 | 9/140 | 14/140 | 35/140 (25.00%) | 94/13/5/28 |
| MMM | 38/140 (27.14%) | 30/140 | 8/140 | 13/140 | 31/140 (22.14%) | 102/9/8/21 |
| QLM | 61/140 (43.57%) | 36/140 | 25/140 | 42/140 | 32/140 (22.86%) | 79/31/19/11 |

QLM member correctness: Q 35/140, L 36/140, M 31/140. Across all three draws per
family: Q 103/420, L 107/420, M 88/420; these 420 responses are not independent
sampling units. Primary equal-category macro coverage equals micro coverage here
because each category has ten fully observed tasks. Paired group bootstrap within
category (140 groups, 1,000 draws) gives QLM coverage differences and percentile
intervals: QQQ +15.00 percentage points [8.57,22.14], LLL +10.71 [4.29,17.14], MMM
+16.43 [10.00,22.86]. These are descriptive development-cohort comparisons under
one seed schedule, not an official leaderboard or a corrected multiple-testing claim.

The mixed team has greater observed private correct-answer availability than each
homogeneous team. Its majority-vote outcome does not establish a final-answer
advantage. Synthesis, revisions, utilization, hold/repair and readout loss remain
unmeasured: Phase B is not executed (0/2,940). Zero-support categories remain in
the cohort; no task/model/seed substitution or positive-support gate is introduced.

Accounting: 645,120 reserved output tokens, 430,029 input tokens, 111,058 actual
output tokens, zero optimizer updates. This adds only the 1,242 new calls to the
previous cumulative count: 17,425 recorded generations plus the unchanged up-to-16
unknown controlled-child calls; historical optimizer updates remain 147.

Sanitized summary equals private and reconstructed summaries. Its only payloads
are summary/report/handoff; all selected questions, raw completions and rendered
prompts were checked absent from its summary/report. Raw evidence remains private.
No local generation, commit, push or methodological change occurred. The observed
MMLU Phase A GPU path is verified; Phase B and other benchmark GPU paths remain
unverified. Any continuation is a separate explicit invocation under the same plan.

## 2026-10-06 — MMLU-Pro Phase B completed and audited

Run `pact-breadth-mmlu-pro-001`, export `1791270113690429538`. Both uploaded
archives match their submitted SHA256 values and internal checksum inventories:

- PRIVATE: `7e15746dbc7832dda3c5698e86737af66d806f25954ce1fc5910844e5b521bad`
- SANITIZED: `c6cf9b5a087ef4610a986e823d3d5dde6bb1353c66d40994bacdf1fb92f4b2e6`

The plan remains `516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9`
at clean source `7185b0c4bda278edabfbe45865d922844bf206d6` (source hash
`9411820ecbc65b069665cd4ef4999b746be04f8cef814160b6d512dae1eee43f`). Recorded GPU:
A100-SXM4-80GB. All Q/L/M/R identities retain BF16, SDPA and absent adapters.
The actual offline audit CLI passed outside Git, checking native identities,
request construction/dependencies, frozen initial-peer delivery, accounting and
summary reconstruction. Independent strict-MCQ rescoring reproduced all 4,200
outcomes, including the final-answer parsing mode for readout. All 5,040 earlier
Phase A intent/call/dependency/score records and the entire plan are unchanged.

Both phases are complete on all 140 characterization tasks, ten/category:
1,260 private calls; 1,680 revisions (560/family); 560 private syntheses; 560 revised
readouts; 140 common task-only calls. Total 4,200 attempted/committed/scored,
zero unresolved attempts, recovery_safe=true. No locked cohort generated.

| Team | Initial coverage | Private vote | Private synthesis | Revised vote | Post-exchange readout |
|---|---:|---:|---:|---:|---:|
| QQQ | 40/140 | 35/140 | 42/140 | 39/140 | 43/140 |
| LLL | 46/140 | 35/140 | 42/140 | 37/140 | 38/140 |
| MMM | 38/140 | 31/140 | 32/140 | 30/140 | 32/140 |
| QLM | 61/140 | 32/140 | 40/140 | 39/140 | 43/140 |

The common task-only readout is 35/140; it is one shared 140-call control, not
four independently generated controls. Equal-category macro and micro terminal
accuracy coincide on this fully observed balanced cohort. Private correctness
availability remains higher for QLM, but its post-exchange accuracy ties QQQ at
30.71%, and its private synthesis is below QQQ/LLL (40 versus 42 correct).

QLM synthesis-to-post-exchange paired outcomes: 38 correct in both, five repairs
of final outcomes, two regressions, 95 incorrect in both. Net +3/140 = +2.14
percentage points; category-stratified paired group-bootstrap percentile interval
[-1.43,+5.71] points includes zero. These final-outcome transitions are distinct
from the recipient-level repair opportunities below. QLM post-exchange minus QQQ
is 0.00 points [-5.71,+5.71]; versus LLL +3.57 [-2.86,+10.71]; versus MMM +7.86
[1.43,+14.29]. Intervals use the frozen 1,000-draw procedure and 140 task/group
sampling units, one seed schedule, without a multiple-comparison correction.
This does not establish a general heterogeneous final-answer advantage.

QLM availability and receiver accounting:

- Initial coverage 61, revised coverage 59: 11/61 initially covered tasks lose all
  correct packets; 9/79 initially uncovered tasks gain a correct revised packet.
- Hold succeeds on 44/55 eligible receiver opportunities; repair on 10/63.
  These are correlated receiver opportunities, not independent task samples.
- Post-exchange success occurs on 38/61 initially covered tasks and 5/79 initially
  uncovered tasks: 38 + 5 = 43. The latter is construction relative to the initial
  bank, not necessarily construction by the final readout itself.
- Private synthesis loses 24 initially covered tasks and constructs three successes
  on initially uncovered tasks: 61 - 24 + 3 = 40.
- Of 59 revised-covered tasks, 16 end in a wrong readout; no correct final readout
  occurs without a correct revised candidate: 59 - 16 + 0 = 43.

Thus initial coverage minus final accuracy (61-43) is a net difference, not an
ignored-answer count or a causal explanation. Honest-error hold/repair and clean
exchange outcomes do not measure attack robustness or trained PACT efficacy.

Phase B parser counts: ok 2,595, abstention 309, invalid_answer 6, malformed 23,
length 7. These 345 non-ok responses remain scored failures, not missing tasks.
Combined parser counts are ok 3,701, abstention 390, invalid_answer 15, malformed
66, length 28; stop reasons EOS 4,172 / length 28. Infrastructure missingness is
zero. Combined accounting: 1,585,920 reserved output tokens, 2,223,136 input tokens,
228,833 actual output tokens, zero optimizer updates. Incremental B consumption:
940,800 reserved, 1,793,107 input and 117,775 actual output tokens.

Sanitized summary/report equal the private copies and reconstructed results. The
sanitized inventory contains summary/report/handoff only; selected questions,
nonempty raw continuations and rendered prompts were checked absent. Raw content
remains private and ignored by Git. Only 2,940 new calls are added to the ledger:
20,365 cumulative recorded generations plus the unchanged up-to-16 unknown calls;
historical optimizer updates remain 147. Historical totals were carried forward,
not re-audited in this import.

This verifies the observed MMLU A/B GPU configuration, including common readout.
Other benchmark GPU paths remain unverified. No local model generation, source
change, commit, push, final-test run or automatic next experiment occurred.

## 2026-10-06 — MuSR included smoke return audited

Run `pact-breadth-musr-001`, export `1791271351392273370`. Both uploaded SHA256
values and internal archive checksum inventories matched:

- PRIVATE: `7919a6e86f2322a1372647b5334dd2ff90c998362cf07db660dd69e2b5c59d09`
- SANITIZED: `2720a1cc9ac965e6818f261c713fa3d54a9e0ed6d602a54fe822d4b8d985f9e8`

Plan `a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae`;
clean source `7185b0c4bda278edabfbe45865d922844bf206d6`, source hash
`9411820ecbc65b069665cd4ef4999b746be04f8cef814160b6d512dae1eee43f`.
Recorded GPU: A100-SXM4-80GB. Q/L/M identities retain BF16, SDPA and absent
adapters. The real offline audit CLI passed outside Git and all 18 strict MCQ
scores independently reproduced. There are six calls/family on exactly the two
planned smoke IDs; all responses parse ok and stop at EOS, zero unresolved
attempts, recovery_safe=true. No Phase B or locked-cohort call is present.

The plan's prior-exposure index exactly equals an independently reconstructed index
from the audited MMLU A/B archive `1791270113690429538`. Selected MuSR fingerprints
do not intersect its blocked fingerprints. Actual selected quotas are thirty per
domain. All source siblings inherit one partition; 756 source rows form 564 eligible
groups, zero excluded groups, and 90/90/384 characterization/confirmation/reserve
representatives. These lexical checks do not establish semantic decontamination.

| Team | Coverage | Majority vote correct | Valid mixed support | N0 (0/1/2/3) |
|---|---:|---:|---:|---|
| QQQ | 2/2 | 2/2 | 0/2 | 0/0/0/2 |
| LLL | 1/2 | 1/2 | 1/2 | 1/0/1/0 |
| MMM | 2/2 | 2/2 | 0/2 | 0/0/0/2 |
| QLM | 2/2 | 2/2 | 1/2 | 0/0/1/1 |

Across all draws: Q 6/6, L 2/6, M 6/6 correct. Every team's observed coverage gain
over its best member is zero. Smoke strata are murder_mysteries and object_placements;
team_allocation has no returned generation evidence yet. Two tasks are insufficient
for a domain-balanced or population complementarity claim. No communication,
utilization, hold/repair or readout outcome was measured.

Accounting: 18 attempted/committed/scored calls, 9,216 reserved output tokens,
24,381 input tokens, 1,132 actual output tokens, zero optimizer updates. Phase A
is correctly partial at 18/810; B is not executed at 0/1,890. Remaining A work is
792 calls / 405,504 reserved output tokens, retaining the smoke calls. This adds
18 to the previous cumulative ledger count: 20,383 recorded generations plus the
unchanged up-to-16 unknown controlled-child calls; historical updates remain 147.

Sanitized summary/report exactly equal the private copies; only summary/report/
handoff are present. All selected questions/narratives, generated continuations and
rendered prompts were checked absent from the sanitized summary/report. Only this
observed MuSR private-smoke GPU path is now verified. No local model generation,
code change, commit, push, automatic continuation or methodological change occurred.

## 2026-10-06 — MuSR full Phase A audited

Run `pact-breadth-musr-001`, export `1791274491198207091`. Uploaded hashes
and internal archive inventories verified:

- PRIVATE: `65da166dc076d4e33c70d37580d1b70d6cf2ff97beef4bfd6c68e3dffa979e7e`
- SANITIZED: `518f3a1d2d1daf64d35fc6a1748f3ed49c210864a203ec3003a171c05f777eb4`

The frozen plan exactly matches the smoke return:
`a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae`.
All 72 smoke call/intent/dependency/score artifacts are unchanged. This preserves
the previously audited source/model pins, selection, group partitions and MMLU
exposure index. Q/L/M identity records retain BF16, SDPA and no adapters.
The real offline audit CLI passed outside Git. All 810 strict MCQ scores were
independently reproduced; no inference was executed locally.

All 90 characterization tasks have their nine private responses, 270 per family.
Phase A is complete; Phase B remains not executed (0/1,890). There are zero
unresolved calls and recovery_safe=true. All stops are EOS. Parser outcomes:
759 ok, 8 malformed, 10 invalid_answer and 33 abstention. These 51 non-ok responses
remain failures, not dropped observations or missing calls.

| Team | Correct coverage | Majority vote correct | Valid mixed support | Gain over best member | N0 (0/1/2/3) |
|---|---:|---:|---:|---:|---|
| QQQ | 50/90 | 48/90 | 6/90 | 2/90 | 40/2/4/44 |
| LLL | 53/90 | 45/90 | 15/90 | 8/90 | 37/10/12/31 |
| MMM | 41/90 | 38/90 | 9/90 | 4/90 | 49/7/7/27 |
| QLM | 62/90 | 44/90 | 38/90 | 17/90 | 28/18/25/19 |

Across private draws, Q is correct on 142/270, L on 127/270 and M on 102/270.
Tasks with wrong-answer diversity number 0, 9, 4 and 5 respectively; wrong-answer
diversity is not correct coverage. Mixed support requires valid correct/wrong
responses, so it need not equal the sum of the N0=1 and N0=2 counts.

Domain results (coverage / vote, each denominator 30):

| Domain | QQQ | LLL | MMM | QLM |
|---|---|---|---|---|
| murder_mysteries | 21 / 19 | 20 / 20 | 18 / 16 | 24 / 19 |
| object_placements | 14 / 14 | 15 / 10 | 13 / 13 | 18 / 12 |
| team_allocation | 15 / 15 | 18 / 15 | 10 / 9 | 20 / 13 |

QLM coverage exceeds QQQ by 13.33 percentage points (reported paired stratified
group-bootstrap interval 6.67 to 21.11), LLL by 10.00 (1.11 to 18.89) and MMM by
23.33 (13.33 to 33.33). The sampling units are the 90 task groups, not 810 calls.
These are balanced development-subset estimates, not official leaderboard results.
QLM's greater available coverage does not produce a majority-vote advantage over
QQQ here. Communication, preservation, utilization and readout remain unmeasured;
this is not evidence of trained PACT efficacy and does not authorize another run.

Accounting: 810 attempted/committed/scored, 414,720 reserved output tokens,
926,715 input tokens, 62,168 actual output tokens and zero optimizer updates.
Only 792 new generations are added beyond the smoke: cumulative recorded
generations 21,175 plus the unchanged up-to-16 unknown controlled-child calls.
Historical optimizer updates remain 147; historical totals were carried forward,
not re-audited.

Sanitized summary/report exactly match the private copies; its inventory contains
only handoff/summary/report. Selected questions/narratives, rendered prompts and
nonempty raw continuations were checked absent from the public summary/report.
Private artifacts remain outside tracked outputs. Only the observed MuSR Phase A
GPU path is now verified. No source change, commit, push, protected-cohort use,
local generation or automatic Phase B execution occurred.

## 2026-10-06 — MuSR complete A/B return audited

Run `pact-breadth-musr-001`, export `1791278710347362192`. Uploaded SHA256
values and internal archive checksum inventories verified:

- PRIVATE: `1eaa5a5a04f4feb2405ae29ff17c90c831886691ea060ee69fe978025f44dd57`
- SANITIZED: `298082b20be17a51e40059a5281eb8f3625cca6bd6f0739b0ff010902a8ca4a6`

Frozen plan `a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae`
exactly equals the audited A return. All 3,240 prior call/intent/dependency/score
records are unchanged. No selection, exposure partition or source migration.
Q/L/M/R identity records retain BF16, SDPA and no adapters. Real offline audit
outside Git passed; all 2,700 strict MCQ scores independently reproduced.
Sanitized summary/report equal private copies; only handoff/summary/report are
present. All selected questions/narratives, rendered prompts and nonempty raw
continuations were checked absent from the sanitized summary/report.

A is complete at 810/810 and B at 1,890/1,890. B contains 360 revisions per Q/L/M
family and 810 common R readouts. All 90 tasks are observed, zero unresolved calls,
recovery_safe=true. All 2,700 stop reasons are EOS. B parser counts are 1,781 ok,
15 malformed, 15 invalid_answer and 79 abstention. Non-ok responses remain failures;
they are not omitted. A's 759 ok / 51 non-ok responses remain unchanged.

| Team | Initial coverage | Private vote | Private synthesis | Revised vote | Post-exchange readout |
|---|---:|---:|---:|---:|---:|
| QQQ | 50/90 | 48/90 | 48/90 | 48/90 | 47/90 |
| LLL | 53/90 | 45/90 | 46/90 | 46/90 | 46/90 |
| MMM | 41/90 | 38/90 | 38/90 | 35/90 | 35/90 |
| QLM | 62/90 | 44/90 | 45/90 | 43/90 | 46/90 |

The shared task-only Qwen3 control is 52/90. It is one control, not four independent
measurements. QLM retains the largest initial coverage, but this does not translate
into superior final accuracy in this cohort.

| Team | Erasure | New availability | Utilization | Construction | Hold | Repair | Private / revised readout loss events |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 2/50 | 0/40 | 47/50 | 0/40 | 8/10 | 1/8 | 2 / 1 |
| LLL | 4/53 | 3/37 | 44/53 | 2/37 | 16/22 | 6/23 | 7 / 6 |
| MMM | 2/41 | 1/49 | 33/41 | 2/49 | 12/15 | 1/12 | 4 / 7 |
| QLM | 5/62 | 0/28 | 46/62 | 0/28 | 50/58 | 6/55 | 17 / 11 |

Readout losses are actual event counts out of 90 tasks, not coverage-minus-accuracy
estimates. Hold/repair use the report's eligible receiver opportunities. Zero
construction/new-availability estimates do not establish population zero rates.

N0-to-N1 matrices (rows initial correct count 0..3; columns revised count 0..3):

- QQQ: [[40,0,0,0],[2,0,0,0],[0,0,3,1],[0,0,0,44]]
- LLL: [[34,3,0,0],[4,5,1,0],[0,1,6,5],[0,0,1,30]]
- MMM: [[48,1,0,0],[2,4,1,0],[0,2,4,1],[0,1,3,23]]
- QLM: [[28,0,0,0],[5,12,1,0],[0,2,18,5],[0,0,2,17]]

For QLM, coverage falls from 62 to 57 tasks: five erasures and no newly covered
task. Its final readout succeeds on 46 of the 62 initially covered tasks; 11
tasks retain a correct revised packet but receive an incorrect final readout.

Paired private-synthesis to post-exchange outcomes:

| Team | Incorrect to correct | Correct to incorrect | Net tasks | Difference (pp), reported bootstrap interval |
|---|---:|---:|---:|---|
| QQQ | 0 | 1 | -1 | -1.11 [-3.33, 0.00] |
| LLL | 3 | 3 | 0 | 0.00 [-5.56, 4.44] |
| MMM | 1 | 4 | -3 | -3.33 [-8.89, 1.11] |
| QLM | 2 | 1 | +1 | +1.11 [-2.22, 5.56] |

Sampling units are the 90 task groups, bootstrapped within the three strata;
2,700 calls are not independent task observations. QLM's interval includes zero.
This bounded development study does not establish a communication benefit or
trained PACT efficacy. Historical MMLU/ARC/LogiQA results remain descriptive,
not pooled independent evidence.

Domain private-synthesis / post-exchange counts (each denominator 30):

| Domain | QQQ | LLL | MMM | QLM | Task-only |
|---|---|---|---|---|---:|
| murder_mysteries | 19 / 18 | 19 / 19 | 15 / 14 | 18 / 18 | 20 |
| object_placements | 14 / 14 | 11 / 11 | 14 / 11 | 12 / 13 | 15 |
| team_allocation | 15 / 15 | 16 / 16 | 9 / 10 | 15 / 15 | 17 |

Accounting: 2,700 attempted/committed/scored, 1,019,520 reserved output tokens,
3,510,679 input tokens, 149,131 actual output tokens, zero optimizer updates.
Incremental B: 1,890 calls, 604,800 reserved, 2,583,964 input, 86,963 actual output
tokens. Adding only B yields 23,065 cumulative recorded generations plus unchanged
up-to-16 unknown controlled-child calls. Historical optimizer updates remain 147;
historical totals were carried forward, not re-audited.

The observed MuSR A/B GPU path, including the common readout, is now verified.
No local model generation, code/methodology change, commit, push, locked-cohort
execution or automatic next experiment occurred.

## 2026-10-07 — MATH-500 included smoke audited

Run `pact-breadth-math-500-001`, export `1791353073408058583`.
Both uploaded SHA256 values and internal inventories verified:

- PRIVATE: `12d4003f3183e24bfd015d6c4dcab40c86eb07f0f76ff4fcbf09a116a6a2e477`
- SANITIZED: `207aee4be2e9790b72f17acdeda3c6764d2ddccc25c8008d09adc51a52d2dcab`

Frozen plan `e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6`;
clean source `7185b0c4bda278edabfbe45865d922844bf206d6`, source hash
`9411820ecbc65b069665cd4ef4999b746be04f8cef814160b6d512dae1eee43f`.
Real offline report reconstruction passed outside Git. All 18 score outcomes and
parse records independently reproduced using the existing local pinned math
environment. Elapsed time and evaluator environment metadata were excluded from
cross-host equality; scorer package versions agree. Colab records Python 3.13.15,
Math-Verify 0.9.0, latex2sympy2_extended 1.11.0, SymPy 1.14.0, mpmath 1.3.0,
antlr4-python3-runtime 4.13.2. Readiness records ready=true/gold_parse_checked with
the frozen evaluator identity. The replacement virtualenv setup succeeded; it
does not change scorer policy or the scientific plan.

Eighteen committed/scored private calls, six per family on two tasks; zero
unresolved, recovery_safe=true. Twelve parse ok, five malformed, one length-limited.
Seventeen EOS stops and one length stop. All six contract failures remain failures.
Q is correct on 6/6, L on 1/6 and M on 1/6 draws.

| Team | Coverage | Valid mixed support | N0 (0/1/2/3) | Gain over best member |
|---|---:|---:|---|---:|
| QQQ | 2/2 | 0/2 | 0/0/0/2 | 0/2 |
| LLL | 1/2 | 0/2 | 1/1/0/0 | 0/2 |
| MMM | 1/2 | 1/2 | 1/1/0/0 | 0/2 |
| QLM | 2/2 | 2/2 | 0/2/0/0 | 0/2 |

QLM's selected Q member supplies both correct answers. This smoke does not show
coverage gain over its best member. Two tasks are insufficient for broader
complementarity claims. Math voting is disabled; no communication/readout outcome
has been measured.

The prior exposure index exactly equals the reconstruction from completed
MMLU-Pro and MuSR plans. Selected math fingerprints have no overlap with its
blocked fingerprints. All subject/level quotas match, including explicitly zero
quotas. Source has 500 rows, 495 eligible groups; partitions contain 100
characterization, 100 confirmation and 295 reserve representatives. These lexical
checks do not establish semantic decontamination. Q/L/M retain BF16/SDPA/no adapters.

Accounting: 18 attempts/commits/scores, 18,432 reserved output tokens, 2,247 input,
6,593 actual output, zero optimizer updates. A is partial 18/900; B not executed
0/2,100. Remaining A: 882 calls / 903,168 reserved output tokens. Cumulative
recorded generations become 23,083 plus unchanged up-to-16 unknown historical
controlled-child calls; historical optimizer updates remain 147. Prior totals
were carried forward, not re-audited.

Private/sanitized summaries and reports match. Sanitized inventory contains only
handoff/summary/report; selected questions, prompts and nonempty continuations
were checked absent. Only the observed math private-smoke GPU/scoring path is
verified. Full A/B remain unverified. No local model generation, methodology
change, commit, push or automatic continuation occurred.

## 2026-10-07 — MATH-500 full Phase A return

Run `pact-breadth-math-500-001`, export `1791368956454486655`.
Both uploaded SHA256 values and internal archive inventories verified:

- PRIVATE: `d7df5c7399357076caf42a1dc9f98dea798c5bbe68ab2c40b638dc05876647b4`
- SANITIZED: `a2c7c88c2af75e6e6b8ed550810a14147a0b0915f4fff0f54365e66264bd5254`

Frozen plan `e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6`
exactly matches the smoke return. All 72 smoke call/intent/dependency/score records
are identical. This retains the previously audited source, scorer, prior-exposure
index and partitions. Q/L/M identities retain BF16, SDPA and no adapters.
The real offline audit CLI reconstructed an identical report outside Git.

Phase A is complete at 900/900 on 100 tasks, 300 calls/family; B remains unexecuted
at 0/2,100. Zero unresolved calls, recovery_safe=true. There are 812 EOS stops and
88 length stops. Parsing: 622 ok, 190 malformed, 88 length-limited. The 278 output
contract failures remain scored failures, not missing observations or exclusions.

| Team | Correct coverage | Best member | Coverage gain | Valid mixed support | N0 (0/1/2/3) |
|---|---:|---:|---:|---:|---|
| QQQ | 84/100 | 77/100 | 7/100 | 15/100 | 16/9/9/66 |
| LLL | 39/100 | 25/100 | 14/100 | 13/100 | 61/26/8/5 |
| MMM | 22/100 | 14/100 | 8/100 | 18/100 | 78/16/4/2 |
| QLM | 74/100 | 73/100 | 1/100 | 56/100 | 26/46/27/1 |

Across all private draws, Q is correct on 225/300, L 57/300, M 30/300.
Within QLM's fixed bindings, Q/L/M are correct on 73/19/11 of 100 respectively.
Thus mixed correct/wrong support does not imply complementary coverage: QLM adds
only one covered task beyond Q. Three Q draws cover ten more tasks than QLM.

QLM minus QQQ coverage is -10 pp (reported paired stratified group-bootstrap
interval [-16,-5]); versus LLL +35 pp [27,43], versus MMM +52 pp [44,60].
These are 100 task-group sampling units, not 900 independent calls. Primary
aggregation is micro across the selected subject/level allocation. Subject counts:
Algebra 25, Intermediate Algebra 19, Prealgebra 16, Precalculus 12, Number Theory
12, Geometry 9, Counting & Probability 7. All quotas, including zero strata, match.

The observed pattern differs descriptively from MMLU/MuSR: heterogeneity here
does not outperform QQQ on initial correct-answer availability. These are bounded
development results under the frozen format and token limits, not an unrestricted
ranking of mathematical capability. Math voting remains disabled. No communication,
hold/repair, utilization or final readout result is available; no claim of trained
PACT efficacy follows and no outcome authorizes an automatic subsequent run.

Accounting: 900 attempted/committed/scored, 921,600 reserved output tokens,
136,899 input tokens, 420,720 actual output tokens, zero optimizer updates.
Only the 882 calls beyond smoke are added to cumulative accounting: 23,965
recorded generations plus unchanged up-to-16 unknown controlled-child calls.
Historical optimizer updates remain 147; prior totals were carried forward,
not re-audited.

Sanitized inventory contains handoff/summary/report only; summary/report exactly
equal private copies. Selected questions, rendered prompts and nonempty raw
continuations were checked absent from sanitized summary/report. No local model
generation, source/methodology change, commit, push or protected-cohort use occurred.

Independent CPU rescoring completed for all 900 records using the existing pinned
local math environment: zero outcome/parse mismatches. Cross-host elapsed-time and
evaluator-environment metadata were excluded from equality, as in the smoke audit.
Per-family parser counts (ok / malformed / length): Q 273/1/26, L 114/133/53,
M 235/56/9. This highlights substantial format failures in L under the fixed
contract. No rescoring changed an imported outcome. The observed full Math A
GPU/scoring path is verified; B remains unverified.

## 2026-10-08 — MATH-500 complete A/B return

Run `pact-breadth-math-500-001`, export `1791412685067931571`.
Both uploaded SHA256 values and internal inventories verified:

- PRIVATE: `0cb8d640bf6b039df046fafdb7d1785fc0ef23dabedea082cd8d42f15c72f748`
- SANITIZED: `b41f2624fd012dbf09282a3b83627803151f87b197b162fb7568efa17d8804d1`

Frozen plan `e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6`
and all 3,600 Phase A call/intent/dependency/score records are unchanged from
the audited A return. Previously audited source/scorer/exposure partitions remain
fixed. Q/L/M/R identities retain BF16, SDPA and absent adapters.
Real offline audit outside Git reconstructs an identical report. Private/sanitized
summary and report match. Sanitized inventory is handoff/summary/report only;
selected questions, rendered prompts and nonempty continuations were checked
absent from those public outputs.

A complete 900/900; B complete 2,100/2,100; all 100 characterization tasks observed,
zero unresolved, recovery_safe=true. All 3,000 records have available scores.
Combined parsers: 2,311 ok, 446 malformed, 243 length-limited. B alone:
1,689 ok, 256 malformed, 155 length-limited. Combined stops: 2,757 EOS, 243 length.
All output contract failures remain failures; no task or response was dropped.

| Team | Initial coverage | Private synthesis | Post-exchange readout | Task-only control |
|---|---:|---:|---:|---:|
| QQQ | 84/100 | 79/100 | 80/100 | 74/100 |
| LLL | 39/100 | 73/100 | 74/100 | 74/100 |
| MMM | 22/100 | 64/100 | 59/100 | 74/100 |
| QLM | 74/100 | 81/100 | 77/100 | 74/100 |

Task-only is one shared Qwen3 control, not four independent measurements.
Math private/revised voting remains disabled. The unadapted readout can solve
tasks absent correct peer answers, so terminal accuracy is not a pure measure of
peer-answer utilization. In particular, high LLL/MMM terminal accuracy relative
to initial coverage includes readout construction.

| Team | Erasure | New availability | Utilization | Construction | Hold | Repair | Private / revised readout loss events |
|---|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 3/84 | 0/16 | 79/84 | 1/16 | 16/22 | 14/21 | 7 / 2 |
| LLL | 2/39 | 17/61 | 37/39 | 37/61 | 9/16 | 7/17 | 2 / 1 |
| MMM | 6/22 | 2/78 | 20/22 | 39/78 | 12/21 | 2/30 | 2 / 2 |
| QLM | 2/74 | 2/26 | 70/74 | 7/26 | 70/74 | 17/63 | 3 / 3 |

Readout losses are actual events out of 100 tasks. Hold/repair denominators are
eligible receiver opportunities, not independent task samples. Construction uses
final correctness with no initially correct actor; new availability instead
requires a correct revised actor packet.

N0-to-N1 matrices, rows initial 0..3, columns revised 0..3:

- QQQ: [[16,0,0,0],[3,1,3,2],[0,0,1,8],[0,0,0,66]]
- LLL: [[44,7,5,5],[2,6,14,4],[0,1,1,6],[0,0,1,4]]
- MMM: [[76,2,0,0],[6,7,3,0],[0,3,1,0],[0,0,0,2]]
- QLM: [[24,2,0,0],[2,25,15,4],[0,3,16,8],[0,0,0,1]]

Paired private-synthesis to post-exchange outcomes:

| Team | Incorrect to correct | Correct to incorrect | Net tasks | Difference pp, reported bootstrap interval |
|---|---:|---:|---:|---|
| QQQ | 4 | 3 | +1 | +1 [-3,+6] |
| LLL | 6 | 5 | +1 | +1 [-4,+6] |
| MMM | 8 | 13 | -5 | -5 [-12,+3] |
| QLM | 0 | 4 | -4 | -4 [-7,-1] |

Sampling units are 100 task groups, resampled within subject/level strata with
micro aggregation, not 3,000 calls. QLM private synthesis has the highest observed
point estimate, but exchange worsens four tasks with none improved. These paired
development results do not establish a general ranking of model families or
trained PACT efficacy; they do not authorize a methodological change or another
run. The math format/token limits remain part of the observed configuration.

Accounting: 3,000 attempted/committed/scored, 3,072,000 reserved output tokens,
3,523,618 input tokens, 1,343,727 actual output tokens, zero optimizer updates.
Incremental B: 2,100 calls, 2,150,400 reserved, 3,386,719 input, 923,007 actual
output tokens. Add only B to the cumulative ledger: 26,065 recorded generations
plus unchanged up-to-16 unknown controlled-child calls; historical updates remain
147. Prior historical totals were carried forward, not re-audited.
No local model generation, source/methodology change, commit, push, protected
cohort execution or automatic follow-up occurred.

For clarity, final readout-construction events with no correct revised actor packet
are QQQ 1, LLL 21, MMM 43, QLM 6 (each out of 100). Private synthesis construction
events with no correct initial actor are respectively 2, 36, 44 and 10.
These differ from the initial-uncovered construction column above.

Independent CPU rescoring of all 2,100 new Phase B records completed with zero score-outcome/parse mismatches. The exact pinned Math-Verify source and dependencies were restored in a temporary local environment; no model was downloaded. Cross-host elapsed-time and evaluator-environment metadata were excluded from equality. All 900 previously independently rescored A records are unchanged. The observed MATH A/B GPU/scoring path is verified. No local GPU run, commit or push occurred.

## 2026-10-08 — MBPP+ included smoke audited, correctness pending

Run `pact-breadth-mbpp-plus-001`, export `1791443310313931697`.
Uploaded ZIP hashes and internal inventories verified:

- PRIVATE: `dcb4f4c773535954302bd35722d70e0012d723d687bc5269a238651c0bc131ad`
- SANITIZED: `5f6bcf971498b8ac79820707fac0385e14dc76388979991a06c4f436c4464aae`
- scoring_jobs.json: `7dd3a06259562aadbf4d5c5bc365e58ed4d2bbed329eb2a121a83d83e266401f`

Frozen plan `72a10bbf296c6210cc5645ceeacc520dd15f6dfe8409e2d8217f8a890a3c0ae9`.
Real offline audit reconstructs the report outside Git. All 18 parse/score
classifications and exported scoring jobs independently reconstructed without
executing generated code. Jobs inventory contains 18 jobs; its exact byte hash
matches the user-provided value. Q/L/M identity records retain BF16/SDPA/no adapters.

| Family | Calls | Parse ok, correctness pending | Malformed, scored failure |
|---|---:|---:|---:|
| Q | 6 | 6 | 0 |
| L | 6 | 6 | 0 |
| M | 6 | 0 | 6 |

All stops are EOS. Six scored records mean six output-contract failures, not six
successful programs or completed EvalPlus tests. The twelve syntactically valid
responses remain pending_isolated_scoring; their correctness is unknown.
scorer_readiness is ready=false / safe_execution_unavailable. No generated program
or imported code was executed locally. Neither family accuracy nor team coverage/
complementarity can be concluded from this return. Invalid outputs remain failures;
unavailable correctness remains missing, never assumed incorrect.

Prior exposure index exactly equals reconstruction from completed MMLU-Pro,
MuSR and MATH-500 plans. Source has 378 rows/groups, with 100 characterization,
100 locked confirmation and 178 locked reserve representatives. Only two selected
smoke tasks have generation evidence. Private/sanitized summary/report match;
sanitized inventory is handoff/summary/report only. Selected questions, rendered
prompts and nonempty continuations were checked absent from public summary/report.

Accounting: 18 attempted/committed calls, 18 scoring attempts, six scored failures
and twelve pending; zero unresolved, recovery_safe=true. Reserved output 18,432,
input 2,742, actual output 2,886, optimizer updates zero. A partial: 18/900
generated, six scored; B unexecuted 0/2,100. Cumulative recorded generations become
26,083 plus unchanged up-to-16 historical unknown controlled-child calls;
historical optimizer updates remain 147. Earlier totals were carried forward.

Observed MBPP private-smoke generation/export path verified; real isolated
EvalPlus execution remains unverified. The next prerequisite is capability-checked
isolated scoring of these jobs, not in-notebook program execution. No automatic
continuation, source/methodology change, commit, push or protected-cohort use.

## 2026-10-08 — MBPP isolated evaluator attempt blocked before execution

Attempted to establish the existing Bubblewrap boundary for the 18 smoke jobs.
Host initially lacked bwrap; prlimit and a simple user/network namespace check
were available. Downloaded and extracted official Ubuntu arm64 Bubblewrap
0.9.0-1ubuntu0.3 into a dedicated /var/tmp directory without changing system
packages. The stale apt candidate URL returned 404; the current official package
was used. Created a dedicated system-Python 3.12 evaluator prefix outside Git/home;
ensurepip was unavailable, so no working EvalPlus environment is claimed.
A pinned EvalPlus dependency dry-run was performed, not a completed installation.

The ordinary tool sandbox denied the probe's host loopback socket. An approved
host-level probe still failed with safe_execution_unavailable. A trusted print-only
diagnostic using the exact same Bubblewrap command/restrictions exposed the cause:
`bwrap: Creating new namespace failed: Resource temporarily unavailable`.
No isolation restriction was removed and no generated program or benchmark
canonical solution was executed. No model calls, score imports or outcome changes.
The blocker is host namespace capability/resources; installing Python packages
alone does not resolve it. Need a dedicated Linux evaluator passing the existing
code-probe before executing scoring jobs. Twelve smoke correctness scores remain
pending; six malformed responses remain scored failures. No continuation launched.

## 2026-10-08 — MBPP+ deferred after Colab isolation probe failure

User returned a Colab code-probe traceback ending in
IsolationUnavailable: safe_execution_unavailable. This is user-reported runtime
evidence, not an imported probe receipt; the traceback does not identify the
underlying namespace failure. The local evaluator had separately failed its
isolation probe. Per the user's instruction to skip MBPP+ if Colab cannot support
safe scoring, MBPP+ is deferred without weakening the boundary or rerunning data.

Preserve the 18-call smoke: six malformed responses remain scored failures,
twelve correctness scores remain pending, and all 18 scoring jobs remain available
in the verified private bundle. Full A (remaining 882 calls) and B (2,100 calls)
are not executed. No accuracy or complementarity result is claimed and no budget
is reassigned. Resumption requires a capable evaluator passing the existing probe
and official evaluator validation. No new generation or score import occurred.
