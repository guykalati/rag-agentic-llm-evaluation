#!/bin/bash
#SBATCH --job-name=repair_sandbox_probe
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:02:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind "$PWD/repair_sandbox_probe.py" /probe.py \
  --chdir /tmp /usr/bin/python3.9 /probe.py
