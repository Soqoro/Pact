# Implementation status — 2026-09-17

The scientific proposal and supplied specification are unchanged. The first implementation
is published at `c15ad0db40f410cb6b173733912ace4de9c82bba`. The user returned the first
real Colab smoke run, `qwen3-smoke-001`, and the raw recovery archive of
`qwen3-profile-001`, reviewed locally on 2026-09-17. All 60 profile records survived
the final Drive stall and runtime restart. Base-model inference is verified on the
reported NVIDIA L4 environment. The storage repair is local and not yet published
or verified on Colab. No PACT training,
final-test evaluation, or empirical PACT improvement claim has been made.

| Component | Implementation | Evidence / remaining verification |
|---|---|---|
| M0 package, typed configs/schemas, CLI, dependency boundaries | implemented, cpu_tested | Editable install; strict preset validation; lazy model imports; standard-library tests |
| M1 synchronous three-agent protocol and fixed attacks | implemented, cpu_tested | Frozen private packets; sender state preserved; identical recipient replacement; synchronous revision; revised-only readout |
| M1 baseline paths | implemented, cpu_tested | Full 8-item mock run covers all 10 natural/matched paths and all 3 channel cells; no-exchange cells N/A |
| M1 metrics and offline analysis | implemented, cpu_tested | Exhaustive joint-outcome identities, null denominators, known erasure/repair/construction/readout fixtures, clustered paired comparisons |
| M1 durable collection/resume | implemented, cpu_tested; Drive repair gpu_unverified | Profile finalization stalled after all 60 records; local recovery ZIP before final sync, 120-second worker deadlines, progress, accurate persistence status; Linux CPU regression tests pass |
| M1 reports/export/import | implemented, cpu_tested | Recomputed imported metrics agree; checksum round trip; hostile archive and secret-redaction tests |
| M2 authoritative validation loaders | implemented, cpu_tested | Both real pinned validation files parsed: ARC 299, original English LogiQA 651; selected 40 + 40; separate evaluator labels |
| M2 Qwen tokenizer/template boundary | implemented, cpu_tested | Actual pinned tokenizer only; 80 early-advisory private contexts fit; role-delimiter escaping checked |
| M2 Transformers base inference | implemented, gpu_verified_on_reported_environment | Qwen3-8B BF16/SDPA, thinking disabled, NVIDIA L4; 152 smoke calls and 500 profile calls; all 60 profile trajectories independently rescored |
| M2 PEFT adapter/readout isolation | implemented, cpu_tested, gpu_unverified | Smoke used no adapters; control-flow test passed, tiny neural test remains skipped |
| M2 packet and receiver eligibility collection | implemented, gpu_verified_on_reported_environment | Profile: 72 private alternatives and eight hold-context receiver candidates; no usable packet or preference pairs; all raw candidates inspected |
| M2 eligible paired suffix replay | implemented, cpu_tested, gpu_unverified | Profile has 0/18 eligible packet contexts; K=2 suffix execution still not exercised on GPU; hold candidate sampling exercised, repair candidate sampling unverified |
| M2 4/20/80 configurations and preflight | implemented, cpu_tested; 4-item smoke and 20-item inference profile gpu_verified_on_reported_environment | Actual L4/BF16/SDPA/model-access checks passed; 80-item pilot remains unrun |
| M2 thin Colab notebook | implemented, gpu_verified_on_reported_environment | Pinned clean checkout, installation, GPU collection, Drive persistence and ZIP handoff reported; ZIP independently verified locally; interrupted GPU restore unverified |
| Training microbatch / length-sensitivity profile | deferred | Inference load/peak/throughput accounting implemented; no training-memory or sensitivity claim |
| PACT training, assignment/NLL/DPO/reference caches, optimizer resume | deferred | Milestone 3; no placeholder training command emits results |
| SAC/composition/full study/adaptive search/BFCL | deferred | Milestones 4–5; no final-test path is enabled |

GPU verification applies only to the reported smoke environment and executed paths.
The imported bundle cannot independently verify the current contents of the user's Drive,
and it does not establish training-memory fit, adapter isolation, or replay efficacy.

## Executed validation

`python -m unittest discover -s tests -v`: **39 tests, 38 passed, 1 skipped**
after the profile storage repair. The original M0–2 run had 34 tests, 33 passed, one skipped.
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

The profile is recovered; do not rerun it. Publish the reviewed storage repair through
the user's explicit commit/push workflow, then check out that new full SHA in Colab.
Run `PRESET="storage"`, `STAGE="smoke"`, `RUN_ID="drive-storage-check-001"`,
`RESUME=False`. This is a 12-record CPU mock check of the real Drive handoff, not GPU
inference or new scientific data. Local round-trip validation passed, including raw
snapshot restore, ZIP verification and metric reanalysis. Real Drive behavior remains
unverified until this check returns. The existing 80-item pilot follows only after
storage verification and workload review; it has 1,440 scheduled cells, not 80 calls.
The scientific gate remains unresolved; training and final evaluation remain deferred.

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
