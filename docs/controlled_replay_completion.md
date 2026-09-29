# Controlled replay implementation completion — 2026-09-29

This is software acceptance and a handoff, not another experiment or a positive
result. The complete path already existed and has been exercised again; this update
closes specific completeness, recovery, fixture and reporting gaps.

## Existing path and changed files

Existing production modules provide the actual base-only donor backend, immutable
pair acquisition, consistent own/peer substitution, K=2 replay and both controls,
frozen scoring, the masked solver, all three real adapter training arms, natural
four-system evaluation, artifact-bound training review, and auditable export/import.
`specialization_train.train_team` remains the production trainer, not a placeholder.
It preserves global coefficients, fresh arm/actor optimizers, all three sequential
adapters, optimizer-boundary resume, and exact effective initialization.

Changed implementation:
- `src/pact/training/controlled_private.py`: exact primary/order/calibration cell
  coverage before scoring. Incomplete, duplicate or unplanned cells fail before
  teacher-forced forwards rather than silently reducing support.
- `src/pact/training/controlled_private_plan.py`: reject existing child plans before
  importing metadata; no overwrite or implicit re-plan.
- `src/pact/training/controlled_specialization.py`: informative stage/accounting/
  review handoff; optional `--restore-timeout-seconds` using existing bounded worker.
- `tests/test_controlled_specialization.py`: additional completeness, immutable
  existing-plan, storage-only timeout, nonzero constant-credit/singleton and all-slot
  view tests, plus handoff assertions in the full mock round trip.
- `tests/fixtures/controlled_private_v1.json`: full 12 actor/sign/replicate views.
- `notebooks/08_controlled_private_specialization_colab.ipynb`: thin configurable
  storage deadline, default plan/execute=False unchanged.
- AGENTS, methodology, decisions/status, ledger, Colab runbooks, and this handoff.

No dependency upgrades, manuscript edits, commits, pushes, pretrained downloads,
GPU work, GPQA data access, or final-test use. Existing local audit edits and the
user-supplied consolidated brief are preserved.

## Evidence and limitations

Closed parent: 32 fit tasks / 64 rows / 1,216 committed generation calls; only five
natural eligible actor-row cells on two tasks. Retained candidates reconstruct to
361 valid correct, 405 valid wrong and two length-limited outputs. Missing pairs do
not establish initial-team agreement or lack of coverage. Parent stays closed.

The active child has later acquisition evidence: 75/75 committed calls, zero unknown
attempts, 22 complete synthetic pairs (11 ARC and 11 LogiQA), 132 eligible cells.
Its acquired support passes both eight-task gates. Some negative sample packets
have contradictory rationales. No rationale verification, human training approval,
reliable credit or scientific efficacy is implied. The supplied acquisition exposure
attestation is preserved; local artifacts cannot discover unrecorded external uses.

Existing acquisition ZIP SHA256:
`4e5e522894f8a67d6486c7ddc769e70843c3110000f0f6a9386e3af371378c52`.
Updated reader re-audited it successfully with exact parent/plan/journal/report
reconstruction. Real tensor checks are reported in Colab receipts; tensors are not
present in the review ZIP for an independent local model reload.

No newer controlled replay ZIP is present at this review. Real replay, frozen
scoring, PEFT/8B training, trained-checkpoint reload and development evaluation are
unverified. The optional tiny CPU test mocks PEFT export while exercising actual
PyTorch gradients/optimizer and checkpoints. Full PACT refresh/receiver/DPO/adaptive
attacks/final tests remain outside this study.

## Exact fictional example

The fixture is synthetic software evidence, never a requested model outcome.
Its shared positive packet is `{"answer":"A","justification":"Fictional controlled evidence."}`;
the negative packet changes only the answer to B. The `all_slot_views` field records
all three interventions, both signs and both K replicates. In each view, the
intervened own packet and both recipients' corresponding peer text equal the same
selected raw string; other packets and the early payload stay fixed. Four physical
node seeds match across actors/signs within each replicate. Generator support-option
metadata is absent from every receiver prompt. Original anchors remain unchanged.

The separate nondegenerate fictional solver example records full matrices; its
first row is approximately:

| Arm | actor0 | actor1 | actor2 |
| --- | ---: | ---: | ---: |
| Uniform | 0.333333 | 0.333333 | 0.333333 |
| Local | 0.333333 | 0.333333 | 0.333333 |
| Continuation | 0.985301 | 0.006639 | 0.008060 |

The fixture's training example stores the original prompt, full synthetic packet
plus EOS, and exact character-token completion mask (prompt 0, target/EOS 1).
This is not Qwen tokenization. Independent unequal-length/sparse-weight gradient
tests exercise actual causal shifting and global loss accumulation.

## Validation commands

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src:tests python -m unittest test_controlled_specialization.GuardTests -v
PACT_TINY_SPECIALIZATION=1 PYTHONPATH=src:tests \
  /home/gnoriq/miniconda3/envs/gmats/bin/python -m unittest \
  test_controlled_specialization.ControlledTinyTests \
  test_specialization.TinyNeuralTests -v
PYTHONPATH=src python -m pact.training.controlled_specialization audit \
  --source-bundle results_import/qwen3-controlled-specialization-001-handoff-1790442678000363226.zip \
  --sha256 4e5e522894f8a67d6486c7ddc769e70843c3110000f0f6a9386e3af371378c52 \
  --run-dir results_import/qwen3-controlled-specialization-001-completion-audit
```

The default full mock traverses acquisition, all replay controls, scoring,
assignments, all three mocked optimizer schedules and all four natural evaluations,
then reconstructs the exported bundle. Actual optimizer behavior is tested separately
by the tiny neural tests. Unsupported acquisition, flat credit, insufficient practical
contrast, interruption/resume and invalid evidence paths are explicitly exercised.

## Validation actually executed

- Full default suite: **221 tests in 535.001 s; 207 passed, 14 optional skips,
  zero failures**. Includes the full controlled mock pipeline and prior natural
  specialization round trip, failed-support/flat-credit paths, and legacy regressions.
- Final focused guards: **12 passed in 0.563 s**, including the all-slot fixture and
  final notebook edits added while the full suite was running.
- Optional tiny CPU neural tests: **3 passed in 9.873 s**. Independent accumulated
  gradients with sparse/unequal weights and target lengths, production optimizer
  isolation, and exact interrupted/resumed three-adapter updates.
- Real acquisition ZIP audit: passed, with original plan and 75-call accounting
  unchanged; no scoring/training/evaluation evidence invented.
- CLI help, notebook compilation/empty outputs, and `git diff --check`: passed.

Logs: `/tmp/pact-controlled-completion-suite.log`, `/tmp/pact-completion-guards.log`,
`/tmp/pact-completion-neural.log`, `/tmp/pact-completion-import.log`.
No failing run was concealed; these executions reported no failures.

## Active Colab run: exact identities and stages

Use the existing pinned revision `e719c088425b4986d1ad63beb0623779269c9547`
for the active plan `fb554a12c60da2d354606f8fb1f5d5c6894321adb47df4de96940e51256432af`.
Do not pull a future commit into this active run or recreate its plan. Source checks
remain strict; this completion update introduces no migration exception.

Full mount/checkout/install/restore cells and the timeout workaround are in
[the Colab runbook](controlled_private_colab.md). Required artifacts:

```text
Parent ZIP:
/content/drive/MyDrive/PACT/specialization/qwen3-specialization-contrast-001/bundles/qwen3-specialization-contrast-001-handoff-1790416052208683365.zip
Parent SHA256:
555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f
Preparation weight snapshot:
/content/drive/MyDrive/PACT/actor-preparation/qwen3-preparation-120-001/training/snapshots/1789930640656395583-479df47c14d9
Local restored preparation export:
/content/pact-scratch/actor-preparation/qwen3-preparation-120-001-inference
Active local child:
/content/pact-scratch/controlled-specialization/qwen3-controlled-specialization-001
Full durable child snapshots:
/content/drive/MyDrive/PACT/controlled-specialization/qwen3-controlled-specialization-001/snapshots/
```

After setup and verified latest restore, run individually:

```python
PLAN_HASH = "fb554a12c60da2d354606f8fb1f5d5c6894321adb47df4de96940e51256432af"
assert digest(read_json(RUN / "plan.json")) == PLAN_HASH
H = ["--plan-hash", PLAN_HASH]
GPU = ["--execute", "--initialization-root", INITIAL, "--cache-dir", SCRATCH / "cache"]
study("replay", *H, *GPU)
```

```python
assert (RUN / "replay_complete.json").is_file()
study("score-assign", *H, *GPU)
study("export", *H)
# STOP FOR REVIEW; upload the printed handoff ZIP and SHA256.
```

Only after explicit artifact-bound approval, select ONE arm per invocation:

```python
ARM = "controlled_uniform_sft"  # separately local or continuation arms
study("train", *H, *GPU, "--arm", ARM, "--review", REVIEW_FILE)
# An interrupted SAME arm requires --resume; never reset its directory.
```

The other arm names are `controlled_local_specialization` and
`controlled_continuation_specialization`. The runbook gives the exact review JSON
contract; reviewer fields must reflect an actual decision, never a fabricated pass.
After training authorization/completion, evaluate each system individually:

```python
ARM = "frozen"  # or one completed trained arm
study("evaluate", *H, *GPU, "--arm", ARM, "--review", REVIEW_FILE)
study("report", *H)
study("export", *H)
```

A missing/unsafe snapshot, unresolved call/update, changed source/precision/model,
or mismatched bank/assignment blocks resume. A finished arm is not retrained.
`--stop-after N` pauses generation at committed boundaries; training interprets it
as new optimizer updates. Existing attempts consume the original budgets.

## Ceilings and return artifacts

| Stage | Generation calls | Reserved output tokens |
| --- | ---: | ---: |
| Acquisition | 128 | 32,768 |
| Primary | 3,072 | 638,976 |
| Order | 768 | 159,744 |
| Calibration | 80 | 16,640 |
| Four-system evaluation | 2,048 | 425,984 |
| Total | 6,096 | 1,274,112 |

Frozen answer/packet scoring caps are 192 each, separate from generation. Training
caps remain 32 steps/actor, 96/arm, 288 total. These are ceilings, not time estimates.
Support requires eight tasks and eight multi-eligible tasks. Contrast requires
mean task L1 at least .10 and eight tasks individually at least .10; neither
passing gate implies reliable credit. Training requires the separate review.

After replay/scoring, return the metadata handoff ZIP and SHA256 containing donor
attempts/pairs/support, replay cells, three assignments, transform, contrast,
seed/order/calibration diagnostics, pretraining decision, resource usage and handoff.
After separately authorized training/evaluation, return the new ZIP containing
loss/target exposure, training summaries, natural per-task outcomes and paired
four-system comparisons. Full weights/optimizer state remain in verified Drive
snapshots; ZIPs are not tensor backups. Preserve all earlier bundles.
