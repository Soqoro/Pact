# Selective correction: missing exposure inventory resolved

The first Colab preparation stopped because the required private exposure inventory
had not been delivered. No model calls occurred at that stop. The guard was correct;
the previous implementation handoff left this operational prerequisite unresolved.

Produced `/var/tmp/pact-selective-exposure-20261014/prior-exposure.json` (2,283,097
bytes), SHA256 `c1632567b6b1be2d1351f3389e0fcbc474a7aa7eb8abcb10ee2cb125a0d305c7`.
Keep it private and outside Git. It is bound to the current exposure ledger SHA256
`6daac2d8daf1ee830db044c0117363aa319d43ab221def2a75b612032d780dd1` and works with
the existing pushed code `9b65ae343b52777b5b716c9adf090959588b72c3`.

## Evidence checked

Read only existing ID/hash manifests, repository selection inventories and opaque
plan bytes for checksum/metadata-membership verification. No plan task payload was
parsed, protected task text or labels opened, benchmark downloaded or generation run.

Five breadth manifests match the exact historical plan hashes already recorded in
the exposure ledger. Their original four successive prior-exposure indices each
reconstruct exactly from the preceding manifests. Every source sibling, excluded
group and locked partition remains in the exclusion inventory, not only generated
characterization representatives.

| Source | Recorded source rows | Characterization / confirmation / reserve representatives |
|---|---:|---|
| MMLU-Pro | 12,032 | 140 / 140 / 11,357 |
| MuSR | 756 | 90 / 90 / 384 |
| MATH-500 | 500 | 100 / 100 / 295 |
| MBPP+ | 378 | 100 / 100 / 178 |
| GPQA breadth metadata | 164 | 32 / 32 / 100 |

The original GPQA parent metadata additionally contributes all 198 recorded IDs and
groups, validating its original 32/164/2 partition. No protected questions are read
to manufacture new fingerprints. The original parent's extra 34 IDs are covered by
recorded IDs/group hashes; only already recorded cross-dataset fingerprints are
included. This is not an assertion of exhaustive semantic or unknown external
decontamination.

Historical 1,200-task and 12-task training manifests match their recorded hashes
`92771b…` and `2cdbd6…`. The heterogeneous source manifest reproduces the 80-task
validation pilot hash `8a8a95…`. All three repository selection files are included.
The pinned loader still reconstructs/excludes the old 1,200 allocation and full
validation-connected groups before selecting any new training-source group.

The resulting union contains **15,144 task IDs, 14,640 group IDs, 1,280 content
groups, 13,242 recorded cross-dataset fingerprints and 11 provenance receipts**.
`reviewed_complete` denotes completion of this recorded-inventory consistency review;
it is not a human rationale annotation, semantic claim or outcome-dependent screen.

## Implementation and validation

Added `tools/build_selective_exposure_inventory.py` to reproduce this metadata-only
derivative. It rejects changed historical plans, unbound manifests, missing sibling
or partition inventories, broken exposure chains and changed training/pilot hashes.
It refuses an existing output file or a destination within Git. No core method,
generation budget, loader guard or historical run changed.

Executed `PYTHONPATH=src python -m unittest discover -s tests -p
test_selective_exposure_inventory.py -v`: **3 tests passed in 0.060 seconds**.
The real metadata review passed all five plan bindings, four exposure-chain links,
historical training/pilot hashes and the current loader's inventory validator.
`git diff --check` passed. No full model/regression rerun was necessary for the new
metadata-only tool; no GPU, credentials, commit or push occurred.

Next: upload the JSON to
`/content/drive/MyDrive/PACT/selective-correction/prior-exposure.json`, verify its
checksum and ledger binding, then rerun the existing Cell 3. Real allocation may
still report a genuine quota/source issue; this review does not assert the 224-task
allocation or real model execution has already succeeded.
