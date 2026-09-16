Continue implementing PACT after the pilot-stage work.

Read AGENTS.md, docs/PACT_IMPLEMENTATION_SPEC.md, docs/PACT_Conference_Proposal.tex, implementation_status.md, implementation_decisions.md, and the latest actual Colab handoff under results_import/.

First verify what has really been implemented and GPU-tested. Inspect reported failure counts, packet-pair eligibility, hold/repair availability, adapter/readout behavior, and measured resource use. A successful mock pipeline is not sufficient evidence of real model compatibility. Fix reproducible foundational bugs before adding training; do not assume the scientific hypothesis is true.

Implement Milestone 3 as a runnable, separately resumable pipeline:
- Clean warm-start adapters with recorded initialization/optimization seeds.
- Immutable outer-iteration team snapshots and a versioned training-only trajectory bank.
- Same-context correct/incorrect packet sampling, fixed-attack paired suffix replay, and missing-credit accounting.
- The masked responsibility optimizer with exact row support, the proposed balance/entropy objective, documented answer-loss normalization, and numerical reference tests.
- Correctly weighted specialization plus uniform base supervision.
- Same-receiver-prompt hold and repair preferences with no metadata leakage.
- Cached completion log probabilities from each actor's immutable warm-start reference adapter.
- DPO with correct prompt/padding masks and completion log-probability sums.
- Sequential updates to only one adapter at a time, preserving backbone/readout/inactive adapters.
- Outer refresh only after the complete bank and all actor updates are finished.
- Training checkpoint/resume at optimizer-step boundaries, with sampler, optimizer, scheduler, RNG, snapshot, and reference-cache identities.

Start with a tiny training/validation configuration and one outer iteration. Add tests using a tiny locally initialized model; prepare real GPU training smoke cells for Colab rather than launching expensive work locally. Ensure base loss, specialization weighting, and revision loss have unit-tested reductions: do not accidentally normalize away the responsibility weights when updating actors separately.

Add controlled training variants through configuration: independent adversarial SFT, gamma=0 local complementarity, revision-only, split specialization then revision, no-revision, hold-only, one-shot assignment, shuffled-credit, and full PACT. Share data and query/accounting interfaces, not fabricated output rows. Document which variants are fully runnable.

Do not call an ad hoc filter SAC or ordinary DPO AdvEvo-MARL. The decisive SAC composition comparison is a separately verified Milestone-4 requirement. Do not implement large benchmark/model/topology sweeps, use final test outcomes to tune the method, or silently reduce the stated threat model to simplify training.

Update the Colab training notebook, experiment ledger, runbook, and implementation status. End with tests actually run, GPU-unverified features, exact one-step/one-refresh Colab commands, and the expected training handoff bundle. No claims of improvement or hardware fit without actual outputs.
