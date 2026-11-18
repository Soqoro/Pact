# Stage II contribution-assay review — 17 November 2026

The completed temporary-update assay shows useful ARC attack-robustness signals, but mixed LogiQA effects. It does not yet demonstrate that a learned allocation policy improves held-out performance.

## Evidence and execution

Verified uploaded SANITIZED archive SHA256: `cbf23e81ba8d81362471089c0839c17f1467caf101b3c91d89bade3c0abd0e7d`. Payload checksums were verified. This local review reads sanitized aggregates; it does not independently re-audit remote private traces or tensor contents.

Remote scoring job 1123980 reported COMPLETED, exit 0:0, in 45m15s. Reported cumulative work: 7,320 generations, 192 temporary optimizer updates, 1,536 supervised forwards, and 2,442 diagnostic scoring forwards. Scoring added no generated answers or training. All 24 temporary branches are complete.

## Generated-answer results

Each branch independently starts from S0 and updates only one actor for eight steps. Q = Qwen, L = Llama, M = Mistral. The table averages correct-answer counts over three ARC fitting blocks or five LogiQA fitting blocks. These are descriptive averages over repeated evaluations of the same probes, not independent samples or confidence intervals.

| Probe source | Updated actor | S0 clean | Mean branch clean | S0 attacked | Mean branch attacked |
|---|---|---:|---:|---:|---:|
| arc_challenge | Q | 17/24 | 18.00/24 | 9/17 | 10.67/17 |
| arc_challenge | L | 17/24 | 18.33/24 | 9/17 | 9.67/17 |
| arc_challenge | M | 17/24 | 16.67/24 | 9/17 | 11.33/17 |
| logiqa | Q | 24/40 | 24.00/40 | 19/32 | 20.80/32 |
| logiqa | L | 24/40 | 23.60/40 | 19/32 | 20.40/32 |
| logiqa | M | 24/40 | 22.00/40 | 19/32 | 17.40/32 |

Attacked results cover only accepted attacks: 17/24 ARC and 32/40 LogiQA. The seven and eight unavailable/rejected attacks are not imputed outcomes. Every branch has complete scoring support for its prescribed available views.

- ARC: attacked correctness improved in eight of nine branches and tied in one. Clean correctness improved in four, tied in four, and declined in one.
- LogiQA: Q improved attacked correctness in all five branches; L improved in four and tied in one. M declined in all five. Clean results were mixed: Q averaged the unchanged S0 count, L averaged 0.4 fewer correct answers, and M averaged two fewer correct answers.
- These changes concern team readout correctness after a single actor update, not that actor’s standalone accuracy.

## Capped answer-prefix NLL gains

The implementation computes S0 capped NLL minus branch capped NLL, with a cap of 10. Positive values mean lower loss after the temporary update. This is a surrogate contribution measure, distinct from generated-answer correctness. Values below are descriptive means across blocks.

| Source | Actor | Clean gain | Attack gain | Private-bank gain |
|---|---|---:|---:|---:|
| arc_challenge | Q | -0.069 | +1.421 | +0.431 |
| arc_challenge | L | +0.387 | +1.203 | +0.776 |
| arc_challenge | M | -0.238 | +1.994 | -0.021 |
| logiqa | Q | +0.044 | +0.074 | -0.081 |
| logiqa | L | -0.019 | -0.041 | -0.166 |
| logiqa | M | -0.511 | -0.856 | -0.516 |

ARC attack-loss gains are positive in all nine branches. LogiQA M attack-loss gains are negative in all five, agreeing directionally with its correctness decreases. Other LogiQA effects are smaller and mixed; improved generated correctness does not guarantee a positive NLL gain.

## Limits and next decision

These are 24 ARC and 40 LogiQA allocation probes reused across branches. They are not the frozen 64 GPQA Main + 64 LogiQA prospective evaluation cohort. No significance claim or generalization claim follows from these repeated branch views. Packet-format success is also not answer accuracy; invalid completions remain failures.

The source standard remains documented-exclusion-screened development. Semantic decontamination and project freshness are not certified, pretrained-model exposure is unknown, and missing historical spending remains unresolved. The completed child accounting does not establish remaining historical budget.

Next is review and freeze of the predeclared five allocation policies using the unchanged solver and analysis contract, followed by separately authorized policy training and prospective evaluation. Do not choose a replacement methodology or cherry-pick branches from these results. This review authorizes no new physical work.
