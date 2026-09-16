# PACT Codex prompt pack

This pack contains instructions and the research proposal, not an implemented repository or measured experiment results.

## Set up the local project

Extract the pack into your intended repository root after checking for existing paths. It adds:

    docs/PACT_IMPLEMENTATION_SPEC.md
    docs/PACT_Conference_Proposal.tex
    prompts/01_BUILD_PILOT.md
    prompts/02_BUILD_TRAINING.md
    prompts/03_REVIEW_COLAB_RUN.md
    PACT_START_HERE.md

No repository URL is assumed. No source code, credentials, or model checkpoints are included.

Open the repository in your local Codex environment and paste `prompts/01_BUILD_PILOT.md`. The full implementation specification stays in the repository so future development sessions can consult it. Codex should produce a tested diagnostic-pilot pipeline first, with actual GPU validation left to Colab.

## The intended cycle

Local implementation and CPU tests → user reviews/commits/pushes → Colab fetches a declared commit → bounded GPU smoke/profile/pilot → durable artifacts and results bundle → user copies the bundle into local `results_import/` → paste `prompts/03_REVIEW_COLAB_RUN.md`.

Once the real-model pilot is functional, use `prompts/02_BUILD_TRAINING.md` to implement the learning components. Continue using the review prompt after each Colab run. Full comparative evaluation and transfer are later milestones in the specification.

GitHub is the code transport, not the default storage for large outputs. The generated runbook should explain how to use a separate persistent output location and export lightweight bundles. Colab notebooks should never contain secrets or automatically launch the final paper suite.

## First scientific checkpoint

The first pilot should establish whether the intended failures and training signals are measurable: initial answer variation, harmful revision, helpful correction, usable counterfactual pairs, and the cost of collecting them. It is not a final estimate of PACT performance.

The primary proposal settings remain three logical agents, Qwen3-8B as the main backbone, one synchronous exchange, fixed readout, bounded textual attacks, and single-accelerator execution. Smaller engineering smoke models must be clearly separated from the primary experiment configuration.

## What this pack does not certify

The prompt pack has been checked for file consistency and archive integrity. It does not verify a future Codex implementation, dataset download, model/library compatibility, Colab allocation, GPU memory fit, or the scientific hypothesis. Those require the local tests and real Colab reports specified in the brief.
