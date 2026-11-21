#!/bin/bash
#SBATCH --job-name=pact-policy-lock
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-policy-lock-%j.out
#SBATCH --error=pact-policy-lock-%j.err
set -euo pipefail
umask 077
: "${PACT_LOCK_CHECKOUT:?Pinned orchestration checkout required}"
: "${PACT_LOCK_COMMIT:?Pinned orchestration commit required}"
test "$(git -C "$PACT_LOCK_CHECKOUT" rev-parse HEAD)" = "$PACT_LOCK_COMMIT"
test -z "$(git -C "$PACT_LOCK_CHECKOUT" status --porcelain)"
PACT_CHECKOUT="$HOME/pact-aai-preflight/checkouts/export-fix-93b89ce38be7"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = 93b89ce38be743acd6a3aa38177237ce99a3eeeb
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_LOCAL="/local/pact-stage2-documented-export-fixed-$USER"
PACT_DATASET="/dataset/$USER/PACT"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_GIT="$HOME/pact-aai-transfer/restoration-v1/git-runtime"
test "$(findmnt -n -o TARGET --target /local)" = /local
test -f "$PACT_LOCAL/runs/pact-stage2-documented-execution-001/plan.json"
exec 9>"$PACT_LOCAL/remaining-branches-batch.lock"
flock -n 9
module load apptainer/1.24
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
mkdir -p "$PACT_LOCAL/container-tmp"
export APPTAINER_TMPDIR="$PACT_LOCAL/container-tmp"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
apptainer exec --cleanenv \
  --bind "$HOME:$HOME" --bind "$PACT_DATASET:$PACT_DATASET" --bind /local:/local \
  --bind "$PACT_DATASET/stage1-migration-v1/content:/content:ro" \
  --env "PATH=$PACT_GIT:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env "PYTHONPATH=$PACT_CHECKOUT/src" --env "PACT_LOCAL=$PACT_LOCAL" --env "USER=$USER" \
  --env CUDA_VISIBLE_DEVICES= --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  --env PYTHONDONTWRITEBYTECODE=1 --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_LOCK_CHECKOUT/tools/aai_documented_policy_lock.py"
