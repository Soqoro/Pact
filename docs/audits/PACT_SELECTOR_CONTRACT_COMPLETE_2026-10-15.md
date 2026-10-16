# Selector contract child: completed GPU return audit

The completed `pact-anchor-selector-contract-002` return passes local offline
verification. All 404 planned calls are committed and scored, with zero unresolved
attempts. Clarifying the output contract substantially improves valid selection,
but clean deployed correctness increases by only one task: 44/64 to 45/64. This is
an exposed-development prompt comparison, not learned PACT improvement or a new
validated correction policy.

## Design and provenance

The study reuses 64 closed-parent development tasks (32 ARC-Challenge, 32 LogiQA),
with 64 clean views and 138 accepted variants on 46 tasks. Every one of the 202
views receives a fresh legacy-prompt repeat and an output-passage-only v2
clarification. Candidates, task text, seeds, parser, fallback, model weights and
inference settings remain fixed. No malformed output is salvaged.

- Return pair: `1792072183327689752`.
- PRIVATE SHA256: `146677bedbfe12481abd4b996fb924faefbc4c544661693737bb5e304dab2b9c`.
- SANITIZED SHA256: `369e2b8df18ce9d695a9a05796e121e2f61e5d577e79de914c7f78fd382dccef`.
- Frozen plan: `d704f2c4e10ed509547773cbabecd214890a23d8f69004ba2cbdb6d9d958d09f`.
- Clean source commit: `58e7bf3e6ed7b9defdc231298133b4a1b2dd6c8e`.
- Model identity snapshot: `65936c3dea8c5b55cf0e89695cc0a0e7b837b9d684fc6ada00a0519e07cd231a`.
- Pristine parent-matching J8/Qwen3-8B, BF16/SDPA, no adapters, greedy non-thinking,
  512 output-token cap and 8192 total-token cap. Returned runtime identity matches
  the included smoke. The earlier CPU-to-GPU metadata correction preceded dispatch
  and changed only the recorded runtime fingerprint.

The four included smoke calls are byte-preserved; the continuation adds exactly
400 calls. The 202 fresh legacy outputs happen to match their historical raw
outputs exactly, verified from separate child intents/results. This is an observed
match on these requests, not a general cross-runtime determinism guarantee.

## Formatting and selection

| Measure, all 202 views per arm | Fresh legacy | V2 |
|---|---:|---:|
| Schema accepted (includes ABSTAIN) | 0 | 198 |
| Valid non-abstaining selection | 0 | 190 |
| ABSTAIN | 0 | 8 |
| Malformed | 202 | 4 |
| Strict correct | 0 | 123 |
| Deployed correct, including fallback | 125 | 126 |
| Fallback | 202 | 12 |
| Correct through fallback | 125 | 3 |
| Intentional anchor selection | 0 | 152 |
| Peer selection | 0 | 38 |

Legacy failures comprise 198 extra/missing/reordered-key failures and four
invalid-JSON/duplicate-key failures. V2's four malformed responses use unknown or
unavailable identifiers; its other eight fallbacks are explicit abstentions.
Schema acceptance is therefore different from a valid substantive selection.
All-view totals repeat tasks and must not be treated as 202 independent examples.

## Clean task outcomes

| Dataset / arm | Strict valid | Strict correct | Deployed correct | Rescue / harm versus anchor | Candidate oracle |
|---|---:|---:|---:|---:|---:|
| ARC fresh legacy | 0/32 | 0/32 | 27/32 | 0 / 0 | 27/32 |
| ARC v2 | 31/32 | 27/32 | 27/32 | 0 / 0 | 27/32 |
| LogiQA fresh legacy | 0/32 | 0/32 | 17/32 | 0 / 0 | 26/32 |
| LogiQA v2 | 31/32 | 18/32 | 18/32 | 1 / 0 | 26/32 |
| Combined fresh legacy | 0/64 | 0/64 | 44/64 | 0 / 0 | 53/64 |
| Combined v2 | 62/64 | 45/64 | 45/64 | 1 / 0 | 53/64 |

V2 clean accuracy is 70.31%, versus 68.75% deployed legacy/anchor accuracy:
+1.56 percentage points. Both v2 clean fallbacks occur on wrong anchors and add no
correct answers. Of nine clean rescue opportunities, all in LogiQA, only one is
used; eight remain unused. ARC has no clean candidate-constrained rescue headroom.
V2 makes two clean answer switches: one rescue and one wrong-to-wrong switch.
There is no observed correct-to-wrong harm, but this small cohort does not certify
low risk on new tasks.

The prespecified paired, task-group bootstrap (500 draws, seed 20261015) gives a
LogiQA clean deployed difference of +3.125 points with a descriptive interval of
0 to +9.375 points. ARC's observed difference and empirical interval are zero.
The latter reflects identical observed outcomes, not proof of zero population
risk. All-view uncertainty keeps each task's views together. These are reused,
exposed development tasks; neither views nor calls are independent sampling units.

## Accepted variants and robustness

Each style has 20 ARC and 26 LogiQA matched tasks, with no missing views. For both
arms, each of claimed consensus, claimed independence, and the separate ordinary
rephrase control has zero correct-to-wrong and zero wrong-to-correct transitions
relative to that arm's own clean response. The clean-correct denominators are 15
ARC and 12 LogiQA tasks per style. Joint correctness over clean plus both attack
styles is 15/20 ARC and 12/26 LogiQA for each arm (27/46 combined).

| V2 style | ARC target answer / candidate | LogiQA target answer / candidate |
|---|---:|---:|
| Claimed consensus | 2/20 / 0/20 | 7/26 / 2/26 |
| Claimed independence | 2/20 / 0/20 | 9/26 / 4/26 |
| Ordinary rephrase (control) | 2/20 / 0/20 | 7/26 / 1/26 |

Legacy target-answer matches are 2/20 ARC and 7/26 LogiQA for every style, with no
intentional target-candidate selections: all legacy decisions are fallback.
Target-answer matching is not itself evidence of persuasion or a newly induced
error. V2 can change a wrong answer or candidate without changing binary
correctness. No semantic judgment about rationale quality is made here.
The single clean rescue is the included smoke task, which has no accepted variants;
its preservation under these rewrites is therefore not tested.

## Accounting and verification actually executed

- 404 attempts / 404 commits / 404 expected; zero unresolved, safe recovery.
- 202 fresh legacy-reference calls; 206,848 reserved output tokens, exactly the cap.
- 242,154 input tokens and 41,854 actual output tokens; compute units unreported.
- Zero new source/checker/rewrite calls, gate fits, optimizer updates or
  teacher-forced forwards.
- Both supplied ZIP hashes and internal archive checks passed. Private extraction
  stayed outside Git; no imported script was executed.
- Exact planned request-key coverage, loaded model identity, native call/token
  accounting, immutable embedded parent receipt and four-call smoke preservation
  passed. All 404 rendered prompts, legacy parent-request identities, corresponding
  seeds and parent-result hashes passed reconstruction.
- Reconstructed private summary equals both saved private and sanitized summaries.
  Candidate-oracle and final = anchor + rescue - harm checks passed. Sanitized
  screening for selected task IDs/questions and decodable token-array fields passed.
- Artifact reconstruction and contract checks ran locally on CPU. Unit tests were
  not rerun for this documentation-only audit. No model download, generation,
  training, commit or push was performed locally.

Private audit receipt:
`/var/tmp/pact-selector-complete-1792072183327689752/local_complete_audit.json`.
The uploaded archives remain unchanged and ignored by Git.

## Disposition

This bounded child is complete; no further Colab calls remain in its plan. The
contract clarification addresses most observed formatting failures but does not
close the candidate-utilization gap. Historical parent outputs, all five KEEP_ONLY
gates, the closed selective result and previous study conclusions remain unchanged.
No replacement policy is selected. Transfer, human/span review, new studies,
full-PACT training and final-test evaluation remain deferred. Any next experiment
requires a separately reviewed design and authorization; this result does not
supply either automatically.
