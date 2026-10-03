#!/bin/bash
#SBATCH --job-name=autoresearch_paired_20261001
#SBATCH --partition=rtx3090
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --gres=gpu:rtx_3090:1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:22:00
#SBATCH --array=0-3%2
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
BASE="$PWD"
PYTHON=/home/guykalat/.conda/envs/hw1_llm/bin/python
CELL=$("$PYTHON" - "$BASE" "$SLURM_ARRAY_TASK_ID" <<'PY'
import hashlib,json,sys
from pathlib import Path
base=Path(sys.argv[1]); d=json.loads((base/'batch_manifest.json').read_text()); c=d['cells'][int(sys.argv[2])]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(digest(base/n)==v for n,v in d['source_sha256'].items())
assert digest(base/'data/data_manifest.json')==d['data_manifest_sha256']
assert digest(base/c['candidate_file'])==c['train_sha256']
assert all(digest(base/'data'/f'{split}.bin')==d['fixed_data'][f'{split}_sha256'] for split in ('train','val'))
print(c['id'])
PY
)
[[ "$CELL" =~ ^pair[12]_(no_history|retrieval)$ ]]
WORK="$BASE/cells/$CELL"
test ! -e "$WORK/output"
mkdir "$WORK/output"
sandbox=(bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --ro-bind /sys /sys --proc /proc --dev-bind /dev /dev --tmpfs /tmp \
  --ro-bind /home/guykalat/.conda/envs/hw1_llm /env \
  --dir /work --ro-bind "$BASE/prepare.py" /work/prepare.py \
  --ro-bind "$BASE/verify.py" /work/verify.py \
  --ro-bind "$BASE/test_contract.py" /work/test_contract.py \
  --ro-bind "$WORK/train.py" /work/train.py \
  --ro-bind "$BASE/data" /work/data --bind "$WORK/output" /work/output \
  --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
  --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH /work \
  --setenv EXPERIMENT_DATA_DIR /work/data --setenv EXPERIMENT_OUTPUT_DIR /work/output \
  --chdir /work)
timeout 60s "${sandbox[@]}" /env/bin/python -c 'import os,torch; assert not os.path.exists("/home/guykalat/.ssh"); assert torch.cuda.is_available(); import test_contract'
timeout 1260s "${sandbox[@]}" /env/bin/python /work/train.py
timeout 60s "${sandbox[@]}" /env/bin/python /work/verify.py /work/data /work/output
