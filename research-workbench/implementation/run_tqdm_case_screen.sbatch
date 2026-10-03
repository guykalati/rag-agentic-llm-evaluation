#!/bin/bash
#SBATCH --job-name=tqdm_case_screen
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:04:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
printf 'version\texit_code\telapsed_seconds\n' > screen_results.tsv
for version in candidate evaluator; do
  started=$SECONDS
  set +e
  timeout 45s bwrap --unshare-all --new-session --die-with-parent \
    --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
    --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$PWD/python369" /env --ro-bind "$PWD/$version" /work \
    --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
    --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH /work \
    --chdir /work /env/bin/python -m pytest -q -s -p no:cacheprovider \
    tqdm/tests/tests_tqdm.py::test_bool > "${version}.log" 2>&1
  code=$?
  set -e
  printf '%s\t%s\t%s\n' "$version" "$code" "$((SECONDS-started))" >> screen_results.tsv
done
cat screen_results.tsv
