# Stage I amended evaluation: smoke return audit

Audit date: 2026-10-24. Run: `pact-revival-stage1-evaluation-amended-002`.
This is returned real Colab smoke evidence, not a mock or completed evaluation.

## Evidence and integrity

PRIVATE `pact-revival-stage1-evaluation-amended-002-PRIVATE-1792772915017426764.zip`:
`5132b4df6c07703b0aa42d720ea1614573479907518cbc80cd34b5ddce8b922b`.
SANITIZED `pact-revival-stage1-evaluation-amended-002-SANITIZED-1792772921480856365.zip`:
`45ddad0ce4c1a6764ac9476668ab30c87a34f7ce5da2174976afa07a416ed6b0`.
Both supplied archive hashes match. Archive validation passed for all 9,260 PRIVATE
and four SANITIZED manifest payloads. All 8,885 immutable imported inventory files
match their recorded hashes. The sanitized archive has exactly the four approved
aggregate reports plus its handoff and checksum metadata; its reports match PRIVATE.
Raw benchmark material remains in ignored private archives, not this report.

Frozen plan: `288a2f9bd5bcbe95c52fd9b7d99cdefd2cb52ebd69c71a0c2939c2428dc72bf5`.
Resolution: `6b9c89d431c7b988215bec34a52270b1d9e43c1f8c17693d10ce8e37e9aabbaa`.
The smoke stage records execution_complete=true, fixture=false and recovery_safe=true.

## Accounting and local checks

- 66 new attempts, 66 committed, zero unresolved; all belong to validation.
- 33,792 reserved output tokens, 26,309 input tokens, 3,179 actual output tokens.
- Two ancestor attack reuse links; no new attack acquisition.
- Zero new synthetic, training, teacher-forced forwards or optimizer updates.
- Sixteen checkpoint-verification forwards remain inherited evidence.
- Zero recorded context incompatibilities; 61 parser-valid and five invalid packets.

Local CPU audit ran the production archive validator, immutable inventory hash
checks, and Journal reconstruction over all 66 calls. Journal checks include plan
and physical owner identity, request/call/token provenance, token limits, strict
packet re-parsing, unresolved dispatch and component/total budgets. Regenerating
summary, paired metrics, peer interaction and runtime/cost reports reproduced all
four supplied JSON objects exactly. No model was loaded or downloaded, and no
GPU calls or training were run locally. This audits returned records; it does not
independently reproduce GPU logits or inspect the external tensor files.

## Two-task observations

The included smoke covers one prespecified validation task per source. Each table
cell is correct final readouts out of those same two tasks, not independent calls.

| Arm | Clean | Attacked exchange |
|---|---:|---:|
| Frozen Q/L/M | 2/2 | 2/2 |
| Independent adversarial SFT | 2/2 | 2/2 |
| Uniform joint SFT | 1/2 | 2/2 |

The five parser-invalid packets comprise two independent private packets, two
independent revisions, and one joint private packet. They remain failures under
the frozen parser; none is retried or repaired. All 12 final readouts are parseable.
Two tasks cannot establish efficacy, superiority, robustness or full-PACT results.

## Disposition and next stage

Smoke execution and returned artifact integrity pass review. Validation is the
next separately invoked stage under the existing approved plan, reusing these
66 calls. Its total ceiling is 4,224 calls including smoke, so at most 4,158 new
validation calls remain; accepted attack availability may reduce execution.
Export and review validation before source evaluation or fixed-history execution.
No new stage was launched by this local audit. Do not repeat smoke, change parser,
replace tasks or expand budgets based on these observations.

Full validation, source evaluation and fixed-history stages remain incomplete.
The report's all_outputs_observed=false is expected at smoke: unexecuted population
rows are missing, not incorrect answers. Original later generation history remains
unknown, and the additional envelope does not close that historical uncertainty.
Parent verification, historical training and original resolution remain unchanged.
