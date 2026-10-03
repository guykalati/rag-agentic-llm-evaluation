#!/bin/bash
#SBATCH --job-name=repair_candidate_eval
#SBATCH --partition=cpu
#SBATCH --account=yshahar
#SBATCH --qos=normal
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:04:00
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"

case "${REPAIR_CASE:?}:${REPAIR_STAGE:?}" in
  pysnooper_2:target)
    test_name='tests/test_pysnooper.py::test_custom_repr_single'
    limit=45
    python_path='/work'
    ;;
  pysnooper_3:target)
    test_name='tests/test_pysnooper.py::test_file_output'
    limit=45
    python_path='/work'
    ;;
  tqdm_3:target)
    test_name='tqdm/tests/tests_tqdm.py::test_bool'
    limit=45
    python_path='/work:/wheels/nose-1.3.7-py3-none-any.whl'
    ;;
  pysnooper_2:regression|pysnooper_3:regression)
    test_name='tests/test_pysnooper.py'
    limit=120
    python_path='/work'
    ;;
  tqdm_3:regression)
    test_name='tqdm/tests/tests_tqdm.py'
    limit=120
    python_path='/work:/wheels/nose-1.3.7-py3-none-any.whl'
    ;;
  *) echo 'invalid case or stage' >&2; exit 2 ;;
esac

started=$SECONDS
set +e
timeout "${limit}s" bwrap --unshare-all --new-session --die-with-parent \
  --ro-bind /usr /usr --ro-bind /lib64 /lib64 --symlink usr/lib /lib \
  --proc /proc --dev /dev --tmpfs /tmp \
  --ro-bind /home/guykalat/codex_repair_probe_20260928/python381 /env \
  --ro-bind /home/guykalat/codex_tqdm_case3_20260928/wheels /wheels \
  --ro-bind "$PWD/candidate" /work \
  --clearenv --setenv PATH /env/bin:/usr/bin --setenv HOME /tmp \
  --setenv PYTHONDONTWRITEBYTECODE 1 --setenv PYTHONPATH "$python_path" \
  --chdir /work /env/bin/python -m pytest -q -s -p no:cacheprovider "$test_name" \
  > pytest.log 2>&1
code=$?
set -e
printf 'case\tstage\ttest\texit_code\telapsed_seconds\n%s\t%s\t%s\t%s\t%s\n' \
  "$REPAIR_CASE" "$REPAIR_STAGE" "$test_name" "$code" "$((SECONDS-started))" \
  > result.tsv
cat result.tsv
