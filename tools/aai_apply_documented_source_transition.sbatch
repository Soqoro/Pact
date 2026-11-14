#!/bin/bash
#SBATCH --job-name=pact-apply-source
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=pact-apply-source-%j.out
#SBATCH --error=pact-apply-source-%j.err
set -euo pipefail
trap 'printf "Prerequisite failed at line %s\n" "$LINENO" >&2' ERR
umask 077
module load apptainer/1.24
: "${PACT_HELPER_CHECKOUT:?Clean helper checkout required}"
: "${PACT_HELPER_COMMIT:?Full helper commit required}"
test "$(git -C "$PACT_HELPER_CHECKOUT" rev-parse HEAD)" = "$PACT_HELPER_COMMIT"
test -z "$(git -C "$PACT_HELPER_CHECKOUT" status --porcelain)"
PACT_BASE="$HOME/pact-aai-preflight"
PACT_OLD="$(cat "$PACT_BASE/documented-execution-checkout.txt")"
PACT_TARGET="$PACT_BASE/checkouts/export-fix-93b89ce38be7"
test "$(git -C "$PACT_TARGET" rev-parse HEAD)" = 93b89ce38be743acd6a3aa38177237ce99a3eeeb
test -z "$(git -C "$PACT_TARGET" status --porcelain)"
PACT_DATA="/dataset/$USER/PACT"
PACT_RUN="/local/pact-stage2-documented-$USER/runs/pact-stage2-documented-execution-001"
PACT_NEW="/local/pact-stage2-documented-export-fixed-$USER/runs/pact-stage2-documented-execution-001"
PACT_DURABLE="$PACT_DATA/stage2-documented-execution-export-fixed-v1/pact-stage2-documented-execution-001"
PACT_COMPAT="$PACT_BASE/compat-probe"
PACT_ENV="$PACT_BASE/runtime-v1"
PACT_GIT="$HOME/pact-aai-transfer/restoration-v1/git-runtime"
test -f "$PACT_RUN/plan.json"
test ! -e "$PACT_NEW"
test ! -e "$PACT_DURABLE"
test "$(findmnt -n -o TARGET --target /local)" = /local
test -x "$PACT_GIT/git"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
export APPTAINER_TMPDIR="$(mktemp -d /tmp/pact-apply-source-XXXXXX)"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_DATA:$PACT_DATA" --bind /local:/local \
  --env "PATH=$PACT_GIT:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env "PYTHONPATH=$PACT_TARGET/src" --env PYTHONDONTWRITEBYTECODE=1 \
  --env CUDA_VISIBLE_DEVICES= --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_HELPER_CHECKOUT/tools/aai_apply_documented_source_transition.py" \
  --old-checkout "$PACT_OLD" --target-checkout "$PACT_TARGET" \
  --original-run "$PACT_RUN" \
  --old-persistent "$PACT_DATA/stage2-documented-execution-v1/pact-stage2-documented-execution-001" \
  --proposal "$PACT_DATA/stage2-export-source-transition-proposal-v1" \
  --output "$PACT_NEW" --persistent "$PACT_DURABLE"
# Stop after durable inactive successor export. No GPU or physical-spending stage.
