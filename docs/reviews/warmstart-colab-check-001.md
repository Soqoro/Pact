# Warm-start Colab preparation — 2026-09-18

All 81 tests pass with the previously authorized tiny CPU neural checks enabled.
The default dependency-free suite passes 78 tests and skips its three explicitly
optional neural checks. Logs and version/source identities are retained in
`results_import/warmstart-colab-check-001/`; hashes are recorded in the
[experiment ledger](../experiment_ledger.md).

The tiny neural test now enables non-reentrant activation checkpointing, matching
the production launcher's mode. Exact resumed parameters/loss logs, dropout RNG,
frozen backbone/inactive adapters and reference export/reload still pass. It uses
a locally initialized one-layer Qwen model, not downloaded Qwen3-8B weights.
PyTorch is the existing isolated 2.9.1+cpu build with Transformers 4.57.6, PEFT
0.18.1 and Accelerate 1.12.0. Model hubs are offline; CUDA is unavailable.

Five new tests check notebook execution opt-in, a checksummed metadata-only review
ZIP, complete fixture checkpoints restored through the storage subprocess,
corruption and path traversal rejection before destination publication, and
persistence timeout/retry that cannot erase a training failure. Missing checkpoints
cannot claim a recoverable snapshot. Fixture tensor files contain explicit test
bytes; these persistence tests do not claim neural or real Drive verification.

The new notebook defaults to planning only. Setting `EXECUTE=True` runs one
optimizer update on four of the fixed 12 training tasks, then builds a local review
ZIP before persisting full checkpoints. The complete recipe remains nine updates
and 36 examples across three adapters. Return the first handoff before expanding
execution. The ZIP excludes tensor payloads: keep the whole verified Drive run
object store for recovery. Exact-snapshot restore and persistence-only retries have
independent configurable deadlines. [Instructions](../warmstart.md#colab-execution-and-recovery).

Real Qwen3-8B BF16 GPU training, memory fit, actual tokenizer training preflight,
GPU optimizer resume and Drive checkpoint throughput remain unverified. No final
model evaluation or PACT improvement claim is supported by this CPU check.
