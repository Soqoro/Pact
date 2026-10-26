#!/bin/bash
#SBATCH --job-name=pact-env-probe
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=pact-env-probe-%j.out
#SBATCH --error=pact-env-probe-%j.err

# Environment inspection only. No model downloads, restore or inference.
set -uo pipefail
printf 'JOB: %s\nNODE: %s\n' "${SLURM_JOB_ID:-unset}" "${SLURMD_NODENAME:-unset}"
printf 'CUDA_VISIBLE_DEVICES: %s\n' "${CUDA_VISIBLE_DEVICES:-unset}"
printf 'SLURM_JOB_GPUS: %s\n' "${SLURM_JOB_GPUS:-unset}"
printf 'TMPDIR: %s\nSLURM_TMPDIR: %s\n' "${TMPDIR:-unset}" "${SLURM_TMPDIR:-unset}"
uname -sm
getconf GNU_LIBC_VERSION || true
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader || true
printf '\nSTORAGE\n'
df -h "$PWD" /tmp
if [ -n "${SLURM_TMPDIR:-}" ] && [ -d "$SLURM_TMPDIR" ]; then
    df -h "$SLURM_TMPDIR"
fi
printf '\nRECORDED PATH AVAILABILITY\n'
if [ -d /content ]; then
    ls -ld /content
    if [ -w /content ]; then printf '/content writable\n'; else printf '/content not writable\n'; fi
else
    printf '/content absent; no directory created\n'
fi
printf '\nAVAILABLE TOOLS\n'
for tool in python3 uv conda apptainer singularity; do
    command -v "$tool" || true
done
if command -v apptainer >/dev/null 2>&1; then apptainer --version; fi
if command -v singularity >/dev/null 2>&1; then singularity --version; fi
printf '\nLOADED MODULES\n'
if type module >/dev/null 2>&1; then module list 2>&1; fi
printf '\nPYTHON METADATA (no Torch import or model load)\n'
if command -v python3 >/dev/null 2>&1; then
python3 - <<'PY'
import json, platform
try:
    from importlib import metadata
except ImportError:
    try:
        import importlib_metadata as metadata
    except ImportError:
        metadata = None
packages = {}
for name in ('torch','transformers','peft','accelerate','tokenizers','huggingface-hub','jinja2','numpy','safetensors'):
    try:
        packages[name] = metadata.version(name) if metadata else 'metadata unavailable'
    except metadata.PackageNotFoundError:
        packages[name] = None
print(json.dumps({'python':platform.python_version(),'platform':platform.system(),
                  'machine':platform.machine(),'packages':packages},indent=2))
PY
fi
printf '\nInspection finished. No model calls, downloads, restoration or study-state changes.\n'
