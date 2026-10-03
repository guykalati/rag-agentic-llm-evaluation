#!/bin/bash
#SBATCH --job-name=repair_python381
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:15:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
CONDA=/storage/modules/packages/anaconda/bin/conda
"$CONDA" create --yes --override-channels --channel defaults \
  --prefix "$PWD/python381" python=3.8.1 pip
"$PWD/python381/bin/python" --version
