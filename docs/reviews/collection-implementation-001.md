# Collection implementation check — 2026-09-19

The bounded train-only collector, frozen-reference loader/scorer and exact
snapshot recovery pass local CPU checks. No Qwen3-8B weights, GPU run or final-test
data were used. The completed warm-start metadata audit remains separate evidence.

The default suite has 90 tests: 85 pass and five explicitly optional neural tests
skip. With the existing user authorization for tiny CPU neural checks, all 90
pass. The isolated environment is `/tmp/pact-reference-cpu`: CPU torch 2.9.1,
Transformers 4.57.6, PEFT 0.18.1 and Accelerate 1.12.0. The opt-in invocation sets
`PACT_TEST_NEURAL=1`, hides CUDA and disables model/dataset hub access. Models are
small random initializations; package installation does not download pretrained
weights. Retained local evidence is under ignored
`results_import/collection-implementation-001/`: suite logs, dependency inventory,
CPU-build assertion, source identity and the actual frozen-data collection plan.
The tested uncommitted source hash is
`17a43e51f98f28f5e01ec96f85ee4054bcdefb5a035f265bdf1fbe3217dc1e52`,
based on Git HEAD `a277794d271720665d57308cc15f3122f1934e27`.
`verification.json` records evidence checksums and confirms the recipe's reference
pins against the returned metadata; the guide's Python cells compile locally.

Nine added checks cover:

- Plan-only CLI behavior, fixed train-task selection, caps and invalid recipe/split rejection.
- Raw paired continuations, identical suffix seeds/attacks, unchanged other private
  packets and unadapted final readout; interrupted shard resume preserves hashes.
- Explicit synthetic provenance, invalid/length candidate accounting and missing
  hold/repair pairs without fabricated counterparts.
- Reference file/manifest/hash/architecture checks and symlink rejection before load.
- Actual tiny-model causal log probabilities against an independent log-softmax
  calculation, completion-only masking and summed EOS scoring.
- Actor mutation changes actor logits while reference scores, reference tensors
  and disabled-adapter base logits stay unchanged. Active adapter, modes and
  gradient flags are restored, including after a failed forward.
- Sampled token IDs survive generation even when decode/re-encode would differ;
  overflow clears the previous generation's token data.
- Cache idempotence/corruption rejection, identity checks and zero-preference
  execution without loading a model.
- Model-load failure diagnostics, timed storage failure, compatible continuation,
  immutable complete bank, zero-call repeat, verified snapshot/bundle and restore
  into a new directory; existing restore destinations are rejected.

One fixture initially exposed a source/destination ZIP-path collision when scratch
and durable directories shared a parent. Persisted collection bundles now live
inside the durable run's `bundles/` directory; the round trip passes. Synthetic
handoffs explicitly retain `scientific_status=synthetic_fixture`.

The actual frozen training-data plan selects `arc_challenge:MCAS_2004_5_13` and
`logiqa:train-7374`, with six scheduled records and no model load. Config hash:
`ac116738ffc68e08ce5471a7d4d2dfda4226fc26cb4a4465ed765a6615c4cb88`.
The immutable reference manifest digest is
`ea4a62c215324b721d259bc3b7f104fa30fd2786548055ebbfd8f0f95837e963`.
The three adapter hashes are pinned in the configuration and previously audited
from the returned warm-start inventory. Actual exported tensor bytes remain on
Drive; no local test claims to have reloaded those real exports.

This check validates implementation behavior, not scientific outcomes or GPU
memory fit. The proposal's larger bank, sparse-support sampling, refreshes, joint
optimizer and full study remain deferred. Review/publish the increment before the
first bounded Colab record; return its handoff before continuing all six records.
See [the collection guide](../collection.md).
