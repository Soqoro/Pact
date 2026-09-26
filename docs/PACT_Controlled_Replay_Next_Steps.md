# PACT: next steps after the fixed-bank collection stop

Date: 26 September 2026
Status: proposed methodological revision and bounded experiment, not new results.

## Recommendation

Close `qwen3-specialization-contrast-001` with its actual insufficient-support result. Do not extend natural sampling. Implement one separately versioned controlled-private-replay study, reusing the completed fitting anchors and unevaluated development partition.

The goal is not simply to obtain more pairs. It is to determine whether a controlled correct-versus-wrong intervention supplies a meaningful *between-agent assignment signal*, and whether using that signal helps beyond training on the same synthetic examples uniformly or according to local answer likelihood.

## 1. What the existing result supports

The latest supplied audit reports 32 fitting tasks, clean/early conditions, 64 rows, 1,216 completed generation calls, and only five eligible actor/row cells on two distinct tasks. Replay, scoring, training and development evaluation did not execute.

This tests the bounded natural-pair acquisition recipe, not specialization efficacy. It also does not by itself establish the reasons every other cell failed eligibility. Those reasons can be reconstructed from the existing candidates without more inference.

The previous selected validation replay established that the estimator can execute on particular supported cases. It did not establish representative training-bank yield. Its data must remain out of fitting.

## 2. The methodological change

Old acquisition:

> Repeatedly sample actor i under its original prompt, then hope to find both a correct and a wrong private packet.

New acquisition:

> Generate a controlled correct/wrong packet pair offline for each fitting task, and insert the same two packet texts at each actor position in separate replay branches.

Use the existing pinned unadapted base model in its donor-generation role. The generator receives the task and assigned option, not the actors' identities, outcomes, early advisory, or desired credit. The same generator template supports both target classes. Two attempts per target; first valid accepted output wins. No rewriting of returned answers/rationales.

The pair is shared across all three actor interventions and both clean/early rows for that task. This controls donor-content differences rather than allowing one actor to receive an easier or better-written probe.

For each actor position, substitute the packet in a cloned private snapshot; regenerate the three revisions and frozen readout with paired seeds. The other actors' natural initial packets remain unchanged. The selected actor's own packet and all clean outgoing views must consistently reflect the substitution.

This explicitly changes the estimand to a controlled packet-insertion effect. It is not an on-policy estimate of how much training that actor to become correct would improve the team. Rationale wording, sender position, remaining initial states and downstream model behavior all contribute. It is a proposed training surrogate requiring empirical validation, not a new causal guarantee.

## 3. Why this might still produce no useful training signal

Three counterfactual credits can all be positive and equal. In that case the common credit cancels from relative assignment costs. Identical actors and symmetric interactions can yield exactly that result.

Alternatively, different credits may reflect packet ordering or finite-sample noise rather than meaningful actor-specific value. Therefore pair support, assignment contrast and held-out learning efficacy are separate outcomes.

The experiment does not add forced diversity, random actor bonuses or new prompts when responsibilities look uniform. A flat result would challenge this controlled-slot credit design; it is not a reason to enlarge the sampling budget after seeing it.

## 4. Reuse rather than restart

Import the original 32 fitting tasks, 64 natural anchors, fixed early payloads, three effective actor identities and 32 development groups from the stopped specialization study. Do not regenerate its 1,216 calls. Preserve its source/plan/bundle hashes and stopped status.

The new study is a child run. Its generated controlled packets and replays have new provenance and budgets. The 32 development tasks remain unused until the declared training/evaluation phase; no GPQA or official test data are accessed.

The expected effective frozen-preparation weights include the previously disclosed nonfocal precision history. Do not silently change that history or use the trained receiver arm as the initialization.

## 5. Stage A: obtain and assess controlled credit

1. Generate at most two target-conditioned attempts for each of two targets on each fitting task: at most 128 calls.
2. Validate packet schema, assigned answer, bounded justification and absence of explicit construction cues. Mark explanation quality unreviewed unless substantive review actually occurs.
3. Require accepted positive/negative pairs and compatible multi-actor replay support on at least eight distinct fitting tasks. Missing support remains missing.
4. On supported rows, replay all three actor interventions with two paired suffix seeds. Keep per-seed outcomes and both positive and negative branches.
5. On eight fitting tasks selected before outcomes, repeat the replay with reversed peer/readout display order, keeping model identities, packets and seeds fixed.
6. Replay the five retained natural pairs as a separate small calibration comparison. These are two tasks, not enough to validate synthetic credit generally.
7. Calculate uniform, local and controlled-credit assignments on identical masks, targets and frozen likelihood scores. Do not mix natural and controlled credits into a single bank.

Practical screen proposed for the new variant: at least eight multi-eligible tasks; task-average L1 credit-versus-local assignment difference at least 0.10 overall; at least eight distinct tasks individually meeting that contrast. These are explicitly chosen engineering thresholds, not statistical power or efficacy criteria. L1 0.10 is a transfer of 0.05 probability mass in an assignment row.

Report seed/order sensitivity and whether one actor receives most responsibility everywhere. The acquisition/replay command stops at this report. A user-invoked training stage follows only after reviewing the contrast and its limitations; no automatic escalation.

## 6. Stage B: test learning, keeping the target data identical

Reuse the existing one-round fixed-bank trainer with these arms:

- Controlled uniform SFT: uniform specialization weights over the same eligible support.
- Controlled local specialization: answer-likelihood-based responsibilities, no continuation credit.
- Controlled continuation specialization: same local cost plus the new controlled credit.

All receive the same base supervision and synthetic correct full-packet targets. Changing the target source is an additional explicit methodological change; it is not unchanged natural packet SFT. The shared targets control for benefits from synthetic-data distillation.

Train all three adapters sequentially per arm, from identical initialization, for the inherited at-most-32 updates per adapter. Keep receiver SFT/DPO off, with no outer refresh or new loss. Preserve global responsibility magnitudes across accumulation instead of independently normalizing each actor's weights.

Evaluate frozen initialization plus all three arms on the same 32 development tasks, clean/early conditions, natural private generation, independent vote/synthesis and clean synchronous debate under each condition. No controlled helpful donors or forced answers are inserted during this evaluation.

More mixed teams is not the endpoint. Seek lower all-wrong frequency and useful coverage beyond the best member without merely turning all-correct teams into mixed failures. Compare final outcomes and clean utility as well as availability.

## 7. Maximum new work

| Stage | Generation calls | Reserved output tokens |
|---|---:|---:|
| Shared controlled packets | 128 | 32,768 |
| Primary controlled replay | 3,072 | 638,976 |
| Order sensitivity on eight fitting tasks | 768 | 159,744 |
| Five natural-pair calibration cells | 80 | 16,640 |
| Four-system natural development evaluation | 2,048 | 425,984 |
| Total ceiling | 6,096 | 1,274,112 |

The first acquisition stage is only 128 calls. The pretraining ceiling including all replays is 4,048 calls, not a commitment to consume them. Missing support or failed contrast stops later work. Frozen scoring adds at most 384 teacher-forced forwards, with at most 288 optimizer updates across the three trained arms. Training input/target tokens and actual elapsed time must be logged separately.

These are substantial worst-case budgets. They are not billed GPU-hour or Colab-credit forecasts. Actual source acceptance, compatible rows and exact cache reuse may reduce calls. No old budget is reset or counted as new.

## 8. How this study can change the project decision

- Controlled pairs remain scarce: this particular generator still does not provide support. Stop the bounded study without altering thresholds.
- Pairs exist but assignments are flat: the controlled intervention does not distinguish learning responsibilities. Do not call positive shared credits complementary allocation.
- Contrast is sensitive to order or seed: the interpretation is unresolved. Do not treat the point estimates as reliable actor value; the report informs a separate decision before training.
- Credit-specific training does not beat shared-target uniform/local training: no demonstrated benefit from the controlled continuation term.
- Coverage improves but natural communication loses it: specialization has a measurable target for a later joint-versus-split preservation study.
- Controlled-credit training improves natural outcomes beyond both controls: proceed to a larger, properly powered study of the coupling. This small run alone is not full PACT or adaptive robustness.

The next milestone is a falsifiable learning experiment, not merely another accepted-pair count. The entire path should be implemented in this update so that a passed data/contrast review does not require another code rewrite before training.
