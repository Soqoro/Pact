# PACT Stage II — Fresh evaluation-source amendment: rigorous reviewed v2

**Status:** IMPLEMENTATION AND CPU AUDIT ONLY. This is a proposed, separate child amendment to the blocked Stage II v3 plan, **not** source approval, a completed eligibility audit, GPU authorization, a new experiment, or a change to any historical record. Prepared 28 October 2026.

## 0. Mission, authority, and scientific boundary

Update the **EXISTING** PACT checkout, not a parallel pipeline. Read applicable `AGENTS.md`, working-tree status, Stage II v3 MethodSpec and runbook, Stage I authoritative source manifests, the 27 October Stage I completed evaluation audit, the 28 October `prospective_eval_not_feasible` report, exposure inventory and freshness policy, checkpoint/model registry, journals, source loaders, strict scorer, attack generator, and current CLI/tests. Preserve unrelated edits. Prefer checked-in, immutable evidence over narrative counts. Do not invent CLI paths, source hashes, or approval receipts.

The purpose is **only** to resolve evaluation-data feasibility for a prospective, static allocation-policy comparison. Preserve Stage II v3 as `prospective_eval_not_feasible`; do not silently edit, activate, resume, or relabel it. Create a new collision-checked **PROPOSED** child source amendment, with explicit parent lineage and incompatible request identities. A failure to meet a prerequisite is a completed blocker report, not permission to waive it.

Starting source facts claimed by the audit (reconstruct, do not take on faith): Stage I source SHA256 `85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`; reviewed parent PRIVATE SHA256 `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`; eight immutable 64-task fitting blocks: ARC 3 (192 groups), original English LogiQA 5 (320); fixed allocation probes ARC 24 / LogiQA 40; Stage I validation ARC 64 / LogiQA 64; Stage I source evaluation ARC 120 / LogiQA 136. Historically eligible ARC 406 with 400 uniquely allocated implies **at most six** under that policy; this is an upper bound, not a claim about the entire official dataset. Current LogiQA eligibility is not established by the old 6,045 bound.

**Keep all actual fitting/probe identities, checkpoint S0, objective, controls and original Stage II evaluation gates. Do not run the 64 allocation probes or any adapter update during this task.**

## 1. One candidate source and the exact changed estimand

Evaluate as the **first and only candidate** `allenai/openbookqa`, config `main`, split `train`, for **64 project-unexposed science questions**, together with **64 newly eligible original English LogiQA groups** from the identical permitted official source revision. Public documentation reports 4,957 OpenBookQA `main/train` rows and the four-choice schema; **4,957 is not an eligible-group count**.

Upstream references for identity and field discovery (not an instruction to download):
- https://huggingface.co/datasets/allenai/openbookqa
- https://github.com/allenai/OpenBookQA

Document the distinction: OpenBookQA+LogiQA is a new **closed-book science-transfer and within-source logical-reasoning development evaluation**, not a balanced ARC+LogiQA comparison, an official OpenBookQA leaderboard result, a clean test set, or an untouched final confirmation. OpenBookQA is publicly released and may have been included in model pretraining; project-ledger disjointness **does not establish pretraining disjointness**. The source choice occurs after inspecting Stage I outcomes; it must be declared as a post-Stage-I design revision, not a wholly preregistered original design. Do not claim source equivalence or guaranteed useful difficulty.

OpenBookQA `main` includes `id`, `question_stem`, `choices` (option `label` and `text` arrays), `answerKey`. The `additional` config contains overlapping IDs and extra facts/ratings and is **not a separate cohort**. Never use `fact1`, `humanScore`, `clarity`, annotator IDs, official science facts, gold labels, or any derived answer hints as generation context or selection criteria. Never use official `validation` or `test` to fill the shortage. Use no retrieval or external supporting facts; evaluation must be explicitly **closed-book** under the existing native prompts.

The Hugging Face card reports license `unknown`; the GitHub repository has an Apache-2.0 LICENSE, but that does **not** by itself certify rights to every data item. Record the exact applicable source terms and provenance. An unresolved rights question means `source_rights_unresolved`, **not** either "licensed for all uses" or "automatically prohibited". Human/source-owner resolution is a separate review decision before activation; do not fabricate legal approval.

If this candidate fails schema/permissions/provenance/eligibility, return a blocker. Do not silently substitute SciQ, QASC, ARC test data, `additional`, or prior exposed data. Suggestions for future sources may appear in a review memo only.

## 2. Two-mode source-access plan — resolve the previous contradiction

**Local implementation mode (always permitted):** CPU fixtures, repository-pinned source files and already authorized, accessible raw snapshots only. Locate actual mounted/cached bytes and existing source registry. Do not auto-download datasets/models, use credentials, execute remote dataset scripts, or fetch moving `main`/`latest` revisions. If bytes are absent, implement and test the adapter and audit code with synthetic fixtures; return `source_bytes_unavailable`, with no invented eligible count, hash, selected ID, or sealed cohort.

**Optional source-materialization mode (NOT automatically permitted):** Prepare a separate, explicit user-invoked CPU-only command/runbook for obtaining **only** the officially identified `main/train` file(s) at an exact immutable revision, conditional on separate approval of source access and rights. Pin upstream commit and content digest, limit file counts/bytes, verify checksum and schema before processing, never use `trust_remote_code`, scripts from the dataset repository, or untrusted pickle execution, and do not silently use a mutable auto-converted Parquet mirror. A curated manually provided snapshot with documented origin and verified hashes is also acceptable. Implement this option if it fits the existing safe downloader convention; **do not execute it now**. If no reliable source/rights path is available, report the blocker.

This sequence makes it possible to implement the auditor without pretending the dataset has already been audited or contradicting the no-automatic-fetch rule.

## 3. Exact source adapter and label separation

Reuse the original task/group representation, strict four-option parser, formatting contract and scoring code. Resolve OpenBookQA's actual nested choice structure without assuming choice labels are in a fixed order. Require exactly four distinct normalized labels A/B/C/D, four corresponding non-empty rendered choices, one matching `answerKey`, deterministic stable IDs, valid Unicode and bounded serialization. Preserve original option-to-answer mapping; do not permute choices, invent missing options, or strip question meaning to make a task fit. Reject/mark individual malformed items with reason codes **before** any model outcomes, and report all such exclusions.

Construct only the trusted question and options for agents and frozen readout. The attack generator sees those plus the preselected incorrect target and original approved style instruction, not gold labels, source tags, privileged science facts or defender outputs. Offline label-aware wrong-target selection may inspect gold in a trusted evaluator boundary; assert it never crosses into attacker/defender context as a gold field. Source metadata, subset/config and provenance labels remain offline.

Prompt **templates/contracts** and decoding are identical across methods. Do **not** demand byte-identical full prompts across different trained teams: legitimate private packets and delivered messages differ by model outcome. Enforce byte-identical fixed attack payload/sender for each evaluation task across policies, with complete request identities and correct arm-dependent private-state dependencies.

Any source-specific prompt, context cap, response-parser, attack-style or token-budget change is a **new proposed method/budget amendment**, not an implicit compatibility patch. Test the original output contract on fixtures; leave native-model tokenizer/context preflight for the later independently approved runtime.

## 4. Eligibility: project-disjoint, with explicit unknowns

Apply the **existing reviewed exposure policy** across all previously used or protected PACT groups, old ARC/LogiQA allocations, replay, selective correction, prior characterization/evaluation cohorts and relevant other datasets covered by the ledger. Resolve exact source revisions and exposure-inventory freshness; refuse an inventory whose declared review coverage is stale. Deduplicate by source stable ID **and** by the original reviewed canonical content/group identity, across sources where the policy supports it. Do not equate different public source identifiers with independence merely because the IDs differ.

Run the audit on BOTH candidate sources, then check cross-source collisions between the two selected populations. For duplicate and near-duplicate categories use only frozen, deterministic, source-blind rules; preserve reasoned counts. Flag potential semantic overlap/contamination as unresolved for separate reviewer inspection; don't selectively discard challenging/correct items after seeing model outputs or run unapproved semantic filtering. Unknown prior exposure is `unknown`, not "fresh". Model pretraining exposure is **unknown unless separately established**, and cannot be eliminated by project-ledger hashes.

Produce actual permitted/denied/unknown item counts and unique group counts with per-source rejection reasons. The old LogiQA remaining count is an **upper bound** only. A cohort passes this stage only if there are at least 64 currently permitted *unique groups* from each source with current lineage, source-rights status, and documented cross-source exclusion findings.

## 5. Freeze one prospective 128-group cohort before exposing probes

Before any Stage II probe-generation, allocation-score, temporary-update or continuation outcome:
1. Fix candidate source/config/split, exact revision(s) and file hashes; document schema and rights status.
2. Fix the existing reviewed filtering/grouping policy and its version. Resolve any material overlap cases or mark cohort unsealable.
3. Fix the deterministic, outcome-independent selection rule **before** applying it. Proposed namespace: `pact-stage2-openbookqa-logiqa-eval-amendment-v2`; derive seed from the frozen method seed `20261016` plus this namespace or explicitly bind a new prespecified seed **in the proposed MethodSpec before revealing any allocation outcomes**. No seed or example cherry-picking based on answer labels/difficulty/model behavior.
4. Select exactly 64 OpenBookQA+64 LogiQA unique eligible groups, with a private ordered manifest, source-group/content fingerprints and a full cross-source uniqueness check.
5. Separate evaluator-only answer labels and attack-target logic from defender/attacker generation. Make cohort contents and annotations inaccessible to allocation/training selection; record access restrictions.
6. Record an immutable candidate selection digest; **`candidate_selected` is not `cohort_approved`**. Seal/activate only after human approval of source rights, source revisions, review and lineage; never by automatic CLI success.
7. Once sealed, freeze all evaluation prompts/parsers/metrics, attack-generation style/sender/seed policy, conditional missingness rules, readout and model contracts, paired contrasts, cost ceilings and smoke identities. No post-probe or post-smoke changes without a separately versioned amendment.

State explicitly: final evaluation source weights are **1/2 OpenBookQA and 1/2 LogiQA**, with per-source results and uncertainty. The *training-block allocation solver* stays **3/8 ARC and 5/8 LogiQA**; never relabel new OpenBookQA tasks as ARC training blocks or claim these mixtures are equal.

## 6. Keep all Stage II science unchanged

For future, separately authorized execution only, keep:
- S0: actual final epoch-2 `uniform_joint_sft` Q/L/M adapters, effective tensor identities; pristine Qwen3-8B nonthinking R; pristine adapter-disabled Q as attack generator.
- Fit/probe: 3 ARC+5 LogiQA immutable 64-task blocks, shared probes 24 ARC /40 LogiQA; total 24 temporary branches, **8 private-answer optimizer steps** each, one paired rollout seed, exact S0 restore, no probe gradients. The update affects the shared adapter's private and revision roles; no false pure-private causal interpretation.
- Terminal/prior-private-bank credits use same frozen R, existing NLL mask and cap, tau=.2/balance=.1, source row-mean 3/8 vs5/8, no fabricated zero or artificially enlarged variation. All 64 repeated probes are training-use metadata, not evaluation material.
- After credit freeze, 12 additional eight-example optimizer slots/block plus eight base slots/family/block, deterministic constrained integer quotas, exact source-family margins, frozen 3/5 derangement, exact schedule aliases, persistent per-family optimizer as specified. **Five** policies: `terminal_block` primary, `uniform`, `source_family`, `private_bank`, `shuffled`; **two** continuation seeds from S0. No score tuning, checkpoint selection, change to source family baseline, receiver-loss refresh, Stage III, extra agent or new attack family.
- In future evaluation, each team's own private outputs feed its own clean/exchange synchronous revisions; one frozen R final readout per condition. Same one-attempt corruption pool per task across all teams, sender independent of outcomes, correct accepted/rejected/missingness treatment. Missing attacks never become clean equivalences or defense successes.

This study can test **static allocation effectiveness** and transfer under a fixed one-sender attack; even favorable findings do not prove Stage I improved peer utilization, distinct semantic specialties, adaptive robustness or full refreshed PACT efficacy.

## 7. Evaluation outcomes and scientific reporting constraints

Prespecify: primary paired final-team correctness difference under **accepted exchange attacks** between `terminal_block` and (a) `uniform` and (b) `source_family`, separately by source and equal-source weighted. Clean final correctness is a co-primary utility check. Report `private_bank`, `shuffled`, unchanged S0, each continuation seed, model output validity, private coverage, post-revision erasure/repair, final readout loss, and inference/training/attack/diagnostic costs. The same attack is paired across policies, but source/acceptance strata differ. **Conditional attacked results are not full-population robustness.** Report attack-acceptance rates, planned-population denominators, descriptive bounds and missingness; if no accepted attacks in either source, combined equal-source attacked outcome is undefined and no favorable fallback is allowed.

Paired uncertainty must cluster by underlying task group and stratify by source, preserving all arm/seed/condition views. Two continuation seeds share S0 and contribution estimates; they are **not** independent replications of the overall learning method. A 64-per-source study may be underpowered for small gains; do not add tasks sequentially or tune the source/prompt after seeing accuracies. Attribute changes carefully: prompts differ by generated content, format validity may explain some effects, and the scientific comparison is not a causal test of the original Stage I receiver mechanism. Keep output reports explicit about OpenBookQA public training split, closed-book evaluation, and potential pretraining contamination.

## 8. Budget accounting: carry over only if protocol is unchanged

Provided the verified adapter uses the exact same two-condition protocol (3 private, 6 revisions, 2 R final generations =11/team/task), budgets remain **conditional upper bounds**, not approved expenditure:

| Component | Max generation calls | Reserved output tokens at 512 |
|---|---:|---:|
| Shared-source temporary-update assay | 8,112 | 4,153,344 |
| Five policies×two continuation seeds + unchanged S0 on 128 new tasks, plus 128 shared attack acquisitions | 15,616 | 7,995,392 |
| **Combined** | **23,728** | **12,148,736** |

The assay has 192 temporary optimizer updates /1,536 supervised forwards /2,640 frozen-readout diagnostic scoring forwards. Policy continuations have 2,880 optimizer updates /23,040 supervised forwards. Combined: 3,072 optimizer updates and 24,576 supervised forwards. All forwarded scores, prompt tokens and per-family training/compute costs are distinct from generated calls. The included assay smoke `<=24` and policy smoke `<=244` apply only if the **new** exact request IDs match the frozen smoke manifest; no plus-one smoke budget. Rejected attacks, exact reuse and aliasing do not create reallocatable capacity. Do not reset or transfer Stage I/old-v3 wallets.

Compile the exact amended dependency/request graph and verify counts, hashes, subset sizes, and reservation before declaring any method ready. If the dataset forces more calls, longer outputs, different contract or unreviewed scoring, mark `budget_or_protocol_conflict` and require separate approval. Old and unknown historical physical attempts must remain distinctly accounted; no assuming an empty local registry proves remote absence.

## 9. Required CPU-only implementation and tests

Implement reusable, fixture-backed source adapter and audit commands under the **existing** CLI design; no dummy config-only implementation. Tests must include:

1. Historical v3 `prospective_eval_not_feasible` remains immutable; new child IDs/hashes cannot collide and old 4/4 manifests cannot be implicitly resumed.
2. Source schema for `main/train` includes nested choices; reject duplicate/unknown labels, invalid gold key, missing content, additional-config extra hints; exact answer-option round trip.
3. Source revision/digest binding; missing raw bytes and unknown rights yield distinct **BLOCKED** states, not fake PASS; optional explicit acquisition plan does not run automatically.
4. Executed Stage I 3/5 fitting groups, 24/40 probes and exact reviewed exposure/overlap rules are intact. No use of protected/source-evaluation items as training or probes.
5. Both sources' 64 eligible unique groups and mutually disjoint selection are verified only with **real approved bytes**, not synthetic tests. Synthetic fixtures demonstrate logic only.
6. Before probes, selection is fixed, answer-label isolation enforced, and all versions/seed/IDs are bound; no reroll or after-outcome reselection.
7. Same original attack contract/one-attempt wrong-target procedure; no gold in model/attacker prompt; no model-output-based sender/style/target choice.
8. Same frozen prompt/decoding **templates** and accepted-payload identities across policies; arm-specific full prompts may differ due to generated packets.
9. Full matched five-policy allocator remains functional with real slots, exact 12-block row sums, source-family totals, deterministic 3/5 shuffle, aliases and no simulated outcome claims.
10. Math: assay 8,112, policy 15,616, full 23,728, 2,640 scorer forwards, 3,072 optimizer updates; included smokes verified under **new child** request identities.
11. Source-separated paired evaluation and conditional/missingness-aware primary endpoint; explicit pretraining exposure unknown; no conflation with official OpenBookQA test scores.
12. End-to-end CPU mock: source import -> real canonicalization/exposure guard -> cohort selection -> proposed child MethodSpec -> request manifest -> mock scoring/export -> read-only reconstruct; PRIVATE contains sensitive IDs/text/labels, SANITIZED excludes raw task strings and per-ID decodable hashes.

Run relevant existing regression tests; report tests actually run, passes/fails/skips and known limitations. Do not load/download pretrained models. Locally initialized tiny-model tests permitted if not pulling new network dependencies. Fail closed on unexpected data provenance or an unknown source contract.

## 10. Handoff: decision-ready, never auto-approved

Return: exact changed files; verified source/config/split/revision/raw SHA256 or precise absence; rights status with source citations (no invented license); audited eligible/dropped/unknown counts from **real** material when available; fresh LogiQA audit; candidate 64+64 cohort manifest roots (if and only if supported); a PROPOSED child MethodSpec and cost reconciliation; exposure-inventory freshness report; CPU tests run; CLI commands implemented; precise steps for separately approved source acquisition if missing; PRIVATE/SANITIZED review outputs; and exact blockers for historical Stage II probe use, native checkpoint tensor/reload verification, full request/budget freeze, and human GPU authority.

Use explicit statuses such as `implemented_fixture_only`, `source_bytes_unavailable`, `source_rights_unresolved`, `eligibility_verified`, `candidate_selected`, `cohort_approved`, `gpu_execution_authorized`. Never conflate these or present a proposed candidate as a sealed experiment. The new child is non-executable by default. No new training, GPU calls, cluster actions, pretrained downloads, unauthorized dataset downloads, paid APIs, credentials, remote changes, commits/pushes, destructive cleanup, or opening protected tests. Do not perform background work.

**BEGIN:** inspect actual repository and executed Stage I source contracts; check which pinned candidate-source bytes are genuinely available, then implement the adapter, auditing logic and proposed child compilation. If data or rights are missing, complete CPU implementation and return a precise blocker rather than fabricating eligibility.
