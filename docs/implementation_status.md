# Implementation status — 2026-09-20

The scientific proposal and supplied specification are unchanged. The first implementation
is published at `c15ad0db40f410cb6b173733912ace4de9c82bba`. The user returned the first
real Colab smoke run, `qwen3-smoke-001`, and the raw recovery archive of
`qwen3-profile-001`, reviewed locally on 2026-09-17. All 60 profile records survived
the final Drive stall and runtime restart. Base-model inference is verified on the
reported NVIDIA L4 environment. The storage repair is published at
`ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`; its normal small-run Colab/Drive path
passed the returned `drive-storage-check-001` review. The complete 80-item pilot
and all its raw traces are now reviewed; post-reset recovery retained all 1,440
records. The selected replay check at `e79a9ab0da7b3801ba1ff488ddd974302768da2a`
now verifies 13 eligible neural packet pairs and all 52 suffix branches; receiver
preference pairs remain unavailable. The complete bounded clean-answer warm start
now passes returned metadata review: nine updates, fresh-process GPU continuation,
three frozen exports and reported verified persistence. No full PACT training,
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
| M2 PEFT adapter/readout isolation | implemented, tiny_cpu_neural_tested, gpu_unverified | Distinct adapter/base logits and restored inference state pass on locally initialized tiny Qwen; real Colab smoke used no adapters |
| M2 packet and receiver eligibility collection | implemented, gpu_verified_on_reported_environment | Selected replay check: 13/18 packet pairs; 64 receiver candidates from eight hold/eight repair contexts, 0/16 preference pairs. All raw candidates inspected |
| M2 eligible paired suffix replay | implemented, cpu_tested, gpu_verified_on_reported_environment | Selected L4 check: 13 eligible pairs, K=2, 52 audited branches / 208 calls; fixed attacks, corresponding node seeds, unchanged other-agent packets and all recomputed credits pass |
| M2 4/20/80 configurations and preflight | implemented, cpu_tested; 4/20/80-item inference gpu_verified_on_reported_environment | Actual L4/BF16/SDPA checks passed; 80-item pilot completed and all raw traces audited |
| M2 thin Colab notebook | implemented, gpu_verified_on_reported_environment | Pinned clean checkout, installation, GPU collection, Drive persistence and ZIP handoff reported; ZIP independently verified; full completed pilot restored after reset; resumed GPU inference unverified |
| Training microbatch / length-sensitivity profile | bounded recipe observed; full length profile pending | 36 examples across three agents, 112–449 tokens; resume peak allocated/reserved 15.891/16.254 GiB. No full-cap fit or length-sensitivity claim |
| M3 scored-bank contract, masked assignment, same-prompt preferences, reference cache | implemented, cpu_tested | Independent numerical reference, missingness, global coefficients, immutable cache and CLI fixture round trip |
| M3 completion NLL / DPO numerical functions | implemented, cpu_neural_tested; gpu_unverified | Numerical-reference agreement, masked gradients, one-step target improvement and detached DPO reference gradients pass |
| M3 train loaders and frozen task manifests | implemented, cpu_tested; pinned real sources verified | Full 8,495 train / 950 validation audit, 59 redundant train rows excluded; 12/1,200 task balanced selections. Semantic paraphrases remain unaudited; no final-test access |
| M3 bounded clean-answer warmstart, adapter exports, optimizer/RNG resume | tiny_cpu_neural_tested; completed GPU run metadata reviewed | Nine updates, fresh-process GPU continuation and three frozen exports reported successful. Initial checkpoints preserved; tensor bytes omitted locally. GPU uninterrupted-equivalence control unverified |
| M3 warm-start Colab handoff and snapshot restore | cpu_tested; completed Colab handoff reviewed | Final archive SHA and 31 payload checksums verified; reported full snapshot/ZIP persistence successful. Actual post-reset Drive restore pending |
| M3 bounded train-only collector and neural frozen-reference scoring | cpu_neural_tested; complete GPU engineering bank reviewed | Six records, compatible resume, 218 generations, five private pairs / 20 suffix branches, 18 answer and five positive-packet scores audited. Zero receiver pairs; GPU reference scoring unverified |
| M3 receiver-feasibility base control | implemented, cpu_tested, gpu_verified_on_reported_environment | Returned 54/54 calls match saved prompts/seeds/model/runtime; base receiver correctness 0/24, no pairs; reported verified persistence. Diagnostic resume/restore remains CPU-only verified |
| M3 broader receiver feasibility | design_frozen, runner_cpu_neural_tested; gpu_unverified | 24 exact train-only IDs, 12 per family, warm-start exclusions; 48 clean/exchange records, 912-call / 224,256-output-token caps; immutable call resume, diagnostic reports and verified handoffs |
| M3 joint specialization/revision updates, sparse-support bank sampling and refreshes | deferred | Full PACT train remains explicitly unimplemented |
| SAC/composition/full study/adaptive search/BFCL | deferred | Milestones 4–5; no final-test path is enabled |

GPU verification applies only to the reported environments and executed paths.
The imported bundle cannot independently verify the current contents of the user's Drive,
and it does not establish full-context training-memory fit, independent tensor-level
adapter isolation, or replay efficacy.

## Executed validation

Latest receiver-runner increment: **113/113 pass** with tiny CPU neural checks
enabled; default suite **107 pass, six skip**. Ten new checks cover the runner,
partial-pool resume, unresolved-attempt rejection, persistence failures, safe
snapshot restoration, missing-pair accounting and tiny CPU neural generation
with unchanged actor/reference tensors and restored base-readout adapter state.
No real GPU execution or pretrained download occurred.
[Implementation evidence](reviews/receiver-feasibility-implementation-001.md).

The prior broader receiver-design increment passed **103/103** with tiny CPU neural
checks enabled; default suite **98 pass, five skip**. Six added planner tests
cover frozen selection, exclusions, family/sender balance, source/selection
tampering, split rejection, budget enforcement and the non-executing CLI.
[Design and local command](receiver_feasibility_design.md).
The preceding preference-feasibility increment passed **97/97** with opt-in,
and **92 pass, five skip** by default.
[New control-path evidence](reviews/preference-feasibility-001.md) covers the 54-call
plan, archive/prompt/runtime checks, diagnostic pair separation and verified recovery.
The prior collection increment passed 90/90 with opt-in, 85 with five skips by default. No pretrained weights were downloaded.
[Current evidence](reviews/collection-implementation-001.md) includes reference/base
isolation, exact sampled-token preservation, six-record resume, cached scores and
verified snapshot restoration. The completed returned-bank audit below additionally
verifies GPU collection and compatible continuation; frozen-reference scoring
remains unverified because no receiver preference pair qualified.

### Prior warm-start implementation check

With explicit user opt-in, the full suite now passes **81 tests, 81 passed, zero
skipped** in `/tmp/pact-neural-cpu`, using CPU-only torch 2.9.1, Transformers 4.57.6
and PEFT 0.18.1. No pretrained weights or datasets were downloaded for testing;
model hubs were offline and the runner asserted a CPU-only torch build. All three
previously skipped neural tests pass. Interrupted warm-start training with nonzero
dropout reproduces uninterrupted final parameters and loss/progress logs exactly
using fresh model/optimizer objects and non-reentrant activation checkpointing.
Frozen exports and adapter0 reload also pass. The new notebook execution gate,
full snapshot restore, corrupt/path-traversal rejection and persistence-only retry
pass CPU fixture tests. [Current evidence](reviews/warmstart-colab-check-001.md);
[initial neural verification](reviews/neural-cpu-check-001.md).

The current default, dependency-free invocation passed **81 tests, 78 passed,
3 skipped**. Seven new CPU control tests cover:
recipe bounds, pinned data/order planning, prompt/target separation, no truncation,
typed optimizer/RNG trees, immutable checkpoints/corruption, early resume mismatch
rejection and a model-free CLI plan. The returned first real Qwen3-8B BF16
update exercises the configured activation-checkpointing path; the completed
follow-up also reports successful GPU continuation and final reference exports. The pinned 12-task dry run plans nine
optimizer updates and 36 forward/backward examples without launching any.
[Warm-start contract and verification gate](warmstart.md).

The preceding train-only data increment passed **68 tests, 66 passed, 2 skipped**.
Its nine tests cover source/split
boundaries, exact and transitive lexical overlaps, reordered-answer duplicates,
conflicting labels, deterministic balance, immutable manifests, corruption and
completion-marker ordering. Real pinned source parsing and a 1,200-item CPU
selection also passed; the old 80-item validation manifest reproduces exactly.
[Source counts, exclusions and limits](training_data.md).

The preceding local learning-foundations increment passed 59 tests (two skips).
Its 16 added tests cover
independent assignment solutions, global coefficients, split/prompt rejection,
missing/invalid candidates, causal scoring, reference cache integrity and CLI round
trips. The synthetic `training-check` converges with two assignment rows, one
base-only row and one preference pair per stratum; no model training is executed.

The selected replay extension previously passed 43 tests (one skip); the storage
repair passed 39 (one skip), and original M0–2 passed 34 (one skip). The three neural
tests remain explicitly opt-in (`PACT_TEST_NEURAL=1`): tiny Qwen/PEFT adapter isolation,
torch completion gradients/reference detachment, and the newly added warm-start
update/isolation/resume test. They still skip in the default environment; their
dependencies were installed only in the isolated `/tmp/pact-neural-cpu` environment.
Default tests use no network or model weights. Earlier M0–2 checks also ran from an
editable installation in a temporary virtual environment; this increment was checked
in the base CPU environment using `PYTHONPATH=src`. The real training-data audit
used only PyArrow 22.0.0 from an isolated `/tmp` install and four pinned source files;
default tests remain network-free and require no data/model dependencies.
[Current commands and remaining gates](training_foundations.md).

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

## Current next gate

The [complete training bank](reviews/qwen3-bank-001-complete.md) passes audit.
This Colab stage is complete; no rerun or further export is needed. Zero correct
receiver candidates among 24 samples leave both hold/repair preference strata
empty. The [matched-base diagnostic](reviews/qwen3-base-control-001.md) also passes
returned audit: 54/54 calls and zero correct base receiver samples. The bounded
check is complete and does not support blaming the warm start. The
[broader design](receiver_feasibility_design.md) and exact selection are now frozen
and CPU-verified. The dedicated receiver-only runner now implements call-boundary
resume and raw diagnostic accounting. Next is user review/commit/push, followed
by the [bounded Colab run](receiver_feasibility_colab.md) pinned to that new SHA
and review of its returned handoff. The new GPU execution path is unverified.
GPU frozen-reference scoring, full revision
optimization and final-test evaluation remain unverified or deferred.

### Earlier gate after the selected replay review

The selected replay check has completed and passed local review. No additional
Colab command, rerun or raw export is needed. Eligible neural suffix replay and
hold/repair candidate sampling are verified on the reported L4 environment.
Revision preference data remains unresolved: zero usable pairs in 16 sampled
receiver contexts. Training, adapter/reference isolation and training-memory checks
are not thereby verified.

The next proposed scope is local Milestone-3 learning-component work plus an
explicit training-split data plan that handles missing pairs honestly. Do not train
on the selected validation artifacts, fabricate receiver counterparts, or report a
full revision objective without usable pairs. No Milestone-3 implementation or GPU
training was started during this review. See the
[replay-check review](reviews/qwen3-replay-check-001.md).

## Returned selected replay check — 2026-09-18

ZIP checksum matches the user's
`21e5133daa634a894357f09658c2a78c5b6bef1bf3d701bcd8d454f7532899cb`.
All six raw records reconstruct their inventory hashes, all 386 calls are audited,
and all metrics/probe summaries/credits reproduce. The 13/18 eligible private-packet
pairs yield five +1, two +0.5 and six zero credits; five missing credits remain null.
Three eligible pairs are not length-bin matched. These selected, K=2 observations
verify execution, not representative effect sizes or training efficacy.

All 52 suffix branches preserve attack bytes/site, other agents' private packets,
corresponding node seeds and revised-only base readout. Corrupted-sender substitutions
also execute correctly. All calls end at EOS: 380 answer parses, six abstentions,
no malformed/length-limit completions. Maximum prompt plus reserved output is 830.
The six main trajectories reproduce the original pilot's texts, prompts, attacks
and seeds, excluding expected new IDs/timing and timing-dependent artifact hashes.

Receiver candidate sampling now runs on both strata: eight hold and eight repair
contexts, four candidates each. Each set contains one correctness class only;
hold has six all-correct/two all-wrong sets, repair one all-correct/seven all-wrong.
No valid same-context preference pair is available or lost by parsing/selection.

Cost: 386 calls, 148,080 input / 18,046 output tokens, 23.02 recorded collection
minutes (0.38361 accelerator-hours), 15.41/15.53 GiB peak allocated/reserved. Final
reporting/persistence and notebook setup are outside that attempt timing. Reported
persistence is complete with a verified snapshot receipt. Full evidence is under
`results_import/qwen3-replay-check-001/analysis/`; originals are unchanged. No source
patch or regression-suite rerun was justified; the full CPU artifact audit passed.

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


## Returned first warm-start update — 2026-09-19

The [qwen3-warmstart-001 handoff review](reviews/qwen3-warmstart-001.md) verifies
all ten payload checksums, code/config/data identities, 12 prompt/target/mask records,
all task orders, both checkpoint metadata inventories and the one-update log.
Real training reports one optimizer update, finite loss/gradient norm, and verified
Drive persistence. Nested local-only persistence flags predate that verification.
Source code remains unchanged; no suite rerun was needed for this artifact review.
Eight further updates, GPU optimizer resume and real frozen exports remain pending.
Next: resume the same clean `a277794d271720665d57308cc15f3122f1934e27` checkout
with `RESUME=True`, `STOP_AFTER=None`, then review the returned final handoff.


## Completed warm-start continuation — 2026-09-19

The [final handoff](reviews/qwen3-warmstart-001-complete.md) passes archive integrity,
code/config/data identity, old checkpoint preservation, all ten checkpoint metadata
records, fixed batch/task ordering, and three reference config/hash checks. Fresh
GPU process continuation completes the eight remaining updates: nine total, 36
examples, three agents. Final exported weights are reported verified against actors
by the pinned runtime; omitted tensor bytes prevent independent local comparison.
Final snapshot/ZIP persistence reports success. No source patch or new suite run was
needed; the CPU artifact audit passes. Next is local reference reload/scoring and
train-only bank collector work. Do not repeat the completed warm-start run.


## Frozen-reference scorer and train-only bank — 2026-09-19

The implemented `collect-bank` and `cache-reference` commands default to plans.
The fixed two-task, three-condition recipe pins the completed warm-start exports
and frozen training manifest. It preserves exact sampled token IDs and all paired
raw evidence, scores the correct frozen reference, rejects incompatible resume,
and retains missing preference strata. All 90 tests pass with CPU neural opt-in;
default execution passes 85 with five expected skips. Synthetic persistence and
restore pass with verified hashes; no GPU collection, Drive restore or new
optimizer execution is claimed. [Evidence](reviews/collection-implementation-001.md).


## First returned train-only bank record — 2026-09-19

SHA256 `ceba32531b82864d694020ac29dce8e612b887c031da198cc644e5982697a7c3`
and all nine payload checksums pass. Clean published source, config/data/model/
reference identities, all 19 prompts/seeds/parses/token-array associations and
three actor answer-score reductions pass the CPU audit. The intentional one-record
stop reports exit zero and a verified snapshot. This exercises real export loading,
frozen-team generation and answer scoring; it does not exercise GPU reference
scoring, positive-packet scoring or paired suffix replay. All 19 outputs answer C
against gold B, leaving three missing private pairs and no eligible receiver
contexts. No efficacy inference or sampling expansion follows. Resume the same
run for the five remaining records. [Full review and continuation cell](reviews/qwen3-bank-001-first.md).


## Completed train-only bank — 2026-09-19

The final ZIP SHA256 `a77e11339b3991e3e0d5f0c1d42d0aed50b62c820619e555a60f9a4da956ac39`
and all 18 payload checksums pass. The first shard and attempt are unchanged;
all six records, 218 calls, five private pairs and 20 suffix branches reproduce
from trusted protocol logic using inert returned outputs. Full bank and preference
accounting match exactly. Eighteen answer and five positive-packet NLL forwards
are recorded; zero reference forwards occur because all 24 receiver candidates
lack a correct answer. Full revision readiness remains false. All six main
trajectories fail; this two-task training check cannot establish effectiveness.
The final log reports verified snapshot/ZIP persistence. No source fix or suite
rerun was needed; the CPU artifact audit passes. [Evidence and next local task](reviews/qwen3-bank-001-complete.md).


## Receiver-feasibility analysis and matched base control — 2026-09-19

Local analysis finds that all six eligible receiver contexts concern one LogiQA
item. Its clean private pool has six correct answers in 15 samples, but the 24
receiver candidates have no correct answer. ARC clean private samples are all
wrong. Format/truncation failures do not explain the missing pairs; the absence of
an exact-context base control prevents attribution to warm-start changes.

`preference-diagnostic` now pins the completed source ZIP and bank, selects 54 saved
actor calls, and plans at most 54 unadapted-base calls with the same prompts, seeds,
sampling and model/runtime identities. Reports separate the two policies and never
export training pairs. Default invocation loads no model. All 97 tests pass with
CPU neural opt-in; default passes 92 with five expected skips. Actual-source plan
and analysis are retained locally; no GPU calls or optimizer updates were executed.
[Evidence](reviews/preference-feasibility-001.md); [decision rules and Colab sequence](preference_feasibility.md).


## Returned matched base control — 2026-09-19

The [qwen3-base-control-001 audit](reviews/qwen3-base-control-001.md) passes the
user-supplied SHA256, 62 payload checksums, 115 inventory entries and all 54
prompt/token-prefix/seed/sampling/model checks. The source plan and final report
reconstruct exactly. Base private correctness is 0/15 ARC and 7/15 LogiQA versus
actors' 0/15 and 6/15. Both have 0/24 correct receiver outputs and no preferences.
All base calls end at EOS without format/length failures. One attempt records
16,995 input / 3,275 output tokens and 343.519 seconds excluding final persistence.
The receipt reports verified snapshot persistence; the supplied final Drive path
and ZIP hash match. Current Drive and GPU diagnostic resume/restore are unverified.

This completes the bounded diagnostic without supporting a warm-start regression
explanation. The next local task is a broader, outcome-independent training-only
feasibility design with fixed budgets, not a repeated run or full revision update.
No executable source changes or suite rerun were needed; the CPU artifact audit
passes. Frozen-reference GPU scoring and full PACT optimization remain unresolved.


## Broader training-only receiver-feasibility design — 2026-09-19

The new offline planner verifies the existing 1,200-task pool and 12-task warm-start
manifests, excludes warm-start IDs/audited groups/content groups, and freezes 24
tasks by outcome-independent hash ranking, 12 per family. Interleaving balances
exchange senders within each family. All 48 planned records use the existing
frozen actors and clean/exchange protocol; four fresh samples per eligible receiver
give at most 912 generations / 224,256 output tokens. No private alternatives,
suffix replays, scores or optimization are part of this diagnostic.

Selection hash `e6842155a4080c0a39e3ad39a8b207539312ffb57b05da7675a7343136e33d96`;
recipe hash `efa9d8cfb1450227b80286309505116d9a8e03fd1732d99d1ee6b5bcabf3d7e1`.
Real local data reconstruction passes, all six new planner tests pass, and the full
suite passes 103/103 with tiny CPU neural opt-in (98 pass/five skip by default).
No weights, datasets or GPU calls were requested. Evidence is retained under
`results_import/receiver-feasibility-design-001/`. The execution runner is explicitly
not implemented; this increment finishes experiment design and local plan validation.


## Receiver-only runner implementation — 2026-09-20

The previously frozen broader design now has a dedicated execution path. Ten new
CPU checks bring the suite to 113 tests: 107 pass/six skip by default, 113/113 pass
with tiny CPU neural opt-in. Immutable per-call results reconstruct exact partial
candidate pools; diagnostic reports preserve ineligible, incomplete and missing
classes. Local ZIP, timed persistence and safe snapshot restoration pass fixture
checks, including stale snapshot and unresolved-attempt rejection. The tiny neural
check confirms unchanged actor/reference tensors and restored adapter state after
base readout, with no scoring forwards.

Production selection and budgets remain unchanged: 24 train tasks, 48 records,
at most 912 calls and 224,256 output tokens. No real model collection occurred;
there are no new receiver pair counts to report. New GPU execution and recovery
remain unverified. Evidence and caveats are in the
[implementation review](reviews/receiver-feasibility-implementation-001.md);
[ordered Colab cells](receiver_feasibility_colab.md) require user publication and
a new pinned commit before execution.
