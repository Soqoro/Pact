# Stage I amended evaluation: validation return audit

Audit date: 2026-10-25. Run: `pact-revival-stage1-evaluation-amended-002`.
Validation is complete in returned real Colab evidence. Source evaluation and
fixed-history evaluation remain unexecuted; this is not a full-PACT result.

## Artifact identities

PRIVATE: `pact-revival-stage1-evaluation-amended-002-PRIVATE-1792839181169439976.zip`
SHA256: `8d5201f3e5886eb888a8de261c2600a3b07c01fd4e752e215ad09ed3e6ed6620`.

SANITIZED: `pact-revival-stage1-evaluation-amended-002-SANITIZED-1792839196788713973.zip`
SHA256: `1c2f6f0985a78660cc00af169c05c29d0644c092f13b673f23f980b9921b5d89`.

Pinned source: `a2ad51f60530e6dafaf1377eba03d0753f87ff92`.
Frozen plan: `288a2f9bd5bcbe95c52fd9b7d99cdefd2cb52ebd69c71a0c2939c2428dc72bf5`.
The original accounting amendment, source allocation, checkpoints, parser and
attack acceptance rules remain unchanged. Raw inputs and traces stay private.

## Local audit checks executed

Both outer SHA256 values matched. Production archive validation passed all 28,712
PRIVATE and four SANITIZED payload checksums, member inventory/path bounds and
symlink/duplicate checks. SANITIZED contains exactly the four approved aggregate
reports plus checksum/handoff metadata; all four reports match PRIVATE.
All 8,885 immutable imported files match their inventory. All 337 saved smoke
intent/call/link/output/attack/stage files checked are byte-identical to the earlier
smoke return.

The production Journal constructor passed over all 3,876 calls, checking physical
owner and frozen plan identity, request/call/token provenance, strict parser
reconstruction, context/output caps, missing intents/results and component/total
budgets. All four aggregate JSON reports were regenerated on CPU and matched
exactly. The handoff and saved recovery both report recovery_safe=true.
No production code changed; no model downloads, GPU work, new unit-test suite,
training or inference were run locally. These checks verify recorded evidence,
not an independent reproduction of GPU logits or external checkpoint tensors.

## Completed work and accounting

The cohort is 128 validation tasks: 64 ARC-Challenge and 64 LogiQA. All three arms
have private packets and clean communication/readout on all 128 tasks. The 128
historical attack attempts were reused: 99 accepted and 29 rejected. Exchange
runs only on the shared 99 accepted-attack tasks (51 ARC, 48 LogiQA).

- 3,876 attempted and committed child generations, including the 66 smoke calls;
  3,810 additional calls since the audited smoke. Zero unresolved dispatches.
- 1,984,512 reserved output tokens; 1,333,223 input and 176,531 output tokens.
- 128 ancestor reuse links, no new attack attempts, no canonical child deduplication.
- No new training, optimizer updates, teacher-forced forwards or synthetic checks.
  The 16 completed checkpoint-verification forwards remain inherited evidence.
- Packet parsing: 3,592 ok, 235 invalid, 49 abstentions across all generated phases.
  Invalid and abstaining completions remain failures; no repairs or retries.
- No recorded context incompatibilities. Compute units were not supplied.

The exact count is 3 arms × (128 tasks × 7 clean/private calls + 99 tasks × 4
exchange calls) = 3,876. The difference from the 4,224 validation ceiling is
29 rejected attacks × 3 arms × 4 exchange calls = 348. These are unavailable
exchange conditions, not unfinished dispatches or tokens transferable to a new study.

## Results

Correct final readouts are shown as counts. Clean includes all 128 tasks; exchange
includes only the 99 accepted-attack tasks. These populations must not be treated
as identical when comparing clean versus attacked accuracy.

| Arm | Clean ARC | Clean LogiQA | Clean total | Exchange ARC | Exchange LogiQA | Exchange total |
|---|---:|---:|---:|---:|---:|---:|
| Frozen Q/L/M | 48/64 | 42/64 | 90/128 | 36/51 | 27/48 | 63/99 |
| Independent adversarial SFT | 53/64 | 42/64 | 95/128 | 41/51 | 27/48 | 68/99 |
| Uniform joint SFT | 54/64 | 41/64 | 95/128 | 44/51 | 28/48 | 72/99 |

The predeclared equal-source observed accuracies are 70.31%, 74.22%, 74.22%
for clean and 63.42%, 68.32%, 72.30% for exchange, respectively. Exchange percentages
average ARC and LogiQA accuracies equally, rather than simply dividing total correct
by 99. The 29 rejected-attack outcomes remain missing for every arm; they are not
counted as defender errors or successful defenses.

The primary joint-minus-independent comparison is:

| Condition | Paired tasks | Gains / losses | Equal-source difference | Descriptive bootstrap interval |
|---|---:|---:|---:|---:|
| Clean | 128 | 13 / 13 | 0.00 percentage points | −7.44 to +7.81 points |
| Exchange, accepted subset | 99 | 10 / 6 | +3.98 percentage points | −4.11 to +12.23 points |

Both intervals span zero. The unit is task/group with source-stratified resampling,
not generation call; the frozen reporting procedure uses 500 bootstrap replicates.
The full-128-task missing-outcome bounds for joint-minus-independent exchange are
−19.53 to +25.78 percentage points. No robust joint-over-independent advantage is
established by this validation return.

Joint-minus-frozen exchange is +8.88 points on observed tasks, with descriptive
interval +0.06 to +17.93 points. This is a secondary, accepted-subset observation;
its full-population missingness bounds span −15.63 to +29.69 points. It does not
establish a general robustness gain or a benefit specifically caused by joint training.
Fixed-history peer-use controls have not yet been executed.

## Scope and next stage

The next existing stage is source evaluation on the already frozen ARC120/LogiQA136
cohort, with its own ceiling of 8,448 calls. It must export and stop for review
before fixed-history evaluation. No stage was launched during this local audit.
Do not tune prompts, checkpoints, parser, seeds, attacks or task selection from
these validation outcomes. No final-test data or manuscript placeholders changed.
Original later-generation history remains unknown and is separate from this
approved additional envelope. The possible historical repeats and unknown parent
training step remain recorded; validation completion does not close those histories.
