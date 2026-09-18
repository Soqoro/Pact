# Selected replay check review — 2026-09-18

The diagnostic completed and verifies eligible neural suffix replay on the reported
L4 environment. All six raw records, 386 calls and 52 suffix branches pass the local
audit. Receiver candidate sampling also executed for both hold and repair, but no
usable receiver preference pair was obtained. No code defect or inference rerun is
indicated. This is selected validation feasibility, not a trained PACT result.

## Provenance and integrity

- ZIP: `results_import/qwen3-replay-check-001-handoff-1789714612508117841 (1).zip`,
  179,664 bytes. SHA256 matches the user's output:
  `21e5133daa634a894357f09658c2a78c5b6bef1bf3d701bcd8d454f7532899cb`.
- Safe member paths/types, membership/size limits and all 17 internal checksums pass.
  All six exported raw records additionally reconstruct the exact size/hash of their
  entries in the raw-shard inventory. No second raw ZIP is needed.
- Clean commit `e79a9ab0da7b3801ba1ff488ddd974302768da2a`; executable source hash
  `c1284a3bcd899fd112f6e63ad856a8a0d64c0dcc0505be0926806864fc84cd8f`, matching local code.
- Config `415be5290ccccc58ad15672a0a33d7693519155d6482a878884fba423c57c611`;
  data manifest `43da504ec1e407835be486b273dbd578be43e97ad76db38d71a809bde1a70cbb`.
  Task/label hashes and original source positions 41/61/70 match the declared pins.
- Unadapted Qwen3-8B snapshot
  `e65c43f2b6abd7dc95bb51ce8d72c0c9c278120b1d4fd41d5f75e56e9d0fdc81`, seed 1729;
  pinned revision `b968826d9c46dd6066d109eabc6255188de91218`, BF16/SDPA,
  non-thinking, temperature 0.7/top-p 0.8/top-k 20, greedy readout.
- NVIDIA L4; runtime fingerprint
  `4d1df1880142a2e4c51bdb9baf55288fec2625d36f5a484ffc79befaf7fe29d9`, matching the
  original pilot. No trained adapters, reference scores or final-test data.
- Six of six applicable records; no missing/duplicate cells or recorded runtime
  failures. Collection/report/persistence complete; training/final test deferred.
  Reported verified snapshot:
  `/content/drive/MyDrive/PACT/qwen3-replay-check-001/snapshots/1789714612157205696-6fb9f16ecabe`.
  Remote Drive contents were not independently accessed locally.

Original imports are preserved under `results_import/qwen3-replay-check-001/`.
Derived metrics, probe summary, `review_audit.json` and the local audit script are
under `analysis/`. Imported contents were treated as data and never executed.
All original member checksums were rechecked after analysis.

## Replay feasibility

There are **13 eligible private-packet pairs / 18 contexts**. Four contexts lack a
correct candidate; one lacks an incorrect candidate. Missing credits remain null.
Every eligible pair has two positive and two negative suffixes, each containing
three revised packets and a new frozen-base final readout: 52 suffixes / 208 calls.

| Task | Condition | Agent 0 delta | Agent 1 delta | Agent 2 delta |
|---|---|---:|---:|---:|
| Mercury_180058 | Clean | 0 | Missing correct | Missing correct |
| Mercury_180058 | Exchange | 0 | Missing correct | Missing correct |
| LEAP_2012_8_10441 | Clean | 1 | 0 | 0 |
| LEAP_2012_8_10441 | Exchange | 1 | 0.5 | 0.5 |
| LogiQA eval-0590 | Clean | Missing incorrect | 0 | 1 |
| LogiQA eval-0590 | Exchange | 1 | 0 | 1 |

Thus five credits are +1, two are +0.5, six are zero, and none is negative in these
selected observations. Ten of 13 pairs share the declared 32-token length bin.
Three LogiQA pairs are unmatched: clean agent 1 (69/52 positive/negative tokens),
clean agent 2 (67/59), exchange agent 2 (69/59). They are flagged, not discarded
or relabeled. Two of the positive credits are among those unmatched pairs.

Every credit and per-seed outcome was recomputed from raw branch finals. Correct
versus incorrect candidate selection reproduces exactly. Candidate contexts,
model snapshot, attack bytes/site, unaffected private packets and corresponding
suffix-node seeds stay fixed. Reconstructed deliveries/revision prompts use initial
peers only; primary readout sees revised packets only. All downstream calls reran.

The important corrupted-sender case actually ran: LEAP exchange agent 1 has delta
0.5 and LogiQA exchange agent 1 has delta 0. Both positive/negative branches still
deliver the same malicious bytes to both other receivers; changing the sender's
private state does not accidentally restore its clean outgoing message.

These observations close the eligible neural replay execution check. They do not
establish an average treatment effect, training efficacy, or population-level pair
availability. Tasks were selected after mixed initial outcomes, packets change both
answer and rationale, K=2 is small, and three pairs are not length-bin matched.

## Receiver preferences remain unavailable

The run sampled four revision candidates in each of eight hold and eight repair
contexts, plus two ineligible contexts with no candidates: 64 receiver calls total.
Every candidate set uses exactly the recorded receiver prompt and declared seeds.
All candidates are well-formed, but each set has only one correctness class:

| Receiver stratum | Contexts | All four correct | All four incorrect | Usable pairs |
|---|---:|---:|---:|---:|
| Hold | 8 | 6 | 2 | 0 |
| Repair | 8 | 1 | 7 | 0 |

The two all-wrong hold contexts are Mercury_180058 clean/exchange; its originally
correct receiver consistently switches to C. Only LEAP's clean repair context
produces correct repair candidates; its exchange repair, both Mercury receivers
under both conditions, and both LogiQA clean repair contexts remain wrong.
No valid same-prompt pair was lost to parsing or selection. This remains a data
feasibility limitation for revision preference training, not a software failure.
Do not count private-packet pairs as receiver DPO pairs or fabricate counterparts.

## Main outcomes, audit and cost

Main outputs reproduce the original pilot for these six task/condition cells:
1/3 clean final successes, 0/3 exchange. All teams initially have a correct packet;
Mercury's correct minority is erased in both conditions, LogiQA preserves a correct
minority but reads out D, and LEAP changes from clean final C to exchange ABSTAIN
despite retaining two correct revised packets. No representative accuracy estimate
is appropriate for this selected subset.

All main private/revision/final texts, prompts, attack assignments and node seeds
match the original pilot. New trajectory IDs, elapsed timing and packet hashes
that include that timing differ as expected; each run's delivery hashes verify
against its own actual packets. No attack or methodology changed during collection.

All exported metrics and probe summaries reproduce. All 386 calls end at EOS:
380 answer parses and six abstentions; no malformed or length-limit completions.
Exact prompt rendering/hashes, seeds, decoding, model/template identities and
recorded context budgets pass. Maximum prompt plus reserved output is 830 tokens,
not a full-context memory test. Token counts reconcile but were not retokenized.

Calls: 42 main + 72 private alternatives + 208 suffix + 64 receiver = 386, below
the 474-call cap. Input/output: 148,080 / 18,046 tokens. Recorded collection attempt
1,380.995 seconds (23.02 minutes, 0.38361 accelerator-hours); generation 1,266.26
seconds at 14.25 output tokens/second. Peak allocated/reserved memory 15.41/15.53
GiB. Attempt timing excludes final reporting/persistence and notebook-wide setup;
compute units remain unknown. These are inference costs, not training-memory data.

## Next gate

This bounded diagnostic is complete. No next Colab invocation, rerun, extra raw
export or larger sampling sweep is warranted by the audit. Retain all prior runs
and this handoff. No executable source/configuration change or regression-suite
rerun was needed; verification consisted of the complete CPU artifact audit.

The next proposed work is local Milestone-3 design/implementation of the learning
components and a training-split data plan, under a separately agreed scope. That
plan must retain missing-pair accounting and obtain valid same-prompt hold/repair
pairs before claiming revision preference training. Do not repurpose these selected
validation records as training data or report a full PACT objective when its
revision term has no usable pairs. Adapter/reference isolation, training memory,
optimizer resume, training-seed variation and final evaluation remain unverified
or deferred. Do not increase caps or alter labels merely to force usable pairs.

Local reanalysis (from matching source commit):

```bash
python -m pact report --run-dir results_import/qwen3-replay-check-001
PYTHONPATH=src python3 results_import/qwen3-replay-check-001/analysis/audit.py
```
