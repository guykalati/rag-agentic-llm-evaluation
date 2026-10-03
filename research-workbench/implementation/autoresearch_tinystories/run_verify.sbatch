#!/bin/bash
#SBATCH --job-name=autoresearch_verify
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:03:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
/home/guykalat/.conda/envs/hw1_llm/bin/python verify.py data output
