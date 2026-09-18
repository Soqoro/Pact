# Bounded clean-answer warm start

The warm-start implementation includes sequential updates to three LoRA adapters,
optimizer-boundary checkpoint/resume and frozen reference exports. **Tiny CPU neural
verification now passes**: all 81 tests pass with model tests enabled, including
exact resumed weights/losses, adapter isolation and frozen export/reload.
Qwen3-8B GPU training and memory fit remain unverified.
[Execution evidence and limits](reviews/neural-cpu-check-001.md).
Full PACT `train` and `collect-bank` remain unimplemented.

## Review the plan locally

```bash
python -m pact warmstart \
  --config experiments/warmstart_engineering.json \
  --data-dir results_import/training-data-001/engineering-12 \
  --run-dir scratch/warmstart-engineering-001
```

Without `--execute`, the command verifies the frozen training data and emits the
plan. It does not import torch, download a model or create the run directory.
If using a freshly prepared data directory, pass that path instead; its manifest
must match the pinned hash. See [training-data preparation](training_data.md).

The included recipe pins manifest
`2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e`:
12 official training tasks, six per family. Each of three adapters sees each task
once in a separately seeded deterministic order: three optimizer updates at an
effective batch of four, microbatch one. That is nine optimizer updates and 36
forward/backward examples in total. Full ordered task IDs are emitted in the plan.
The engine accepts only 2–32 tasks and at most one pass per agent; the 1,200-task
proposal manifest is deliberately outside this engineering path.

## Method and model boundary

This implements the proposal's common **clean supervised warm start**, using
answer-only targets because these source datasets supply no verified rationales.
The dedicated warm-start prompt requests exactly `{"answer":"A"}` with the
appropriate canonical ID; it does not ask for a justification and then silently
omit one. It is distinct from the later private/revision packet prompts. No rationale
is invented, and no sampled wrong answer is rewarded. This prompt-format choice
needs downstream validation; warm-start loss reduction alone cannot establish good
packet behavior, robustness, complementarity or PACT improvement.

Labels are accessed only to construct targets after the prompt is rendered. The
official pinned chat template runs with thinking disabled. Joint tokenization must
preserve the prompt prefix; one terminal EOS is appended and scored. Mean completion
NLL excludes prompt tokens. Overflows/boundary changes fail without truncation.

The real execution path uses the existing pinned Qwen3-8B backbone/revision,
one CUDA GPU, BF16/SDPA, FP32 LoRA parameters and non-reentrant gradient checkpointing.
There is no quantization, CPU offload or precision fallback. Three independently
seeded rank-16, alpha-32 adapters target `q_proj` and `v_proj` only: an explicitly
named engineering choice, not a claim that the proposal fixed these modules.
Dropout is zero in the included recipe. Initialization seeds are 1729/1730/1731,
with recorded derived initialization and optimization seed rules.

Use AdamW with constant LR 1e-5, betas (0.9, 0.999), epsilon 1e-8, zero weight decay,
gradient clipping at one, and `foreach=False`. Accumulate each example with weight
1/effective_batch. Only the selected adapter's LoRA A/B parameters require gradients
or belong to the optimizer. One optimizer is resident at a time; all three small
adapter parameter sets remain resident. Mode/gradient flags restore on exceptions.
Each update checks backbone gradient/parameter-version invariants and hashes inactive
adapter values. These runtime guards are supplemented by an optional tiny-model
test that compares actual backbone bytes; that check now passes on the tiny CPU model.

## Checkpoints and references

The engine saves step zero and every completed optimizer update in immutable
`checkpoints/step-NNNNNN/` directories. State includes all three adapters, the last
active AdamW optimizer, Python and torch CPU/CUDA RNG states, progress and loss logs.
The sample order is deterministic and separately hashed. No NumPy sampling or global
NumPy RNG is used. An interrupted accumulation restarts its entire optimizer step
from the last completed checkpoint; partial gradients are not committed.

Checkpoint tensors use safetensors; typed JSON retains integer optimizer keys and
tuple RNG states. There is no pickle/`torch.load` path. Files are hashed and flushed
before the final checksum inventory and directory publication. A missing/corrupt
step fails; resume never silently falls back to an earlier complete checkpoint.
Incomplete hidden staging directories are not completion markers.

Resume checks code/config/data identity before model loading, then actual pinned
model/tokenization/runtime identities and torch execution flags before state restore.
Changing length, targets, seeds, precision, model, runtime or source code requires a
new run. Matching RNG state does not promise bitwise GPU reproducibility across
different hardware/kernels; changed runtime fingerprints are rejected.

After all updates, export each adapter to `references/agent0`, `agent1`, `agent2`.
`references.json` names their immutable content hashes and warm-start role. Exported
tensor values are checked against the completed adapters; embeddings/base weights
are not exported. These files are separate from the mutable actor model and will
serve as frozen DPO references. This increment does not yet compute reference
log probabilities or connect a scored-bank collector to these snapshots.

## Execution gate and remaining checks

Actual model loading/training requires `--execute`; compatible continuation requires
`--execute --resume`. `--stop-after N` simulates interruption after N new committed
updates. Use scratch storage. Successful local updates are reported separately from
durable persistence (`persistent_copy_verified=false`) in the plain CLI. The new
[Colab notebook](../notebooks/02_warmstart_colab.ipynb) wraps it with verified snapshots
and a small review ZIP. Preserve the complete directory for resume.
If failure occurs before step zero is saved, use a new run directory.

The user-authorized tiny CPU model check has passed. Review the local changes and
publish a pinned code revision before profiling the bounded GPU path. The optional
test uses a randomly initialized
tiny Qwen with nonzero dropout and checks one-agent isolation, uninterrupted versus
resumed weights/losses with non-reentrant activation checkpointing, restored
optimizer/RNG state, and frozen export/reload:

```bash
PACT_TEST_NEURAL=1 python -m unittest discover -s tests -p test_warmstart.py -v
```

It requires torch plus the pinned Transformers/PEFT dependencies but no pretrained
weights or dataset downloads. The default suite skips it. Reference API behavior was
checked against the [pinned PEFT source](https://github.com/huggingface/peft/blob/v0.18.1/src/peft/peft_model.py),
not inferred from the current development release.

Remaining work: profile Qwen memory/throughput and verify GPU isolation/resume;
implement actual frozen-reference scoring and scored-bank collection; then implement
joint specialization/revision updates and their checkpoint lifecycle. No final-test
data is involved in this path.

## Colab execution and recovery

Open `notebooks/02_warmstart_colab.ipynb` after publishing the reviewed changes.
Fill `GIT_REF` with that full commit SHA. The old validation/replay commit cannot
run this training workflow. Use a fresh `RUN_ID="qwen3-warmstart-001"`, keep
`RESUME=False` and `STOP_AFTER=1`, and set `EXECUTE=True`. Run cells in order.
With the default `EXECUTE=False`, the notebook installs dependencies, prepares
training data and validates the plan, but never loads or trains a model.

The execution helper starts the CLI in a child process, streams a redacted log,
and releases its model allocations before persistence. Training prints each
microbatch's position and token count and each verified optimizer checkpoint.
The handoff records invocation wall time (including model loading), reported GPU
resources, all checkpoint metadata and tensor-file hashes. It first writes a
small local review ZIP; full tensors stay in the scratch run and verified Drive
object store. The review archive has its own `review_checksums.json` and
`HANDOFF.json` schema; the validation `import-bundle` command does not accept it.
Treat returned metadata/logs as untrusted data, and verify hashes before review.

The first run commits steps zero and one. Return the review ZIP before completing
the remaining eight updates. Following review, use the same commit and run ID,
`RESUME=True`, and `STOP_AFTER=None`. Recreate the exact data manifest after reset;
set `RESTORE_SNAPSHOT` to the full verified snapshot path from the previous handoff.
Restore verifies every object, checkpoint hash and the contiguous step sequence
before publishing a new local directory. It requires an absent destination and
never searches for an older snapshot. Clear `RESTORE_SNAPSHOT` when continuing an
intact scratch run. Resume still rejects changed source/model/runtime identities.

Snapshots retain all optimizer boundaries and can be much larger than the review
ZIP. The object store deduplicates identical file bytes across snapshots. Each
Drive operation has an independent 120-second default deadline and periodic
progress notices, including restore. If a healthy large copy needs longer, raise
`STORAGE_TIMEOUT_SECONDS` explicitly. After a copy timeout, use the notebook's
persistence-only retry cell; it never launches training. Keep the runtime and
scratch checkpoints until `persistent_copy_verified=true`; the small review ZIP
cannot recover tensor weights. Preserve the **whole** Drive `warmstart/<RUN_ID>/`
directory, including `objects/`, not just the selected `snapshots/` folder.
Abrupt runtime loss before a verified snapshot loses unsynced updates. A handled
training failure still produces a diagnostic ZIP; successful persistence does
not erase that failure. Failure before any complete checkpoint cannot claim a
recoverable snapshot and requires a new run ID.

CPU tests exercise local persistence/restore with fixture bytes, corruption and
path traversal rejection, timeout recovery and the notebook execution gate.
These are not evidence of Drive performance or real Qwen GPU training. The tiny
CPU neural resume check additionally enables the production non-reentrant
activation-checkpointing mode. Both real GPU training and GPU resume remain pending.
