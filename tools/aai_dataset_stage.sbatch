#!/bin/bash
#SBATCH --job-name=pact-dataset-stage
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --output=pact-dataset-stage-%j.out
#SBATCH --error=pact-dataset-stage-%j.err
set -euo pipefail
umask 077
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
python3 -B -u "$HOME/Pact/tools/aai_dataset_stage.py"
printf 'DATASET_STAGE_COMPLETE; no inference, deletion or changes to original evidence.\n'
