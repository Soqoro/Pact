# Stage II CPU decision-packet return — 3 November 2026

## Result

The returned receipt reports `inactive_packet_written`, zero model calls and no
active receipts written. The packet supplies the previously remote-only GPQA group
classification. It does not certify a cohort or approve execution.

| Question | Returned finding |
|---|---|
| GPQA records / unique grouped identities | 448 / 448; zero ungrouped records |
| Definitely excluded GPQA groups | 199 |
| Unresolved GPQA groups | 249 |
| Certified eligible GPQA groups | None reported |
| Unique LogiQA group accounting | Unavailable (`null`) |
| Previously reported LogiQA item accounting | 1,335 denied; 6,041 unknown out of 7,376 items |
| Preserved Stage I allocations | 960 unique source content groups |
| Review queue | Two scope decisions; zero supplied concrete pair cases |
| Candidate / freeze | Absent / false |
| Historical spending / remaining balance | Unresolved / unknown |
| Future proposal | Inactive; conditional 23,728 generations, not an allowance |

The 199 exclusions and 249 unresolved groups partition the 448 grouped GPQA
identities. The earlier 198 Diamond-protected count is a reason-specific count;
this returned summary does not establish the reason for every additional excluded
group. Do not sum overlapping exclusion reasons or promote the unresolved 249 to
eligible. LogiQA's 6,041 figure remains an item count, not a unique-group count.

## Provenance and validation

The pasted SANITIZED summary, serialized exactly as supplied with a terminal
newline, matches the SHA256 in its supplied CPU receipt:
`f71f912bc116f1936f8861d7a7661caa56d03a715a3bdbcf906c39d73942657e`.
The two supplied JSON objects were parsed and preserved under ignored
`results_import/stage2-decision-packet-return-2026-11-03/`.

This is an internal integrity match against a user-returned receipt, not an
independent cluster attestation. No PRIVATE packet was supplied or reverified.
The receipt also identifies the inactive proposal with SHA256
`de116912b1e7f367bf150e137b7604a315f4ce0601909a4c009f22b9294c5435`,
matching the earlier local proposal's recorded identity. The remote proposal bytes
were not separately supplied in this return.

The worker reports it verified the existing audit, source/lineage metadata,
exposure inventory, exact reconciliation draft and authoritative parent records
on the cluster. Its `locally_verified_bytes` provenance refers to that worker's
filesystem, not independent access by this assistant. The supplied audit now
reports GPQA and LogiQA `bytes_verified`; this packet did not reread raw sources or
recompute eligibility (`raw_source_eligibility_recomputed=false`).

The training dependency hash remains
`d01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49`.
No current GPU runtime or checkpoint-tensor preflight was performed.

## What changes, and what does not

The remote-metadata handoff is complete for the fields this worker exposes.
The earlier local packet's unavailable-source status is superseded for source
availability by the returned audit metadata. Its absence of local GPQA group
counts is supplemented by the 199/249 classification above. Historical packets
remain unchanged.

The two decisions in the [exposure review](stage2_exposure_review_2026-11-03.md)
remain outstanding:

1. **Coverage scope:** whether to accept the stated conditional nonintersection
   under the original frozen-source contract, while retaining missing later
   enforcement and spending uncertainty and all existing exclusions.
2. **Material overlap:** whether an applicable existing private review covers the
   current sources and exclusions, or which concrete scope/cases still need an
   authorized review. Zero supplied pair cases does not certify zero ambiguity.

Neither judgment can be inferred from successful CPU execution. Do not set
`coverage` or `material_overlap_review` merely to clear the gate. There is no need
to rerun the completed packet or repeat history scans. If a candidate is later
constructed, its actual group eligibility and source counts must be verified;
current aggregate capacity is not a substitute.

Future accounting acceptance remains a separate decision. The existing proposal
is unchanged, its signature unset, and the real GPU child remains unconnected.
This return does not authorize inference, training, source acquisition or a new
prospective evaluation.

## Local work performed

Parsed the two returned JSON records, verified the summary-to-receipt hash and
448 = 199 + 249 arithmetic, preserved the sanitized return, and added this review.
No implementation changes or new unit tests were necessary. Existing evidence,
experiment-ledger bindings and unrelated local files were preserved. No remote
commands, model work, approval activation, commit or push occurred.
