# Proposed OpenBookQA–LogiQA evaluation-source amendment

28 October 2026. Implementation and CPU audit only. **No source acquisition,
cohort approval or GPU execution is authorized.** The existing v3 source plan
remains `prospective_eval_not_feasible`; its code and artifacts are unchanged.

## Scope and proposed identities

The separate CPU route is `python -m pact evaluation-source`.
Version: `stage2-evaluation-source-openbookqa-logiqa-v2`.
Review child: `pact-stage2-openbookqa-logiqa-eval-amendment-v2-001`.
Reserved future assay/policy identifiers:
`pact-update-allocation-openbookqa-logiqa-v2-004` and
`pact-allocation-policy-openbookqa-logiqa-v2-003`.
These are PROPOSED identities, not newly activated experiments. Output-directory
collisions stop; there is no overwrite, resume, execute, approve or seal option.

Only the prospective evaluation source is proposed to change: 64 OpenBookQA
`main/train` science questions plus 64 original English LogiQA training groups,
contingent on current eligibility, exact source identity and human rights review.
This is a post-Stage-I design revision. It estimates closed-book science transfer
and within-source logical-reasoning development performance, not balanced ARC
performance, official OpenBookQA leaderboard accuracy or final-test confirmation.
Project disjointness never establishes pretrained-model disjointness: the latter
remains unknown. Public release is not evidence of pretraining exclusion.

The original executed 3 ARC / 5 LogiQA blocks and 24/40 probes remain immutable.
The solver stays eight-row, tau .2, balance .1, weighted 3/8 ARC and 5/8 LogiQA.
Evaluation means weight OpenBookQA and LogiQA 1/2 each and report each separately.
S0, all five policies, real base/extra update slots, two continuation seeds,
per-family persistent optimizer, exact rollback, pristine R scoring and original
loss masking remain the existing v3 implementation. No receiver loss or Stage III.

## Source import and evidence requirements

The importer reads local JSONL or bounded Parquet only. It checks raw SHA256,
immutable revision, main/train identity, byte/row bounds and nested choice fields.
Exactly four normalized distinct A/B/C/D labels and distinguishable option texts
are required; input ordering and answer mapping are preserved. Extra fields,
including facts/ratings, are rejected. Gold is a separate TaskLabel. No additional,
validation or test OpenBookQA source is supported; no dataset script or pickle runs.

A reviewed source specification must bind the complete 4,957-row main/train file
identity (that public count is not an eligible count). A manual curated JSONL
snapshot needs a documented origin review, not a claim that it is an upstream raw
file. Official-origin receipt bytes must match the supplied digest and source
identity. Neither a caller-provided hash nor a boolean alone certifies provenance.
There is no moving-revision or mutable converted-mirror fallback.

Rights approval requires actual local terms files with verified hashes and an
external human review receipt binding exact source identity, terms, intended use
and item scope. The auditor records that assertion; it does not make a legal
judgment or create approval receipts. The official
[Hugging Face card](https://huggingface.co/datasets/allenai/openbookqa/blob/main/README.md)
reports unknown licensing. The [repository LICENSE](https://github.com/allenai/OpenBookQA/blob/main/LICENSE)
is Apache-2.0; its presence alone does not resolve rights to every data item.
Only public metadata pages were inspected locally; no dataset was fetched.

LogiQA must use the existing official original-English Train.txt revision and
SHA256 in `training.data.TRAIN_SOURCES`. Existing complete train/validation caches
are required to reproduce the original 1,200-selection and overlap policy, with
`download=False`. No test files are opened. These validation files are historical
exclusion evidence, not candidate evaluation questions.

## Exposure audit and candidate selection

The current benchmark-ledger hash and experiment-ledger hash must match a reviewed
inventory covering all previously used and protected project groups. It must bind
the executed Stage I source and state whether material overlap cases are unresolved.
Original source exclusions, prior selection manifests and all Stage I groups are
added independently. Current external probe-use history is separately reviewed;
local absence never substitutes for it.

Grouping reuses the existing normalized content and transitive word-trigram Jaccard
>= .9 rules, including validation-connected exclusions and conflicting labels.
Original group identities are retained as exclusion aliases when adding OpenBookQA
changes components. Historical exclusion propagates through the whole combined
component, including cross-source members. These lexical checks are not a semantic
paraphrase or pretraining-contamination certificate. Material unresolved review
cases stop selection. No model outcome is used to screen or choose examples.

Audits distinguish schema rejections, denied overlap groups, unknown review status,
and permitted unique groups. With unavailable bytes, counts are null, never zero
or invented. Both sources need 64 currently permitted groups. The selection key is
SHA256([20261016, `pact-stage2-openbookqa-logiqa-eval-amendment-v2`, group_id]), with
stable task ID tie-break. The first 64 per source are selected once; selected group,
canonical content and cross-source fingerprint uniqueness are independently checked.
Candidate labels stay evaluator-only. `candidate_selected` is not `cohort_approved`.
No code path in this amendment approves a cohort or activates training/inference.

## Protocol and dependency graph

Existing private/revision/final templates and 8,192 context / 512 output caps remain
unchanged. No source label, provenance, gold field or privileged fact reaches the
prompt. Wrong-target choice uses the existing evaluator-side rule; attacker input
contains trusted question/options, assigned wrong option and approved style only.
Sender/style selection is deterministic and outcome-independent. Each task has
one shared attempt/payload across teams. Rejected attacks yield missing exchange
conditions, not successes or clean substitutes.

The compiler emits generation nodes, diagnostic nodes, update reservations and
freeze/lock dependencies. Unchanged private assay nodes are reused; changed-private
and all affected revision/readout nodes are new. Model checkpoint references keep
unchanged actors at S0 and R/attacker Q pristine. Every node binds the new method,
source/cohort/lineage, code contract and seed. Smoke manifests are subsets of these
same node identities. No old wallet or request identity is transferred.

Future trained checkpoint hashes, policy-dependent family schedules, native rendered
prompts, generated packets and accepted attack bytes cannot be known before their
stages. The compiler labels these late bindings explicitly. Its graph is **not a
fully resolved dispatchable request manifest**. Actual per-family interleaving is
still `allocation_v3.design.schedules`, not the update-reservation order. The
CPU request renderer hashes actual team-specific packet bytes, native identity
and effective checkpoint; fixed templates do not require identical full prompts
across trained teams. Native tokenizer/context validation remains deferred.

## Reconciled conditional budgets

Actual fitting/probe identities imply 64 baseline probes and 816 changed-branch
probe views: 3 actors × (3 blocks ×24 +5 blocks ×40).

| Component | Generations | Updates | Supervised forwards | Diagnostic forwards |
|---|---:|---:|---:|---:|
| Baseline assay and shared attacks | 768 | 0 | 0 | 192 |
| 24 temporary branches | 7,344 | 192 | 1,536 | 2,448 |
| 10 policy/seed teams plus S0, 128 candidate slots and shared attacks | 15,616 | 2,880 | 23,040 | 0 |
| Total conditional ceiling | **23,728** | **3,072** | **24,576** | **2,640** |

Reserved output cap: 12,148,736 tokens. Included smoke subsets: 24 assay and 244
policy calls. Aliases/rejections reduce physical work, not authorize replacement
calls. Synthetic GPU allowance remains zero. Actual graph counts are only populated
with a candidate manifest; unavailable cohorts get arithmetic reconciliation with
128 explicitly *required slots*, never fabricated eligible identities.

Reports preserve per-source/seed results, task-paired contrasts against uniform
and source-family, clean utility, accepted-exchange missingness, HOLD/REPAIR,
coverage, erasure, readout loss and strict invalids. Bootstrap units are underlying
groups, source-stratified with both seeds together, using the existing 10,000
replicates and descriptive 95%/97.5% intervals. No accepted support in either source
makes the combined attacked estimate undefined. Intended-population bounds remain
reported. Two seeds do not replicate Stage I or the entire learning procedure.

PRIVATE exports contain source identities/text, labels, audit detail, lineage,
candidate and graph when present. SANITIZED is an aggregate allowlist with no raw
questions or per-ID hashes. Checksums and read-only reconstruction are mandatory.
Invented CPU mock outputs carry no scientific result. No new neural training or
runtime path is activated by this source amendment.
