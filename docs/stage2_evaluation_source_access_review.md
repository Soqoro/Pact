# Stage II evaluation-source access review — 2026-10-28

Decision: a concrete OpenBookQA file can now be proposed for acquisition, but the
64+64 cohort remains unverified. No source bytes were fetched, no eligibility was
asserted, and no acquisition or execution approval was recorded.

## Proposed single-file identity

- Repository/config/split: `allenai/openbookqa`, `main`, `train`.
- Immutable revision: `388097ea7776314e93a529163e0fea805b8a6454`.
- File: `main/train-00000-of-00001.parquet`.
- Advertised payload SHA256: `98148f8a54e62eb862346a75192d5fb824d6cbb68f2f59aecd793d39ecb5cd8b`.
- Advertised payload size: 495,845 bytes; expected rows: 4,957.

These are upstream metadata claims, not locally verified payload properties.
The [official commit](https://huggingface.co/datasets/allenai/openbookqa/commit/388097ea7776314e93a529163e0fea805b8a6454)
records the train-file LFS digest/size and the main/train row count. The
[file metadata page](https://huggingface.co/datasets/allenai/openbookqa/blob/main/main/train-00000-of-00001.parquet)
also advertises the same payload digest. The proposed acquisition must use the
immutable revision above, never the moving `main` branch. No validation, test,
additional configuration, remote loader script or archive-wide acquisition is proposed.

The machine-readable [candidate specification](stage2_openbookqa_source_candidate.json)
contains empty identity/rights review fields deliberately. It is not a human
review receipt or a frozen eligible cohort.

## Rights and remaining evidence

The official Hugging Face dataset card currently reports `license: unknown`.
The [upstream code repository LICENSE](https://github.com/allenai/OpenBookQA/blob/main/LICENSE)
is Apache-2.0. This review does not infer that the code license resolves the rights
of every question or permits all proposed data redistribution. An actual human
review must establish applicability to the specific dataset and proposed private
closed-book research use, retain the terms bytes, and supply the required receipt.
Do not manufacture an approval assertion from these links.

Original English LogiQA raw bytes, its rights evidence, and a current project
exposure audit remain prerequisites. Historical exclusions, semantic/content-group
uniqueness, external Stage II consumption reconciliation and checkpoint verification
remain unchanged. Project-unexposed status would not establish absence from
pretrained-model training data.

## Implemented CPU command and observed outcome

```bash
PYTHONPATH=src python -m pact evaluation-source acquisition-plan \
  --source-spec docs/stage2_openbookqa_source_candidate.json
```

Executed successfully. Output: `PROPOSED_ACQUISITION_ONLY`, `approved: false`,
`network_requests: 0`, one-file limit, 20 MiB safety cap. Remaining acquisition
blockers: `separate_source_access_approval_required` and `source_rights_unresolved`.
This command validates metadata shape, not payload authenticity or legal rights.

Next decisions are separate: resolve the source-use review; explicitly approve
acquisition of this exact single file; then audit actual local bytes and both
sources' eligibility. Cohort approval and GPU execution would require later,
separate decisions. Existing Stage II v3 remains blocked. No completed Stage I
artifact or previously exported CPU review was rewritten.

This follow-up changes documentation and metadata only. The previously executed
57 CPU tests are historical implementation evidence; they were not rerun here.

## Follow-up official documentation review

The official [Ai2 dataset landing page](https://allenai.org/data/open-book-qa)
redirected to the Hugging Face dataset page. Its licensing-information section
still requests more information. The upstream GitHub README describes the repository
as model/experiment code and offers download instructions; those instructions do
not settle the dataset-item rights question. No additional applicable dataset-use
permission was established by this review. Status remains `source_rights_unresolved`,
not a finding that research use is prohibited.

The landing-page redirect unexpectedly returned a public `additional/train`
viewer preview. No dataset file was downloaded, but this was content exposure,
not purely metadata. The returned excerpt exposed these OpenBookQA IDs:
`7-980`, `7-584`, `7-870`, `7-321`, `9-732`, `9-782`, `9-87`, `155`, `1046`.
Do not treat these as project-unexposed candidates. A refreshed exposure inventory
must conservatively exclude their matching main/config content groups and document
any uncertainty about further preview coverage before selection. No question text
or answers are copied into this report. Avoid dataset landing/viewer URLs in further
metadata checks; use exact README/LICENSE/commit metadata pages.

### Human review handoff

A source-owner or qualified project reviewer needs to establish whether the
specific OpenBookQA main/train release may be downloaded and used privately for
this closed-book development evaluation, and what attribution, sharing or other
conditions apply. Record the applicable terms or written permission and their
scope; no contact has been sent on the user's behalf. The same evidence is needed
for original English LogiQA. An assertion of approval without supporting evidence
must not be substituted for that review.

The governing reviewed brief explicitly says: “Human/source-owner resolution is a
separate review decision before activation” and conditions materialization on
“separate approval of source access and rights.” The implementation cannot resolve
this remaining prerequisite from the currently available public documentation.
