# Tiny CPU neural verification — 2026-09-18

The user explicitly authorized the optional model tests. **All 76 tests passed,
zero skipped**, including the three previously skipped neural checks. No executable
source change was needed. This verifies the tested tiny CPU paths, not Qwen3-8B GPU
training, memory fit, or scientific performance.

## Environment and execution

Installed dependencies only in `/tmp/pact-neural-cpu`, a separate virtual environment:
Python 3.12.7 on Linux aarch64; PyTorch 2.9.1+cpu, Transformers 4.57.6, PEFT 0.18.1,
Accelerate 1.12.0, safetensors 0.8.0. `pip check` passes. The complete transitive
dependency lock and platform information are retained with the local evidence.
The ordinary project/base environment is unchanged.

Tests ran with `PACT_TEST_NEURAL=1`, `CUDA_VISIBLE_DEVICES=''`,
`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_DATASETS_OFFLINE=1`,
and OMP/MKL thread counts set to one. Before execution, the runner asserted
`torch.version.cuda is None` and `torch.cuda.is_available() is False`.
Package downloads occurred during environment setup; no pretrained model weights
or datasets were downloaded for testing. Models were initialized locally from configs.

The test runner completed in 12.707 seconds (12.797 seconds including evidence
bookkeeping). The equivalent invocation in the prepared environment is:

```bash
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
HF_DATASETS_OFFLINE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PACT_TEST_NEURAL=1 PYTHONPATH=src \
/tmp/pact-neural-cpu/bin/python -m unittest discover -s tests -v
```

## What passed

- Distinct LoRA adapters produce different logits from each other and from the
  adapter-disabled base readout. Inference restores the previously active adapter
  and leaves parameters frozen. The legacy fixture names one adapter `a`, which
  produces a PEFT naming warning; the warm-start export/reload uses `agent0` instead.
- Differentiable completion scores agree with the independent numerical reference.
  Prompt/padding gradients remain zero, a step improves target log probability, and
  DPO propagates policy gradients while detaching reference scores.
- Warm-start training uses a randomly initialized one-layer Qwen3 with hidden width
  16, vocabulary 32, two attention/KV heads, and rank-2 q/v adapters. Four synthetic
  token sequences supply two updates per agent, effective batch two, for six total
  optimizer updates. LoRA dropout is 0.2 and attention dropout 0.1.
- A second run stops after the first optimizer update. Fresh model/optimizer objects
  restore its checkpoint and finish the remaining updates. Every final parameter
  and the complete loss/progress logs match the uninterrupted run exactly.
- The active adapter changes; inactive adapter values and backbone values remain
  unchanged. All three adapters receive updates by completion. Gradient flags restore
  after the explicit failure path and are frozen after training.
- All three frozen exports match the completed adapter tensors and their content
  hashes. Reloading agent0 into a fresh base reproduces its adapter parameters.
  Repeated export verifies existing artifacts; a subsequently mutated actor is
  rejected instead of overwriting the saved reference.

## Evidence and limits

Evidence directory: `results_import/neural-cpu-check-001/`:
`tests.log`, `verification.json`, `requirements-lock.txt`, and `pip-check.txt`.
Test-log SHA256:
`be34118f9ca10d5eaaf5b8aa5a78f0ea0b413e4b5e989e8ac3e2d8e42813ea7b`.
Tested working-tree source hash:
`5762a58971732b16bb1729c7a70f8a5aaad3753ab0209627a2965068f8ed684b`,
based on commit `e79a9ab0da7b3801ba1ff488ddd974302768da2a` with local changes.

The tiny tests use CPU floating-point weights and fresh objects in the same process.
They do not execute the real model loader, BF16 CUDA training, non-reentrant gradient
checkpointing, real-tokenizer training preflight, GPU interruption/resume, or Drive
persistence. No 12-task Qwen3-8B run or full PACT training has occurred. Fixture losses
are software evidence and must not populate paper result placeholders.

Next: review and publish a pinned revision, then prepare the bounded 12-task Colab
memory/throughput check with verified persistence and a return bundle. The existing
Colab notebook remains a validation launcher. Real frozen-reference scoring,
scored-bank collection and joint PACT updates are still outstanding.
