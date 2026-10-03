#!/bin/bash
#SBATCH --job-name=tqdm_wheels
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --proc /proc --dev /dev --tmpfs /tmp \
  --bind "$PWD/python369" /env --ro-bind "$PWD/wheels" /wheels \
  --chdir /tmp /env/bin/python -m pip install --no-index --find-links /wheels \
  --only-binary=:all: pytest==5.4.3 nose==1.3.7
"$PWD/python369/bin/python" -m pytest --version
