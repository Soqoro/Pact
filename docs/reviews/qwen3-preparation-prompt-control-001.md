# Completed 72-call prompt diagnostic — 2026-09-22

The returned archive passes the offline audit. Answer-only prompting yields the same
45/72 correctness as the prepared actors' packet prompts. All 72 outputs follow the
answer-only schema. Four answer IDs change, but all four remain wrong. Close the fixed
diagnostic: no accuracy benefit is observed on this reused training-development slice.
Full PACT readiness remains false.

## Integrity and comparison

Bundle: `qwen3-preparation-prompt-control-001-handoff-1790038795500928454.zip`.
SHA256: `a48bfe31276a58479d80780db48226ef55d3d1d85526f530e435bc497535db34`.
Size: 581,409 bytes. All 226 safe archive members and 225 payload checksums pass;
368 inventory entries reconcile, including 144 reconstructed shard checksum markers.
Clean source: `8d57861f0623bda7df0bd553fbdbb201cd611907`, executable hash
`57b2af43b35cc83d7d8ae82a82a5d3238b1512fe13130b7df8a3f4ac2c4501d7`.

The frozen plan reconstructs from the pinned completed training and prepared-probe
ZIPs. Request hash remains
`69059c28cc3f9ab6558124c65c250814cc1e864c392ae816b67fef5857c9ad63`.
The model, final adapter identities, runtime, task/agent/seed assignments, template and
sampling parameters match. The comparator is the completed **prepared-actor packet
probe**, not the earlier engineering actors or seed-1729 draw. Only prompt/response
contract changes. Labels remain outside defender messages.

All 72 intents have results. Offline journal replay reconstructs each call and record
with zero model execution, verifies token prefixes, lengths, EOS and context bounds,
and exactly reproduces the complete report. There are no unresolved attempts, missing
records, cache hits, teacher-forced forwards, receiver calls or optimizer updates.
Strict packet and answer-only parsers are applied to their respective arms.

## Results

| Measure | Prepared packet prompt | Answer-only prompt |
|---|---:|---:|
| Overall correct | 45/72 (62.5%) | 45/72 (62.5%) |
| ARC Challenge correct | 24/36 (66.7%) | 24/36 (66.7%) |
| LogiQA correct | 21/36 (58.3%) | 21/36 (58.3%) |
| All-correct teams | 15/24 | 15/24 |
| Mixed-correctness teams | 0/24 | 0/24 |
| All-wrong teams | 9/24 | 9/24 |

Correctness transitions: 45 correct-to-correct and 27 wrong-to-wrong; no improvements
or regressions. Exact answer IDs agree for 68/72 responses. All three agents on
`arc_challenge:Mercury_7210613` change from wrong D to wrong B. Agent 1 on
`logiqa:train-5656` changes from wrong B to wrong D. No correct alternative is created.

All 72 new outputs are valid one-key answer JSON, end at EOS, and contain six output
tokens including EOS. There are no abstentions, malformed outputs or truncations.
The output is shorter, but this is not evidence of better reasoning or receiver support.
This experiment generates no receiver candidates, so it does not newly estimate
preference-pair availability; prior missing-pair evidence remains unresolved.

## Resources and recovery evidence

One invocation generated all 72 responses: 14,235 input and 432 output tokens,
within the reserved 18,432 output-token budget. Invocation time: 161.158 seconds,
including 54.615 seconds loading the model; generation time summed to 36.562 seconds.
Final persistence is outside the invocation timer. Peak allocated/reserved bytes:
16,658,328,576 / 16,689,135,616. Compute units remain unknown.

The enclosing receipt reports verified persistence and exit zero; the user supplied
the final Drive ZIP path and matching outer checksum. It also records a compact
inference snapshot. Nested local-ZIP fields predate final bundle copying and do not
identify the enclosing archive. Current Drive contents and reset/resume of this new
run were not independently inspected. The ZIP contains no adapter or optimizer tensors.

## Decision and limits

Apply the prespecified no-observed-benefit branch and close this diagnostic. Do not
extend its seeds/sample cap, change the main communication protocol to answer-only,
or infer that additional warm-start training will solve preference scarcity.

The result does not establish that prompt mismatch never matters. It tests a joint
instruction/format intervention on 24 repeatedly inspected training tasks with one
recorded draw per agent. It does not isolate individual wording or justification
effects, assess generalization, train the full PACT objective, or measure receiver
learning/terminal success. No final-test data were used and no preference pairs exported.
Further work requires an explicit methodological decision, not an automatic new GPU
run: review whether to design a distinct receiver-supervision feasibility intervention
or stop this configuration given the repeated absence of usable within-context pairs.
No new training objective or experiment is selected by this artifact audit.

Evidence: `results_import/qwen3-preparation-prompt-control-001-analysis/`, containing
`audit.py`, `audit.log`, `metrics.json`, `recomputed_report.json`, `verification.json`.
Reproduce on the corresponding source with:

```bash
PYTHONPATH=src python results_import/qwen3-preparation-prompt-control-001-analysis/audit.py
```

No local model/logit/tokenizer reproduction or tensor-byte verification was performed.
This update changes documentation only; no application regression rerun was needed.
