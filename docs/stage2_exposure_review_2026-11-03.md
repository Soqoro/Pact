# Stage II exposure review — 3 November 2026

Status: bounded evidence review completed; acceptance unset. No cohort certification,
plan freeze, accounting activation or execution authorization.

## Outcome

The source/S0 lineage and proposed mechanical bindings check out. The remaining
coverage and overlap fields cannot be filled by copying hashes or treating the
user's “proceed” as scientific approval. There are two review judgments, plus a
specific remote metadata limitation. There is no reason to repeat broad history
scans, redownload sources or reopen completed diagnostics.

This follow-up implements the evidence review proposed after the
[project report](audits/PACT_PROJECT_REVIEW_2026-11-02.md). It supplements the
[decision packet](stage2_exposure_accounting_decision_v2.md), without rewriting it.

## Checks actually performed

The existing bounded `exposure_accounting.read_inputs` reader rechecked the named
local source/audit manifest, seven authoritative parent JSON hashes and S0 registry
bindings. No source questions, model tensors or remote filesystem were inspected.

- Executed source canonical digest remains
  `85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b`.
- S0 matches the authoritative uniform-joint checkpoint inventory. This is a
  metadata identity check, not a new tensor or runtime verification.
- The proposed packet's experiment-ledger binding matches the current file SHA256:
  `542249126f036130dd58dae20256af98239b8833d9b1efed4e3cbed43d04c088`.
- The inherited exposure inventory has 12 source receipts and a review dated
  16 October covering closed selective correction and selector reuse. It lacks
  `parent_source_sha256`, `experiment_ledger_sha256`, `coverage`, and
  `material_overlap_review`. Missing fields are not themselves evidence of a
  contradictory source or a discovered semantic overlap.
- The existing proposed exclusion union retains the baseline and adds 960
  allocations to each identity representation. No actual eligible candidate is
  present. Review acceptance remains unset.

The inspected local source audit predates the reported remote source acquisition.
Its `source_bytes_unavailable` status cannot be used as a current finding about
AAI. Conversely, the user-returned acquisition summary is not a fresh local check
of those source bytes or of per-group eligibility.

## Coverage map

| Evidence class | Supported coverage | Remaining issue |
|---|---|---|
| Twelve inherited receipts | Breadth exposure manifests, training selections, heterogeneous pilot and closed selective plan are referenced by the inherited inventory | This review checked receipt structure and inherited binding, not every referenced historical archive again |
| Executed Stage I source | All 400 ARC and 560 LogiQA allocations are represented in the conservative union | Allocation is an exclusion reason, not proof that every item received every possible operation |
| Later amended Stage I evaluation | Recorded validation/source/fixed-history evaluations use the executed source; their completed audits remain authoritative | No new cohort exemption or release follows from evaluation completion |
| Historical GPQA | Returned partition audit preserves original and breadth protections, including all Diamond groups | Remote per-group metadata has not been imported into this local packet |
| OpenBookQA preview | Nine preview identities are documented in the access review and remain exclusions | The packet adds source allocations; that does not prove it materializes all preview/cross-source aliases. Any relevant mapping must stay unresolved until the existing private audit supports it |
| CPU proposals, migration and accounting reports | Documentation/metadata work does not itself establish new model consumption | Do not count file copying as inference or use a ledger hash as proof of coverage |
| Missing original-run interval | Bound source/code restrict the documented run to allocated ARC/LogiQA groups | Continued enforcement in missing later activity is conditional, not verified |

The original source relation supports a narrowly stated assumption: if the bound
contract continued to govern that run, its possible task use falls inside an
already excluded source allocation. It does not prove arbitrary external activity
impossible. Prior allocation-probe use concerns training adaptation and spending;
it does not automatically expose a different prospective evaluation cohort.

## Exact decisions still needed

### 1. Coverage scope

**Proposed review wording, not accepted:**

> Assess future evaluation freshness against the inherited protected/used groups,
> all 960 Stage I allocations, preserved GPQA partitions and recorded preview
> exclusions. For the missing original-run interval, accept conditional
> nonintersection only within the documented frozen-source contract. Keep any
> concrete candidate-relevant exception unresolved. Do not infer zero historical
> spending, terminal closure, or absence of pretrained-model exposure.

This is a scoped interpretation for an authorized project reviewer. It does not
certify that a particular 64+64 selection satisfies the exclusions. The inherited
inventory's earlier review is not an acceptance of this extended scope.

Recommendation: review this narrow scope explicitly, rather than request a claim
that Stage II never ran. If the assumption is not acceptable, source freshness
must remain unresolved; a future budget approval cannot fix that.

### 2. Material overlap scope

The active policy checks `material_overlap_review == "no_unresolved_cases"`.
The implemented lexical checks explicitly do not establish semantic decontamination.
No applicable acceptance for the proposed current GPQA/LogiQA scope was established
in the inspected named evidence. No concrete semantic pair was identified by this
review either; absence of a supplied pair is not a positive overlap certificate.

**Required review question:** does an existing accepted private review cover the
current sources, exclusions and material overlap scope? If it does, bind that
receipt. Otherwise an authorized reviewer must assess the actual scope and any
specific cases identified by evidence. Do not declare all 249 provisional GPQA
groups or all 6,041 unknown LogiQA items eligible from aggregate counts.

Recommendation: use existing restricted audit metadata first. No blanket human
review of every item, hosted semantic grading, or invented pair queue is proposed.

## Smallest remaining evidence handoff

The existing optional CPU decision-packet command in the
[runbook](stage2_gpqa_logiqa_runbook.md#reviewed-v2-exposureaccounting-decision-packets-no-scans-or-activation)
reads the already completed AAI audit and exact exposure-union draft. It is the
prepared mechanism for obtaining remote group-status metadata, not another source
or history search. No job was submitted here.

After local review/commit/push, the user can run that existing `sbatch` command
and return only `summary.sanitized.json` and `cpu-receipt.json`. PRIVATE group IDs,
raw GPQA text, labels and maps remain on the cluster. The command neither approves
the two judgments above nor selects/seals a new cohort.

Until that evidence and the applicable review judgments support a current audit,
the honest cohort status remains **not certified**. The next scientific action is
not GPU execution. Accounting acceptance, candidate freeze, runner integration
and checkpoint/runtime gates remain separate later decisions.

## Scope of this follow-up

Only this review document was added. No active policy, receipt, ledger, proposal,
wallet or existing packet was changed. Keeping the ledger unchanged also preserves
the verified packet binding above. No new unit suite was needed for this
read-only review; the actual checks were bounded metadata verification, binding
comparison, relative-link checks and whitespace validation. No network, source
acquisition, remote command, model work, cleanup, commit or push occurred.
