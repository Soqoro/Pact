# PACT

Preservation-Aware Complementarity Training: a local-to-Colab **diagnostic pilot**.
This implementation covers the Milestones 0–2 execution path and initial local
Milestone-3 learning foundations. It does not train PACT
or establish a trained PACT result. Unadapted Qwen3-8B inference is verified on the
reported Colab L4 environment through the 80-item validation pilot and full raw audit.
Eligible neural suffix replay is also verified by the selected six-record check.
Receiver preference availability remains unresolved; the bounded warm-start
engineering run has completed, as described below.

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
the complete nine-update Qwen3-8B GPU engineering run, continuation and exports
now pass [returned metadata review](docs/reviews/qwen3-warmstart-001-complete.md).
This is not a full PACT training or efficacy result. The default command only emits the reviewed plan.

[Frozen-reference scoring and bounded train-only collection](docs/collection.md)
are now implemented and tested locally: 97/97 tests pass with tiny CPU neural
checks enabled. The six-record collector preserves raw paired replays, actual
sampled token IDs, missing preferences and verified recovery snapshots. Its
default is plan-only. The [complete GPU engineering bank](docs/reviews/qwen3-bank-001-complete.md)
now passes returned audit: six records, preserved resume, five private pairs and
20 suffix branches. All 24 receiver candidates lack a correct answer, so there
are no hold/repair preferences and the full revision objective is not ready.
GPU reference scoring remains unverified. A [bounded base-control diagnostic](docs/preference_feasibility.md)
is now implemented and CPU tested: it compares the same saved prompts/seeds using
54 fresh base calls, with no new actor samples or training-pair export. Its default
is plan-only; review and publish before the new Colab check.

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

The completed GPU engineering check used [the bounded warm-start notebook](notebooks/02_warmstart_colab.ipynb):
one update by default, verified checkpoint persistence and a small review ZIP.
[Execution and recovery](docs/warmstart.md#colab-execution-and-recovery) require a newly published commit.
