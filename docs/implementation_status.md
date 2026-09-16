# Implementation status — 2026-09-16

The scientific proposal and supplied specification are unchanged. No commits/pushes,
model-weight downloads, GPU experiments, training, final-test evaluations, or empirical
PACT performance claims were made in this development pass.

| Component | Implementation | Evidence / remaining verification |
|---|---|---|
| M0 package, typed configs/schemas, CLI, dependency boundaries | implemented, cpu_tested | Editable install; strict preset validation; lazy model imports; standard-library tests |
| M1 synchronous three-agent protocol and fixed attacks | implemented, cpu_tested | Frozen private packets; sender state preserved; identical recipient replacement; synchronous revision; revised-only readout |
| M1 baseline paths | implemented, cpu_tested | Full 8-item mock run covers all 10 natural/matched paths and all 3 channel cells; no-exchange cells N/A |
| M1 metrics and offline analysis | implemented, cpu_tested | Exhaustive joint-outcome identities, null denominators, known erasure/repair/construction/readout fixtures, clustered paired comparisons |
| M1 durable collection/resume | implemented, cpu_tested | Interrupted writes, idempotent resume, incomplete-copy fallback, simulated storage failure/recovery, corrupt shard rejection, mismatch rejection |
| M1 reports/export/import | implemented, cpu_tested | Recomputed imported metrics agree; checksum round trip; hostile archive and secret-redaction tests |
| M2 authoritative validation loaders | implemented, cpu_tested | Both real pinned validation files parsed: ARC 299, original English LogiQA 651; selected 40 + 40; separate evaluator labels |
| M2 Qwen tokenizer/template boundary | implemented, cpu_tested | Actual pinned tokenizer only; 80 early-advisory private contexts fit; role-delimiter escaping checked |
| M2 Transformers/PEFT inference | implemented, gpu_unverified | Pinned revision, lazy loading, explicit precision/thinking/decoding, frozen adapter control; control-flow test passed, tiny neural test skipped |
| M2 packet and receiver eligibility, paired replay | implemented, cpu_tested, gpu_unverified | Missing pairs stay null; same context/snapshot/attack; paired node seeds; all affected nodes rerun; negative/zero/positive mock credit |
| M2 4/20/80 configurations and preflight | implemented, cpu_tested, gpu_unverified | Bounds/dry-run accounting validated; GPU/precision/kernel/model-access checks await Colab |
| M2 thin Colab notebook | implemented, cpu_tested, gpu_unverified | JSON and every code cell compile, outputs empty, bounded default; actual cloning/install/Drive/GPU execution awaits Colab |
| Training microbatch / length-sensitivity profile | deferred | Inference load/peak/throughput accounting implemented; no training-memory or sensitivity claim |
| PACT training, assignment/NLL/DPO/reference caches, optimizer resume | deferred | Milestone 3; no placeholder training command emits results |
| SAC/composition/full study/adaptive search/BFCL | deferred | Milestones 4–5; no final-test path is enabled |

No component has status `gpu_verified_on_reported_environment` yet.

## Executed validation

`python -m unittest discover -s tests -v`: **34 tests, 33 passed, 1 skipped**.
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

## Next gate

Review the diff, commit and push using the user's workflow. Open
`notebooks/01_pilot_colab.ipynb`, fill repository URL and reviewed commit SHA, leave
`PRESET="smoke"`, `STAGE="smoke"`, choose a fresh run ID and Run All.
Bring back its verified handoff ZIP. Review actual parsing/overflow rates, individual
variation, harmful/beneficial revision, missing pairs, costs, and failure logs before
the 20-item profile and 80-item pilot. Do not infer GPU success from local mocks.

See [the exact runbook](colab_runbook.md) and [choices/limits](implementation_decisions.md).
