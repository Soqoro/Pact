#!/bin/bash
#SBATCH --job-name=pact-eval-smoke
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=12:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-eval-smoke-%j.out
#SBATCH --error=pact-eval-smoke-%j.err
set -euo pipefail
umask 077
: "${PACT_SMOKE_CHECKOUT:?Supply pinned orchestration checkout}"
: "${PACT_SMOKE_COMMIT:?Supply orchestration commit}"
test "$(git -C "$PACT_SMOKE_CHECKOUT" rev-parse HEAD)" = "$PACT_SMOKE_COMMIT"
test -z "$(git -C "$PACT_SMOKE_CHECKOUT" status --porcelain)"
export PACT_CHECKOUT="$HOME/pact-aai-preflight/checkouts/export-fix-93b89ce38be7"
export PACT_COMMIT=93b89ce38be743acd6a3aa38177237ce99a3eeeb
export PACT_LOCAL="/local/pact-stage2-documented-export-fixed-$USER"
test "$(findmnt -n -o TARGET --target /local)" = /local
test -d "$PACT_LOCAL"
exec 9>"$PACT_LOCAL/remaining-branches-batch.lock"
flock -n 9
python3 -u "$PACT_SMOKE_CHECKOUT/tools/aai_documented_evaluation_smoke.py"
