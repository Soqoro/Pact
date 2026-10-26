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

## Returned AAI probe: job1106306 (2026-10-26)

The user returned metadata-only probe output from node01. GPU name exactly matches
NVIDIA A100-SXM4-80GB; driver570.133.20, Linux x86_64, glibc2.39. Slurm supplied
CUDA_VISIBLE_DEVICES=0 and SLURM_JOB_GPUS=5; these are different visibility/index
namespaces and are not an error to fix by overriding GPU selection. No Torch
visibility test has yet run. Python3.13.11 and no recorded ML packages were found
in the current base environment. Only slurm/slurm/24.11 is loaded; apptainer and
singularity were not on PATH, which does not establish absence from modules.

/tmp has only1.8GiB available; do not use it for model downloads, environments or
archives. Home is on a shared109TiB filesystem with26TiB reported available; this
is filesystem availability, not the user's quota or node-local scratch. /content
is absent. All these are prerequisites still to resolve, not scientific failures.

NVIDIA's CUDA compatibility documentation states ordinary CUDA13.x compatibility
requires driver580+. The official forward-compatibility matrix lists
cuda-compat-13-0 with570+ as compatible for supported systems, including data-center
GPUs. Therefore driver570 is a blocker to ordinary use of cu130, not proof that
all deployment routes fail. Check site-supported compatibility libraries/container
modules and test explicitly before model work; do not silently downgrade Torch to
CUDA12 or edit the recorded runtime. A container alone does not replace the host
kernel driver. A compatibility-library deployment would need its actual loaded
libraries recorded in migration provenance, even if the existing fingerprint
matches, and does not prove bitwise equivalence.

Sources checked 2026-10-26:
- https://docs.nvidia.com/deploy/cuda-compatibility/610/minor-version-compatibility.html
- https://docs.nvidia.com/deploy/cuda-compatibility/forward-compatibility.html

Next read-only information needed: available module catalog (containers and CUDA
compatibility), scheduler wall-time limits, personal storage quota and supported
node-local scratch. No dependency installation, transfer, restoration or inference
is yet prescribed by this probe result.

## Module and partition return; compatibility probe prepared

User reports apptainer/1.24 in shared modules, NA100q UP with only node01,
MaxTime=UNLIMITED and no partition account/group restriction. This does not prove
unlimited account/QoS time or personal disk quota. quota command is unavailable;
shared filesystem free space is not personal entitlement. Python3.13.11 remains
sufficient for the diagnostic scripts only, not the frozen experiment runtime.

Prepared tools/aai_prepare_compat.py and tools/aai_cuda_compat_probe.py/.sbatch.
The preparer reads NVIDIA's official HTTPS repository metadata, selects only
cuda-compat-13-0 version580.82.07-0ubuntu1 amd64, verifies package size/SHA256 and
extracts into a user directory with dpkg-deb (no system installation or sudo).
This exact package is listed by NVIDIA and uses the580.82.07 user-mode library
version seen in prior Colab NVIDIA-SMI output; the host kernel driver stays570.
Verification is against metadata received over official HTTPS, not an independently
verified repository signature. No silent alternate package is selected.

Use a small Ubuntu24.04 diagnostic Apptainer image and record its local SIF SHA256.
The tag is a setup input, not an immutable scientific container identity; any later
experiment environment must bind its actual immutable image/libraries/provenance.
Bind the prepared user directory to /content and inspect all required path parents
for symlinks. Slurm visibility is passed explicitly through --cleanenv, and the
compatibility-library path precedes host libraries. The probe requires cuInit,
CUDA13 driver API, exactly one correctly named visible GPU, a4096-byte allocation
and free, and the actual mapped libcuda path under the verified package. It does
not import Torch, load models, launch a model/kernel computation, restore checkpoints
or modify study state. Passing proves only these driver/path operations, not Torch,
PTX/compiler interoperability or numerical equivalence of the full workload.

Local checks: both Python files compile, sbatch passes bash -n, exact package
metadata selection and five rejection cases pass (duplicate record, wrong version,
unsafe filename, excessive size, malformed checksum). No downloads or GPU work
were performed locally for this probe. Keep package/cache/tmp directories under
the user-selected preflight root; actual node-local scratch for experiment hot
files still needs to be identified before scientific execution.

### User commands after pushing tooling

In the AAI Jupyter Terminal:

```bash
cd "$HOME/Pact"
git pull --ff-only
module load apptainer/1.24
apptainer --version
command -v dpkg-deb
export PACT_AAI_PROBE_ROOT="$HOME/pact-aai-preflight/compat-probe"
mkdir -p "$PACT_AAI_PROBE_ROOT"/{tmp,cache,content/pact-stage1/verified-final-tensors}
export APPTAINER_TMPDIR="$PACT_AAI_PROBE_ROOT/tmp"
export APPTAINER_CACHEDIR="$PACT_AAI_PROBE_ROOT/cache"
export TMPDIR="$PACT_AAI_PROBE_ROOT/tmp"
python3 "$HOME/Pact/tools/aai_prepare_compat.py" "$PACT_AAI_PROBE_ROOT"
```

Stop on failure. Then prepare the diagnostic image and copy the probe script:

```bash
apptainer pull "$PACT_AAI_PROBE_ROOT/ubuntu24.04.sif" docker://ubuntu:24.04
sha256sum "$PACT_AAI_PROBE_ROOT/ubuntu24.04.sif"
cp "$HOME/Pact/tools/aai_cuda_compat_probe.py" "$PACT_AAI_PROBE_ROOT/"
cd "$HOME/pact-aai-preflight"
sbatch "$HOME/Pact/tools/aai_cuda_compat_probe.sbatch"
squeue -u "$USER"
```

Read pact-compat-probe-JOBID.out and .err. Return preparation receipt, image hash,
Apptainer version and both job logs. No shell retry loop and no experiment dispatch.
An existing prepared directory/package/image is preserved on failure; inspect it
instead of deleting or silently replacing it. Do not install full Torch/model
weights or transfer large evidence until this smaller compatibility test is reviewed.

Reference documentation:
- https://apptainer.org/docs/user/latest/gpu.html
- https://apptainer.org/docs/user/latest/bind_paths_and_mounts.html
- https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/
