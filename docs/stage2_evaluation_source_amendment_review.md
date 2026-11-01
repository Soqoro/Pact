# Decision review: proposed OpenBookQA–LogiQA evaluation source

28 October 2026. **Implementation and CPU audit complete; real cohort feasibility
is NOT established.** No candidate was selected or sealed. No source acquisition,
probe, training, inference, cluster job or Colab work was performed.

## Evidence and findings

The exact completed Stage I PRIVATE archive was rehashed against
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
Seven authoritative source/lineage/checkpoint metadata files matched their pins;
the completed summary matched the archive inventory. Source hash remains
`85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`.
Actual 3 ARC /5 LogiQA blocks and 24/40 shared probes are intact. The completed
13,467-call journal audit is historical evidence; this CPU source review did not
newly verify GPU execution or reload real model tensors.

| Prerequisite | Actual finding |
|---|---|
| Existing v3 | Remains `prospective_eval_not_feasible`; at most six fresh ARC groups under its unchanged policy |
| OpenBookQA main/train local raw bytes | Not found in inspected repository/results-import/Hugging Face cache and temporary paths |
| OpenBookQA immutable revision / raw SHA256 | Not established; no candidate pin fabricated |
| OpenBookQA rights | Unresolved; no item-scope human approval receipt or verified terms package supplied |
| Original English LogiQA revision | Existing pinned registry revision `ff6c4cbca47627b3ac2da94a29fa28204a167b41` |
| Registered LogiQA Train.txt SHA256 | `7d5bb1f58278e33b395744cd2ad8d7600faa0b3c4d615c659a44ec1181d759fa`; current raw bytes not available/verified |
| Fresh LogiQA source/overlap audit | Not executable without the original local train/validation caches; old remaining-capacity bound is not a new audit |
| Current complete exposure inventory | Not supplied with current experiment-ledger, parent lineage and material-overlap review coverage |
| External historical probe consumption | Unresolved; local imported-history search found no conflicts, but cannot prove remote absence |
| Current checkpoint tensor/reload and native context checks | Deferred, not replaced by historical receipts |
| Real eligible / denied / unknown item counts | **Null**, because the actual candidate source bytes were unavailable; no invented zero/count or IDs |
| Candidate / cohort approved / GPU authorized | **False / false / false** |

The public card's 4,957 OpenBookQA training rows are not eligible groups. The
[official card](https://huggingface.co/datasets/allenai/openbookqa/blob/main/README.md)
reports license unknown; the [repository license](https://github.com/allenai/OpenBookQA/blob/main/LICENSE)
does not itself resolve rights to every data item. Public documentation inspection
was metadata-only, not dataset acquisition. Project-unexposed and pretrained-model
unexposed are different claims; pretraining exposure remains unknown.

## Delivered implementation

- Separate `evaluation-source` CLI and seven-module CPU-only package: source
  adapter, existing-rule exposure/group audit, fixed selection, proposed MethodSpec,
  dependency graph, original strict-parser scoring, reports, exports/reconstruction.
- Explicit rights/provenance receipt-file hash verification; no invented approval,
  source fetch, execute or seal command. A proposed manual acquisition procedure
  records the missing revision/digest/rights prerequisites.
- Source-separated paired reporting with equal-source weighting, seed-preserving
  task bootstrap, acceptance/missingness bounds, strict invalids and HOLD/REPAIR.
- Existing v3 allocator and training contracts reused unchanged. New proposed
  identities cannot migrate old wallets or roots. Exact existing S0 is preserved.

Conditional arithmetic from actual source identities: assay 768 baseline/attack
calls +7,344 branch calls =8,112; policy 128 ×(1 +11 teams ×11) =15,616; total
23,728 generations /12,148,736 reserved tokens, 3,072 updates /24,576 supervised
forwards /2,640 diagnostic forwards. The 128 factor is explicitly **required slots**,
not a real selected cohort. A complete invented graph verified these counts and
24/244 included smoke subsets. No real graph manifest could be frozen without the
candidate. Future model outputs/checkpoints/schedules also require explicit runtime
binding before dispatch; the present graph is non-dispatchable.

## CPU evidence

- New source/amendment tests: **20 passed**.
- Existing v3 tests with local CPU Torch: **24 passed**.
- Existing training-data tests: **9 passed**.
- Existing exposure-inventory tests: **4 passed**.
- Compilation and `git diff --check` passed.

The invented round trip reads bounded OpenBookQA-shaped JSONL and original-format
LogiQA text, canonicalizes/excludes/selects, compiles all upper-bound nodes, scores
mock packets, exports PRIVATE/SANITIZED and reconstructs the same reports. It does
not download weights, call model backends or establish real data eligibility.
The actual blocked parent/source review was also exported and successfully
reconstructed from its PRIVATE bundle on CPU, independently of the fixture run.

## Actual review artifacts

Private root: `results_import/evaluation-source-amendment-v2-final-reviewed/`
(ignored and untracked). Proposed MethodSpec: `method.private.json`; source and
lineage detail: `source.private.json`, `lineage.private.json`; blocker report:
`audit.private.json`; aggregate report: `summary.json`.
No `candidate.private.json` or `graph.private.json` exists in this real review.

PRIVATE bundle:
`pact-stage2-openbookqa-logiqa-eval-amendment-v2-001-PRIVATE-815f5d845ce029d6.zip`
SHA256 `0d6ad2190faa6ce13069cdaaa7a6658ec114b097edea29803d49757a7474fe25`.

SANITIZED bundle:
`pact-stage2-openbookqa-logiqa-eval-amendment-v2-001-SANITIZED-421901c468a37d13.zip`
SHA256 `fe898f5fe7ebafa0a82b3ea3b06ce0aa0e26f483f0cf9bb80b36acadd33400ab`.

These are audit handoffs, not experiment results or model recovery checkpoints.
Keep PRIVATE restricted; SANITIZED has aggregate fields and no task-level identifiers.

## Separate decisions still required

1. Establish and review the exact official OpenBookQA main/train immutable file,
   expected bytes/hash and applicable item-scope rights; arrange original LogiQA
   cached-source and rights evidence too. No reliable approved acquisition package
   exists yet. Source access/materialization needs its own explicit user approval.
2. Supply actual bytes and current reviewed project exposure/overlap inventory;
   run the implemented CPU audit for both sources. Only that can establish whether
   64+64 permitted unique groups exist. A shortfall ends this candidate review; no
   silent replacement dataset or relaxed exclusion is provided.
3. If supported, review the private candidate, revisions, source rights, historical
   probe use, analysis and proposed MethodSpec. Candidate selection does not seal it.
4. Separately review effective checkpoint reload/native context evidence and the
   complete frozen request plan, then decide on GPU execution. None is authorized now.

The next decision is about source evidence/access, not assay execution. Exact CPU
commands and receipt requirements are in
[the runbook](stage2_evaluation_source_amendment_runbook.md); the preserved scientific
contract is in [the methodology](stage2_evaluation_source_amendment_methodology.md).

## Changed files for this amendment

New code: `src/pact/revival/evaluation_source/__init__.py`, `__main__.py`,
`sources.py`, `graph.py`, `review.py`, `results.py`, `fixtures.py`.
CLI integration: `src/pact/cli.py`.
New tests: `tests/test_evaluation_source.py`.
New documentation: `docs/stage2_evaluation_source_amendment_methodology.md`,
`docs/stage2_evaluation_source_amendment_runbook.md`, and this review.
Appended project records: `AGENTS.md`, `docs/implementation_decisions.md`,
`docs/implementation_status.md`, `docs/experiment_ledger.md`.
The supplied reviewed specification and earlier uncommitted v2/v3 work were
preserved. No completed run record or existing v3 execution module was modified.
