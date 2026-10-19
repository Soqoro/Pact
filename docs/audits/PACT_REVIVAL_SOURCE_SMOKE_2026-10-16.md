# Heterogeneous receiver revival: source smoke audit

## Evidence and verification

Run: `pact-heterogeneous-receiver-training-001`, allocation `arc400_logiqa560_v2`.
Pinned clean source commit: `3605dcf70cef4c12092b72231456fad8355b0492`.
Plan hash: `a8ee5cf50d0878dbe6fec8c36364e8b1469cc79c39afd66244b9ecf5f1e5bc71`.

Imported archive suffix: `1792154655706175740`.

- PRIVATE SHA256: `f500fd71fd9656bef5586d9d3ea38a3050f4f614a9422f26ca97c38164eb3729`
- SANITIZED SHA256: `be901a74f302a6fb7563c388054e41b6957aca2917c16d4ba59a7866b9759649`

Both archive hashes and every member checksum verified. Paths and duplicate/symlink
entries were checked before private extraction outside the repository. Sanitized
contents are summary plus handoff/checksum metadata; both summaries agree exactly.
The existing Journal validator accepted all call identities, seeds, token accounting,
rendered-context hashes and strict parser results. The report was independently
recomputed from the imported private records and exactly matched the supplied report.
Source validation accepted the 960 groups, exclusions, exact split quotas and 3/5
homogeneous probe blocks. Six calls correspond to the two fixed fitting smoke tasks,
with two calls per native actor. No local model calls or downloads occurred.

## Observed results

| Actor | Calls | Valid packets | Correct valid answers | Invalid packets |
|---|---:|---:|---:|---:|
| Qwen2.5 | 2 | 2 | 2 | 0 |
| Llama3.1 | 2 | 2 | 1 | 0 |
| Mistral | 2 | 1 | 0 | 1 |
| Total | 6 | 5 | 3 | 1 |

The invalid Mistral response is not valid JSON and stopped at EOS, not the length
cap. It remains invalid; no parser salvage, retry, task replacement or correctness
fallback. These are two fitting tasks, not independent model-performance estimates.
There is no receiver-learning or efficacy result.

Accounting: 6 attempted / 6 committed / 0 unresolved; 1,273 input tokens,
270 output tokens and 3,072 reserved output tokens. No training, scratch updates,
live evaluation or allocation probe has executed. The included six calls must be
reused in subsequent fitting collection, not regenerated.

All four official model metadata/access receipts are present. Q/L/M real native
private generation is now observed; R generation, adapter training and receiver
execution remain GPU-unverified. Recorded per-load peak allocated GPU memory ranges
from 14,570,021,376 to 16,135,936,000 bytes; this does not establish training fit.

## Download recovery

The archive records Mistral tokenizer recovery at the unchanged pinned revision:
Git pointer `029a2451811177349803d8a4789f6861a7afb0e0`, payload SHA256
`37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89`, 587,404 bytes.
The user verified the raw Git identity and pointer-to-payload chain in Colab before
cache installation. This audit confirms the receipt is present; the archive does
not include the external model-cache payload, so its bytes were not independently
rehash-verified locally. No model revision or parser was substituted.

## Disposition

Source smoke completed with one retained format failure. No outcome-support screen
requires replacing it. Next bounded engineering milestone: finish the fixed private
bank, acquire the fixed one-attempt attacks, build the shared supervised bank and
run the disposable 48-step/six-generation scratch check. Export and review before
main six-adapter training. This disposition is not an automatic GPU launch or
approval for Stage II or coupled training. Continue the existing pinned Colab source;
local audit documentation does not require migrating its frozen plan.
