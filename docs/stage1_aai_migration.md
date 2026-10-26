# Stage I fixed-history: AAI Slurm migration preparation

Prepared 2026-10-26 following the user's explicit request to move the remaining
work from exhausted Colab compute to their Jupyter/Slurm system. This authorizes
preparation for that system, not a method change or additional experiment. The
assistant has no access to AAI; the user executes commands and returns evidence.

## Supplied documentation and scope

Read both supplied PDFs in full: AAI-resourcelist.pdf (two pages), AAI-userguide.pdf
(11 pages). Resource-list page 2 lists node01 as A10080GB SXM4 under NA100q; node13
is40GB, and PA10080q/HPCAIq list PCIe hardware. H100/A6000/A40 are not substitutes
for the recorded GPU identity. This is a documented candidate, not a claim that
the node/partition is currently available to this user. Check live Slurm metadata.
The guide pages2–6 document sinfo, scontrol, srun, sbatch, GPU gres, node selection,
and four CPU cores per GPU. Page7 documents Jupyter access; no browser-host GPU
allocation is inferred. Use a batch job for the eventual long run, not notebook-
kernel inference on a login node. The guide's CUDA11.1 examples do not establish
compatibility with the recorded Torch2.11.0+cu130 build and are not installation
instructions for this experiment.

Only fixed_history remains, ceiling1,920 new calls, no training or new attacks.
Source evaluation has already completed, cumulative11,712 calls, zero unresolved.
Use the same run ID, plan and source; never initialize a new scientific plan or
repeat smoke/validation/source evaluation to facilitate migration.

## Initial diagnostic commands

Run these in a Jupyter Terminal or SSH shell on AAI, not a Python cell:

```bash
mkdir -p "$HOME/pact-aai-preflight"
cd "$HOME/pact-aai-preflight"
sinfo -N -o '%N %P %t %G'
scontrol show partition NA100q
scontrol show node node01
module list
module avail
```

Upload `tools/aai_stage1_probe.sbatch` from this repository to that directory using
Jupyter's file browser. Keep this diagnostic file outside the pinned PACT checkout.
Then:

```bash
cd "$HOME/pact-aai-preflight"
bash -n aai_stage1_probe.sbatch
sbatch aai_stage1_probe.sbatch
squeue -u "$USER"
```

The script requests one GPU, four CPUs,8GB host RAM and ten minutes on node01 in
NA100q. It inspects GPU model/driver, system libc, Python/package metadata, storage,
container tools and /content availability. It prints no tokens, full environment
or benchmark content. It does not install packages, load models, restore evidence
or generate. nvidia-smi may enumerate other physical GPUs on the node; this alone
is not proof that Torch sees exactly one allocated GPU. A later exact-runtime
check must verify device_count=1 under Slurm's assigned visibility. Do not override
CUDA_VISIBLE_DEVICES manually. No CUDA toolkit module is guessed for this probe.

Read the .out and .err files for the job ID returned by sbatch and return them
along with node/partition/module output. If submission is rejected, return that
message rather than replacing the partition, hardware, account or QoS by guess.
The scheduler time limit can kill work; the eventual inference job must have an
adequate reviewed limit and explicit persistence policy. No inference batch script
is prescribed before the environment and storage details are known.

## Requirements to resolve before execution

Recorded runtime: Python3.13.15, Linux x86_64, one NVIDIA A100-SXM4-80GB,
Torch2.11.0+cu130, CUDA build13.0, Transformers4.57.6, PEFT0.18.1,
Accelerate1.12.0, Tokenizers0.22.2, huggingface-hub0.36.2, Jinja2 3.1.6,
NumPy2.1.3, Safetensors0.8.0. Fingerprint:
`e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0`.
The installed NVIDIA driver must support this software; a CUDA module or container
cannot simply replace the host kernel driver. Driver/libc/build compatibility and
network/model access are not established by the supplied hardware list. Matching
the recorded fingerprint is necessary but does not prove bitwise equality of all
unrecorded host details. Record those details in transport/execution provenance.

The immutable checkpoint map references
`/content/pact-stage1/verified-final-tensors`. The loader rejects symlinks in any
path component. Do not rewrite the map or use a symlink workaround. If the host
cannot provide that exact real directory, investigate an approved Apptainer/
Singularity bind mount and host-local scratch, preserving visible paths. Container
availability and GPU passthrough remain unverified. Durable cluster storage and
its quota must be identified separately from job-local scratch; Google Drive paths
are not assumed accessible on the cluster. Keep one authoritative execution site
and preserve pending/inflight markers during any transfer.

Required private inputs for later transfer:

- Completed source-evaluation PRIVATE1792943764599174109 ZIP, SHA256
  `9d57f182d6dd680dc87cf0c5b7dff01b92410cbc1d66f1370b901321aa9c1fa1`.
- Its SANITIZED1792943799592289924 ZIP, SHA256
  `b81a48cd2784de941a4472dc64ae1bd1c793a2e38ce00bbee2ca3a2a459af1db`.
- The latest complete compact snapshot metadata/receipt/state objects, or a
  separately verified transport restoration path. A review ZIP is not silently
  substituted for a durable snapshot: it precedes the current export receipt.
- Continuation003 training PRIVATE1792630912628874679 ZIP and
  RECOVERY1792630916259050432 ZIP with its checksum sidecar, for the six actual
  final tensors. Review exports alone omit weights.
- User-authorized access to the same pinned official model weights, with credentials
  kept out of scripts, commands, logs and Git.

Pin code `a2ad51f60530e6dafaf1377eba03d0753f87ff92`, plan
`288a2f9bd5bcbe95c52fd9b7d99cdefd2cb52ebd69c71a0c2939c2428dc72bf5`.
Do not bypass runtime guards, change GPU/precision or consume extra benchmark/
synthetic checks to establish portability. A genuine incompatible environment
requires a separately specified decision, not an automatic fingerprint edit.

## Local validation / current status

`bash -n tools/aai_stage1_probe.sbatch` passed. No scheduler submission, cluster
access, model downloads, GPU inference or migration execution occurred locally.
A small PDF reader was installed only under /tmp to read the user's documents.
The initial probe is ready for user execution; environment compatibility, snapshot
transport, checkpoint mapping and fixed-history GPU execution remain pending.
