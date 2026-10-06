# Benchmark breadth v1

Implemented for the 6 October 2026 [update](PACT_Codex_Benchmark_Expansion.md).
This is clean development inference, not trained PACT or an official leaderboard
submission. No new model outcomes exist locally. Historical studies and manuscript
placeholders are unchanged. There is no support gate or automatic follow-up run.

## Frozen experiment

The completed heterogeneous parent plan is
`b972e06e3b8e69f8e53053d238b7fa7f04c1ddb331654b7555262021d47a506f`.
The runner checks its entire four-model registry against that parent's hash.

| Key | Official model | Revision |
|---|---|---|
| Q | Qwen/Qwen2.5-7B-Instruct | a09a35458c702b33eeacc393d103063234e8bc28 |
| L | meta-llama/Llama-3.1-8B-Instruct | 0e9e39f249a16976918f6564b8830bc894c89659 |
| M | mistralai/Mistral-7B-Instruct-v0.3 | c170c708c41dac9275d15a8fff4eca08d52bab71 |
| R | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 |

No adapters or previous training checkpoint is loaded. Native tokenizer, template,
EOS set, BF16/SDPA and one resident model are inherited from `backends.native`.
Packet sampling remains temperature .7, top-p .8, top-k 20; readout is deterministic.
The existing fixed Llama template date and non-thinking Qwen3 readout remain fixed.
Only the declared context/output profile changes. Every rendered request is
tokenized with its recipient tokenizer. Overflow stops that dataset; no truncation,
retry at a smaller cap, model fallback, or replacement task is allowed.

Seed 20261006 is namespaced by dataset, partition, group/stratum and request node.
Each task has three private draws from each family. QQQ/LLL/MMM reuse their three
draws; QLM uses the same balanced six family/slot permutations as the parent,
with family F's replica j at slot j. Nine packets must be frozen before delivery.
Corresponding physical family/replica revision seeds match across teams.

Phase A generates only these nine packets. Phase B is a separate invocation for
the four cores, using the exact saved bank: twelve revisions, four syntheses of
private packets, four readouts of revised packets, one task-only readout. Revisions
see their own original packet and original peers, never another revision.

| Dataset | Tasks | Packet/final/context | A calls / reserved tokens | Additional B calls / tokens |
|---|---:|---|---:|---:|
| MMLU-Pro | 140 | 512 / 64 / 8192 | 1,260 / 645,120 | 2,940 / 940,800 |
| MuSR | 90 | 512 / 64 / 8192 | 810 / 414,720 | 1,890 / 604,800 |
| MATH-500 | 100 | 1024 / 1024 / 8192 | 900 / 921,600 | 2,100 / 2,150,400 |
| MBPP+ | 100 | 1024 / 1024 / 8192 | 900 / 921,600 | 2,100 / 2,150,400 |
| New GPQA | 32 | 256 / 64 / 4096 | 288 / 73,728 | Not authorized |
| LiveBench requested slice | 100 | 1024 / 1024 / 16384 | 900 / 921,600 | Not authorized |
| Total | 562 | | **5,058 / 3,898,368** | **9,030 / 5,846,400** |

Portfolio ceiling: 14,088 attempts / 9,744,768 reserved output tokens. A smoke
uses the first two already selected tasks: 18 INCLUDED calls. Scoring CPU work,
input tokens, model loading and optimizer updates (zero) are separate counters.
Unavailable LiveBench does not transfer its allowance to another dataset.

## Sources, grouping and exposure

The exact source and evaluator checks are recorded in
[source verification](benchmark_breadth_sources.md). Real loaders use official
files, not remote dataset scripts. Source files, cards/notices and SHA256 receipts
stay in the private source cache. Prepared data contains only characterization
text/EvalSpecs, plus hash/ID manifests for all partitions. Bundles do not contain
the full benchmark source cache. Do not publish the source cache or private bundle.

Partitioning precedes inference. `characterization_dev`, `confirmation_locked`,
and `reserve_locked` are evaluation material; `training_allowed=false`. The CLI
rejects generation on locked partitions. No code automatically trains or exposes
confirmation/reserve answers to models.

Grouping preserves case/Unicode and normalizes whitespace in the public problem.
MuSR additionally unions narrative word-trigram Jaccard >= .9. The source inventory
retains every legitimate variant, including variants with different labels. One
SHA-ranked source ID per group is the inference representative, independently of
answers; **all siblings inherit its exposure partition**. This resolves the real
MuSR object-placement groups of four without splitting related narratives or
inflating the 30/domain quota. Groups spanning source strata are explicitly
excluded rather than assigned an arbitrary category. Quota shortfalls stop.

MMLU uses ten representatives per each of 14 actual categories in characterization
and confirmation. MuSR uses thirty per each of three domains in both. Math uses
largest-remainder subject/level quotas; small strata may receive zero, explicitly
recorded. MBPP uses 100/100/rest. GPQA validates the original immutable parent
partition against the official source and allocates from its protected pool only.
The parent 32 exposed and two exclusions remain separate from the child's nominal
32 characterization / 32 confirmation / 100 reserve.

`benchmarks exposure-index` merges the hash-only inventories of earlier prepared
datasets. Pass it to `prepare --exposure`: exact matches to earlier exposed OR
locked pools are unavailable to later selection. The notebook does this for other
prepared JSON files present on scratch. Restore those manifests before preparing
the next dataset after a reset. Joint fingerprints/flags make observed duplicates
visible; there is no claim of semantic decontamination or complete detection of
rewritten MATH/coding problems. Cross-benchmark reports are a vector, not pooled
independent evidence. Selection is never revised after outcomes.

## Response and evaluator contracts

`BenchmarkInput` is a separate, strict public type. Legacy `TaskInput`/A-D checks
are unchanged. Private EvalSpecs never enter messages, vote keys or revisions.

These are invented format fixtures, not benchmark results:

| Adapter | Public input example | Generated contract / private evaluator |
|---|---|---|
| MMLU-Pro | Choose the tenth token; options A-J | `{"answer":"J","justification":"..."}`; strict official index/letter mapping |
| MuSR | Full story: cube moved from room one to room two; where is it? | Same MCQ JSON; safe literal parsing and zero-based source mapping |
| MATH-500 | Compute one half plus one half | `... \boxed{1}`; pinned Math-Verify equivalence, no options or LLM judge |
| MBPP+ | Write `fixture_increment(x)` returning x+1 | One fenced Python block with full definition/imports; official base AND expanded tests |
| New GPQA | Invented four-choice chemistry question | MCQ JSON with deterministic shared source mapping; parent exposure validation |
| Native LiveBench | Invented task asking for TRUE/FALSE | Native task output, e.g. `TRUE`; pinned objective task dispatch, fractional score retained |

Math extraction accepts exactly one balanced final box, no fallback to intermediate
expressions. Math-Verify uses strict comparison, six-place floating rounding,
15-digit numeric precision, five-second parsing/comparison limits, no set/relation
coercion. Text answers use exact `\text{...}` or alphabetic-word matching. The
bounded scorer subprocess executes trusted parser code, never prediction text as
Python. Malformed/length-limited completions are task failures. Infrastructure
timeouts, missing evaluators and context overflow remain unavailable outcomes.

Python extraction requires one complete fenced block and valid Python syntax.
Syntax is only a format check; success requires the official EvalPlus full base
and plus suite with `fast_check=False`, minimum per-test time 1s and multiplier 4.
The official v0.2.0 record with an empty `{}` plus-input collection is retained and
deserialized by EvalPlus; tests are not manufactured. Passing finite tests is not
a proof of correctness. Code voting is N/A. Math voting is deliberately disabled;
exact expression disagreement is labeled as textual, not semantic diversity.

LiveBench dispatch follows the pinned official `play_a_match_gt` and its registered
objective scorers; unknown tasks fail readiness. Native score and full-credit
indicator are separate: 0.5 is not a correct answer. The requested release is
currently unavailable in the checked public inventories; older questions are not
a replacement. Changing the source/release requires a reviewed new frozen design.

Generated programs and LiveBench scorers run only via a dedicated Bubblewrap
worker after capability probes: separate user/PID/network namespaces, dropped
capabilities, read-only evaluator runtime, disposable writable work area, no
workspace/home/Drive mounts or inherited secrets, process/time/memory/file limits.
Limits: 120s wall, 100s CPU, 4GiB address space, 64 processes, 1MiB output file.
The probe tests host-file and loopback denial, nonprivilege, read-only runtime,
secret absence and resource limits. EvalPlus's Python guard is not the security
boundary. Host kernel/Bubblewrap security remains a runtime trust assumption.

This local host lacks Bubblewrap, so real isolation and expanded-test execution
are **unverified**. The functioning fallback exports immutable jobs and leaves
scores pending. Import binds task/test/response/evaluator/job hashes and retains
worker limits, package versions and receipts; hashes are not remote attestation.
Use a trusted isolated evaluator. Never manually invent an `enforced` receipt.
Pending imports do not change or rerun generation. An isolated preflight can check
the first official MBPP canonical solution without any model call; otherwise
generation requires explicit `--allow-pending-scoring`.

## Analysis and recovery

Metrics reuse the existing heterogeneous decompositions: N0, coverage, individual
family/member accuracy, selected-best gain, joint failure, mixed valid support,
unique coverage, pairwise rescue, and gold-free MCQ voting. QLM is compared against
EACH homogeneous team. Math string disagreement does not establish mathematical
disagreement; code answer disagreement/voting are N/A. Native partial scores are
reported separately as mean candidate score and oracle-best-candidate score.

Phase A has null communication metrics. Phase B adds N0-to-N1, hold/repair,
erasure/new availability, utilization/construction, actual private/revised readout
loss events, and paired synthesis/debate outcomes. Coverage minus accuracy is not
treated as an ignored-answer count. Missing scorer evidence never becomes zero
correctness. Complete-case estimates and intended-cohort bounds remain separate.
MMLU/MuSR report macro and micro aggregates. Paired group bootstrap samples within
strata, recomputes selected maxima, and labels degenerate intervals inconclusive.

Attempt journals, immutable dependency files, native identities, full token/call
accounting and explicit A/B caps guard resume. Unknown dispatch windows remain
unsafe even when a partial report reconstructs. Compact ZIP/receipt snapshots
reuse existing bounded storage; latest-only restore cannot fall back to an older
safe prefix. Use `--stop-after` for bounded **new** calls in an explicit family
stage when more frequent durable boundaries are needed. A reset during a stage
can still lose work and leave the latest durable snapshot unsafe.

Private and sanitized bundles are distinct. Only the private archive supports
offline reconstruction; sanitized summaries contain no raw questions, answers,
prompts, continuations, hidden tests or decodable token arrays. Review before
publishing. Models/weights are not bundled. Local CPU mocks are labeled fixtures;
every new dataset's GPU behavior remains unverified until an actual return audit.
