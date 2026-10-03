#!/bin/bash
#SBATCH --job-name=repair_py369_offline
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:12:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
CONDA_PKGS_DIRS=/home/guykalat/.conda/pkgs \
  /storage/modules/packages/anaconda/bin/conda create --offline --copy --yes \
  --override-channels --channel defaults --prefix "$PWD/python369" python=3.6.9 pip
"$PWD/python369/bin/python" --version
"$PWD/python369/bin/python" -m pip --version
