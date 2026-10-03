#!/bin/bash
#SBATCH --job-name=repair_regression_screen
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:08:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p regression_logs
printf 'case\texit_code\telapsed_seconds\n' > regression_results.tsv
for case_id in pysnooper_2 pysnooper_3 tqdm_3; do
  case "$case_id" in
    pysnooper_2)
      source_dir="$PWD/evaluator/case_2"
      test_file='tests/test_pysnooper.py'
      python_path='/work'
      ;;
    pysnooper_3)
      source_dir="$PWD/evaluator/case_3"
      test_file='tests/test_pysnooper.py'
      python_path='/work'
      ;;
    tqdm_3)
      source_dir='/home/guykalat/codex_tqdm_case3_20260928/evaluator'
      test_file='tqdm/tests/tests_tqdm.py'
      python_path='/work:/wheels/nose-1.3.7-py3-none-any.whl'
      ;;
  esac
  started=$SECONDS
  set +e
  timeout 120s bwrap --unshare-all --new-session --die-with-parent \
    --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
    --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$PWD/python381" /env \
    --ro-bind /home/guykalat/codex_tqdm_case3_20260928/wheels /wheels \
    --ro-bind "$source_dir" /work \
    --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
    --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH "$python_path" \
    --chdir /work /env/bin/python -m pytest -q -s -p no:cacheprovider "$test_file" \
    > "regression_logs/${case_id}.log" 2>&1
  code=$?
  set -e
  printf '%s\t%s\t%s\n' "$case_id" "$code" "$((SECONDS-started))" \
    >> regression_results.tsv
done
cat regression_results.tsv
