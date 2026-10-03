"""Harmless isolation check for a future repair-evaluation runner."""

import os
import socket
from pathlib import Path


assert not Path("/home").exists(), "home leaked into sandbox"
assert not Path("/root").exists(), "root home leaked into sandbox"
Path("/tmp/probe").write_text("sandbox writable scratch\n")
assert Path("/tmp/probe").read_text() == "sandbox writable scratch\n"
try:
    Path("/probe.py").write_text("changed")
except OSError:
    pass
else:
    raise AssertionError("source unexpectedly writable")
with socket.socket() as sock:
    assert sock.connect_ex(("1.1.1.1", 53)) != 0, "network unexpectedly reachable"
print(f"sandbox OK: uid={os.getuid()} home_hidden network_blocked source_readonly scratch_writable")
