# PACT

Preservation-Aware Complementarity Training: a local-to-Colab **diagnostic pilot**.
This implementation covers the Milestones 0–2 execution path. It does not train PACT
or establish a trained PACT result. Unadapted Qwen3-8B inference is verified on the
reported Colab L4 environment through the 80-item validation pilot and full raw audit.
Eligible neural suffix replay, trained-adapter isolation and training remain unverified.

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
