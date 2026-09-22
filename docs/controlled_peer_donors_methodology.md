# controlled_peer_donors_v1 — implementation addendum

This implements the explicit [22 September controlled-donor update](PACT_Codex_Controlled_Peer_Donors_Update.md).
Source variant `controlled_peer_donors_v1` feeds objective `receiver_supervision_v1`
and target `receiver_answer_ce_v1`. No real donor generation, receiver training,
or new efficacy result is established by this implementation.

## Authorized intervention

Only the OFFLINE generator may be instructed to support a selected option. This
supersedes the previous answer-forcing prohibition solely for this synthetic source.
It does not authorize forcing deployed actors, replacing the focal own state, or
putting synthetic donors into the private replay/responsibility estimator. The
original proposal, source recipe, losses and completed reports remain reproducible.

The pinned parent ZIP is checked with the existing safe reader. Its plan is rebuilt
from the original pool/preparation/selection; all 672 journal links, prompts, seeds,
parses and recorded decoding are checked without inference. Child acquisition uses
only the ORIGINAL three private packets, and always focal agent0. Four parent focal
alternatives remain imported historical evidence and never supply an own state.
The 64/32 groups are unchanged. This is inspected development-held-out training
material, not pristine validation or final-test evidence.

Wrong targets use `random.Random(node_seed(seed, source_variant, task_id,
"wrong-target")).choice(sorted(incorrect_options))`; sender slots use the independent
`sender` namespace and choose 1 or 2. Neither depends on own correctness, donor
success, task reindexing or receiver outputs. Realized sender balance is reported;
there is no reassignment after outcomes. An invalid own packet is unsupported.
For the other unchanged peer, `ok` or an explicit `abstention` is supported;
malformed/invalid/truncated bytes are never silently repaired. The original packet
in the replaced slot remains intact in history and provenance, regardless of its
parse status.

Both target types share one exact template, base model and sampled decoding
(.7/.8/20), two fixed seeds, 256-token output and 4,096 combined context limit.
`DonorBackend` loads the pinned unadapted backbone, uses existing adapter isolation,
and additionally restores incoming mode/gradient flags even on exception. Model,
tokenizer/template, precision, attention and runtime identities must match the parent.
There are no learner adapters resident in this dedicated acquisition process.

Every dispatched attempt has an immutable intent before generation. First accepted
wins; rejected outputs are retained without rewriting. The narrow versioned
validator separates parsing, target match, bounded nonempty explanation, explicit
construction disclosures and privileged-role delimiters. Ordinary assertions such
as “option B is correct” are permitted. Acceptance means structural validity and
answer match, **not verified reasoning**. Rationale review is `not_reviewed`; the
bundle includes up to sixteen deterministically stratified accepted examples and
sixteen rejection examples, with exact task inputs and provenance. A systematic
content defect requires stopping and a new version, not changing this run's prompt.

The receiver sees the unchanged normal revision prompt: trusted task, byte-identical
original own packet, unchanged other peer and one replacement in its original source
envelope/order. It does not receive target kind, generator instructions, correctness
metadata or stratum labels. Donor content is explicitly label-conditioned intervention
data, not wholly label-free or a naturally occurring trajectory. Distinct donor
contexts have different hashes and cannot be a same-prompt DPO pair.

## Support and unchanged learning

Correct original own + wrong donor gives primary hold; wrong original own + correct
donor gives primary repair. Opposite donor failure does NOT disqualify a valid primary.
Both target acquisitions are attempted independently. Count original task groups;
keep minima eight fit/four held-out per stratum and caps 32/16 per stratum. Selection
uses a frozen group-hash ordering, never downstream outcomes. Unsupported sources,
rejections, pre-cap yields, selected support and missing opposite controls are explicit.
Insufficient support exports evidence; optimizer/evaluation stages refuse execution.

Loss routing is unchanged: `L_rx + 0.1 L_clean_anchor` or the matched task-only
`L_task + 0.1 L_clean_anchor`. Hold and repair each receive half the task-averaged
primary loss. There is no duplicate receiver base loss, rationale target, new DPO
sampling or reference-score gate. Both trained arms have identical labels, record
multiplicities, clean anchors and frozen schedules, independent fresh optimizers,
and identical original preparation bytes. Only focal agent0 changes. Microbatch one,
effective batch four, LR 1e-5, at most two passes/32 updates per trained arm.

The genuine packet prefix is `{"answer":"B"`, without closing the object or EOS.
Only tokens overlapping answer characters are scored, with merged delimiter offsets
recorded. The donor explanation is input, never a supervised rationale. The exact
[synthetic example](../tests/fixtures/controlled_peer_donors_v1.json) retains BOTH
generator requests and full receiver prompts plus token IDs/masks. Its own packet
is identically `{"answer":"A","justification":"I counted three."}` in both contexts.
Using the explicitly non-Qwen character tokenizer, B has token ID 67; the only scored
positions are 809 (correct donor) and 829 (wrong donor), zero-based. Every other
position is masked. Real tokenizer masks are frozen before training in Colab.

## Matched evaluation and recovery

Three arms generate full normal packets on available correct/wrong donor contexts
and peer-withheld contexts (both peers removed, same own/task). Seeds are task-based
and matched across versions and arms; checkpoint-specific caches reject mismatches.
Primary support and both-donor paired denominators are separate. Report hold harm,
repair, agreement/misleading behavior, parser failures, paired transitions and CE
separately. Answer correctness is a proxy, not certified reasoning or proof a
particular justification caused the answer. Removing peers changes context length;
it is not a perfect linguistic-factor isolation.

Natural private evaluation uses all 32 diagnostic tasks. Natural-team smoke uses an
outcome-independent eight-task slice from those 32, regardless of donor acceptance,
with unchanged clean/exchange fixed-pool attacks and node seeds. It generates fresh
private states; it never imports conditioned donors. The updated focal adapter serves
both its turns, other actors stay fixed and the final readout disables adapters.
Original terminal/individual/coverage/erasure/readout metrics retain denominators.
Compare receiver SFT with BOTH task-only SFT and peer-withheld outcomes before
attributing anything to communication learning. One seed/eight team tasks are not
powered efficacy evidence.

Worst-case acquisition 384, controlled receiver 288, private 96, natural-team 336:
**1,104 new calls / 273,408 reserved output tokens**. Imported parent calls consume
zero new budget. Training adds at most 64 combined updates/512 primary+anchor
forward/backward calls; diagnostic answer CE at most 288 separate forwards. Actual
input tokens and persistence costs are separate; compute units remain null.

The existing scratch-first shard, full optimizer/RNG checkpoint, safe-snapshot and
bounded persistence machinery is reused. The acquisition ID identifies `RUN/donors`
inside the new consumer study; one atomic recovery namespace avoids duplicating
or resetting its budget. Unknown dispatched attempts block automatic regeneration.
Latest unsafe snapshots cannot roll back to older safe ones. Compact original
preparation exports only initialize fresh jobs; they cannot resume new optimizers.
Local review ZIPs precede durable copying and omit tensors, with inventories and
full-snapshot paths. See [ordered Colab cells](controlled_peer_donors_colab.md).

Full PACT integration, joint refreshes, enabled DPO here, natural complementarity,
reasoning validation, broader robustness and final-test conclusions remain deferred
or unestablished. No historical result becomes a controlled-donor result retroactively.

Local parent preflight identifies 92 eligible original source states: fitting
correct/wrong 31/31, development-held-out 20/10. Four unsupported original states
remain in the frozen manifest. These counts establish only potential support before
donor acquisition, not accepted donor yield or a successful learning study.

## Audited execution deviation: controlled-001, 2026-09-23

The first returned training run used a loader that preserved focal FP32 values but
rounded nonfocal FP32 adapters through BF16. Thus the intended original-export
identity was not realized numerically for agents1/2. The explicitly scoped
[evaluation recovery](controlled_peer_donors_recovery.md) instead certifies identical
**effective** initialization and unchanged effective nonfocal tensors across arms.
It preserves all saved weights and original records, records the deviation, and
checks actual resident tensors. This does not retroactively establish preservation
of original FP32 nonfocal values, or any learning benefit.
