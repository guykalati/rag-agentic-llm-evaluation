#!/bin/bash
#SBATCH --job-name=autoresearch_isolation
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:02:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p isolation_probe_output
timeout 60s bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --ro-bind /sys /sys --proc /proc --dev-bind /dev /dev --tmpfs /tmp \
  --ro-bind /home/guykalat/.conda/envs/hw1_llm /env \
  --ro-bind "$PWD" /work --bind "$PWD/isolation_probe_output" /work/isolation_probe_output \
  --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
  --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH /work \
  --chdir /work /env/bin/python -c 'import os,torch; assert not os.path.exists("/home/guykalat/.ssh"); assert torch.cuda.is_available(); x=torch.ones(4,device="cuda"); assert x.sum().item()==4; open("/work/isolation_probe_output/probe.txt","w").write(torch.cuda.get_device_name()); print("restricted GPU and hidden home passed", flush=True)'
