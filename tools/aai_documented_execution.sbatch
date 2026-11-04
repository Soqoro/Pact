#!/bin/bash
#SBATCH --job-name=pact-documented-stage
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=48:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-documented-stage-%j.out
#SBATCH --error=pact-documented-stage-%j.err
# Installed adapter only. Submission requires a separate reviewed stage approval.
set -euo pipefail
umask 077
module load apptainer/1.24
: "${PACT_CHECKOUT:?Pinned checkout required}"
: "${PACT_COMMIT:?Full reviewed commit required}"
: "${PACT_EXECUTION_CONFIG:?Private single-stage config required}"
: "${PACT_LOCAL:?Existing /local scratch directory required}"
[[ "$PACT_COMMIT" =~ ^[0-9a-f]{40}$ ]]
[[ "$PACT_LOCAL" == /local/* ]]
test -d "$PACT_LOCAL"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_DATASET="/dataset/$USER/PACT"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_GIT="$HOME/pact-aai-transfer/restoration-v1/git-runtime"
PACT_TOKEN="$HOME/.config/pact/hf-token"
test -f "$PACT_TOKEN"
test -f "$PACT_ENV/tokenizer-dependencies-v1/VERIFIED.json"
test "$(findmnt -n -o TARGET --target /local)" = /local
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
printf '%s  %s\n' 20e6ceff0c67aa902f74c662719108677c758651d9bb1e1eff738835c681f82b "$PACT_COMPAT/compat/usr/local/cuda-13.0/compat/libcuda.so.580.82.07" | sha256sum --check -
mkdir -p "$PACT_LOCAL/container-tmp" "$PACT_LOCAL/tmp"
export APPTAINER_TMPDIR="$PACT_LOCAL/container-tmp"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
apptainer exec --cleanenv --nv --bind /etc/ssl/certs:/etc/ssl/certs:ro \
  --env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
  --env REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
  --bind "$HOME:$HOME" --bind "$PACT_DATASET:$PACT_DATASET" --bind /local:/local \
  --bind "$PACT_DATASET/stage1-migration-v1/content:/content:ro" \
  --bind "$PACT_COMPAT:/opt/pact-compat:ro" \
  --env "PATH=$PACT_GIT:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:?Slurm GPU required}" \
  --env 'LD_LIBRARY_PATH=/opt/pact-compat/compat/usr/local/cuda-13.0/compat:/.singularity.d/libs' \
  --env "TMPDIR=$PACT_LOCAL/tmp" --env "HF_HOME=$PACT_LOCAL/hf-home" \
  --env "USER=$USER" --env "PYTHONPATH=$PACT_CHECKOUT/src" \
  --env PYTHONDONTWRITEBYTECODE=1 --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_CHECKOUT/tools/aai_documented_execution.py" \
  --config "$PACT_EXECUTION_CONFIG" --token-file "$PACT_TOKEN"
# No next-stage submission, cleanup, retry or wallet reset.
