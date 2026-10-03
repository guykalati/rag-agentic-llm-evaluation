"""Security-relevant candidate boundary checks using synthetic files only."""

import tempfile
import unittest
from pathlib import Path

from repair_gateway import CandidateGateway


class CandidateGatewayChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.candidate = base / "candidate"
        (self.candidate / "pysnooper").mkdir(parents=True)
        (self.candidate / "tests").mkdir()
        (self.candidate / "pysnooper" / "tracer.py").write_text("old = 1\n")
        (self.candidate / "tests" / "test_tracer.py").write_text("assert True\n")
        self.secret = base / "evaluator" / "secret.py"
        self.secret.parent.mkdir()
        self.secret.write_text("answer = 42\n")
        self.gateway = CandidateGateway(self.candidate, "pysnooper")

    def test_lists_candidate_only_and_reads_bounded_lines(self):
        self.assertEqual(self.gateway.list_files(),
                         ["pysnooper/tracer.py", "tests/test_tracer.py"])
        result = self.gateway.read_file("pysnooper/tracer.py", 1, 1)
        self.assertEqual(result["text"], "old = 1")
        with self.assertRaises(ValueError):
            self.gateway.read_file("pysnooper/tracer.py", 1, 121)

    def test_rejects_absolute_traversal_hidden_and_symlink_reads(self):
        (self.candidate / "pysnooper" / "answer.py").symlink_to(self.secret)
        for name in (str(self.secret), "../evaluator/secret.py",
                     "pysnooper/answer.py", ".git/config", "pysnooper\\tracer.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.gateway.read_file(name)
        self.assertNotIn("pysnooper/answer.py", self.gateway.list_files())

    def test_replaces_only_one_implementation_match_without_touching_tests(self):
        result = self.gateway.replace_text("pysnooper/tracer.py", "old = 1", "old = 2")
        self.assertIn("+old = 2", result["diff"])
        self.assertEqual((self.candidate / "pysnooper" / "tracer.py").read_text(),
                         "old = 2\n")
        for name in ("tests/test_tracer.py", "../evaluator/secret.py"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.gateway.replace_text(name, "assert", "fail")
        self.assertEqual(self.secret.read_text(), "answer = 42\n")
        with self.assertRaises(ValueError):
            self.gateway.replace_text("pysnooper/tracer.py", "missing", "x")

    def test_existing_temp_symlink_cannot_redirect_a_write(self):
        (self.candidate / "pysnooper" / "tracer.py.gateway-tmp").symlink_to(self.secret)
        self.gateway.replace_text("pysnooper/tracer.py", "old = 1", "old = 3")
        self.assertEqual(self.secret.read_text(), "answer = 42\n")


if __name__ == "__main__":
    unittest.main()
