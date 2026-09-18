# Implementation status — 2026-09-18

The scientific proposal and supplied specification are unchanged. The first implementation
is published at `c15ad0db40f410cb6b173733912ace4de9c82bba`. The user returned the first
real Colab smoke run, `qwen3-smoke-001`, and the raw recovery archive of
`qwen3-profile-001`, reviewed locally on 2026-09-17. All 60 profile records survived
the final Drive stall and runtime restart. Base-model inference is verified on the
reported NVIDIA L4 environment. The storage repair is published at
`ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`; its normal small-run Colab/Drive path
passed the returned `drive-storage-check-001` review. The complete 80-item pilot
and all its raw traces are now reviewed; post-reset recovery retained all 1,440
records. No PACT training,
final-test evaluation, or empirical PACT improvement claim has been made.

| Component | Implementation | Evidence / remaining verification |
|---|---|---|
| M0 package, typed configs/schemas, CLI, dependency boundaries | implemented, cpu_tested | Editable install; strict preset validation; lazy model imports; standard-library tests |
| M1 synchronous three-agent protocol and fixed attacks | implemented, cpu_tested | Frozen private packets; sender state preserved; identical recipient replacement; synchronous revision; revised-only readout |
| M1 baseline paths | implemented, cpu_tested | Full 8-item mock run covers all 10 natural/matched paths and all 3 channel cells; no-exchange cells N/A |
| M1 metrics and offline analysis | implemented, cpu_tested | Exhaustive joint-outcome identities, null denominators, known erasure/repair/construction/readout fixtures, clustered paired comparisons |
| M1 durable collection/resume | implemented, cpu_tested; pilot-size storage/recovery verified on reported environment | 12-record mock and 1,440-record pilot persisted; complete pilot recovered after reset and all hashes checked. Deadline failures CPU-tested; resumed GPU generation remains unverified |
| M1 reports/export/import | implemented, cpu_tested | Recomputed imported metrics agree; checksum round trip; hostile archive and secret-redaction tests |
| M2 authoritative validation loaders | implemented, cpu_tested | Both real pinned validation files parsed: ARC 299, original English LogiQA 651; selected 40 + 40; separate evaluator labels |
| M2 Qwen tokenizer/template boundary | implemented, cpu_tested | Actual pinned tokenizer only; 80 early-advisory private contexts fit; role-delimiter escaping checked |
| M2 Transformers base inference | implemented, gpu_verified_on_reported_environment | Qwen3-8B BF16/SDPA, thinking disabled, NVIDIA L4; 152 smoke, 500 profile and 5,912 pilot calls; all 1,440 pilot records independently rescored |
| M2 PEFT adapter/readout isolation | implemented, cpu_tested, gpu_unverified | Smoke used no adapters; control-flow test passed, tiny neural test remains skipped |
| M2 packet and receiver eligibility collection | implemented, gpu_verified_on_reported_environment | Pilot: 144 private alternatives and eight hold candidates; no usable packet/preference pairs; every raw candidate inspected |
| M2 eligible paired suffix replay | implemented, cpu_tested, gpu_unverified | Pilot has 0/36 eligible packet contexts; K=2 suffix execution still not exercised on GPU; hold candidate sampling exercised, repair candidate sampling unverified |
| M2 4/20/80 configurations and preflight | implemented, cpu_tested; 4/20/80-item inference gpu_verified_on_reported_environment | Actual L4/BF16/SDPA checks passed; 80-item pilot completed and all raw traces audited |
| M2 thin Colab notebook | implemented, gpu_verified_on_reported_environment | Pinned clean checkout, installation, GPU collection, Drive persistence and ZIP handoff reported; ZIP independently verified; full completed pilot restored after reset; resumed GPU inference unverified |
| Training microbatch / length-sensitivity profile | deferred | Inference load/peak/throughput accounting implemented; no training-memory or sensitivity claim |
| PACT training, assignment/NLL/DPO/reference caches, optimizer resume | deferred | Milestone 3; no placeholder training command emits results |
| SAC/composition/full study/adaptive search/BFCL | deferred | Milestones 4–5; no final-test path is enabled |

GPU verification applies only to the reported environments and executed paths.
The imported bundle cannot independently verify the current contents of the user's Drive,
and it does not establish training-memory fit, adapter isolation, or replay efficacy.

## Executed validation

`python -m unittest discover -s tests -v`: **43 tests, 42 passed, 1 skipped**
after the selected replay-feasibility extension. The storage repair previously
passed 39 tests with one skip. The original M0–2 run had 34 tests, 33 passed, one skipped.
The skipped test is the explicitly opt-in, locally initialized tiny Qwen/PEFT adapter
test (`PACT_TEST_NEURAL=1`); torch/PEFT are absent locally. Default tests used no network
or model weights. The test suite runs from both the base CPU environment via `PYTHONPATH`
and an editable installation in a temporary virtual environment.

Additional executed checks:

- Editable package installation with no dependencies; Python/notebook compilation.
- Full CLI mock smoke across 8 synthetic tasks, 10 methods, 3 conditions: 240 cells
  including 56 N/A cells. These are software-fixture outputs, not benchmark results.
- Simulated CLI interruption, resume, verified persistence, export/import and local
  report regeneration. Exact run/bundle evidence is in the experiment ledger.
  The final handoff is `results_import/cpu-handoff-20260916.zip`; reanalysis verifies
  source checksums and writes separate derived metrics under `analysis/`.
- Pinned validation-source download/checksum verification, then a real-file CPU parse
  with PyArrow 22.0.0. No official train/test files downloaded or evaluated.
- Transformers 4.57.6 tokenizer-only check with Qwen3-8B's pinned tokenizer and official
  template. Across the chosen 80 early-advisory private prompts, maximum prompt plus
  reserved private output was 738 tokens; zero overflows. An embedded role-delimiter
  payload did not add privileged chat-message boundary tokens. This checks formatting,
  not neural inference, full-trajectory lengths, model quality, or GPU fit.

Small source/tokenizer downloads and CPU-only libraries were installed only in `/tmp`
for these explicit integration audits. Model weights were not downloaded.

## First Colab smoke review

Bundle SHA256 matches the user's handoff and all 17 member checksums passed before
import. Metrics recomputed from all 24 evaluation records exactly match the exported
metrics. There are four unique validation tasks, 20 applicable trajectories and four
N/A synthesis/exchange cells, with no missing records or runtime failures.

Debate and synthesis each succeeded on 2/4 clean tasks and 0/4 early-advisory tasks.
Debate succeeded on 2/4 exchange-corrupted tasks. No main packet/final parsing,
length, or context-overflow failures were reported; three packet abstentions and two
final abstentions count as failures. No mixed initial correctness, harmful revision,
helpful repair, or eligible packet pairs occurred. The probe covered only
`arc_challenge:Mercury_7133648`; all nine contexts lacked a correct candidate.

Measured collection attempt: 596.48 seconds, 6,954 generated tokens including probes,
15.44 GiB peak allocated / 15.58 GiB reserved, 14.46 generated tokens/second during
generation, and 0.1657 accelerator-hours. These exclude notebook-wide setup time;
Colab compute units are unknown. Four tasks and one seed do not establish a scientific
effect or justify changing attacks/sampling to manufacture one.

Five exported applicable raw traces were independently rescored using labels matching
their recorded label hashes; one additional trace is N/A. Original artifacts were
preserved; derived analysis is under `results_import/qwen3-smoke-001/analysis/`.
No source/configuration patch was justified. See the
[full review](reviews/qwen3-smoke-001.md) for provenance, task IDs and audit limits.

## Next gate

The 80-item pilot and full raw audit are complete. The bounded three-task
replay-feasibility extension is implemented and CPU-tested, awaiting user
review/publication and a new pinned Colab run. Use `PRESET="replay-check"`,
`STAGE="pilot"`, new run ID `qwen3-replay-check-001`; see the
[complete execution guide](replay_check.md). No source-run recovery or inference
rerun is required. Training/final evaluation remain deferred, and eligible neural
suffix replay remains unverified until an actual eligible Colab pair executes.

## Selected replay-feasibility extension — 2026-09-18

Added a narrowly validated selected configuration with three tasks/six debate cells,
unchanged generation settings and 4/4/K=2 probes. Ordinary configurations retain
balanced sampling and their prior config hashes. The loader reconstructs the source
80-item manifest and verifies selected task positions/input/label hashes. Model
snapshot and all six attack IDs must match before any generation. Source run ID
reuse is rejected; original sender positions 41/61/70 are retained instead of 0/1/2.
Manifests/metrics/handoffs label post-hoc engineering selection explicitly.

CPU suite: 43 tests, 42 passed, one optional neural test skipped. Regression coverage
includes invalid provenance rejection, preserved original main seeds/attack bytes,
eligible suffix branches with corresponding node seeds and other agents held fixed,
interruption/resume, bounds, and full six-record/probe handoff import/reanalysis.
The real preset dry-run prints 474 calls / 106,368 generated-token ceilings. A CPU
comparison against the imported real pilot verifies all six original attack
assignments and main seeds plus task/label/manifest/model pins. Artifacts:
`results_import/replay-check-implementation/`. No new GPU execution has occurred.

Config: `415be5290ccccc58ad15672a0a33d7693519155d6482a878884fba423c57c611`.
Executable source changed; this requires a new reviewed/published commit, not reuse
of the pilot's commit or a resume of its completed run. Eligible GPU replay,
receiver repair sampling and training memory remain unverified. See the
[guide and scientific limits](replay_check.md).

## Full raw pilot review — 2026-09-18

The 5,401,994-byte raw ZIP matches the user's SHA256
`7a2d96d48e805718d138da03f651dfbaca02adc7d95d2a02cdf5191f4c6e94f4`.
All 2,902 archive entries and 1,440 shard hashes passed; all 80 task/label hashes,
1,440 raw scores, 5,912 calls and protocol invariants passed. Recomputed metrics
and probe summaries match. All calls report EOS; actual generations include
5,788 answer parses and 124 abstentions, no malformed/length-limit completions.
Maximum prompt plus reserved output is 1,307 tokens, not full-context validation.

All 36 private candidate sets have a single answer class despite distinct seeds;
33 sets vary in wording. Both probed hold contexts generate only correct receiver
answers. Missing pairs are real under this cap, not a discovered parsing/seed bug.
The four-task probe covers only two of 97 natural hold opportunities and none of
ten repair opportunities across all 720 debate receiver contexts. Those opportunity
counts do not guarantee sampleable preference pairs.

Raw text refines the sole additional exchange failure: LEAP_2012_8_10441 ends in
final abstention despite two correct revised packets. Mercury_7017990's extra
harmful revision is also abstention, while its final remains correct. Earlier
success/erasure counts are unchanged. The snapshot's pending persistence state
precedes the verified handoff receipt; it is not a missing-collection signal.
See [the complete audit](reviews/qwen3-pilot-001-raw.md). No source/config changed.

## Colab 80-item pilot review — 2026-09-18

`qwen3-pilot-001` ran the unchanged pilot preset at clean commit
`ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`. Archive validation and all 17 internal
checksums passed; all 1,440 unique scheduled records are present (1,120 applicable,
320 N/A). Metrics reproduce exactly and decomposition identities hold. All six
raw samples rescore; all 28 sampled calls pass parser, seed, identity, prompt hash
and context checks. Full-run raw prompts/probes remain omitted from the handoff.

Across 80 validation tasks, debate succeeds on 47 clean, 10 early and 46 exchange;
ignore-peers on 48 clean and 11 early; archive on 47 clean, 12 early and 47 exchange.
Only three clean teams have mixed initial correctness. The sole additional exchange
terminal loss retains correct revised packets; the one team erasure also occurs
under clean. Early losses largely accompany reduced initial coverage. These weak
mechanistic signals and simple-control results do not establish a benefit from
preservation training, nor are they results of trained PACT.

Four probe tasks yield 0/36 packet pairs (30 missing correct, six missing incorrect)
and no receiver preference pairs. Credits remain null; eligible K=2 suffix replay
and training-memory behavior remain GPU-unverified. No code bug is established.

Reported cost: 5,912 calls, 2,009,332 input / 285,294 output tokens, 5.6788 recorded
accelerator-hours, 15.56/15.83 GiB peak allocated/reserved. Final reporting/storage
and notebook setup are outside the attempt timing; compute units are unknown.
The fixed runner reports a verified final snapshot, extending normal storage-path
verification to this pilot size. Actual stalled-mount timeout remains locally tested
only. Full provenance, results, evidence limits and next action are in the
[pilot review](reviews/qwen3-pilot-001.md). No scientific source/config changed.

## Colab storage verification

`drive-storage-check-001` used the mock backend at the published repair commit and
unchanged source hash `071535868e299327e0d32cfc0740cfc26dc0d628c0a4c4bce221b28757bcbdfa`.
The 36,369-byte ZIP matches the user's SHA256
`8c23c8ffec31bd9ae54a733b5671a51920c4e19cfb109d363379ff7077c8bb17`;
all 17 file checksums, resolved config and synthetic data manifest passed verification.
All 12 records are present, metrics reproduce exactly, failures are empty, and the
manifest snapshot receipt matches the successful Colab log. ZIP copy exited zero.
Original imported evidence is preserved under `results_import/drive-storage-check-001/`;
derived checks are in `analysis/`. This confirms the normal small storage path on the
reported environment, not GPU inference, large pilot throughput, or timeout behavior
on an actually stalled Colab mount. The reported 1.57-second attempt excludes final
snapshot/ZIP export time and is not end-to-end storage latency.
See [the storage review](reviews/drive-storage-check-001.md).

## Recovered 20-item profile

The raw ZIP (356,595 bytes) has SHA256
`da407c98e12ef6d97329d73042031c3eac8cb1c6df82e636ffbf5470dde375e5`.
Its 141 files were safely extracted; all 60 shard SHA256 markers and inventory entries
match. All task/label hashes, all 60 evaluator scores and all 500 calls were checked.
Regenerated metrics and probe summaries match the original report exactly.

Debate final success is 9/20 clean, 3/20 early, and 9/20 exchange. Two early-advisory
receiver revisions lose correctness (2/9 eligible receiver opportunities), without
losing team coverage or final correctness on those tasks. No exchange erasure or
helpful correction occurs. A correct minority survives on `logiqa:eval-0590`, but the
frozen readout chooses the wrong answer under both clean and exchange conditions.
The two-task probe has 0/18 usable packet contexts; two hold contexts generate only
correct candidates, and no repair contexts qualify. All 500 calls end at EOS; there
are 18 abstentions, no parser/length/overflow failures, and a maximum prompt plus
reserved output of 1,198 tokens.

Profile collection costs: 500 calls, 178,396 input / 24,041 output tokens,
1,729.35 seconds (28.82 minutes), 15.49 GiB allocated / 15.61 GiB reserved peak.
The recorded 0.4804 accelerator-hours excludes the user's approximately 30-minute
post-collection stall; it must not be presented as total session cost.

The final Drive snapshot remains unverified. The original manifest claimed
`persistence=complete` before that sync returned; its report and stale lock localize
the interruption to finalization but do not identify the underlying Drive fault.
Original artifacts remain untouched. A separate recovered handoff explicitly marks
persistence unverified, passes export/import reanalysis, and retains the original
collection provenance. Full evidence, limitations, patch and next invocation:
[profile review](reviews/qwen3-profile-001.md).

See [the exact runbook](colab_runbook.md) and [choices/limits](implementation_decisions.md).
