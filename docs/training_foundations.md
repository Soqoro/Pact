# Local learning foundations and training-data plan

This is the first local increment of Milestone 3: scored-bank validation, masked
assignment, preference construction, reference-score storage and loss calculations.
The foundations check does **not** execute model training. A subsequent bounded
[warm-start implementation](warmstart.md) now passes tiny CPU neural checks, with GPU verification pending;
`collect-bank` and full PACT `train` still fail with `not_implemented`.

The returned Qwen replay check verified 13 private-packet pairs and 52 suffix
branches, but yielded zero receiver preferences in 16 eligible contexts.
[That validation evidence](reviews/qwen3-replay-check-001.md) cannot be reused as
training examples or treated as a reason to manufacture wrong completions.

## Run the CPU increment

From the repository root, after the usual editable install:

```bash
python -m unittest discover -s tests -v
python -m pact training-check --output-dir scratch/training-foundations-001
python -m pact assign \
  --bank scratch/training-foundations-001/bank.json \
  --output scratch/training-foundations-001/assignments-recheck.json \
  --allow-synthetic
python -m pact build-preferences \
  --bank scratch/training-foundations-001/bank.json \
  --output scratch/training-foundations-001/preferences-recheck.json \
  --allow-synthetic
```

Alternatively prefix commands with `PYTHONPATH=src` without installing. Use a fresh
output path each time; commands reject existing output. No GPU, network or download
is involved. The generated bank and reference scores are explicitly synthetic.
The summary says `cpu_fixture_only_no_model_training`; this is not a scientific
result or trained checkpoint. Inputs are JSON, never pickle or executable traces.

## Scored-bank contract

Version-1 dataclasses in `src/pact/training/bank.py` define the exact schema;
`training-check` emits an example. Unknown fields and validation/test splits are
rejected. Synthetic processing requires explicit opt-in. The schema carries:

- Frozen actor, base, data-manifest, tokenizer, template and runtime identities,
  precision, context limit, EOS ID and three named warm-start adapter references.
- Per-row training task/source/label hashes, canonical answers, three initial
  correctness flags, answer NLLs and nullable replay credits/pair IDs. Missing credit
  requires a missing usable-pair ID. Evaluator fields never enter prompt construction
  in these functions.
- Receiver prompt bytes/tokens, agent and row identity, helpful/misleading evaluator
  flags, and up to four raw candidates with prompt identity, token IDs and stop reason.
  All candidates remain in the bank, including invalid outputs.

This validates supplied scored records, **not source authenticity**. It cannot prove
that a hash names an official training source, supplied tokens match a tokenizer,
replays were valid, or peer helpfulness flags are accurate. The future collector
must audit those claims against immutable tasks, deliveries, tokenizer output and
replay traces. Relabeling arbitrary data as `training` is not supported. There is no
validation-handoff conversion. Base targets and sampled positive packets still need
a collector/trainer bridge before neural updates.

## Objective choices

Costs use `answer_nll - gamma * delta`, with gamma=1, tau=0.2, balance=0.1 defaults.
Default standardization fits population mean/std across **all agent cells of one
frozen training bank**, including rows lacking replay pairs, and stores statistics
with bank/actor hashes. Constant banks use scale one. `--nll-mode raw` preserves
unstandardized NLL. Neither mode fits transforms on validation/test records.

Masked exponentiated gradient logs objective history, tolerance, iteration cap/count,
convex first-order gap, feasibility and masked mass. The step cap `1/(tau + balance)`
avoids near-optimum numerical oscillation; backtracking remains available. A 1e-300
floor is used inside logarithms only. All-missing rows stay zero and leave assignment
optimization. Nonconvergence is saved in diagnostics and makes the CLI return nonzero.

One bank is the declared assignment batch here. Scarcity weights
`1/(1 + number initially correct)` have mean one over eligible rows. Specialization
coefficients include the global eligible-row denominator; base coefficients include
every row and agent. Adapter/microbatch slices must retain these coefficients,
without per-adapter renormalization. Missing cells are skipped before loss access.

Answer targets serialize as `{"answer":"A"}` with the gold canonical ID and no
rationale. The scoring convention is mean completion-token NLL including one
terminal EOS. Correct sampled packet NLL uses the same mean reduction; DPO uses
**summed** completion log probabilities. Joint tokenization must preserve the exact
prompt prefix. Changed boundaries and overlong sequences are rejected, never silently
truncated. Logits at t-1 score token t; prompt/right-padding positions are excluded.
Target tokenization appends exactly one EOS, included in the completion score.

Hold/repair follow initial receiver correctness and misleading/helpful delivered-peer
flags. Within one exact prompt, valid correct/incorrect candidates are ranked by same
32-token length bin, then closest length, then indices. Lengths include EOS; unmatched
pairs remain marked. Abstentions, malformed outputs and length-limited completions
cannot be negatives. Missing classes and ineligible contexts retain accounting.
Revision coefficients give half the mass to each stratum. If either is absent,
`full_revision_ready=false` and coefficients are null; a future trainer must stop or
run an explicitly named ablation. One pair per stratum is only structural readiness,
not evidence of adequate coverage.

Reference-cache keys include exact text/tokens, attention/completion masks, agent,
warm-start adapter, base/tokenizer/template/runtime identities, precision, EOS policy
and sum reduction. Scores are checksummed and immutable; missing entries raise with
no base/current-actor fallback. The cache stores supplied scores, not model inference.
The future scorer must load and verify actual frozen warm-start weights and execution
identity. Optional PyTorch wrappers detach reference scores and return differentiable
completion sums/DPO losses; their CPU gradient/reference-detachment test now passes.

## Training-data collection plan

1. Completed in the next local increment: separate train-only loaders for the pinned
   ARC-Challenge and original English LogiQA releases, with verified file hashes,
   schemas and counts. Existing validation entry points stay validation-only.
   [Commands, source evidence and limits](training_data.md).
2. Frozen 12-task engineering and 1,200-task proposal selections now include complete
   train/validation ID, exact-content and lexical near-copy screening. All exclusions
   are logged; semantic paraphrases remain unaudited. No final-test files were accessed.
   Future attack, replay, packet and preference derivatives must inherit task splits.
3. Retain the proposal's 1,200-task balanced warm-start and 300-record/three-refresh
   schedule as unexecuted study targets. Before a small neural check, publish a
   bounded train-only subset, exact IDs, seeds/bootstrap orders, clean/attacked
   allocation, uniform/sparse-support mixture and call/token budget. Freeze choices
   before inspecting eligibility and give compared methods the same bank budget.
4. Warm-start three adapters, hash immutable reference copies, and collect each bank
   under one frozen actor snapshot. Save prompt/candidate/peer origins, same-task
   helpful-message evidence, attacks, paired seeds, raw outcomes and answer scores.
   Independently validate tokenization. Natural peers and curated training-only
   same-task insertions require separate provenance/reporting; this plan does not
   prescribe a curated insertion for the next run.
5. Keep the existing four-candidate cap and K=2 for an initially bounded feasibility
   design. Report candidate validity, pair eligibility, missingness and length
   matching by stratum, agent and family. Inspect the fixed bank once; do not loop
   until both classes appear. Further collection requires a new recorded train-only
   design/budget. Missing strata prevent full-revision claims. Rows without replay
   or preference pairs retain eligible ordinary answer supervision.

## Remaining Milestone-3 gates

Train loaders and exact/lexical manifest audits are now CPU-verified. The bounded
warm-start optimizer, immutable exports and checkpoint/resume are implemented, with
control-path and tiny CPU neural checks passed. Before full GPU training:
scored-bank collector, real reference scoring, joint specialization/revision updates,
and GPU isolation/resume checks. Profile training memory in a separately pinned, bounded
Colab configuration. Inference memory does not establish training fit. A new commit
is needed before that invocation; full training and final tests remain deferred.
