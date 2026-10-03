#!/bin/bash
#SBATCH --job-name=tqdm_py381_probe
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:04:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
printf 'version\texit_code\telapsed_seconds\n' > py381_screen_results.tsv
for version in candidate evaluator; do
  started=$SECONDS
  set +e
  timeout 45s bwrap --unshare-all --new-session --die-with-parent \
    --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
    --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind /home/guykalat/codex_repair_probe_20260928/python381 /env \
    --ro-bind "$PWD/wheels" /wheels --ro-bind "$PWD/$version" /work \
    --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
    --setenv PYTHONDONTWRITEBYTECODE 1 \
    --setenv PYTHONPATH /work:/wheels/nose-1.3.7-py3-none-any.whl \
    --chdir /work /env/bin/python -m pytest -q -s -p no:cacheprovider \
    tqdm/tests/tests_tqdm.py::test_bool > "py381_${version}.log" 2>&1
  code=$?
  set -e
  printf '%s\t%s\t%s\n' "$version" "$code" "$((SECONDS-started))" \
    >> py381_screen_results.tsv
done
cat py381_screen_results.tsv
