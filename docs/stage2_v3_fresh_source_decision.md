# Stage II v3 fresh-source feasibility review

Review date: 28 October 2026. Status: **prospective_eval_not_feasible**.
This is a decision record, not an approved methodological amendment or GPU plan.

## Finding

The implemented v3 study cannot meet its 64 fresh ARC plus 64 fresh LogiQA
prospective evaluation requirement under the currently permitted source revisions
and preserved exclusions. Do not run the contribution assay first: the v3 brief
explicitly requires resolving this cohort before exposing allocation probes.

The exact Stage I source was reconstructed again from the hash-verified parent.
All seven authoritative metadata hashes passed the executed-source check.

| Inventory | ARC Challenge | Original English LogiQA |
|---|---:|---:|
| Historically eligible groups | 406 | 6,605 |
| Main fitting | 192 | 320 |
| Allocation probes | 24 | 40 |
| Stage I validation | 64 | 64 |
| Stage I source evaluation | 120 | 136 |
| Unique groups already allocated | 400 | 560 |
| Upper bound remaining | **6** | **6,045** |
| Required prospective groups | 64 | 64 |
| Minimum shortfall | **58** | 0 |

These are historical eligibility counts and a conservative remaining-capacity
bound, not a new enumeration of raw benchmark files. Later exposures and duplicate
screening can only reduce availability. In particular, LogiQA's upper bound does
not certify that a fresh final cohort has passed current exclusions.

## Why the bound applies

`src/pact/revival/data.py:allocate` counts the eligible official training pool
before selecting any Stage I splits. It first applies overlap auditing, the
historical 1,200-task selection, prior experiment selections and reviewed exposure
exclusions. The recorded 406 ARC groups are therefore the remaining eligible
pool, not the size of the entire ARC dataset.

The verified source contains 400 distinct ARC group identities across the four
splits. V3's `select_fresh` preserves those exclusions, adds every Stage I group,
and requires the same official source revisions. Re-downloading those files or
changing selection seeds cannot increase this pool. A raw-source re-audit could
identify a historical counting defect, but no such defect is currently evidenced;
it cannot simply declare previously excluded groups eligible.

Source hash:
`85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`.
Parent PRIVATE SHA256:
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
No raw task text, labels or task identities are reproduced in this report.

## Decisions available

| Choice | Consequence | Required before execution |
|---|---|---|
| Keep v3 unchanged and defer it | Preserves the intended prospective comparison; no Stage II evidence is collected | No GPU work; retain implementation and completed Stage I results |
| Propose a different, explicitly permitted prospective evaluation source | Changes the evaluation population and potentially scorer/protocol requirements; availability is not assumed | A separate reviewed amendment, CPU eligibility audit, immutable cohort and analysis/budget review before any assay |
| Propose an explicitly retrospective or one-source diagnostic | Answers a narrower, different question; cannot claim the v3 balanced fresh-source result | A separate reviewed design and child identity; quantify exposure and limitations; no silent reuse of the v3 plan |

Recommendation: retain v3 as blocked. If Stage II remains the priority, first
prepare a separate evaluation-source amendment for review. Do not release protected
or previously exposed groups, substitute a test split, reduce the cohort to six,
or drop ARC within the existing v3 contract. No alternative source or new run is
selected or authorized by this review.

## Independent prerequisites still outstanding

Even a future source amendment would not resolve these automatically:

- External historical Stage II/probe-consumption evidence must be reconciled.
  No matches in local imported history is not proof of no remote attempts.
- Current checkpoint bytes and the exact native runtime must pass execution checks.
  Verified historical receipts are not a new real tensor-load test.
- A new sealed cohort, frozen plan and explicit GPU execution review are required.

## Work performed for this review

Read the v3 requirements, source-allocation addendum and actual selection code;
re-ran authoritative source verification; independently counted unique groups and
split membership; recomputed the capacity bound. The results match the previous
private source review. This documentation-only follow-up changes no runtime logic.

No data download, new cohort selection, model call, training, cluster submission,
commit, push or historical artifact modification occurred. Existing CPU test
results remain recorded in `implementation_status.md`; they are not new scientific
outcomes. The complete CLI and deferred stage interface remain in
`stage2_allocation_v3_runbook.md`.
