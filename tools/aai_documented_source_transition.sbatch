#!/bin/bash
#SBATCH --job-name=pact-source-transition
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=pact-source-transition-%j.out
#SBATCH --error=pact-source-transition-%j.err
set -euo pipefail
trap 'printf "Prerequisite failed at line %s\n" "$LINENO" >&2' ERR
umask 077
module load apptainer/1.24
: "${PACT_CHECKOUT:?New reviewed checkout required}"
: "${PACT_COMMIT:?New full commit required}"
PACT_BASE="$HOME/pact-aai-preflight"
PACT_OLD="$(cat "$PACT_BASE/documented-execution-checkout.txt")"
test "$(git -C "$PACT_OLD" rev-parse HEAD)" = 995e814e0883414b1ed56c590faad2e240cdf9b1
test -z "$(git -C "$PACT_OLD" status --porcelain)"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_DATA="/dataset/$USER/PACT"
PACT_RUN="/local/pact-stage2-documented-$USER/runs/pact-stage2-documented-execution-001"
PACT_OUTPUT="$PACT_DATA/stage2-export-source-transition-proposal-v1"
PACT_COMPAT="$PACT_BASE/compat-probe"
PACT_ENV="$PACT_BASE/runtime-v1"
PACT_GIT="$HOME/pact-aai-transfer/restoration-v1/git-runtime"
test -f "$PACT_RUN/plan.json"
test ! -e "$PACT_OUTPUT"
test -x "$PACT_GIT/git"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
export APPTAINER_TMPDIR="$(mktemp -d /tmp/pact-source-transition-XXXXXX)"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_DATA:$PACT_DATA" --bind /local:/local:ro \
  --env "PATH=$PACT_GIT:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env "PYTHONPATH=$PACT_CHECKOUT/src" --env PYTHONDONTWRITEBYTECODE=1 \
  --env CUDA_VISIBLE_DEVICES= --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_CHECKOUT/tools/aai_documented_source_transition.py" propose \
  --old-checkout "$PACT_OLD" --new-checkout "$PACT_CHECKOUT" \
  --run-dir "$PACT_RUN" --output "$PACT_OUTPUT"
# Proposal only. No plan replacement, model loading, wallet or next job.
