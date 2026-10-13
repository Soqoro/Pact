# Fixed-bank adjudication: frozen rewrite-pool audit

## Verified evidence

Run `pact-adjudication-diagnostic-001`, bundle timestamp `1791814527918178831`.
Unchanged source `8b0f750f29467af84d5ffa9fc30230ce79f3fea1` and plan
`ab855a15eafe32513dda3ae0f2363921683dbbb713bbf4d3286c57d169fc8e3d`.

- PRIVATE SHA256: `0bbc92dd7509b1251d594034e87c27d9815fbf9488a614c35a982172bf02bcd9`.
- SANITIZED SHA256: `e49fbf13fe04528f7fd6e7fc093d09d6746b3d48539ab4d6f0c84ca8d6d0bc4b`.
- Frozen pool hash: `d7b806510441b23547f9ccaa10a194777a0ac0a573b17ae8085dac1c59ea8c05`.

Archive/internal checksums, frozen plan/bank/model/request journal audit and pool
reconstruction passed. Recomputed report exactly matches both returned summaries.
All 2,726 earlier call shards are byte-identical and all clean summary results
are unchanged. All 230 private task IDs are absent from the sanitized archive.
Private extraction and report reconstruction stayed outside Git. No GPU calls or
model downloads were performed locally. This is returned-artifact validation.

## Acquisition results

| Dataset | Attempts | Accepted | Rejected |
|---|---:|---:|---:|
| MMLU-Pro | 210 | 182 | 28 |
| MuSR | 190 | 187 | 3 |
| Total | 400 | 369 | 31 |

| Style | MMLU accepted /42 | MuSR accepted /38 |
|---|---:|---:|
| argument_pressure | 38 | 37 |
| claimed_verification | 40 | 38 |
| claimed_consensus | 40 | 38 |
| claimed_independence | 38 | 38 |
| ordinary_rephrase | 26 | 36 |

MMLU rejection reasons: 23 malformed, three field-mutation/schema failures,
two length failures. MuSR: two malformed and one field-mutation/schema failure.
Rejected variants remain explicit and must not be resampled or replaced.
All accepted variants have status `accepted_unverified_semantics`: acceptance
is a structural contract check, not certification of semantic equivalence,
rationale quality, attack-style fidelity or attack success. In particular,
ordinary-rephrase acceptance does not establish meaning preservation.

Both datasets' 80 task-by-five-style records are frozen before any victim call.
The reconstructed accepted-request plan contains 2,214 victim calls:
182 MMLU variants × three modes × two judges = 1,092;
187 MuSR variants × three modes × two judges = 1,122.
The 186 nominal victim slots corresponding to rejected variants are not
replacement generation capacity. The 2,400-slot report still records all attack
outcomes as unobserved; distinguish this from the accepted-request count.

## Accounting

400 new committed acquisition calls; 204,800 reserved output tokens;
311,225 actual input and 46,153 actual output tokens. MMLU acquisition wall time
921.91 seconds, MuSR 853.42 seconds, including model loads. Rewrite Q now has
real GPU evidence for this runtime. Victim GPU execution remains unverified.

Cumulative: 3,126 attempted and committed calls, zero unresolved; 1,600,512
reserved output tokens; 2,599,433 input and 369,366 output tokens. Recovery safe,
all clean outcomes complete. No training updates or teacher-forced forwards.
Compute units are unreported. Overall scientific ceilings remain unchanged.

## Next prescribed stage

Preflight the now-frozen attacked requests, then evaluate MMLU-Pro/J8 (546
accepted variant/mode requests), followed by MuSR/J8 (561), then the corresponding
J14 stages. Preserve the same source, plan, recipient contracts and clean
references. Reuse rationale-blind controls by exact identity without new calls.
Do not select variants based on victim outcomes. No victim stage was launched
locally, and no new study, training or final-test access follows automatically.
