# Documented-development Stage II execution adapter

Status: implemented for CPU review; **no physical spending approved or performed**.
This is a separate adapter for `pact-stage2-documented-exclusions-amendment-001`.
Its proposed execution owner is `pact-stage2-documented-execution-001`.
It does not unblock or modify the historical v3 validator, reset a historical
wallet, or assert that the missing historical interval consumed zero work.

## Evidence boundary

The exact 64 GPQA Main + 64 original English LogiQA cohort and request graph were
frozen by AAI job 1114953. Job 1115599 subsequently verified the three current
Stage I uniform-joint S0 tensor files, FP32 saved adapter identities and recorded
CPU packages. Its returned receipt hash is
`b4c6d7433ed7fa1a2fa367027268b39cb26aabc5d08a7ba8a38ab3b54e74e7e8`.
That returned output is evidence of CPU verification, not effective GPU loading.
The receipt bytes must match on AAI when preparing the execution plan.

The candidate digest remains
`66f13a4fae506c2ec944a0833fd6dab9f898375caa46bcb60d625ab131375e22`;
the graph digest remains
`ddff260749cc7b9736265a258295f97e6d7c7fea36c95a6587e3bbcd8cbea9a0`.
No source rescreening, replacement candidate or new freeze is required by this
adapter. The original frozen packages and their code hashes remain unchanged.

## Implemented behavior

`pact.revival.documented_execution` prepares a separate inactive plan from the
exact seal, CPU receipt, training contract and parent metadata. It pins the clean
checkout and absolute scratch path. It creates no events store or spending wallet.
GPQA identities, labels and question text remain in private sealed files; the
training/assay interface contains fitting and allocation-probe rows only.

The stage adapter calls the existing native temporary-branch training, NLL scorer,
policy compiler, continuation trainer and checkpoint locker. This retains the
three/five fitting blocks, 24/40 probes, optimizer and batch contracts, exact S0
rollback, FP32 adapters/BF16 bases, five policies, two seeds and full-contract
aliases. This is executable routing, not a list of function-name placeholders.

Evaluation uses the frozen graph's two policy smoke tasks, one GPQA and one LogiQA.
The assay smoke still uses one ARC and one LogiQA task. Neither smoke adds tasks
or calls. Every locked checkpoint is checked before policy attack acquisition;
shared attacks finish before victims. Native trajectories freeze the three
initial private packets before simultaneous revision, and pristine R reads the
revised packets. Native wallet keys bind the actual team-generated messages,
effective models, seeds and token provenance. Invalid outputs remain failures;
missing results remain missing. No truncation or precision fallback was added.

Reports expand exact policy aliases for logical comparisons while charging only
physical calls. They use stored strict packet statuses, including stop-reason
failures, without permissive re-parsing. GPQA science transfer and LogiQA
generalization remain separate, with equal-source final weighting and task-level
paired analysis. The existing PRIVATE/SANITIZED/RECOVERY storage format is reused;
the child identity and scientific version live in its plan and summary, not in a
replacement interpretation of the historical storage-format version.

The single-stage AAI wrapper is `tools/aai_documented_execution.sbatch`. It uses
the existing pinned container, compatibility library, runtime, certificate bind
and private token file. Hot state/cache stays under `/local`; durable private
state stays under `/dataset/$USER/PACT`. It never queues a next job, requeues a
failure, removes evidence or changes Slurm IDs into scientific seeds. It has not
been submitted or GPU-tested.

## Conditional ceilings (unchanged)

| Component | Generations | Updates | Supervised forwards | Diagnostic forwards |
|---|---:|---:|---:|---:|
| Contribution assay | 8,112 | 192 | 1,536 | 2,640 |
| Policy evaluation and fitting | 15,616 | 2,880 | 23,040 | 0 |
| Total | 23,728 | 3,072 | 24,576 | 2,640 |

Reserved output tokens: **12,148,736**. Included smoke ceilings: 24 assay calls
and 244 policy calls. Alias reuse and rejected interventions may reduce actual
work, but never expand a ceiling. Synthetic forward allowance remains zero.
These are conditional future limits, not a statement of historical remaining
budget and not an active spending allowance.

## Permission and recovery contract

Every scientific stage requires an externally supplied, separately reviewed
`documented_stage2_stage_approval_v1` JSON and its exact file SHA256. There is no
approval generator. A valid document binds `run_id`, `plan_hash`, the complete
`freeze` map, `source_code`, `fixture`, exact `scope`, and `limits` to the prepared
plan; it retains `historical_spending: null` and `historical_budget_reset: false`.
It must carry the actual separate `user_decision` and `execution_approved: true`.
The hash binds that record; it is not a cryptographic reviewer signature or
automated proof of human approval.

Preflight scope has `spending_approved: false`: it permits explicit native metadata,
GPU identity and effective S0 loading checks, but no generation/training/scoring
forwards. Static training contexts are checked; dynamic contexts remain checked
at each native dispatch. Evaluation text stays sealed during this preflight.

Later stage approvals require `spending_approved: true` plus
`preflight_sha256` binding the successful execution-preflight file. Branch scope
also binds block/family; continuation scope binds policy/seed/family. Stage-wide
scope cannot silently authorize another stage. Smaller/different limit objects
are rejected rather than falsely claiming that the inherited wallet enforces
them. Any narrower allowance requires a reviewed change to this implementation.

No such real approval document has been created by this work. CPU fixtures use
explicitly marked invented fixture decisions, never real signatures or grants.

Checks precede wallet creation/model opening. Pending durable markers, an unsafe
latest receipt, a different plan owner, changed policy locks or an unresolved
physical attempt stop dispatch. Safe identical requests can reuse committed
results; uncertain dispatch is never retried. Recovery uses the latest verified
snapshot only, the exact plan hash and original scratch path; failed restoration
keeps evidence. Do not use an older snapshot or a new run ID to reset consumption.

## Exact implemented CLI

These commands document the interface; they are **not authorization to submit a
GPU job**. Use the already established container/runtime and private paths.
`RUN` must end in `pact-stage2-documented-execution-001` on `/local`. `SEAL`,
`CPU_PREFLIGHT` and `PARENT` refer to the existing reviewed artifacts, not newly
created substitutes. `PY` is the recorded runtime's Python executable.

CPU-only preparation, after the user commits/pushes and pins the reviewed checkout:

```bash
"$PY" -B -u -m pact.revival.documented_execution prepare \
  --run-dir "$RUN" --seal "$SEAL" --cpu-preflight "$CPU_PREFLIGHT" --parent "$PARENT"
```

It prints the new inactive execution `plan_hash`. Return that plan for review
before preparing any real stage approval. Do not substitute the cohort digest or
historical Stage I plan hash for this execution hash.

Only after separate approval, the implemented stage interface is:

```bash
"$PY" -B -u -m pact.revival.documented_execution "$STAGE" \
  --run-dir "$RUN" --plan-hash "$PLAN_HASH" --execute \
  --approval "$APPROVAL" --approval-sha256 "$APPROVAL_SHA256" \
  --cache-dir "$CACHE" --persistent "$PERSISTENT"
```

`branch` additionally requires `--block N --family Q|L|M`.
`continuation` additionally requires `--policy NAME --seed 113|227 --family Q|L|M`.
Use `--resume` only for an explicitly reviewed safe partial training checkpoint;
it cannot override an unresolved attempt. One invocation executes one stage and
exports/stops. Order: preflight, assay-smoke, collect, the 24 explicit branches,
score, policy-freeze, unique continuations, policy-lock, evaluation-smoke, evaluate.
Each step needs its own matching approval; this list does not authorize the sequence.

CPU report/export and safe restore:

```bash
"$PY" -B -u -m pact.revival.documented_execution report --run-dir "$RUN" --plan-hash "$PLAN_HASH"
"$PY" -B -u -m pact.revival.documented_execution export --run-dir "$RUN" --plan-hash "$PLAN_HASH" --persistent "$PERSISTENT"
"$PY" -B -u -m pact.revival.documented_execution restore --run-dir "$RUN" --plan-hash "$PLAN_HASH" --persistent "$PERSISTENT"
```

The Slurm wrapper takes `PACT_CHECKOUT`, `PACT_COMMIT`, `PACT_LOCAL`, and
`PACT_EXECUTION_CONFIG`. That private JSON contains `stage`, `run_dir`, `plan_hash`,
`approval`, `approval_sha256`, `cache_dir`, `persistent`, and the stage-specific
selectors above (underscores in JSON names), optionally `resume: true`. There is
no scheduler job submitted by preparation or the CLI. The wrapper rejects unknown
configuration keys and non-scratch hot paths.

## Remaining review

CPU adapter tests exercise native request generation/accounting with invented
outputs, exact smoke reuse, graph seeds, initial-peer messages, aliases, strict
missingness, wrong checkpoints, export privacy and latest-only recovery. Mock
dispatch and mocked training-call routing are not evidence of native optimization
or GPU compatibility. Existing optional neural tests remain separately labeled.

The next review must bind the clean adapter checkout and newly prepared inactive
plan. Effective GPU/native access/context/S0 loading then requires its own explicit
preflight approval. Physical assay spending needs a further artifact-bound
decision, followed by smoke review. No further source eligibility certification,
semantic decontamination, pretrained exposure claim, or historical zero-spend
claim has been made. No Stage II experiment result exists yet.
