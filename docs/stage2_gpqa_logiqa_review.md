# Review: Stage II GPQA Main / original English LogiQA proposal

Date: 2026-10-28. Authority: implementation and local CPU audit only.

## Decision

**The real 64+64 cohort is not yet established.** The CPU source audit, dependency
graph, proposed candidate seal, scoring/reporting, private/sanitized exports and
CPU Slurm wrapper are implemented. Actual source eligibility remains blocked on
unavailable source and current exclusion evidence. This is not a negative finding
about GPQA's eventual capacity, and not an executed training/evaluation result.

| Readiness | Actual state |
|---|---|
| CPU implementation | Implemented and focused tests passed, with regression limitations below |
| Real candidate exists | **False** |
| Real candidate frozen | **False** |
| Execution authorized | **False** |
| New real model calls/forwards/updates | **0 / 0 / 0** |
| Historical relevant spent/remaining budget | **Unknown / unknown**, not zero/full ceiling |
| New GPU dispatcher for this child | Not enabled; guarded connection remains deferred |

No download, pretrained load, GPU work, remote command, Slurm submission, secret
inspection, commit, push or cleanup occurred. Existing source and execution
records were retained.

## Evidence actually inspected

The closed Stage I archive is SHA256
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
Its authoritative members and summary match the extracted local parent. The
summary records 13,467 committed calls, zero unresolved, and all stages complete.
The executed source hash is
`85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`.
The actual 3/5 block hash is
`40892bfd28b458bdd6438b47ea5909467d690df5c66b5789f11182e618925644`.
The exact uniform_joint_sft checkpoint inventory is carried forward. Historical
checkpoint verification does not imply a fresh tensor load/runtime check here.

The resulting training-only dependency hash is
`d01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49`.
Scientific seed values, memberships, ordering and policy mathematics are preserved;
future source/admin/job changes alter authorization identity but not training RNG.

The inspected repository/local HF-cache filename inventory did not locate Main,
Diamond or original LogiQA training raw files. No cluster storage was inspected.
No real GPQA example text was read or reproduced. The loader reuses official GPQA
revision `83022cefff930aea54f654c0b282e74b9eeda5c6`, original Diamond and terms pins,
and native option mapping. **There is no newly verified Main source hash or real
eligible count.** Acquisition exists only as an explicit user-invoked command.
Existing dataset/account terms evidence can be reused; no new acceptance is asserted.

The local audit had no refreshed exposure/partition/remote consumption inputs, so
its nine machine blockers are:

- `experiment_history_coverage_stale`
- `exposure_coverage_unknown`
- `exposure_inventory_stale_or_incomplete`
- `gpqa_historical_partitions_unverified`
- `gpqa_main_bytes_unavailable`
- `original_train_validation_bytes_unavailable`
- `parent_exposure_lineage_conflict`
- `relevant_external_consumption_unresolved`
- `semantic_overlap_review_unresolved`

These describe missing audit inputs, not proof that existing cluster records are
invalid. The shortest next action is a **cluster CPU source/exclusion audit using
the existing authorized files**, with the config/runbook below. Do not start an
assay or automatically fetch substitutes. Source acquisition, if needed, is a
separate explicit action. Later candidate sealing and bounded GPU execution are
separate decisions; an audit or scheduler success supplies neither.

## Implemented files and behavior

- `src/pact/revival/gpqa_source/sources.py`: pinned bounded official acquisition
  (explicit only), local CSV/receipt verification, Main/Diamond grouping and
  protections, conflicting keys/aliases, deterministic exact64+64 selection.
- `review.py`: exact parent/source/checkpoint lineage, existing original-source and
  exposure audit, scoped history inspection, immutable artifacts and export validation.
- `contracts.py`, `graph.py`: training-only interface, scientific dependency
  identity, unchanged native prompts, complete conditional dependency graph and
  exact budget reconciliation. Dynamic request identity includes actual packets.
- `context.py`: local-only staged native tokenizer verification and static context
  checks; no model load. Full generated-message context remains a runtime check.
- `plan.py`: explicit MethodSpec-hash candidate seal with prospective embargo and
  no new wallet/automatic executable authorization.
- `results.py`: strict scoring reuse, seed-paired/equal-source contrasts,
  intended-population bounds, incomplete/undefined endpoints, per-team natural
  hold/repair denominators and S0 once.
- `recovery.py`: existing durable owned Wallet, single writer and exact checkpoint
  restoration interface; unresolved attempts/markers/changed ownership stop.
- `fixtures.py`, `__main__.py`, `__init__.py`, CLI `gpqa-source`: executable CPU
  audit/validate/export/seal/static-context/reconstruct/inventory/mock/recovery-check;
  independent explicit `acquire` command.
- `tools/aai_gpqa_source_audit.sbatch`: existing pinned container/runtime, CPU-only
  private `/dataset` audit, no new migration, installation, job chaining or GPU work.
- `tests/test_gpqa_source_amendment.py`, methodology/runbook and appended AGENTS,
  decisions, status and experiment-ledger entries.

**Remaining implementation boundary:** new child GPU dispatch is not exposed.
The original v3 runner is not silently patched to accept GPQA or a sealed proposal.
A real execution bridge must bind the reviewed candidate and new report to that
runner only after the actual owned-budget and checkpoint/runtime prerequisites
are resolved. Thus this handoff does not claim complete GPU execution readiness.

## Budgets

The real executed 64 allocation probes give 816 branch-task views. Reconciliation:

| Resource | Assay | Continuation/evaluation | Ceiling |
|---|---:|---:|---:|
| Generation calls | 8,112 | 15,616 | 23,728 |
| Reserved output tokens | 4,153,344 | 7,995,392 | 12,148,736 |
| Updates | 192 | 2,880 | 3,072 |
| Supervised forwards | 1,536 | 23,040 | 24,576 |
| Diagnostic forwards | 2,640 | 0 | 2,640 |

Included smoke maxima 24/244. Full synthetic graph counts match exactly. The real
128-task evaluation graph cannot be instantiated without a candidate; its ceiling
is conditional, not an invented real request inventory. Aliases/rejections do not
reallocate spare calls. The new source/child/job identity cannot reset ownership.

## Tests actually executed

Commands used `PYTHONPATH=src python -m unittest discover -s tests -p PATTERN -v`.

| Pattern / check | Actual outcome |
|---|---|
| `test_gpqa_source_amendment.py` | **20 passed** |
| `test_allocation_v3.py` | **20 tests ran successfully; optional neural class skipped** because local Torch/safetensors are unavailable |
| `test_evaluation_source.py` | **20 passed** |
| `test_gpqa_support.py` | **17 passed, 2 errors**: native outside-Git privacy check rejects the test temporary paths under this environment's `/tmp` Git boundary |
| `bash -n tools/aai_gpqa_source_audit.sbatch` | Passed; no controller contact |
| `python -m compileall -q src/pact/revival/gpqa_source` | Passed |
| `git diff --check` | Passed |
| Real metadata-only `audit`, `validate`, `export` | Completed; accurately returned BLOCKED, no candidate, zero model work |

The native regression errors were not suppressed and its privacy guard was not
weakened. No full repository test-suite or GPU pass is claimed. The newly added
checks cover source/admin substitution invariance, graph/smokes, protected and
conflicting mappings, option/label boundaries, no hidden network, embargo,
context overflow, five-policy round trip, paired weighting/missingness, durable
ownership, sanitized output and immutable seal. Actual staged tokenizer assets
and neural checkpoint restore were not exercised locally.

## Handoff

Local metadata-only audit directory:
`results_import/stage2-gpqa-logiqa-source-review-v2-final`.
It includes source/lineage/training/audit/proposed-MethodSpec records, aggregate
summary, manifest, bundles and `local-audit-receipt.json`.

- SANITIZED filename:
  `pact-stage2-gpqa-logiqa-eval-amendment-v2-001-SANITIZED-10bdaf65c4a565ed.zip`
- SANITIZED SHA256:
  `f2a0f2de46d1ed6b1ebbe54a8bd5add4d466880cbcafafa703f96b1905e671c9`
- PRIVATE metadata-only archive SHA256:
  `263c0f0b88d1c40a93ea43cb168e42dcc304b9efe20989ae86a7bc3ae588b060`

This local blocked audit contains no newly acquired GPQA rows. Future real source
PRIVATE artifacts must remain outside Git in restricted cluster storage; return
only SANITIZED ZIP plus local audit receipt. Exact implemented commands and
input schemas are in [the runbook](stage2_gpqa_logiqa_runbook.md). Scientific and
privacy contracts are in [the methodology](stage2_gpqa_logiqa_methodology.md).

## 2026-11-02 evidence update

The initial missing-source state above is historical. User-returned acquisition
and CPU audits now establish staged official bytes, but not a certified cohort.
The [scoped history review](stage2_scoped_history_review_2026-11-02.md) consolidates
provisional source counts, exposure additions, remote inventory evidence and the
original retained archive. No Stage II activity was found within inspected scope;
missing later original history prevents a zero-spending conclusion. Candidate,
freeze and execution remain false. No additional allowance has been approved.
