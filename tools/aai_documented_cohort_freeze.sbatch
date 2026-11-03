#!/bin/bash
#SBATCH --job-name=pact-cohort-freeze
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-cohort-freeze-%j.out
#SBATCH --error=pact-cohort-freeze-%j.err
set -euo pipefail
umask 077
# CPU-only wrapper; no GPU allocation, hub access, install or scientific dispatch.
module load apptainer/1.24
PACT_CHECKOUT="${PACT_CHECKOUT:?Set immutable checkout path}"
PACT_COMMIT="${PACT_COMMIT:?Set full reviewed commit SHA}"
PACT_CONFIG="${PACT_CONFIG:?Set private CPU audit config path}"
PACT_FREEZE_OUTPUT="${PACT_FREEZE_OUTPUT:?Set new private freeze destination}"
[[ "$PACT_COMMIT" =~ ^[0-9a-f]{40}$ ]]
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_DATASET="/dataset/$USER/PACT"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
test -f "$PACT_ENV/install-receipt.json"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
# Small container extraction uses the already tested /tmp lifecycle; study data do not.
export APPTAINER_TMPDIR="$(mktemp -d /tmp/pact-cohort-freeze-XXXXXX)"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_DATASET:$PACT_DATASET" --bind /local:/local \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTHONDONTWRITEBYTECODE=1 \
  --env "PYTHONPATH=$PACT_CHECKOUT/src" --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u -m pact.revival.documented_freeze --config "$PACT_CONFIG" --freeze-output "$PACT_FREEZE_OUTPUT"
# Stop after the CPU seal. No scientific wallet, inference, training or next stage.
