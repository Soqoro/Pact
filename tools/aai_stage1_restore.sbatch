#!/bin/bash
#SBATCH --job-name=pact-storage-restore
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=pact-storage-restore-%j.out
#SBATCH --error=pact-storage-restore-%j.err
set -euo pipefail
umask 077
module load apptainer/1.24
PACT_BASE="$HOME/pact-aai-transfer/restoration-v1"
PACT_CHECKOUT="$HOME/pact-aai-transfer/checkout-a2ad51f60530"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_BUNDLE="$HOME/pact-aai-transfer/incoming/stage1-AAI-PRIVATE.zip"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
test -f "$PACT_ENV/install-receipt.json"
test -f "$PACT_BUNDLE"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = a2ad51f60530e6dafaf1377eba03d0753f87ff92
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
test "$(df -Pk /tmp | awk 'NR==2 {print $4}')" -ge 1048576
# A separate storage rehearsal; shared-home files are not yet scientific hot storage.
mkdir "$PACT_BASE"
mkdir "$PACT_BASE/content" "$PACT_BASE/tools" "$PACT_BASE/tmp"
cp "$HOME/Pact/tools/aai_stage1_restore.py" "$HOME/Pact/tools/aai_stage1_transport.py" "$PACT_BASE/tools/"
sha256sum "$PACT_BASE"/tools/*.py > "$PACT_BASE/tool-sha256.txt"
python3 "$PACT_BASE/tools/aai_stage1_restore.py" prepare-git --base "$PACT_BASE"
export APPTAINER_TMPDIR="$(mktemp -d "/tmp/pact-restore-${SLURM_JOB_ID}-XXXXXX")"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
export TMPDIR="$PACT_BASE/tmp"
set +e
apptainer exec --cleanenv --bind "$HOME:$HOME" --bind "$PACT_BASE/content:/content" \
  --env "PATH=$PACT_BASE/git-runtime:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env HF_HUB_OFFLINE=1 --env TRANSFORMERS_OFFLINE=1 --env PYTHONDONTWRITEBYTECODE=1 \
  --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_BASE/tools/aai_stage1_restore.py" restore --base "$PACT_BASE" \
  --checkout "$PACT_CHECKOUT" --bundle "$PACT_BUNDLE"
PACT_EXIT=$?
set -e
printf 'Container exit code: %s\n' "$PACT_EXIT"
rmdir "$APPTAINER_TMPDIR"
test "$PACT_EXIT" -eq 0
printf 'RESTORE_JOB_COMPLETE; stop for review. No inference or training performed.\n'
