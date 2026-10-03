"""Send one candidate to a fixed, no-network Slurm test runner.

Only the trusted controller calls this module. Model arguments never become
shell commands, remote paths, test names, or Slurm options.
"""

import csv
import hashlib
import json
import secrets
import subprocess
import time
from pathlib import Path


HOST = "guykalat@slurm.bgu.ac.il"
REMOTE_BASE = "/home/guykalat/codex_agent_repair_runs_20260929"
JOB_SCRIPT = Path(__file__).with_name("run_repair_candidate_eval.sbatch")
CASES = {"pysnooper_2", "pysnooper_3", "tqdm_3"}
STAGES = {"target", "regression"}
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY"}


def command(argv: list[str], timeout: int = 30) -> str:
    return subprocess.run(argv, check=True, capture_output=True, text=True,
                          timeout=timeout).stdout.strip()


def validate_candidate(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("candidate directory missing or symlinked")
    total = 0
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_symlink() or ".git" in relative.parts or path.name == "bug_patch.txt":
            raise ValueError(f"unsafe candidate path: {relative}")
        if path.is_file():
            total += path.stat().st_size
    if total > 20_000_000:
        raise ValueError("candidate exceeds 20 MB")


def candidate_digest(root: Path) -> str:
    validate_candidate(root)
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def evaluate(candidate: Path, case: str, stage: str, results_dir: Path,
             poll_seconds: int = 4) -> dict:
    if case not in CASES or stage not in STAGES:
        raise ValueError("unknown case or stage")
    candidate = candidate.resolve(strict=True)
    validate_candidate(candidate)
    if results_dir.exists():
        raise FileExistsError(results_dir)
    results_dir.mkdir(parents=True)
    remote = f"{REMOTE_BASE}/{secrets.token_hex(8)}"
    command(["ssh", "-o", "BatchMode=yes", HOST, f"mkdir -m 700 -p {remote}"])
    command(["rsync", "-a", f"{candidate}/", f"{HOST}:{remote}/candidate/"], timeout=120)
    command(["rsync", "-a", str(JOB_SCRIPT), f"{HOST}:{remote}/"], timeout=60)
    job_id = command(["ssh", "-o", "BatchMode=yes", HOST,
                      f"cd {remote} && sbatch --parsable "
                      f"--export=ALL,REPAIR_CASE={case},REPAIR_STAGE={stage} "
                      f"{JOB_SCRIPT.name}"]).split(";")[0]
    if not job_id.isdecimal():
        raise RuntimeError(f"unexpected Slurm job ID: {job_id}")
    deadline = time.monotonic() + 330
    state = "UNKNOWN"
    while time.monotonic() < deadline:
        rows = command(["ssh", "-o", "BatchMode=yes", HOST,
                        f"sacct -j {job_id} --noheader --format=JobIDRaw,State -P"])
        for row in rows.splitlines():
            parts = row.strip().split("|")
            if len(parts) >= 2 and parts[0] == job_id:
                state = parts[1].split()[0]
                break
        if state in TERMINAL:
            break
        time.sleep(poll_seconds)
    else:
        raise TimeoutError(f"Slurm job {job_id} not terminal; remote run {remote}")
    for name in ("result.tsv", "pytest.log"):
        command(["rsync", "-a", f"{HOST}:{remote}/{name}", str(results_dir / name)],
                timeout=60)
    with (results_dir / "result.tsv").open(newline="") as source:
        result = next(csv.DictReader(source, delimiter="\t"))
    result.update({"job_id": job_id, "slurm_state": state, "remote_run": remote,
                   "log": (results_dir / "pytest.log").read_text(errors="replace")[-6000:]})
    (results_dir / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
