#!/bin/bash
#SBATCH --job-name=pact-runtime-setup
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=pact-runtime-setup-%j.out
#SBATCH --error=pact-runtime-setup-%j.err
set -euo pipefail
module load apptainer/1.24
PACT_ROOT="$HOME/pact-aai-preflight/compat-probe"
PACT_ENV_ROOT="$HOME/pact-aai-preflight/runtime-v1"
PACT_TOOLS="$HOME/Pact/tools"
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
printf '%s  %s\n' bbf8c5438967427787be2514ebc2f101ba7dd89ae6995414f5e0c532e40a12e3 "$PACT_ROOT/ubuntu24.04.sif" | sha256sum --check -
test "$(df -Pk "$HOME" | awk 'NR==2 {print $4}')" -ge 41943040
test "$(df -Pk /tmp | awk 'NR==2 {print $4}')" -ge 1048576
# Exclusive creation: interrupted installations are preserved, never silently reused.
mkdir "$PACT_ENV_ROOT"
mkdir "$PACT_ENV_ROOT/tmp" "$PACT_ENV_ROOT/cache" "$PACT_ENV_ROOT/tools"
cp "$PACT_TOOLS/aai_runtime_install.sh" "$PACT_TOOLS/aai_runtime_probe.py" "$PACT_ENV_ROOT/tools/"
sha256sum "$PACT_ENV_ROOT"/tools/* > "$PACT_ENV_ROOT/tool-sha256.txt"
export TMPDIR="$PACT_ENV_ROOT/tmp"
# Bootstrap installer only; base Python and its packages are unchanged.
python3 -m pip --isolated install --no-cache-dir --only-binary=:all: \
  --index-url https://pypi.org/simple --target "$PACT_ENV_ROOT/bootstrap" uv
"$PACT_ENV_ROOT/bootstrap/bin/uv" --version > "$PACT_ENV_ROOT/uv-version.txt"
export APPTAINER_TMPDIR="$(mktemp -d "/tmp/pact-setup-${SLURM_JOB_ID}-XXXXXX")"
export APPTAINER_CACHEDIR="$PACT_ROOT/cache"
set +e
apptainer exec --cleanenv --bind "$HOME:$HOME" \
  "$PACT_ROOT/ubuntu24.04.sif" /bin/bash \
  "$PACT_ENV_ROOT/tools/aai_runtime_install.sh" "$PACT_ENV_ROOT" "$PACT_ENV_ROOT/tools"
PACT_EXIT=$?
set -e
printf 'Container exit code: %s\n' "$PACT_EXIT"
rmdir "$APPTAINER_TMPDIR"
test "$PACT_EXIT" -eq 0
printf 'RUNTIME_SETUP_COMPLETE; GPU remains unverified.\n'
