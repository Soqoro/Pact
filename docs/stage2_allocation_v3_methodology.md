# Executed-source Stage II v3 implementation

Version `stage2-allocation-executed-source-v3`; CLI `pact allocation-v3`.
Implementation approval only. **GPU NOT AUTHORIZED.** Historical v2 code, plans,
results and its `pact allocation` route remain separate and unchanged.

The implementation uses new candidate children:
`pact-update-allocation-crossed-v3-003` (physical portfolio root) and
`pact-allocation-policy-evaluation-v3-002` (logical policy child, separately frozen
in `policies.json`). Existing roots/plans cannot be re-planned. Version, owner,
source, code and complete dependency hashes reject v2 resume or request reuse.

## Verified source, and the remaining feasibility stop

The exact Stage I PRIVATE archive SHA256 is
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
Seven authoritative source/plan/lineage/checkpoint files are individually pinned.
Both evaluation and executed-training source manifests agree byte-for-byte under
canonical hashing. The complete source hash is
`85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`;
the exact block-membership hash is
`40892bfd28b458bdd6438b47ea5909467d690df5c66b5789f11182e618925644`.
Counts alone cannot satisfy this check.

| Source | Immutable blocks | Fit groups | Shared probes |
|---|---:|---:|---:|
| ARC Challenge | 3 | 192 | 24 |
| Original English LogiQA | 5 | 320 | 40 |

The v2 4/4 and 32/32 conflict is resolved by this approved implementation amendment.
**A different blocker remains:** the verified original eligibility receipt records
406 eligible ARC groups, of which 400 were allocated across all Stage I splits.
Preserving all original exclusions leaves **at most six** fresh ARC groups, at least
58 short of the required 64. LogiQA's corresponding upper bound is 6,045. This is
a monotone bound from the verified historical eligibility receipt, not a new raw-source
measurement; subsequent exclusions can only reduce availability. Real planning
returns `prospective_eval_not_feasible` before consuming assay calls. It never
substitutes older questions, test material or invented fixtures.

A complete external Stage II/probe-consumption review is independently required.
A local search found no such attempts in inspected imported evidence; this does not
certify absent remote history. Unknown original work remains unknown. History review
must bind the exact parent/source and evidence hashes, establish no old Stage II/probe
consumption and no unresolved probe-consumption window. Current tensor bytes must
also be reverified at execution; verification of historical receipts is not a new
local verification of all real tensors.

## Executable assay and continuation

S0 remains the exact final epoch-2 joint Q/L/M adapters. Every branch uses a fresh
optimizer, eight private-answer steps on its unchanged 64 fitting tasks, then exact
adapter/RNG rollback. Only the selected adapter changes. Updated private and all
three receiver revisions plus pristine R regenerate for each eligible condition;
unchanged private packets reuse only full model/prompt/seed/request identities.
Pristine Q makes one attack attempt per probe, frozen before victims. Initial peers
remain frozen and one corrupted outgoing packet goes to both other recipients only.

Raw finite pristine-R answer NLL and `min(NLL,10)` are recorded for both initial-bank
and revised-bank contexts. Answer-bearing prefix tokens alone are scored; no EOS,
rationale, receiver training loss or probe gradients. Terminal credit averages clean
and accepted-exchange gains .5/.5. Technical missing scores stop policy selection;
reports expose intended/paired/all-branch common support and bounded missing-score
sensitivity. They never select a favorable intersection. No accepted exchange in a
source means undefined terminal credit and explicitly unsupported uniform rows.

The solver still averages eight block rows, tau .2 and balance .1: **3/8 ARC, 5/8
LogiQA allocation weighting**, not 50/50. Final prospective evaluation is 50/50.
Hamilton rounding allocates 12 actual extra update slots per block. Every family
receives all base examples once, with fixed base/extra pools, repeat cycles and
interleaving. One fresh persistent AdamW per family/policy/seed retains state across
blocks. LR 5e-5, no warmup, clip one, zero decay, betas .9/.999, eps 1e-8; BF16
frozen bases, FP32 LoRA and optimizer state. No constant loss-scaling substitute.

Five policies and seeds 113/227 remain fixed. `source_family` jointly enforces exact
row sums and source/family column totals with floor/ceil distribution over three or
five blocks and a deterministic feasible-matrix tie break. Invalid constraints fail
with a witness. `shuffled` freezes one actual 3/5 within-source derangement before
scores. Full schedules, initialization, optimizer/RNG, native/runtime and source
contracts determine aliases; no forced differences or recycled budgets.

The 128 fresh evaluation groups must be sealed before the assay. Their IDs/text/labels
are absent from the public training/allocation plan; it contains only count and a
sealed-file hash. All final policies, checkpoints and analysis lock before evaluator
access. S0 and all unique policy executions share the attack pool and paired rollout;
strict invalids are failures and missing attacks stay missing. Primary attacked
contrasts are terminal_block minus uniform/source_family, with clean utility, other
controls, each seed, per-source and equal-source estimates. Ten thousand task-cluster
bootstrap replicates keep both seeds together; 95%/97.5% intervals are descriptive.
Full intended-cohort bounds accompany incomplete intersections. HOLD/REPAIR uses the
actual delivered peer context, and remains an on-policy descriptive cohort.

Reports separate physical and alias-expanded logical calls, per-family updates,
training tokens and model-session resource records. Equal updates are not equal
FLOPs; FLOPs and compute units are not inferred from token counts.

| Ceiling | Assay | Policy | Portfolio |
|---|---:|---:|---:|
| Generation calls | 8,112 | 15,616 | 23,728 |
| Reserved output tokens | 4,153,344 | 7,995,392 | 12,148,736 |
| Updates | 192 | 2,880 | 3,072 |
| Supervised forwards | 1,536 | 23,040 | 24,576 |
| Diagnostic forwards | 2,640 | 0 | 2,640 |

The 24/244 smoke calls are INCLUDED. Synthetic GPU allowance is zero. Reports give
consumed and remaining ceilings; skipped/rejected/aliased calls do not replenish them.

Each explicit stage exports and stops. Typed checkpoints, per-operation durable intent
markers, compact metadata snapshots and separately addressed tensor objects preserve
known work. Unknown attempts block execution; latest-only restore rejects missing or
unsafe boundaries. No automatic pruning. PRIVATE contains traces; RECOVERY adds typed
tensors; SANITIZED is an aggregate allowlist. All scientific GPU behavior, throughput
and full-study storage requirements remain unverified for v3. Stage III and full PACT
remain deferred.
