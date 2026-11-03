# PACT project review — 2 November 2026

## Review conclusion

PACT has a working, audited experimental pipeline, real completed adapter training,
and multiple development studies. The latest Stage I source evaluation gives a
positive **clean joint-versus-independent training result**. It does not establish
full PACT efficacy, a robust advantage under attack, or an improvement specifically
caused by using peer information.

Stage I amended evaluation is complete. Stage II has implementation and CPU-test
evidence, but no new authorized real execution or verified fresh evaluation cohort.
The original Stage II v3 cohort is infeasible under its preserved ARC exclusions.
The latest proposed GPQA Main/LogiQA alternative remains uncertified. The scoped
history assessment is complete with residual uncertainty, and a finite future-work
accounting proposal is implemented but inactive. **There are no new Stage II
scientific results.**

This report synthesizes existing audits, the experiment ledger and the latest
exposure/accounting decision packet. It updates the 28 October review without
changing its historical evidence. It does not
repeat raw-archive verification, inference, training, or statistical analysis.
Historical audit statements such as “next stage pending” describe their dates;
the latest completed-stage status below takes precedence for this synthesis.

## 1. Work completed and its disposition

| Workstream | Work performed | Result or current status |
|---|---|---|
| Protocol and infrastructure | Private packets, synchronous exchange, frozen readout, attacks, replay, strict parsing, budgets, safe resume, private/sanitized handoffs | Operational engineering foundation; not itself scientific efficacy |
| Early preparation | Small warmstart and larger actor preparation training; matched diagnostics | Training ran; larger matched probe correctness did not improve |
| Natural receiver learning | Preference feasibility, supervised answer-prefix objective, hold/repair support audit | Sampling/support gates prevented the bounded natural study from training |
| Controlled receiver supervision | Frozen, task-SFT and receiver-SFT arms; 24 focal updates in each trained arm | Matched receiver correctness unchanged across arms |
| Specialization/replay | Natural support screen and separately controlled replay | Natural support insufficient; controlled replay closed incomplete with historical uncertainty |
| Heterogeneity/breadth | ARC/LogiQA pilot, MMLU-Pro, MuSR, MATH; GPQA private-answer diagnostic | Useful diversity varies by model and source; communication is not uniformly helpful |
| Fixed-bank adjudication | Clean decision modes and wrong-rationale variants, 5,340 calls | Peer rescues coexist with regressions; rewrite sensitivity observed |
| Selective correction | Five real CPU gate fits and frozen development evaluation | All chose KEEP_ONLY; no learned correction benefit |
| Selector clarification | Fresh paired 404-call output-contract comparison | Large compliance improvement, only one clean rescue |
| Heterogeneous training revival | Independent adversarial SFT and uniform joint SFT for Q/L/M | Six completed 128-update fits on the amended committed path |
| Stage I amended evaluation | Validation, source evaluation, fixed-history controls; included smoke | Complete: 13,467 committed calls, no unresolved child attempts |
| AAI migration | Runtime/container, checkpoint transport, private storage and execution checks | Fixed-history evaluation completed on AAI; completed evidence imported locally |
| Stage II v2/v3 | CPU implementation and executed-source reconciliation | v2 allocation conflict; v3 retains executed allocation but lacks fresh ARC capacity |
| Proposed evaluation-source amendments | Earlier OpenBookQA alternative; latest GPQA Main/LogiQA loader, audit, selection and graph | Official GPQA/original source acquisition reported verified; actual 64+64 eligibility not certified |
| Exposure and accounting reconciliation | Scoped history review, conservative exclusion union, inactive future-work proposal | No further broad search required; factual scope and approval decisions remain |

Q/L/M in the heterogeneous studies denote Qwen2.5, Llama3.1 and Mistral families.
Their pristine common readout R and the older Qwen3 preparation actors are distinct
identities. Cross-study rates must not be pooled as if they used one population,
model, prompt or scoring contract.

## 2. Earlier results that motivated the current work

### Receiver supervision and specialization

The controlled receiver study retained the same correctness on all 57 matched
receiver responses across frozen, task-SFT and receiver-SFT arms: 40 correct and
17 wrong. Repair with correct donors was 1/6 in every arm; without peers it was
0/6. Repair target NLL fell from 11.3762 to 8.3008 to 6.3415, but this did not
translate into improved correctness. Nonfocal precision rounding was recorded and
matched through explicit effective-initialization recovery, not silently repaired.

Natural specialization yielded only five eligible cells on two supported tasks,
below the eight-task requirement. Controlled replay recorded 125/132 zero primary
cell effects and seven nonzero cells across six tasks, but incomplete calibration
and unsafe interruption prevented a valid assignment-contrast conclusion.
“Not evaluated completely” is different from “shown ineffective.”

### Diversity and communication

| Development cohort | Tasks | QLM private correct coverage | QLM valid correct/wrong mixed support | Initial synthesis → final exchange readout |
|---|---:|---:|---:|---:|
| ARC/LogiQA pilot | 80 | 63 | 47 | 43 → 40 |
| MMLU-Pro | 140 | 61 | 42 | 40 → 43 |
| MuSR | 90 | 62 | 38 | 45 → 46 |
| MATH-500 | 100 | 74 | 56 | 81 → 77 |
| New GPQA breadth cohort | 32 | 16 | 12 | Phase B not executed |

Coverage is the existence of a correct private answer, not final success.
Disagreement between wrong answers is not correct/wrong support. Heterogeneity
was not uniformly superior: MATH QQQ coverage was 84/100, above QLM's 74/100.
The original adapted-Qwen3 GPQA study was separate and sparse: coverage 9/32,
only two valid mixed teams, and voting/synthesis/debate each 7/32.

### Adjudication, gates and selector contract

Fixed-bank adjudication completed 5,340 calls with zero unresolved attempts.
Task-only answering had the highest clean point estimate in each MMLU/MuSR ×
J8/J14 block. Full-packet selection rescued 15/25, 12/24, 13/19 and 10/17 available
opportunities, respectively, but regressed on 28, 32, 15 and 12 independently correct
tasks. Rescue existed without positive net performance.

Wrong-candidate rationale edits could change decisions while correct packets were
preserved. This establishes sensitivity to tested rewrites, not a semantic causal
explanation. Independent semantic reviews and cue/sham intervention remain deferred.

All five selective-correction gates chose KEEP_ONLY. The primary development
result was 44/64 correct, zero switches, rescues or harms. A separate selector
clarification increased validity from 0/202 fresh legacy responses to 190/202;
clean deployed correctness rose from 44/64 to 45/64 through one rescue. Eight
available clean rescue opportunities remained unused. Formatting improvement did
not solve candidate selection or establish a safe learned correction policy.

Sources: [14 October research synthesis](PACT_RESEARCH_DECISION_REVIEW_2026-10-14.md),
[selective correction](PACT_SELECTIVE_CORRECTION_CORE_2026-10-15.md),
[selector decision review](PACT_GATE_SELECTOR_DECISION_REVIEW_2026-10-15.md).

## 3. Completed heterogeneous adapter training

The continuation path completed independent and joint adapters for Q, L and M:
128 updates per fit, 768 committed updates overall (477 inherited +291 new).
All six epoch-two mean training losses were below epoch-one means. These losses
are descriptive training diagnostics, not held-out efficacy or comparable rankings
across objectives/families.

The replacement parent's step 94 remains unknown. The replacement-plus-continuation
physical bound is at most 769 updates; older original-run history remains separate.
Completed continuation does not retroactively close lost work or make unsafe
historical snapshots safe.

Final checkpoint evidence was subsequently verified for evaluation and AAI
migration. The earlier metadata-only completion audit is not itself tensor proof.
See [training completion](../revival_continuation_completion_audit.md) and
[checkpoint verification](../stage1_checkpoint_verification_audit.md).

## 4. Latest Stage I performance

Three arms were compared: frozen heterogeneous actors, independent adversarial
SFT, and uniform joint SFT. Source rates are weighted equally. Exchange results
use only common accepted attacks and must not be compared directly with all-task
clean results as if they covered identical populations.

| Cohort / condition | Frozen | Independent | Joint | Joint − independent | Descriptive interval |
|---|---:|---:|---:|---:|---:|
| Validation clean, 128 tasks | 70.31% | 74.22% | 74.22% | 0.00 pp | −7.44 to +7.81 |
| Validation accepted exchange, 99 tasks | 63.42% | 68.32% | 72.30% | +3.98 pp | −4.11 to +12.23 |
| Source clean, 256 tasks | 56.57% | 63.21% | 69.19% | **+5.98 pp** | **+1.17 to +11.77** |
| Source accepted exchange, 205 tasks | 43.60% | 58.62% | 63.19% | +4.56 pp | −2.39 to +12.37 |

Source evaluation used exactly 120 ARC and 136 LogiQA tasks. Clean correct counts
were 144,159,175; joint versus independent gained 35 tasks and lost 19. Most of the
net increase was LogiQA (+14 correct) versus ARC (+2).

The clean source result is positive development evidence. It did not replicate as
a clean advantage on validation. Neither primary exchange interval establishes a
positive attacked advantage. The source exchange missing-outcome bounds over all
256 intended tasks are −16.27 to +23.58 pp, retaining 51 rejected attacks as missing
conditions rather than failures or successful defenses.

Intervals use the frozen 500-replicate source-stratified task/group bootstrap.
Calls and receiver views are not independent sampling units. These are development
results, not untouched final-test confirmation.

Sources: [validation audit](../stage1_amended_validation_audit.md),
[source-evaluation audit](../stage1_amended_source_evaluation_audit.md).

## 5. Does joint training specifically improve peer use?

Fixed-history controls hold private histories fixed and compare peers present
versus withheld. These are receiver correctness rates, not final team accuracy.

| Condition | Independent present | Independent withheld | Joint present | Joint withheld |
|---|---:|---:|---:|---:|
| Clean, 64 tasks | 53.13% | 47.40% | 69.27% | 61.46% |
| Accepted exchange, 53 tasks | 51.28% | 52.59% | 60.68% | 56.32% |

Peer-access interaction is `(joint present − joint withheld) − (independent present − independent withheld)`:

| Condition | Interaction | Descriptive interval |
|---|---:|---:|
| Clean | +2.08 pp | −5.73 to +9.38 |
| Accepted exchange | +5.67 pp | −1.60 to +13.83 |

Both intervals span zero. Much of the clean joint-over-independent gain remains
without peers. Frozen clean receiver accuracy was 60.94% present and 51.56%
withheld: independent SFT fell below frozen on both views, while joint exceeded it.
The independent comparator's degradation is relevant to interpreting the gain.
Family interactions differ; aggregate improvement is not proof of a common
communication mechanism.

Source: [completed fixed-history audit](../stage1_amended_fixed_history_audit.md).

## 6. Stage I accounting and migration

| Amended evaluation component | Committed new calls |
|---|---:|
| Validation, including smoke | 3,876 |
| Source evaluation | 7,836 |
| Fixed history | 1,755 |
| Total | **13,467** |

The completed child has zero unresolved attempts and 6,895,104 reserved output
tokens, below its 14,592-call /7,471,104-token ceilings. Packet statuses were
12,482 ok, 834 invalid and 151 abstentions across phases. No new optimizer updates
or training forwards occurred in this evaluation. Rejected conditions and exact
reuse explain reduced calls; spare budget does not authorize additional work.

AAI migration reproduced the recorded Python/package/GPU runtime fingerprint,
verified transport against Drive, verified six checkpoint tensor files and staged
private data under `/dataset/suaq0001/PACT`, with hot execution under `/local`.
Authentication, tokenizer dependencies, certificates and container lifecycle issues
were diagnosed before successful fixed-history execution. Remote execution was
performed by the user; local review verifies returned artifacts, not independently
reproduced GPU logits or direct access to the cluster filesystem.

Final PRIVATE SHA256:
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
Final SANITIZED SHA256:
`1c4474a57bb28bd228040a32c496b6426e21531112e493b06be47dca0741047a`.
The completed audit validated all 13,467 journal calls and reproduced four reports.
Historical unknown work remains separate; this report does not invent a complete
project-wide compute total.

## 7. Why Stage II is blocked

Reviewed-v2 required four/four fitting blocks and 32/32 probes while retaining an
executed source with three ARC/five LogiQA blocks and 24/40 probes. V3 preserves the
actual allocation, but still requires 64 fresh ARC plus 64 fresh LogiQA groups.

| Historical pool accounting | ARC | LogiQA |
|---|---:|---:|
| Historically eligible | 406 | 6,605 |
| Already allocated in Stage I | 400 | 560 |
| Remaining upper bound | **6** | **6,045** |
| Fresh groups required | 64 | 64 |

ARC is short by at least 58. Redownloading, changing seeds or reusing excluded tasks
does not resolve this under the existing contract. LogiQA's upper bound is not a
current eligibility certification. Existing v3 remains `prospective_eval_not_feasible`.
See [fresh-source decision](../stage2_v3_fresh_source_decision.md).

## 8. Latest GPQA Main / LogiQA proposal

The current proposed evaluation cohort is **64 GPQA Main groups and 64 fresh
original English LogiQA groups**. All Diamond protections survive within Main.
This changes prospective evaluation sources, not Stage II fitting methodology.
The earlier OpenBookQA implementation remains historical; its recorded preview
exposures remain excluded and its unresolved rights are not silently approved.

The proposal preserves the exact Stage I joint-trained starting checkpoint S0,
three ARC/five LogiQA fitting blocks, 24/40 allocation probes, five allocation
policies, optimizer/scoring contracts and fixed scientific seeds. Prospective
science-transfer and LogiQA results would be reported separately and weighted
50/50 overall. Project freshness never establishes absence from model pretraining.

### Source audit findings

The user executed official source acquisition and CPU audits on AAI. Job 1112958
reported verified pinned GPQA and original ARC/LogiQA bytes, with no model work.
These are returned remote receipts; this report does not freshly hash remote files.
GPQA revision: `83022cefff930aea54f654c0b282e74b9eeda5c6`.

| Finding | Meaning |
|---|---|
| GPQA Main: 448 records | Actual audited source size, not eligible cohort size |
| 198 Diamond-protected records | Existing historical/protected exclusions preserved |
| 3 GPQA option-integrity flags | Multi-reason flags overlap; do not subtract counts as disjoint sets |
| 249 GPQA unique groups with only scope uncertainty | Potential capacity, **not certified eligibility** |
| LogiQA: 7,376 audited items | Original training-source inventory |
| LogiQA: 1,335 denied; 6,041 unknown | Denials include 58 duplicate-group and 1,277 historical/protected items; unknown items are not unique eligible groups |
| Permitted counts returned as zero | Eligibility gate withheld permission; not proof the source contains zero usable questions |

Historical GPQA partitions were verified: original support selected 32, protected
164 and excluded two; breadth partitioned the protected pool into 32 characterization,
32 locked confirmation and 100 locked reserve questions. Historical selected cohorts
were disjoint. No protected partition was released by this audit.

The current exposure inventory lacked newer experiment-ledger, parent-source,
coverage and overlap-review bindings. An old `reviewed_complete` flag cannot certify
the newer scope. Job 1113032 created a **draft**, adding all 960 executed Stage I
allocations to the conservative exclusion union:

| Inventory field | Before | Draft union |
|---|---:|---:|
| Task IDs | 15,368 | 16,328 |
| Group IDs | 14,864 | 15,824 |
| Content groups | 1,504 | 2,464 |
| Cross-dataset fingerprints | 13,466 | 14,426 |

These are different identity representations of one union, not separate exposure
events. The source auditor already excluded executed allocations directly; do not
subtract 960 again from its provisional results. Historical GPQA partitions and
repository selections added no further identities to this union.

**Feasibility remains unestablished:** the provisional capacity looks sufficient,
but no real 64+64 cohort has been certified, selected and frozen under accepted
current exposure evidence. Source bytes alone do not resolve eligibility.

Sources: [GPQA proposal review](../stage2_gpqa_logiqa_review.md),
[scoped history review](../stage2_scoped_history_review_2026-11-02.md), and
[exposure/accounting decision packet](../stage2_exposure_accounting_decision_v2.md).

## 9. What the history investigation established

We investigated whether earlier Stage II probe or training work could affect
source independence, reuse or spending. The bounded assessment is now complete
with residual uncertainty; repeating the same broad scans would not close it.

- The Slurm inventory inspected 30,707 JSON records across four recorded roots
  and found no matching candidates. Some directories, symlinks and archives were
  outside that inspection scope.
- The broad Drive scan hit its limit after inspecting only one JSON record.
  Its lack of matches cannot establish absence of execution.
- Continuation and replacement snapshot inventories listed no probe-training,
  probe-score or score-intent artifacts. These checks were metadata-only;
  replacement remained unsafe.
- The verified retained original step-28 archive contained **2,438 Stage I
  generation intents**, no Stage II intents and no listed probe artifacts.
  Intents do not automatically prove completed physical calls.
- Later original-run archives are missing and its latest snapshot is incomplete.
  An earlier retained boundary cannot close that interval or authorize resume.

Therefore **no Stage II execution was found in the inspected evidence**, but
historical Stage II spending and probe adaptation remain unknown. No finite
remaining balance or complete project-wide compute total is established. The
user's uncertainty has not been turned into a claim that nothing ran.

The bound original source contains only the 960 ARC/LogiQA allocations. That
supports conditional nonintersection with new GPQA and LogiQA outside the complete
exclusion union **if the original contract remained in force**. Missing later
execution compliance remains unproven. This is a scoped review decision, not a
reason to declare every future source contaminated or every source fresh.

See [the bounded evidence and exact identities](../stage2_scoped_history_review_2026-11-02.md).

## 10. Latest implementation and inactive accounting proposal

A new CPU decision-packet module separates factual exposure, review acceptance
and unknown spending. It reads a finite allowlist of metadata, verifies lineage,
retains exclusions, distinguishes physical executions from repeated exports and
preserves missing history. It does not modify the active GPU or history gates.

The private review queue has two scope decisions: current coverage and material
overlap. It does not invent thousands of manual pair reviews or fabricate semantic
labels. Applicable existing review receipts can be reused; concrete unresolved
pairs require private review only when evidence identifies them.

The proposed alternative is an explicitly bounded **future allowance**, not a
claim that old allowance remains unspent. Its acceptance, signature and effective
boundary are unset. No accepted reuse, active wallet or execution approval exists.

| Conditional proposed component | Ceiling |
|---|---:|
| Assay baseline/attack generations | 768 |
| Assay branch generations | 7,344 |
| Assay total generations | 8,112 |
| Policy-evaluation generations | 15,616 |
| Total generations | **23,728** |
| Reserved output tokens | 12,148,736 |
| Temporary / continuation updates | 192 / 2,880 |
| Total optimizer updates | 3,072 |
| Supervised forwards | 24,576 |
| Diagnostic scoring forwards | 2,640 |

The 24-call assay smoke and 244-call policy smoke are included. These quantities
are conditional compiled contract arithmetic; no actual eligible cohort/request
graph has been frozen. Unknown past work plus a future allowance does not yield a
verified finite cumulative historical total. A new run name cannot reset spending.

Tests executed in the preceding implementation work:

| CPU suite | Passed |
|---|---:|
| Exposure/accounting decision packet | 17 |
| GPQA source-amendment regression | 21 |
| Evaluation-source regression | 20 |
| Total | **58** |

Shell syntax and whitespace checks passed. The real local metadata packet was
built and reread idempotently. This proves engineering behavior within tested
scope, not real cohort eligibility, scientific efficacy or GPU readiness.

Outputs include a PRIVATE exposure/history packet, SANITIZED summary and proposal,
checksums and CPU receipt. The readable
[inactive proposal](../stage2_future_accounting_proposal_v2.json) and
[implementation/validation details](../stage2_exposure_accounting_decision_v2.md)
are available for review. No raw GPQA content is reproduced here.

## 11. Decisions remaining before Stage II

| Prerequisite | Current state |
|---|---|
| Completed Stage I evaluation and checkpoint evidence | Available; completed records unchanged |
| Original Stage II v3 ARC cohort | Infeasible; remains blocked |
| Official replacement-source integrity | Reported verified remotely |
| Current exposure coverage and material-overlap scope | Unresolved acceptance/evidence gaps |
| Certified, frozen 64+64 cohort | Absent |
| Bounded historical assessment | Complete with residual uncertainty |
| Finite future-accounting amendment | Proposed, inactive |
| Accepted exact reuse / remaining balance | None / unknown |
| GPQA child real GPU integration and current preflight | Separate work still required |
| New Stage II execution | Not authorized; no scientific result |

The next useful review is a decision about the precise coverage and overlap scope,
followed by the finite future-accounting proposal and its possible prior-probe
adaptation limits. Neither approval can substitute for factual source eligibility.
With those issues resolved, the unchanged deterministic source audit can establish
whether a real cohort exists, and a separately reviewed plan can bind the actual
requests, checkpoints, analysis and budget before any execution.

The scientific decision is whether the allocation hypothesis warrants that work.
Our strongest current evidence supports a clean source-development advantage for
joint training; it does not yet show allocation efficacy, robust attacked gains,
or a clear peer-use mechanism. Stage II should test those narrower hypotheses,
not be presented as confirmation that full PACT already works.

Semantic forensics remains deferred. MBPP+ remains deferred pending isolated
execution; LiveBench remains blocked by release-proof requirements; GPQA breadth
Phase B was not authorized. Full coupled PACT, Stage III, untouched final tests
and manuscript result placeholders remain uncompleted.

## Report scope and verification

This is a documentation synthesis of linked audits and the current decision packet.
It preserves the older reports and all existing local changes. Relative links,
selected accounting arithmetic and whitespace were checked for this report.
The 58-test outcome above belongs to the preceding implementation, not a fresh
unit-suite run. No archives, source bytes, model outputs or statistical estimates
were independently regenerated for this report. No source acquisition, cluster
job, model call, training, deletion, commit or push was performed.
