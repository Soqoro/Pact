# Fixed-bank adjudication and rationale-only perturbation, v1

Implementation of [the explicit study brief](PACT_Codex_Fixed_Bank_Adjudication.md)
for `pact-adjudication-diagnostic-001`. This is an inference-only development
diagnostic, not trained PACT, a learned adjudicator, an adaptive attack, or final-test
evidence. The returned J8 two-task smoke is now verified; see the
[imported audit](audits/PACT_ADJUDICATION_SMOKE_2026-10-12.md). J8/MMLU-Pro clean is also complete; see its
[audit](audits/PACT_ADJUDICATION_MMLU_J8_2026-10-12.md). J8/MuSR is also complete; see its
[audit](audits/PACT_ADJUDICATION_MUSR_J8_2026-10-12.md). J14/MMLU-Pro is also complete; see its
[audit](audits/PACT_ADJUDICATION_MMLU_J14_2026-10-12.md). All four clean stages are now complete; see the
[complete audit](audits/PACT_ADJUDICATION_CLEAN_COMPLETE_2026-10-12.md).
Rewrite acquisition is complete with a frozen pool; see the
[pool audit](audits/PACT_ADJUDICATION_REWRITE_POOL_2026-10-12.md). MMLU-Pro/J8 victim execution is now verified; see its
[audit](audits/PACT_ADJUDICATION_MMLU_J8_VICTIMS_2026-10-13.md). MuSR/J8 victim execution is also complete; see its
[audit](audits/PACT_ADJUDICATION_MUSR_J8_VICTIMS_2026-10-13.md). MMLU-Pro/J14 victims are also complete; see the
[audit](audits/PACT_ADJUDICATION_MMLU_J14_VICTIMS_2026-10-13.md). All prescribed stages are now complete with returned GPU evidence; see the
[complete-study audit](audits/PACT_ADJUDICATION_COMPLETE_2026-10-13.md).
Completion does not authorize another study.

## Frozen evidence and estimands

The importer accepts only the exact completed PRIVATE MMLU-Pro, MuSR and MATH
bundles pinned in `adjudication_data.PARENTS`. It checks ZIP/internal hashes,
parent plan/source/model identities, journals/dependencies, complete A/B status,
and reconstruction of the old report. Every MMLU/MuSR MCQ call is independently
rescored with the existing parser/scorer. MATH joint/format statistics use its
recorded pinned Math-Verify scores; this phase does not rerun symbolic scoring.

All 140 MMLU-Pro and 90 MuSR characterization tasks retain their original option
mappings, group/stratum membership, QLM/QQQ sample bindings and anonymous slots.
No best-of-nine search or regeneration occurs. Parent selected-output evidence,
identities and request references are retained in the private bundle. No locked
cohort text is copied into the new bank. Training is forbidden; these tasks are
already development-exposed, never untouched final tests. MATH is offline only.

O0/O1/Y joint tables distinguish erasure, new availability, initially-covered
terminal loss, revised readout loss, and construction from either initial or
revised unavailability. Exact decompositions are checked. Construction can use
partial reasoning in wrong packets; it does not prove independent solving.
Up to eight revised-readout-loss and eight revised-covered-success tasks per
dataset form a fixed-hash, outcome-stratified PRIVATE human review pack. It is
not a prevalence sample; annotation fields default to `not_reviewed` and cannot
filter any inference cohort. Answer correctness does not verify a rationale.

## Inputs, models, and six clean modes

`FrozenCandidateBank` contains three stable c0/c1/c2 slots. `AdjudicationInput`
accepts only a public `BenchmarkInput` plus candidate views. `EvalSpec` is used
only offline. Family, raw provenance and correctness never appear in judge
messages. Existing safe_json escaping keeps embedded special role tokens as data.
Invalid, abstaining and length-limited packets become nonselectable
unavailable envelopes, with no answer salvage. Duplicate answers keep distinct
candidate IDs. Empty selectors produce a deterministic ABSTAIN without a call;
that is a known task failure, not infrastructure missingness.

| Mode | Candidate view | Decision space |
|---|---|---|
| task_only_free | None | Any original option or ABSTAIN |
| qlm_answers_select | Original QLM answer labels, no rationales | Selectable candidate ID or ABSTAIN |
| qlm_full_select | Original QLM packets | Selectable candidate ID or ABSTAIN |
| qlm_evidence_select | Same QLM packets; compare task-grounded disagreements | Selectable candidate ID or ABSTAIN |
| qlm_free_synthesis | Same QLM packets | Any original option or ABSTAIN |
| qqq_full_select | Original QQQ packets | Selectable candidate ID or ABSTAIN |

Every mode shares the same trust rule, 512 output-token cap and 8,192 total
recipient-context cap. JSON must have exactly `decision_basis` first (nonempty,
at most 160 whitespace-delimited words), then `candidate_id` or `answer`. No
fences, extra fields, duplicate keys, partial-prefix salvage or label-assisted
repair. Length-limited output is failure even if its prefix contains an answer.
Selectors cannot be correct without a correct selectable candidate; free solvers
can construct an answer absent from that set. Raw responses and decision bases
are private; reports retain invalid/wrong/abstention/length/missing distinctions.

- J8: pristine parent Qwen/Qwen3-8B @ `b968826d9c46dd6066d109eabc6255188de91218`.
- J14: official Qwen/Qwen3-14B @ `40c069824f4251a91eefaf281ebe4c544efd3e18`.
- Rewrite Q: pristine parent Qwen/Qwen2.5-7B-Instruct @ `a09a35458c702b33eeacc393d103063234e8bc28`.

J14 was resolved through the [official model metadata](https://huggingface.co/api/models/Qwen/Qwen3-14B)
on 11 October 2026 without downloading pretrained weights. Both judges explicitly
pass `enable_thinking=False` through native templates. All three new call roles
are greedy, BF16/SDPA, one CUDA GPU, one resident model, no adapters, offload or
quantization. Weight bytes are verified against official pinned metadata before
loading. Metadata-only preflight is distinct from verified loaded weight identity.
The rewrite generator's greedy decoding is a prespecified engineering choice;
there is no alternate sample or retry. Native EOS/end-of-turn IDs are preserved.

New 512-token readouts are deliberately different from historical 64-token
readouts. Only the six new matched modes support the new comparisons. Increased
capacity or output budget is not a new algorithmic gain.

## Fixed perturbation pool

Eligibility is reconstructed before new outcomes: original QLM has a valid correct
and valid wrong packet. The real imported counts must be exactly 42 MMLU + 38
MuSR; mismatch stops planning. A hash of seed 20261011, task and candidate ID
chooses one wrong candidate. A separate fixed hash orders the four attack styles
per task; it never uses judge outcomes. Corresponding clean/attacked judge seeds
match; cache identities include the complete prompt and perturbation identity.

One rewrite attempt per eligible task/style: argument_pressure,
claimed_verification, claimed_consensus, claimed_independence, ordinary_rephrase.
Q sees only the task/options and assigned candidate answer/original justification,
plus the style instruction. No peers, hidden gold, correctness tags or feedback.
The host accepts exactly one nonempty bounded `justification` string with a
complete EOS output; field additions, malformed/length/empty and a prespecified
refusal screen are rejected. This is a syntactic screen, not semantic validation.
Raw rejected outputs and reasons remain in the acquisition journal.

Only the chosen justification changes. Task/options, answer vector, candidate IDs,
order/status/source references, every other packet and all correct raw packets
are checked unchanged. The entire two-dataset pool must be frozen and verified
against its acquisition results before any victim evaluation. Every accepted
variant goes to J8/J14 × full/evidence/free; no outcome-dependent victim choice,
successful-attack stopping, or QQQ attack. Recipient context compatibility is
checked with the actual native tokenizer, without truncation; incompatible cases
are nonexecuted technical missingness. Available requests are preflighted before
the first dispatch of each explicit stage.

Task-only and answer-only requests are proven identical including seed and public
prompt, and reuse exact clean outputs. Voting reuses the identical answer vector.
`by_construction_invariant` applies only to this justification-only threat.
Ordinary rephrase is a separate control, never a member of q=1/2/4 attack prefixes;
it is not certified semantic equivalence or length matching.

## Statistics and accounting

Report each dataset separately. Paired bootstraps use 1,000 resamples of groups
within strata, with equal category/domain weight; paired values for each task are
retained together. Reports disclose missing strata and exploratory multiple
comparisons. Counts use observed task denominators, never generation calls as
independent samples. Original historical comparisons remain descriptive.

Attack ASR conditions on paired clean successes; no clean successes means null.
Exact candidate adoption differs from target-answer adoption with duplicates.
Correct-to-valid-wrong and correct-to-invalid/abstain are separate. Eligible
utilization is explicitly conditional on the original mixed-support population.
q-prefix robustness requires clean correctness AND all prefix responses correct.
Rejected, incompatible or absent variants are unavailable, not vacuous success;
complete-prefix estimates and explicit full-eligible lower/upper bounds are saved.
A perturbation that fixes a clean error cannot inflate robust correctness.

| Stage | Maximum new calls | Reserved output tokens |
|---|---:|---:|
| Clean | 2,760 | 1,413,120 |
| Rewrite acquisition | 400 | 204,800 |
| Perturbed victims | 2,400 | 1,228,800 |
| Total | 5,560 | 2,846,720 |

The first two MMLU tasks' smoke is included: 12 calls for J8 or 24 for both judges.
Dataset/stage ceilings and the total are checked. Failed dispatched calls consume
attempt reservations. Skips never replenish or transfer allocations. Training,
teacher-forced scoring, proposer/revision generation and replay budgets are zero.
Resources retain actual tokens, model loading/wall times and GPU peaks. Compute
units are null unless actually supplied; reservations are not billed usage.

## Recovery, privacy, and boundaries

Each generation uses the existing immutable `JournalBackend`/`ShardStore` path,
with a study-specific validator. Source, full plan, prompt contracts, model,
precision/runtime and loaded identities are checked. Unknown attempts forbid
retry. A durable unsafe marker precedes first dispatch; periodic compact snapshots
remain unsafe until an explicit successful invocation boundary. A safe snapshot
is verified before continuing. A reset in an unsafe window remains a forensic
blocker even if visible counts match. Use `--stop-after N` for bounded safe breaks;
never edit state flags or fall back to an older safe snapshot.

Each explicit GPU stage creates a report and private/sanitized local bundles,
then performs bounded Drive copies and stops. PRIVATE includes bank/labels,
parent selected evidence, prompts/responses, token IDs, acquisition and new
journals. SANITIZED is an explicit aggregate-file allowlist. No model weights are
bundled. Private material must stay outside every Git checkout. Old completed
runs, incomplete controlled replay, GPQA B, MBPP, LiveBench and paper placeholders
are unchanged. No outcome authorizes the next study.

This is not an [AgentAuditor reasoning-tree/ACPO reproduction](https://arxiv.org/abs/2602.09341)
or [JudgeDeceiver optimization attack](https://arxiv.org/abs/2403.17710). Those
published methods remain relevant future learned-adjudicator/adaptive baselines;
the current one-pass evidence prompt and fixed rewrite pool do not implement them.
