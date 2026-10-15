# PACT saved-gate diagnostic audit — 15 October 2026

The primary gate's zero-switch tuning result is reproduced. Its highest active
utility is **−0.571269**, below every original finite threshold. Its six tuning
rescue-opportunity tasks have a correct alternative ranked highest in all 16
observed clean/variant opportunity views, yet no utility crosses zero. This is
compatible with useful relative ordering alongside conservative score location;
it is not permission to change thresholds or evidence of reliable generalization.

The checking signal is also imperfect. The restricted checker favors alternatives
for 30/32 clean fitting improvements, but also for 91/112 harmful replacements.
Thus agreement and favorable verdicts alone do not identify safe corrections.
The prospective selector clarification is implemented and CPU-tested, but no real
selector calls have occurred. The parent remains KEEP_ONLY, 44/64, zero switches,
with all 202 historical selector outputs malformed.

## Provenance and reconstruction

Exact parent PRIVATE SHA256:
`b013fc63b8c4331b25f0589374b162cdade24759b1a5442bb85ca89c81926449`.
Parent plan:
`848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6`.
The closed parent contains 128 fit, 32 tuning and 64 development groups and 3,579
committed calls, with no unresolved dispatches. This audit adds **zero model calls,
zero fits, zero optimizer updates and zero teacher-forced forwards**.

The bounded reader verified archive/member hashes. Authoritative parent code
reconstructed sources, pools, E/full/restricted feature paths, original baselines,
all five model/fit identities, fit-only transforms, weighted objectives/gradients,
original tuning curves and development decisions. Parent bytes were compared before
and after. No source labels, coefficients, thresholds, parser or historical scores
were changed. Missing evidence is an error rather than a regeneration request.

Private derivative: `/var/tmp/pact-gate-diagnostics-001`.
The local model-free child plan was separately validated against the real parent:
202 views, 404 requests, **four included smoke calls**. The two outcome-independent
hash-selected smoke tasks have only clean views; they are not replaced to reach
16. This local development plan is not a Colab revision pin; create the Colab plan
from the user's reviewed pushed commit using the runbook.

## Weighted support and signal

Clean fitting: 171 rows (112 harm, 27 neutral, 32 improve). Augmented fitting:
487 correlated rows (336 harm, 81 neutral, 70 improve). Actual class mass is identical
for clean and augmented arms because view augmentation preserves candidate targets
and redistributes each task's weight:

| Class | Objective mass | Fraction of observed classification mass |
|---|---:|---:|
| Harm | 0.4921875 | 0.7000000 |
| Neutral | 0.0924479 | 0.1314815 |
| Improve | 0.1184896 | 0.1685185 |

Total classification mass is 0.703125 = 90/128; the other 38 fitting tasks have no
alternative rows and retain their share of the original task denominator. The
normalized frequencies are a descriptive prior comparator, not a sixth gate.
No class smoothing or reweighting was introduced.

| Gate | Fit utility ROC AUC | Tuning utility ROC AUC | Maximum active tuning utility | Original choice |
|---|---:|---:|---:|---|
| Full clean | .7049 | .6022 | +.4331 | KEEP_ONLY |
| Full augmented | .7148 | .6436 | −.4659 | KEEP_ONLY |
| Restricted clean | .6723 | .5640 | −.5024 | KEEP_ONLY |
| Restricted augmented, primary | .6840 | .6424 | −.5713 | KEEP_ONLY |
| Metadata augmented | .6520 | .5029 | −.7551 | KEEP_ONLY |

AUC compares improvement against non-improvement, uses the arm's task/view/alternative
weights, and gives ties half credit. Clean arms use clean rows; augmented arms use
clean plus accepted fitting/tuning attack views. These are different row populations,
not a matched model ranking. Fit is in-sample; tuning was already used for selection.
The artifacts also report improve-versus-harm log-odds/utility AUC and tied-block AP,
neutral distributions, supports and nulls for undefined comparisons.

Primary weighted NLL is .6936 on fitting and .7059 on tuning, compared with the
fit-prior reference .8165 and .7695. Primary Brier scores are .3940 and .4209.
These descriptive scores do not certify probability calibration or future risk.
Log reporting clips at 1e-15 only; probabilities, Brier scores and policies are
unchanged. Task-level uncertainty uses 500 source-stratified bootstrap replicates,
seed 20261015, rather than treating correlated candidate rows as independent.

The primary gate ranks a correct top alternative in 48/56 observed fitting
opportunity views (22 groups) and 16/16 tuning views (six groups). Tuning has nine
clean improving candidate rows: one ARC and eight LogiQA, across one/five groups.
All 21 improving candidate uses across tuning views are active; no tuning candidate
is disabled. The primary's lack of actions is therefore score suppression before
the 5% screen, not rejection of a proposed useful switch by that screen.

Full-clean differs: one attack-view score crosses zero and causes harm without
clean gain. Original thresholds 0 through .35 fail the observed-pool screen;
.50/.75 and KEEP_ONLY tie, and the prescribed final tie-break selects KEEP_ONLY.
All original curves and choices match the parent exactly.

## Checking, collisions and retrospective cases

Clean restricted verdicts favor alternatives for 30/32 improving and 91/112 harmful
fit rows; for 8/9 improving and 18/25 harmful tuning rows; and for 11/12 improving
and 37/46 harmful development rows. These are candidate rows, not independent tasks.
Full/restricted clean agreement is 28/32 on fitting improvements and 100/112 on
fitting harms; agreement does not mean factual correctness. Conditional tables
also retain disagreement, evidence categories, extractor types, references,
external-knowledge assessments, public metadata and disabled paths.

No cross-label exact feature-vector collision was found for the full/restricted
representations. Metadata has nine collision vectors across 454 fit view rows,
three across 63 tuning rows, and seven across 239 development rows. These observed
collisions are not an impossibility theorem; absence of exact equality is not proof
of separability, especially with continuous length features.

The escaped PRIVATE dossier contains **59 task groups**:

- 22 fitting rescue groups, including all 32 clean improving candidate rows;
- six tuning rescue groups;
- all nine clean LogiQA development rescue groups, with none on ARC;
- 22 fixed hash-selected harmful fitting groups, explicitly not a prevalence sample.

All original/edited views, raw checking records, references, feature values,
logits/probabilities, active masks and parent decisions are retained separately.
Among the 12 clean development improving candidate rows, 11 are active; the largest
primary utility is +.003866. The selected KEEP_ONLY policy still takes no action.
This is retrospective inspection under the original rule, not development tuning.
No semantic correctness or independent human review is asserted.

## Fixed sensitivity and interpretation

All 4 × 13 points were computed for each of five models on fit/tuning separately:
520 deterministic policy evaluations, zero model calls. Every point is marked
`diagnostic_only=true`, `policy_selection_authorized=false`. No development grid,
winner, replacement receipt or transfer invocation exists.

For illustration, retaining primary harm cost 2: tuning threshold −2 makes six
clean rescues and fifteen harms and fails the original screen; −1 makes one rescue
and one harm; −.5 and every larger original finite threshold make neither. These
are prespecified diagnostic points, not recommended operating points. Lowering a
threshold can introduce harms as well as rescues. The original KEEP_ONLY result
stands. The complete grid is private; no attractive point is selected here.

The next implemented comparison addresses the separate broken selector control:
a fresh exact legacy prompt versus a contract-only clarification on all 202 views.
It cannot retroactively repair the parent. Better formatting may or may not yield
useful correction. Generalization, calibrated risk and actual v2 compliance remain
unestablished. No new gate, dataset, transfer, human/span review or full PACT update
is authorized by this audit.

## Implementation and validation

New trusted modules: `closed_parent.py`, `diagnostics.py`, `selector_contract.py` in
`src/pact/selective`; canonical CLI routes `gate-diagnostics` and `selector-contract`.
The existing gate validator adds an explicit diagnostic-artifact rejection. Notebook
23 and [the exact command sequence](../gate_diagnostics_colab.md) default to model-free
planning. Real model/tokenizer/weights access occurs only in explicit Colab stages.

Focused new tests: **25 passed** in 19.832 s. Relevant existing selective-correction
and exposure-inventory regressions: **39 passed** in 20.143 s. No skips or failures
in those final runs. Earlier development runs exposed and fixed fixture input and
partial-report extension errors; these are not unresolved test failures. No claim
of a full-suite run is made. The design checker and notebook syntax/default checks
passed. `git diff --check` passed.

The test fixtures exercise zero-support KEEP_ONLY, no refits, strict parsing,
label isolation, rank/tie/null behavior, weighting, forbidden development grid,
private escaping, safe import, fresh child identity, paired seeds, budget constants,
resume/unsafe windows, broken-v2 negative outcomes and complete mock export/import.
Mocks do not establish real prompt efficacy. GPU inference remains **unverified**.
No large-model downloads, credentials, GPU calls, commits or pushes occurred.
