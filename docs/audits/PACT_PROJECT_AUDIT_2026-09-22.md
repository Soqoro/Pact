# PACT consolidated project audit — 22 September 2026

## Review conclusion

**We have built and exercised a research pipeline, executed real private
counterfactual replay, and completed two bounded clean-answer adapter preparations.
We have not executed full PACT training, demonstrated a PACT advantage, or evaluated
the final test benchmark.**

The new `receiver_supervision_v1` implementation removes the requirement for sampled
correct/incorrect receiver completions. Its first real collection completed, but
**training never started**: legitimate hold/repair contexts were too scarce. An offline
search found no matching same-task donors in retained historical training reviews.
A new donor source has not been selected or supplied. No further GPU run is scheduled.

This report consolidates the earlier [21 September audit](PACT_PROJECT_AUDIT_2026-09-21.md)
and subsequent evidence. It supersedes their obsolete *current-next-step* and
*pending* descriptions, while preserving historical records and conclusions. It is
intended for review before choosing another experiment, not as a claim that the next
methodology has already been approved.

## 1. Evidence scope and what was checked now

Real-model work was run by the user in Colab. Local work comprised implementation,
CPU/neural-fixture tests, safe artifact inspection and recomputation. The reported
real-model stack is pinned Qwen3-8B, BF16/SDPA, thinking disabled, on NVIDIA L4.
Adapter stages use three logical agents sharing the frozen backbone.

Published implementation identity for the latest returned run:
`fd38b5e90bf6e5c648922405d46094abbc2449b2`, executable source hash
`b179e7d109cef2533c87466c43de1bb3df612dca1118b5078b71cfbc14990cc7`.
The local working tree now additionally contains the subsequent audit reports and
inventory utility. This report does not assert those edits have been committed/pushed.
Each historical experiment retains its own source/config/model identities.

For this consolidation:

- Reread, SHA256-hashed and CRC-checked **all 21 top-level retained ZIPs**, totaling
  15,412,327 bytes. All passed. The [archive inventory](PACT_ARCHIVE_INVENTORY_2026-09-22.json)
  records paths, hashes, sizes and member counts. This checks present local bytes;
  it does not replace the historical semantic audits or establish every transport hash.
- Re-executed the offline donor inventory and obtained byte-equivalent JSON content.
- Incorporated the recent receiver collection audit: exact plan reconstruction,
  all 672 request/call checks, and exact reconstruction of the support report.
- Cross-checked earlier numbers against the prior consolidated audit and linked
  per-run reviews. Did not regenerate model outputs, recompute historical logits,
  rerun training or access final-test data.
- Did not rerun the software suite for this documentation-only consolidation.
  Previously executed test results are explicitly labeled below.

**Evidence limits:** returned training reviews omit adapter/optimizer tensor payloads.
Their recorded identities and runtime verification receipts were audited; this is
not an independent local rehash of omitted tensors. Drive receipts establish reported
successful copying at that time, not present remote availability. Archived token
arrays and request provenance are not independent numerical reproduction of logits.

## 2. What has been implemented

| Component | Current evidence/status |
|---|---|
| Typed task/label separation, deterministic request identities, bounded CLI, checksummed artifacts | Implemented and CPU-tested |
| Three saved private packets, synchronous exchange, identical one-sender corruption to recipients | CPU-tested and reconstructed from real returned traces |
| Revised-packet readout using the unadapted base; archive baseline separately named | Implemented, tiny-neural isolation checks and real protocol evidence |
| Single, vote, synthesis, debate, ignore-peers and archive diagnostics | Executed on the validation pilot; not a completed matched-cost study |
| Private counterfactual replay and continuation-credit calculation | Executed and audited on eligible real-model cases |
| Responsibility solver, specialization numerics, DPO builder/loss and reference-cache validation | Local CPU/tiny-neural evidence; not full GPU PACT optimization |
| Clean-answer LoRA preparation and optimizer/RNG checkpoints | Two real bounded preparation recipes completed; metadata audited |
| Receiver-supervised answer-prefix loss, context builder, focal training engine and three-arm evaluation | Implemented and CPU/tiny-neural tested; new 8B training/evaluation unexecuted |
| New receiver-study source collection and support gate | Real 672-call collection audited; stopped at insufficient support |
| Bounded persistence, compact initialization restore, immutable full training checkpoints | Local failure tests and selected successful real storage/recovery paths; not universal recovery guarantees |
| Joint replay/responsibility/specialization/receiver updates and refreshed banks | Deferred |
| Matched SAC/composition comparison, adaptive attacks, BFCL/tool transfer, final-test study | Deferred/not executed |

The original DPO path remains available in the codebase. The new first-study runner
fixes DPO off and does not require preference pairs or reference-score evidence.
Enabling DPO within that new runner, or coupling all objectives in joint refreshes,
is not implemented as completed work.

## 3. Data and split accounting

Pinned data are ARC-Challenge and original English LogiQA. Previous preparation
parsed 1,119 ARC and 7,376 LogiQA training rows plus 299 ARC and 651 LogiQA validation
rows. Declared exact/source-ID and word-trigram screening excluded 59 redundant
training rows. This screening is **not a semantic-paraphrase guarantee**. Final-test
overlap has not been audited through final-test access.

| Selection | Use |
|---|---|
| 80 validation tasks, 40/family | Untrained diagnostic pilot; selected replay cases remain validation evidence |
| 12 training tasks, six/family | Small adapter-training mechanics check |
| 1,200-task training pool, 600/family | Available frozen pool; it was not all used for preparation |
| 24 training-development tasks, 12/family | Repeatedly inspected feasibility/control probes; not untouched validation |
| 120 preparation tasks, 60/family | Includes the original 12; excludes the 24 probe tasks/groups |
| 96 fresh receiver-study groups | 64 fit / 32 diagnostic held-out, balanced by family; excludes 120 preparation and 24 prior probe IDs plus known duplicate groups |

The latest 32-task slice is held out from proposed fitting, but its source-context
eligibility has now been inspected. It is not an untouched final benchmark.
No old validation trajectory has been relabeled as receiver training data. Task,
call, context and optimization-presentation counts below must not be conflated.

## 4. Completed experiment history

| Run/stage | Actual scope | Result and interpretation |
|---|---|---|
| CPU foundation and storage exercises | Mock interruption/resume; 240 scheduled mock cells; later 12-cell Colab storage check | Software/storage evidence only |
| `qwen3-smoke-001` | Four validation tasks; 152 calls | Clean debate/synthesis 2/4, early 0/4, exchange debate 2/4; no usable private replay pairs |
| `qwen3-profile-001` | 20 validation tasks; 500 calls | Debate clean/early/exchange 9/20, 3/20, 9/20; raw data recovered after final persistence stall |
| `qwen3-pilot-001` | 80 validation tasks; 5,912 calls; 1,440 scheduled cells | Fixed early attacks substantially reduced success; detailed table below; initial probe 0/36 private pairs |
| `qwen3-replay-check-001` | Three post-selected validation tasks; 386 calls | 13/18 private pairs, 52 suffix branches; no receiver preference pairs |
| `qwen3-warmstart-001` | 12 tasks × three agents; nine updates, 36 presentations | Completed clean-answer preparation and compatible continuation; no efficacy comparison established |
| `qwen3-bank-001` | Two training tasks × three conditions; 218 calls | All six main trajectories fail; five private pairs / 20 suffix branches; zero receiver pairs |
| `qwen3-base-control-001` | 54 matched fixed-context base calls | Base also 0/24 correct receiver candidates; does not identify warm start as cause |
| `qwen3-receiver-feasibility-001` | 24 training tasks; 472 calls | 32 hold/two repair pools; all 136 candidates correct; zero valid-wrong counterparts/pairs |
| `qwen3-private-support-control-001` | Same 24 tasks, one new private seed; 72 calls | 45/72 correct, 15 all-correct/nine all-wrong teams, no mixed teams |
| `qwen3-curated-repair-001` | Two selected ARC tasks; 32 calls | Original 0/16 correct; curated help 8/16; gain confined to one task, zero within-prompt pairs |
| `qwen3-preparation-120-001` | 120 tasks × three agents; 90 updates, 360 presentations | Completed larger clean-answer preparation; not full PACT |
| `qwen3-preparation-probe-001` | 72 private + 32 receiver calls | Matched private 45/72 → 45/72; receiver 8/32 → 8/32; recovery added zero calls |
| `qwen3-preparation-prompt-control-001` | 72 answer-only private calls | Same prepared actors: 45/72 under both packet and answer-only instructions; diagnostic closed |
| `qwen3-receiver-supervision-001` | 96 new source tasks; 672 private/donor calls | Fit hold/repair 2/2; held-out 0/1; support gate stopped training |
| Offline donor inventory | Eight historical training reviews; 950 distinct retained private/revision call/raw identities | Zero exact task or known duplicate-group matches for the frozen 96 tasks; zero new calls |

Across the listed real inference runs: **8,646 recorded generation calls**
(7,902 in the prior audit + 72 prompt-control + 672 new source-collection calls).
Count resumed runs once, not once per ZIP. Exclude cached recovery, mock calls and
teacher-forced training/scoring forwards. The 950 donor-inventory identities are
reused historical evidence, not another 950 generations. These are not independent
task counts or a billing total.

Real clean-answer preparation totals **99 optimizer updates and 396 presentations**
across the two separate recipes. The 120-task preparation used fresh adapters; it
was not 90 additional updates applied to the old nine-update checkpoint. These are
not receiver-SFT, specialization or joint PACT updates.

## 5. Main numerical results

### 5.1 Validation pilot: final correct answers out of 80

| Method | Clean | Early exposure | Exchange corruption |
|---|---:|---:|---:|
| Single | 45 | 13 | N/A |
| Vote | 45 | 12 | N/A |
| Frozen synthesis | 47 | 12 | N/A |
| Debate | 47 | 10 | 46 |
| Ignore peers | 48 | 11 | N/A |
| Archive | 47 | 12 | 47 |

This was unadapted Qwen3-8B, one task/seed selection and fixed attack templates.
Archive receives additional context; it is not a matched-compute robustness control.
N/A means no relevant exchange surface, not successful defense. No trained PACT
method appears in this table. All 1,440 raw cells and 5,912 calls were historically
audited. [Pilot raw review](../reviews/qwen3-pilot-001-raw.md).

### 5.2 Private replay works on eligible cases

The selected validation replay produced 13 usable private pairs: five credits +1,
two +0.5 and six zero; five contexts remained missing. Each pair used two positive
and two negative suffix branches with matched corresponding seeds and fixed attack
bytes/site. Three pairs were not length-bin matched. The training bank subsequently
produced five private pairs: four zero credits and one +1.

This establishes execution of the private continuation estimator on real cases.
It does not establish a population causal benefit, useful learned specialization,
or receiver DPO availability. Selection and K=2 limit the inference.
[Replay review](../reviews/qwen3-replay-check-001.md),
[bank review](../reviews/qwen3-bank-001-complete.md).

### 5.3 Original receiver-DPO bottleneck

- Small bank: 24 receiver candidates, **zero correct**, 14 valid wrong and ten
  abstentions. No valid same-prompt correct/wrong pairs.
- Fixed-context base control: also **zero correct out of 24** receiver candidates.
  This does not prove the preparation caused the shortage, or had no effect.
- Broader screen: 136 receiver candidates, **all correct**. Zero valid-wrong
  counterparts. Repair eligibility itself covered only two contexts on one task.
- Curated help: original peers 0/16 correct versus curated peers 8/16; one task
  changed from 0/8 to 8/8 and the other stayed 0/8. This is a narrow context effect,
  not a generalization result. Original and curated prompts differ, so their outputs
  cannot be paired as same-prompt DPO examples. Within each prompt arm, pairs remain zero.

These results show a limitation of the tested recipe, not a theorem that DPO needs
on-policy sampling or that a correct/wrong completion has zero probability.
[Broader screen](../reviews/qwen3-receiver-feasibility-001.md),
[curated diagnostic](../reviews/qwen3-curated-repair-001.md).

### 5.4 Preparation and prompt controls

| Matched comparison | Before/control | After/intervention |
|---|---:|---:|
| Old 12-task vs new 120-task actors: private correctness, seed 1730 | 45/72 | 45/72 |
| Fixed-history receiver correctness: original peers | 0/16 | 0/16 |
| Fixed-history receiver correctness: curated help | 8/16 | 8/16 |
| Prepared actors: packet vs answer-only private instruction | 45/72 | 45/72 |

**Baseline correction:** the early 46/72 → 45/72 preparation comparison used a
seed-1729 baseline. The proper matched seed-1730 join is **45/72 → 45/72**:
45 correct-to-correct, 27 wrong-to-wrong, one wrong answer ID changes.

The later prompt control had 68 unchanged answer IDs and four wrong-to-wrong changes;
all 72 new responses parsed. Both prompt arms scored ARC 24/36 and LogiQA 21/36;
teams remained 15 all-correct, zero mixed and nine all-wrong.

No accuracy gain was observed on these matched probes. That does not prove the
adapters learned nothing or that all prompt changes are irrelevant. The answer-only
control contains no receiver outputs and does not measure receiver-pair yield.
Fixed-history receiver probes use saved old histories, not natural trajectories
of a newly trained team. [Preparation review](../reviews/qwen3-preparation-120-001.md),
[prompt-control review](../reviews/qwen3-preparation-prompt-control-001.md).

## 6. Receiver supervision: change implemented, learning not yet tested

The explicit methodological change is `receiver_supervision_v1`, target
`receiver_answer_ce_v1`. The official label supplies an answer-field target under
the unchanged full receiver prompt; successful receiver sampling is not required.
A target such as `{"answer":"B"` is an incomplete prefix of a normal packet.
Only answer-bearing tokens are scored; no EOS or invented rationale is appended.
Gold information stays outside system/user inputs.

The planned three arms are frozen preparation, task-only SFT and receiver SFT.
Only prespecified focal agent0 trains. Both trained arms start from identical prepared
weights with fresh optimizers, matching label exposures and a 0.1 clean anchor.
Hold and repair each receive half the receiver loss, averaging repeated contexts
within tasks. Missing strata are not renormalized. The old executed base preparation
was private QA; the new runner does not also apply a duplicate receiver base loss.

The loss/masks, real adapter engine, resume, comparison arms, peer-withheld controls,
private checks, natural-team smoke and review export are implemented. **Their new
8B training/evaluation stages did not run.** The first study had a planned ceiling
of 1,296 generations, 322,560 reserved output tokens and 32 updates per trained arm.
Only its 672-call source-collection stage was reached. The full ceiling is not actual
consumption. [Methodology](../receiver_supervision_methodology.md).

### Actual support result

| Partition | Tasks | Hold-supported tasks | Repair-supported tasks | Minimum per stratum |
|---|---:|---:|---:|---:|
| Fit | 64 | 2 | 2 | 8 |
| Diagnostic held-out | 32 | 0 | 1 | 4 |

Five contexts occur across only three distinct original tasks: two curated fitting
hold contexts, two natural fitting repair contexts on those same two tasks, and one
natural held-out repair context. The recorded empty weights and
`insufficient_context_support` status reproduce exactly.

Across seven sampled packets per task (three initial + four focal alternatives):

| Partition | Only correct valid packets | Only wrong valid packets | Both correctness classes | No valid packets |
|---|---:|---:|---:|---:|
| Fit | 31 | 31 | 2 | 0 |
| Held-out | 20 | 9 | 1 | 2 |

“Only” describes valid packets; invalid packets can coexist. Wrong options need not
be identical. There were 364 correct, 287 valid wrong, 13 abstentions, seven invalid
answers and one length-limited packet: **651/672 valid (96.875%)**. No malformed or
context-overflow outputs were recorded. Parsing therefore does not explain the
predominance of tasks lacking both correctness classes.

The held-out mixed task has a wrong focal own packet in all five focal draws, but a
correct nonfocal peer. It supports repair, not hold. Thus the zero held-out hold
count is consistent with source evidence, not a dropped eligible record.

**What changed versus the old bottleneck:** receiver-completion pair availability
was removed as a prerequisite. The separate requirement for legitimate eligible
own-state/peer contexts remains. This collection tested that context recipe and
failed its support gate; it did not test whether receiver CE can improve behavior.
[Complete collection audit](../reviews/qwen3-receiver-supervision-001.md).

## 7. Donor inventory and the current missing prerequisite

The offline audit conservatively screened eight retained training reviews, including
older/different checkpoints and archived private/revision outputs. It matched exact
trusted inputs, then known group/content-group identities. There were 950 distinct
call/raw identities, zero unmapped calls and **zero matches to the frozen 96 tasks**.
Including carried-forward and answer-only records did not produce a match. This
inventory does not certify every historical output as a usable donor.

This rules out importing a donor from the inspected archive set to fill current
support. It does not prove that no external source could provide a legitimate packet.
Reviewing a correct answer label alone is not a source of a verified rationale.
A donor importer without actual material would not resolve the missing data.

No human packet set or separately bounded model-based acquisition design has been
selected, supplied or approved. Such a proposal would need authentic same-task
outputs, explicit source/checkpoint/prompt provenance, preserved partitions, a finite
predeclared budget, clear curated labels, no forced own-state disagreement and an
unchanged missing-support stop. It would be a separately versioned experiment,
not an extension of the closed run. [Inventory and contract requirements](../reviews/receiver-donor-inventory-001.md).

## 8. Engineering evidence, incidents and costs

Previously executed software checks for the receiver update:

- Default full suite: **165 tests — 156 passed, nine optional skips**.
- Explicit CPU neural/legacy subset: **25 passed**, including all nine optional
  neural tests; no pretrained model weights downloaded.
- Tiny locally initialized Qwen: independent answer-mask/causal-shift calculations,
  target-loss decrease under actual LoRA updates, unchanged backbone/nonfocal
  adapters and bit-identical optimizer/RNG resume.
- Mock three-arm study: 1,296 calls; 192 teacher-forced diagnostics; cache reuse and
  changed checkpoint/context/seed rejection. These are software fixtures, not real
  receiver learning or performance numbers.
- Final focused receiver checks and local plan/snapshot/review/import/restore round
  trips passed. Tests were not rerun for this report; fresh archive/inventory checks
  are listed in section 1.

Operational history matters when interpreting runtime logs:

- The profile finished generation but stalled during Drive finalization. All raw
  records were later recovered; original final persistence verification remains
  unestablished. Local-first ZIPs and bounded workers were added.
- Restoring the 120-task preparation's full 647-file snapshot exceeded 600 seconds.
  Compact final-weight restoration was added, distinct from optimizer-state recovery.
- The preparation probe had already completed 104 calls. Recovery reused all 104
  cached results, generating zero new calls; training was not repeated.
- The receiver support stop is an intentional data gate, not a Colab crash or a
  failure to finish collection. The returned archive has 672 committed calls and
  zero unresolved attempts.

Latest receiver collection consumed 159,313 input and 34,766 output tokens; its
attempted-call output reservation was 172,032 tokens. The earlier pilot dominated
recorded inference time at about 5.68 collection hours, excluding final storage and
setup. Historical timers have different boundaries and cannot be summed into a
reliable billing total. **Compute units and monetary spend remain unknown.**
Executed short sequences and CPU fixtures do not establish worst-case 4,096-token
8B training memory fit. Preserve full Drive `objects/` and snapshots separately;
review ZIPs cannot reconstruct omitted tensors. `results_import/` is Git-ignored,
so pushing code does not back up its contents.

## 9. What the evidence supports—and does not

| Supported conclusion | Limit |
|---|---|
| The protocol, private replay estimator and bounded workflow have executed on real Qwen examples | No completed full PACT optimization or benefit |
| Private correctness is highly homogeneous on several inspected task sets | Not a universal property of Qwen, all seeds or all prompts |
| Both all-wrong and all-correct receiver pools occurred | Neither gives valid mixed DPO pairs under the declared recipe |
| Authentic curated help changed one selected task's receiver outcome | No broad communication-learning or held-out generalization claim |
| Larger preparation and answer-only prompting showed no gain on matched inspected probes | Does not prove no parameter learning or universal prompt irrelevance |
| New supervised targets do not require sampled receiver positives/negatives | Their actual learning efficacy has not been tested |
| New source collection lacks sufficient legitimate hold/repair support | Not proof receiver supervision is impossible |
| Historical donor archives do not overlap the new selection | Other authentic sources remain an open question |

No manuscript result placeholder should be filled as a PACT result from these runs.

## 10. Decision checkpoint for the user

The current state is **a stopped feasibility study with reusable code and intact
evidence**, not a trained receiver model awaiting evaluation. Do not run cells 6–8,
relax support minima, append more draws, replace tasks after seeing outcomes or reopen
the completed 72-call diagnostic.

The decisions still open are:

1. Whether to pursue another separately bounded donor-source experiment at all.
2. If yes, what authentic source is available: independently authored/reviewed
   same-task material, or a separately specified model-based collection. Neither
   has been supplied or implemented as the next authorized experiment.
3. What changed provenance, acquisition budget and diagnostic claims that source
   entails. A broader source cannot silently become a natural trajectory or a
   same-prompt DPO pair.
4. What stop criterion applies if it still cannot support both strata. Pausing or
   reporting the feasibility limit is a valid outcome; success is not assumed.

This audit makes no new methodological choice and schedules no Colab execution.

## Evidence index

- [Prior comprehensive history](PACT_PROJECT_AUDIT_2026-09-21.md),
  [ledger](../experiment_ledger.md), [implementation status](../implementation_status.md).
- [Smoke](../reviews/qwen3-smoke-001.md), [profile](../reviews/qwen3-profile-001.md),
  [storage](../reviews/drive-storage-check-001.md), [pilot raw audit](../reviews/qwen3-pilot-001-raw.md).
- [Replay](../reviews/qwen3-replay-check-001.md), [warm start](../reviews/qwen3-warmstart-001-complete.md),
  [bank](../reviews/qwen3-bank-001-complete.md), [base control](../reviews/qwen3-base-control-001.md).
- [Receiver feasibility](../reviews/qwen3-receiver-feasibility-001.md),
  [private control](../reviews/qwen3-private-support-control-001.md),
  [curated help](../reviews/qwen3-curated-repair-001.md).
- [Preparation/probe](../reviews/qwen3-preparation-120-001.md),
  [prompt control](../reviews/qwen3-preparation-prompt-control-001.md).
- [Receiver collection audit](../reviews/qwen3-receiver-supervision-001.md),
  [donor inventory](../reviews/receiver-donor-inventory-001.md),
  [fresh archive inventory](PACT_ARCHIVE_INVENTORY_2026-09-22.json).
