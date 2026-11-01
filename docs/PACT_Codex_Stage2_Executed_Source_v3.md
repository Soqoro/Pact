# PACT Stage II — executed-source amendment, rigorous implementation-only specification (v3)

Prepared: 27 October 2026. Supersedes *proposed* `stage2-allocation-reviewed-v2` where inconsistent. **This is not approval for GPU execution, not a new experimental result, not a modification of the completed Stage I run.** Implement and CPU/mock-test in the existing PACT repository only. Read this entire specification, the earlier reviewed-v2 document, the actual executed Stage I source/lineage/plan manifests, the 27 October amendment and Stage I evaluation audit, AGENTS.md, exposure ledger, existing code, and any historical Stage II attempts. Resolve actual contracts from signed/immutable artifacts rather than copying reported counts unverified. Preserve unrelated changes and every old plan and recovered result.

## 1. Scope and research claim

Test whether a **communication-aware measurement of an actual short training update** improves allocation of further *private-answer* training across three heterogeneous communicating agents, beyond equally sized uniform, source-family, private-bank, and block-shuffled allocations.

S0 = exact saved epoch-2 `uniform_joint_sft` Qwen2.5-7B-Instruct (Q), Llama-3.1-8B-Instruct (L), Mistral-7B-Instruct-v0.3 (M) trio. One pristine Qwen3-8B readout R, explicitly non-thinking; pristine, adapter-disabled Q for attack generation. Exact model/tokenizer/template, adapter tensor hashes, loss mask, decoding, dtype and runtime come from the **executed** contracts and checkpoint verification receipts. Do not select another Stage I arm, model or checkpoint by favorable results.

Three separately invoked parts:
- A: **Read-only** Stage I mechanism reconstruction (zero model calls/updates).
- B: Crossed temporary-update assay with full checkpoint rollback, precommunication and postcommunication scoring. These labels and probes are **training-use meta-data**.
- C: Freeze five resulting training schedules, train matched continuations from S0, and evaluate on a newly frozen **common** prospective source-domain development cohort.

Stage III alternating/refreshed PACT, fresh model/agent families, GPQA/MATH/MBPP/LiveBench, adaptive attack search, frontier APIs, held-out final confirmation and new human reviews are OUT OF SCOPE. Two extra continuation seeds are not replicated Stage I training, and this is **static** allocation, not full PACT.

### Implementation-only authority
Local Codex can inspect/patch/code/test, with CPU fixtures or locally initialized tiny models. No pretrained local downloads, GPU inference/training, cluster/Colab launch, paid API, credentials, git commit/push/remotes, or historical deletion/migration. Actual model execution requires explicit user invocation after the checks and a separately frozen child plan. Implement both B and C, not merely config stubs.

## 2. Source-provenance amendment — no balancing by substitution

The reviewed-v2 **assumed** 4 ARC + 4 LogiQA fitting blocks and 32/32 probes. The 27 October proposed correction reports the **executed Stage I group identities** as:

| Source | Immutable 64-task fitting blocks | Fitting tasks | Same-source shared allocation probes |
|---|---:|---:|---:|
| ARC Challenge | **3** | **192** | **24** |
| Original English LogiQA | **5** | **320** | **40** |
| TOTAL | **8** | **512** | **64** |

Reconstruct **all exact task IDs, duplicate/content group IDs, block memberships and source revisions** from authoritative Stage I artifacts. If they disagree, produce `source_contract_conflict` and STOP the dependent real plan; do not manufacture 3/5 or use narrative reports as replacement source files. No moving groups, replacing questions, adding probes, or silently migrating an old 4/4 child plan. Use new child IDs after collision checks and complete request/plan hashes. Previous v2 attempts, if any, remain independently owned, not implicitly resumed. Never infer absence of historical GPU calls from an empty local search; reconcile the external prior Stage II/probe-consumption history and abort real execution if unresolved.

Every ARC branch uses **all same 24 ARC probes**; every LogiQA branch uses **all same 40 LogiQA probes**. Probe group identities are reused for comparisons, not treated as 816 independent tasks. Training update gradients never see probe text or labels. Those labels are only available to the scoring module, not the model input. Probes are no longer valid independent confirmation material.

Preserve the already specified solver mean over **8 block rows**, with `tau=0.2`, balancing coefficient `0.1`. In the row-mean objective, ARC contributes 3/8 and LogiQA 5/8; **this is not equal-source allocation learning**. Do not change to 50/50 optimization. Later prospective final metrics are **equal-source weighted**, and reports must show each source separately and disclose this training/evaluation mixture difference.

Before observing probe outcomes, prove the availability and freeze IDs of **128 fresh evaluation groups, 64 per source**, using only reviewed permitted sources. Exclude all existing fit/probe/Stage I validation/source-evaluation groups, earlier selective-correction and benchmark studies, protected/locked allocations, duplicate groups and known cross-source overlaps. If there is a shortfall, stop planning for the prospective policy comparison; do not consume thousands of assay GPU calls before discovering that a required evaluation is impossible. Task IDs/labels are sealed from allocation decisions and training. Attack-label access, if applicable, is evaluator-only after policy freeze.

## 3. Part A — read-only Stage I synthesis

Reconstruct actual frozen, independent-SFT and joint-SFT on-policy final outcomes under clean and **accepted exchange**; source-separated paired transitions, private coverage, revised availability/erasure, reader construction/loss, and strict failures. Separately reconstruct fixed-history receiver HOLD/REPAIR and peer-present/withheld comparisons. Do not infer missing attacked rows from the previously quoted +5.98 pp clean effect. Existing source/archive preservation limits remain reported, not retrospectively fixed. Never select a different S0 from these results. Zero model calls, optimizer updates and teacher-forced forwards.

## 4. Part B — actual temporary-update assay

For each of 8 actual 64-task fitting blocks and each of Q/L/M (24 branches):
1. Resolve and hash exact effective S0 FP32 adapter parameters and the clean corresponding optimizer/runtime baseline. Restore S0 identically for every branch, with no temporary-state leakage.
2. From a **fresh temporary** optimizer, do **8** private-answer optimizer updates (8 distinct fitting task groups/update, one pass over the 64; no receiver loss), LR and optimizer from the previously reviewed Stage II training contract. Test token masks, weight accounting and native model separation; no model swaps, changing training step count or synthetic-gold explanations.
3. For the source's **whole shared probe set** (24 ARC, 40 LogiQA), regenerate the updated actor's original private packet. Reuse the other two S0 private packets *only on exact dependency identity*.
4. Regenerate every affected receiver revision and frozen R final readout under CLEAN and, where the **pre-frozen one-attempt** message rewrite is accepted, EXCHANGE. A changed private answer also changes that adapter's receiver computation. Count all physical dispatched calls, even failed/ambiguous attempts. Use one predeclared paired rollout seed.
5. Score on permitted probe labels with the same pristine R, never showing those labels to the generated agents or attacker. Store terminal exact generated correctness and R answer-prefix NLL. Restore effective parameter hashes before the next branch; never keep temporary weights as policy continuation weights.

The one-sender outgoing-message replacement is identical for the two recipients, does not change that sender's saved private packet, is not returned to the sender, and is never a revised-peer chain. Use one frozen, label-aware wrong-option attack attempt per probe task before any candidate-update victim evaluation. Retain rejection/missingness and strict parser failures; no retry or outcome-directed targeting. Rejected exchanges do not become clean successes.

### Paired scores and support

Record raw finite per-answer R NLL and prospectively capped `min(raw_NLL, 10.0)` for both baseline and updated contexts. A nonfinite score is a technical failure, not zero or a silently clipped valid observation. Use the **same frozen R** and answer-mask/format contract for all families and conditions; precommunication score reads the **initial** packet bank, terminal score reads revised packets. They are two different contexts, so don't assert causal identification from their difference.

Terminal credit, per (block, actor), is half the mean R loss reduction on CLEAN tasks plus half on **accepted** exchange tasks. The precommunication control uses the same readout and source probes but **initial** packets only. Report both conditional and intended-cohort attack support. On each source, define comparable paired support without choosing tasks based on whether an update improved the answer; technical missingness across branches must be explicitly reported on full intended and common-support populations, with sensitivity/bounds. Do not conceal hard cases through a post-outcome intersection. An absent attack is not failure, zero, or success. If a source has no accepted exchanges, terminal clean-plus-exchange credit is undefined; follow a predeclared no-selection/report pathway rather than silently favoring clean.

The entire cross-assay is **one Stage I starting snapshot, one temporary-update RNG per branch and one probe rollout seed**. Repeated probes and branch views are correlated. Generate no extra probe draws to reduce uncertainty. Short update effects may not predict later permanent training; Part C tests that, not assumed additivity.

### Exact Part B ceilings

- Baseline probe trajectories: `64 * 11 = 704` generations.
- One-attempt probe attacks: `64` generations.
- Branch task views: `3 * (3*24 + 5*40) = 816`.
- At most `9` affected calls per branch view (changed private + 3 clean revisions + clean R + 3 attacked revisions + attacked R): `816*9 = 7,344`.
- **TOTAL assay: 8,112 calls; 4,153,344 reserved 512-token outputs.**
- Diagnostic readout scoring: `(64 + 816)*3 = 2,640` upper-bound forwards (initial-bank, clean-terminal, accepted-exchange-terminal).
- Temporary training: 24 branches * 8 steps = **192 updates**; **1,536** supervised sequence forwards.

These are upper bounds; no consumed attempts are replenished by caching, rejection, aliases or failed schemas. Keep generation, token, scoring, training and physical ownership counts separate.

## 5. From credits to explicit training schedules

Solve the existing convex masked balanced allocation over the **eight actual block rows** with `tau=.2`, balance `.1`, row sum 1 and three families. Use terminal scores for the **primary** `terminal_block` matrix, precommunication score for `private_bank`. Do not standardize by family, amplify near-flat differences, convert missing credits into measured zero or infer specialties from arbitrary hash blocks.

Convert each row to EXACTLY 12 integer extra eight-task update slots via deterministic largest-remainder rounding (`12 * r[B,i]`) with a **frozen outcome-independent** hash tie rule. If all rows round to 4/4/4, accept the scientific degeneracy and mark the method equivalent to uniform at this resolution; do not lower entropy or perturb credits after observing them. If a valid row lacks supported comparable credit, use a predeclared uniform row marked unsupported, never a manufactured measured zero.

Every family always receives one **full base pass over every block** (8 eight-example updates/block/family = 192 base updates/team), regardless of allocation. Extra slots total 12/block ×8 =96 extra steps/team. Thus **288 updates/team**, 2,304 supervised sequence forwards/team. An extra slot corresponds to a real optimizer update on a deterministic eight-example minibatch; do not express specialization solely as a constant adapter loss multiplier (Adam can approximately cancel that scaling). A persistent fresh optimizer is maintained **per family, policy and continuation seed**. Preserve prespecified base and extra task permutations and effective update order; no resetting Adam when moving between source blocks. Equal step totals are **not** equal FLOPs or training tokens when model families/sequence lengths differ; report exact per-family exposure and resource costs and do not claim equal-compute superiority without a separate matched-cost comparison.

Freeze exactly five prespecified policy definitions, two continuation seeds, identical S0 initialization and all compiled data schedules before prospective model evaluation:

1. `terminal_block` — primary; block-specific terminal credit allocations.
2. `uniform` — 4/4/4 extra updates per block.
3. `source_family` — preserve exact terminal per-source/per-family extra-update totals while distributing as evenly as feasible across **3 ARC or 5 LogiQA** blocks. Enforce all row totals `12` and all source/family column totals EXACTLY, not by independent rounding. Each source/family should have per-block counts `floor(T[s,i]/n_s)` or `ceil(T[s,i]/n_s)` where jointly feasible. Implement a deterministic integer-constrained routine (e.g. small min-cost flow / bounded search with frozen hash tie break), and fail with a mathematical witness if constraints are inconsistent. Do not substitute an approximate greedy distribution.
4. `private_bank` — derive quotas using **same R loss instrument**, solver, cap, and quota rounding on initial bank, no final-exchange scores.
5. `shuffled` — apply one **outcome-independent pre-frozen** within-source index derangement on the terminal quota rows, independently for 3 ARC and 5 LogiQA blocks. Preserve per-block row sums and all source/family totals. Rows can repeat; genuine full-schedule equality then constitutes an alias, not a reason to force a new shuffle.

Run exact schedule equality/alias detection from **full task/batch/update orders, initialization/optimizer/seed and runtime contracts**, not merely numerical row quotas. When execution identities are truly equal, run once and reference the identical observation—do not create fake independent repetitions or spend freed calls on new examples. A shuffled negative control with one fixed permutation cannot support a universal claim about all shuffles.

The communication-aware allocation and the source-family comparison receive the same total source/family extra-update quotas. Other controls can shift family mix. This separates block correspondence from coarse allocation, but **does not ensure identical FLOPs** across all five arms.

## 6. Part C — prospective complete-policy test

Use the previously frozen fresh 128 task groups (64/source). All teams use the **same** one-attempt, offline wrong-target attack pool and same trusted question/options. Generate attacks only **after schedules/policies are frozen** and before any defender evaluation. No success-driven payload selection or repeated attempts. Missing/rejected exchange conditions remain missing with denominators/bounds.

Train all five policy arms from the same S0 with two fixed continuation seeds (at most **10** trained teams) and evaluate an additional **unchanged S0** team. No choosing the best seed, adapter checkpoint, hyperparameters or source groups after results. Every team produces its own natural Q/L/M private packets, one synchronous clean and attacked revision, and the same frozen Qwen3-8B readout. One paired evaluation rollout seed across models and policies. Strict output failures remain failures. A model missing one of its three final adapters is incomplete, not an invitation to substitute S0.

**Primary endpoint:** final generated team correctness under accepted EXCHANGE attacks, with source-equal weighting; report clean correctness as a co-primary utility check. Primary paired comparisons are `terminal_block - uniform` and `terminal_block - source_family`; report `private_bank`, `shuffled`, S0 and each continuation seed. Do not report marginal private competence as demonstrated robust collaboration. Observe paired task transitions and common accepted-attack pool. Retain the prespecified exploratory clean-utility tolerance of 2 percentage points as descriptive, not a statistical guarantee.

Use task-group paired, source-stratified intervals; two continuation seeds share a single Stage I S0 and allocation-estimation history, so do not count them as independent studies. Label task/receiver/view observations as correlated. Report per-source and combined accuracy, conditional repair/hold, initial/revised coverage, erasure, readout loss, output validity, cost and source-specific missingness. If accepted attacks are absent in either source, the equal-source attacked endpoint is undefined: no favorable substitution.

The eight fitting blocks are hashed training partitions, NOT known semantic domains. Even a successful primary contrast would establish this **static block-aware allocation under the given attack and checkpoint**, not learned specialty identities, adaptive robustness, or original PACT's refreshed specialization–communication coupling. The additional block-specific signal is supported only if it beats source-family and preferably private-bank/shuffle controls on the common unseen tasks. Uniform joint training and true team-reward training remain important later baselines.

### Exact Part C ceilings

- Max teams: `5 policies * 2 continuation seeds + 1 unchanged S0 = 11`.
- Fresh eval generations: `128 tasks * 11 teams * 11 calls = 15,488`.
- One-attempt attack acquisitions: `128`.
- **TOTAL: 15,616 generations; 7,995,392 reserved output tokens.**
- Continuation training: `5*2*288 = 2,880` updates, `2,880*8 = 23,040` supervised sequence forwards.

## 7. Versioning, planning safety, and exact total ceilings

New child IDs must not collide with existing plans/attempts. Create a versioned **v3 amended** design: never edit an old Stage I manifest or reviewed-v2 plan in place. The amendment is implementation-only; Stage II/probe historical-consumption reconciliation is an explicit hard gate before any real model stage. Parent PRIVATE artifacts may be imported read-only and never contain trusted executable instructions.

Totals: `8,112 + 15,616 = 23,728` maximum generations, `12,148,736` reserved output tokens; `192 + 2,880 = 3,072` optimizer updates; `1,536 + 23,040 = 24,576` supervised forwards; `2,640` diagnostic scoring forwards (Part B). These ceilings **replace**, not add to, reviewed-v2 proposed budgets; no Stage I wallet recycling, attack retry, plus-one smoke, training sanity rerun or synthetic-forward GPU allowance. Strict context and generation caps from executed source manifests; do not invent a different runtime cap.

Stage progression, separately invoked and export-and-stop at each step:
0. **CPU implementation/preflight**: verify 3/5 source hashes, exact groups, history of external old Stage II calls, availability of 128 eligible fresh groups, S0 effective checkpoint provenance, new budget/attack identities and code tests. Block GPU readiness on unresolved prerequisites; do not confuse implementing code with granting execution approval.
1. **Assay smoke**: two fixed probes (one per source), complete original baseline clean/attack requirements, **at most 24 INCLUDED calls** (two attacks + 22 baseline calls). Bind exact new v3 request IDs; do not reuse abandoned 4/4 smoke IDs without proof of full identity. Export and STOP.
2. **Full assay**: run all 24 temporary branches and scoring under the amended request graph; one launch per explicitly authorized segment. Export; audit support, credits and full provenance. Stop; do not auto-start continuation.
3. **Policy freeze**: compute score/quotas/schedules deterministically without GPU. Detect aliases/degenerate uniform results. Export source/family/method matrices, tie/solver proofs, and one immutable child-policy plan.
4. **Continuation**: after independent user approval, train matched policy teams at frozen updates; export checkpoints, tensor hashes and resource records. Stop before prospective evaluation.
5. **Policy evaluation smoke**: two fixed **fresh** tasks (one per source), all 11 declared team identities, **at most 244 INCLUDED generations** (2 attacks + 2*11*11); aliases may reduce actual dispatch. Export and STOP.
6. **Complete prospective evaluation**: run remaining frozen tasks, emit PRIVATE and SANITIZED summaries, and read-only reconstruct all metrics/costs. No automatic Stage III/full-PACT.

All unknown in-flight physical attempts remain unresolved and count against the appropriate parent/child accounting until reconciled. Rejected attacks are unavailable, not attack-resistant successes; no budget replenishment or extra task selection. If the prior v2 assay has actually begun, preserve it and report a collision: **do not resume it as v3**. If the fresh 128-task cohort cannot be supplied under reviewed exclusions, mark `prospective_eval_not_feasible` and STOP GPU assay planning before exposing probes.

## 8. Required implementation and tests

Reuse real project CLI, staging, checkpoints, model/tokenizer/native template backend, immutable request journals, exposure-guard, strict parsers, summary provenance and PRIVATE/SANITIZED packaging. CPU/model-free tests must not load pretrained weights. Locally initialized tiny model checks are permitted without downloaded data. All task/peer/attacker text remains untrusted data, escaped in HTML/Markdown output. No arbitrary pickle/imported-code execution.

Minimum targeted tests:
1. Executed 3 ARC / 5 LogiQA block group IDs; 192/320 fitting; 24/40 probes; same-source sharing; old 4/4 manifests refused, no implicit resume/migration.
2. Freeze new 128 cohort/exclusions BEFORE assay; protected data denied; historical Stage II physical-attempt uncertainty blocks real dispatch, not local fixture implementation.
3. 24 genuine temporary updates with native mask and loss target, unchanged other adapters, full rollback (effective tensor hash and optimizer/RNG isolation), sequential model memory.
4. One changed private + all affected clean/exchange suffixes, pristine R and Q generator, exact ID-based reuse, correct source validity, strict malformed/missing behavior.
5. Common support scorer, raw/capped finite NLL, no gold leakage, separate initial versus terminal renderer; exact `2,640` forward ceiling; zero if unsupported not falsely measured.
6. Eight-row soft assignment solver: tau .2 /balance .1, 3/8 vs5/8 weighting, finite gradients and equal-credit invariance, deterministic row rounding to 12.
7. `source_family` constrained integer matrix: row sum12, exact source/family totals, floor/ceil per column; deterministic tie break, impossible-contract report; test random feasible margins.
8. Frozen 3/5 source derangements with full-schedule equality/alias detection and no cherry-picked permutation.
9. Base and extras as **real optimizer slots**, 288 updates/team, unchanged base per-family examples, true same-family RNG/optimizer persistence; report exact family exposure and physical cost.
10. Probe historical-use guard, checkpoint S0 proof, old v2 smoke rejection unless exact hashes, assay24-call and policy244-call smoke included in 8,112/15,616 ceilings.
11. 128-task common evaluation, accepted exchange missingness, paired task uncertainty, correct source-equal final evaluation despite 3/5 training weighting, no conditional-score pooling of calls as tasks.
12. Whole fake end-to-end pipeline: immutable plan -> assay -> credit scoring -> quota solving -> 5 policies -> real tiny adapter updates/restore -> mock eval -> export/reimport -> summary recomputation; all actual CPU test counts reported.

Implementation result must include source-contract and history resolution, files changed, exact real CLI/notebook commands, versions/hashes, all focused and relevant regression test results, consumed/remaining ceilings, checkpoint/probe/evaluation readiness, PRIVATE/SANITIZED output expectations and explicit **GPU NOT AUTHORIZED** status. Fail closed on real missing prerequisites; do not silently shrink cohorts, change numeric design or use extra calls. Do not claim scientific efficacy until the trained prospective policies are evaluated. 

BEGIN by inspecting the actual PACT checkout, source manifest/lineage and Stage II history; implement the complete amended B and C paths under CPU tests, without launching model work.
