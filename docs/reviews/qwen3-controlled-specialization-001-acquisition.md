# Controlled specialization: acquisition audit

Audited locally on 2026-09-27. This is acquisition evidence only, not a training,
replay-credit, or scientific-efficacy result. The stopped natural parent is unchanged.

## Provenance and validation

- Bundle: `qwen3-controlled-specialization-001-handoff-1790442678000363226.zip`.
- Locally computed SHA256: `4e5e522894f8a67d6486c7ddc769e70843c3110000f0f6a9386e3af371378c52`.
  No independently supplied export checksum was present in the pasted acquisition log.
- Plan: `fb554a12c60da2d354606f8fb1f5d5c6894321adb47df4de96940e51256432af`.
- CPU-only `pact.training.controlled_specialization audit` passed: inventory checks,
  reconstruction from embedded parent, child plan/selection, recovery journals,
  donor validation/support, and exact saved-report reconstruction.
- Colab log reports actual loaded frozen actor tensor verification. The metadata
  bundle does not contain weights for a second local tensor comparison.
- Saved recovery state is safe; all 75 attempted calls are committed, zero unresolved.

## Acquisition results

| Measure | Observed |
| --- | ---: |
| Prespecified fitting tasks | 32 |
| Complete correct/wrong synthetic pairs | 22 |
| Complete pairs by family | 11 ARC / 11 LogiQA |
| Accepted correct-target packets | 30 |
| Accepted wrong-target packets | 23 |
| Rejected attempts (target mismatch) | 22 |
| Supported clean/early rows | 44 of 64 |
| Eligible actor/row cells | 132 of 192 |
| Supported tasks / multi-actor supported tasks | 22 / 22 |
| Generation calls | 75 of 128 maximum |
| Reserved output tokens | 19,200 of 32,768 maximum |
| Actual input / output tokens | 19,236 / 3,056 |
| Summed generation time | 213.71 seconds |

Structural status is `ready_for_replay`; both eight-task support thresholds pass.
Ten tasks still lack complete pairs. They remain missing; do not add draws or
replace tasks. Generation time excludes model loading and Drive persistence and
is not billed runtime. Replay, frozen scoring, optimization, and development
evaluation have not executed in this child.

## Fixed sample inspection and limits

The eight prespecified review tasks contain five complete pairs, two positive-only
tasks and one task with neither target accepted. Local assistant inspection found
concrete limitations: the negative packet for `arc_challenge:Mercury_7057295`
provides reasoning consistent with the correct option while asserting the wrong
option; the negative packet for `logiqa:train-3788` explains why its option fits
the defined effect although the question asks for the exception. Other negative
packets include false assertions or loose rationalizations. Wrong answers are
intentional in this design, but answer/rationale contradictions can confound the
meaning of controlled insertion effects. Two of the five complete sampled pairs
also fail the recorded length-bin match; this is a diagnostic, not an added filter.

These observations are not a formal human approval or a determination that the
whole source has a systematic defect. They must remain visible in the later
packet/order/seed review. Structural acceptance does not verify reasoning. No
packets were edited, regenerated or removed, and no approval file was created.

## Next decision

Replay is structurally eligible but has not been authorized by this audit. If the
user elects to continue, use the same plan, frozen pairs and effective actors for
the bounded replay and subsequent frozen scoring stages, then return their bundle
for the required artifact-bound pretraining review. Do not start training from
acquisition support alone. No full-PACT or efficacy claim is supported.
