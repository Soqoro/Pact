# Stage I amended evaluation: source-evaluation audit

Audit date: 2026-10-26. Run: `pact-revival-stage1-evaluation-amended-002`.
Returned real Colab source evaluation is complete. This is a development result;
fixed-history controls remain unexecuted and full PACT has not been evaluated.

## Artifact identities and checks

PRIVATE: `pact-revival-stage1-evaluation-amended-002-PRIVATE-1792943764599174109.zip`
SHA256: `9d57f182d6dd680dc87cf0c5b7dff01b92410cbc1d66f1370b901321aa9c1fa1`.
SANITIZED: `pact-revival-stage1-evaluation-amended-002-SANITIZED-1792943799592289924.zip`
SHA256: `b81a48cd2784de941a4472dc64ae1bd1c793a2e38ce00bbee2ca3a2a459af1db`.
Plan: `288a2f9bd5bcbe95c52fd9b7d99cdefd2cb52ebd69c71a0c2939c2428dc72bf5`.
Source remains pinned to `a2ad51f60530e6dafaf1377eba03d0753f87ff92`.

Both outer hashes and all 68,684 PRIVATE / four SANITIZED payload hashes passed.
The sanitized allowlist is exactly four aggregate reports plus handoff/checksums;
all aggregate files agree with PRIVATE. All 8,885 immutable imported files passed.
All 19,766 prior validation intent/call/link/output/attack/stage files checked remain
byte-identical to the audited validation archive.

The production Journal validated all 11,712 calls: owner/plan identities, canonical
request hashes, call/token provenance and counts, context/output limits, strict
packet reconstruction, unresolved dispatch and component/total budgets. For audit
performance only, the immutable plan object's digest was computed once and reused
inside Journal; its unchanged digest was asserted afterward. All other hashes were
recomputed. No repository implementation was changed. All four aggregate reports
were regenerated on CPU and matched the supplied JSON exactly. Recovery and handoff
record safe completion. No GPU inference, model downloads, training or new unit-test
suite was executed locally. This verifies recorded evidence, not GPU logits or
external checkpoint tensor files independently.

## Accounting

Source evaluation used 7,836 calls. Combined with 3,876 validation calls (including
smoke), the child has 11,712 attempted and committed generations, zero unresolved.
Cumulative reserved output tokens: 5,996,544; input tokens: 4,102,101; output tokens:
548,581. No new attacks, synthetic checks, teacher-forced forwards, optimizer updates
or training forwards. All 384 historical attack attempts are reused; 304 accepted
and 80 rejected across validation and source evaluation. Original later-generation
history remains unknown and separate from this approved additional envelope.

The source cohort is exactly 120 ARC-Challenge / 136 LogiQA tasks. Of its 256
historical attacks, 205 were accepted (96 ARC / 109 LogiQA) and 51 rejected.
The exact source call count is 3 arms × (256 × 7 private/clean calls + 205 × 4
exchange calls) = 7,836. The 612-call difference from its 8,448 ceiling is exactly
51 × 3 × 4 skipped exchange calls. Rejected conditions are missing outcomes,
not defender failures or unfinished calls. Skipped budget is not transferred.

Cumulative parser counts are 10,846 ok, 731 invalid and 135 abstentions. Relative
to validation, source adds 7,254 ok, 496 invalid and 86 abstaining packets. These
counts span all generation phases, not only final readouts. Invalid/abstaining
completions stay failures under the frozen contract; no retry or format repair.
There are no recorded context incompatibilities; compute units were not supplied.

## Source-evaluation results

| Arm | Clean ARC | Clean LogiQA | Clean total | Exchange ARC | Exchange LogiQA | Exchange total |
|---|---:|---:|---:|---:|---:|---:|
| Frozen Q/L/M | 74/120 | 70/136 | 144/256 | 52/96 | 36/109 | 88/205 |
| Independent adversarial SFT | 97/120 | 62/136 | 159/256 | 65/96 | 54/109 | 119/205 |
| Uniform joint SFT | 99/120 | 76/136 | 175/256 | 72/96 | 56/109 | 128/205 |

The predeclared equal-source accuracies are clean 56.57%, 63.21%, 69.19% and
exchange 43.60%, 58.62%, 63.19%, respectively. These average the two source rates
equally; they are not pooled-count percentages. Exchange uses the common accepted
subset, so direct clean-versus-exchange differences mix different populations.

Primary joint-minus-independent paired comparisons:

| Condition | Paired tasks | Gains / losses | Equal-source difference | Descriptive bootstrap interval |
|---|---:|---:|---:|---:|
| Clean | 256 | 35 / 19 | +5.98 percentage points | +1.17 to +11.77 points |
| Accepted-attack exchange | 205 | 30 / 21 | +4.56 percentage points | −2.39 to +12.37 points |

The clean result supports a positive descriptive joint-over-independent difference
on this frozen development cohort. Most of the additional correct answers occur
on LogiQA (+14), versus ARC (+2). The exchange point estimate favors joint but its
interval spans zero. Missing-outcome bounds over all 256 intended exchange tasks
are −16.27 to +23.58 points for joint-minus-independent. No unconditional attack
robustness advantage or final-test generalization claim follows.

Joint-minus-frozen differences are +12.62 clean (interval +6.49 to +18.48 points)
and +19.59 observed exchange (interval +11.86 to +27.72 points). Independent-minus-
frozen differences are +6.64 clean and +15.03 observed exchange. These are secondary
comparisons, not proof that joint learning specifically improves use of peers.
All intervals use the existing 500-replicate descriptive source-stratified
bootstrap with task/group sampling units; calls are not independent observations.

## Communication diagnostics and interpretation

On clean tasks, initial correct coverage is frozen185, independent198 and joint190
of 256: the joint arm does not start with the greatest coverage. The corresponding
harmful revision counts are 30/112/39, newly correct revision counts 77/140/177,
coverage erasures 16/26/14 and readout losses 37/49/31. These are on-policy arm-specific
trajectories and strata, not matched fixed-context causal comparisons. Newly correct
revision counts can include initially invalid packets, so they do not alone prove
repair of valid wrong answers. Frozen remains lower in harmful revisions than joint.

On the accepted exchange subset, harmful revisions are 50/80/43, newly correct
revisions 42/115/144, erasures 21/20/10 and readout losses 46/44/36. These observations
motivate examining the already planned fixed-history peer-present/withheld controls,
not changing tasks or interpreting communication mechanism as established.

## Disposition

Source-evaluation integrity and accounting pass review. Validation remains unchanged;
its joint-minus-independent clean difference was zero, whereas the source cohort
shows a positive clean difference. Keep these stage-specific results separate.
The next existing stage is fixed_history, capped at 1,920 calls, followed by export
and review. Rejected attacks or exact reuse can reduce the actual count. No further
stage was launched locally. No prompts, checkpoints, parser, seeds, budgets or source
selection changed; no final-test access or manuscript placeholder updates occurred.
Full-PACT efficacy, Stage II/III and closure of unknown original history remain deferred.
