# Source verification for benchmark breadth

Checked on 6 October 2026 using official repositories, APIs and data files. These
checks establish source/schema identities, not model performance. Raw benchmark
files were inspected outside the repository and are not committed.

| Source | Immutable revision / release | What was checked |
|---|---|---|
| [TIGER-Lab/MMLU-Pro](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro) | `b189ec765aa7ed75c8acfea42df31fdae71f97be` | Official test parquet, 12,032 rows; variable options, index/letter, category, cot fields |
| [TAUR-Lab/MuSR](https://huggingface.co/datasets/TAUR-Lab/MuSR) | `7c365b439a222150f317764d4f16ae6c96d7d94a` | Three CSVs: 250 murder, 256 object placement, 250 team allocation rows; narrative, choices, zero-based label |
| [HuggingFaceH4/MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500) | `6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be` | 500 test JSONL rows; problem/answer/solution/subject/level/unique ID |
| [Official MBPP+ release](https://github.com/evalplus/mbppplus_release/releases/tag/v0.2.0) | v0.2.0; asset SHA256 `af43697e8791c4c149bdfd6b489d8b5412507551ac20e28a439f650b8225db63` | 378 canonical expanded-test records; base/plus inputs, entry point, tolerance, canonical solution |
| [evalplus/mbppplus hosted view](https://huggingface.co/datasets/evalplus/mbppplus) | `b2d74c91837c3f2a20c1299ae98133cbe7cfa077` | Card/schema provenance; hosted schema differs from canonical asset, so **not** used as the expanded-test data authority |
| [Idavidrein/gpqa](https://huggingface.co/datasets/Idavidrein/gpqa) | `83022cefff930aea54f654c0b282e74b9eeda5c6` | Existing official loader/pin and historical manifest inspected; no new gated download locally; synthetic 198-row partition regression |
| [LiveBench](https://github.com/LiveBench/LiveBench) | `8f8e5c381a16e3f24257776edd53471fe86f8091` | Release registry includes 2026-06-25; native dispatch and addition/removal predicate inspected; public availability is a separate check |

Observed source-only grouping with the current rule: MMLU 11,637 eligible groups
after four cross-category groups are excluded, giving 140/140/11,357 representative
IDs. MuSR 564 groups (250/64/250), giving 90/90/384 representatives; all 756 source
variants remain classified. MATH 100/100/300, MBPP 100/100/178. These are metadata
checks, not executed benchmark runs. Actual runtime manifests also apply any
supplied prior cross-dataset exposure index and can stop on reduced support.

Official source asset hashes checked:

| File | SHA256 |
|---|---|
| MMLU test parquet | `0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8` |
| MuSR murder CSV | `ce19b6dc0b953f698e79528c72705804bc97e772a4303734808971f63ce233a7` |
| MuSR object CSV | `98cd17d2c9ea53664e274365e901c90dfcaa40d17547dfbd369f1cd26fd2a81c` |
| MuSR team CSV | `ddbef3bb61857a7cc3b73db62fac4605679e1b7ff4357d57fdfcf91f7caaa1f8` |
| MATH test JSONL | `35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132` |

Always use generated source receipts as the operational authority; do not hand-edit
an offline receipt. Loaders retain cards/notices, including GPQA's license file.
Upstream scorer installs retain their own licenses. No redistribution permission
is inferred from a successful download.

## Scorers

- [Math-Verify](https://github.com/huggingface/Math-Verify/tree/ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b):
  `ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b`, package 0.9.0, with
  latex2sympy2_extended 1.11.0, sympy 1.14.0, mpmath 1.3.0, antlr4 runtime 4.13.2.
  Installed into an isolated temporary venv and exercised on invented equivalence
  cases. VCS install hit an upstream SSH submodule fetch; the exact official commit
  archive installation succeeded. The worker verifies direct-url provenance and
  dependency versions before scoring.
- [EvalPlus](https://github.com/evalplus/evalplus/tree/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e):
  `26d6d00bb1fd0fa37f39c99d5290da67891d1c5e`. Reviewed
  `mbpp_deserialize_inputs`, `gen.util.trusted_exec`, `check_correctness`, special
  MBPP oracles and full base/plus semantics. Isolated official execution is not
  verified on this host. The worker checks package VCS provenance and records
  actual dependencies; the execution environment must be validated before use.
- [LiveBench native dispatch](https://github.com/LiveBench/LiveBench/blob/8f8e5c381a16e3f24257776edd53471fe86f8091/livebench/gen_ground_truth_judgment.py):
  same pinned source above, package name `livebench` (metadata version 0.0.4).
  `MatchSingle`/`play_a_match_gt` objective routing, failure status and fractional
  score handling inspected; fixture dispatch tested. Full runtime dependency and
  native scorer integration remains unverified, and generation remains blocked
  by missing verified release questions.

## LiveBench availability evidence

Pinned official HF repositories:

| Repository | Revision | Inspection |
|---|---|---|
| livebench/reasoning | `6fc6498a5dfba553f69f4413feabade1f1a2d384` | 200 rows, observed release dates in 2024 |
| livebench/math | `bb66571c8ccf32d3df9e6f48b920d3770ff4aacb` | 368 rows, observed release dates in 2024 |
| livebench/data_analysis | `31b9661ff678df9958e2f7fa228427f4c858c1a1` | 150 rows, observed release dates in 2024 |
| livebench/language | `3ada32a2e53d5e04e57fa503384cb85ce9116c40` | 190 rows, observed release dates in 2024 |
| livebench/coding | `a958549fdd8aa57be0a3fafe7b205ffc160ed5f4` | Revision verified; bounded local download was incomplete, content not verified |

The first missing category already prevents the specified five-category slice.
The loader writes `readiness.json` with `requested_release_unavailable`, checked
source hash/pin and observed dates, then stops without fetching the remaining
large files. It never substitutes a 2024 release. Its conservative proof rule
requires requested-release additions in each category before applying the official
retained-item predicate; this may reject a legitimate retained-only category until
an authoritative release inventory is reviewed. No arbitrary local export or
unreviewed mirror bypass is implemented. A newly available authorized official
release inventory needs a reviewed source-pin/proof update, not a retry with
fabricated dates. Other datasets remain independently usable.
