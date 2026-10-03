#!/bin/bash
#SBATCH --job-name=autoresearch_candidate
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:10:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
BASE=/home/guykalat/codex_autoresearch_tinystories_20260929
test -f train.py
test ! -L train.py
test ! -e output/result.json
test "$(sha256sum "$BASE/prepare.py" | cut -d' ' -f1)" = 9e276b61d9e332a457a88e36c39b66f2950cdda5b2769a76b386a1008188db3a
test "$(sha256sum "$BASE/data/data_manifest.json" | cut -d' ' -f1)" = f2ed3ba0d7f173a105650a46a1f8a04b80f3ad3748c8798950f0b0b667e10ac9
test "$(sha256sum "$BASE/data/train.bin" | cut -d' ' -f1)" = c8c5a2c809af4d6412d41bf03e9f0383862b883d694d44a79d8ad33c8717aab8
test "$(sha256sum "$BASE/data/val.bin" | cut -d' ' -f1)" = fbe28e40adbeba86d5cb78f17edeac859bf858d1cc99bbe1a6b69b1f9e008f71
mkdir -p output
sandbox=(bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --ro-bind /sys /sys --proc /proc --dev-bind /dev /dev --tmpfs /tmp \
  --ro-bind /home/guykalat/.conda/envs/hw1_llm /env \
  --dir /work --ro-bind "$BASE/prepare.py" /work/prepare.py \
  --ro-bind "$BASE/verify.py" /work/verify.py \
  --ro-bind "$PWD/train.py" /work/train.py \
  --ro-bind "$BASE/data" /work/data --bind "$PWD/output" /work/output \
  --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
  --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH /work \
  --setenv EXPERIMENT_DATA_DIR /work/data --setenv EXPERIMENT_OUTPUT_DIR /work/output \
  --chdir /work)
timeout 60s "${sandbox[@]}" /env/bin/python -c 'import os,torch,prepare,train; assert not os.path.exists("/home/guykalat/.ssh"); assert torch.cuda.is_available(); assert os.path.isfile("/work/data/data_manifest.json"); print("candidate sandbox preflight passed", flush=True)'
timeout 440s "${sandbox[@]}" /env/bin/python /work/train.py
timeout 100s "${sandbox[@]}" /env/bin/python /work/verify.py /work/data /work/output
