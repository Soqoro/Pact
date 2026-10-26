#!/bin/bash
#SBATCH --job-name=pact-container-check
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=pact-container-check-%j.out
#SBATCH --error=pact-container-check-%j.err
set -euo pipefail
module load apptainer/1.24
PACT_ROOT="$HOME/pact-aai-preflight/compat-probe"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
printf '%s  %s\n' \
  bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 \
  "$PACT_ROOT/ubuntu24.04.sif" | sha256sum --check -
# Only the small existing Ubuntu image is extracted here; no models or archives.
df -h /tmp
test "$(df -Pk /tmp | awk 'NR==2 {print $4}')" -ge 1048576
PACT_LOCAL_TMP="$(mktemp -d "/tmp/pact-container-${SLURM_JOB_ID}-XXXXXX")"
export APPTAINER_TMPDIR="$PACT_LOCAL_TMP"
export TMPDIR="$PACT_LOCAL_TMP"
export APPTAINER_CACHEDIR="$PACT_ROOT/cache"
printf 'Temporary directory: %s\n' "$PACT_LOCAL_TMP"
set +e
apptainer exec --cleanenv "$PACT_ROOT/ubuntu24.04.sif" /bin/true
PACT_EXIT=$?
set -e
printf 'Apptainer exit code: %s\n' "$PACT_EXIT"
if ! rmdir "$PACT_LOCAL_TMP"; then
    printf 'Temporary files retained for inspection: %s\n' "$PACT_LOCAL_TMP"
    exit 1
fi
test "$PACT_EXIT" -eq 0
printf 'CONTAINER_LIFECYCLE_OK; no GPU or study operations performed.\n'
