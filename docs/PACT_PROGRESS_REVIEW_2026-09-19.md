# PACT progress and results review

Review date: **19 September 2026**. Scope: work completed through
`qwen3-base-control-001`, using the repository's retained run audits and returned
Colab artifacts. Latest executed code commit:
`80992b48f9159c427d65e87cbd80849af295021b`.

**1. Current position**

We have built and exercised the experimental infrastructure, completed an
80-task validation pilot, verified counterfactual continuation replay, trained a
small engineering warm start, collected a training bank, and completed a matched
base-model diagnostic. The latest recorded software suite passes all 97 tests
with optional tiny CPU neural checks enabled; the default suite passes 92 and
skips five optional checks.

**Full PACT training has not been implemented or executed. No improvement from
PACT has been demonstrated.** The only real optimizer run so far is a nine-update,
12-task clean-answer warm start. Joint specialization/revision optimization and
bank refreshes remain deferred. Receiver preference data is also unresolved:
the completed sampling checks have produced no usable same-context receiver
preference pairs.

The latest control found that the unadapted base also fails on all 24 tested
receiver completions. This does not support attributing that shortage to the
small warm start. It does not prove the warm start had no effect, or that pairs
cannot be obtained on a broader training population.

This report consolidates current evidence. Earlier run reviews retain the next
steps and limitations known at their original dates; later completed audits
supersede those historical status statements. No new model run or methodology
change is part of this review.

**2. Research objective and implemented protocol**

PACT asks whether learning complementary capabilities according to their value
after communication, together with learning when to retain or revise an answer,
improves attacked team performance beyond simpler alternatives.

The implemented core protocol uses three agents. All private packets are generated
and frozen before delivery. Each agent then revises using its own original packet
and the other agents' original messages. A frozen base-model readout sees only
the revised packets. One exchange attack replaces one sender's outgoing message
identically for both recipients, while preserving the sender's saved private state.
Early attacks instead place an advisory note before private generation.

Counterfactual replay substitutes one private packet and reruns the downstream
revisions and final decision, pairing attack bytes, model snapshot and corresponding
node seeds across branches. Missing correct/incorrect candidate pairs remain
missing. Labels, correctness annotations and receiver strata remain outside the
defender inputs.

Real runs use pinned Qwen3-8B, BF16/SDPA, thinking disabled, on the reported NVIDIA
L4 environment. Private/revision sampling uses temperature 0.7, top-p 0.8 and
top-k 20; the main readout is greedy. The QA context cap is 4,096 tokens, with
256-token private/revision caps and a 64-token final-answer cap. Executed short
sequences do not verify memory fit at the full context limit.

Scientific source: [proposal](PACT_Conference_Proposal.tex) and
[implementation specification](PACT_IMPLEMENTATION_SPEC.md).

**3. Work completed**

| Area | Delivered and verified | Important remaining boundary |
|---|---|---|
| Experiment framework | Python CLI, pinned configurations, deterministic manifests, protocol/baselines, metrics and raw trace export | Full study orchestration remains incomplete |
| Data preparation | Official validation loaders; separate training loaders; frozen 12- and 1,200-task balanced training selections | The 1,200-task selection is prepared data, not a completed training run |
| Split discipline | Source hashes, separate labels, exact/lexical duplicate screening and logged exclusions | Semantic paraphrase and final-test overlap audits remain unperformed |
| Colab durability | Scratch-first operation, immutable shards, verified snapshots, timeout workers, local ZIP before final Drive copy | Current Drive contents are not independently inspected locally; not every GPU restore/failure path has run |
| Inference and baselines | Real smoke, profile and 80-task pilot; all pilot raw records audited | No trained-method comparison or final-test evaluation |
| Counterfactual credit | Real paired suffix replay; exact branch invariants and credits audited | Selected, small K=2 observations are not population effect estimates |
| Learning foundations | CPU-tested masked assignment, missing-pair accounting, preference construction, loss calculations and reference cache/scorer | Real GPU frozen-reference preference scoring has not executed |
| Warm start | Nine optimizer updates, fresh-process continuation, three frozen adapter exports | Engineering-sized clean-answer training only; no demonstrated capability gain |
| Training bank | Six records, 218 generations, five private pairs, actor answer/packet scores | Zero receiver preferences; full revision objective not ready |
| Base control | 54 matched calls on saved prompts/seeds; complete artifact audit | Two training tasks, with all receiver contexts on one task |
| Full PACT | Proposed objective and local components retained | Sequential joint updates, sparse-support collection and refresh schedule remain deferred |

The data audit parsed 1,119 ARC training rows and 7,376 LogiQA training rows, plus
950 validation rows. It excluded 59 redundant training rows, leaving 1,118 ARC
and 7,318 LogiQA tasks eligible under the declared rules. No train–validation
matches or conflicting labels were found under that exact/lexical screen. This
is not a semantic-decontamination claim. Final-test files were not accessed.
[Data evidence](training_data.md).

**4. Completed run sequence**

Counts below distinguish tasks, experiment records and model calls. Repeated
conditions and sampled continuations are not additional independent tasks.

| Run | Scope | Completion and key result |
|---|---|---|
| CPU development round trips | Synthetic fixtures | Protocol, interruption/resume, archive integrity and reporting exercised; no scientific results |
| `qwen3-smoke-001` | 4 validation tasks; 24 scheduled records | 20 applicable + 4 N/A; 152 calls; debate/synthesis each 2/4 clean and 0/4 early |
| `qwen3-profile-001` | 20 validation tasks; debate in 3 conditions | 60/60 records; 500 calls; clean 9/20, early 3/20, exchange 9/20 |
| `drive-storage-check-001` | Synthetic storage check in Colab | 12/12 records and reported verified Drive snapshot/ZIP; not model inference |
| `qwen3-pilot-001` | 80 validation tasks; 6 natural baseline paths | 1,440 scheduled records: 1,120 applicable + 320 N/A; 5,912 calls; full raw audit completed |
| `qwen3-replay-check-001` | 3 selected validation tasks; clean/exchange | 6 records; 386 calls; 13 private pairs and 52 suffix branches; no receiver pairs |
| `qwen3-warmstart-001` | 12 training tasks; 3 LoRA agents | 9 optimizer updates, 36 example presentations; continuation and 3 frozen exports completed |
| `qwen3-bank-001` | 2 training tasks; clean/early/exchange | 6 records; 218 calls; 5 private pairs and 20 suffix branches; no receiver pairs |
| `qwen3-base-control-001` | Same saved actor-produced contexts | 54/54 base calls; no correct receiver outputs or receiver pairs |

The profile completed inference but stalled during final persistence for roughly
30 minutes. All 60 records were recovered after restart. This led to storage
changes that write a local recovery ZIP first, bound Drive operations and verify
durable copies before reporting completion. The subsequent mock storage check
and pilot handoff exercised the normal repaired path. All 1,440 pilot records
were later recovered and audited after a runtime reset.

**5. Main validation results: 80-task pilot**

This is the largest completed performance diagnostic: 40 ARC-Challenge and
40 original English LogiQA validation tasks, using unadapted base-model samples.
Every applicable entry below has denominator 80. Exchange is N/A for methods
without a peer-exchange channel; N/A is not a robustness score.

| Method | Clean | Early advisory attack | Exchange corruption |
|---|---:|---:|---:|
| Single agent | 45/80 — 56.25% | 13/80 — 16.25% | N/A |
| Independent voting | 45/80 — 56.25% | 12/80 — 15.00% | N/A |
| Independent frozen synthesis | 47/80 — 58.75% | 12/80 — 15.00% | N/A |
| Ordinary debate | 47/80 — 58.75% | 10/80 — 12.50% | 46/80 — 57.50% |
| Ignore peers | 48/80 — 60.00% | 11/80 — 13.75% | N/A |
| Archive initial + revised drafts | 47/80 — 58.75% | 12/80 — 15.00% | 47/80 — 58.75% |

Natural archive uses additional input context. These are not fully matched-cost
trained comparisons. The separately planned matched-control run has not been
completed, and the SAC/composition baselines required for the research claim
have not been evaluated.

The main observations are:

- **Early exposure sharply reduces performance in this fixed-pool diagnostic.**
  Debate falls from 47/80 to 10/80, while initial team coverage falls from 47/80
  to 13/80. Much of the loss occurs before communication; it cannot all be
  attributed to harmful revision.
- **Useful initial diversity is sparse.** Only three clean teams contain a mix
  of correct and incorrect private answers. Multiple samples alone have not
  established useful learned specialization.
- **Preservation and readout failures are both observable.** One correct minority
  is erased in both clean and exchange debate. The sole additional exchange final
  failure occurs despite two correct revised packets and ends in final abstention.
  These are distinct failure mechanisms.
- **Simple controls remain competitive at the observed point estimates.** Ignore
  peers is one task ahead of clean debate; archive is one task ahead under exchange.
  These small differences do not establish population superiority or equivalence.

The recorded task-clustered bootstrap interval for each of those one-task
advantages is [0, 3.75] percentage points, using 1,000 resamples and one diagnostic
seed. Ties and small discordances do not establish non-inferiority or stability
across training seeds.

The full raw audit checked all 1,440 records and 5,912 calls. All generations end
at EOS; 124 actual generations are abstentions, with no malformed or length-limit
completions. Protocol, attack, seed and prompt checks passed. This validates the
recorded experiment; it is not an evaluation of trained PACT.
[Pilot results](reviews/qwen3-pilot-001.md);
[full raw audit](reviews/qwen3-pilot-001-raw.md).

**6. Counterfactual replay and receiver-pair feasibility**

A private-packet pair and a receiver preference pair serve different purposes.
The former enables a continuation-credit estimate by substituting a correct and
an incorrect private proposal. The latter requires correct and incorrect revision
completions sampled under the exact same receiver prompt. Private-pair success
does not make revision preference training ready.

| Check | Private-packet pairs | Eligible receiver contexts sampled | Receiver preference pairs |
|---|---:|---:|---:|
| Smoke probe | 0/9 | 0 | 0 |
| Profile probe | 0/18 | 2 hold | 0 |
| Pilot probe on 4 tasks | 0/36 | 2 hold | 0 |
| Selected validation replay check | 13/18 | 8 hold + 8 repair | 0/16 |
| Training bank | 5/18 | 2 hold + 4 repair | 0/6 |
| Fixed-context base control | Not a new private replay bank | Same 2 hold + 4 repair contexts | 0/6 |

These rows must not be pooled as independent task samples: selections and contexts
overlap, and the final control explicitly reuses training-bank contexts.

In the selected validation replay check, 13 private pairs yield five credits of
+1, two of +0.5 and six of zero; five missing credits remain null. All 52 positive/
negative suffix branches pass paired attack, state and seed checks. Three pairs
are not length-bin matched and remain flagged. Tasks were selected after observing
mixed initial outcomes, and K=2 is small, so these values verify the estimator's
execution rather than a representative effect size.

Receiver sampling in that check produced four candidates per context. Six hold
contexts were all-correct and two all-wrong; one repair context was all-correct
and seven all-wrong. There were correct receiver outputs, but never both answer
classes within one sampled context. This is different from the later training
bank, whose 24 receiver outputs contain no correct answer at all. No valid pair
was lost through the audited parsing or selection rules.
[Selected replay audit](reviews/qwen3-replay-check-001.md).

**7. What was actually trained**

The engineering warm start used 12 training tasks, six per family, presented once
to each of three agents in separately recorded orders: 36 example presentations
and 216 target completion tokens. Each agent received three optimizer updates,
for nine total. Targets were canonical answer-only JSON plus EOS, rather than
generated rationales or revision preferences.

Configuration: BF16 backbone, FP32 LoRA parameters, rank 16, alpha 32, q/v target
modules, zero dropout, microbatch one and effective batch four. Training stopped
after the first optimizer boundary, persisted, and continued in a fresh process
through update nine. All logged losses and gradient norms are finite. Losses
across different batches/agents range approximately 0.0032–1.1554; this is not a
before/after learning curve.

Three frozen warm-start adapters were exported with distinct hashes. Metadata,
checkpoint continuity, task order and export configurations passed audit. The
runtime reports verification of exported weights against actors. The review ZIP
omits tensor payloads, so those values were not independently compared locally.
Distinct adapter hashes do not establish useful specialization, and no paired
accuracy evaluation demonstrates a warm-start gain.

Fresh-process GPU continuation is verified by returned evidence. Bitwise
equivalence to an uninterrupted GPU control, actual post-reset warm-start Drive
restoration and full-context training-memory fit remain unverified.
[Completed warm-start review](reviews/qwen3-warmstart-001-complete.md).

**8. Training-bank results and matched base control**

The frozen warm-start actors were used on two prespecified training tasks:
`arc_challenge:MCAS_2004_5_13` and `logiqa:train-7374`, each under clean, early and
exchange conditions. Collection completed all six records across two invocations;
the first shard and resource attempt were preserved unchanged during continuation.

All six main trajectories fail. Five of 18 private contexts yield usable pairs,
giving 20 suffix branches: four credit estimates are zero and one is +1. The
remaining 13 private pairs are missing. Eighteen actor answer-NLL and five
positive-packet NLL forwards execute, but zero receiver preferences qualify and
therefore no GPU frozen-reference preference scoring runs.

The 24 receiver candidates are 14 wrong answers and ten abstentions, all on the
LogiQA item. The next diagnostic compares saved actor outputs with 54 fresh
unadapted-base outputs on exactly the same prompts, token prefixes, seeds and
sampling settings, with matching model/runtime identities.

| Fixed context group | Saved warm-start actors | Fresh unadapted base |
|---|---|---|
| ARC private — 15 samples | 0 correct, 15 wrong | 0 correct, 15 wrong |
| LogiQA private — 15 samples | 6 correct, 9 wrong | 7 correct, 8 wrong |
| LogiQA hold — 8 samples | 0 correct, 8 abstentions | 0 correct, 8 abstentions |
| LogiQA repair — 16 samples | 0 correct, 14 wrong, 2 abstentions | 0 correct, 16 wrong |

All 54 base calls pass artifact audit and end at EOS, without format or truncation
failures. Thirty-five raw outputs and completion-token arrays are identical to
their paired actor outputs. Neither policy has a receiver preference pair.

The evidence does not support blaming the small warm start for the receiver
shortage. One additional correct private base sample is too little to establish
a capability difference. Both the task/context support and the prompt behavior
remain open explanations. The LogiQA item's option wording is flagged as a
possible confound; its official gold label A was preserved, not changed after
seeing outputs.

The control receives actor-produced peer contexts, so it does not estimate an
independently generated base team's performance. It is also a diagnostic on
training tasks already used by the warm start, not held-out performance evidence.
[Training-bank audit](reviews/qwen3-bank-001-complete.md);
[base-control audit](reviews/qwen3-base-control-001.md).

**9. Recorded resources and reliability limits**

| Stage | Generation calls | Generated tokens | Recorded invocation time |
|---|---:|---:|---:|
| Smoke | 152 | 6,954 | 9.94 min |
| Profile | 500 | 24,041 | 28.82 min |
| Pilot | 5,912 | 285,294 | 340.73 min |
| Selected replay | 386 | 18,046 | 23.02 min |
| Training bank, both invocations | 218 | 10,588 | 15.94 min |
| Base control | 54 | 3,275 | 5.73 min |
| Warm start, both invocations | Not generation | 216 training target tokens | 3.80 min |

The six generation stages total **7,222 calls, 2,476,522 input tokens and 348,198
output tokens**. Their recorded invocation times sum to approximately **7.07 hours**;
including the small warm start gives **7.13 hours**. This is a sum of logged stage
timers, not GPU-active time, billed time or total project cost. It excludes notebook
setup outside those timers, final persistence/export work, local development and
the profile's approximately 30-minute finalization stall. Warm-start targets and
teacher-forced scoring tokens are separate from generated-token totals. No run
or exported copy is counted twice. Colab compute units and monetary cost are unknown.

Recorded inference peak allocations are roughly 15.4–15.6 GiB. The warm-start
continuation peaks at approximately 15.89 GiB allocated / 16.25 GiB reserved.
These figures apply to the executed lengths and environments only.

Evidence quality is strongest where full raw records were returned and metrics
were reconstructed. The pilot, selected replay, training bank and base control
have detailed raw audits. The warm-start review is metadata-based for tensor
state. Reported verified Drive copies are distinct from independently reading
current remote objects. Review ZIPs that omit tensor files or shard markers must
not be treated as complete resume archives.

**10. Conclusions supported by the evidence**

| Supported now | Not established |
|---|---|
| The bounded inference, replay and artifact-review pipeline works on the reported environment | End-to-end full PACT learning works |
| Correct initial answers can be erased, and correct revised answers can be ignored by readout | Preservation training improves terminal accuracy |
| Eligible private counterfactual pairs and nonzero credits can occur | Those credits produce useful specialization after optimization |
| The small warm start executes and exports reloadable actors used by collection | Warm start improves capability or creates useful diversity |
| Current bounded receiver samples lack same-context preference pairs | Receiver pairs are impossible on broader training data |
| Base also fails on the training bank's fixed receiver contexts | The warm start is the cause, or definitely has no effect |
| Simple untrained controls are competitive in this pilot | PACT beats matched composition, independent methods or adaptive attacks |

No final-test evaluation, full 1,200-task warm start, 300-record refresh study,
joint specialization/revision update, adaptive attack evaluation, SAC composition
comparison or BFCL transfer experiment has been completed. Paper result
placeholders remain unfilled.

**11. Decisions for this review**

The immediate review question is whether to proceed with a broader, prespecified
training-only feasibility check before investing in the full trainer. The existing
two-task bank is too narrow to establish data support, and the fixed-context
control has completed its purpose. Repeating either run unchanged would add cost
without addressing that coverage limitation.

The following decisions remain open; this report does not implement them:

1. **Data support:** choose an outcome-independent training selection, fixed query
   budget and explicit stopping rule; report hold and repair availability separately.
2. **Diagnostic scope:** decide whether to first review task wording and current
   receiver prompts, keeping any prompt variant explicitly separate from the
   already completed protocol and results.
3. **Training scale:** distinguish a capability-oriented warm start from the
   completed nine-update engineering test, with a declared budget and validation rule.
4. **Learning gate:** require actual same-context preference data and real reference
   scoring before claiming a full revision objective; retain missing data honestly.
5. **Research gate:** require comparisons against simple controls and the planned
   composition baseline before attributing any later improvement to PACT's coupling.

No further GPU work is needed to review the evidence in this report. The current
working tree includes the latest artifact-review documentation; no commit or push
was made as part of preparing this report.

**12. Evidence index**

- [Implementation status](implementation_status.md), [decisions](implementation_decisions.md),
  and [experiment ledger](experiment_ledger.md): detailed provenance and milestone history.
- [Smoke](reviews/qwen3-smoke-001.md), [profile recovery](reviews/qwen3-profile-001.md),
  and [storage check](reviews/drive-storage-check-001.md).
- [80-task pilot](reviews/qwen3-pilot-001.md) and [complete raw review](reviews/qwen3-pilot-001-raw.md).
- [Selected replay](reviews/qwen3-replay-check-001.md) and [training-data audit](training_data.md).
- [Completed warm start](reviews/qwen3-warmstart-001-complete.md) and
  [collector/reference CPU checks](reviews/collection-implementation-001.md).
- [Completed training bank](reviews/qwen3-bank-001-complete.md),
  [diagnostic implementation tests](reviews/preference-feasibility-001.md), and
  [completed base control](reviews/qwen3-base-control-001.md).

Original ZIPs, extracted records, audit scripts and derived metrics are retained
under the Git-ignored `results_import/` directory. The evidence links above identify
their paths and checksums. Latest returned ZIP SHA256:
`49bf59ceaeabcd917a91db4fef0ab0ed92fb05a367bd5233c05bc1fe3e1dc954`.
