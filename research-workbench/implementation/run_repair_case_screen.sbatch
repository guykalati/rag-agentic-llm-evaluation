#!/bin/bash
#SBATCH --job-name=repair_case_screen
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:08:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p screen_logs
printf 'case\tversion\texit_code\telapsed_seconds\n' > screen_results.tsv
for case_id in 1 2 3; do
  case "$case_id" in
    1) target='tests/test_chinese.py::test_chinese' ;;
    2) target='tests/test_pysnooper.py::test_custom_repr_single' ;;
    3) target='tests/test_pysnooper.py::test_file_output' ;;
  esac
  for version in candidates_v2 evaluator; do
    started=$SECONDS
    set +e
    timeout 45s bwrap --unshare-all --new-session --die-with-parent \
      --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
      --proc /proc --dev /dev --tmpfs /tmp \
      --ro-bind "$PWD/python381" /env \
      --ro-bind "$PWD/$version/case_$case_id" /work \
      --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
      --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH /work \
      --chdir /work /env/bin/python -m pytest -q -s -p no:cacheprovider "$target" \
      > "screen_logs/case_${case_id}_${version}.log" 2>&1
    code=$?
    set -e
    printf '%s\t%s\t%s\t%s\n' "$case_id" "$version" "$code" "$((SECONDS-started))" \
      >> screen_results.tsv
  done
done
cat screen_results.tsv
