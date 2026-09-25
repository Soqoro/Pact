# GPQA development exposure and private artifact policy

The only authorized GPQA run is `qwen3-gpqa-diamond-support-001`, a32-item
inference-only development diagnosis. The official storage split named `train`
never authorizes PACT training. No GPQA task, label, continuation, synthetic donor
or preference export may enter training in this update. Warm-start and scored-bank
entry points reject GPQA identities even if their split is relabeled.

Before inference, the frozen private plan records selected IDs/groups, excluded
known exposures/group siblings and protected remainder IDs/groups. The selected32
are `usage=development_diagnostic`, `training_allowed=false`, and
`eligible_for_untouched_final=false`. The nominal166 protected items are not sent
to any model. Their text is read only by deterministic automated identity/grouping
code; only selected32 text is retained in the run. Lexical screening is not a
certificate of absent semantic paraphrases or model-pretraining contamination.

The reviewed prior-use policy is [gpqa_exposure_policy.json](../experiments/gpqa_exposure_policy.json).
It records no prior GPQA run found in the project ledger as of24 September2026.
Known external exposures/groups must be supplied there before the user's review,
push and plan freeze. Changing it later rejects the frozen plan rather than
substituting tasks. No post-hoc sampling, group reassignment or difficulty filtering.

Raw official sources, selected questions/options, gold mapping, full prompts,
continuations and decodable token arrays must remain outside every Git checkout in
private access-controlled storage. Keep notebook outputs private too. Private
ZIPs contain these artifacts; sanitized ZIPs contain computed metrics and hashes
only. The sanitized per-task view excludes answer letters and gold labels. Never
attach a PRIVATE ZIP to a public issue or release. The runner does not configure
Drive sharing permissions on the user's behalf.

A later full198 score must disclose development exposure. A later protected-remainder
score must state its nonstandard selection and denominator. Any later main/extended
training design must exclude all Diamond content/groups reserved for evaluation,
not just the32 exposed tasks. No such follow-up or training is authorized here.


Approved 25 September 2026: exact repeated-option rows and their detected duplicate
groups are source-integrity exclusions before selection. Option comparisons retain
case and Unicode. All198 source identities remain accounted for across selected,
protected and excluded sets; excluded text is not retained in the plan or generated
on. Partition schema v2 records reasons and the eligible-group denominator. With
only the two reported malformed singleton rows, the protected remainder is164,
not166. Neither the exclusions nor their labels become training data.
