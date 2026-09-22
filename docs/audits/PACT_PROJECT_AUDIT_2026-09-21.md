# PACT project audit — 21 September 2026

## Audit conclusion

PACT has an operational local-to-Colab research pipeline, real Qwen3-8B inference,
verified examples of paired neural suffix replay, two completed bounded supervised
adapter-training recipes, and imported/recomputed diagnostic results. **We have not
trained or evaluated the complete PACT objective, demonstrated a PACT advantage,
or run the final test benchmark.**

The recurring scientific obstacle is usable same-prompt receiver preferences:
observed four-sample pools have only correct outputs, only wrong outputs, or
abstentions. Private packet replay pairs do exist on selected cases, but those
are not receiver DPO pairs. Increasing clean-answer preparation from 12 to 120
tasks did not improve matched private or fixed-history receiver correctness.

This report supersedes outdated current-status statements in historical ledger
entries. It separates executed work from designs and software tests. Underlying
imported outputs are preserved. Numerical findings below come from linked local
reviews and returned artifacts, not mocks or manuscript placeholders.

## 1. Scope and evidence standard

Local work: package development, CPU tests, source/data audits, safe archive
inspection, protocol reconstruction, metric recomputation and experiment design.
Real model runs were executed by the user in Colab and audited from returned files.
The recorded environment uses Qwen3-8B, BF16, SDPA, thinking disabled, on an NVIDIA L4.
Three logical actors share a frozen backbone and use separate adapters after warm start.
This does not certify arbitrary hardware, software versions or 4,096-token training fit.

Code baseline at this audit: `6364c52906c190890e7c1cce580951d3a3cb8fdd`.
The working tree additionally contains uncommitted reports/design metadata; this
report is not a claim that those changes have been published. Older experiments
have their own immutable source/config/model identities in their linked reviews.

Evidence strength differs:

1. CPU fixtures verify implementation behavior, not neural efficacy.
2. Returned raw calls support exact reconstruction of recorded prompts, seeds,
   attacks, outputs and scores; local audits do not independently regenerate logits.
3. Training ZIPs contain metadata and tensor inventories, not optimizer/adapter
   tensor bytes. Reported runtime tensor checks are not independent local rehashes.
4. Persistence receipts support successful copying at the recorded time. They do
   not establish current Drive availability or replace the full object store.

For this consolidation, all **19 top-level retained ZIPs** were reread, SHA256-hashed
and CRC-checked successfully. [Archive inventory](../../results_import/project-audit-20260921/archive_inventory.csv)
records filenames, sizes, hashes and member counts. CRC/hash inventory is not a new
semantic re-audit of every historical run; those audits are linked below.

## 2. Implemented system and tests

| Capability | Evidence/status |
|---|---|
| Typed task/label separation, deterministic identities, CLI and artifact validation | Implemented and CPU-tested |
| Three private packets frozen before synchronous revision; one outgoing corruption delivered identically to recipients | CPU-tested and reconstructed from returned raw trajectories |
| Revised-packet readout with adapters disabled; named archive baseline distinct | CPU neural isolation tests and recorded real-run protocol evidence; omitted tensors limit independent GPU isolation proof |
| Single, vote, synthesis, debate, ignore-peers, archive; fixed early/exchange attacks | Real validation diagnostics completed; matched-cost study not completed |
| Private alternatives, missing-pair accounting and paired suffix replay | Real eligible branches executed and audited |
| Masked responsibility solver, NLL/DPO numerical functions, same-context preference builder, reference cache | CPU and selected tiny-neural tests; not evidence of full GPU PACT optimization |
| Clean-answer LoRA training, checkpoints, final exports | 12-task and 120-task recipes completed; metadata audited |
| Frozen actor bank collection and answer/positive-packet scoring | Real six-record bank completed; no usable DPO pairs or GPU frozen-reference pair-scoring evidence |
| Local-first ZIPs, bounded persistence workers, immutable snapshots, guarded resume | CPU failure tests and successful returned persistence/recovery paths; not every failure path exercised on Drive |
| Joint specialization/revision training, refreshed banks, decisive composition baselines | Deferred |
| Adaptive attack study, BFCL transfer, final-test evaluation | Deferred/not executed |

A fresh default-suite run is recorded in
[tests.log](../../results_import/project-audit-20260921/tests.log).
**Result: 145 tests, 139 passed and six optional neural tests skipped (84.606 seconds).**
Optional neural skips must not be counted as passes. Historical tiny CPU neural checks used locally initialized
models; they did not establish pretrained 8B efficacy.

## 3. Data preparation and separation

Pinned sources: ARC Challenge and original English LogiQA, not LogiQA 2.0.
The data audit parsed 1,119 ARC plus 7,376 LogiQA training rows, and 299 ARC plus
651 LogiQA validation rows. Exact/source-ID and word-trigram screening excluded
59 redundant training rows, leaving 1,118 ARC and 7,318 LogiQA eligible rows.
There were no train–validation matches under those declared screening rules.
**Semantic paraphrase separation and final-test overlap remain unaudited.**

Frozen selections:

- 80 validation tasks: 40 per family, for the diagnostic pilot.
- 12 training tasks: six per family, for training mechanics.
- 1,200-task training pool: 600 per family; preparation is not proof all 1,200 were trained.
- 24 training-development tasks: 12 per family, excluding the original warm-start tasks.
- 120-task preparation: 60 per family, retaining the original 12 and excluding the
  24 probe IDs and audited groups. All 120 used once per actor.

The 24 tasks have been repeatedly inspected. They are development probes from the
training split, not untouched validation. Selected validation replay records were
not repurposed as training examples. Labels remain evaluator/training-side metadata.
[Data details](../training_data.md).

## 4. Experiment history and results

| Stage | Executed scope | Main result |
|---|---|---|
| CPU foundation/storage | 240 scheduled mock cells; interruption/resume; later 12-cell Colab mock storage check | Software/storage evidence only |
| `qwen3-smoke-001` | 4 validation tasks; 24 cells, 20 applicable; 152 calls | Clean debate/synthesis 2/4; early 0/4; exchange debate 2/4; no eligible private pairs |
| `qwen3-profile-001` | 20 validation tasks; 60 debate records; 500 calls | Clean 9/20, early 3/20, exchange 9/20; 0/18 private pairs; final storage stalled, raw outputs recovered |
| `qwen3-pilot-001` | 80 validation tasks; 1,440 cells, 1,120 applicable; 5,912 calls | Early attack strongly lowers fixed-pool success; only three mixed-correctness clean teams; original probe 0/36 private pairs |
| `qwen3-replay-check-001` | Three post-selected validation tasks, clean/exchange; 386 calls | 13/18 private pairs; 52 suffix branches; zero receiver preference pairs |
| `qwen3-warmstart-001` | 12 train tasks × three agents; 9 updates, 36 presentations | One-step stop and compatible completion to nine; three frozen adapter exports; engineering training, not efficacy |
| `qwen3-bank-001` | Two training tasks × three conditions; 218 calls | All six main trajectories fail; 5/18 private pairs and 20 suffix branches; zero hold/repair pairs |
| `qwen3-base-control-001` | 54 calls under the bank's fixed prompts/seeds | Unadapted base also 0/24 correct receiver candidates; missing pairs not attributable to warm start from this evidence |
| `qwen3-receiver-feasibility-001` | 24 train tasks; 48 main records; 472 calls | 32 hold/two repair pools, all 136 candidates correct; zero pairs because valid-wrong counterparts missing |
| `qwen3-private-support-control-001` | Same 24 tasks, one additional private seed; 72 calls | 45/72 correct; 15 all-correct/nine all-wrong teams; no mixed teams or potential clean repair |
| `qwen3-curated-repair-001` | Two post-selected ARC tasks; eight contexts × four draws; 32 calls | Original peers 0/16 correct; curated help 8/16, confined to one task; zero within-prompt pairs |
| `qwen3-preparation-120-001` | 120 train tasks × three agents; 90 updates, 360 presentations | Completed; 73,974 training sequence tokens; final exports recorded |
| `qwen3-preparation-probe-001` | 72 private + 32 fixed-history receiver calls | Matched private 45/72 → 45/72; receiver 8/32 → 8/32; zero pairs; recovery reused all 104 calls |
| Proposed prompt control | 72 answer-only calls on the existing prepared adapters | Design only; runner not implemented; no results |

The listed real inference experiments account for **7,902 recorded generation calls**.
This sums logical calls once per completed run: it excludes CPU mocks, cache-only
recovery, training forwards and the bank's 23 teacher-forced forwards. Selected replay
reruns count as executed calls even where text matches earlier pilot outputs. It is
not a count of independent tasks or a complete billing ledger.

### Validation pilot: final correct answers out of 80

| Method | Clean | Early exposure | Exchange corruption |
|---|---:|---:|---:|
| Single agent | 45 | 13 | N/A |
| Vote | 45 | 12 | N/A |
| Frozen synthesis | 47 | 12 | N/A |
| Debate | 47 | 10 | 46 |
| Ignore peers | 48 | 11 | N/A |
| Archive baseline | 47 | 12 | 47 |

These use unadapted Qwen3-8B, one task/seed selection and a fixed attack pool.
Archive has extra context and is not a matched-cost control. N/A means the method
has no peer-revision attack surface, not perfect robustness. Full raw audit checked
all 1,440 cells and 5,912 calls. One exchange terminal failure occurred despite
correct revised packets; a separate task lost its only correct private alternative.
No population superiority or trained PACT claim follows.
[Full pilot audit](../reviews/qwen3-pilot-001-raw.md).

### What replay established

On the three selected validation tasks, 13 usable private pairs gave five credits
of +1, two of +0.5 and six of zero; five contexts remained missing. Three pairs were
not length-bin matched. Each pair used two positive and two negative suffixes,
with matching corresponding node seeds, unchanged other packets and fixed attack
bytes/site. All affected revisions and readouts reran. This verifies execution of
the estimator; K=2 and outcome-based task selection do not establish a population
causal effect. The later training bank produced five pairs, four zero credits and
one +1. Neither set supplied receiver DPO pairs.
[Replay review](../reviews/qwen3-replay-check-001.md),
[training-bank review](../reviews/qwen3-bank-001-complete.md).

### Why revision training remains blocked

The two-task training bank had no correct receiver candidates. The broader screen
had only correct candidates in its eligible pools. The curated message intervention
changed success on one task, but original and curated prompts differ: a correct
curated response cannot be paired with a wrong original response for same-prompt DPO.
Abstentions are failures and are not valid-wrong substitutes. Private replay pairs,
helpful messages and mixed teams are distinct from eligible receiver preferences.
Both hold and repair support remain insufficient for the planned full revision loss.

### Larger preparation: corrected matched comparison

| Measure | Old 12-task actors | New 120-task actors |
|---|---:|---:|
| Private correct, same seed-1730 requests | 45/72 | 45/72 |
| All-correct private teams | 15/24 | 15/24 |
| Mixed-correctness private teams | 0/24 | 0/24 |
| All-wrong private teams | 9/24 | 9/24 |
| Potential clean-repair contexts | 0 | 0 |
| Receiver correct, original peers | 0/16 | 0/16 |
| Receiver correct, curated help | 8/16 | 8/16 |
| Within-prompt receiver pairs | 0 | 0 |

Private matched transitions: 45 correct-to-correct, 27 wrong-to-wrong; 71 answer IDs
unchanged, one wrong answer changes to another wrong answer. Receiver transitions:
eight correct-to-correct, 16 wrong-to-wrong, seven abstention-to-abstention and one
abstention-to-wrong. Receiver histories deliberately remain the old saved private
states/donors; this is not a natural rollout of a newly prepared team.

**Correction:** our first review quoted 46/72 → 45/72 because the imported report
helper inherited seed-1729 baseline packets. The intended comparator is the completed
seed-1730 private control. The corrected join verifies seeds, messages and prompt
prefixes and gives 45/72 → 45/72. This corrects interpretation, not the imported bytes.
The archived report's baseline remains historical; future checkpoint-comparison
reporting must use an explicit matched source rather than the inherited baseline.
[Corrected preparation review](../reviews/qwen3-preparation-120-001.md).

## 5. Operational incidents and recovery

The profile reached 60/60 records but stalled during final persistence. Its raw
records were recovered and audited; original final Drive verification remains
unestablished. Repairs introduced bounded worker processes, progress messages,
local ZIPs before Drive writes and completion markers after verification. The
small Colab storage test and later pilot-size handoffs succeeded.

The completed preparation training had 647 files. Full recovery exceeded 600
seconds; the repair restores 12 final inference payloads plus snapshot proof files,
without optimizer history. It verifies selected bytes, forbids training from the
compact export, and narrowly accepts the recorded source migration while preserving
all attempted/committed probe calls.

The probe's original invocation had already completed 104 calls. Recovery used
104 cache hits and zero new generations. Training also remained complete; its ZIP
was already on Drive and later returned. No retraining was required. This proves
completed-run recovery on the reported path, not bitwise interrupted-training
reproducibility or recovery of ambiguous in-flight GPU calls.

Old nested persistence flags can precede the enclosing verified receipt. Likewise,
nested handoff hashes may identify the preceding local review ZIP, not the enclosing
final ZIP. Audit the correct receipt layer and recompute the enclosing hash; do not
interpret staged fields alone as a failed copy.

## 6. Resources and cost limits

The pilot dominates recorded inference time: 20,443.64 seconds, about 5.68 hours,
with 2,009,332 input and 285,294 output tokens. Selected replay took 1,381 seconds;
the broader receiver screen 1,812.53 seconds. The 120-task training invocation
reported 990.51 seconds; original probe 540.60 seconds; cache-only recovery 121.67
seconds. The nine-update warm start totalled 228.25 seconds across two invocations.

These timers have different boundaries, commonly excluding final persistence and
notebook setup. Profile finalization also stalled outside its recorded collection
timer. Do not sum them into billed GPU hours. Compute units and monetary spend are
unknown. Short executed sequences do not establish maximum-context memory fit.
Per-run reviews retain measured tokens, timing and peak allocated/reserved memory.

## 7. Audit findings and unresolved risks

| Finding | Disposition |
|---|---|
| Private report inherited a different seed baseline | Corrected local comparison and review; archived report preserved; future reporting needs explicit comparator provenance |
| No usable same-prompt receiver pairs in completed diagnostics | Scientific feasibility limitation; no fabricated counterparts or full revision claim |
| Training prompt is answer-only; protocol asks for answer plus justification | Known objective/prompt mismatch; causal impact untested |
| Larger preparation changes task count, content and update count together | Cannot attribute effects separately to those factors |
| Review ZIPs omit adapter/optimizer tensors | Recorded identities checked; actual bytes require full durable snapshots |
| Drive state is not directly accessible to local audit | Receipts and returned files provide time-specific evidence only |
| Selected/reused tasks and four draws per pool | No broad generalization, absence-of-variation proof or independent-sample confidence claim |
| Semantic paraphrases and final-test overlap unaudited | Lexical screening is not semantic deduplication |
| Historical status tables contain stale pending labels | This report and later dated entries take precedence; history retained |
| Old audit scripts may assert their original executable hash | Reproduce under matching recorded source; do not weaken checks merely to run on HEAD |

No full joint PACT updates, validation checkpoint selection study, matched SAC/composition
baseline, adaptive attack curve, BFCL transfer or final QA test has been completed.
No manuscript result placeholder should be filled as a PACT result from these runs.

## 8. Current next step — proposed, not executed

The [objective review](../preparation_objective_review.md) freezes a 72-call
answer-only prompt control with the existing 120-task adapters, same 24 tasks and
same seeds. It compares to cached prepared private outputs, with zero updates,
receiver calls, new attacks or preference exports. This tests prompt/response-contract
sensitivity before changing the objective; it does not isolate the individual effects
of formatting, instruction wording and justification requirements.

The design/config/request hash are recorded. **The runner is not implemented and
there are no new GPU results.** Completed experiments stay closed. No repeated seed
search, larger warm-start sweep, final-test run or main-protocol change follows
automatically from this proposal.

## 9. Evidence map and reproduction

Start with the archive inventory linked above and [experiment ledger](../experiment_ledger.md).
Per-run reviews preserve exact commits, hashes, scopes, resource measurements and limitations:

- [Smoke](../reviews/qwen3-smoke-001.md), [profile](../reviews/qwen3-profile-001.md),
  [storage check](../reviews/drive-storage-check-001.md).
- [Pilot](../reviews/qwen3-pilot-001.md), [full raw audit](../reviews/qwen3-pilot-001-raw.md),
  [selected replay](../reviews/qwen3-replay-check-001.md).
- [First warm-start step](../reviews/qwen3-warmstart-001.md),
  [completed warm start](../reviews/qwen3-warmstart-001-complete.md),
  [first bank record](../reviews/qwen3-bank-001-first.md),
  [completed bank](../reviews/qwen3-bank-001-complete.md).
- [Base control](../reviews/qwen3-base-control-001.md),
  [broader receiver screen](../reviews/qwen3-receiver-feasibility-001.md),
  [private-seed control](../reviews/qwen3-private-support-control-001.md),
  [curated help](../reviews/qwen3-curated-repair-001.md).
- [Preparation/recovery repair](../reviews/preparation-restore-repair-001.md),
  [completed preparation and probe](../reviews/qwen3-preparation-120-001.md),
  [objective review](../preparation_objective_review.md).

Current-source CPU audit commands for the latest artifacts:

```bash
PYTHONPATH=src python results_import/project-audit-20260921/inventory.py
PYTHONPATH=src python results_import/qwen3-preparation-120-001-analysis/audit.py
PYTHONPATH=src python results_import/preparation-objective-review-001/audit_and_plan.py
PYTHONPATH=src python -m unittest discover -s tests -v
```

The objective audit regenerates its frozen design JSON deterministically; it runs
no model. Older per-run scripts may require the corresponding historical source.
`results_import/` is ignored by Git: a code push does not back up these ZIPs or local
audit outputs. Preserve them separately along with full Drive snapshots, especially
`objects/` directories. Small review archives cannot reconstruct missing model tensors.

## Addendum — 22 September 2026

The previously proposed 72-call prompt control is now implemented, executed and
audited. Same prepared adapters/tasks/seeds: 45/72 correct in both prompt arms;
68 answer IDs unchanged, four wrong-to-wrong changes. All new responses parse.
The run adds 72 generations to the earlier 7,902, yielding 7,974 recorded calls
across these listed runs. The 19-ZIP inventory above remains a dated snapshot; the
new ZIP has its own verified checksum and audit. The diagnostic is closed.
[Full review](../reviews/qwen3-preparation-prompt-control-001.md).
