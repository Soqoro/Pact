# Stage I amended evaluation: completed fixed-history audit

Audit date: 2026-10-27. Run: `pact-revival-stage1-evaluation-amended-002`.
All four existing stages are complete. Fixed-history GPU execution returned from
AAI; the local audit used CPU only. This remains a development evaluation, not
full PACT or a final-test result.

## Evidence and validation

PRIVATE: `pact-revival-stage1-evaluation-amended-002-PRIVATE-1793033718300732417.zip`
SHA256 `754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`.
SANITIZED: `pact-revival-stage1-evaluation-amended-002-SANITIZED-1793033745808058957.zip`
SHA256 `1c4474a57bb28bd228040a32c496b6426e21531112e493b06be47dca0741047a`.

Both outer hashes and all 78,172 PRIVATE / four SANITIZED payload hashes passed.
Archive paths, duplicate entries, symlinks and inventory bounds passed production
archive validation. The sanitized payload is exactly summary.json,
paired_metrics.json, peer_access_interaction.json and runtime_and_cost_report.json;
all four agree with PRIVATE. The uploaded COMPLETED.json accounting matches the
bundle's accounting. PRIVATE handoff records fixed_history and recovery_safe=true.

The production Journal validated all 13,467 calls, including request identities,
physical-attempt ownership, raw/token provenance, strict packet reconstruction,
context/output caps, unresolved attempts and component/total budgets. To avoid
repeated hashing of the large immutable plan, its digest alone was cached by object
identity during Journal validation and rechecked afterward. No other hashes were
bypassed. All four aggregate reports were regenerated with production metrics on
CPU and matched the returned JSON exactly.

The preceding source-evaluation ZIP is no longer available locally, so this audit
does not newly establish byte-for-byte preservation of its raw records against
that separate artifact. The earlier source audit remains historical evidence.
This audit verifies recorded artifacts, not GPU logits, external model weights or
the cluster filesystem independently. No model download, GPU work, training or
new unit-test suite was run locally. Extracted private data stays in ignored
results_import; no raw prompts, text or token arrays are added to Git.

## Accounting and completeness

| Component | Attempted and committed calls |
|---|---:|
| Validation, including smoke | 3,876 |
| Source evaluation | 7,836 |
| Fixed history | 1,755 |
| Total amended child | 13,467 |

Zero unresolved attempts, zero context incompatibilities, zero new synthetic
attempts, teacher-forced forwards, training forwards or optimizer updates.
Reserved output tokens total 6,895,104 against the 7,471,104 ceiling; total calls
are below 14,592. Input/output tokens are 4,730,105 / 630,869. Cumulative packet
statuses are 12,482 ok, 834 invalid and 151 abstentions; invalid/abstaining packets
remain failures rather than repaired or retried samples.

Fixed history uses 64 prespecified validation tasks, including 53 accepted exchange
conditions. The 11 rejected attacks are missing exchange conditions, not unfinished
inference or defender failures. There are 192 clean and 159 observed exchange
receiver cells per arm/view. Each of the 117 observed task/condition combinations
requires 15 fresh calls and three exact frozen-present reuses:
117 × 15 = 1,755 new calls and 117 × 3 = 351 child reuses.
The 165 calls below the 1,920 ceiling correspond to 11 rejected exchanges × 15.
Cumulative ancestor reuse links remain 384. Skipped calls do not authorize extra
tasks or generation.

## Matched fixed-history receiver results

These are receiver correctness rates under the same frozen private histories,
not final team/readout accuracy. Rates average sources equally and, for this
table, the three receiver families equally.

| Condition | Independent peers present | Independent withheld | Joint peers present | Joint withheld |
|---|---:|---:|---:|---:|
| Clean, 64 tasks | 53.13% | 47.40% | 69.27% | 61.46% |
| Accepted exchange, 53 tasks | 51.28% | 52.59% | 60.68% | 56.32% |

The peer-access interaction is
(joint present − joint withheld) − (independent present − independent withheld).

| Condition | Joint gain with peers | Joint gain without peers | Peer-access interaction | Descriptive interval |
|---|---:|---:|---:|---:|
| Clean | +16.15 pp | +14.06 pp | +2.08 pp | −5.73 to +9.38 pp |
| Accepted exchange | +9.40 pp | +3.73 pp | +5.67 pp | −1.60 to +13.83 pp |

Intervals use the existing 500-replicate, source-stratified task/group bootstrap,
keeping receiver views together. Sampling units are 64 or 53 task groups, not
generation calls or 192/159 independent receiver observations. Exchange estimates
are conditional on accepted attacks.

Frozen receiver accuracy is 60.94% present / 51.56% withheld clean and
45.75% present / 38.91% withheld on accepted exchange. Thus independent SFT is below
frozen on both clean views, while joint is above frozen; joint-versus-independent
gains should not be read in isolation from this control.

Family interactions are heterogeneous:

| Receiver | Clean interaction | Accepted exchange interaction |
|---|---:|---:|
| Q | −15.63 pp | +3.85 pp |
| L | +10.94 pp | +1.99 pp |
| M | +10.94 pp | +11.18 pp |

Q's clean descriptive interval is −31.25 to −1.56 pp; L/M clean intervals each span
zero. All three exchange intervals span zero. M's positive exchange interaction
includes a −9.40 pp joint-versus-independent withheld change and only +1.78 pp
present gain: a positive interaction alone is not proof of better communication.
These family breakdowns are descriptive, not multiplicity-adjusted discoveries.

## Interpretation and disposition

The matched data support higher joint-versus-independent receiver accuracy in
the aggregate, but do not establish a positive additional peer-access benefit:
both aggregate interaction intervals include zero. Much of the clean gain remains
when peers are withheld. The earlier source-evaluation clean advantage (+5.98 pp
equal-source final accuracy) remains a separate on-policy development finding;
it does not by itself establish the receiver mechanism or robust generalization.

The amended Stage I evaluation is complete and auditable. No automatic next
experiment follows. Original later-generation history remains unknown and separate;
possible repeats of unrecoverable history are preserved in accounting. Stage II/III,
full coupled PACT, final tests and manuscript result placeholders remain deferred.
No commits, pushes, cluster execution or cleanup were performed in this audit.
