# Training-data preparation

Train-only loaders and frozen task manifests are now implemented and verified on
the pinned ARC-Challenge and original English LogiQA files. This is data preparation,
not warm-start training, a replay bank, or evidence of PACT performance.

## Commands

From the repository root, after installing the optional data dependency:

```bash
python -m pip install -e '.[data]'
python -m pact prepare-training-data \
  --cache-dir scratch/cache/training-sources \
  --output-dir scratch/prepared/engineering-12 \
  --items 12 --seed 20260918 --download
python -m pact inspect-training-data \
  --data-dir scratch/prepared/engineering-12
```

The explicit `--download` flag allows fetching four pinned training/validation files.
Without it, missing cache entries fail offline. Files have a 20 MiB individual bound,
fixed SHA256 checks and exact row-count checks; incompatible cached files are rejected,
never silently replaced. `--items` and `--seed` are required. Counts must be even and
between 2 and the proposal's 1,200-task target; insufficient post-audit family counts
fail rather than silently changing balance. Existing output directories are rejected.

No Colab invocation is needed for this step. Default unit tests use synthetic fixtures
and require neither network nor PyArrow. The real-source audit used PyArrow 22.0.0
installed only under `/tmp`, without changing the base environment.

## Verified sources

Use the same source revisions as the validation pilot. The
[AllenAI dataset card](https://huggingface.co/datasets/allenai/ai2_arc/blob/210d026faf9955653af8916fad021475a3f00453/README.md)
declares ARC-Challenge split sizes and CC-BY-SA-4.0 metadata. The
[original LogiQA release](https://github.com/lgw863/LogiQA-dataset/tree/ff6c4cbca47627b3ac2da94a29fa28204a167b41)
identifies `Train.txt` as English training data and documents the eight-line format.
Its licensing remains unresolved as already recorded; no new license grant is inferred.

| File | Parsed rows | Bytes | SHA256 |
|---|---:|---:|---|
| ARC-Challenge training parquet | 1,119 | 189,909 | `e488c1587ffdcfc8443f916c53488a95cd471c5790e0746c6bfe4cecf20962cb` |
| Original English LogiQA Train.txt | 7,376 | 6,281,272 | `7d5bb1f58278e33b395744cd2ad8d7600faa0b3c4d615c659a44ec1181d759fa` |
| ARC-Challenge validation parquet | 299 | 55,743 | `395a5c88d1580d69855fbaee9450270578df1ad5af6259771cd0a42c20e99f05` |
| Original English LogiQA Eval.txt | 651 | 550,021 | `4c49e6753b7262c001506b9151135abf722247035ab075dad93acdea5789c01f` |

ARC revision: `210d026faf9955653af8916fad021475a3f00453`.
LogiQA revision: `ff6c4cbca47627b3ac2da94a29fa28204a167b41`.
Exact download URLs are in `src/pact/training/data.py` and the generated manifest.
No final-test file was downloaded or parsed.

## Split and overlap rules

The training command loads the full 8,495 training and 950 validation records before
selection. Existing public validation parser/normalizer entry points remain
validation-only. Train parsers share their implementation while assigning the train
split directly; they do not relabel imported pilot records. LogiQA uses `train-NNNN`
source IDs, separate from existing `eval-NNNN` IDs. Original option labels and
canonical answer mapping survive normalization. Labels remain in separate records.

Audit rules are fixed before selection:

- Link identical source IDs within a family, or identical normalized content groups
  (context, question and sorted option texts, ignoring case/punctuation).
- Also link lexical near copies with word-trigram set Jaccard similarity at least
  9/10. Include context, question and sorted option texts. Form transitive components
  across both splits and families. Stored near-copy edges describe component-building
  links, not an exhaustive list of similar pairs.
- Exclude every training member of a component touching validation. Quarantine
  conflicting exact-duplicate labels, comparing normalized correct **option text**
  so reordered choices do not create a false conflict. Otherwise retain the smallest
  task ID as one representative of each training component. Log every removed row.
- Rank eligible components by `SHA256(seed, component identity)`, select half the
  requested count from each family, then deterministically order the result. Smaller
  selections at the same seed are nested in larger ones. No correctness/eligibility
  outcomes from model runs influence this selection.

The full-file audit excludes 59 redundant training rows: one ARC and 58 LogiQA.
There are 58 training duplicate components, 15 exact-content links and 44 additional
lexical links. No label conflicts or train–validation matches occur under these rules.
Eligible pools are 1,118 ARC and 7,318 LogiQA tasks, sufficient for 600 per family.
This lexical screen **does not establish absence of semantic paraphrases**; that audit
remains explicitly unperformed. Final-test overlap auditing also remains unperformed.

## Frozen artifacts and evidence

Preparation writes `tasks.json`, separate `labels.json`, `overlap_audit.json`, and
`manifest.json`. The manifest pins source descriptions, full train/validation pool
hashes, seed, selection policy, per-task input/label hashes, group IDs and audit hash.
Checksums are published last, after payload reads, hash checks and schema/provenance
validation. Inspection rejects missing markers, corrupt payloads, wrong splits,
excluded tasks, changed source identities, missing labels or family imbalance.
These are integrity checks, not a cryptographic attestation of arbitrary supplied
bundles; future training must pin a reviewed manifest hash and retain source evidence.

Local evidence is under `results_import/training-data-001/`:

- `engineering-12/`: 6 tasks per family, seed 20260918. Manifest hash
  `2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e`.
- `proposal-1200/`: 600 per family at the same seed, with the engineering selection
  nested inside. Manifest hash
  `92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a`.
  This establishes data availability only; no model run is launched by these commands.
- `source_audit.json`, `validation_compatibility.json`, `tests.log` and
  `verification.json`: checksums, counts, exclusions, tests and source identity.

The original 80-item pilot validation manifest reproduces exactly after the shared
parser refactor (hash `8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495`).
Current snapshots remain immutable; no prior pilot result or selected task changes.

The next local increment now implements a bounded [warm-start optimizer and snapshots](warmstart.md),
with checkpoint/resume control checks and tiny CPU neural verification passed. Real reference
scoring and scored-bank collection remain outstanding. GPU training is deferred.
