# Completed curated helpful-peer diagnostic — 2026-09-20

The returned run passes the offline artifact audit for all **32/32 revision
calls**. Correct receiver answers rise from **0/16 with original peers to 8/16
with curated help**, entirely on the moon task. **Zero within-prompt preference
pairs** are available. This closes the fixed diagnostic; full revision training
remains unsupported.

## Integrity and execution

Archive `qwen3-curated-repair-001-handoff-1789919214853319498.zip`, 217,060 bytes,
SHA256 `c06a1cff473841c7271f2c07e61f6e0a61b31c76b982361f4ddeb029917ea3b4`.
All 106 safe archive members, 105 payload checksums and 168 inventory entries
pass. The 64 omitted shard checksum markers reconstruct from original JSON bytes.
Imported content was treated as data; no imported code was executed.

Clean source commit `43151280b2b4c01a1461445878c3a544dad397db` and executable hash
`5070895320fa98c4bb44ffbf673ba525aadc4f0bb414406f641983ae9c9399bb`
match the reviewed local implementation. Both parent archives reconstruct the
complete executable plan exactly. Frozen config/context hashes remain
`ac29ebf94ee954729923ed7d72c8e474cf165e48a289a545fe0e8b6a002587d4` and
`66ff6a758fdc8226fde3fcb2e78aced0dfec059041c50bac883efaa102da65ab`.

All three saved private states, donor identities/provenance, outgoing replacement
bytes and matched arm seeds are preserved. All 32 journal intents have verified
results and derived records. Offline cache replay reconstructs every request
without generation. Actual saved token prefixes agree with the eight preflight
contexts and within each pool; lengths are 353–430 input tokens, safely within
the 4,096-token context with 256 reserved output tokens. Model, frozen adapters,
template, BF16/SDPA, disabled thinking and reported L4 runtime identity match
the parent runs. Sampling remains temperature 0.7, top-p 0.8 and top-k 20.
The full report recomputes exactly; independent raw-answer counts agree.

## Results

Each row contains two recipients × four samples. These are repeated samples on
two post-selected ARC tasks, not 16 independent tasks.

| Task | Original peers | Curated helpful peer | Correctness change |
|---|---|---|---|
| Thermal pollution: `Mercury_406916` | 8 abstentions, 0 correct | 8 valid-wrong B answers, 0 correct | 0/8 → 0/8 |
| Moon classification: `Mercury_7210613` | 8 valid-wrong D answers, 0 correct | 8 correct C answers | 0/8 → 8/8 |
| Total | 0 correct, 8 wrong, 8 abstentions | 8 correct, 8 wrong, 0 abstentions | 0/16 → 8/16 |

All 32 completions end at EOS. There are eight explicit abstentions, no malformed
or invalid-answer outputs, and no length/context failures. Abstentions remain
task failures and cannot serve as valid-wrong preference counterparts.
Across 16 corresponding seed comparisons, eight failures become correct and
eight remain failures; no initially correct receiver sample exists in the
original arm. There is no missing comparison.

The eight four-sample pools contain: two abstention-only original pools on the
thermal task; two wrong-only curated pools on that task; two wrong-only original
pools on the moon task; and two correct-only curated pools on the moon task.
No pool contains both valid correctness classes. There are **0/8 within-arm
pairs and 0/4 curated repair pairs**. Pairing a correct curated output with a
wrong original output would violate the same-prompt requirement.

All 32 raw responses were inspected. Original thermal responses describe
conflicting peer reasoning and abstain. With the recorded correct donor, they
instead endorse increasing river temperature (wrong B), sometimes rejecting the
correct A advice explicitly. Original moon responses endorse the wrong
light-reflection criterion; curated responses select orbiting a planet (C) and
refer to the helpful sender. These textual explanations are descriptive evidence,
not a verified account of internal reasoning or proof that a receiver did not
independently re-solve the task.

## Interpretation and decision

The predeclared outcome is `curated_help_without_pairs`: the particular message
intervention supplies useful correction on one task, but supplies no within-prompt
correct/wrong preference support. The thermal case shows that correct peer text
is not sufficient for correction on every selected case; replacing abstention
with a wrong answer is not an accuracy improvement.

This result does not establish population efficacy, natural repair prevalence,
hold support, LogiQA coverage, terminal team accuracy or correctness-only causality.
The two donors differ in provenance (private versus exchange revision), content
and length, and cases were selected for observed wrong states plus available
correct donors. Do not treat the aggregate 50-percentage-point sample difference
as a general accuracy gain or report confidence intervals across the 16 draws
as if they were independent tasks.

Close this 32-call diagnostic without extending its sample cap or changing seeds.
No scoring/training stage is unlocked. Any further donor acquisition, actor
preparation or preference-supply experiment needs a separate bounded design.
No additional GPU run is scheduled by this audit.

## Resources and persistence

One invocation, 32 new calls, zero cache hits, unresolved attempts or missing
records. No private generation, readout, teacher-forced scoring or optimization.
Input/output tokens: **12,392 / 1,787**, below the 8,192-output-token ceiling.
Invocation time: **249.594 seconds (4.16 minutes)**, including 55.911 seconds
model loading; final persistence is outside that timer. Summed generation time:
129.298 seconds. Peak allocated/reserved bytes: 16,685,571,072 / 16,770,924,544.
Compute units are unknown.

The handoff reports verified snapshot
`/content/drive/MyDrive/PACT/curated-repair/qwen3-curated-repair-001/snapshots/1789919214806955396-1edfd59d13d4`.
The user supplied the final Drive bundle path and matching outer checksum.
Nested receipt path/hash/size refer to the preceding local review ZIP; its null
bundle field and manifest's false persistence flag predate final copying and
verification. They do not indicate a failed handoff. Current Drive contents and
GPU reset/resume remain independently unverified. Preserve the durable objects.

Original bytes: `results_import/qwen3-curated-repair-001-review/`.
Reproducible audit, recomputed report, raw-response table and evidence hashes:
`results_import/qwen3-curated-repair-001-analysis/`.
No local model/tokenizer numerical reproduction, independent tensor verification,
new model download, GPU invocation or final-test access occurred. This review
changes documentation only; no application test-suite rerun was needed.
