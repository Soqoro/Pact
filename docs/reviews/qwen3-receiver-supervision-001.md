# Receiver supervision 001: context-collection audit

Result: **insufficient_context_support**, reproduced from the returned archive.
Collection completed; receiver-supervised training and comparison evaluation did not
execute. This is a context-sourcing result, not a learning failure or PACT efficacy result.

## Provenance and checks

- ZIP: `results_import/qwen3-receiver-supervision-001-handoff-1790063068160794241.zip`
- Verified SHA256: `93332881dbe83bd6dd975beaad6a678094c7f1164f9aa044674e1c06593f783b`.
- Source: clean `fd38b5e90bf6e5c648922405d46094abbc2449b2`, source hash
  `b179e7d109cef2533c87466c43de1bb3df612dca1118b5078b71cfbc14990cc7`;
  matches the local audited implementation before documentation updates.
- Study identity: `843b331d0e7ca51429afd42acc02ffa60f97972ff330e70b34499f7cdd4ef15f`.
- All 1,451 review members passed archive/checksum validation. The frozen plan
  reconstructs exactly from retained source data, initialization review and selection.
- All 96 source records and 672 attempted/committed calls were checked. Each source
  has three initial private packets and four prespecified focal private alternatives.
  Request hashes, task/prompt, actor, seeds, decoding, snapshot, token accounting,
  EOS/length rules and source-packet/call equality validate. No unresolved attempts.
- Rebuilding contexts from source packets reproduces `contexts.json` exactly.
  No training/evaluation artifacts or error records are present in this handoff.
- The archive records recovery-safe state and verified full snapshot
  `/content/drive/MyDrive/PACT/receiver-supervision/qwen3-receiver-supervision-001/snapshots/1790063068092177649-6c1eb3871652`.
  Local audit verifies the returned metadata; it does not independently access current
  Drive contents, initialization tensor bytes or prove reset/resume behavior.

## Support gate

| Partition | Hold tasks | Repair tasks | Minimum tasks per stratum |
|---|---:|---:|---:|
| Fit (64 tasks) | 2 | 2 | 8 |
| Held-out (32 tasks) | 0 | 1 | 4 |

The five contexts are two curated fitting hold contexts, two natural fitting repair
contexts and one natural held-out repair context. The two fitting strata reuse the
same two original tasks; they are not four independent source tasks. Empty balanced
weights and missing-stratum statuses are correct. This gate is independent of DPO
pair availability; no receiver completions or preference pairs were collected.

## Why support was low

Across all seven packets per task:

| Partition | Only correct valid answers | Only wrong valid answers | Both correct and wrong valid answers | No valid answers |
|---|---:|---:|---:|---:|
| Fit | 31 | 31 | 2 | 0 |
| Held-out | 20 | 9 | 1 | 2 |

“Only” describes the valid packets; a task may additionally have invalid packets.
Wrong answers need not be the same wrong option. Only three tasks supplied both
correct and wrong valid packets, despite the fixed extra donor draws.

| Packet source | Correct | Wrong, valid | Abstention | Invalid answer | Length limit |
|---|---:|---:|---:|---:|---:|
| Initial private (288) | 157 | 122 | 5 | 3 | 1 |
| Focal alternatives (384) | 207 | 165 | 8 | 4 | 0 |
| Total (672) | 364 | 287 | 13 | 7 | 1 |

651/672 packets (96.875%) were valid. There were no malformed or context-overflow
outputs. Parsing loss is present but does not explain the predominance of tasks
without both correctness classes.

The mixed tasks are:
- Fitting `arc_challenge:Mercury_SC_400986` (label A): initial B/A/B;
  focal alternatives A/B/A/B. Natural repair and curated hold are available.
- Fitting `logiqa:train-4035` (label C): initial B/C/C;
  focal alternatives B/B/C/B. Natural repair and curated hold are available.
- Held-out `logiqa:train-1916` (label C): initial D/D/C;
  focal alternatives D/D/D/D. Natural repair is available, but no answer-correct
  focal own state exists for hold. Zero held-out hold support is therefore expected.

Actual generation accounting: **672 calls, 159,313 input tokens, 34,766 output tokens**;
reserved output allowance consumed by these intents: 172,032 tokens. All calls are
private-phase source/donor collection, not receiver evaluation. Billed compute units
are unknown. No new optimizer updates, teacher-forced learning or three-arm accuracy
comparison is established by this bundle.

## Interpretation and next boundary

The bounded same-task actor-sampling recipe did not provide enough eligible
hold/repair histories. Removing the sampled positive/negative receiver-completion
requirement did not remove the separate need for legitimate own-state/peer contexts.
This does not establish that the supervised objective cannot learn or that changing
the inference prompt would help. The completed answer-only diagnostic remains closed.

Keep this run at its support stop. Do not lower minima, replace tasks, force answers,
add draws or proceed to cells 6–8. A possible next methodological proposal is a
separately reviewed source of authentic same-task donor packets, with explicit
curated provenance and unchanged labels/inputs rules. This is not implemented or
approved as an extension of this run; its availability and held-out separation must
be established before defining another experiment. No new GPU run is scheduled.
