# Fixed-bank specialization collection audit

Audit date: 2026-09-26. Run: `qwen3-specialization-contrast-001`.
Outcome: **insufficient_assignment_support; stop before replay**.

## Provenance and verification

Returned bundle: `qwen3-specialization-contrast-001-handoff-1790416052208683365.zip`.
SHA256: `555d9bd2e724c59ca4a91db156d450f814d0149ed6413922e965c3a85fb4e69f`.
Source commit: `28565003e10c91cf64f5c54b87284598f1331f65`, recorded clean.
Plan hash: `99ff21066f93f26fae33e6cbf70623313b0f9acd09e9e6d49e0702674af5131c`.

The trusted metadata-only CLI audit verified the ZIP inventory and reconstructed
its saved report exactly. A separate offline collection reconstruction regenerated
all prescribed anchor/candidate requests from the frozen plan, checked committed
responses against saved anchors, recomputed pair masks using the existing selector,
and matched candidate_support.json exactly. Recovery validation passed and the
returned state records recovery_safe=true. No model or imported code executed.
Local audit artifacts are in results_import/specialization-return-audit/.
The review ZIP does not contain weights; this audit cannot independently reload
GPU tensors. The returned environment records the historical effective-load policy.

## Results

All 32 fitting tasks completed both clean and early conditions (64 rows).
The 32 selected development tasks were not evaluated.

| Measure | Observed | Required to proceed |
|---|---:|---:|
| Distinct tasks with an eligible pair | 2/32 | At least 8 |
| Distinct tasks with a multi-eligible row | 2/32 | At least 8 |
| Eligible actor/task/condition cells | 5/192 | Task-level gates above |
| Rows with no eligible actors | 62/64 | — |
| Rows with two eligible actors | 1/64 | — |
| Rows with three eligible actors | 1/64 | — |

Supported tasks were arc_challenge:MCAS_2004_8_8 (all three actors in one row)
and logiqa:train-0903 (actors 0 and 2 in one row). Eligibility means the unchanged
selector found an admissible correct/wrong private-completion pair among four
additional candidates. Missing eligibility is not synonymous with zero correct
coverage or no disagreement among the three initial agents.

Collection attempted and committed 1,216 generation calls, with zero unresolved
attempts. Reserved output tokens: 299,008; actual input tokens: 344,838; actual
output tokens: 57,095. This exactly exhausts the collection call ceiling without
exceeding it. Replay calls, teacher-forced scores and evaluation calls: zero.
Training was not executed. Each of the four evaluation systems has 64 missing
rows; these are unexecuted observations, not incorrect answers.

## Interpretation and disposition

This bounded candidate acquisition did not provide enough admissible natural
correct/wrong pairs across distinct tasks for the prespecified specialization
study. No continuation-credit or assignment contrast was measured on this new
bank, and no specialization efficacy comparison exists. This does not establish
that specialization cannot work under other configurations. The older bank's
assignment contrast remains separate historical evidence.

Stop this run before replay, assignment, training or development evaluation.
Do not add draws, replace tasks, relax the support threshold or reset budgets.
Any new run or methodological change requires a separate explicit decision.
Completed receiver/GPQA results and manuscript placeholders remain unchanged.

The returned export log reports durable snapshot
`1790416058064299645-d3b470ec3286` and the matching Drive bundle. Local audit
verified the uploaded bundle; it did not independently read Google Drive.

## Checks executed

- specialization_study audit with the expected SHA256: passed.
- Full read-only collection reconstruction and exact support comparison: passed.
- Journal/recovery validation: passed.

No code changed, so the regression suite was not rerun. Actual collection is now
GPU-executed evidence; replay, real-model specialization training and evaluation
remain unverified and unexecuted in this study.
