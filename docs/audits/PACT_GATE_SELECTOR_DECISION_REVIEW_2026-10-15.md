# Gate and selector decision review — 15 October 2026

The authorized diagnostic phase is complete. The evidence supports a substantial
output-contract improvement and a remaining candidate-selection problem. It does
not support promoting a learned gate, changing thresholds, or starting full PACT.

This synthesis joins the [saved-gate audit](PACT_GATE_DIAGNOSTICS_2026-10-15.md)
and [completed selector audit](PACT_SELECTOR_CONTRACT_COMPLETE_2026-10-15.md).
It adds a read-only mechanical breakdown of existing clean selector records. No
model call, fitting, new semantic annotation, or policy selection occurred.

## What the evidence distinguishes

| Question | Observed evidence | Interpretation and limit |
|---|---|---|
| Was the selector contract a problem? | Fresh legacy valid 0/202; clarification valid 190/202, with identical parser and fixed inputs/model | The specified clarification greatly improves compliance on this bank; historical failures stay failures |
| Does fixing it solve useful correction? | Clean deployed 44/64 to 45/64, one rescue, no observed harm | Small observed benefit; eight available rescue opportunities remain unused |
| Is the primary gate blocked by the tuning risk screen? | Maximum active original tuning utility −0.571269 | No proposed switch reaches that screen at original nonnegative thresholds |
| Does ranking contain useful information? | Correct top alternative in 16/16 tuning opportunity views, spanning six tasks | Relative ranking can coexist with nonpositive utility; six reused groups do not establish generalization |
| Is a favorable checker verdict enough? | Restricted fit verdict favors 30/32 improving and 91/112 harmful candidate rows | Favorable checking alone is not a demonstrated safe correction signal |
| Would lowering thresholds suffice? | Primary diagnostic threshold −2 yields six tuning rescues and fifteen harms | Releasing more actions can introduce substantial harm; no diagnostic point is a selected policy |

## Remaining clean selector errors

Read directly from the completed PRIVATE derivative's
`selector_per_view.private.jsonl`, retaining only `selector_contract_v2` and
`view == clean`. Opportunity means the original anchor is wrong and at least one
valid candidate is correct. These are evaluator-side descriptions, never runtime
selection masks.

| Clean population | Tasks | Outcome |
|---|---:|---|
| Correct original anchor | 44 | All remain correct |
| Wrong anchor, correct candidate available | 9 | One rescued; eight remain wrong |
| No correct anchor or candidate | 11 | All remain wrong; selection cannot exceed this answer-set bound |

All nine opportunity responses are strictly valid. Among the eight missed
opportunities, six intentionally select the wrong anchor and two select a wrong
peer. One of those two peer selections changes the answer; the other retains the
same wrong answer through a peer. The sole successful rescue is also a peer
selection. Both clean abstentions occur among the eleven tasks with no correct
candidate. There are no malformed clean v2 responses.

Thus a further parser-only fix cannot recover these eight recorded misses: their
outputs already satisfy the contract. This does not identify why the model chose
those candidates. Anchor bias, weak discrimination, rationale content and other
mechanisms remain hypotheses. No semantic truth label or causal attribution is
inferred from the selected identifier.

The six anchor-retention misses are not evidence that forcing a switch is safe:
44 clean anchors were correct, and the saved checking evidence contains many
favorable verdicts for harmful alternatives. Selection and deciding whether to
switch must both be evaluated.

## Recommendation for review

Close the current phase and retain v2 as a functioning, measured simple baseline
for any separately designed future comparison. Do not replace the historical
parent baseline, adopt v2 as a validated deployment policy, or extend its exhausted
404-call plan. No additional Colab work is required for this phase.

If a new method is pursued, prioritize a bounded, prespecified study of whether
existing evidence can distinguish beneficial switches from harmful ones. Merely
adding optimizer steps, forcing disagreement, loosening parsing or lowering a
threshold is not justified by these results. Any future proposal must specify its
mechanism, controls, objective, risk rule, sampling units, exposure boundaries and
budget before execution. This recommendation chooses no new model, dataset,
threshold, training pool or experiment ID.

The genuinely missing evidence is performance of a frozen actionable correction
rule on separately authorized evaluation material, with enough independent rescue
and harm opportunities to assess its trade-off. Current development observations
cannot supply fresh confirmation after guiding the next design. Neither observed
zero harm nor a task-bootstrap interval is a risk guarantee. Transfer and the
previously deferred human/span review remain deferred.

## Validation and scope

The completed selector audit already verified archive hashes, immutable parent,
all 404 requests, model identity, smoke reuse and report reconstruction. This
follow-up read only the resulting private records and counted clean paths by
oracle support, original correctness, strict status and selected candidate type.
Only aggregate counts are recorded here; raw questions, IDs, prompts and responses
remain outside Git. Documentation whitespace checks passed. No unit tests were
rerun, since code and methodological contracts were unchanged.
