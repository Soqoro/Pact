# PACT project review — 28 October 2026

## Review conclusion

PACT has a working, audited experimental pipeline, real completed adapter training,
and multiple development studies. The latest Stage I source evaluation gives a
positive **clean joint-versus-independent training result**. It does not establish
full PACT efficacy, a robust advantage under attack, or an improvement specifically
caused by using peer information.

Stage I amended evaluation is complete. Stage II has implementation and CPU-test
evidence, but no new authorized real execution or verified fresh evaluation cohort.
The original Stage II v3 cohort is infeasible under its preserved ARC exclusions.
The proposed OpenBookQA/LogiQA alternative remains a conditional design, not a result.

This report synthesizes existing audits and the experiment ledger. It does not
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
| Proposed evaluation-source amendment | CPU loader/auditor, selection, graph, scoring, exports and mock round trip | Implemented and CPU-tested; actual 64+64 eligibility unknown |

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

## 8. Proposed OpenBookQA/LogiQA amendment

A separate CPU-only implementation proposes 64 OpenBookQA main/train questions
plus 64 fresh original-English LogiQA questions. It retains fitting allocation,
probes, exact joint-trained S0, five allocation policies, optimizer/scoring
contracts, unchanged prompt templates and separate source reporting with equal
final weighting. Actual generated messages may differ across trained teams.

Implemented: bounded source parsing, provenance/rights evidence checks, grouping
and exposure exclusions, deterministic selection, proposed MethodSpec and request
graph, strict scoring, missingness-aware comparisons, PRIVATE/SANITIZED export and
reconstruction. There is no execute/download/approve/seal CLI in this child.

Conditional graph ceilings are 8,112 assay generations +15,616 policy-evaluation
generations =23,728 generations, 12,148,736 reserved output tokens, 3,072 updates,
24,576 supervised forwards and 2,640 diagnostic forwards. Fixture graphs reconcile
these counts. They are ceilings for a proposed experiment, not consumed work.
No actual candidate graph is frozen because a real cohort is unavailable.

| Evidence | Current finding |
|---|---|
| OpenBookQA immutable candidate | Revision `388097ea7776314e93a529163e0fea805b8a6454`, main/train Parquet |
| Advertised file identity | SHA256 `98148f8a54e62eb862346a75192d5fb824d6cbb68f2f59aecd793d39ecb5cd8b`, 495,845 bytes |
| Actual candidate bytes | Not acquired or verified locally |
| Dataset rights | Unresolved; no supported human approval receipt |
| Original LogiQA local source audit | Raw caches/rights and refreshed exclusions still needed |
| Current exposure inventory | Not yet complete/current for this selection |
| External historical Stage II consumption | Unresolved; local absence is not proof of remote absence |
| Eligible counts / selected cohort | Unknown / none |
| New GPU experiment | Not authorized or executed |

Public row counts and advertised hashes establish neither eligible groups nor
usage rights. The official landing-page redirect unexpectedly returned nine
OpenBookQA previews during documentation review; their identities are recorded in
the access review for exclusion. No question text is included here. Any subsequent
eligibility audit must account for that exposure and possible preview-coverage
uncertainty. Project-unexposed does not mean pretrained-model-unexposed.

Historical CPU results for this implementation: 20 new amendment tests, 24 existing
v3 tests, nine training-data tests and four exposure tests passed: **57 total**.
The real blocked review also exported/reconstructed on CPU. These are engineering
checks, not experimental outcomes or a rights determination.

The earlier frozen source review predates the metadata pin and preview exposure;
its bundles remain unchanged. The access-review addendum records the newer facts.
See [implementation review](../stage2_evaluation_source_amendment_review.md),
[access review](../stage2_evaluation_source_access_review.md), and
[CPU runbook](../stage2_evaluation_source_amendment_runbook.md).

## 9. Decisions for the user

1. **Scientific interpretation:** retain the positive clean source-development
   result while reporting null validation advantage, uncertain attack advantage,
   and unresolved peer-use mechanism alongside it.
2. **Stage II priority:** decide whether the allocation hypothesis still warrants
   the proposed cost. No current result shows allocation efficacy.
3. **Source prerequisite:** obtain applicable OpenBookQA and original LogiQA rights
   evidence. Then separately approve exact source acquisition and run the real
   byte/exposure/uniqueness audit. A generic approval cannot substitute for factual
   rights or eligibility evidence.
4. **Before any execution:** reconcile external consumption, review the 64+64
   candidate if feasible, freeze complete requests/analysis/budgets, verify effective
   checkpoints/native runtime, and give separate artifact-bound GPU authorization.

Human semantic review remains deferred. MBPP+ remains deferred pending isolation;
LiveBench remains blocked under its release-proof requirement; GPQA breadth Phase B
was not authorized. Full coupled PACT, Stage III, final tests and manuscript result
placeholders remain uncompleted. Completed diagnostics should not be reopened to
manufacture additional support.

## Report validation

This report was checked against the linked repository audits, current experiment
ledger and source-access review. Relative links and `git diff --check` were checked.
No unit suite, archive reconstruction, new statistical computation, source download,
model call, training, cluster job, commit or push was performed for this report.
The 57-test result above belongs to the preceding implementation work.
