# Selective correction: anchor_check_gate_v1

Implementation of [the 14 October update](PACT_Codex_Selective_Correction_Update.md)
for `pact-selective-correction-001`. This is frozen-LLM outcome-supervised routing,
not original joint PACT, receiver SFT, a verified reasoning system or a risk certificate.
Human semantic review and cue/sham interventions remain deferred.

## Source and contracts

224 new official training groups: 128 fit, 32 threshold tuning, 64 source-development,
each balanced ARC-Challenge / original English LogiQA. Reuse the pinned training
loader and its transitive exact/word-trigram grouping. Exclude the entire previous
1,200-item preparation allocation conservatively, the full official validation-connected
groups and recorded prior/locked IDs, group IDs, content groups and breadth fingerprints.
The prior 1,200 manifest must reproduce its historical hash. No official test source
is downloaded. A reviewed **hash/ID-only** prior-exposure inventory matching the current
exposure ledger is a real prerequisite; missing inventory or insufficient quotas stops
preparation before inference. This is not semantic decontamination.

One Q/L/M packet and one independent J8 answer per task; native pristine pinned
registry models, no adapters. J8 uses the inherited task-only answer/basis contract.
Natural packet system text is inherited unchanged. All new calls use 512 output and
8192 total tokens, J greedy/non-thinking, Q/L/M and Q rewriting use inherited complete
sampling parameters. One resident model, model-major stages, separate fresh requests.
Source-develop­ment dispatch requires frozen policy hashes. Transfer requires the
exact closed adjudication PRIVATE parent and uses only its original J8 anchors/QLM
bank and accepted pool. No parent regeneration or J14 substitution.

Every complete three-task binding block assigns Q/L/M once to each anonymous slot;
remainders differ by at most one within a source/split. Historical selection inventory
readers support both the existing list and object formats. Prepared label inventories
must match selected task IDs exactly. Before victim checking, frozen pools are
reconstructed against committed rewrite evidence with acquisition disabled.

## Checking and features

One extractor per alternative, shared between full and restricted paths. Host-validated
spans index `QUESTION:\n...\nCONTEXT:\n...\nOPTIONS (possible answers, not premises):\n...`
in Python Unicode code points; at most two spans. Options are explicitly hypothetical,
and `verified_proof=false` on every reference. Empty references are valid. The schema
rejects extra fields, invented quote text, invalid bounds, duplicate JSON keys and
oversized strings. It never truncates a bad response into validity.

Both verifier instructions and schemas are identical. Full alone includes the current
raw justification; restricted omits it. Neither sees peer counts, families, correctness,
other verifier outputs or attack names. Both cache identities include the extractor
request/result provenance; a changed extractor invalidates both, even if its returned
challenge text happens to match. Corresponding verifier seeds match. Unaffected paths
reuse identical requests. Changing only another peer cannot change a pair prompt.

Features are versioned in `contracts.feature_spec`. Numeric length bounds are 8192
characters for the source rationale and 1200 for the combined challenge strings.
Numeric means/scales use fit task/view/alternative weights, renormalized over actual
classification rows for the transform only. Categorical vocabularies are fixed, with
UNKNOWN; categories are not standardized. The classification loss retains `1/N_fit`
including tasks that produce no alternatives. Disabled checker rows remain training
rows, with missingness features, but cannot be selected at deployment.

`metadata_augmented` has precisely five public count/availability features, no text,
reference, extraction or checking dependency. It can select a valid alternative even
when the checker path failed. Gate decisions never call an LLM.

## CPU fitting and thresholding

Five fits only; harm/neutral/improve class order, zero initialization, L2=0.001 on
coefficients and no intercept penalty. Equal task weights; equal valid-alternative
weights; clean-only view mass 1; augmented clean mass .5 and accepted attack views
share .5, reverting to clean mass 1 without applicable accepted variants. No class
rebalancing or hyperparameter search. Fit/tuning labels are physically separate files;
fit reconstruction never opens tuning/source-development label payloads.

A small NumPy-only full BFGS optimizer with Armijo backtracking minimizes the exact
specified objective using its analytic gradient. NumPy 2.2.3 is the optional `gate`
extra; no SciPy or GPU dependency is needed. Stop at gradient infinity norm 1e-6,
with at most 500 iterations and 50 line-search halvings per iteration. Nonfinite,
line-search or iteration-limit failure raises an explicit error and retains a consumed
fit intent; it does not produce a trained gate or silently retry. No improvement
support or one class produces the specified named constant KEEP-only outcome.
Coefficients, transform, class support, weights and diagnostics are JSON, never pickle.
Distinct task-class support and clean candidate-class counts are separate from
correlated augmented-row counts. Fit wall time and NumPy version are recorded outside
the deterministic model hash.

Tune the entire max-over-candidates policy on tuning tasks using the fixed grid
0/.05/.10/.20/.35/.50/.75/KEEP_ONLY and strict `u > tau`, `u=p(improve)-2p(harm)`.
Ties use ascending anonymous candidate IDs. Maximize clean gain, then joint observed
pool success, then minimize tasks switched in any observed tuning view, then choose
the larger threshold. Clean and observed-pool harm must each be <=5% of all tuning
tasks. Missing variants receive explicit bounds, not success. The screen is empirical;
32 tasks cannot certify 5% risk. KEEP_ONLY is a valid completed negative result.

## Controls, outcomes and accounting

Always KEEP; one-call anchor-inclusive selection; three independent critique/reconsider
cycles (six calls, no peers, final cycle fixed); metadata; four learned checking gates;
and a prespecified zero-extra-call restricted rule requiring alternative-supported and
baseline-contradicted with a unique qualifying answer. It is not tuned as a sixth gate.
Selectors and independent final outputs use the same original-anchor fallback on
model-format failure. Strict generated-output correctness is retained separately;
deterministic gate action correctness and checker-format failure incidence are distinct.
Infrastructure missingness never becomes a successful fallback.

Each deployed checking method uses at most two calls per alternative; collected union
uses three. The clean and augmented policies reuse those features, never collect four
copies. Reports retain raw class counts, feature failures, exact reference integrity,
source availability, rescue/harm identities, strict/fallback outcomes, target-answer vs
candidate adoption, rejected/inapplicable variants, complete attack-prefix bounds,
rephrase separately and task-group bootstrap comparisons. Bootstrap intervals are
exploratory, equal-stratum, and unadjusted. No evaluation threshold is selected.

| Scope | Calls | Reserved output tokens |
|---|---:|---:|
| Fit + tuning | 3,360 | 1,720,320 |
| Source development | 2,240 | 1,146,880 |
| Core | 5,600 | 2,867,200 |
| Optional transfer | 5,156 | 2,639,872 |
| Portfolio | 10,756 | 5,507,072 |
| First included FIT source smoke | 8 | 4,096 |

Budgets count attempted dispatches. No replenishment for failures. Unsafe persistent
windows and unresolved intents block automatic resumption. Compact two-file snapshots
avoid per-shard Drive restore; the latest unsafe snapshot is never skipped. Private
exports include text, labels, token arrays and coefficients. Sanitized exports contain
allowlisted aggregates only. No new result follows from CPU fixtures.

## Fictional CPU example, not a benchmark result

The deterministic integration fixture uses a fictional symbol task, anchor A and
peer B. On one held-out fixture record, the trained restricted-augmented model gives
`[p(harm), p(neutral), p(improve)] ≈ [0.002797, 0.002218, 0.994985]`.
Thus `u ≈ 0.989392 > tau=0.75`: SWITCH copies the stored peer answer B. On another
fixture record it gives `[0.748564, 0.249262, 0.002174]`, so `u ≈ -1.494953` and
KEEP copies the original anchor A, including its saved raw bytes. No final LLM
regeneration occurs. These values came from actual CPU optimization of fictional
saved features, not hand-written scores or real-model scientific evidence.
