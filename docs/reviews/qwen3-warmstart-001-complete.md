# Completed bounded warm start — 2026-09-19

The returned handoff passes its local metadata audit. The run resumed from update
one, completed updates two through nine, and exported three frozen warm-start
adapters. Colab reports successful verification of the full durable snapshot and
handoff ZIP. This completes the 12-task engineering recipe, not full PACT training
or an effectiveness evaluation. No additional warm-start invocation is needed.

## Integrity and continuation

Archive `qwen3-warmstart-001-handoff-1789796424401226566.zip`: 126,895 bytes;
SHA256 `417682b7868231c4103ae4a324d4213263b9308aaf97dfecc7c178191ad587be`
matches the user's supplied output. All 32 members pass path/type/size/uniqueness
checks and all 31 checksummed payloads match. The run inventory lists 44 files;
13 tensor files and the generated model-card README are deliberately omitted.
The reported complete file inventory totals 1,565,774,671 bytes.

Imported originals remain in `results_import/qwen3-warmstart-001-complete-review/`.
The local CPU audit and derived report are retained in
`results_import/qwen3-warmstart-001-complete-analysis/{audit.py,audit.json}`.
Archive contents were treated as data, never executed.

Source remains clean `a277794d271720665d57308cc15f3122f1934e27`, with unchanged
source/config/data/model/runtime/execution identities. The original `run.json` and
12 tokenized examples match the first handoff exactly. All prompts and targets
reproduce from the locally verified training data. Stored tokens/masks/EOS/lengths
pass structural checks; independent tokenization was not rerun.

Checkpoints zero and one retain byte-identical metadata and the same recorded
tensor hashes/sizes as the first handoff. All ten checkpoint metadata records
(steps 0–9) have contiguous progress, matching identities and matching cumulative
log prefixes. Each names all 432 adapter parameters; steps 1–9 each retain 144
AdamW parameter states for the expected agent, configured optimizer settings and
Python/CPU/CUDA RNG references. Step one and its loss/task log are unchanged.
The resumed invocation records `resume=true`, `stop_after=null`, and exactly
32 microbatches for updates 2–9, in the fixed task order. Across both invocations,
three agents each receive all 12 tasks once: 36 examples and 216 completion tokens.
The final status is `warmstart_updates_complete`, nine updates, exit code zero.

## Frozen references

The reference manifest binds all three exports to the same identity and final
step nine. Their configs match rank 16, alpha 32, zero dropout, q/v targets,
inference mode, causal-LM LoRA and the pinned base snapshot. Each exported weight
file is reported as 30,690,184 bytes, with a different SHA256. The combined
config/weight hashes reproduce from the run inventory:

| Agent | Frozen adapter hash |
|---|---|
| agent0 | `6ed4066c0116420e6e7b3fec9301ccda55b6d7a4eb43ff446db3fad6c52c7dc5` |
| agent1 | `5ab0bf7fb4d27a4aeef0221002dde571e97851390efbb64ea310840efe30e3da` |
| agent2 | `3b483c7d1b61f43f0fc2ad73f238ec6547cf05c2c33f3daaf599ee97e83c2c71` |

The pinned exporter checks saved tensor values against completed actor adapters
before reporting success. This handoff supports that runtime execution result;
tensor bytes are absent locally, so independent tensor comparison, actual optimizer
values and adapter-change isolation are not established by this ZIP. Distinct
hashes alone do not demonstrate useful specialization. The exported config's base
path is a Colab cache path; subsequent reload code must load the pinned backbone
explicitly and attach the verified adapter, not assume that path exists elsewhere.

## Resource and persistence evidence

The resume invocation reports 103.988 seconds including a 10.036-second model load,
local checkpoints and exports, excluding final persistence/ZIP generation. Combined
with the first invocation: 228.251 seconds. Peak allocated/reserved memory for the
resume invocation is 15.891/16.254 GiB. Executed sequence lengths are 112–449;
this does not measure fit at the 4096-token cap or provide a length-sensitivity
profile. Compute units remain unknown. Both invocation logs are preserved.

All logged losses and pre-clipping gradient norms are finite. Losses span roughly
0.0032–1.1554 across different batches and agents; they do not constitute a
before/after learning curve or evidence of task accuracy improvement. The large
norms are pre-clipping values, with the configured clip threshold of one.

The enclosing receipt reports `persistent_copy_verified=true`; nested local
training status still predates persistence and remains false by design. Reported
verified final snapshot:

```
/content/drive/MyDrive/PACT/warmstart/qwen3-warmstart-001/snapshots/1789796424349439412-7eeb6af87200
```

The returned metadata and user log agree on successful persistence. Drive objects
were not independently reread locally. Keep the entire Drive
`warmstart/qwen3-warmstart-001/` directory, including its object store. The small
review ZIP cannot restore weights. The successful fresh-process GPU continuation
is not proof of bitwise equivalence to an uninterrupted GPU run; that paired
control was not executed. Restore following actual runtime loss remains unverified.

## Next development gate

Preserve this completed run; no further GPU execution or raw export is requested
now. Next is local implementation/testing of frozen-adapter reload and actual
reference-policy scoring, followed by a bounded train-only replay-bank collector.
The existing reference cache accepts supplied scores; it does not run a model.
Use the three pinned reference hashes above in a new future collection recipe.
Validate disabled-adapter readout and immutable reference/actor separation before
publishing another bounded Colab configuration. Never repurpose the selected
validation replay artifacts as training data or expand sampling until pairs appear.

The 12-task run is an engineering artifact. Full clean warm-start training, PACT
specialization/revision updates, outcome-based validation and final-test evaluation
remain separate future work. No paper result placeholders were filled.
