Update the existing PACT repository according to:

docs/PACT_Codex_GPQA_Support_Study.md

Read it in full, then inspect AGENTS.md, the latest completed controlled-receiver audit, the experiment ledger, the actual implementation and Git status. Preserve unrelated work and all completed runs.

Implement qwen3-gpqa-diamond-support-001 as one inference-only development study. Do not just produce a plan.

The question is whether GPQA-Diamond supplies natural correct/wrong diversity and whether clean communication preserves or uses it. Do not assume harder means more complementary.

Use 32 prespecified GPQA-Diamond items and the exact effective frozen-preparation arm from the latest completed controlled study. Do not use task-SFT/receiver-SFT arms or silently repair the recorded precision history. Restore real weights and verify their effective identities.

Keep non-thinking Qwen3-8B, the existing three-agent packet protocol, decoding and token caps unchanged. No training, attacks, synthetic donors, forced disagreement, alternative sampling, option-margin scoring or full PACT refreshes.

For each task:
1. Generate and freeze three independent private packets.
2. Compute independent voting and frozen synthesis from those same packets.
3. Run one clean synchronous exchange using initial peer packets only.
4. Use the same frozen base readout on the revised packets.

Complete all 32 tasks, not only those with disagreement. The hard ceiling is 256 generation calls and 53,248 reserved output tokens; there are no training or teacher-forced scoring forwards. A two-task smoke must reuse the exact requests within the 32-task plan rather than add examples or calls.

Add the official gated GPQA loader with immutable revision, deterministic shared option shuffling, correct answer mapping, label/metadata isolation, and explicit access-error handling. Never use an unreviewed mirror or expose tokens.

Mark the 32 selected tasks as development-exposed, never as training or untouched final-test data. Protect the remainder and keep raw benchmark text, prompts, continuations and decodable token arrays out of Git/public outputs. Provide private and sanitized bundles separately.

Report initial N0 counts, valid correct/wrong mixed support, individual accuracy, coverage, hold/repair opportunities, N0-to-N1 transitions, erasure/utilization/construction/readout loss and paired synthesis-versus-debate outcomes. Separate wrong-answer diversity from correct coverage. Treat 32 task IDs as the sampling units, not 256 calls. Historical ARC/LogiQA results are descriptive only.

Reuse existing checkpoint restoration, artifact accounting, resume, metrics, protocol and notebook infrastructure. Add focused CPU/mock tests, including exact budget enforcement, option mapping, privacy boundaries, adapter identity/isolation, stage matching, missingness and resume. No pretrained downloads or GPU runs locally; do not commit or push.

Deliver a real local-testable loader, runner, report/export path and thin Colab notebook with exact commands and required dataset/checkpoint prerequisites. Mark GPU behavior unverified until I return actual evidence.

No outcome automatically authorizes another run or a methodological change. Keep the completed receiver result unchanged and leave manuscript PACT placeholders unfilled.

Begin by inspecting the repository and reading the full instruction file, then implement.
