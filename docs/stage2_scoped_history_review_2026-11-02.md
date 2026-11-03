# Stage II scoped history reconciliation — 2 November 2026

**Decision: no Stage II execution was found in the inspected records. This does
not establish zero historical spending or authorize execution.** The original
revival run has missing later history. Keep that uncertainty explicit; do not
repeat broad scans of the same evidence or promote an older checkpoint to a safe
resume boundary.

This report compiles user-returned aggregate results from AAI Slurm and Colab.
Codex inspected the repository's storage-incident audit and inventory implementation;
it did not access those remote systems or independently re-read their archives.
No raw GPQA examples, labels or item maps are included. This is a documentation
review, not an accepted `reviewed_history` receipt, new MethodSpec or approval.

## What was inspected

| Evidence | Returned result | Scope and limitations |
|---|---|---|
| Slurm job 1114278 | Completed, exit 0:0, 74 seconds; four roots present; 147,646 files seen; 30,707 JSON records inspected; no candidate matches | Four recorded roots only. Four directories skipped, 39 symlinks not followed, 14 archives unopened. Absence is not a zero-spending attestation. |
| Broad Drive discovery | 9,931 files seen; one JSON inspected; no candidate matches | Hit its time limit; 33 directories skipped and 135 archives unopened. This scan does not substantiate absence. |
| Drive shallow listings | Three revival runs and two Stage I evaluation runs; no separate Stage II folder in the returned top-level listing | Names alone cannot exclude embedded probe activity or work outside this root. |
| Continuation-003 latest snapshot | Inventory verified; safe receipt; 928 recorded files; zero `probe_training`, `probe_scores`, or `score_intents` entries | Snapshot metadata only; payloads were not freshly verified by this diagnostic. |
| Replacement-002 latest snapshot | Inventory verified; unsafe receipt; 1,479 recorded files; zero entries in the same three probe categories | Historical unsafe state remains unsafe. The pending marker was not changed. |
| Original-001 latest snapshot | Incomplete index/marker state | No fallback or terminal closure was inferred. |
| Original retained step-28 archive | Exact 3,569,263,304-byte archive copied and SHA256 verified; 9,994 recorded files; all 2,438 generation intents belong to budget stage I; no entries in the three probe categories | Original plan identity and inspected JSON-member checksums verified. This is an earlier retained boundary, not evidence about missing later work. No restore or model load. |

Recorded Slurm roots were `/dataset/suaq0001/PACT`,
`/export/home2/suaq0001/pact-aai-transfer`,
`/export/home2/suaq0001/pact-aai-downloads`, and
`/local/pact-suaq0001-1106891-d2PoqB`.
The Drive root was `/content/drive/MyDrive/PACT`.
The user states they are **unsure** whether Stage II ever ran. That statement
must not be converted into a negative execution attestation.

## Evidence identities

| Artifact | Identity |
|---|---|
| Slurm private inventory canonical digest | `b5bd4163d7f9401b6b592e5e4666ba28a4b03da6cdb80e7dd538c07ea29a08b7` |
| Partial Drive private inventory canonical digest | `f0a9f24c1466797897d2c223779faf6bc5da49af8d0bf1ad9170b7538d9b6e02` |
| Original retained archive SHA256 | `8371bafc49022ae2d8e344696be465fcb8410a39712e348a0715530a0a455e4c` |
| Original plan canonical digest | `a8ee5cf50d0878dbe6fec8c36364e8b1469cc79c39afd66244b9ecf5f1e5bc71` |
| Original incomplete latest snapshot | `1792325381948137221-1b99c7e2ccd6` |
| Continuation snapshot | `1792630897599488541-51037828132a` |
| Replacement snapshot | `1792486927348121446-eefe02888431` |
| Exposure draft canonical digest from job 1113032 | `fb31284ac87bc76cc55153b98fb78715413bb54865f9a601b07c9dae3c04722f` |
| Exact completed Stage I parent PRIVATE archive SHA256 | `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0` |
| Executed Stage I source canonical digest | `85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b` |

The inventory digests above identify canonical private JSON contents, not an
independently imported remote report or whole-file hash including its trailing
newline. The archive SHA256 identifies actual archive bytes. Preserve these
identity distinctions.

## What is and is not reconciled

The saved original boundary has 2,438 Stage I generation intents and zero Stage II
generation intents. That agrees with the prior source/scratch milestone. The
replacement and continuation probe-file inventories add no evidence of Stage II
execution. The scoped Slurm search adds no matching plans or attempts.

The original storage incident nevertheless left later archives missing and newer
snapshot directories incomplete. The previously documented missing object names
and cleanup provenance remain authoritative. Cleanup removed only reviewed older
objects; it did not close the missing later history. See the
[storage incident audit](audits/PACT_REVIVAL_STORAGE_INCIDENT_2026-10-19.md) and
[Stage I prerequisite review](stage1_evaluation_prerequisite_review.md).

Do not label all unknown original Stage I work as consumed Stage II work. Equally,
do not infer no relevant probe exposure or spending from an earlier checkpoint.
The unresolved interval must be assessed for possible Stage II overlap before
execution ownership can be closed. No terminal original-run receipt is available
in the evidence reviewed here. No finite remaining Stage II budget is established.

## Source-readiness findings remain separate

Official GPQA Main and original ARC/LogiQA bytes were reported verified by job
1112958. The CPU source audit and diagnostic (1112981 and 1113022) found:

- GPQA Main: 448 records; 198 Diamond-protected records; 249 unique groups whose
  only reported reason is unverified exposure scope. These are not certified
  eligible groups. Multi-reason counts overlap and cannot be summed as partitions.
- LogiQA: 7,376 audited items, 1,335 denied and 6,041 unknown. Unknown item count is
  not a certified count of unique eligible groups.
- Job 1113032's draft adds all 960 Stage I allocations to each of the four
  exclusion fields. Historical GPQA partitions and repository selections add no
  further identities to that union. The source auditor already directly excluded
  executed allocations; do not subtract 960 again from its provisional counts.

The historical inventory matches its benchmark ledger but lacks the new
experiment-history, parent-source, full-coverage and overlap-review bindings.
The draft binds evidence and preserves exclusions; it is not an approved exposure
file. Material semantic-overlap review and current coverage remain unresolved.
Pretrained-model exposure remains unknown even if project freshness is certified.

## Readiness and budgets

| Question | Current answer |
|---|---|
| CPU loader/auditor and conditional graph implemented? | Yes, with previously reported CPU tests; this report adds no executable changes. |
| Real 64+64 cohort certified? | No. |
| Real candidate frozen? | No. |
| Historical relevant spending reconciled? | No; not assumed zero. |
| Remaining execution budget known? | No. |
| GPU execution authorized by this report? | No. |
| Original v3 plan released? | No; its ARC source infeasibility remains unchanged. |
| Existing Stage I results changed? | No. |

Conditional ceilings remain 8,112 assay generations plus 15,616 policy generations
(23,728 total; 12,148,736 reserved output tokens), 3,072 optimizer updates,
24,576 supervised forwards and 2,640 diagnostic forwards. These are prospective
ceilings, not remaining balances. New child names and scheduler jobs do not reset
wallets. Current checkpoint/runtime gates and the unconnected GPQA child GPU
execution path remain separate prerequisites.

## Next work and separate decisions

1. Continue CPU exposure reconciliation: match the current experiment history and
   recorded preview/manual exposures to actual exclusion receipts; preserve
   uncovered cases. Resolve material overlap questions under the existing policy.
   Do not populate approval flags merely to make the loader pass.
2. Re-audit the source only with genuinely reviewed exposure evidence, using a
   new versioned destination. Candidate construction can proceed independently
   of unresolved execution ownership; no probe or training follows automatically.
3. Revisit historical spending only if new terminal evidence, execution logs or
   previously uninspected relevant records become available. There is no reason
   to rerun the same broad inventory. Archive contents and other roots remain
   outside the completed discovery scope.
4. If relevant missing history cannot be recovered, an explicit accounting
   amendment would be a separate methodological decision. It must specify which
   historical uncertainty remains, what probe/request ownership may overlap, and
   finite proposed additional work. This report neither drafts a new allowance
   nor grants one. The user has not approved such an amendment.

No new cluster or Colab command is needed to review this report. No source
acquisition, training, inference, restore, cleanup, commit or push was performed
for this documentation update.
