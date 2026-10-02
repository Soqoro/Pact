Update my EXISTING PACT repository according to:

docs/PACT_Codex_Heterogeneous_Complementarity_Phase.md

Read that document in full. Then inspect AGENTS.md, Git status, the 30 September
project review, experiment ledger, existing model backend, original 80-task pilot
manifest, protocol, and reporting/recovery code. Preserve unrelated work.

This is a request to IMPLEMENT the new phase, not merely write another plan.
Reuse existing components and complete any parts already started.

## Scientific scope

Implement pact-heterogeneous-complementarity-001 as a clean, inference-only
natural-complementarity diagnostic. It compares:
- Qwen + Llama + Mistral.
- Three independent Qwen samples.
- Three independent Llama samples.
- Three independent Mistral samples.

Official proposed constituent checkpoints:
- Qwen/Qwen2.5-7B-Instruct
- meta-llama/Llama-3.1-8B-Instruct
- mistralai/Mistral-7B-Instruct-v0.3

Use the existing pinned unadapted Qwen3-8B as the COMMON readout, with no adapters.
Resolve immutable official revisions and each model's native tokenizer/template.
These are fresh frozen checkpoints, not the old prepared PACT adapters.

The goal is to measure correct coverage beyond the best member and the effect of
communication. It is NOT to force disagreement or claim that heterogeneity or
model size guarantees complementarity. This is an adapted diagnostic, not an
exact reproduction of the cited diversity paper.

No training, attacks, synthetic donors, private replay, extra sample sweeps,
new loss, thinking-mode experiment, GPQA access, or final-test evaluation.
Preserve every completed/stopped/incomplete earlier run and its safety status.

## Population and comparisons

Reuse ALL 80 original validation-pilot tasks: 40 ARC-Challenge and 40 original
English LogiQA. Restore exact IDs, inputs, source revisions, and option mappings.
They remain development-exposed, not untouched tests or training examples.
Do not select tasks based on previous answers or replace missing source records.

Per task, generate three private samples from each family: nine calls total.
Freeze all private packets before that task's revisions.

Build QQQ, LLL, MMM and QLM using the precise shared-packet bindings in the full
specification. The mixed team uses one predetermined sample from each family;
there is no best-of-nine selection. Balance family-to-anonymous-slot mapping
before any model outcomes. Do not disclose model names or expertise in prompts.

For all four teams, compute independent voting, independent frozen synthesis,
one synchronous revision per member, and the same frozen readout on revisions.
Also run one task-only readout baseline per task.

Complete communication on ALL tasks, even when mixed support is zero. There is
no positive-diversity gate that stops the inference study before its outputs.

## Colab implementation

Extend the model registry/backend for native family-specific chat templates,
EOS/end-of-turn IDs, tokenizer identities, and exact request/caching keys.
Do not use the Qwen tokenizer or chat format for Llama/Mistral.

Retain common semantic task/packet instructions, private/revision temperature
0.7, top-p 0.8, top-k 20, and 256 output-token caps. Readouts are greedy with
64-token caps. Check the 4096-token total limit using the RECIPIENT tokenizer.
BF16/SDPA is the requested preset; no silent quantization, offload or fallback.

Use ONE GPU-resident model at a time. Batch the work by model and stage:
private Q/L/M, revisions Q/L/M, then the common readout. Save text between stages.
Do not load/unload all models per question or require simultaneous host residency.

Verify access to ALL models before benchmark inference. Llama authorization
must come from me; do not accept terms, expose tokens, or substitute a mirror/model.
Downloads and real generation happen only in my explicitly invoked Colab session.

The exact ceiling is 2400 generation attempts / 476160 reserved output tokens:
720 private, 960 revisions, 640 synthesis, 80 readout-only.
Zero optimizer or teacher-forced scoring steps.
An optional first-two-task smoke is at most 60 calls INCLUDED in this plan and
must be reused. Failed/ambiguous attempts count; resume never resets the budget.
Default notebook execution is plan/preflight, not an automatic large run.

## Reports and acceptance

Report individual accuracy by FAMILY, N0 counts, correct coverage, joint failure,
coverage gain over best member, unique coverage and pairwise rescue, valid mixed
support separately from wrong-answer disagreement, N0->N1 transitions, hold/repair,
erasure/utilization/construction/readout loss, and paired protocol outcomes.

Compare QLM with EACH homogeneous team, not only their mean or a weak reference.
The readout may construct answers missing from all peers; do not call every final
gain evidence of complementary private knowledge. Use 80 task groups as the
sampling units, clustering all models/replicas/teams. Unknown/boundary estimates
remain qualified. Natural costs and cross-tokenizer/FLOP differences are explicit.

Reuse trusted artifact validation, immutable journals, bounded persistence,
model-major resume, and raw versus shareable reports. Unknown dispatches remain
unknown; do not turn reconstructed partial metrics into a recovery-safe flag.

Run CPU/mock tests and optional tiny locally initialized neural tests locally.
No pretrained downloads, GPU jobs, commits or pushes here. Implement real CLI and
thin notebook paths, a complete four-team mock round trip, focused regression
tests, reporting/export, and exact Colab commands with required access/data paths.

Finish with changed files, actual test results, example model/template/team
bindings, exact budgets and invocations, expected handoff artifacts, and what is
GPU-unverified. Do not claim natural complementarity or PACT success in advance.

Begin by reading the full specification and inspecting the repository, then
implement the smallest complete runnable path.
