"""Prepare three pinned BugsInPy PySnooper cases without exposing answer patches."""

import argparse
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path


def git_bytes(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=repo)


def unpack_commit(repo: Path, revision: str, destination: Path) -> None:
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(git_bytes(repo, "archive", "--format=tar", revision))) as archive:
        archive.extractall(destination, filter="data")


def prepare(repo: Path, bugs: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.mkdir(parents=True)
    cases = []
    for number in (1, 2, 3):
        case_dir = bugs / str(number)
        info = dict(line.split("=", 1) for line in (case_dir / "bug.info").read_text().splitlines())
        buggy = info["buggy_commit_id"].strip('"')
        fixed = info["fixed_commit_id"].strip('"')
        test_file = info["test_file"].strip('"')
        command = (case_dir / "run_test.sh").read_text().strip()
        if not command.startswith("pytest -q -s ") or ".." in test_file or test_file.startswith("/"):
            raise ValueError(f"unexpected case metadata: {number}")
        candidate = output / "candidates" / f"case_{number}"
        evaluator = output / "evaluator" / f"case_{number}"
        unpack_commit(repo, buggy, candidate)
        unpack_commit(repo, fixed, evaluator)
        # Transfer fixed-revision tests and their local support modules, never implementation files.
        shutil.rmtree(candidate / "tests")
        shutil.copytree(evaluator / "tests", candidate / "tests")
        for path in (candidate / "pysnooper").rglob("*.py"):
            relative = path.relative_to(candidate).as_posix()
            if path.read_bytes() != git_bytes(repo, "show", f"{buggy}:{relative}"):
                raise ValueError(f"buggy implementation changed: {relative}")
        if any(path.name in {".git", "bug_patch.txt"} for path in candidate.rglob("*")):
            raise ValueError(f"answer or git history exposed in case {number}")
        cases.append({"case": number, "buggy_commit": buggy, "fixed_commit": fixed,
                      "test_file": test_file, "test_command": command,
                      "candidate": str(candidate), "evaluator": str(evaluator)})
    manifest = {"source_repo": str(repo), "bugsinpy_metadata": str(bugs), "cases": cases,
                "note": "Evaluator tree and fixed revisions must not be mounted in the agent sandbox."}
    (output / "evaluator" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path)
    parser.add_argument("bug_metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_repo, args.bug_metadata, args.output), indent=2))
