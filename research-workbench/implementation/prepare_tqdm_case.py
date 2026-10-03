"""Prepare pinned BugsInPy tqdm case 3 for a one-case replacement screen."""

import argparse
import json
import shutil
from pathlib import Path

from prepare_pysnooper_cases import git_bytes, unpack_commit


def prepare(repo: Path, metadata: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    info = dict(line.split("=", 1) for line in (metadata / "bug.info").read_text().splitlines())
    buggy = info["buggy_commit_id"].strip('"')
    fixed = info["fixed_commit_id"].strip('"')
    candidate, evaluator = output / "candidate", output / "evaluator"
    unpack_commit(repo, buggy, candidate)
    unpack_commit(repo, fixed, evaluator)
    shutil.rmtree(candidate / "tqdm" / "tests")
    shutil.copytree(evaluator / "tqdm" / "tests", candidate / "tqdm" / "tests")
    for path in (candidate / "tqdm").rglob("*.py"):
        relative = path.relative_to(candidate)
        if "tests" not in relative.parts:
            if path.read_bytes() != git_bytes(repo, "show", f"{buggy}:{relative.as_posix()}"):
                raise ValueError(f"buggy implementation changed: {relative}")
    if any(path.name in {".git", "bug_patch.txt"} for path in candidate.rglob("*")):
        raise ValueError("answer or git history exposed")
    result = {"project": "tqdm", "case": 3, "buggy_commit": buggy, "fixed_commit": fixed,
              "python_version": info["python_version"].strip('"'),
              "test_command": (metadata / "run_test.sh").read_text().strip(),
              "test_tree_from_fixed": True,
              "candidate": str(candidate), "evaluator": str(evaluator)}
    (output / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_repo", type=Path)
    parser.add_argument("bug_metadata", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source_repo, args.bug_metadata, args.output), indent=2))
