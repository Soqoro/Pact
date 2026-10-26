#!/bin/bash
#SBATCH --job-name=pact-compat-probe
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=pact-compat-probe-%j.out
#SBATCH --error=pact-compat-probe-%j.err
set -euo pipefail
module load apptainer/1.24
PACT_ROOT="${PACT_AAI_PROBE_ROOT:-$HOME/pact-aai-preflight/compat-probe}"
PACT_PYTHON="$(command -v python3)"
test -f "$PACT_ROOT/ubuntu24.04.sif"
test -f "$PACT_ROOT/compat-receipt.json"
test -f "$PACT_ROOT/aai_cuda_compat_probe.py"
export APPTAINER_TMPDIR="$PACT_ROOT/tmp"
export APPTAINER_CACHEDIR="$PACT_ROOT/cache"
export TMPDIR="$PACT_ROOT/tmp"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
apptainer --version
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
sha256sum "$PACT_ROOT/ubuntu24.04.sif" "$PACT_ROOT/aai_cuda_compat_probe.py"
apptainer exec --cleanenv --nv \
  --bind "$HOME:$HOME" \
  --bind "$PACT_ROOT:/opt/pact-compat:ro" \
  --bind "$PACT_ROOT/content:/content" \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:?Slurm GPU visibility missing}" \
  --env 'LD_LIBRARY_PATH=/opt/pact-compat/compat/usr/local/cuda-13.0/compat:/.singularity.d/libs' \
  "$PACT_ROOT/ubuntu24.04.sif" \
  "$PACT_PYTHON" -I -u /opt/pact-compat/aai_cuda_compat_probe.py
