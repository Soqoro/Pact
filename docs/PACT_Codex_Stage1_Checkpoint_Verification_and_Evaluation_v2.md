# PACT — Stage I checkpoint verification and evaluation, revised implementation prompt

Prepared: 22 October 2026. Planning revision: `stage1-evaluation-review-v2`.
Status: implementation instructions and proposed evaluation staging; NOT a completed checkpoint verification or evaluation.

This document supersedes the preceding **planning prompt**, not any experiment, checkpoint, frozen scientific contract or historical result. Preserve the old prompt as history. Implement in the EXISTING PACT repository. Reuse its readers, native model backend, strict parsers, immutable journals, exposure policy, evaluator and notebooks. Do not build another framework.

## 1. Mission and authority

Verify the actual final inference weights from `pact-heterogeneous-receiver-training-continuation-003`, then implement the already specified Stage I comparison:

- `frozen_qlm`: pristine Qwen2.5-7B / Llama-3.1-8B / Mistral-7B;
- `independent_adversarial_sft`: the three completed independent-arm adapters;
- `uniform_joint_sft`: the three completed joint-arm adapters;
- the same pristine Qwen3-8B frozen readout for every team and condition.

No new training, adapter selection, changed objective, extra epochs, policy tuning, Stage II/III, original replay, new judge/gate, five-agent study, new benchmark expansion, frontier API, semantic review or span intervention. No locked final-test/confirmation access. Allocation probes remain locked.

Read AGENTS.md, Git status, the actual completed continuation/replacement audits, their frozen plans and amendments, source/model manifests, generation journals and reviewed exposure ledger before editing. Local work is implementation and CPU/mock tests. The user reviews/pushes and explicitly invokes Colab stages. Do not run local pretrained downloads/GPU work, access credentials, commit, push, change remotes or delete recovery artifacts.

### Resolve contracts rather than guessing

The authoritative execution contract is the signed/frozen manifest lineage actually used, including explicit amendments. An older design document is context, not permission to restore superseded settings. The latest audit summarizes evidence; it does not contain every source ID, weight path, parser version or seed.

Implement `contract_resolution` output that lists inherited task/split IDs, six fit/checkpoint identities, four backbones, parser/prompt/tokenizer versions, decoding, attack design, fixed-history selection, runtime policy and budget ownership. Cite the source artifact for each field. Refuse silent conflicts. Missing source artifacts must not prevent fixture-backed implementation, but block the dependent real stage.

The v2 changes below clarify planning mistakes; they do not authorize changing the trained method. Any material discrepancy between prose and an executed contract needs a conflict report, not a silently invented reconciliation.

## 2. Evidence bindings: correct the copied hash and retain uncertainty

The user-pasted completed audit identifies:

```text
run = pact-heterogeneous-receiver-training-continuation-003
plan_sha256 = bbd6decefbd9ba4808de22b31c87f02f4d19094ee1b4035383db0285000d5897
recorded_clean_source = 3e3fddf8d2fde03dd1bd903bfa7e3b4313c63fd5
amendment_sha256 = 2546efe226d2f6d80d0b13bb04930a482487ea7477a892ec821f763de618f0db
training_runtime_fingerprint = e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0
PRIVATE_sha256 = 2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959
SANITIZED_sha256 = 9a34de7cb4d5602b1fa4beeaa735ca14d9418f47fc08cdc14b4b11e2dbf72d1a
```

The previous prompt's PRIVATE digest was accidentally 63 hexadecimal characters. Use the 64-character value above and validate digest syntax before comparison. These values are **audit-reported local hashes**; the audit explicitly said an independent user-supplied outer hash was unavailable. A match binds a present archive to the reported archive, not independent proof of historical weight authenticity.

Preserve these reported facts pending reconstruction from available evidence:

- Six fits have 128 committed updates each: 477 inherited + 291 new = 768 on the amended path.
- Each fit has 2,776 recorded supervised forwards: 16,656 total; new forwards 6,319 within 6,984.
- New optimizer intents are resolved and continuation recovery is recorded safe.
- Replacement-002 physical step 94 remains UNKNOWN. The replacement-plus-continuation physical bound remains at most 769; earlier original-run work remains separate.
- This child records no new generation/evaluation. That does NOT establish that every ancestor has zero generation or that any generation budget is untouched.
- Review bundles omit final adapter/optimizer tensors. Logs and metadata do not establish their actual byte identity or reloadability.

The historical unknown step must remain visible, but it is not a blanket instruction to reject the independently approved safe descendant. Verify the descendant's actual parent/restore bindings. Do not replay step 94, count it as zero, include unknown effects in verified weights, or rewrite its safety state.

## 3. Immutable handoff and checkpoint readiness

Discover checkpoint locations only from the actual lineage/configuration and explicitly supplied or mounted checkpoint roots. No broad account search, guessed Drive paths or selection of whichever directory is named `latest`.

Create a six-row mapping of `(arm, family) -> final step-128 checkpoint -> base revision -> file manifest -> parent receipt`. Bind inherited and newly produced fits individually; some final fits may live in different ancestors/snapshots. Do not assume continuation-003 itself contains six new tensor files.

For each final inference adapter:

1. Verify config, target modules, key set, shapes, native base architecture and exact revision/tokenizer/template binding. Confirm final committed step 128/epoch 2 from the executed contract, not file modification time. No best-checkpoint selection.
2. Read actual adapter tensor bytes through trusted non-executable loading code. Validate finite values, supported tensor dtypes, exact expected keys/shapes, file and canonical tensor-content hashes. Avoid unsafe deserialization of optimizer or checkpoint-shipped code.
3. Compare against historical expected tensor hashes when present. Preserve THREE separate statuses: structural/load validity, historical hash binding, and newly recorded content fingerprint. A fresh fingerprint is not historical attestation.
4. Verify saved FP32 adapter values against their effective loaded parameter values without an unrecorded BF16 round-trip. Use the actual committed precision contract if an approved amendment exists, and disclose it; do not silently restore, improve or normalize weights. Base compute precision and adapter storage precision are separate.
5. Compare with actual initialization only when its artifact/identity is available. An adapter need not change every parameter or every test output. Do not fabricate an initialization comparison.
6. Keep optimizer/scheduler/RNG/sampler recovery readiness separate. Evaluation needs valid inference tensors and config, not deserialization or resumption of an optimizer. Missing optimizer tensors alone do not make otherwise verified inference impossible. Never delete them or claim training recovery was verified.

If historical tensor hashes are absent but loadable tensors are present, export the weaker provenance and precise lineage evidence. Do not label this `historical_tensor_verified`. A documented acceptance of that weaker binding is needed before a scientific evaluation plan can be declared ready; it must not be an automatic claim that any loadable file is the audited final checkpoint.

Missing, corrupt, nonfinite, wrong-family, wrong-step, mismatched or unbound required adapters block the full three-arm comparison. Export a blocker; do not silently substitute base/epoch-1/other-arm weights or train new ones. Completed independent verification checks remain valid partial artifacts, not a completed comparison.

## 4. Verify activation, isolation and all four backbones

Preflight includes pristine Q, L, M **and the Qwen3-8B readout**. Q also serves as the pristine attack generator. The readout and attack generator must never inherit an active trained adapter.

Use one large backbone at a time. On every actual load:

- check effective base/adapter identities, active adapter set, dtype and frozen parameters;
- set evaluation mode, disable training/dropout, use inference/no-grad behavior;
- ensure changing the active adapter did not leave parameters trainable;
- use native tokenizer/template/EOS/padding and the pinned attention/decoding stack;
- reset request KV state and per-request random state according to the inherited seed policy;
- prohibit merged-adapter contamination of the frozen control, readout or generator.

Do not assume that calling a loading function activates the intended adapter. Confirm the effective active modules and their tensor binding. Do not rely only on a printed adapter name. No automatic adapter merging or mutation of the base.

### Explicit non-generation verification allowance

This revised prompt makes the prior unspecified synthetic-forward allowance finite: at most **16 short synthetic sequence forwards in the initial checkpoint-verification stage**, batch one, at most 128 input tokens each. They are neither generation nor label-based scoring and do not enter training/evaluation metrics.

For each of Q/L/M, use the same synthetic native-template input for five states:

1. pristine base;
2. independent adapter active;
3. base restored/adapter disabled;
4. joint adapter active;
5. base restored/adapter disabled again.

Then one pristine R forward. Total: `3*5+1=16`.

Check finite logits and state isolation. Compare restored-base behavior within the same runtime using the existing reviewed numeric tolerance; if none exists, predeclare and report the tolerance before any benchmark results. Same logits on a synthetic input do not by themselves disprove a valid nonzero adapter. Verify tensor/module activation separately. No generation, gold target, benchmark item, backward pass or optimizer is used.

Log attempted/completed synthetic forwards separately. This is an explicit added verification allowance, not an extension to generation or training budgets. Later stage reloads must revalidate hashes/config/activation; they do not gain an unbounded synthetic-test loop. An exhausted/interrupted verification allowance needs an explicit recovery disposition rather than hidden extra forwards.

A short forward does not certify maximum-context memory fit. Recipient-token counts are checked for every real request. No automatic dtype, attention, quantization, context or model fallback. A recorded training fingerprint does not mean the evaluation runtime is identical: record both and follow the actual predeclared compatibility policy. A material unapproved runtime change stops execution, not silently starts another comparison.

Export the checkpoint-only receipt and STOP. All six adapters and all four pristine model roles must be ready before scientific inference starts.

## 5. Freeze the evaluation contract before benchmark outcomes

Create an evaluation-only child plan with a new immutable ID resolved against repository collisions. Link it to the full training/amendment lineage and verification receipt. Do not reset HEAD to the recorded training commit; pin the actual reviewed evaluation code separately.

Inherit exact existing task groups:

- validation: 128 = 64 ARC + 64 original English LogiQA;
- source_evaluation: 256 = 128 ARC + 128 LogiQA;
- fixed-history diagnostic: the original hash-selected 64 validation groups = 32/source.

Keep splits separate. Source evaluation is held out from this recipe's fitting, but not a final project confirmation claim. The 64 allocation probes and all other protected cohorts remain locked. No replacement/supplementary tasks.

Check exposure by identity against the original frozen plan and later events: authorized self-exposure during this study is not a reason to reject the same frozen IDs as newly ineligible, and prior unrelated exposure must not be hidden. Preserve the exposure-inventory freshness guard. If later unauthorized fitting accessed evaluation labels, report contamination rather than choosing a new split silently.

Freeze epoch-2 weights, actual task IDs, diagnostic selection, strict parser, prompts, seeds, sender/style/target allocation, runtime policy, analyses and budgets BEFORE the first smoke response. If the diagnostic subset was not actually saved, reconstruct only from the already frozen deterministic rule. Do not choose an outcome-rich subset now.

### Correct input/label boundary

Defender prompts MUST contain the trusted task text and options, and the permitted own/peer packet content. The previous wording banning task contents from prompts was wrong.

Defender inputs MUST NOT contain gold-answer annotations, correctness flags, held-out success labels, hold/repair strata, attack-style labels, privileged evaluator state or gold-bearing training prefixes. Keep TaskInput separate from EvalSpec.

Gold is used only for scoring and the already authorized OFFLINE selection of a wrong attack target. The generator can receive the designated target value, but not the gold-answer annotation or victim outcomes. The target-selection procedure is label-aware and must be described as such.

No evaluation loss training, teacher-forced answer scoring, threshold fitting or checkpoint selection is part of this phase.

## 6. Fixed attacks: complete the existing pool, not a new campaign

The instruction 'no new attacks' means no NEW ATTACK DESIGN/SEARCH. Missing, previously authorized acquisition attempts for the existing validation/source-evaluation pool may run within their original cap.

There is at most one pristine-Q generator attempt per planned task, with the inherited wrong-option target, sender, style, parser, seed and output cap. Use the exact approved plans, not new narrative templates. No access to trained responses, no query feedback, no targeting of a newly discovered weak arm, no retries after a rejected payload, no best-of-N.

Each attack is frozen before any defender arm uses that task's attacked view. All arms receive byte-identical payloads at the same sender position. The acquisition manifest is immutable even when the live private packets differ by arm.

Distinguish accepted, rejected, never-attempted, attempted-unresolved and context-incompatible statuses. Rejected attempts stay rejected. New run IDs cannot replenish them. Use existing accepted records only by exact artifact/request binding. Never re-acquire a 'better' payload or adjust it to fit a receiver.

Rejected/unavailable attacks do not become clean conditions or robust successes. Clean inference continues where valid. Dynamic recipient context incompatibility is separate from generator rejection, and must not be hidden by narrowing the attack pool per method.

## 7. Main evaluation protocol: unchanged science

At evaluation all three teams communicate normally. Honest peers are withheld ONLY in the separately specified diagnostic; the independent-SFT team's live communication is not crippled to reproduce its training inputs.

For each team/task:

1. Generate three natural private packets using that team's correct weights.
2. Freeze the three packets before delivery. Use them in both clean and exchange conditions.
3. Clean: each agent sees its saved own packet plus the other two original peer packets.
4. Exchange: overwrite the designated sender's outgoing packet identically for the two recipients. Preserve the sender's saved own packet; never deliver its replacement to itself.
5. Generate one revision per receiver per condition. No receiver sees another receiver's revised message.
6. The same pristine R sees the trusted task and the three actual revised packets only. No direct attack overlay at readout, independent anchor, checker or archive input.

Maximum `3 private + 6 revisions + 2 readouts = 11` generations per team/task.

Inherit the executed answer-first packet contract and parser exactly. Expected design is exactly two keys `answer` then `justification`, option/ABSTAIN membership, completed strict output. The actual version/hash is authoritative; do not silently tighten or relax key ordering or other rules. Model-generated malformed/abstaining/truncated responses are observed failures; do not salvage, force a choice, reprompt or substitute earlier answers. Infrastructure missingness is not a model failure.

Inherit full generation configuration, not just temperature: expected Q/L/M revisions/private sampling .7/.8/top-k20, greedy non-thinking R, 512 new-token and 8192 recipient total cap, BF16 base/SDPA, native tokens. Any authorized executed amendment must be surfaced. Compute token fit from the actual recipient's rendered prompt; never truncate source/narrative/rationale or increase caps to complete a difficult example.

Pair the original task/node seeds across arm comparisons as specified. Preserve condition/view seed rules; do not change them to obtain more cache reuse. Derive each request from stable identities, not iteration order/global RNG.

Separate logical evaluation IDs from canonical inference-request fingerprints. Reuse only when checkpoint/base/active state, native tokenized prompt, generation config, seed and required runtime dependencies match. Frozen private packets cannot serve as trained on-policy packets. Same seed alone is insufficient. New child IDs do not require regeneration of an already exact completed request, and different inputs cannot be called reuse.

## 8. Fixed-history diagnostic: the right comparison for peer use

Use the original 64 validation groups and frozen-team private histories, regardless of whether they are correct. For each of 3 families, 3 checkpoint states, and 2 conditions, evaluate:

- P: natural delivered honest peer content present;
- W: honest/unmodified peer content replaced by the original fixed withholding envelope; retain the exact corrupted incoming slot where it is delivered.

'Honest' means unmodified, NOT guaranteed correct. Never remove only wrong or only correct peers. For the corrupt sender itself there is no incoming malicious replacement; W withholds its two honest peers. Preserve exact own packet, task, target role, attack and sender across checkpoints. Same native prompt bytes within a receiver family must be identical apart from the intended P/W intervention, while checkpoint identity changes.

Use common seed bindings. The frozen-P logical cases reuse the live frozen revision evidence ONLY when the full inference request matches. Reuse is evidence linkage, not another observation. No readout is added to this diagnostic.

Logical upper bound: `64 tasks *3 receivers *3 checkpoints *2 conditions *2 access =2304`.

- 384 frozen-P results are reusable from the main frozen evaluation;
- 768 trained-P calls are new;
- 1152 W calls are new;
- additional generation cap: **1920**.

Do not silently spend 2304 NEW calls if the 384 reuse links fail. Fix a bookkeeping-only identity defect without changing actual requests, or report the contract mismatch and stop for a separate budget/method decision.

### Analysis that isolates the peer-access contrast

On the SAME frozen histories define, per family/dataset/condition and then with declared equal receiver weights:

`U_a = mean(correct(a,P) - correct(a,W))`.

Report the paired training-arm interaction:

`interaction = U_uniform_joint_sft - U_independent_adversarial_sft`.

Also report frozen comparisons and both access-condition accuracies separately. Decompose the interaction into `(joint,P - independent,P) - (joint,W - independent,W)`. It can become positive solely because joint-trained receivers get WORSE when peers are withheld; that is greater dependence, not by itself better peer-assisted performance. A useful communication-learning interpretation must examine peer-present performance, withheld performance, clean/attacked utility and the on-policy endpoints together. A positive interaction is evidence for changed behavior under this intervention on these histories, not proof of semantic truth verification or all on-policy team gains being caused by peers.

Define common HOLD/REPAIR strata using the frozen own packet and ACTUALLY DELIVERED P-view packets, then reuse those strata for the P/W comparison. Never reclassify the withheld view as having no repair opportunity and thereby remove its failures. When a correct private message is overwritten, it is not available to that receiver. Source-invalid and empty strata remain explicit.

## 9. Metrics, denominators and interpretation

Primary comparison: joint minus independent SFT in final source_evaluation correctness, separately for CLEAN and fixed EXCHANGE. Frozen comparisons are required context. Validation stays separate and does not choose a checkpoint/prompt/method or whether to report source evaluation.

Report per source plus equally weighted combined-source point estimates. Use paired task-group resampling, preserving all arms, receivers, conditions and source strata; use the already pinned analysis implementation. If no interval configuration was frozen, state a fixed configuration in the child plan before inference. Report raw paired counts alongside intervals. This is one training seed, not a population or low-risk certificate.

Required reports:

- final clean/attacked success, strict output status, paired gains/losses and joint-IAT differences;
- each model's private accuracy and team coverage, N0/N1 distributions, best-member coverage gain;
- hold/repair, harmful revision, erasure, newly correct revisions, final readout loss and final construction;
- fixed-history interaction from section 8;
- attack/input availability, tokens, generation/diagnostic forwards, runtime/loading/memory and reuse.

On-policy HOLD/REPAIR opportunities depend on each trained team's own outputs. Those populations can differ across arms; do not interpret a higher conditional rate alone as a controlled training benefit. Report their support explicitly and use the common-history diagnostic for matched receiver comparisons.

HOLD-conflict requires a correct own initial answer and an actually delivered valid wrong peer. REPAIR-available requires an incorrect/unavailable own answer and an actually delivered valid correct peer, with source-invalid own cases broken out. A correct label does not certify its rationale. Source/candidate validity and attack availability must remain distinct.

Before scoring, show all intended task IDs/counts, accepted/rejected attack IDs and executed/complete masks. Model failures stay in denominators. Infrastructure-unavailable outputs stay missing, not fabricated failures/successes. Report incomplete status and bounds. For paired attacked effects use the same method-independent accepted pool and matched available records; disclose any incomplete intersection and its selection risk. Also report full-planned-population missingness bounds; do not hide exclusions under an unconditional-accuracy label.

Check counts directly from joint task records, including:

`#final_correct = #final_correct_with_initial_coverage + #final_correct_without_initial_coverage`.

Readout loss is `#(revised_correct_available AND final_wrong)`, not coverage minus final accuracy. A synthesizer can construct an answer absent from peer answers. Conversely, successful final correctness with a correct peer present does not establish causal copying or valid peer rationale.

No generative KEEP fallback, post-hoc parser rescue, model ranking from training losses, adaptive robustness claim, full-PACT claim or promotion to Stage II based on this phase alone.

## 10. Budget: inherited limits, not a new wallet

The original Stage I generation design had 17030 attempts maximum. Its evaluation components are:

| Component | Maximum generations | Reserved output at 512 |
|---|---:|---:|
| 128 validation groups *3 teams *11 | 4224 | 2162688 |
| 256 source-evaluation groups *3 teams *11 | 8448 | 4325376 |
| fixed-history additional | 1920 | 983040 |
| originally planned validation/eval attack attempts | 384 | 196608 |
| nominal evaluation components before reuse/previous spending | **14976** | **7667712** |

These are NOT automatically the remaining allowance. Continuation-003 has no new generations, but ancestors may have completed/spent/ambiguous attempts. Build a reconciled ledger by canonical component, logical request and physical attempt:

- identify which frozen plan/amendment owns each cap;
- distinguish inherited evidence, actual attempts, committed results, rejected outputs, unresolved attempts, reuse and unattempted requests;
- deduplicate export copies, not distinct physical work;
- preserve original-run/replacement/continuation histories separately and the training-step uncertainty;
- never charge optimizer forwards as generations or treat 291 new updates as model-generation consumption;
- never reset budgets because a new child/run ID exists;
- never transfer unused fit/scratch/rejected-attack allowance to evaluation;
- preserve and reserve ambiguous generation attempts without blind replay.

If amended generation-budget ownership cannot be reconstructed, export a budget blocker. Do not infer it by subtracting a single aggregate from 17030 or declare an unknown attempt did not happen.

Maximum initial evaluation smoke: one original validation group per source, all three arms/conditions =66 live calls; at most two previously unattempted planned attacks =2. Thus at most68 attempts /34816 reserved output tokens, INCLUDED in the above component limits. Accepted/rejected existing attacks and exact completed requests are reused, not retried. Smoke selection is fixed independently of outcomes.

The 16 synthetic forward checks in section 4 have their own explicitly bounded non-generation ledger. New optimizer steps=0, training forwards=0, label-conditioned teacher-forced scoring forwards=0. Do not add benchmark forward probes or an unbudgeted 'canary generation'. Input tokens, repeated loads and CPU work are measured separately.

## 11. Stages and stopping rules

Implement all stages now using mocks; actual user-invoked Colab stages:

1. **Offline inspect/resolve:** contracts, lineage, path inputs, safety and remaining-budget report. No model downloads.
2. **Checkpoint verification:** actual read-only tensor inventory/loading and bounded synthetic checks; export/STOP. No benchmark responses.
3. **Freeze child evaluation plan:** bind verified bytes and all evaluation settings/analysis before outputs.
4. **Two-task validation-prefix smoke:** original requests/IDs reused by later stages; export/STOP.
5. **Complete validation:** all128 tasks, including smoke by reuse; export/STOP.
6. **Complete source_evaluation:** all256 tasks with frozen settings; export/STOP.
7. **Fixed-history diagnostic:** separately invoke the original64-task diagnostic; export/STOP.
8. **Local read-only audit:** trusted reconstruction of actual raw records and summaries, with no code execution from bundles.

If the original already froze a different harmless scheduling order, preserve it with documented dependencies. Do not create outcome-based optional stopping. A low, zero or negative score does not authorize prompt/weight/runtime/task changes or suppression of remaining prespecified outputs.

Hard technical failures include checkpoint/identity mismatch, incorrect active state, source corruption, token incompatibility, unresolved dispatch, budget exhaustion, actual protocol/rendering defect or unapproved runtime change. Stop the affected stage and retain partial evidence. A syntactically malformed response under a faithfully implemented frozen prompt is normally an observed model outcome, not permission to fix the prompt and overwrite the run. A genuinely defective contract requires a prospective amendment and separately labelled result, preserving all previous outputs.

All six checkpoints are a readiness condition for the declared full comparison. Do not publish an incomplete set of arms as that completed comparison. Avoid broad deletion or pruning of Drive/RECOVERY snapshots at every stage.

## 12. Required implementation tests

Run actual CPU/mock tests; optionally locally initialized tiny neural fixtures. No pretrained local downloads. Required coverage:

1. Digest syntax rejects the earlier 63-character PRIVATE value; correct audit binding parses; bundle hashes and historical weight-hash assurance are different fields.
2. Read actual six-checkpoint ancestry, inherited fits, final step and known/unknown work; no modification of parent receipts.
3. Missing/corrupt/nonfinite/wrong-family/wrong-step adapters rejected; missing optimizer recovery does not falsely invalidate an otherwise ready serving model.
4. Actual loaded parameter identity/FP32 values, eval/dropout/no-grad, active-adapter selection, base restoration, pristine attack Q and pristine R isolation.
5. Synthetic probe accounting <=16 sequence forwards, no generate/backward/benchmark label or output scoring.
6. Native templates/EOS/token caps and gold-safe rendering: task/options present, evaluator fields absent. No unauthorized targets in user text.
7. Main trained teams generate their OWN private histories and communicate normally; fixed-history diagnostic alone shares frozen histories.
8. One-sender corruption reaches both other recipients identically, not the sender; synchronous revisions; R receives actual revised packets only.
9. Exactly shared fixed attack pool; originally missing acquisition vs rejected vs unresolved; no conditional retry, pool substitution or adversarial adaptation.
10. Strict parser failures versus infrastructure missingness; no previous-answer fallback; intended and complete counts/bounds.
11. Seed/content/checkpoint/runtime-aware canonical reuse; fixed-history384 reuse and additional1920 counts; prompt changes cannot masquerade as reuse.
12. Frozen common strata and training-arm-by-peer-access interaction; on-policy opportunity masks differ and are not used as if matched.
13. Per-component budget and amended lineage ownership, shared smoke, correct14976 nominal arithmetic, no extra wallet or double counting.
14. Technical smoke gates versus scientific outcomes; no checkpoint selection or performance-conditioned changes after validation.
15. Private/sanitized export integrity, escaping untrusted texts, exposure self-event versus contamination distinction, complete mock verification -> smoke -> validation -> evaluation -> diagnostic -> audit.
16. Real CLI/notebook entrypoints and relevant legacy regression tests; report actual passes/failures/skips, not old totals.

## 13. Deliverables and Codex handoff

Use repository-native filenames/commands; implement missing capabilities and document their ACTUAL syntax. Proposed artifact responsibilities:

```text
contract_resolution.json
training_lineage_map.json
checkpoint_inventory.private.json
checkpoint_verification_receipt.json
inference_identity_manifest.json
reconciled_generation_budget.json
frozen_stage1_evaluation_plan.json
source_and_attack_availability.json
live_per_task.private.jsonl
fixed_history_per_receiver.private.jsonl
paired_metrics.json / peer_access_interaction.json
runtime_and_cost_report.json
PRIVATE and SANITIZED handoff bundles
CODEX_HANDOFF.md
```

Keep raw tasks, answers, tokens, tensor bytes and private paths outside tracked/public artifacts. A sanitized numerical summary is not a replacement for private audit traces. No checkpoint deletion. No misleading recovered-safe flag for an unresolved ancestor.

Finish with changed files, the concrete issues found, actual CPU tests, contract conflicts/prerequisites, verified versus unverified statuses, exact checkpoint/smoke/validation/evaluation/diagnostic commands, full and remaining component budgets, expected bundles and what the user must provide or invoke. Do not claim that actual Drive tensors were verified unless that stage really ran.

No new scientific result follows merely from implementing this prompt. The purpose is to measure whether the already trained joint receivers outperform the already trained independent controls on matched clean and attacked tasks and on common-history peer-use behavior.

### Technical references (contracts, not permission to upgrade)

Use the repository's pinned library versions. Official PEFT documentation distinguishes adapter tensors/config from the base model, and distinguishes loading an adapter from setting it active. It also documents dtype behavior. Consult the matching version of:

- `https://huggingface.co/docs/peft/developer_guides/checkpoint`
- `https://huggingface.co/docs/peft/package_reference/peft_model`

Do not copy current API arguments into an older pinned environment without checking compatibility.

BEGIN with source/contract inspection and CPU implementation. No real GPU stage starts automatically.
