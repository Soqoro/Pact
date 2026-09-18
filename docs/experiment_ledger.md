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
