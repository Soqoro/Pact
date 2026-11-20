#!/bin/bash
#SBATCH --job-name=pact-policy-train
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=7-00:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-policy-train-%j.out
#SBATCH --error=pact-policy-train-%j.err
set -euo pipefail
umask 077
: "${PACT_TRAIN_CHECKOUT:?Supply pinned orchestration checkout}"
: "${PACT_TRAIN_COMMIT:?Supply orchestration commit}"
test "$(git -C "$PACT_TRAIN_CHECKOUT" rev-parse HEAD)" = "$PACT_TRAIN_COMMIT"
test -z "$(git -C "$PACT_TRAIN_CHECKOUT" status --porcelain)"
export PACT_CHECKOUT="$HOME/pact-aai-preflight/checkouts/export-fix-93b89ce38be7"
export PACT_COMMIT=93b89ce38be743acd6a3aa38177237ce99a3eeeb
export PACT_LOCAL="/local/pact-stage2-documented-export-fixed-$USER"
test "$(findmnt -n -o TARGET --target /local)" = /local
test -d "$PACT_LOCAL"
exec 9>"$PACT_LOCAL/remaining-branches-batch.lock"
flock -n 9
if [[ "${1:-}" == --from-fit15 ]]; then
  test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
  test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
  module load apptainer/1.24
  pre="$HOME/pact-aai-preflight"
  dataset="/dataset/$USER/PACT"
  image="$pre/compat-probe/ubuntu24.04.sif"
  printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$image" | sha256sum --check -
  mkdir -p "$PACT_LOCAL/container-tmp"
  export APPTAINER_TMPDIR="$PACT_LOCAL/container-tmp"
  apptainer exec --cleanenv --bind "$HOME:$HOME:ro" --bind /local:/local \
    --bind "$dataset:$dataset:ro" --bind "$dataset/stage1-migration-v1/content:/content:ro" \
    --bind /etc/ssl/certs:/etc/ssl/certs:ro --env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    --env REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt --env HF_HOME="$PACT_LOCAL/hf-home" \
    --env PACT_LOCAL="$PACT_LOCAL" --env PACT_DATASET="$dataset" --env PYTHONPATH="$PACT_CHECKOUT/src" \
    --env PYTHONDONTWRITEBYTECODE=1 --env CUDA_VISIBLE_DEVICES= \
    "$image" "$pre/runtime-v1/venv/bin/python" -Bu "$PACT_TRAIN_CHECKOUT/tools/aai_stage2_fit15_inputs.py"
fi
python3 -u "$PACT_TRAIN_CHECKOUT/tools/aai_documented_training_batch.py" "$@"
