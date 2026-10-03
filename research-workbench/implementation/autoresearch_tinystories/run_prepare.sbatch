#!/bin/bash
#SBATCH --job-name=autoresearch_prep
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:15:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
/home/guykalat/.conda/envs/hw1_llm/bin/python prepare.py data
