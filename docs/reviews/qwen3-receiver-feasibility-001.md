# Completed broader receiver feasibility — 2026-09-20

The returned 24-task, 48-record experiment passes offline artifact review. All
472 generations complete within the frozen 912-call ceiling. There are **zero
hold/repair preference pairs**: every one of the 136 fresh receiver candidates
is correct, leaving no valid-wrong counterpart. This is different from the earlier
two-task bank, whose receiver candidates contained no correct answer. Neither
result establishes that the fixed four-candidate recipe supplies training pairs.

## Integrity and execution

Archive: `qwen3-receiver-feasibility-001-handoff-1789837104959632692.zip`,
2,068,798 bytes, SHA256
`d61cb9bb82895f09f146a83ac52a26d4fdad18238585fb0bcf4bd13034996a9f`.
All 1,004 safe archive members, 1,003 payload checksums and 1,522 inventory entries
pass. The 520 omitted call/record checksum markers reconstruct from original
payload bytes. Imported JSON is treated as data; no imported code executes.

Clean source commit `b3951fde181bb216130cb206fdf87e39fca87632`, executable hash
`57e1b6bf2a469e15bb7dcafde8f22126fb454c660b661ae9107eda8f2602a964`, matches the
reviewed local implementation. The production plan reconstructs from the audited
1,200-task pool and 12-task warm-start exclusion manifest. All 24 selected tasks,
labels, family/sender assignments, recipe and selection hashes match. The saved
model/runtime metadata matches Qwen3-8B BF16/SDPA, disabled thinking, the three
frozen warm-start actors and the pinned reported L4 environment.

Offline protocol reconstruction uses every saved call exactly once, with no model
loading or new generation. All 48 main trajectories, attack bytes/sites, private
and revised packets, synchronous delivery, base-readout requests, candidate
prompts/seeds, evaluator results and complete receiver records match. The saved
call journal verifies request hashes, token-array lengths, EOS, context limits and
sampling settings. The raw report recomputes exactly. There are no unresolved
attempts, omitted records, incomplete pools or unobserved receiver contexts.
Attack/readout-only token counts are retained metadata, not independently
retokenized; model logits and tokenizer decoding were not reproduced locally.

## Receiver outcomes

| Stratum | Eligible contexts | Distinct tasks | Candidates | Correct | Valid wrong | Pairs |
|---|---:|---:|---:|---:|---:|---:|
| Hold | 32 | 16 | 128 | 128 | 0 | 0 |
| Repair | 2 | 1 | 8 | 8 | 0 | 0 |

All 34 pools have four fresh candidates. None contains an abstention, invalid
answer, malformed output, truncation or overflow. Every missing-pair reason is
`missing_incorrect`. The other 110 of 144 original receiver contexts are
ineligible; they are retained and do not receive candidate generations.

Hold contexts: ARC clean 1, ARC exchange 17, LogiQA clean 0, LogiQA exchange 14.
They cover nine ARC and seven LogiQA tasks; agent counts are 8, 10 and 14.
The two repair contexts are clean ARC task `arc_challenge:Mercury_406916`, agents
0 and 1. There is no eligible LogiQA repair context, exchange repair context or
agent-2 repair context in this selection. Thus repair coverage is narrow even
before requiring positive/negative pairs.

These are conditional candidate counts, not 136 independent tasks or a general
100% receiver-accuracy result. Four correct samples do not establish zero
probability of a wrong continuation. Original main revisions are excluded from
candidate pools as specified; no negatives are fabricated from other prompts,
attacks, abstentions or main revisions.

## Main trajectories

| Family | Clean final correct | Exchange final correct |
|---|---:|---:|
| ARC Challenge | 9/12 | 9/12 |
| LogiQA | 6/12 | 7/12 |
| Total | 15/24 (62.5%) | 16/24 (66.7%) |

Initial team coverage is 16/24 in each condition; eight tasks have all three
private answers wrong. Initial individual correct counts are 15, 15 and 16 out
of 24. Clean helpful repair is 2/2 eligible original receivers; exchange has no
eligible helpful-repair denominator. Clean harmful revision is 1/46 initially
correct receivers; exchange is 0/46. Main final outputs include one abstention
per condition. Every generation stops at EOS; EOS does not imply correctness.

These descriptive training-split outcomes do not establish attack benefit,
held-out performance, a warm-start effect or PACT efficacy. The samples are paired
by task and were selected for feasibility, not a powered efficacy comparison.

## Resources and persistence

One recorded invocation: 336 main calls plus 136 candidate calls = 472, zero cache
hits, zero teacher-forced forwards and zero optimizer steps. Recorded input/output
tokens: 168,842 / 22,390. Reserved output allowance for attempted calls is 111,616,
below the frozen 224,256 maximum. All 472 calls have verified results.

Invocation: 1,812.534 seconds (30.21 minutes), including a 56.691-second model load
and task snapshots; final snapshot/ZIP operations are outside that timer. Summed
generation time: 1,620.704 seconds (27.01 minutes). Peak allocated/reserved memory:
16,739,545,600 / 16,890,462,208 bytes. Compute units are unknown; these figures are
not billing totals or proof of full-context memory fit.

The handoff reports verified snapshot
`/content/drive/MyDrive/PACT/receiver-feasibility/qwen3-receiver-feasibility-001/snapshots/1789837104902108384-c21c9fca326b`.
The user reports the final Drive bundle and matching outer checksum. Nested
handoff path/hash/size refer to the preceding local review ZIP, and its null
bundle field predates the final copy. The manifest's false persistence field
also predates verification; these staged fields follow the existing exporter.
The archive alone does not independently verify current Drive contents or GPU
reset/resume. Preserve the full durable object store; this ZIP is not a resume
archive and contains no adapter weights.

## Decision and next gate

Apply the frozen `no_pairs` decision. Neither stratum passes the engineering gate;
there are no candidates for the proposed follow-on reference-scoring check.
Close this bounded run without more sampling. Full revision optimization remains
unsupported; no training-pair export, objective change or paper efficacy claim
follows.

The next useful local review is the selection's context support and candidate
outcome distribution: correct private answers mostly agree, repair contexts are
scarce, and every eligible sampled pool is all-correct. Compare this with the
prior all-wrong/abstaining receiver pools before proposing any new experiment.
Any changed selection, prompt, attack, sampling policy or query budget must be
recorded as a separate design; do not expand this run until pairs appear.

Original bytes: `results_import/qwen3-receiver-feasibility-001-review/`.
Reproducible audit, metrics and recomputed report:
`results_import/qwen3-receiver-feasibility-001-analysis/`.
This review changes documentation only. No executable change, suite rerun, GPU
execution, model/data download or final-test access was needed locally.

Follow-up: the [local support review](receiver-support-review-001.md) now explains
the observed context scarcity and records the next proposed bounded control.
It uses existing artifacts only and changes none of this run's results.
