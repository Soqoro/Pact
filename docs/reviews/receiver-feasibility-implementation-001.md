# Receiver-feasibility implementation — 2026-09-20

The receiver-only runner and fresh-runtime Colab guide are implemented. The full
suite passes **113/113 tests** with CPU neural checks enabled; the default suite
passes **107 with six optional skips**. This is implementation evidence, not a new
Qwen3 experiment result. No pretrained model download, GPU execution, optimizer
update or final-test access occurred.

The frozen design is unchanged: 24 official training tasks, 12 per family, all
excluded from the 12-task warm start; 48 clean/exchange records; four fresh samples
per eligible original receiver prompt. Maximum cost remains **912 generation calls
and 224,256 output tokens**. The main revision does not become a fifth candidate.
No private alternatives, suffix replay, teacher-forced scoring or training-pair
export is added. The recipe and selection hashes remain respectively
`efa9d8cfb1450227b80286309505116d9a8e03fd1732d99d1ee6b5bcabf3d7e1` and
`e6842155a4080c0a39e3ad39a8b207539312ffb57b05da7675a7343136e33d96`.

The `receiver-feasibility` command defaults to plan-only and requires `--execute`
for collection. It verifies source, data, selection, frozen references and runtime;
then uses the existing synchronous three-agent protocol and disabled-adapter base
readout. Labels remain outside defender prompts. Each logical call has a durable
scratch intent and immutable checksummed result containing actual prompt and
completion tokens. Resume reconstructs trajectories from those results and draws
only missing candidates. Completed repeated invocations make zero new calls.

Reports retain all contexts, candidate outcomes and missing classes, with separate
hold/repair denominators, task/family/agent coverage and clean/exchange main-task
results. A partial pool cannot produce a pair, and an incomplete run cannot pass
the coverage gate or conclude pair absence. The gate remains at least six pairs,
three tasks and both families separately per stratum. Passing it only supports
reviewing a separately bounded reference-scoring check; `full_pact_ready` remains
false for every outcome.

Recovery deliberately protects the fixed sampling budget. Before a task's fresh
calls, the runner verifies a durable snapshot marked unsafe for post-reset resume.
After both conditions finish, or a handled call-boundary pause, it publishes a
safe snapshot. Restore accepts only the latest safe snapshot. It rejects an older
snapshot or an unresolved call intent because previously consumed generation
budget cannot be inferred after those calls are lost. An abrupt runtime loss
inside a task may therefore require an explicit recovery-budget review instead
of an automatic retry. Intact scratch can resume verified calls normally.

Local review ZIP creation precedes final timed Drive operations. A persistence
timeout preserves the local archive; it does not establish a verified Drive copy.
Receipts distinguish local completion, verified snapshot and persisted bundle.
The bounded archive reader allows the declared call inventory and checks hashes,
member paths and size limits. Review ZIPs contain diagnostic data, not weights.

Ten new tests exercise partial-pool resume, immutable completed work, exact
prompts/seeds, frozen private-packet delivery, base readout, call/token budgets,
zero-eligible and invalid pools, coverage decisions, runtime/source mismatch,
unresolved calls, failed storage, stale/unsafe snapshot rejection and verified
restore/handoff. The synthetic runner fixtures use four tasks to keep CPU storage
tests small; separate planner checks verify all 24 production selections. The
optional tiny Qwen/PEFT CPU test runs the real generation backend and confirms
unchanged actor/reference tensors, restored adapter state after base readout and
zero reference-scoring forwards. It uses locally initialized weights only.

Evidence is retained under
`results_import/receiver-feasibility-implementation-001/`: actual offline plan,
targeted and full-suite logs, environment/source identity, compiled-guide checks
and a verification record with evidence hashes. The default suite took 35.565
seconds; the CPU neural suite took 39.985 seconds. These timings describe local
tests, not an estimate of Colab experiment duration. The guide's six Python blocks
compile locally; Google Drive and GPU cells have not been executed here.
The tested uncommitted executable source hash is
`57e1b6bf2a469e15bb7dcafde8f22126fb454c660b661ae9107eda8f2602a964`,
based on Git HEAD `80992b48f9159c427d65e87cbd80849af295021b`.

Remaining verification: real Qwen3 receiver collection, GPU memory behavior,
GPU interruption/continuation and actual post-reset Drive restoration for this
new path. The completed warm-start, bank and base-control runs do not verify those
new execution paths. Review/commit/push this implementation, then follow the
[ordered Colab cells](../receiver_feasibility_colab.md) pinned to the new full SHA.
Return the ZIP and checksum for independent review before selecting another stage.
