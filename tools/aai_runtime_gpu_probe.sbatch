#!/bin/bash
#SBATCH --job-name=pact-runtime-gpu
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=00:15:00
#SBATCH --output=pact-runtime-gpu-%j.out
#SBATCH --error=pact-runtime-gpu-%j.err
set -euo pipefail
module load apptainer/1.24
PACT_ROOT="$HOME/pact-aai-preflight/compat-probe"
PACT_ENV_ROOT="$HOME/pact-aai-preflight/runtime-v1"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
test -f "$PACT_ENV_ROOT/install-receipt.json"
sha256sum --check "$PACT_ENV_ROOT/tool-sha256.txt"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_ROOT/ubuntu24.04.sif" | sha256sum --check -
printf '%s  %s\n' 20e6ceff0c67aa902f74c662719108677c758651d9bb1e1eff738835c681f82b "$PACT_ROOT/compat/usr/local/cuda-13.0/compat/libcuda.so.580.82.07" | sha256sum --check -
test "$(df -Pk /tmp | awk 'NR==2 {print $4}')" -ge 1048576
export APPTAINER_TMPDIR="$(mktemp -d "/tmp/pact-torch-${SLURM_JOB_ID}-XXXXXX")"
export APPTAINER_CACHEDIR="$PACT_ROOT/cache"
export TMPDIR="$PACT_ENV_ROOT/tmp"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
set +e
apptainer exec --cleanenv --nv --bind "$HOME:$HOME" \
  --bind "$PACT_ROOT:/opt/pact-compat:ro" --bind "$PACT_ROOT/content:/content" \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:?Missing Slurm GPU allocation}" \
  --env 'LD_LIBRARY_PATH=/opt/pact-compat/compat/usr/local/cuda-13.0/compat:/.singularity.d/libs' \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  "$PACT_ROOT/ubuntu24.04.sif" "$PACT_ENV_ROOT/venv/bin/python" -I -u \
  "$PACT_ENV_ROOT/tools/aai_runtime_probe.py" gpu "$PACT_ENV_ROOT/gpu-receipt-${SLURM_JOB_ID}.json"
PACT_EXIT=$?
set -e
printf 'Container exit code: %s\n' "$PACT_EXIT"
rmdir "$APPTAINER_TMPDIR"
test "$PACT_EXIT" -eq 0
printf 'RUNTIME_GPU_PROBE_COMPLETE; no study execution authorized by this check.\n'
