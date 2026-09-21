# Fixed 72-call prompt-control implementation

The `preparation-prompt-control` command now implements the frozen answer-only
prompt intervention. It defaults to planning; `--execute` is required for generation.
The [six Colab cells](../preparation_prompt_control_colab.md) recover the two pinned
source ZIPs and final compact exports, then run or resume the new diagnostic.
Real Qwen/L4 execution remains unverified until a returned bundle is audited.

The archived design JSON remains byte-identical, including its historical design-time
`execution_implemented=false`. The executable planner reports `execution_implemented=true`.
Its pinned config digest and 72-request digest reject recipe/selection drift. The
production offline plan reconstructs from the actual audited training and probe ZIPs;
no training-data download, new task selection, GPU call or tokenizer loading occurs.

The training ZIP supplies the completed design/reference manifest. The probe plan
and report recompute from its stored calls and must match that final reference set.
Only its 72 prepared-actor private responses become comparators. Their exact task,
agent and seed map to the new requests. The older engineering/seed-1729 baseline is
not used. Labels remain separate from message construction and request identities.

The dedicated runner requires a verified compact inference export, persists it
before inference, verifies model/runtime/template/adapter identities, tokenizes all
72 new contexts before generation, and uses the existing attempted-call journal.
The budget is 72 private calls, 18,432 reserved output tokens, 276,480 input tokens,
zero updates, zero receiver/readout/replay calls and zero teacher-forced scoring.
Completed reruns use cached calls. Changed sources/recipes, stale snapshots and
unresolved attempts stop recovery. Completed report bytes are immutable.

The answer-only arm uses the strict one-key parser; cached packet responses use
the packet parser. Packet-format outputs in the answer-only arm are malformed,
not silently repaired. Invalid/abstaining/truncated outputs remain failures.
Reports retain paired response identities, raw text, lengths/stop reasons, parser
counts, per-family/agent accuracy and complete versus missing team counts.
Nothing is exported as a PACT packet or preference pair.

Six CPU tests cover frozen configuration, request/message separation, partial
reporting, pause/resume preserving prior hashes, 72-call limits, zero-call repeats,
latest-snapshot restoration, incompatible source/recipe rejection, ambiguous
attempts, preflight overflow, strict schema/length failures, persistence failure
with retained local ZIP, plan-only CLI, and six-cell syntax/import checks.
The full-suite result is recorded under `results_import/prompt-control-implementation-001/`.
These are synthetic control-path tests, not evidence of model performance.

No historical execution code or report baseline was changed to reinterpret old
results. The new comparison explicitly binds the appropriate prepared-probe source.
The storage worker adds one distinct restore kind and retains existing kind checks.
The next step is user review/commit/push, then a newly pinned Colab checkout.

Prompt-control validation: full default suite **151 tests: 145 passed, six optional
neural skips**, 92.010 seconds. Actual archived requests reconstruct byte-for-byte
under canonical serialization; six notebook cells compile. GPU run remains pending.
