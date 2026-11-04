# Documented-exclusion Stage II child: implementation and readiness

3 November 2026. Child: `pact-stage2-documented-exclusions-amendment-001`.

**Decision: CPU implementation is available; real 64+64 feasibility is not yet
established locally. No cohort is certified, frozen or approved for execution.**
The user's approval accepts the documented-exclusion development standard and
conditional ceilings. It authorizes implementation/CPU validation, not a physical
spending allowance. The preceding proposal remains a historical artifact.

## Implemented change

`src/pact/revival/documented_child/` is a separate versioned path. It does not change
old Stage II validators, the completed Stage I evidence, or the blocked v3 plan.

- `audit.py` binds the exact executed source/S0 metadata and returned exclusion
  union, verifies local official GPQA Main/Diamond and original English LogiQA
  files through existing loaders, and runs actual item/group screening. No fetch.
- Legacy GPQA reconciliation still receives `reviewed=False`. Only this child
  treats lack of blanket scope/semantic certification as an accepted limitation.
  Diamond protections, integrity failures, documented exposures, concrete cases
  and unknown reason codes are not waived. Candidate-specific cases can be
  supplied as a hash-bound PRIVATE list of `{task_id, reason}`; unmatched IDs stop.
- `lexical.py` applies the existing exact identity/content and word-trigram
  Jaccard >=0.9 transitive rule across sources, preserving actual splits. It does
  not relabel GPQA as training data. Validation overlaps and label conflicts are
  excluded; historical exclusions propagate across components. Duplicate
  components can be conservatively excluded in full rather than released by
  selecting an unexposed alias.
- The nine documented OpenBookQA preview IDs remain recorded exclusions for
  their actual source. They are not fabricated as GPQA/LogiQA IDs. No selected
  source is OpenBookQA. Their possible semantic relation across sources remains
  unknown, not a claim of semantic separation. A concrete identified cross-source
  case must be supplied and remains binding.
- Exactly 64+64 groups are proposed only after source/partition/union verification
  and sufficient screened unique-group counts. Selection, option mapping, seeds
  and attack templates are inherited unchanged; no outcome filtering or reroll.
- `review.py` compiles a child-owned graph with distinct node identities but
  unchanged scientific seeds, prompt implementation and dependency structure.
  Assay smoke is ARC/LogiQA (24 included calls); policy smoke is GPQA/LogiQA
  (244 included calls). Both are subsets of the full graph.
- `policies.py` uses the real five-policy compiler and credit estimator, with a
  training-only interface. It preserves 3/8–5/8 allocation weighting and supplies
  GPQA/LogiQA 50/50 evaluation weighting. The existing source-stratified reporter
  retains missingness, task-level sampling and seed pairing.
- The execution guard checks exact MethodSpec, stage ownership, candidate,
  pending state, S0 receipt and evaluation policy/checkpoint/analysis locks.
  **It then denies execution under the current CPU-only approval.** There is no
  authorization-boolean bypass or CLI that mints an execution grant or wallet.
- Content-addressed PRIVATE/SANITIZED ZIPs, checksum verification, CPU audit
  recovery, incompatible-output rejection and sanitized exception logging are
  implemented. SANITIZED exports contain aggregates/digests only, not task IDs,
  labels, text, paths, generated packets or token arrays.
- `tools/aai_documented_child_audit.sbatch` connects audit/validate/report/export
  to the existing pinned, offline Apptainer CPU workflow. It requests no GPU,
  performs no installation and submits no further job.

## Real evidence versus tests

The local audit verified the executed source and S0 registry through authoritative
Stage I metadata. The unchanged training dependency digest is:

`d01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49`.

The locally available evidence does **not** include official GPQA/original raw
source files, the actual returned reconciliation draft, or its private historical
partition manifests. The real local result is therefore `SOURCE_AUDIT_BLOCKED`:

- `documented_exclusion_union_unavailable`
- `historical_partitions_unverified`
- `gpqa_bytes_unavailable`
- `original_bytes_unavailable`

These are local evidence-availability blockers, not a finding that AAI's verified
files disappeared. No real `candidate.private.json` or `graph.private.json` was
created locally. The reported historical 249 GPQA scope-only groups and 6,041
unknown LogiQA **items** are not recertified eligible unique groups.

The separate invented-data tests exercise actual parsers, component screening,
selection, graph compiler, policy compiler and export/recovery. Fixture results
are not experimental results or real-source feasibility evidence. No current
checkpoint tensors or GPU behavior were verified by this implementation task.

## Exact conditional budget

| Component | Generation calls | Updates | Supervised forwards | Diagnostic scoring forwards |
|---|---:|---:|---:|---:|
| Contribution assay | 8,112 | 192 | 1,536 | 2,640 |
| Policy continuation/evaluation | 15,616 | 2,880 | 23,040 | 0 |
| Total | **23,728** | **3,072** | **24,576** | **2,640** |

Reserved output tokens: **12,148,736** (512 per generation). Included smoke calls:
24 assay, 244 policy. No extra synthetic forwards. The fixture graph reconciles
these counts exactly. The real graph remains absent until the real cohort passes.
Historical spending and remaining historical balance remain `null`/unknown.
Aliases or rejected attacks reduce physical work, not permission to add requests.

## CPU commands and AAI handoff

Local tests (no pretrained downloads):

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_documented_child.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_development_amendment.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_gpqa_source_amendment.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_exposure_accounting.py -v
```

After user review/commit/push and a pinned checkout on AAI, prepare a **new** config
from the existing source audit config. This is documentation only; no remote
command or job has been executed by this task. Do not return PRIVATE source data
to the assistant.

```bash
cd "$HOME/Pact"
export PACT_CHECKOUT="$HOME/Pact"
export PACT_COMMIT="$(git rev-parse HEAD)"
export PACT_CONFIG="$HOME/pact-aai-preflight/documented-child-cpu-v1.json"
python3 - <<'PY'
import json, os
from pathlib import Path
home=Path.home()
dataset=Path('/dataset')/os.environ['USER']/'PACT'
old=json.loads((home/'pact-aai-preflight/stage2-gpqa-audit-v1.json').read_text())
config={k:old[k] for k in ('parent_dir','exposure','gpqa_dir','data_dir','inventory')}
config.update(
    audit_root=old['run_dir'],
    exposure_draft=str(dataset/'stage2-exposure-reconciliation-v1/reconciliation.private.json'),
    output=str(dataset/'stage2-documented-exclusions-cpu-v1'))
p=Path(os.environ['PACT_CONFIG'])
if p.exists():
    assert json.loads(p.read_text())==config, 'Preserve differing config; stop.'
else:
    p.write_text(json.dumps(config,indent=2)+'\n');p.chmod(0o600)
print('CPU config prepared. No submission or execution.')
PY
```

The implemented Python entry points, run **inside the established pinned container
CPU environment**, are:

```bash
python -B -u -m pact.revival.documented_child audit --config "$PACT_CONFIG"
python -B -u -m pact.revival.documented_child validate --config "$PACT_CONFIG"
python -B -u -m pact.revival.documented_child export --config "$PACT_CONFIG"
```

The prepared sbatch wrapper accepts `PACT_STAGE=audit`, `validate`, `report`, or
`export`, with `PACT_CHECKOUT`, full `PACT_COMMIT`, and `PACT_CONFIG` as above.
**No sbatch submission is authorized by this approval.** The next separate action
is approval to submit this CPU source-audit job on AAI. It needs no GPU budget and
no dataset acquisition. Return only the sanitized summary and SANITIZED bundle.

CPU-only recovery of a handoff uses a config with a new absent output directory:

```bash
python -B -u -m pact.revival.documented_child restore \
  --config "$RECOVERY_CONFIG" --bundle "$PRIVATE_ZIP" --sha256 "$PRIVATE_SHA256"
```

This verifies the entire archive and recompiles its contracts; it cannot recover
or resume a scientific execution wallet. Changed code/contracts require review,
not an implicit migration of the old packet.

## Artifacts and next decision

Always: `source.private.json`, `lineage.private.json`, `audit.private.json`,
`training.private.json`, `method.private.json`, `summary.sanitized.json`,
`manifest.json`. Only a sufficient real screen adds `candidate.private.json` and
`graph.private.json`. Export creates verified PRIVATE and SANITIZED ZIPs in
`bundles/`. A candidate remains proposed, not automatically certified or frozen.

Before any real assay: review the actual candidate/graph and unresolved cases,
accept a specific cohort, approve a new stage-bound physical-spending allowance,
and verify current exact S0 tensors/runtime/tokenizers/context limits. A future
execution amendment must connect the real dispatch adapter and durable wallet to
that grant. This CPU implementation deliberately does not expose model dispatch.
Existing native training/evaluation machinery is retained, but its old validator
cannot be used to bypass the new child's approval boundary. No Stage III follows.

All future results must state: exploratory development evaluation screened against
documented project exclusions and deterministic lexical overlap; semantic
contamination, pretrained exposure and missing-interval compliance are not
established. No new performance or scientific-efficacy result exists from this task.

## Executed validation and local handoff

- New child regression suite: **14 passed**.
- Existing development-proposal, GPQA amendment and exposure-accounting suites:
  **49 passed** (11 + 21 + 17).
- Existing allocation-v3 suites: **20 test methods passed**; optional neural test
  class skipped because local Torch/safetensors are unavailable, and the opt-in
  full CPU round trip skipped. No claim that either skipped path was verified.
- `bash -n tools/aai_documented_child_audit.sbatch` and `git diff --check` passed.
- Real local CLI `audit` and `export` completed with the blockers listed above.
  This checks named lineage and emits an honest blocked report, not eligibility.

Local files are under ignored
`results_import/stage2-documented-child-metadata-final-001/`.

PRIVATE metadata audit bundle SHA256:
`3235c0c5b80a00483765ae329765da6ceef919e63bca87317e7dc24c021c4c0d`.

SANITIZED metadata audit bundle SHA256:
`39e921bae91001b83152942f065b55e17acbfa5eb2761f22af9536f0d2591b68`.

These are local blocked-audit bundles, not new AAI source-audit evidence or
experimental results. No source raw text was added to tracked outputs.

## Returned AAI CPU audit — job 1114923

User returned the SANITIZED stdout and Slurm accounting: `COMPLETED`, exit `0:0`,
elapsed 37 seconds. This is returned remote evidence, not a locally inspected
PRIVATE source audit or independently verified export. It supersedes the *remote*
source-availability uncertainty; the earlier local blocked result is preserved.

The real (`fixture=false`) audit reports no screening blockers, 249 screened unique
GPQA Main groups and 5,995 screened unique original English LogiQA groups. It
proposes 64 groups from each source under the documented-exclusion development
standard, with no certification of project freshness or semantic decontamination.

- Candidate digest: `66f13a4fae506c2ec944a0833fd6dab9f898375caa46bcb60d625ab131375e22`.
- Graph digest: `ddff260749cc7b9736265a258295f97e6d7c7fea36c95a6587e3bbcd8cbea9a0`.
- Training dependency digest remains `d01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49`.
- Compiled graph: 8,112 assay + 15,616 policy generations; 3,072 updates,
  24,576 supervised forwards and 2,640 diagnostic forwards; 12,148,736 reserved
  output tokens. These are conditional limits, not expenditure or an active wallet.
- `cohort_frozen=false`, `execution_authorized=false`, `wallet_active=false`;
  historical spending/remaining balance unknown; model calls/training forwards zero.

Next: validate and export this exact existing CPU audit via its `export` stage,
then return only the SANITIZED ZIP and its SHA256. Do not rerun acquisition,
change the cohort, or start a model stage. Review of the exported evidence and
separate cohort/execution decisions remain outstanding. This task did not submit
a cluster job or commit/push changes.

## Locally verified SANITIZED export — AAI job 1114925

The uploaded 1,478-byte SANITIZED archive was verified locally against SHA256
`92b02b69acbc02cc002fcef2b2572291f88e98316287f8469971f367c078a99d`.
Its exact three-member inventory, internal summary checksum, child/version/kind,
candidate and graph digests, and conditional budgets match the returned audit and
local budget contract. The summary contains no raw task text, task IDs, labels,
prompts or tokens. Verification copies and a local receipt are preserved under
ignored `results_import/stage2-documented-child-aai-1114925-sanitized/`.

This verifies the exported aggregate evidence, not the private source bytes,
individual candidate membership or checkpoint tensors on AAI. The reported
249/5,995 screened groups support the proposed 64+64 development cohort under the
accepted standard. The candidate remains unfrozen and unapproved for execution.
All residual limitations and unknown historical spending remain unchanged.

The CPU export/review handoff is now complete. The next decision is explicit
acceptance of the concrete candidate and graph above for freezing, separately
from any physical-spending approval. Current checkpoint/runtime verification and
reviewed execution integration remain required before real assay work. No new
experiment, wallet or GPU work was initiated by importing this archive.

## Exact cohort freeze handoff

The user instructed: “Proceed toward freezing the exact proposed cohort.”
`pact.revival.documented_freeze` implements that CPU-only action with hard-bound
candidate, graph, training and PRIVATE archive hashes listed above. It validates
the original audit with its unchanged implementation, matches every PRIVATE ZIP
member to the live audit, checks the training-only interface/S0 metadata, and
writes a new seal through verified staging. A matching existing seal is verified
idempotently; incomplete, changed or symlink destinations stop without overwrite.
The tool does not reselect data or alter the original `cohort_frozen=false` report.

`tools/aai_documented_cohort_freeze.sbatch` requires the existing pinned environment,
`PACT_CHECKOUT`, `PACT_COMMIT`, `PACT_CONFIG`, and new `PACT_FREEZE_OUTPUT`. It requests
CPU only. The exact Python entry point inside that environment is:

```bash
python -B -u -m pact.revival.documented_freeze \
  --config "$PACT_CONFIG" --freeze-output "$PACT_FREEZE_OUTPUT"
```

Recommended new destination:
`/dataset/$USER/PACT/stage2-documented-cohort-frozen-v1`.
Artifacts: immutable `evidence/` copies, `sealed/prospective.private.json`,
`sealed/graph.private.json`, `training.private.json`, `freeze.sanitized.json`,
`checksums.json`, and `COMPLETE`. Return stdout and the sanitized freeze receipt
only. Keep all other evidence on AAI. Freezing is not yet reported as remotely
completed until that evidence returns. Physical spending remains unauthorized.

## Returned freeze completion — AAI job 1114953

User-returned stdout and Slurm accounting report `COMPLETED`, exit `0:0`, elapsed
five seconds, `fixture=false`, `COHORT_FROZEN_EXECUTION_DISABLED`. Candidate and
graph digests match the locally verified SANITIZED audit. This is confirmation
from returned remote output; the freeze receipt file and private sealed files
have not been independently inspected locally.

- Candidate: `66f13a4fae506c2ec944a0833fd6dab9f898375caa46bcb60d625ab131375e22`.
- Graph: `ddff260749cc7b9736265a258295f97e6d7c7fea36c95a6587e3bbcd8cbea9a0`.
- Method: `13817d7b6ebdb6634e9028d8421c57203bf76f1d2483d297b8ddba39bfa184f7`.
- Freeze receipt file SHA256: `0d1530b1658bcab6216eab9c6bb8dc311a2321b9efcb09f28960e7f233ad8921`.
- Freeze manifest SHA256: `b13f9f7571cb6b8a6d6fb3a5d17020dc77976d3e76887af6e35440a80cdd45e7`.
- Original audit manifest SHA256: `5b22b2477d9e47f1376ad592301e0d0eabe06368b1f0cd269925a58d335b58e0`.

`candidate_frozen=true`; execution and wallet remain false. No model calls,
training forwards or optimizer updates occurred. Current S0 tensors are not
verified by this seal, and policies/trained checkpoints are not locked. The
conditional ceilings and all exposure/history limitations remain unchanged.

The next evidence handoff is only `freeze.sanitized.json`. After that, execution
integration, current checkpoint/runtime verification and a separately scoped
physical-spending decision remain prerequisites. No training, assay or GPU job
is authorized by the returned freeze completion.

## CPU checkpoint readiness integration — 5 November 2026

`pact.revival.documented_preflight` is separate from the frozen audit package.
It first verifies the exact freeze receipt/manifest identities reported by job
1114953, all sealed files, original audit compilation and immutable candidate,
graph and training digests. It then validates the seven authoritative Stage I
metadata files and checks the three **uniform_joint_sft** S0 adapter files with
`stage1.weights.tensor_inventory`, on CPU. File SHA256, effective adapter hash,
FP32 dtype, key/shape registry and finite values must match the frozen registry.
Independent-arm substitutions are rejected. Optimizer state is not restored.

The output includes a training-only execution-contract bridge, preserving the
five policies, original optimizer, 3/5 blocks, 24/40 probes, scientific seeds and
conditional budgets. Prospective question text and labels are absent from this
bridge. Existing assay/training stage functions are identified; the child-specific
policy evaluation dispatch adapter remains unimplemented. The bridge is explicitly
non-dispatchable. Neither a preflight result nor a modified authorization boolean
can pass its execution gate. No physical wallet is instantiated.

Package inspection checks the recorded Python/package versions without fetching
anything. CPU-only package matching cannot verify the CUDA runtime, current GPU,
native model loading or tokenizer/context behavior. Those remain separate
prerequisites, along with reviewed execution integration and physical allowance.
A package mismatch is reported explicitly even if CPU checkpoint identities pass.
No scientific forward is included in this preflight.

Prepared CPU wrapper: `tools/aai_documented_cpu_preflight.sbatch`. It uses the
existing offline pinned environment; mounts the verified migration tensor tree
read-only at its recorded `/content` path; and hides CUDA devices. Required env:
`PACT_CHECKOUT`, `PACT_COMMIT`, `PACT_CONFIG` (existing audit config), `PACT_SEAL`,
`PACT_PREFLIGHT_OUTPUT` (new absent private directory). No job was submitted by
local development. The Python entry point inside the container is:

```bash
python -B -u -m pact.revival.documented_preflight \
  --config "$PACT_CONFIG" --seal "$PACT_SEAL" --output "$PACT_PREFLIGHT_OUTPUT"
```

Outputs: `execution-contract.private.json`, `preflight.sanitized.json` and
`checksums.json`. The original seal and parent remain unchanged. Return sanitized
stdout and the sanitized receipt only. The actual CPU checkpoint read on AAI is
still unverified until its result returns; local tests use invented metadata and
exercise guards without downloading or loading a pretrained model.
