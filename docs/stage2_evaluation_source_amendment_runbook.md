# CPU-only evaluation-source amendment commands

These commands do not launch models, obtain credentials, download sources, submit
jobs or approve a cohort. No Colab or sbatch work is needed for this review.

## Inspect the existing local blocked review

From the repository, with the existing package environment:

```bash
export PYTHONPATH=src
python -m pact evaluation-source validate --run-dir results_import/evaluation-source-amendment-v2-final-reviewed
python -m pact evaluation-source export --run-dir results_import/evaluation-source-amendment-v2-final-reviewed
python -m pact evaluation-source acquisition-plan
```

The last command prints unresolved materialization prerequisites; it does not
fetch anything. The first two use the review created during this implementation.

## Create a new CPU audit from genuinely available evidence

Use a new empty output directory. Preserve both the exact parent bundle and its
previously validated extraction. Existing local paths are:

```bash
python -m pact evaluation-source audit \
  --run-dir results_import/evaluation-source-amendment-v2-next-review \
  --parent-dir results_import/stage1-final-audit-1793033718300732417 \
  --parent-bundle results_import/pact-revival-stage1-evaluation-amended-002-PRIVATE-1793033718300732417.zip
```

Without new source/exposure evidence this produces a precise BLOCKED review, not
an experiment. Add the following only after actual approved local material exists:

```bash
python -m pact evaluation-source audit \
  --run-dir /private/new-empty-amendment-review \
  --parent-dir /private/verified-stage1-parent \
  --parent-bundle /private/exact-stage1-parent.zip \
  --openbook-file /private/approved-main-train.parquet \
  --source-spec /private/reviewed-source-spec.json \
  --data-dir /private/original-train-validation-cache \
  --exposure /private/current-reviewed-exposure.json \
  --history-receipt /private/reviewed-external-stage2-history.json \
  --history-root /private/available-prior-stage2-history
```

This second block documents the implemented interface; its `/private/...` arguments
are placeholders requiring real reviewed files. Do not create empty substitute
inventories or approval JSON. Runtime source paths must remain private; the CLI
allows only storage outside Git or the explicitly ignored/untracked local
`results_import/` evidence area. It refuses overwrite and symlink destinations.

The OpenBookQA source specification has fields `repository`, `config`, `split`,
`revision` (full immutable 40-hex upstream commit), `path` (main/train file identity),
`format` (parquet or curated jsonl), `sha256`, `expected_rows` (4,957),
`identity_review`, `rights_review`, and `logiqa_rights_review`.
The subsequent [source-access review](stage2_evaluation_source_access_review.md)
records an upstream commit and advertised file digest. Actual file bytes remain
unavailable and unverified; the candidate JSON contains no approval receipts.

An independent reviewer supplies identity-review receipt bytes binding the
`source_identity_sha256`, `official_origin_verified` and `reviewed_by_human`
findings; `identity_review.receipt_file` and `receipt_sha256` must verify. A rights
review requires local terms files (`url`, `sha256`, `local_file`) and an actual
`review_receipt_file`/`review_receipt_sha256` binding that source, the exact terms,
`approved_for_proposed_use`, human review and item scope. These field descriptions
are not approval receipts. LogiQA rights bind its existing full registry entry
with `family: logiqa`, not the OpenBookQA identity.

Exposure additionally binds `experiment_ledger_sha256`, `parent_source_sha256`,
`coverage: all_prior_used_and_protected_project_groups`, and the actual finding
`material_overlap_review: no_unresolved_cases`, alongside the existing complete
benchmark-ledger inventory. Review evidence must support those assertions.
External-history receipt uses the existing v3 exact-parent/source contract;
unknown prior probe consumption remains a blocker.

## Separately approved source materialization

There is no automatic downloader in this child. Before acquisition:

1. Independently identify the official immutable main/train file and expected
   digest; review its provenance and source rights. Do not use `additional`,
   validation, test, a moving revision or an unreviewed converted mirror.
2. Present that exact file, byte cap (20 MiB), digest and terms for a separate
   explicit user acquisition decision. The pinned metadata candidate is now documented, but rights approval
   remains unresolved.
3. After approval, manually supply the one approved file or a documented curated
   snapshot. Record transformation/source provenance if JSONL is curated.
4. Run the local audit above. Its hash/schema/rights checks precede eligibility.
   Existing original training/validation caches must also be available; no new
   LogiQA fetch occurs through this command.

Source acquisition approval is distinct from cohort approval. A selected candidate
still requires human cohort review, native tensor/reload/context checks, historical
consumption reconciliation, complete runtime request freezing and later explicit
GPU authority. None is granted by a successful CPU audit.

## CPU tests and invented end-to-end demonstration

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_evaluation_source.py -v
PYTHONPATH=src python -m unittest discover -s tests -p test_training_data.py -v
PYTHONPATH=src python -m pact evaluation-source mock --run-dir /tmp/new-empty-evaluation-source-fixture
```

The mock command imports invented OpenBookQA JSONL and original-format LogiQA text,
uses real canonicalization/exclusion/selection/graph/scoring code, and exports
PRIVATE/SANITIZED fixture bundles. It runs no model backend. To reconstruct a bundle:

```bash
python -m pact evaluation-source reconstruct \
  --bundle /private/review-PRIVATE.zip --sha256 FULL_VERIFIED_SHA256 \
  --run-dir /private/new-empty-reconstruction
```

Expected artifacts: `audit.private.json`, `lineage.private.json`, `source.private.json`,
`method.private.json`, `summary.json`, `acquisition-plan.json`; candidate and graph
files appear only if supported. Fixture runs also contain mock outcomes/report.
Bundles are under `bundles/`. PRIVATE contains sensitive data; share SANITIZED for
aggregate review. No real training/inference command exists in this amendment CLI.
