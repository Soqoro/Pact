# Export checksum source transition — CPU review, 14 November 2026

The recovered inactive plan remains
`5ff472604f74ed80cdbdecb574dc83c9306e6a912f0159249b1861a689fdd025`, pinned to
commit `995e814e0883414b1ed56c590faad2e240cdf9b1`. Job 1121664 reconstructed it
exactly and persisted snapshot `1794641113259988805-22b145006de1`. No source
transition has been applied to that plan.

## Reviewed change

The only runtime/configuration byte change against that commit is in
`src/pact/revival/allocation_v3/storage.py`:

```python
# Before
persist_bundle(path, destination/'bundles'/path.name, timeout_seconds=600)
# Proposed
persist_bundle(path, destination/'bundles'/path.name, out[kind]['sha256'], timeout_seconds=600)
```

The original call cannot satisfy the existing required checksum argument.
The proposed call supplies the hash of the ZIP just packaged, preserving the
existing verified-copy API rather than changing it. No protocol, sampling,
training, scoring, eligibility, graph, cohort, checkpoint, precision, budget,
resume validator or execution permission is changed. All other 206 files covered
by `code_identity` are byte-identical. Documentation, tests and tools are separately
versioned by the eventual commit; they do not alter the scientific source hash.

Local code-review hashes:

| Binding | SHA256 |
|---|---|
| Old runtime source map | `17465cd698c0c7e1bc1935c546e5614862b8df682bc0619f6c3eefe913f63d4a` |
| Proposed runtime source map | `c7dbf4bccc7501456ee96aed79e7897e638674fe22faf4fb27a2ef30e54a4719` |
| Old storage file | `1a09ce82e1d78c2737ea8aebee5fac18e8c59ea17f00e024028746b7c63258b9` |
| Proposed storage file | `21adb24366ed54d002302ebccfc6d5bf4045db9fb06b99b5b5f0c46a9b5a3496` |

The new commit does not yet exist locally; the user must commit/push and pin it
before a real transition proposal is produced. The local dirty-tree comparison is
code review only, never a usable execution identity.

## Implemented audit

`tools/aai_documented_source_transition.py` supports:

```bash
PYTHONPATH=src python tools/aai_documented_source_transition.py code-review --new-checkout "$PWD"
```

The CPU-only `propose` stage requires old and new clean checkouts, the exact old
plan and a new private output destination. It runs the original validator in a
separate process under the old checkout. It checks that the exact recovered child
has no execution/preflight/policy artifacts, then verifies the plan bytes remain
unchanged before and after writing the separate proposal. This narrow inactivity
check does not certify zero historical spending elsewhere.

```bash
python -B tools/aai_documented_source_transition.py propose \
  --old-checkout "$OLD_CHECKOUT" --new-checkout "$NEW_CHECKOUT" \
  --run-dir "$EXISTING_RUN" --output "$NEW_PROPOSAL_DIRECTORY"
```

Outputs are `proposal.sanitized.json`, checksums and COMPLETE. No candidate plan,
approval record, signature, active allowance or modified old plan is emitted.
The proposal includes the exact old plan, both source identities, frozen scientific
digests, unchanged conditional limits, and explicit unresolved historical spending.
Current tensor loading and GPU checks are not repeated or claimed.

`tools/aai_documented_source_transition.sbatch` prepares this packet on node01
using CPU only, the established offline container/runtime and `/local:ro`. It
requires `PACT_CHECKOUT` and `PACT_COMMIT` for the newly committed candidate,
reads the old checkout from the existing pointer file, and writes only to the new
`/dataset/$USER/PACT/stage2-export-source-transition-proposal-v1` directory.
It does not submit itself or apply the proposal. Return the sanitized receipt;
raw GPQA content and PRIVATE bundles are not needed for this review.

## Validation and next decision

Five CPU tests passed for exact-patch enforcement, unrelated scientific edits,
source additions/deletions, no-fix rejection, unresolved attempts, and activated
preflight/policy artifacts. The real filesystem export regression passed for
PRIVATE/SANITIZED/RECOVERY copies and a verified compact snapshot. Shell syntax
passed. No GPU/model execution, network download, training or cluster submission
was performed locally.

The next artifact is the CPU-generated proposal binding the user's new commit.
Its review must explicitly decide the source transition before any plan/source
binding is changed. GPU preflight and physical spending remain distinct later
decisions. Do not pull new source into the original pinned checkout or edit the
old plan's `source_code`/hash to bypass validation.

## Returned proposal — job 1121675

AAI returned COMPLETED 0:0 in six seconds, status
`SOURCE_TRANSITION_PROPOSED_NOT_APPLIED`. Proposal SHA256:
`6e217d91d3b00464013ad3734a4ee1d23a476c619237c93e303c0e6c4d376d6a`.
The clean candidate is commit `93b89ce38be743acd6a3aa38177237ce99a3eeeb`;
old/new source and storage hashes match the local review above. Tool SHA256
`43755973eb6a90dec0f277a305eb41f40c90625bb989c318bc8335402e570e67`
also matches the local committed file. Returned evidence validates the original
plan under its original checkout and reports its bytes unchanged, zero model
calls/forwards/updates, and inactive wallet. No new tensor or GPU check was run.
The proposal file itself has not been independently imported locally; its digest
is recorded from returned stdout.

Review recommendation: accept only the exact checksum-repair source transition,
bound to this proposal and commit, while preserving original plan evidence and
requiring a separately recorded resulting source/plan binding. This recommendation
is not user approval or permission to run a GPU preflight, train, infer, or activate
spending. Transition approval/application remain false pending the user's decision.

## Subsequent user approval and implementation

The user replied “proceed” to the explicit approval question binding proposal
`6e217d91…76d6a` and commit `93b89ce3…eeeb`, with GPU preflight, training,
inference and spending still disabled. This authorizes the exact storage-source
transition only. It is not a new physical allowance or a reviewer signature.

Implemented `tools/aai_apply_documented_source_transition.py` plus CPU-only
`tools/aai_apply_documented_source_transition.sbatch`. The helper is versioned
separately from the approved runtime checkout. Its Python imports come from the
unchanged approved `93b89ce3…` checkout, so adding this helper does not silently
advance the scientific code pin. Both original and target validators stay intact.

Before writing, it verifies the exact approved proposal bytes, clean old/target
identities, original plan bytes, original validator, absence of execution artifacts
in this child, and the exact latest original durable snapshot/receipt/archive. Any
changed latest boundary or pending marker stops the operation. This scoped check
does not resolve unknown historical execution outside this inactive child.

The output is a separate inactive successor at:

`/local/pact-stage2-documented-export-fixed-$USER/runs/pact-stage2-documented-execution-001`

Its separate persistence namespace is:

`/dataset/$USER/PACT/stage2-documented-execution-export-fixed-v1/pact-stage2-documented-execution-001`

The logical child owner is unchanged. Only the plan's `source_code` and
`scratch_root` fields change; all cohort/graph/training/checkpoint/analysis/limit
fields remain exact, including unknown historical spending and inactive execution.
The resulting plan hash necessarily changes and is printed for review. The old
plan and snapshot are retained. Separate transition provenance links both hashes
to the approved proposal; PRIVATE/SANITIZED/RECOVERY exports and a verified
snapshot use the corrected native persistence function. No approval for GPU work
is generated. A failed operation retains partial evidence and never auto-retries.

Four focused CPU tests passed: exact two-field copying with old-plan preservation,
rejection of activation/zero-history substitution, execution-artifact rejection,
and actual compact snapshot verification including pending/latest-only stops.
The AAI application has not yet been submitted or verified by this local work.
Commit/push the helper, then submit the CPU wrapper with `PACT_HELPER_CHECKOUT` and
`PACT_HELPER_COMMIT`. It uses the existing old checkout pointer and exact target
path `checkouts/export-fix-93b89ce38be7`; it never updates either checkout.


### 2026-11-14: returned source transition and scoped GPU-preflight approval

User-returned job 1121682 completed 0:0 and reports
`SOURCE_TRANSITION_APPLIED_EXECUTION_DISABLED`. The successor plan is
`024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9`;
transition receipt SHA256 is
`2781aaa1377a5538586fe3bef5fcde5279c6c371970617465dfe7dfe8cb8898a`.
Only source_code and scratch_root changed; the original plan remains preserved.
These are returned log receipts, not locally rehashed imported bundles.

The user's subsequent “proceed” accepts preparation of the explicitly described
GPU preflight for this successor only: native access/runtime, context limits and
effective S0 loading. Use the existing preflight-only guard with spending_approved
false and the exact runtime checkout 93b89ce38be743acd6a3aa38177237ce99a3eeeb.
No generation, training, diagnostic forwards, spending-wallet activation or next
stage is approved. Historical spending remains unknown. Operator submission uses
sbatch; no cluster job was submitted locally. GPU outcome remains unverified.


### 2026-11-15: imported assay-smoke SANITIZED review

Locally verified archive `pact-stage2-documented-execution-001-SANITIZED-1794726627526519175.zip`
SHA256 `8c0ae9c04d0c39f7e5b8adf3f389bc82fdb9d1f0a926b96408176cda7db8fbd4`.
Verified unique membership (four files), exact payload inventory, both payload
checksums, and SANITIZED handoff type. Contents comprise summary and assay support
only, with checksum/handoff metadata; no task text or per-call traces present.

Summary reports 24 assay generation attempts, 24 committed operations, zero
unresolved, recovery_safe=true, 12,288 reserved output tokens, 8,370 input tokens
and 990 output tokens. Scores, training forwards, updates and policy operations
are all zero. Format statuses are 23 ok and one invalid. Invalid remains a failure;
no regeneration or repair is approved. This aggregate bundle cannot locate the
invalid call or determine its effects on downstream task outcomes.

One attack was attempted and accepted for ARC, and one for LogiQA. The report's
23 ARC and 39 LogiQA rejected_or_unavailable values cover the full 24/40 probe
cohorts; with only one attempt per source, these are unattempted remainder here,
not 62 observed rejected attacks. All contribution branch pairs are missing
because branch training/scoring has not executed, not evidence of zero gains.
There is no efficacy estimate or policy comparison at this stage.

Decision: smoke accounting/integrity passes within this SANITIZED evidence scope.
Per-call native identity, packet contents and invalid-call location were not
independently audited. Next review should obtain a private-side CPU diagnostic
with sanitized phase/family/status counts and the invalid-call category before
requesting collection execution. No broader physical spending is authorized;
historical spending and remaining historical budget remain null.


### 2026-11-15: locally verified collection SANITIZED bundle

Verified `pact-stage2-documented-execution-001-SANITIZED-1794730033344682597.zip`
SHA256 `6ba1d2ff176b393ecd4273cd8adbd15d4e810c603c1ed0d19f28ae65b9b2ccfe`,
unique four-member inventory and both payload checksums. Report is non-fixture,
assay-smoke and collect complete, recovery_safe=true, unresolved=0.
708 generation attempts and 708 committed operations include the prior 24 smoke
calls: 684 new generations, within the approved additional ceiling of 744.
Cumulative reserved tokens 362,496; new reserved tokens 350,208. Cumulative input
tokens 251,115 and actual output tokens 33,732. All training/scoring/update and
policy operation counts remain zero. Historical spending remains unknown.

Attack attempts cover all 24 ARC and 40 LogiQA probes. Accepted: 17/24 ARC and
32/40 LogiQA, totaling 49/64. The other 15 attacks were not accepted; this summary
does not distinguish invalid/abstaining/wrong-target reasons. Call arithmetic
reconciles exactly: 64*(1 attack+3 private+3 clean revisions+1 clean readout)
+49*(3 exchange revisions+1 exchange readout)=708. The 60 unexecuted conditional
calls are not lost dispatches and must not be regenerated.

Stored format counts: 668 ok, 33 invalid, 7 abstention. These are call counts,
not task accuracy or scientific efficacy. The SANITIZED bundle does not locate
failures by model/phase or show task-level outcomes. Branch pairs are all absent
because branch training and scoring have not occurred. No allocation gain can
be inferred. Next useful evidence is a private-side read-only CPU summary of
format failures by model/phase and attack rejection categories; no changed parser,
prompt, retry, branch training, scoring or later spending is authorized here.


### 2026-11-15: returned Q lineage diagnostic, job 1122723

User-returned CPU comparison completed 0:0 with no new inference. It reports
verified Stage I archive 754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0
and collection archive f9793a06b1a0cb431552117e8847d1b9f48d636d317cb319371558a606be40f1.
Exact joint S0 Q adapter identity is shared. All four stage/phase combinations
share model identity hash cc2dd6c4a59226e7a523064aae6f44cbdd712888569a960dade65c78d780d979,
generation-parameter hash 5330d1946ee54727c0ffcca75971406aee7252ed2dd7ac7f6e1b5a549ea77d4d,
and system-message hash 8b5833174af1a365c6e5a8f897ed9b7900a5876932a880e00763ac15a4ef85b1.
Stage II pristine fields match the parent. Tensor bytes were not rechecked by
this diagnostic, and full task/peer prompts naturally differ.

Q private invalid counts: Stage I same S0 203/384 (52.9%); Stage II 30/64
(46.9%). Revision invalid counts: Stage I 16/922 (1.7%); Stage II 0/113.
These historical physical-call counts are descriptive, not independent task
samples or a paired improvement estimate. Strong private-format failure predates
Stage II; no mismatch was found in the recorded identities checked. This does
not establish the causal mechanism or exclude every possible execution issue.
Preserve failures and exact S0/prompt/parser contracts; do not silently repair
the inherited behavior. There is no new inference or training authorization from
this result. A separately scoped branch proposal is the next execution decision.


### 2026-11-15: first temporary-branch proposal (not execution approval)

Prepared in response to the user's request to proceed with the first bounded
branch proposal. Proposed scope: branch/block=0/family=Q only, under successor
plan 024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9
and runtime commit 93b89ce38be743acd6a3aa38177237ce99a3eeeb. Start from
exact joint-trained Q S0; block 0 is the frozen first ARC fitting block. This is
fixed order, not selection based on the observed Q formatting failures.

The existing runner orders block fit tasks with temporary seed 17 and performs
eight batches of eight: eight optimizer updates, 64 supervised training forwards.
It saves a separate branch checkpoint and restores the live Q adapter and RNG
state in finally; rollback.json must mark complete and equal initial/restored
hashes before branch probe generation. The saved branch is then loaded for Q
only; L/M use S0 and R is pristine. No fitting uses probe tokens.

With 24 ARC probes and 17 already accepted frozen attacks, maximum additional
generation work is 24 new Q private packets + 41 conditions * (3 revisions +
1 readout) = 188, reserving 96,256 output tokens. The 48 L/M private calls reuse
exact S0 requests. No new attacks or rejected-attack retries. The full predeclared
all-attacks-accepted branch ceiling is 216; the reviewed observed-support scope
is tighter at 188 and must not authorize expansion. Cumulative maximum after
this branch: 896 generations, 458,752 reserved output tokens, eight updates and
64 supervised forwards. Zero diagnostic scoring forwards. Prior unknown
spending remains separate and unknown.

Pre-submission preparation must bind the exact completed collection PRIVATE
archive f9793a06b1a0cb431552117e8847d1b9f48d636d317cb319371558a606be40f1,
preflight receipt 1e697a75aec6dd47fe2669235b1597f2010c85b05158f773c097880dd33ea8bb,
verify 708 committed and zero unresolved at start, absence of earlier branch
work, and the actual block/probe/attack counts. A mismatch stops preparation; no
re-plan, replacement data or budget increase. Scope approval must be separate
from this proposal, permit only branch 0/Q, and export/stop. No score, next branch,
policy training, evaluation or Stage III is included. No job submitted, weights
loaded, or approval signature fabricated by this local preparation.


### 2026-11-15: locally verified block-0/Q SANITIZED export

Verified ZIP `pact-stage2-documented-execution-001-SANITIZED-1794734201351042740.zip`
SHA256 edda34ae52687dc527f79f45b61635e9396d2e50625c5f8ddd7871dbb439a198,
unique exact four-member inventory and both payload checksums.
Cumulative assay accounting: 896 generation attempts, eight optimizer updates,
64 supervised forwards, zero diagnostic scores; 904 committed operations, zero
unresolved, recovery_safe=true. Reserved output tokens 458,752. Relative to the
verified collection summary, delta is 188 generations / 96,256 reserved tokens,
171 ok, 16 invalid, one abstention. Cumulative formats: 839 ok,49 invalid,8
abstention; input/output tokens 308,616/41,600. Attack acceptance remains17/24
ARC and32/40 LogiQA. Policy operations remain zero.

The bundle contains summary.json and assay_support.json plus manifest/checksums,
not branches/block-0-Q/status.json, rollback.json or evaluated.json. Therefore
rollback/checkpoint identity and branch completion cannot be independently
verified from this export. The global stages list remains assay-smoke/collect;
implementation writes branch completion under its branch directory, so absence
from that list is not itself a failed branch. Returned job1122724 completed0:0
and reports complete=true, but receipt inspection is still needed.

No contribution scores exist; all branch paired score support remains zero.
Next evidence: read-only private-side CPU inspection of branch status, exact S0
rollback receipt, evaluated marker, checkpoint metadata and new call format
breakdown, without new inference or tensor-changing operations. Do not infer
accuracy from formatting or 904 generations from committed operation count.
No next-branch or scoring authorization is granted by the uploaded ZIP.


### 2026-11-15: locally verified block-0/L SANITIZED export

Verified ZIP pact-stage2-documented-execution-001-SANITIZED-1794744018060185519.zip
SHA256 3a018d811061aa821d70d8b75de77582b1c7b6ada989f60262a6c06c45f2c757,
exact unique four-member inventory and both payload hashes; compared with the
previous independently verified post-Q SANITIZED export. Cumulative:1084
generations,16updates,128supervisedforwards,zero diagnostic scores;1100committed
operations,zero unresolved,recovery_safe=true,555008reservedoutputtokens.
Block-L delta:188generations,8updates,64forwards,96256reservedoutputtokens,
187ok,zero invalid,one abstention. Cumulative formats1026ok/49invalid/9abstention.
Input/output tokens364837/49678. Policy operations remainzero; unknown historical
spending remainsnull. These aggregate format counts are not accuracy or gains.

The SANITIZED archive does not contain L status/rollback/evaluated/checkpoint
receipts; independent verification of those remains outstanding. Returned
job1122780 reports branchcomplete and0:0,9m09s, but does not replace receipt
inspection. Next read-only CPU review should verify L rollback/checkpoint and
preservation of prior Q evidence. No next branch or scoring authorized.


### 2026-11-15: locally verified block-0/M SANITIZED export

Verified archive pact-stage2-documented-execution-001-SANITIZED-1794745498814850054.zip
SHA2563518af207f8b541aa2abf1412282bbe96f1b5c9bae5dd4a4eddbd7bb28ef38f1,
exact unique four-member inventory and both payload checksums. Compared with
verified post-L export: delta188generations,8updates,64supervisedforwards,
96256reservedtokens,187ok/1invalid/0abstention. Cumulative1272generations,
24updates,192forwards,zero diagnostic scores,1296committedoperations,zero
unresolved,recovery_safe=true,651264reservedtokens. Cumulative1213ok/50invalid/
9abstention;420678inputtokens/57770outputtokens. No efficacy claims from format
counts. All policy operation counts remain zero; historical spending unknown.

Returned job1122786 reports block-0-M complete,0:0,9m04s. Earlier1122785 stopped
in preparation before model dispatch due an incorrect L-absence assertion in
the generated M script; corrected v2 requires M absent and preserves L. This
was a wrapper correction, not a scientific or source-plan change.

SANITIZED bundle lacks rollback/checkpoint/evaluated receipts; M private-side
CPU verification and attribution of the one new invalid completion remain
outstanding. Prior Q/L evidence should be checked unchanged. No block1, scoring
or further execution approved from this import.


### 2026-11-15: locally verified block-1/Q SANITIZED export

Verified ZIP pact-stage2-documented-execution-001-SANITIZED-1794746725152886427.zip
SHA25665533197dc770eafec91cc2be4d53c194f8fb2167447a7e051f7d90176d595a8,
exact unique four-member inventory and both payload hashes. Compared with the
verified post-M summary:188new generations,8updates,64supervisedforwards,
96256reservedoutputtokens;177ok/10invalid/1abstention. Cumulative1460generations,
32updates,256forwards,zero scores;1492committedoperations,zero unresolved,
recovery_safe=true,747520reservedtokens. Cumulative1390ok/60invalid/10abstention;
478687inputtokens/65213outputtokens. No accuracy or contribution-gain claim.
Returned job1122789 completed0:0,8m41s and reported block-1-Qcomplete.
The sanitized archive does not contain branch rollback/checkpoint/evaluated
receipts or call-level failure attribution. Next private-side CPU review must
verify those receipts and preserve prior1296events. No next branch/scoring
authorization is inferred; historical spending remainsunknown.


### 2026-11-15: locally verified block-1/L SANITIZED export

Verified pact-stage2-documented-execution-001-SANITIZED-1794748571738340144.zip
SHA2562b5451c1b3d19b66cb640c430b2bdade6ef15f477499c1adb89538dc6ab0800a,
exact unique four-member inventory and both payload checksums. Compared with
verified post-1Q summary:188newgenerations,8updates,64supervisedforwards,
96256reservedtokens;187ok/0invalid/1abstention. Cumulative1648generations,
40updates,320forwards,zero scores,1688committedoperations,zero unresolved,
recovery_safe=true,843776reservedtokens. Cumulative1577ok/60invalid/11abstention;
534387inputtokens/72999outputtokens. No accuracy/contribution-gain inference.
Returned job1122802 completed0:0,9m26s and reports block-1-Lcomplete.
The sanitized bundle lacks status/rollback/checkpoint/evaluated receipts.
Read-only private-side verification and preservation of prior1492events remain
outstanding. No next branch/scoring authorization inferred. Historical spending
and remaining historical budget remain unknown.


### 2026-11-16: locally verified block-1/M SANITIZED export

Verified SANITIZED-1794750813047174401.zip, SHA256
d9e1cee57d8ccbed0f85f796f02f7775105831f8a6b3fd45dbae8c5aad3c6820,
unique four-member inventory and both payload checksums. Compared against the
verified post-1/L bundle: 188 new generations, 8 updates, 64 supervised forwards,
96,256 reserved output tokens; 187 valid-format and one abstention, no new invalid
completions. Cumulative 1,836 generations, 48 updates, 384 training forwards,
1,884 committed operations, zero unresolved, recovery_safe=true; zero diagnostic
scores or policy work. Cumulative formats: 1,764 ok, 60 invalid, 12 abstentions.
Reserved tokens 940,032; input tokens 589,881; output tokens 80,771.
Returned job 1122816 completed 0:0 in 13m34s and reported block-1-M complete.
This sanitized archive does not verify rollback, checkpoint tensors, or unchanged
prior 1,688 events; those require the private-side CPU review. No accuracy or
contribution benefit inferred. No later execution authorized by this review.
Historical spending and remaining historical budget remain unknown.


### 2026-11-16: block-2/Q sanitized accounting verified

Locally verified SANITIZED-1794814255018159373.zip SHA256
e951b953b36dd15db8e9fbcdcb8c181f7974201a0976053d16959d361903a7ac,
unique four-member inventory and both payload checksums. Compared with verified
post-1/M summary: 188 generations, 8 updates, 64 supervised forwards, 96,256
reserved tokens added; 165 ok, 23 invalid, zero abstentions added. Cumulative
2,024 generations, 56 updates, 448 forwards, 2,080 committed operations,
zero unresolved, recovery_safe=true, no scores or policy work. Formats total
1,929 ok / 83 invalid / 12 abstentions. Reserved output tokens 1,036,288;
input tokens 645,554; output tokens 88,379.
User-returned corrected job 1123074 completed 0:0 in 9m33s. Earlier job 1123068
was rejected with PermissionError: config selected block 1/Q while approval
selected block 2/Q. Separate v2 script corrected dispatch and training-block
lookup, preserving v1 files. The new summary delta matches the one approved
branch; individual prior event preservation remains to be verified privately.
Sanitized data cannot localize the 23 invalid outputs by actor/phase, verify
rollback or checkpoint bytes, or establish contribution gains. Next is a
read-only private-side check of recovery e3ca5bee9f8a25e431b9b0877e98cbab538ab2b2b2a6a38bd818ad13e2089f2c
and preservation of prior 1,884 events. No later execution authorization inferred.
Historical spending and remaining historical budget remain unknown.


### 2026-11-16: block-2/L sanitized accounting verified

Locally verified SANITIZED-1794820696798100663.zip SHA256
e35cbd0cc900d17ce3a25543ae468eec275b74f02f57fde855e538a1635c9b77,
unique four-member inventory and both payload checksums. Compared with verified
post-2/Q summary: 188 generations, 8 updates, 64 supervised forwards and 96,256
reserved output tokens added; 186 valid-format, zero invalid and two abstentions.
Cumulative 2,212 generations, 64 updates, 512 supervised forwards, 2,276 committed
operations, zero unresolved, recovery_safe=true. No diagnostic scoring or policy
work. Cumulative formats: 2,115 ok / 83 invalid / 14 abstentions. Reserved output
tokens 1,132,544; input tokens 701,455; output tokens 96,432.
Returned job 1123132 completed 0:0 in 13m31s and reported block-2-L complete.
The sanitized export cannot verify rollback, checkpoint tensor bytes, preservation
of prior 2,080 events, or actor/phase attribution of abstentions. Those checks
remain pending private-side CPU review of recovery archive
b88622912635c484d304a0b4cd423675da7911afdf2853aae6dd763e5a6f7ce3.
No accuracy or contribution-gain inference; no later branch authorized. Historical
spending and remaining historical budget remain unknown.


### 2026-11-16: block-2/M sanitized accounting verified

Verified SANITIZED-1794823060582525297.zip SHA256
209f7dd1f79bb2792f7cdfdb36fb03fb2d390eb73fbded08d2995c73ad3b5ddd,
unique four-member inventory and both payload checksums. Against verified
post-2/L summary: 188 generations, 8 updates, 64 supervised forwards and
96,256 reserved output tokens added; 187 ok / one invalid / zero abstentions.
Cumulative: 2,400 generations, 72 updates, 576 forwards, 2,472 committed
operations; zero unresolved, recovery_safe=true, no scores or policy work.
Formats: 2,302 ok / 84 invalid / 14 abstentions. Input tokens 757,260; output
tokens 104,450; reserved output tokens 1,228,800.
Returned job 1123208 completed 0:0 in 11m24s. All nine ARC branches now reported
execution complete; latest rollback, tensor verification and preservation of
prior 2,276 events remain pending private-side CPU review. Recovery checksum:
9bfa530b37ab4bbe671a2b72a40dd62b5ce4e53d13bb3d275b618b780bdf71ce.
Sanitized data do not locate the invalid output by model/phase. No accuracy or
contribution-gain inference; no LogiQA branch or scoring authorization inferred.
Historical spending and remaining historical budget remain unknown.


### 2026-11-16: block-3/Q sanitized accounting verified

Verified SANITIZED-1794839260628771575.zip SHA256
8de0a474a2f93280828c65b977459c1f8dfa3b8b3767c4805d877e2ec70b4779,
unique four-member inventory and both payload checksums. Compared with verified
post-2/M summary: 328 generations, 8 updates, 64 supervised forwards, 167,936
reserved output tokens added; 316 valid-format / 11 invalid / one abstention.
Cumulative 2,728 generations, 80 updates, 640 forwards, 2,808 committed operations,
zero unresolved, recovery_safe=true, zero scores and no policy work. Formats
total 2,618 ok / 95 invalid / 15 abstentions. Input tokens 902,828; output tokens
120,855; reserved output tokens 1,396,736.
Returned job 1123423 completed 0:0 in 17m31s. Latest private-side review remains
pending for rollback, checkpoint bytes, prior 2,472 events and actor/phase format
attribution. Recovery archive SHA256
8626165be0adc981e17ec85c54398f5649d307628ec1fe7371e1e3ef3131c81c.
No accuracy or allocation-gain inference. No next branch authorized by this
review; historical spending and remaining historical budget remain unknown.


### 2026-11-17: block-3/L sanitized accounting verified

Locally verified SANITIZED-1794894062748675952.zip SHA256
01271b66256505453591a3a586d4494d42a28e4e14a4abe5ac8826f8a43d1b78,
unique four-member inventory and both payload checksums. Against verified
post-3/Q summary: 328 generations, 8 updates, 64 supervised forwards and 167,936
reserved output tokens added; 324 valid-format / one invalid / three abstentions.
Cumulative: 3,056 generations, 88 updates, 704 forwards, 3,144 committed operations;
zero unresolved, recovery_safe=true, no scores or policy work. Formats total
2,942 ok / 96 invalid / 18 abstentions. Input tokens 1,049,111; output tokens
136,865; reserved output tokens 1,564,672. Returned job 1123732 completed 0:0
in 22m37s. Rollback, checkpoint bytes, preservation of prior 2,808 events and
actor/phase attribution remain pending private-side CPU review of recovery
a1982a2fa027ae6cfbeb03824334d4f2c582c7b76a1c270eea2ed63d89d52572.
No accuracy or contribution-gain inference; no next branch authorized. Historical
spending and remaining historical budget remain unknown.


### 2026-11-17: completed remaining-branch batch handoff verified

Returned job 1123762 completed 0:0 in 6h03m20s, reporting all 13 remaining
branches verified. Locally verified SANITIZED-1794916858241229664.zip SHA256
b05fcacfdde6fd886eb34f5ec76126775edba5661e9ad187e17469a9da2d677b,
unique four-member inventory and both payload checksums. Against post-3/L:
4,264 generations, 104 updates, 832 training forwards; 4,176 valid-format,
73 invalid, 15 abstentions. Cumulative 7,320 generations, 192 updates, 1,536
training forwards, 7,512 committed operations, zero unresolved, recovery_safe
true; 7,118 ok / 169 invalid / 33 abstentions. Input tokens 2,946,812, output
tokens 350,972, reserved output tokens 3,747,840. Zero scores or policy work.
All 24 branches completed according to returned batch/private-side checks;
SANITIZED inspection itself does not independently re-read private checkpoints.

Next proposed scope is score only. Native scorer uses pristine R with no
adapters and no gradients to score saved packets and answer-prefix likelihood,
not to generate or update weights. Actual expected diagnostic forwards:
S0: 2*(24+40)+17+32 = 177; nine ARC branches: 9*(2*24+17)=585;
fifteen LogiQA branches: 15*(2*40+32)=1,680; total 2,442, within the frozen
2,640 ceiling. Zero new generations, training forwards or optimizer updates.
Scoring is not yet approved by the batch authorization, which explicitly
excluded it. No policy-freeze/training/evaluation authority inferred. Historical
spending remains unknown and source limitations unchanged.
