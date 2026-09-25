# Controlled receiver supervision: completed evaluation audit — 2026-09-24

The bounded study completed. Receiver SFT changed answer-token likelihoods but did
not change receiver correctness relative to either frozen initialization or task
SFT on the matched evaluation cohort. This is an executed training-only feasibility
study, not demonstrated PACT efficacy, natural robustness, or final-test evidence.

## Returned artifact and verification

- File: `results_import/qwen3-receiver-supervision-controlled-001-handoff-1790186567377083314.zip`
- Bytes: 10,639,934
- SHA256: `ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea`
- Reported Drive snapshot: `/content/drive/MyDrive/PACT/receiver-supervision/qwen3-receiver-supervision-controlled-001/snapshots/1790186567287661355-f91b8bf05d04`
- Recovery source: clean `13ab011df8b1b27d6d1478104db1a9e8a35a4081`.
- Original training source: clean `27889da90d2afce934fffb1baac9acb64ec3a1e2`.

The bounded safe archive reader verified all 2,658 payload members and their
checksums. Rehydrating metadata on temporary scratch and running the existing
`report()` audit reproduced the returned report exactly (canonical JSON equality).
This rechecks parsed correctness, cohort coverage, paired prompts/seeds/decoding,
team attack/node matching, scoring coverage and call journals. All 1,266 protected
inventory entries from the preceding training bundle retain their recorded bytes
and SHA256. Actual available JSON bytes were verified by the archive reader;
omitted checkpoint tensors are represented by inventory hashes, not independently
rehashed locally. No imported code was executed.

All three arm checkpoints declare effective actor tensor hashes matching the
recovery receipt and its digest. This supports completion of the GPU recovery path
under the recorded runtime checks. The prior FP32→BF16→FP32 nonfocal loading
deviation remains explicit; it is not retroactively original-FP32 preservation.
Full tensor files remain in the reported Drive snapshot, which was not independently
accessed during this local audit. State reports `recovery_safe: true`.

## Completion and budget

| Component | Completed |
|---|---:|
| Donor generation | 217 calls |
| Frozen evaluation | 201 calls, 57 CE forwards |
| Task-SFT evaluation | 201 calls, 57 CE forwards |
| Receiver-SFT evaluation | 201 calls, 57 CE forwards |
| Total generation | 820 attempted / 820 committed; zero unresolved |
| Total evaluation CE | 171 forwards |
| Training | 24 updates per trained arm; no recovery updates |

Global input/output tokens are 253,017 / 37,337; reserved output tokens 200,704,
within the unchanged 1,104-call / 273,408-token ceiling. Each arm contains 105
records: 57 controlled receiver responses, 32 private answers, and 16 natural-team
trajectories (eight tasks × clean/exchange, seven calls per trajectory).
Fit support is 45 tasks (17 hold, 28 repair). Held-out support is 19 tasks
(13 hold, six repair); held-out means the study's held-out portion of training-split
data. Both donor controls exist for all these contexts. These 57 conditions are
not 57 independent tasks.

## Free-generation outcomes

Entries are correct / evaluated. Hold and repair strata refer to the original
frozen focal packet. Failed/abstaining answers remain failures in denominators.

| Outcome | Frozen | Task SFT | Receiver SFT |
|---|---:|---:|---:|
| Hold, wrong-target donor (primary preservation) | 13/13 | 13/13 | 13/13 |
| Repair, correct-target donor (primary repair) | 1/6 | 1/6 | 1/6 |
| Hold, correct-target donor | 13/13 | 13/13 | 13/13 |
| Repair, wrong-target donor | 0/6 | 0/6 | 0/6 |
| Hold, peers withheld | 13/13 | 13/13 | 13/13 |
| Repair, peers withheld | 0/6 | 0/6 | 0/6 |
| Private answers | 20/32 | 21/32 | 21/32 |
| Natural-team clean terminal success | 5/8 | 5/8 | 4/8 |
| Natural-team exchange terminal success | 4/8 | 4/8 | 5/8 |

Every pair of arms has identical receiver correctness on all 57 matched responses:
40 correct→correct and 17 incorrect→incorrect. This does not mean identical raw
outputs, abstention behavior or likelihoods. Correct-target advice repairs one
of six tasks compared with withholding peers in **all three arms**, on the same
`logiqa:train-2180` item. That observed peer benefit predates the new SFT updates.
Receiver SFT does not add a successful repair or improve hold performance here.

Both trained arms gain the same one private-answer success relative to frozen;
this is not receiver-specific. Each arm has one private abstention and one invalid
answer, counted as failures. For peer-withheld repair, receiver SFT has two
abstentions versus three in the other arms, but still zero correct answers.

Natural-team receiver SFT loses one clean success and gains one exchange success;
all arms total 9/16 terminal successes. These are eight paired tasks, not 16
independent tasks. The smoke result does not establish natural-team improvement
or attack robustness. Task SFT preserves frozen team correctness on every pair.

## Teacher-forced answer-token loss

Task-mean NLL below is over the prespecified scored answer token, not generated
rationale quality or full-completion likelihood. Lower is better on this diagnostic.

| Receiver condition / stratum | Frozen | Task SFT | Receiver SFT |
|---|---:|---:|---:|
| Correct-target / repair | 11.376202 | 8.300790 | 6.341497 |
| Wrong-target / repair | 24.211892 | 18.394501 | 16.058600 |
| Peer-withheld / repair | 19.332207 | 14.992425 | 13.440624 |
| Wrong-target / hold | 0.063540 | 0.044620 | 0.025162 |

The probability-level changes show the arms are not identical in scoring. They do
not translate to extra correct receiver completions in this bounded run. Repair
loss decreases also occur without peers, so attributing all loss change to learned
peer use is unsupported. Correct-target/hold and withheld/hold loss remains near
zero (receiver SFT approximately 8.25e-8 and 1.78e-5 respectively).

## Interpretation and limits

The supervised path is operational: supported examples, real focal updates,
matched three-arm GPU evaluation, explicit precision recovery and an auditable
return all completed. The study did not demonstrate an incremental receiver-SFT
accuracy or repair benefit. Do not replace this conclusion with a claim that
supervised receiver learning is impossible: there is one training seed and only
six held-out repair tasks. Degenerate [0,0] empirical paired-bootstrap intervals
for unchanged outcomes do not establish population equivalence.

Synthetic donors were generated with offline answer conditioning; their rationales
remain `not_reviewed`. Keep these controlled-context findings separate from natural
trajectories. Original frozen own-packet histories are unchanged. DPO remains off;
all-agent joint refresh, specialization/full-PACT integration and final-test
assessment remain deferred. No new model calls, training, dependency changes,
commits or pushes were performed for this audit.

The current bounded run is complete. Any next experiment requires a separately
specified design; no extra draws, seeds, steps or retrospective task replacement
are authorized by this result. Existing donor/trace inspection can inform that
review without reopening completed diagnostics.

## Checks executed for this audit

Archive SHA256, bounded member/type/path checks and all payload checksums passed.
Production report reconstruction matched exactly. Protected prior inventory,
effective-identity receipt links and three 201-call journals passed. No regression
suite or GPU experiment was rerun: this change records audited evidence only.
