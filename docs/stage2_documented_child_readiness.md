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
