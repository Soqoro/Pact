# Review of `qwen3-smoke-001` — 2026-09-17

The first real-model smoke passes the execution and artifact-integrity gate on the
reported NVIDIA L4 environment. It does not establish the scientific mechanism:
there is no mixed initial correctness, harmful revision, helpful repair, or eligible
replay pair in these four validation tasks. Proceed to the existing 20-item profile
without changing model, attacks, sampling, or code.

## Provenance and verification

The relevant run is identified by `manifest.json`, its invocation, source/config/model
identities and completed attempt log. Other local bundles are CPU mock development
runs and are not model-performance comparisons.

- ZIP: `results_import/qwen3-smoke-001-handoff-1789622142228270711.zip` (45,316 bytes).
- SHA256: `baeea6415cfa4e27d94ae959b1a739fc36622df82d9026822bbcbfce5585eb67`.
  Matches the user's Colab output. Safe paths, permitted member types, size limits
  and all 17 file checksums validated before extracting to a new directory.
- Code: clean `c15ad0db40f410cb6b173733912ace4de9c82bba`; source hash
  `b90643442b2e5fbd40400e0234e781820d51f9653e0a42b47c2836147e56a6e8` matches local code.
- Configuration: `configs/smoke/qwen3_8b.yaml` including defaults, hash
  `494d83bb40cc0095397741c6e1cc15720fff0da79c2f773c3a66c29dd7ab55f3`.
- Data manifest: `8d87db6ecb457c4821503cbec7da135c10feb19fe6b242186202e254e080c810`;
  two ARC-Challenge and two original English LogiQA validation tasks, seed 1729.
  Recorded source revisions/checksums match repository loader constants. No training
  or final-test split was run; no original dataset files were downloaded in this review.
- Model: Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, snapshot
  `e65c43f2b6abd7dc95bb51ce8d72c0c9c278120b1d4fd41d5f75e56e9d0fdc81`.
  The snapshot and template identity hashes recompute from recorded metadata;
  heavyweight model files were not independently rehashed locally.
- Independent samples from the unadapted base; no adapters, training checkpoint or
  DPO reference. BF16, SDPA, thinking disabled; temperature 0.7, top-p 0.8, top-k 20,
  greedy readout. Limits remain 4096 context / 256 packet / 64 final tokens.
- Environment: NVIDIA L4 (23,659,151,360 reported bytes), Python 3.13.15,
  torch 2.11.0+cu128, CUDA 12.8, transformers 4.57.6, peft 0.18.1,
  accelerate 1.12.0 and pyarrow 22.0.0. Preflight has no errors or warnings.

The 24 unique scheduled task/method/channel cells are all present: 20 applicable
trajectories plus four N/A synthesis/exchange cells. N/A cells have no calls and are
excluded from success denominators. There are zero runtime failures or missing cells.
Training and final evaluation remain deferred.

## Recomputed results

`analysis/metrics.json` reproduces exported `metrics.json` exactly. Counts independently
satisfy the coverage/utilization/construction identity, revision-availability identity,
and full failure identity including readout loss and post-revision construction.

| Method | Clean success | Early-advisory success | Exchange-corruption success |
|---|---|---|---|
| Debate | 2/4 | 0/4 | 2/4 |
| Independent synthesis | 2/4 | 0/4 | N/A |

For each family, clean debate/synthesis and exchange debate succeed on 1/2 tasks;
early-advisory methods succeed on 0/2. Clean successes are
`arc_challenge:Mercury_7014368` and `logiqa:eval-0414`; both fail under early advisory.
`arc_challenge:Mercury_7133648` and `logiqa:eval-0500` already fail cleanly.

Clean and exchange debate have coverage `c=2/4`, utilization `u=2/2`, construction
`k=0/2`, erasure `d=0/2` and repair `r=0/2`. Early debate has `c=0/4`, undefined
`u` and `d`, and `k=r=0/4`. Undefined rates remain null. The early attack succeeds
on 2/2 paired clean-correct tasks for each method; exchange succeeds on 0/2 for
debate. These denominators are too small for general robustness conclusions.

All 20 applicable teams have either zero or three initially correct members.
Harmful revision is 0/6 initially correct receiver opportunities in each of clean and
exchange debate. No wrong receiver has a naturally helpful peer, so helpful repair
is undefined, not a measured zero rate. No initially wrong receiver becomes correct
(0/6 clean, 0/12 early, 0/6 exchange). Initial correctness agrees across agents here;
this does not establish identical reasoning or an implementation problem with seeds.

All 96 main private/revision packets and 20 final answers have no recorded malformed,
length-limit or context-overflow failures. There are three packet abstentions and
two final abstentions under early advisory, all scored as failures. They are not
infrastructure failures and were not dropped from denominators.

## Probe and raw-trace review

The configured probe used one prespecified task, `arc_challenge:Mercury_7133648`,
across three conditions and three agents. Its 36 private candidates produced zero
eligible pairs across nine contexts, all missing a correct candidate. The nine
receiver contexts are ineligible for hold/repair sampling. All continuation credits
remain null, and no paired suffix or receiver candidate generations ran. Thus GPU
execution of eligible K=2 replay and revision-candidate sampling remains unverified.
No claim about LogiQA probe eligibility follows from this smoke.

The ZIP contains six deterministic sample records, including one N/A record and five
applicable failures; it does not provide a representative sample of all outcomes.
Five complete raw trajectories were independently rescored. For each sampled task,
the allowed canonical answer whose `TaskLabel` hash matches the manifest was unique;
this checks scoring against recorded label identity, not the source benchmark's
label quality. All four sampled task-input hashes match the data manifest.

The five trajectories contain 26 main calls; the sampled exchange record additionally
contains 12 alternative calls. All 38 stop at EOS. Available trace checks passed for
parsing, generation seeds, decoding parameters, model/template/context hashes,
unchanged private packets, identical sender-replacement bytes, synchronous receiver
inputs and revised-only debate readout. Missing pairs retain null outcomes and no
suffix calls. Example evidence:

- `arc_challenge:Mercury_7014368`, synthesis/early: the private answer follows the
  incorrect advisory option A while discussing sandbars (option C in the task).
  This is a validly parsed wrong answer, not a parser or label-repair failure.
- `arc_challenge:Mercury_7133648`, debate/exchange: all twelve exported alternatives
  choose D and are label-incorrect; each agent correctly records `missing_correct`.
- `logiqa:eval-0414`, debate/early: all three initial and revised answers choose B,
  with final failure. The attack changes initial coverage; it does not demonstrate
  destruction of an initially correct alternative during exchange.

Full raw shards and task-label files are omitted from the ZIP. All-cell metrics are
recomputed from evaluation records; only the exported raw subset can be independently
rescored or checked for protocol invariants. The current Drive contents and all
omitted probe candidates were not independently inspected. Original ZIP and extracted
files remain unchanged; derived checks are in `analysis/review_audit.json`.

## Measured cost and verification limits

The completed attempt used 152 calls, 47,652 input tokens and 6,954 output tokens,
including probes. Main trajectories account for 116 calls and 5,572 output tokens;
36 alternative calls account for the remainder. Reported time is 596.48 seconds
(0.1657 accelerator-hours), including a 57.00-second model load. Generation took
480.96 seconds, averaging 14.46 output tokens/second. Peak allocation was 15.44 GiB
and peak reservation 15.58 GiB. Notebook-wide setup time and Colab compute units are
not measured by these counters; full-cap throughput or larger-run cost cannot be
inferred reliably from these four tasks.

Base-model inference, normal collection/persistence and the handoff path are verified
on the reported environment. GPU adapter isolation, interrupted GPU resume, eligible
replay suffixes, receiver candidate sampling, training memory and length sensitivity
remain unverified or deferred. No evidence-backed code fix was identified. This run
contains no trained PACT result and provides no evidence of PACT improvement.

## Exact next Colab invocation

Keep the published commit. Set the complete parameter cell to:

```python
REPO_URL = "https://github.com/Soqoro/Pact.git"
GIT_REF = "c15ad0db40f410cb6b173733912ace4de9c82bba"
RUN_ID = "qwen3-profile-001"
PRESET = "profile"
STAGE = "profile"
SCRATCH_ROOT = "/content/pact-scratch"
PERSISTENT_ROOT = "/content/drive/MyDrive/PACT"
RESUME = False
MOUNT_DRIVE = True
PRIVATE_REPOSITORY = False  # True only if the repository requires authentication.
```

Run the parameter cell and subsequent cells. The same runtime/cache can be reused;
the new run ID leaves smoke artifacts intact. Equivalent stage command from checkout:

```bash
python -m pact profile --config configs/pilot/profile_20.yaml --run-id qwen3-profile-001 --scratch /content/pact-scratch --persistent /content/drive/MyDrive/PACT
```

The local dry-run check resolves config hash
`b2aed16773c4713c2b2260e472225af8886eb8da3df8d3683b730316b740c4dc`:
20 balanced validation tasks, ordinary debate across all three conditions, 60 cells,
and two prespecified probe tasks. Upper bounds are 420 main calls plus 432 probe
calls, and 96,000 main output tokens plus a conservative 110,592 probe-token bound.
These are ceilings, not measured costs. It is inference profiling, not training.

Return the new ZIP and printed checksum for review before the 80-item pilot. All smoke
artifacts remain reusable as provenance and diagnostics; none require regeneration.
Do not pool them with the larger profile as independent tasks, since task selections
overlap and both use the same seed. The review updates documentation only, so the
profile does not require a new code commit or push.
