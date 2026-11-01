#!/bin/bash
#SBATCH --job-name=pact-source-acquire
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=pact-source-acquire-%j.out
#SBATCH --error=pact-source-acquire-%j.err
set -euo pipefail
umask 077
module load apptainer/1.24
PACT_CHECKOUT="${PACT_CHECKOUT:?Set reviewed checkout path}"
PACT_COMMIT="${PACT_COMMIT:?Set full reviewed commit}"
[[ "$PACT_COMMIT" =~ ^[0-9a-f]{40}$ ]]
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
PACT_DATASET="/dataset/$USER/PACT"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_DEST="$PACT_DATASET/stage2-source-acquisition-v1"
test ! -e "$PACT_DEST"
test -f "$HOME/.config/pact/hf-token"
test -f "$PACT_ENV/install-receipt.json"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
test "$(findmnt -n -o TARGET --target /local)" = /local
PACT_LOCAL=$(mktemp -d "/local/pact-source-acquisition-$USER-XXXXXX")
export APPTAINER_TMPDIR=$(mktemp -d /tmp/pact-source-container-XXXXXX)
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
printf 'Source-only scratch: %s\nDestination: %s\n' "$PACT_LOCAL" "$PACT_DEST"
apptainer exec --cleanenv \
  --bind /etc/ssl/certs:/etc/ssl/certs:ro \
  --bind "$HOME:$HOME" --bind "$PACT_DATASET:$PACT_DATASET" --bind "$PACT_LOCAL:$PACT_LOCAL" \
  --env SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
  --env REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
  --env CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
  --env "HF_TOKEN_PATH=$HOME/.config/pact/hf-token" \
  --env "HF_HOME=$PACT_LOCAL/hf-home" --env HF_HUB_DISABLE_PROGRESS_BARS=1 \
  --env HF_HUB_VERBOSITY=error --env PYTHONDONTWRITEBYTECODE=1 \
  --env "PYTHONPATH=$PACT_CHECKOUT/src" \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_CHECKOUT/tools/aai_stage2_source_acquisition.py" \
  --local "$PACT_LOCAL/download" --destination "$PACT_DEST" --approve-source-acquisition
# Stop after source receipt; never select a cohort, submit another job or run a model.
