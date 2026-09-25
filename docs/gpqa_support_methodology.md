# GPQA Diamond natural support and clean communication v1

Implements [the authorized study](PACT_Codex_GPQA_Support_Study.md), run
`qwen3-gpqa-diamond-support-001`. The completed controlled-receiver result remains
closed and unchanged: no added receiver correctness across the three arms. This
new study asks about natural support and clean communication, not trained PACT,
attack robustness, or a causal effect of difficulty. No GPQA outcome exists yet.

## Official access and partition

Official dataset [Idavidrein/gpqa](https://huggingface.co/datasets/Idavidrein/gpqa),
configuration/file `gpqa_diamond` / `gpqa_diamond.csv`, resolved revision
`83022cefff930aea54f654c0b282e74b9eeda5c6`. The public official tree supplies exact
Git blob SHA1 `7589e3e467d69a1dceb126a60c4108d6d4f1d166`, size1,373,492 bytes. README
and license bytes are pinned too; runtime receipts additionally record SHA256.
This uses ordinary pinned data-file download through huggingface_hub, not an
executable dataset script. No gated content was downloaded locally. User must
personally accept conditions and supply authorized HF access, or the identical
three-file official directory. No mirrors or access bypass. Failed access prints
`dataset_access_required` with the action; token-bearing exceptions are suppressed.

The [authors' loader](https://github.com/idavidrein/gpqa/blob/main/baselines/utils.py)
identifies the final Question, Correct Answer and three Incorrect Answer fields.
Their [repository](https://github.com/idavidrein/gpqa) also identifies the dataset
canary; the [paper](https://arxiv.org/abs/2311.12022) describes the benchmark.
Runtime requires the exact198-row Diamond file and `High-level domain` values in
Biology/Chemistry/Physics. Actual authenticated CSV/header/domain acceptance is
**unverified until user access**, not a silently assumed successful preflight.
Unexpected fields needed by the contract, counts or domain values stop the study;
no label-derived domain inference or post-hoc replacement is allowed.

Final text is whitespace-trimmed, with internal Unicode and mathematical notation
preserved. Each task has four distinct NFKC/casefold/whitespace-normalized options.
When Record ID exists, ID is SHA256 of its namespaced value; otherwise SHA256 of
final question plus sorted answer texts (canonical JSON). This is order-independent,
not a row index. Options are ranked by SHA256 of seed20260924, namespace, task ID
and option text; IDs A–D follow this once-per-task permutation. Gold is mapped on
the evaluator side; source field names never enter prompts. Only trusted question,
context (empty) and canonical option text enter the existing prompt builders.

Largest-remainder allocation chooses32 unique task groups proportionally by domain
with alphabetic domain ties; seeded SHA256 group ranks determine membership and
seeded task ranks determine execution/smoke order. Question equality after NFKC /
casefold / whitespace normalization and word-trigram Jaccard>=0.9 for questions
with>=12 words are unioned with known groups. One stable representative per group
is eligible; siblings of selected groups are excluded from the protected remainder.
Cross-domain duplicate groups stop for review. No outcome affects selection.
Semantic paraphrase absence is not established by this lexical screen.

`experiments/gpqa_exposure_policy.json` records the ledger review: no prior GPQA
run was found. It accepts known exposed content/group hashes and known ID groups
before freezing. This is not a claim about pretraining contamination or unknown
external exposure. Selected32 are development-exposed, never training or untouched
final items; nominal remainder166 can decrease with documented exclusions. All198
records are read automatically for partitioning; only selected32 task texts are
retained in the study plan and only those IDs are accepted by the call journal.
The full authorized source CSV remains outside Git and outside review bundles.

## Frozen arm and unchanged protocol

The pinned completed study bundle `ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea`
supplies the **frozen** checkpoint and effective-initialization receipt, not either
trained arm. Original90-step preparation exports are compact-restored from the
verified full snapshot (see runbook). Export/config hashes and runtime are checked;
the legacy loader then reproduces its actual FP32 focal and BF16-rounded→FP32
nonfocal effective tensors. The same `verify_loaded` guard and snapshot calculation
used in the completed recovery checks all three effective actor hashes. No tensor
is corrected or rewritten. Stored/effective dtypes and load policy are recorded.

Qwen3-8B base/tokenizer revision `b968826d9c46dd6066d109eabc6255188de91218`,
BF16/SDPA, thinking off,4096 context; packet cap256 and readout cap64. Exact decoded
parameter dictionaries are read from the prior frozen-arm calls (including min_p,
repetition penalty, beam/cache settings and special-token IDs) and checked on each
call. Base/template/defaults/runtime/effective identities must match before inference.
No actor/backbone update or scoring call exists in this study.

All three private packets are frozen before any delivery. The existing vote ignores
invalid ballots and abstains on ties/all invalid; labels never break ties. Existing
synthesis and debate `Protocol.suffix` calls share the frozen packets. Debate revises
synchronously from own initial and initial peers only. Both readouts use the same
base-only prompt/decoding and packet ordering, with distinct stage-derived node
seeds for the two deterministic readouts. Prompt contents differ only in packets. The existing adapter disable/restore context is reused.
Full packet prompts remain unchanged; no rationale or answer target is supplied.

Node seeds derive from study seed20260924, immutable task ID, stage and actor via
existing node_seed. Each task has immutable slots: private0/1/2, independent readout,
revision0/1/2, debate readout. Vote adds zero calls. Budget is exactly256 possible
calls /53248 reserved output tokens. Two-task smoke uses the first two selected
IDs and these same16 slots. `private` may collect96 calls first; `complete` reuses
them and completes all32 regardless of observed support. No extra samples/retries.

## Artifacts, privacy and recovery

Private paths are rejected inside any Git checkout, including ignored directories.
Additional Git ignores defend against accidental official CSV additions. GPQA task
split is `development_diagnostic`; legacy scored-bank and warm-start entry points
also reject GPQA IDs/families, including a relabeled train split. No training/donor/
preference/final-test export exists. Future main/extended training would need a new
design excluding all Diamond content/groups, not merely the exposed32.

The existing immutable call shards, checksums and bounded Drive snapshot workers
are reused. An unsafe durable marker precedes the first new call of a task; further
calls remain unsafe until the task/stage commits and a verified safe snapshot is
written. This avoids copying snapshots around every individual call, but loses the
ability to resume from Drive alone if a runtime dies midway through a task. Retained
scratch can prove all attempts committed; ambiguous attempts never silently retry.
Only the newest safe snapshot can restore; source/model/data/options/request hashes
must match. A bounded pause counts fresh calls and preserves committed cache entries.

Private bundle: selected task text, prompts, labels/mappings, raw completions,
tokens, frozen source/identity receipts, journals, metrics and resource records.
No tensors or protected source CSV. A private review is not an optimizer or weight
backup. Local private recovery ZIP is attempted on failure before a Drive copy.
Errors record type and a message hash, not arbitrary raw exception text or secrets.

Sanitized bundle: allowlisted computed counts/booleans, task/group hashes,
partition IDs, configuration, paired metrics/costs and missingness. No questions,
option strings, explanations, prompts, continuations, token arrays or raw errors.
It cannot establish raw-prompt correctness; return the private ZIP through a private
local channel for that audit. Neither store access permissions nor actual Drive
availability can be verified locally; use an access-controlled destination.

## Scoring and interpretation

Existing strict parser: length-limited output fails, even if an answer prefix is
visible. Raw stop statuses and token arrays remain in the private audit for sensitivity
analysis; no lenient salvage changes primary scores. Private preflight checks all32
questions before dispatch. Actual revision/readout overflow stops before inference;
no truncation, replacement or budget expansion.

Reports include observed and conservative full32 N0 histograms, complete-valid-team
N0 view, per-agent accuracy, coverage and oracle gain, valid correct/wrong mixed
support, all-wrong diversity, invalid patterns, pairwise rates and natural hold/repair
counts (task, agent-context and agent0). Communication reports N0→N1 counts/rates,
existing c/u/k/d/r/readout-loss identities, opportunity-conditioned hold/repair,
vote/synthesis/debate scores, paired task transitions/bootstrap and token/time cost.
Actual totals count private work once; logical deployment costs charge shared private
work to each protocol. Time is not billed compute; units stay null.

Incomplete tasks are missing, not silently discarded from expected32; conservative
N0 sensitivity assigns missing teams zero separately. Primary conditional metrics
use complete observed cohorts and retain null zero denominators. Boundary rates
are explicitly flagged uncertain, and degenerate paired-bootstrap intervals are
not equivalence evidence. The32 IDs are sampling units, not256 calls.

Screen: >=8/32 mixed tasks allows designing (not executing) a follow-up;1–7 is
sparse;0 is no observed support in this configuration. Incomplete/unresolved work
or >=48 invalid private packets out of96 qualifies the screen rather than giving
an uncomplicated verdict. Honest wrong peers are not attacks. Correct answer labels
do not certify rationales or causal peer use. Historical ARC/LogiQA results are
not pooled or rerun; the report explicitly marks historical comparison not pooled.

Deferred: attacked follow-up, additional seeds/items/reasoning budgets, alternative
models/options scores, any GPQA training, full PACT refresh and official full-Diamond
leaderboard/final-test claims. No result authorizes another run automatically.

## Fictional normalization example (not GPQA content)

Input: `Fictional device: which lamp is lit?`; correct source answer `Amber`,
incorrect source answers `Blue`, `Green`, `Violet`; domain `Physics`.
With the fixed hash permutation the visible options are:

| Canonical ID | Visible text |
|---|---|
| A | Violet |
| B | Amber |
| C | Green |
| D | Blue |

Evaluator label is B. The defender sees only the question and those uniformly
formatted options; it does not see `Correct Answer`, domain, gold B, explanations,
source-to-canonical mapping or exposure flags. All three actors and both readout
branches receive this same option order. The normal generated target is still a
full answer-plus-justification packet; there is no supervised output or score mask.
See [exposure policy](gpqa_exposure_policy.md) for allowed downstream uses.
