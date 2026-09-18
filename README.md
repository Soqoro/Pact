# PACT

Preservation-Aware Complementarity Training: a local-to-Colab **diagnostic pilot**.
This implementation covers the Milestones 0–2 execution path and initial local
Milestone-3 learning foundations. It does not train PACT
or establish a trained PACT result. Unadapted Qwen3-8B inference is verified on the
reported Colab L4 environment through the 80-item validation pilot and full raw audit.
Eligible neural suffix replay is also verified by the selected six-record check.
Receiver preference pairs and Qwen3-8B adapter training remain unresolved;
see the [replay review](docs/reviews/qwen3-replay-check-001.md).

Masked assignment, same-prompt preference construction and immutable reference-score
caching now have CPU tests. For an explicitly synthetic round trip, run:

```bash
python -m pact training-check --output-dir scratch/training-foundations-001
```

See the [learning foundations and training-data plan](docs/training_foundations.md)
for the contract, commands and remaining neural-training work.

Train-only ARC/LogiQA loaders and frozen manifests now support full validation overlap
screening. See [training-data preparation](docs/training_data.md) for the offline
workflow, explicit download option, source checks and audit limits.

A bounded [clean-answer warm-start path](docs/warmstart.md) now plans sequential updates
to three LoRA adapters with checkpoint/resume and frozen reference exports. Tiny CPU
neural checks now pass, including exact resumed weights/losses and adapter isolation;
Qwen3-8B GPU training remains unverified. The default command only emits the reviewed plan.

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pact smoke --config configs/smoke/cpu.yaml --run-id local-smoke
python -m pact export-bundle --run-dir scratch/runs/local-smoke --output scratch/bundles/local-smoke.zip
python -m pact import-bundle --bundle scratch/bundles/local-smoke.zip --destination results_import/local-smoke
python -m pact report --run-dir results_import/local-smoke
```

CPU tests and reporting use only the standard library. They do not download models.
Configurations use JSON syntax, a valid YAML 1.2 subset. Install `.[data]` for the
official validation loaders; `.[model]` for Transformers/PEFT inference. The Colab
installer constrains PyTorch to the already installed runtime build.

Open [the Colab notebook](notebooks/01_pilot_colab.ipynb), set a credential-free
repository URL and reviewed commit SHA, and run the default four-item smoke preset.
Follow [the exact runbook](docs/colab_runbook.md) before the 20-item profile or 80-item pilot.

The protocol freezes three independent private packets, delivers initial peers,
collects synchronous revisions, and reads only revisions with the frozen base.
Fixed-pool early and exchange attacks, natural/matched baseline paths, packet-pair
eligibility, paired suffix replay, and offline metrics are implemented.

Sources: [specification](docs/PACT_IMPLEMENTATION_SPEC.md),
[proposal](docs/PACT_Conference_Proposal.tex). See [status](docs/implementation_status.md),
[decisions and limitations](docs/implementation_decisions.md), and
[experiment ledger](docs/experiment_ledger.md). Imported traces are untrusted data.

The next GPU engineering check uses [the bounded warm-start notebook](notebooks/02_warmstart_colab.ipynb):
one update by default, verified checkpoint persistence and a small review ZIP.
[Execution and recovery](docs/warmstart.md#colab-execution-and-recovery) require a newly published commit.
