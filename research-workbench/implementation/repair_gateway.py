"""Candidate-only file operations for a future repair model tool loop.

The model receives return values from these methods, never a shell or raw path.
The evaluator and credentials must remain in the calling application.
"""

import difflib
import hashlib
import os
import tempfile
from pathlib import Path, PurePosixPath


READ_SUFFIXES = {".py", ".md", ".toml", ".txt"}
MAX_FILE_BYTES = 200_000
MAX_REPLACEMENT_BYTES = 20_000


class CandidateGateway:
    def __init__(self, root: Path, editable_package: str):
        self.root = root.resolve(strict=True)
        if not self.root.is_dir():
            raise NotADirectoryError(root)
        if editable_package not in {"pysnooper", "tqdm"}:
            raise ValueError("unknown editable package")
        self.editable_package = editable_package
        if not (self.root / editable_package).is_dir():
            raise ValueError("editable package absent")

    def _file(self, name: str, *, editable: bool = False) -> Path:
        if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
            raise ValueError("invalid path")
        relative = PurePosixPath(name)
        if relative.is_absolute() or any(part in {".", ".."} or part.startswith(".")
                                         for part in relative.parts):
            raise ValueError("path outside candidate")
        path = self.root.joinpath(*relative.parts)
        if not path.resolve().is_relative_to(self.root) or not path.is_file() or path.is_symlink():
            raise ValueError("file outside candidate or unavailable")
        if any(parent.is_symlink() for parent in path.parents if parent != self.root):
            raise ValueError("symlink path")
        if path.suffix not in READ_SUFFIXES or path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("file type or size disallowed")
        if editable and (relative.parts[0] != self.editable_package or
                         "tests" in relative.parts or path.suffix != ".py"):
            raise ValueError("implementation Python files only")
        return path

    def list_files(self) -> list[str]:
        found = []
        for parent, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and
                             not (Path(parent) / d).is_symlink())
            for name in sorted(files):
                if name.startswith("."):
                    continue
                relative = (Path(parent) / name).relative_to(self.root).as_posix()
                try:
                    self._file(relative)
                except ValueError:
                    continue
                found.append(relative)
        return found

    def read_file(self, name: str, start_line: int = 1, line_count: int = 80) -> dict:
        if start_line < 1 or not 1 <= line_count <= 120:
            raise ValueError("invalid line window")
        path = self._file(name)
        raw = path.read_bytes()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        return {"path": name, "start_line": start_line,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "text": "\n".join(lines[start_line - 1:start_line - 1 + line_count])}

    def replace_text(self, name: str, old: str, new: str) -> dict:
        path = self._file(name, editable=True)
        if not old or max(len(old.encode()), len(new.encode())) > MAX_REPLACEMENT_BYTES:
            raise ValueError("empty match or oversized replacement")
        before = path.read_text(encoding="utf-8")
        if before.count(old) != 1 and "\\n" in old:
            normalized_old = old.replace("\\n", "\n")
            if before.count(normalized_old) == 1:
                old, new = normalized_old, new.replace("\\n", "\n")
        if before.count(old) != 1:
            raise ValueError("replacement must match exactly once")
        after = before.replace(old, new, 1)
        if len(after.encode()) > MAX_FILE_BYTES:
            raise ValueError("result too large")
        temp = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                             prefix=".gateway-", delete=False) as output:
                temp = Path(output.name)
                output.write(after)
            os.replace(temp, path)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            fromfile=name, tofile=name))
        return {"path": name, "sha256": hashlib.sha256(after.encode()).hexdigest(),
                "diff": diff}
