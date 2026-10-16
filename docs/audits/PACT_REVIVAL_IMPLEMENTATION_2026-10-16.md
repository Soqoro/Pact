# Revival implementation and feasibility audit — 16 October 2026

The requested heterogeneous dense-training study and separate update assay have
local executable paths in `src/pact/revival`. No new real experiment has run.
The current exact cohort is infeasible under the retained exclusion policy.

## Verified source bound

Audited closed selective plan:
`848b8e6941f958628e8697e96fcd11a465237c056f313d84b12b7088c461c0d6`.
Its exposure manifest matches its recorded hash. Prior proposal-1200 manifest:
`92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a`.

| Quantity | Count |
|---|---:|
| Pinned official ARC training rows | 1119 |
| Historical reserved ARC rows | 600 |
| Additional selective ARC rows | 112 |
| Intersection of those two sets | 0 |
| Maximum remaining ARC rows | 407 |
| Requested new ARC groups | 480 |
| Minimum shortage | 73 |

This bound alone rules out the requested allocation. It does not claim an exact
eligible count after duplicate/validation/protected-group exclusions. Full official
source files were not available locally and were not downloaded. No previous
fit-only allocation was silently released. Revised quotas/sources/permissions
require an explicit methodological decision, not a retry or additional sampling.

The reviewed metadata-only inventory is at
`/var/tmp/pact-revival-prerequisites-20261016/prior-exposure.json`, SHA256
`3138e7a0ab7b3deb8b05d24f530a68f15f0fd92c436e0c301224242618a01849`.
The sibling `revival-source-feasibility.json` records the bound. These are private
metadata derivatives, not source/training data or an authorization to train.

## Implemented path

- Official source preparation, reviewed exclusions, equal splits, disjoint fitting/
  allocation blocks, public-only prompt builders and immutable plan hashes.
- Pristine native Q/L/M/R access/loading; direct FP32 LoRA delta path, matched family
  initialization, private and synchronous revision use of the same adapter.
- Honest-peer withholding that retains the exact malicious incoming packet; strict
  two-key answer-first packets, no gold rationale, EOS target or evaluation fallback.
- Native tokenizer-aware prefix CE with causal masking, globally shared clipped
  stratum weights and exact group accumulation; two epochs/six trained adapters.
- Scratch responsiveness check with discarded weights; safe JSON/safetensors
  optimizer/RNG/sampler checkpoints and refusal of unresolved attempts.
- Full frozen/independent/joint live evaluation and off-policy peer-use diagnostic,
  task-level paired summaries, missingness/format/hold-repair/coverage accounting.
- Separately frozen final-joint update assay,24 temporary branches, before/after
  private and terminal scores, restored source weights, and non-deployable allocation
  analyses retaining flat/negative/missing effects.
- Finite CPU coupling orchestration and the specified comparison modes, with real
  coupled execution disabled until a separate reviewed MethodSpec exists.
- Tested CLI routes, thin default-safe notebook, exact runbook and separate PRIVATE,
  SANITIZED and real-weight RECOVERY bundles.

The neural fixture uses a locally initialized tiny causal network and real optimizer
steps; generation outputs are explicitly mock packets. It does not demonstrate
large-model generation quality, native tokenizer compatibility or scientific efficacy.
The specification's real update/forward quotas are preserved; the integration
fixture has smaller explicitly marked split sizes and step counts.

## Validation

Executed locally, without pretrained downloads:

```bash
PYTHONPATH=src /home/gnoriq/miniconda3/envs/gmats/bin/python \
  -m unittest discover -s tests -p test_revival.py -v
```

**21 tests passed in 94.893 seconds.** The fixture exercises all six adapter fits,
all 24 temporary branches and exact rollback, with 1,232 fixture generation calls
and 448 diagnostic scoring forwards. These are smaller, explicitly mock study
counts, not real experimental evidence. Tests also cover causal masks/reference
gradients, accumulation, BF16-base/FP32-adapter arithmetic, initial no-op equality,
projection checks, resume refusal, budgets, source separation, privacy, immutable
review binding, CLI defaults and coupling controls.

After that run, delivery envelopes were changed to deep-copy packet contents to
prevent mutation of frozen private state through aliases. The updated targeted
`test_revival.Contracts.test_delivery` passed (1 test); the whole suite was not
repeated after this narrow change.

Relevant legacy regressions: receiver tests ran 14 (11 passed, 3 opt-in tiny
neural tests skipped); native-backend tests passed 18; exposure tests passed 4.
Thus 33 legacy tests passed and 3 were skipped. This is not a full-repository
test-suite claim. Logs are in `/tmp/pact-revival-accepted.log`,
`/tmp/pact-revival-immutable-test.log` and
`/tmp/pact-revival-legacy-{receiver,native,exposure}.log`.

The design arithmetic checker, Python compilation, notebook code-cell syntax and
default-safe smoke setting, exposure-inventory freshness, and `git diff --check`
also passed. Native GPU training/generation, real tokenizer masks, model fit,
throughput and Drive persistence remain unverified.

The supplied design checker was repaired from `config/` to the existing `configs/`
path; it checks arithmetic/defaults, not execution or scientific success.
No manuscript placeholders, historical studies or unrelated local files were
rewritten. No commit, push, secret access or model download occurred.
