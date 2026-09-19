# First real warm-start update — 2026-09-19

**Follow-up completed:** the remaining updates and three exports now pass the
[final handoff review](qwen3-warmstart-001-complete.md). The resume instructions
below document the completed step; do not repeat this run.

The returned handoff passes its local metadata audit. One Qwen3-8B BF16/SDPA
optimizer update completed on agent0 and stopped at the requested boundary.
The wrapper reports verified persistence of the complete checkpoint tree and
handoff ZIP. This establishes the bounded execution path on the reported runtime;
GPU resume, the remaining eight updates and final reference exports are pending.

## Evidence checked

Archive: `qwen3-warmstart-001-handoff-1789795816803016271.zip`, 34,280 bytes.
SHA256 `060d1a115631a785c85749cd53f4fa1ca0f190d919e6b95d9ceeb2e5a73034ab`
matches the user's log. All 11 archive members pass path/type/size/uniqueness checks;
all ten checksummed payloads match. Imported originals remain unchanged in
`results_import/qwen3-warmstart-001-review/`. The executable CPU audit and derived
report are in `results_import/qwen3-warmstart-001-analysis/{audit.py,audit.json}`.
No archive content was executed.

Recorded source is clean `a277794d271720665d57308cc15f3122f1934e27`, source hash
`22b9dd8ed1662cd6ebd487a26445d46fa0b7ef90dace4eaae2ac3b1d94949eb1`, matching
the local tested code. Config hash
`631ab416524276da3798db7b2edecfe231d5f197d3fd54d886779acce4faf579` and train
manifest hash `2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e`
match the frozen recipe. The complete plan and all three task orders reproduce.
All 12 prompts and answer targets reproduce from independently verified local
training tasks/labels; masks, concatenated token prefixes, terminal EOS and lengths
pass. Actual tokenization was not independently rerun. No labels/evaluator fields
were added to the prompts. All prepared sequences contain 112–449 tokens.

Model identity matches the pinned Qwen3-8B revision and prior base snapshot;
thinking is disabled. Runtime fingerprint matches the previously reported L4
runtime, but this handoff does not separately include a fresh device-name/package
inventory. The base-model identity's unadapted condition describes the loader's
backbone; the warm-start recipe and checkpoint metadata separately identify adapters.

Step-zero and step-one metadata share the exact recipe/model/runtime/examples/order
identity. Each names 432 LoRA parameter tensors: three agents, 36 layers, q/v, A/B.
Step zero has no optimizer; step one names agent0 and 144 AdamW parameter states,
matching the configured learning rate, betas, epsilon, weight decay and foreach
policy. Both retain Python/CPU RNG metadata and one CUDA RNG tensor reference.
Checkpoint checksums match the handoff inventory. Tensor payloads are omitted:
92,052,992 bytes for step zero and 153,430,392 bytes for step one. Their contents,
actual weight changes, clipping outcome and optimizer tensor values cannot be
independently checked from this ZIP. Runtime freeze/isolation guards reported no
failure; the prior tiny CPU tests provide separate isolation evidence.

## Observed execution and limits

The four expected tasks are `logiqa:train-0252`, `logiqa:train-4689`,
`arc_challenge:Mercury_7001418` and `arc_challenge:MCAS_2004_5_13`.
Their logged sequence lengths are 320, 449, 127 and 139, with 24 completion tokens
in total. Mean completion NLL is 1.0178536289. Gradient norm is 11.9798793793;
the implementation reports the **pre-clipping** norm, with clipping configured at
one. This value alone does not indicate failure or prove learning improvement.

Invocation duration: 124.263 seconds, including model loading and local checkpoint
work, excluding final persistence/export. Reported model load: 55.798 seconds.
Peak allocated/reserved GPU memory: 15.777/16.010 GiB. This measures the four
executed sequences, not the full 4096-token cap or a general length-sensitivity
profile. Compute units were not recorded. Warnings in the log do not interrupt the
run; exit code is zero.

`interrupted_at_optimizer_boundary` is the intentional `STOP_AFTER=1` outcome.
The nested training status's `persistent_copy_verified=false` predates the copy;
the enclosing handoff receipt correctly records the later verification as true.
Reported durable snapshot:

```
/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/snapshots/1789795816767143719-d1a84cb6fab7
```

The archive validates that receipt, not an independent local reread of Drive objects.
Keep the whole Drive `warmstart/qwen3-warmstart-001/` object store. This ZIP alone
cannot restore the model. No final-test evaluation or PACT benefit is established.

## Previously authorized bounded execution (now completed)

Continue the same commit and run ID; do not change the recipe or repeat a fresh run.
In the existing Colab runtime, run:

```python
from pact.training.colab import execute

HANDOFF = execute(
    checkout=CHECKOUT, data_dir=DATA_DIR, run_id="qwen3-warmstart-001",
    scratch=SCRATCH_ROOT, persistent=PERSISTENT_ROOT,
    resume=True, stop_after=None, timeout_seconds=STORAGE_TIMEOUT_SECONDS,
)
print("Bring back:", HANDOFF["persistent_bundle"] or HANDOFF["path"])
print("SHA256:", HANDOFF["sha256"])
print("Verified snapshot:", HANDOFF["persistent_snapshot"])
if HANDOFF["exit_code"]:
    raise RuntimeError("Resume or persistence failed; keep scratch and return the diagnostic ZIP.")
```

This resumes the saved optimizer and runs eight remaining updates, ending at nine
and exporting all three frozen reference adapters. Return the new handoff for review.
The resume implementation rejects changed model/runtime/source identities rather
than adjusting settings. No duration promise follows from one update.

After a runtime reset, first rerun setup/data preparation at the same full commit.
Set `RESUME=True`, `STOP_AFTER=None`, `EXECUTE=True` and `RESTORE_SNAPSHOT` to the
exact path above, then run restore before execution. Restore requires an absent
local run directory. For an intact scratch run, leave `RESTORE_SNAPSHOT=""`.
If only persistence fails, use the notebook's persistence-only retry; keep the
runtime until durable verification succeeds. Full checkpoint copies are larger
than the small review ZIP and may need an explicitly increased storage deadline.
