# Preparation objective review and next bounded diagnostic

The larger clean-answer preparation did not improve the matched development probes.
Before changing the objective, test its known prompt mismatch with one fixed 72-call
control. The separate runner is now implemented and CPU-tested; GPU execution remains
unverified. This does not expand any completed run. [Frozen settings](../experiments/preparation_prompt_control.json).

## Corrected evidence

The original imported private report compares new seed-1730 outputs to the old
seed-1729 trajectory, yielding 46/72 versus 45/72. That is not the matched-seed
comparison specified in the preparation design. Rejoining the completed seed-1730
private-control ZIP to the new private records by task and agent, and verifying seed,
message bytes and token prefixes, gives **45/72 versus 45/72**: 45 correct-to-correct,
27 wrong-to-wrong, 71 identical answers and one wrong-to-different-wrong answer.
Both checkpoints have 15 all-correct teams, nine all-wrong teams and zero potential
clean-repair contexts. Receiver correctness is also unchanged, with no eligible pairs.
Do not interpret the previous cross-seed one-answer drop as a preparation effect.
Preserve imported reports; corrected comparisons must explicitly name both sources.

Offline evidence and reproducible audit/planner:
`results_import/preparation-objective-review-001/audit_and_plan.py`,
`matched_seed_comparison.json`, `plan.json`. The separate earlier archive audit still
verifies the archived report as written; it does not make its baseline seed-matched.

## What the objective did and did not train

The executed loss is mean completion-token NLL on canonical answer-only JSON plus
EOS, under `warmstart_prompt`. Every agent sees the same 120 labeled tasks once;
initialization seeds and orders differ. It contains no specialization responsibilities,
continuation-credit term, receiver-context examples or hold/repair preference loss.
The private and revision inference prompts instead request answer-and-justification
packets. Therefore scaling that loss does not directly teach packet production or
when to revise, and different optimization seeds alone need not produce complementary
correctness. These are objective properties, not a demonstrated cause of the null result.

The proposal requires uniform supervision plus additional *positive* specialization
and same-context hold/repair preferences. Missing pairs remain missing. Forcing wrong
answers, rewarding disagreement, pairing across prompts/checkpoints, or manufacturing
rationales would change the method and is not a valid remedy. The supervised fallback
is permitted, but receiver-context supervision and packet-target construction need
separately justified data and controls; they have not been tested by this warm start.

## Frozen question and intervention

Run ID: `qwen3-preparation-prompt-control-001`.

Question: do the completed 120-task adapters answer the same 24 training-development
tasks differently when prompted in the exact answer-only format they were trained on?
Keep the final 90-update adapters, model, tokenizer, precision, runtime, agent identity,
node seeds, sampling settings and tasks fixed. Change only the message construction
from the stored private packet prompt to `warmstart_prompt(task)`. Reuse the completed
72 prepared private outputs as the comparator; generate only the answer-only arm.
No optimizer update or receiver generation is included.

This is a prompt/response-contract intervention: the system instructions and serialized
user message differ together. It does not separately identify justification burden,
format, instruction wording or rationale quality, and cannot prove causality for the
training outcome. It also cannot diagnose receiver learning or establish generalization.

Freeze all 24 tasks (12 per family) and three actors before execution; no task selection
based on correctness. They are excluded from the 120 optimized tasks but are repeatedly
inspected training-split development probes. Every request inherits its exact recorded
seed, not a new seed search. The request inventory hash is
`69059c28cc3f9ab6558124c65c250814cc1e864c392ae816b67fef5857c9ad63`.
Labels remain separate evaluator metadata. Only the allowed task and instruction text
enter prompt construction. Answer-only completions never become full PACT packets,
replay alternatives, rationale targets or preference pairs.

## Budget and execution contract

- Exactly one arm: at most 72 new generations, 24 tasks × three agents.
- Temperature 0.7, top-p 0.8, top-k 20; thinking disabled; 256 output tokens and
  4,096 total tokens. Reserve at most 18,432 output and 276,480 input tokens.
- Zero training steps, teacher-forced scoring, new attacks, donors, receiver calls,
  readouts, suffix replays or preference exports. No additional checkpoint or seed.
- Pin the training and completed probe ZIP checksums in the settings file. Verify
  the final three adapter bytes from the compact inference snapshot before loading;
  review metadata alone is insufficient. Original optimizer history is unnecessary.
- Require the same recorded runtime/base/tokenizer/template and decoding settings.
  Preflight all prompts and token lengths before generation; stop on overflow or
  incompatible identities, without shortening messages or changing precision.
- Record attempted calls before execution, preserve cached results and an unsafe
  durable marker before new calls, and restore only the latest verified safe snapshot.
  An unresolved intent stops recovery; it never authorizes a replacement call.
- Write the local review ZIP before bounded Drive writes. Verify durable copies
  before marking completion. Report failures and missing records without extra draws.

The runner uses a distinct `preparation-prompt-control` command/run identity. Do not reuse the completed
104-call runner with altered prompts. CPU validation must check label separation,
fixed request reconstruction, checkpoint-sensitive identities, exact cached comparator
joins, invalid/missing outcomes, and interruption/resume accounting. Use the [six Colab cells](preparation_prompt_control_colab.md) after reviewing and
publishing the implementation.

## Report and decision rules

Compare strict parsed correctness for all 72 task-agent pairs; invalid, abstaining or
truncated completions are failures. Also report exact answer-only schema compliance,
raw outputs, lengths, stop reasons, correctness transitions, per-agent/family accuracy,
and all-correct/mixed/all-wrong teams. State denominators and missingness explicitly;
72 responses are clustered within 24 tasks, not 72 independent task observations.
Any packet arm format assessment must respect its own packet contract.

- Better answer-only correctness: prompt sensitivity on this slice. Consider a
  separate matched-format training design; do not switch the main protocol to
  answer-only packets or claim the mechanism is proven.
- Similar correctness: no observed benefit from the trained prompt on this slice.
  Close the diagnostic; do not automatically add tasks, seeds or temperatures.
- Worse correctness or more invalid outputs: report the degradation and close it.
- Incomplete/identity mismatch: engineering failure; no scientific comparison.

No outcome unlocks PACT training. Genuine replay support, both hold and repair strata,
useful private coverage and downstream terminal benefit remain unresolved. Choosing a
new objective requires a separate bounded design after this control, not a larger
warm-start sweep. Final-test data and manuscript placeholders remain untouched.
