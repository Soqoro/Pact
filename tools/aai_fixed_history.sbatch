#!/bin/bash
#SBATCH --job-name=pact-fixed-history
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=48:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-fixed-history-%j.out
#SBATCH --error=pact-fixed-history-%j.err
set -euo pipefail
umask 077
module load apptainer/1.24
PACT_DATASET="/dataset/$USER/PACT"
PACT_EXEC="$PACT_DATASET/stage1-execution-v1"
PACT_CHECKOUT="$HOME/pact-aai-transfer/checkout-a2ad51f60530"
PACT_ENV="$HOME/pact-aai-preflight/runtime-v1"
PACT_COMPAT="$HOME/pact-aai-preflight/compat-probe"
PACT_GIT="$HOME/pact-aai-transfer/restoration-v1/git-runtime"
PACT_TOKEN="$HOME/.config/pact/hf-token"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
test -f "$PACT_TOKEN"
test -f "$PACT_ENV/install-receipt.json"
test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = a2ad51f60530e6dafaf1377eba03d0753f87ff92
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"
test "$(findmnt -n -o FSTYPE --target /local)" = xfs
test "$(findmnt -n -o TARGET --target /local)" = /local
test "$(df -Pk /local | awk 'NR==2 {print $4}')" -ge 125829120
test "$(df -Pk "$PACT_DATASET" | awk 'NR==2 {print $4}')" -ge 20971520
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_COMPAT/ubuntu24.04.sif" | sha256sum --check -
printf '%s  %s\n' 20e6ceff0c67aa902f74c662719108677c758651d9bb1e1eff738835c681f82b "$PACT_COMPAT/compat/usr/local/cuda-13.0/compat/libcuda.so.580.82.07" | sha256sum --check -
# Exclusive dispatch owner: even a preflight failure requires inspection before another submission.
mkdir "$PACT_EXEC"
PACT_LOCAL="$(mktemp -d "/local/pact-${USER}-${SLURM_JOB_ID}-XXXXXX")"
printf '%s\n' "$PACT_LOCAL" > "$PACT_EXEC/local-path.txt"
mkdir "$PACT_LOCAL/content" "$PACT_LOCAL/tmp" "$PACT_LOCAL/container-tmp" "$PACT_EXEC/tools"
cp "$HOME/Pact/tools/"{aai_fixed_history.py,aai_stage1_transport.py,aai_stage1_restore.py,aai_dataset_stage.py} "$PACT_EXEC/tools/"
sha256sum "$PACT_EXEC"/tools/*.py > "$PACT_EXEC/tool-sha256.txt"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader > "$PACT_EXEC/gpu-host.txt"
export APPTAINER_TMPDIR="$PACT_LOCAL/container-tmp"
export APPTAINER_CACHEDIR="$PACT_COMPAT/cache"
export TMPDIR="$PACT_LOCAL/tmp"
# Preserve both scratch and durable state on failure. Never auto-delete or auto-retry.
set +e
apptainer exec --cleanenv --nv --bind "$HOME:$HOME" \
  --bind "$PACT_DATASET:$PACT_DATASET" --bind "$PACT_LOCAL:$PACT_LOCAL" \
  --bind "$PACT_LOCAL/content:/content" --bind "$PACT_COMPAT:/opt/pact-compat:ro" \
  --env "PATH=$PACT_GIT:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  --env "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:?Missing Slurm GPU visibility}" \
  --env 'LD_LIBRARY_PATH=/opt/pact-compat/compat/usr/local/cuda-13.0/compat:/.singularity.d/libs' \
  --env "SLURM_JOB_ID=$SLURM_JOB_ID" --env "SLURMD_NODENAME=$SLURMD_NODENAME" \
  --env "TMPDIR=$PACT_LOCAL/tmp" --env "HF_HOME=$PACT_LOCAL/hf-home" \
  --env PYTHONDONTWRITEBYTECODE=1 --env OMP_NUM_THREADS=4 \
  "$PACT_COMPAT/ubuntu24.04.sif" "$PACT_ENV/venv/bin/python" -B -u \
  "$PACT_EXEC/tools/aai_fixed_history.py" --dataset "$PACT_DATASET" --local "$PACT_LOCAL" \
  --checkout "$PACT_CHECKOUT" --token-file "$PACT_TOKEN"
PACT_EXIT=$?
set -e
printf 'Container exit code: %s\nScratch retained: %s\n' "$PACT_EXIT" "$PACT_LOCAL"
printf '%s\n' "$PACT_EXIT" > "$PACT_EXEC/container-exit-code.txt"
# Slurm logs remain available in the submission directory as well.
for extension in out err; do
  PACT_LOG="$SLURM_SUBMIT_DIR/pact-fixed-history-${SLURM_JOB_ID}.$extension"
  if [ -f "$PACT_LOG" ]; then cp "$PACT_LOG" "$PACT_EXEC/slurm.$extension"; fi
done
exit "$PACT_EXIT"
