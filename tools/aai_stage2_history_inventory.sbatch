#!/bin/bash
#SBATCH --job-name=pact-stage2-history
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=pact-stage2-history-%j.out
#SBATCH --error=pact-stage2-history-%j.err
set -euo pipefail
umask 077
: "${PACT_CHECKOUT:?Set checkout}" "${PACT_COMMIT:?Set commit}"
[[ "$PACT_COMMIT" =~ ^[0-9a-f]{40}$ ]]
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
# Standard library only; no GPU, container, install or network needed.
python3 -B -u "$PACT_CHECKOUT/tools/stage2_history_inventory.py" \
  --root "/dataset/$USER/PACT" \
  --root "$HOME/pact-aai-transfer" \
  --root "$HOME/pact-aai-downloads" \
  --root "/local/pact-suaq0001-1106891-d2PoqB" \
  --output "/dataset/$USER/PACT/stage2-history-discovery-v1"
