# Controlled receiver supervision: completed training audit — 2026-09-23

Reviewed `qwen3-receiver-supervision-controlled-001-handoff-1790098915763332271.zip`,
4,067,890 bytes, SHA256
`ce9f97aca8a24e7a15b890d5e557c3da7af8331f944847b8d4036feb152ae993`.
Archive checksums verified. Source was clean commit
`27889da90d2afce934fffb1baac9acb64ec3a1e2`. Review metadata omits tensor payloads;
local audit cannot independently certify the real GPU checkpoint values.

## Observed results

| Evidence | Result |
|---|---|
| Donor acquisition | 217 attempted/committed; zero unresolved |
| Accepted/rejected donors | 154 / 63; rejections target mismatch |
| Input/output tokens | 57,587 / 9,736 |
| Fit contexts | 45: hold 17, repair 28 |
| Held-out contexts | 19: hold 13, repair 6 |
| Opposite controls | Available for all 45 fit and 19 held-out contexts |
| Task SFT | Complete, 24/24 updates |
| Receiver SFT | Complete, 24/24 updates |
| Evaluation | Zero calls; blocked before model loading |

Reconstructed donor journal accounting and contexts match the returned artifacts.
Each arm has 90 primary presentations and 90 private anchors over two epochs,
180 forward/backward microbatches per arm. Both report nonfocal unchanged and
identical initial tensor hash
`8d606e4de2c906dd45c6e899e51ba2f84d9f58e420f1ad598236e1242c30be08`.
These are focal receiver-study updates, not all-agent full-PACT training.
Donor rationales remain unreviewed; acceptance does not establish sound reasoning.

## Evaluation blocker and evidence limits

The guard raised `Nonfocal checkpoint differs between arms`. Both trained arms
export identical nonfocal files to each other, but different files from the
original preparation. User-run tensor diagnostics report all 144 tensors per
nonfocal actor exactly equal the original FP32 values rounded through BF16 back
to FP32. None is numerically identical to its original tensor. Maximum differences
are 6.103143095970154e-05 (agent1) and 6.103329360485077e-05 (agent2).

A tiny randomly initialized CPU Qwen reproduction confirms this loader behavior:
the first actor preserves FP32 values; subsequent adapters round during loading.
The trainer's unchanged check starts after loading, so its reported success does
not prove original-export preservation. This is a precision/provenance deviation,
not merely harmless file serialization. There is no evidence yet that training
improved receiver performance.

## Implemented recovery and remaining work

The explicit `--effective-init-recovery` transition is restricted to this archive,
original study/source and evaluate/report/export stages. It preserves completed
training and tensors. CPU proof checks original initialization, both step-zero and
final checkpoints and all exports. Actual loaded model tensors must then exactly
match certified effective tensors before evaluation. New effective snapshot IDs
and a source-transition receipt record the distinction from original exports.
Any other difference rejects recovery; the ordinary guard remains strict.

Remaining evaluation: 603 generation calls and 171 CE forwards, within the
original ceiling; total acquisition plus evaluation would be 820 calls. Full
PACT integration, final-test evaluation and a general loader precision redesign
remain deferred. [Exact Colab recovery cells](../controlled_peer_donors_recovery.md).

## Local validation

Default CPU/mock suite: 176 tests, 165 passed and 11 skipped. New recovery suite
with tiny neural opt-in: three passed, including actual BF16 adapter reload and
rejection of changed actor tensors. This reproduces loader behavior locally; it
does not independently verify the omitted real checkpoint tensors. Those are
mandatory checks in the Colab recovery preflight. No GPU experiment executed locally.
Additional receiver-supervision and controlled-donor regression suite with neural
opt-in: all 22 tests passed, including actual tiny training and resume.
