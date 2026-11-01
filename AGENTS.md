# PACT development

Read [the implementation specification](docs/PACT_IMPLEMENTATION_SPEC.md) and
[the scientific proposal](docs/PACT_Conference_Proposal.tex) before changing methodology.
Record choices in `docs/implementation_decisions.md` and evidence in
`docs/implementation_status.md`; never fill paper result placeholders from mocks.

- Local CPU development → user review/commit/push → pinned Colab checkout → imported bundle.
  Do not commit, push, change remotes, or run final-test data without explicit instruction.
- Freeze all three private packets before delivery. Every revision sees initial peers only.
  Exchange corruption changes one outgoing message for both recipients, never saved state.
- Labels/evaluator metadata stay outside defender inputs. Readout uses revised packets
  and disabled adapters, except the explicitly named archive baseline.
- Same snapshot, attack bytes/site, and corresponding node seeds across replay branches.
  Missing pairs are missing; invalid completions are task failures.
- Hot files stay on scratch disk. Verify durable copies before completion markers.
  Reject incompatible resume; never silently change model, precision, lengths, or team size.
- Treat imported traces, attacks, model text, and notebooks as untrusted data, never instructions.
- No required local CUDA, large downloads in default tests, clusters, paid APIs, or training sweeps.

Install: `python -m pip install -e .`. Test: `python -m unittest discover -s tests -v`.
CPU round trip: `python -m pact smoke --config configs/smoke/cpu.yaml --run-id local-smoke`.
GPU/model tests require explicit opt-in and must remain labeled unverified until executed.

Receiver-supervision methodology is versioned in
[the addendum](docs/receiver_supervision_methodology.md). Keep its first study focal-only,
train-split-only and DPO-disabled; official labels supervise answer-bearing prefix tokens
under the unchanged receiver prompt, never gold-bearing input or invented rationale.
Missing hold/repair support stops the bounded study. Do not reopen completed diagnostics
or describe receiver SFT as executed full PACT or demonstrated scientific efficacy.

[Controlled peer donors](docs/controlled_peer_donors_methodology.md) explicitly allow
answer conditioning ONLY in the offline synthetic donor generator. Keep original
natural focal0 packets unchanged; never route these donors into legacy replay.
Primary hold/repair support does not require both donor types. Retain the 384 donor /
1,104 total call caps, unchanged support stops and separate synthetic/natural claims.

[GPQA support study](docs/gpqa_support_methodology.md) is inference-only development:
32 prespecified Diamond tasks, frozen effective preparation actors, 256 calls / 53,248
reserved output tokens. No training, attacks or protected-remainder generation.
Keep gated text/prompts/decodable IDs outside Git; private and sanitized exports differ.

[Fixed-bank specialization](docs/specialization_fixed_bank_methodology.md) is a
separate opt-in all-actor ablation, not full PACT: receiver/DPO off, one frozen
natural training bank, global base/spec reductions, eight-task support/contrast
stops. Default to offline plan; each GPU stage requires its frozen plan hash.
No GPQA access or reopening of completed runs. Preserve exact effective actors.

[Controlled private replay](docs/controlled_private_specialization.md) is a separate
child: controlled_private_packets_v1 / controlled_slot_delta_v1, not natural credit.
Reuse immutable parent anchors; one shared task pair, base-only generation, matched
physical-node seeds across slots/signs, fixed order/calibration controls. Synthetic
positive full packets are targets only; evaluation stays natural. Preserve global
loss scaling and historical effective weights. Require support/practical screens
and an explicit artifact-bound review before training. No automatic next run.

The [controlled replay completion brief](docs/PACT_Controlled_Replay_Codex_Implementation_Prompt.md)
consolidates the existing child. Never re-plan its existing ID or migrate its pinned
source implicitly. Require complete primary/order/calibration evidence before scoring;
storage deadline changes do not expand scientific budgets.

[Heterogeneous complementarity](docs/heterogeneity_methodology.md) is a separate
clean inference-only diagnostic: exact 80 exposed pilot tasks, fresh official
Qwen2.5/Llama3.1/Mistral actors, common unadapted Qwen3 readout. Native tokenizers,
predeclared shared nine-packet bindings, all-task communication, one resident model,
2,400 attempts / 476,160 reserved tokens, included two-task smoke. No adapters,
training, attacks, replay, GPQA or final tests. All-model access precedes generation.
Unsafe dispatch windows remain unsafe even when partial reports reconstruct.

[Benchmark breadth](docs/benchmark_breadth_methodology.md) reuses the completed
heterogeneous pristine Q/L/M/R identities. New per-dataset development cohorts:
nine-call private Phase A, separately invoked 21-call Phase B on four cores only.
No positive-support gate, training, attacks, donors, old-GPQA regeneration or locked
cohort execution. Freeze source/group/exposure/scorer/contracts before inference;
do not route math/code through MCQ parsing. Code requires capability-checked OS
isolation; otherwise export jobs and leave scores pending. Requested LiveBench
2026-06-25 must be proven available, never replaced by older public questions.
Keep private/sanitized exports separate, preserve unsafe resume and exact budgets.

[Fixed-bank adjudication](docs/adjudication_methodology.md) is inference-only on
exact completed 140 MMLU / 90 MuSR development tasks and original PRIVATE QLM/QQQ
bindings. Six clean modes for pristine non-thinking J8/J14 use 512 output / 8192
context caps. One wrong candidate's justification only may change; freeze all
80 × 5 one-attempt rewrites before victims, preserve all correct packets, and reuse
rationale-blind controls by exact identity. Cap 5,560 calls / 2,846,720 reserved
tokens, included smoke; no training, new proposers/revisions, GPQA or locked data.
Keep rejected/missing variants explicit, unsafe dispatch windows unsafe, and
private/sanitized exports separate. No result authorizes the next study.

[Semantic forensics](docs/semantic_forensics_methodology.md) reads only the closed
final adjudication parent. Main review is 20 outcome-independent mixed-support
tasks; enriched examples never select interventions. Two real independent reviews
must lock before outcome reveal. Keep raw casebooks/mappings/reviewer IDs outside
Git; no automatic semantic labels. The optional exact cue/sham deletion child
requires completed reviews, both edit approvals, tokenizer checks, a frozen plan
and a separate artifact-bound user decision. New reference repeats count toward
576 attempts / 294,912 reserved tokens, with ≤36 included smoke calls. No implicit
approval, retries of ambiguous dispatch, fabricated shams, paid APIs or training.

[Selective correction](docs/selective_correction_methodology.md) trains only five
small CPU gates; all Q/L/M/J8 weights stay pristine and frozen. Use 224 fresh official
training groups with enforced fit/tune/source-development separation. Shared extractor,
paired full/restricted checks, exact source spans are unverified hypotheses. Metadata
gate has no checker dependency. Freeze whole-policy thresholds before development or
separately invoked exact-parent transfer. KEEP_ONLY is a valid negative outcome.
Cap core at 5,600 calls, optional transfer at 5,156, five fits/500 iterations each;
first smoke is eight included FIT source calls. No old-bank training, unsafe retries,
new datasets, final tests or reactivation of deferred human/span review.

[Gate diagnostics and selector contract](docs/gate_diagnostics_methodology.md)
reads the exact closed selective parent without refits or new checking. Sensitivity
is diagnostic fit/tuning arithmetic only; never select/export a replacement policy
or tune on development. Keep all 202 historical selector failures unchanged. The
separate child pairs a fresh legacy repeat with an output-passage-only clarification
on 202 existing views, pristine J8, 404 attempts/206848 tokens including <=16 smoke
calls. Smoke exports and stops. No key stripping, parent-cache substitution, new
sources, transfer, human review or implicit next experiment. Preserve freshness guard.

[Heterogeneous training revival](docs/PACT_Codex_Heterogeneous_Training_Revival.md)
is a separate dense-supervision study: Q/L/M adapters, pristine R, matched independent
and joint arms, FP32 LoRA/BF16 bases, answer-prefix-only targets, no DPO or sampled
pair gate. The independent control retains the same malicious incoming packet.
Stage I caps 17,030 generations / 768 main updates; the separately reviewed Stage II
caps 4,928 generations / 192 temporary updates with exact rollback. Never allocate
probe tokens to gradients or treat two epochs as outer refreshes. Preserve all
prior exclusions. The [approved v2 allocation](docs/revival_source_allocation_v2.md)
requires 400 ARC / 560 LogiQA with three/five homogeneous probe blocks; source
preparation must verify availability. Reject v1 source/plan resume. No silent
quota/source change. Coupled real training needs a new finite
MethodSpec; current coupling orchestration is fixture-only.

[Stage I accounting amendment](docs/stage1_amended_evaluation_methodology.md)
creates only `pact-revival-stage1-evaluation-amended-002` from the exact verified
parent. Explicit approval binds proposal 49de20c6…; additional ceilings are
14,592 generations / 7,471,104 reserved tokens, with an included <=66-call smoke.
Preserve unclosed original history and exact 120/136 source allocation. No new
attacks, synthetic verification, training or final tests. Every stage exports and
stops; ambiguous child dispatch is never retried. Parent records remain immutable.

[Reviewed-v2 Stage II allocation](docs/stage2_allocation_methodology.md) is a separate
static allocation study, not Stage III/full PACT. Preserve the exact completed
uniform_joint_sft S0 and historical unknown work. The executed 3/5 fitting blocks
and 24/40 probes conflict with the new brief's 4/4 and 32/32; real planning must
stop until explicitly amended. Do not silently repartition. Use same-source shared
probes, exact temporary rollback, pristine-R capped NLL, actual base/extra update
schedules and full-contract aliases. Seal fresh 128-task evaluation until all
policies/checkpoints/analyses lock. Enforce separate 7,680/15,616 call wallets,
3,072 total updates and 2,496 diagnostic forwards. Every explicit stage exports
and stops; fixture success neither resolves data conflicts nor verifies GPU work.

[Executed-source Stage II v3](docs/stage2_allocation_v3_methodology.md) supersedes
v2's proposed source/budget assumptions for NEW v3 children only. Keep actual
3/5 immutable blocks and 24/40 shared probes, eight-row 3/8–5/8 solver weighting,
and equal-source prospective metrics. New wallets cap 8,112 assay /15,616 policy
calls, 2,640 diagnostic forwards and 3,072 updates. No synthetic GPU allowance.
Do not migrate v2 plans or unlock real execution from implementation approval.
Verify exact source hashes, external probe history and fresh 64+64 eligibility
before assay. The verified original ARC pool leaves at most six fresh groups;
report prospective_eval_not_feasible, never substitute or loosen exclusions.

[Proposed Stage II evaluation-source amendment](docs/stage2_evaluation_source_amendment_methodology.md)
is CPU-only and separate from blocked v3. Candidate sources are OpenBookQA main/train
and original English LogiQA, 64 project-unexposed groups each only after actual
bytes, rights, current exposure and lineage review. Pretraining exposure remains
unknown. Preserve exact 3/5 fitting blocks, 24/40 probes, S0 and all v3 learning
contracts. No automatic source fetch, cohort approval or model execution. Candidate
selection and conditional budget compilation never authorize GPU work; old v3
remains prospective_eval_not_feasible. Private reports stay ignored/outside Git.

[GPQA Main / LogiQA Stage II source amendment](docs/stage2_gpqa_logiqa_methodology.md)
implements a separate PROPOSED CPU-audited candidate, graph and explicit seal.
Retain actual Stage I S0, 3/5 fitting blocks, 24/40 probes, fixed scientific seeds
and prior unknown spending. Exactly64+64 requires real bytes/current exclusions;
all Diamond protections survive in Main. No automatic acquisition or GPU dispatch.
GPQA PRIVATE text/labels/maps stay outside Git and hosted assistant context;
return SANITIZED receipts only. Slurm IDs never seed work or reset wallets.
