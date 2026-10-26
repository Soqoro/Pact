#!/bin/bash
#SBATCH --job-name=pact-tokenizer-fix
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=pact-tokenizer-fix-%j.out
#SBATCH --error=pact-tokenizer-fix-%j.err
set -euo pipefail
umask 077
module load apptainer/1.24
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_LOCAL=/local/pact-suaq0001-1106891-d2PoqB
PACT_CHECKOUT="$HOME/pact-aai-transfer/checkout-a2ad51f60530"
PACT_RECORD="$PACT_ENV/tokenizer-dependencies-v1"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
# No environment mutation while a previous execution might still be active.
for PACT_JOB in 1106891 1106899; do
  test "$(sacct -n -X -j "$PACT_JOB" --format=State | awk 'NF {print $1; exit}')" = FAILED
  test -z "$(squeue -h -u "$USER" -o '%A' | awk -v id="$PACT_JOB" '$1 == id {print $1}')"
done
test -d "$PACT_LOCAL/model-cache"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = a2ad51f60530e6dafaf1377eba03d0753f87ff92
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
mkdir "$PACT_RECORD"
cp "$HOME/Pact/tools/aai_tokenizer_dependencies.py" "$PACT_RECORD/"
sha256sum "$PACT_RECORD/aai_tokenizer_dependencies.py" > "$PACT_RECORD/tool-sha256.txt"
export APPTAINER_TMPDIR="$(mktemp -d "$PACT_LOCAL/tokenizer-container-XXXXXX")"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
set +e
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_LOCAL:$PACT_LOCAL" \
  --env "TMPDIR=$PACT_LOCAL/tmp" --env "UV_CACHE_DIR=$PACT_ENV/cache" \
  --env UV_LINK_MODE=copy --env PYTHONDONTWRITEBYTECODE=1 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_RECORD/aai_tokenizer_dependencies.py" --record "$PACT_RECORD" \
  --uv "$PACT_ENV/bootstrap/bin/uv" --checkout "$PACT_CHECKOUT" --local "$PACT_LOCAL"
PACT_EXIT=$?
set -e
printf 'Container exit code: %s\n' "$PACT_EXIT"
rmdir "$APPTAINER_TMPDIR"
exit "$PACT_EXIT"
