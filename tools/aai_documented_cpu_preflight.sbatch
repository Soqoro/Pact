#!/bin/bash
#SBATCH --job-name=pact-stage2-preflight
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-stage2-preflight-%j.out
#SBATCH --error=pact-stage2-preflight-%j.err
set -euo pipefail
umask 077
# CPU-only wrapper; no GPU allocation, hub access, install or scientific dispatch.
module load apptainer/1.24
PACT_CHECKOUT="${PACT_CHECKOUT:?Set immutable checkout path}"
PACT_COMMIT="${PACT_COMMIT:?Set full reviewed commit SHA}"
PACT_CONFIG="${PACT_CONFIG:?Set private CPU audit config path}"
PACT_SEAL="${PACT_SEAL:?Set verified cohort seal directory}"
PACT_PREFLIGHT_OUTPUT="${PACT_PREFLIGHT_OUTPUT:?Set new private preflight directory}"
[[ "$PACT_COMMIT" =~ ^[0-9a-f]{40}$ ]]
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_DATASET="/dataset/$USER/PACT"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
test -f "$PACT_ENV/install-receipt.json"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
# Small container extraction uses the already tested /tmp lifecycle; study data do not.
export APPTAINER_TMPDIR="$(mktemp -d /tmp/pact-stage2-preflight-XXXXXX)"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
test -d "$PACT_DATASET/stage1-migration-v1/content/pact-stage1/verified-final-tensors"
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_DATASET:$PACT_DATASET" --bind /local:/local \
  --bind "$PACT_DATASET/stage1-migration-v1/content:/content:ro" \
  --env CUDA_VISIBLE_DEVICES= --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTHONDONTWRITEBYTECODE=1 \
  --env "PYTHONPATH=$PACT_CHECKOUT/src" --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u -m pact.revival.documented_preflight --config "$PACT_CONFIG" --seal "$PACT_SEAL" --output "$PACT_PREFLIGHT_OUTPUT"
# Stop after CPU checkpoint validation. No scientific wallet, inference, training or next stage.
