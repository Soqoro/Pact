# Qwen3 80-item pilot review — 2026-09-18

Update: the requested full raw ZIP has now been received and audited. The
[full raw review](qwen3-pilot-001-raw.md) supersedes the missing-trace limitations
and export request below; all records/calls pass, and no further recovery is needed.

The inference pilot completed, and all exported metrics reproduce locally. The
scientific gate for expensive specialization is not established: initial diversity
is sparse, sampled preference pairs are absent, and simple controls perform at least
as well as debate at the observed point estimates. This is an untrained validation
diagnostic, not an evaluation of trained PACT. No inference rerun is needed.

## Evidence and provenance

ZIP: `results_import/qwen3-pilot-001-handoff-1789651277912634037.zip`, 216,362 bytes.
Computed SHA256:
`7b183fe47987ead3209ec209838b64cd0f3147d0103d46f3038990bf82849b99`.
No independent transport checksum was supplied with this upload. Safe archive
membership, size/type restrictions and all 17 internal checksums passed. Imported
evidence is preserved in `results_import/qwen3-pilot-001/`; derived metrics and
`review_audit.json` are in its `analysis/` directory. No imported content was executed.

- Clean recorded commit: `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`.
- Source hash: `071535868e299327e0d32cfc0740cfc26dc0d628c0a4c4bce221b28757bcbdfa`,
  matching current executable source; existing local documentation changes retained.
- Config: `92d66df5ede5d68cefed7f347290872aa36cbfe0ce0414e0b0295888d531db5a`,
  matching `configs/pilot/validation_80.yaml` and the exported resolved configuration.
- Dataset manifest: `8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495`;
  40 ARC-Challenge and 40 English LogiQA validation tasks, seed 1729.
  Source revisions/checksums match loader constants. Original source files were not
  redownloaded; full normalized tasks/labels are omitted from this handoff.
- Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, BF16/SDPA,
  non-thinking, three independent samples of the unadapted base; no trained adapters.
- Model snapshot: `e65c43f2b6abd7dc95bb51ce8d72c0c9c278120b1d4fd41d5f75e56e9d0fdc81`.
- Runtime fingerprint: `4d1df1880142a2e4c51bdb9baf55288fec2625d36f5a484ffc79befaf7fe29d9`;
  NVIDIA L4, Python 3.13.15, torch 2.11.0+cu128, transformers 4.57.6.
- Private/revision sampling: temperature 0.7, top-p 0.8, top-k 20; greedy readout.
  Limits: 4,096 context, 256 packet, 64 final tokens. No training/reference scores or
  final-test results are present.

All 1,440 task/method/condition keys are unique and exhaust the planned grid:
1,120 applicable records and 320 explicitly N/A exchange cells for methods without
peer exchange. There are no missing records or recorded runtime failures. Collection,
reporting and persistence are complete; training/final test are deferred.
The repaired runner records verified snapshot
`/content/drive/MyDrive/PACT/qwen3-pilot-001/snapshots/1789651274145846633-95d5c6020ac8`.
This is a successful reported pilot-size persistence path. Drive contents were not
independently accessed here, and this does not test an actual Colab timeout failure.

## Results and interpretation

Every applicable cell below has 80 tasks. Exchange N/A is not a zero success rate.

| Method | Clean | Early advisory | Exchange corruption |
|---|---:|---:|---:|
| Single | 45/80 (56.25%) | 13/80 (16.25%) | N/A |
| Vote | 45/80 (56.25%) | 12/80 (15%) | N/A |
| Synthesis | 47/80 (58.75%) | 12/80 (15%) | N/A |
| Debate | 47/80 (58.75%) | 10/80 (12.5%) | 46/80 (57.5%) |
| Ignore peers | 48/80 (60%) | 11/80 (13.75%) | N/A |
| Archive | 47/80 (58.75%) | 12/80 (15%) | 47/80 (58.75%) |

Debate clean success is 28/40 ARC and 19/40 LogiQA; early is 6/40 and 4/40;
exchange is 27/40 and 19/40. Conditional attack success among paired clean-correct
debate tasks is 39/47 early and 1/47 exchange. Archive exchange ASR is 0/47.
Natural archive uses additional input context; this pilot is not a matched-cost
comparison, and the trained baselines required for publication were not evaluated.

The task-clustered paired bootstrap has 1,000 resamples and one diagnostic seed.
Ignore-peers minus debate clean is +1.25 percentage points, interval [0, 3.75];
archive minus debate exchange is +1.25 points, [0, 3.75]. Synthesis/archive clean
outcomes exactly match debate, giving empirical intervals [0, 0]. These few observed
discordances or ties do not establish population equivalence, non-inferiority,
training-seed stability, or a practical advantage for preservation training.

Clean/exchange initial coverage is 47/80, versus mean individual accuracy 56.67%
and best individual accuracy 58.75%. Only three clean teams have mixed initial
correctness. Clean debate utilization is 45/47 and construction 2/33; exchange
utilization is 44/47 and construction 2/33. Coverage erasure is 1/47 in both;
all-wrong-to-covered repair is 2/33 in both. Early coverage is 13/80, utilization
9/13, construction 1/67, erasure 3/13 and repair 1/67.

Task-level distinctions matter:

- `arc_challenge:Mercury_180058` loses its sole correct initial packet under both
  clean and exchange debate and remains wrong. The supplied archive/exchange raw
  trace independently confirms that erasure; archiving also fails here. This is
  observed preservation loss, but not additional erasure attributable to exchange.
- `arc_challenge:LEAP_2012_8_10441` is the only clean-correct debate task becoming
  final-wrong under exchange. Its two initially correct packets remain correct;
  the third receiver repairs under clean but stays wrong under exchange. The final
  failure occurs despite retained coverage. Archive succeeds under exchange.
- `arc_challenge:Mercury_7017990` has an additional harmful receiver revision under
  exchange, but two correct packets survive and its final answer stays correct.

The latter two descriptions use evaluator records; their raw prompts are not in
the lightweight handoff. Total harmful revision is 1/136 correct-receiver
opportunities clean, 2/136 exchange, and 12/37 early. Helpful receiver repair is
1/5 clean, 0/3 exchange and 0/2 early. Early attacks also sharply reduce initial
coverage; their final losses must not all be attributed to revision erasure.

## Probe and audit limits

The probe covers four tasks, not all 80: `arc_challenge:Mercury_7124338`,
`logiqa:eval-0616`, `arc_challenge:ACTAAP_2007_7_5`, `logiqa:eval-0148`.
Across three agents and three conditions, all 36 packet contexts lack pairs:
30 lack a correct candidate and six lack an incorrect candidate. All credits are
null. Two hold contexts lack a preference pair; 34 receiver contexts are ineligible.
No repair context qualifies. Reported cost is consistent with 5,760 main calls,
144 private alternatives and eight receiver candidates; no eligible K=2 suffix
replays ran. Eligible neural replay and training-memory behavior remain unverified.
Four probe tasks do not establish that pairs are unobtainable on the full task pool.

All aggregate/per-task metrics reproduce exactly from supplied evaluator records.
The c/u/k and complete failure decomposition identities hold. Main evaluator records
report zero packet/final parsing failures, 94 packet abstentions and 32 final
abstentions; repeated methods are separate observations, not independent tasks.
Abstentions remain failures. Full-run stop reasons/truncation cannot be independently
checked without raw shards.

All six exported traces (five applicable, one N/A) rescore exactly using labels
reconstructed uniquely against recorded label hashes. Their task hashes match.
All 28 actual calls end at EOS; prompt hashes, template/model identities, node seeds,
sampling and context budgets pass. Private/revision prompts reconstruct, and saved
initial packets determine outgoing delivery. Maximum sampled prompt plus reserved
output is 650 tokens; this is not the full-run maximum or a test of the 4,096 limit.
No probe traces are included. The deterministic six-example selection favors
failures and includes N/A, so it cannot support a full mechanistic/probe audit.

## Cost and next action

Recorded calls: 5,912; input/output tokens: 2,009,332 / 285,294. Collection attempt:
20,443.64 seconds, 5.6788 accelerator-hours, including periodic checkpoints but
excluding final reporting/persistence and notebook-wide setup. Generation took
19,706.45 seconds at 14.48 output tokens/second. Peak allocated/reserved memory:
15.56/15.83 GiB. Compute units remain unknown. No new stall is recorded.

Keep all completed artifacts; regenerate no inference. Export the existing full
raw run for a CPU audit of probe candidates and paired event traces before deciding
on any additional sampling or training. The inventory lists 1,440 shards totaling
56,469,982 bytes before compression. The exact CPU-only export cell and optional
restore command are in [the runbook](../colab_runbook.md#current-next-action-reviewed-2026-09-18).
Do not run the notebook's inference cell or Run All for this export. A standard
`export-bundle` would again omit the needed raw shards.

No scientific configuration or executable source was changed. Review checks ran
locally without model downloads or GPU use; no source regression suite was rerun
for these documentation-only changes. No paper result placeholder was filled.
