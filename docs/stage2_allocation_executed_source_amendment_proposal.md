# Proposed Stage II amendment: preserve executed source groups

Status: **PROPOSED — not approved or active**. Prepared 27 October 2026.
This makes the source-contract decision concrete for review. It does not change
code defaults, existing plans, approved ceilings, group exposure or execution authority.

## Recommended resolution

Preserve all 512 fitting groups, their eight immutable 64-task blocks and all 64
allocation probes from the verified Stage I parent:

| Source | Fitting blocks | Fitting groups | Shared probes for every same-source branch |
|---|---:|---:|---:|
| ARC Challenge | 3 | 192 | 24 |
| Original English LogiQA | 5 | 320 | 40 |

No replacement groups, repartitioning, discarded probes or additional probe draws.
The assay still has 24 branches (eight blocks × three adapters), each with eight
updates. Every source's branches use its entire identical retained probe set.
Stage I remains immutable; this would be a newly versioned child contract.

## Consequences that must be approved together

1. Replace four/four fitting-block and 32/32 probe assertions with exact executed
   identities and three/five,24/40 counts. Reject both mixed contracts and implicit
   resume/migration from reviewed-v2 plans.
2. Preserve the existing solver's mean over eight block rows, tau .2 and balance .1.
   With full support, source contributions to that mean are now 3/8 ARC and 5/8
   LogiQA; this is **not equal-source allocation estimation**. Do not introduce an
   unreviewed source reweighting. Report this asymmetry explicitly. Prospective
   final comparisons remain equal-source weighted.
3. For `source_family`, preserve exact terminal source/family totals and distribute
   them over that source's actual three or five blocks, using floor/ceil(total/n).
   Retain row totals of 12 and the existing outcome-independent hash tie rule.
   Freeze a new within-source derangement over the actual three/five block sets.
4. Replace generation/scoring ceilings as calculated below. Do not take the
   additional calls from another wallet or reduce controls to fit the old ceiling.

## Exact ceilings

Base bank and one-attempt attack pool: `64 × 11 + 64 = 768` calls.
Branch task views: `3 adapters × (3 × 24 + 5 × 40) = 816`.
Changed-private plus all clean/exchange suffixes: `816 × 9 = 7,344` calls.
Pristine-R diagnostic scoring: `(64 + 816) × 3 = 2,640` forwards.
These are upper bounds; rejected attacks and exact aliases do not replenish budgets.

| Quantity | Current reviewed v2 | Proposed executed-source amendment |
|---|---:|---:|
| Assay generation calls | 7,680 | 8,112 |
| Assay reserved output tokens | 3,932,160 | 4,153,344 |
| Diagnostic scoring forwards | 2,496 | 2,640 |
| Policy generation calls | 15,616 | 15,616 |
| Portfolio generation calls | 23,296 | 23,728 |
| Portfolio reserved output tokens | 11,927,552 | 12,148,736 |
| Temporary optimizer updates | 192 | 192 |
| Continuation optimizer updates | 2,880 | 2,880 |
| Total supervised forwards | 24,576 | 24,576 |

No change to the 24-call included assay smoke, 244-call included policy smoke,
zero added synthetic forwards in this implementation, five policies, two continuation
seeds, S0, pristine readout/attack models, masks, protocol, optimizer settings or
checkpoint rollback. No Stage III, final-test or automatic GPU authorization.

## Remaining independent prerequisites

Approval would authorize implementing and CPU-testing this exact amendment, not
claiming readiness or launching experiments. Still required:

- Actual reviewed external old-Stage-II/probe-consumption history; unknown original
  generation history cannot be silently certified as absent.
- Official-source availability and complete exclusion checks for 128 fresh groups,
  64 per source. A source shortage remains a stop, not permission to reuse groups.
- Clean reviewed/pushed revision, exact runtime and actual checkpoint verification,
  then separately invoked bounded GPU stages through the user's workflow.

Decision requested: approve this executed-source-preserving amendment and its
explicitly increased ceilings, or provide a different source/budget amendment.
Until decided, the existing real planning stop remains in force.
