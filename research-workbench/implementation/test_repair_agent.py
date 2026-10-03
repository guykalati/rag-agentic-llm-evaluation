"""Offline checks for the function boundary; no API or cluster calls."""

import json
import tempfile
import unittest
from pathlib import Path

from repair_agent import RepairTools, run_agent, run_ollama_agent, verify_final


class RepairAgentChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.candidate = root / "candidate"
        (self.candidate / "pysnooper").mkdir(parents=True)
        (self.candidate / "pysnooper" / "tracer.py").write_text("old = 1\n")
        self.secret = root / "evaluator" / "answer.py"
        self.secret.parent.mkdir()
        self.secret.write_text("answer = 42\n")
        self.eval_calls = []

        def fake_evaluate(candidate, case, stage, output):
            self.eval_calls.append((candidate, case, stage, output))
            return {"exit_code": "0", "log": "1 passed in 0.1s",
                    "job_id": "123", "slurm_state": "COMPLETED"}

        self.tools = RepairTools(self.candidate, "pysnooper_2", root / "run",
                                 evaluator=fake_evaluate)

    def test_model_can_edit_candidate_and_request_only_named_test(self):
        requests = []
        outputs = [
            {"id": "r1", "usage": {"total_tokens": 10}, "output": [
                {"type": "function_call", "name": "replace_text", "call_id": "c1",
                 "arguments": json.dumps({"path": "pysnooper/tracer.py", "old": "old = 1",
                                          "new": "old = 2"})}]},
            {"id": "r2", "usage": {"total_tokens": 12}, "output": [
                {"type": "function_call", "name": "run_test", "call_id": "c2",
                 "arguments": '{"stage":"target"}'}]},
            {"id": "r3", "usage": {"total_tokens": 8}, "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "Done."}]}]},
        ]

        def transport(payload, key):
            self.assertEqual(key, "fake-key")
            requests.append(payload)
            return outputs.pop(0)

        result = run_agent("fake-model", "Fix the visible bug", self.tools,
                           "fake-key", transport=transport)
        self.assertEqual(result["status"], "finished")
        self.assertEqual(result["tokens"], 30)
        self.assertEqual(self.secret.read_text(), "answer = 42\n")
        self.assertEqual((self.candidate / "pysnooper" / "tracer.py").read_text(),
                         "old = 2\n")
        self.assertEqual([call[2] for call in self.eval_calls], ["target"])
        self.assertEqual(requests[1]["previous_response_id"], "r1")
        self.assertEqual(requests[1]["input"][0]["call_id"], "c1")
        self.assertNotIn("answer = 42", json.dumps(requests))

    def test_invalid_paths_and_test_names_never_reach_evaluator(self):
        for name, arguments in (("read_file", {"path": "../evaluator/answer.py",
                                                      "start_line": 1, "line_count": 5}),
                                ("replace_text", {"path": "../evaluator/answer.py",
                                                  "old": "answer", "new": "leak"}),
                                ("run_test", {"stage": "shell"}),
                                ("run_shell", {"command": "cat /etc/passwd"})):
            with self.subTest(name=name):
                self.assertIn("error", self.tools.call(name, arguments))
        self.assertFalse(self.eval_calls)
        self.assertEqual(self.secret.read_text(), "answer = 42\n")

    def test_failed_exact_match_has_safe_actionable_feedback(self):
        result = self.tools.call("replace_text", {"path": "pysnooper/tracer.py",
                                                  "old": "missing = 1\\n", "new": "old = 2"})
        self.assertEqual(result["message"], "replacement must match exactly once")
        self.assertEqual((self.candidate / "pysnooper" / "tracer.py").read_text(),
                         "old = 1\n")

    def test_escaped_newline_edit_normalizes_only_on_unique_exact_match(self):
        result = self.tools.call("replace_text", {"path": "pysnooper/tracer.py",
                                                  "old": "old = 1\\n", "new": "old = 2\\n"})
        self.assertNotIn("error", result)
        self.assertEqual((self.candidate / "pysnooper" / "tracer.py").read_text(),
                         "old = 2\n")

    def test_ollama_messages_use_the_same_bounded_tools(self):
        requests = []
        outputs = [
            {"prompt_eval_count": 15, "eval_count": 5, "message": {
                "role": "assistant", "content": "", "tool_calls": [{"function": {
                    "name": "read_file", "arguments": {"path": "pysnooper/tracer.py",
                                                    "start_line": 1, "line_count": 5}}}]}},
            {"prompt_eval_count": 20, "eval_count": 7, "message": {
                "role": "assistant", "content": "Done."}},
        ]

        def transport(payload):
            requests.append(json.loads(json.dumps(payload)))
            return outputs.pop(0)

        result = run_ollama_agent("local-model", "Inspect candidate", self.tools,
                                  transport=transport)
        self.assertEqual(result["status"], "finished")
        self.assertEqual(result["tokens"], 47)
        self.assertEqual(result["events"][0]["result"]["text"], "old = 1")
        self.assertEqual(requests[1]["messages"][-1]["role"], "tool")
        self.assertEqual(requests[1]["messages"][-1]["tool_name"], "read_file")
        self.assertNotIn("answer = 42", json.dumps(requests))

    def test_ollama_transport_failure_preserves_completed_tool_trace(self):
        replies = [{"prompt_eval_count": 3, "eval_count": 2, "message": {
            "role": "assistant", "content": "", "tool_calls": [{"function": {
                "name": "list_files", "arguments": {}}}]}}]

        def transport(_payload):
            if replies:
                return replies.pop(0)
            raise ConnectionRefusedError("local service stopped")

        result = run_ollama_agent("local-model", "Inspect candidate", self.tools,
                                  transport=transport)
        self.assertEqual(result["status"], "transport_error")
        self.assertEqual(result["error_type"], "ConnectionRefusedError")
        self.assertEqual(result["events"][0]["tool"], "list_files")

    def test_final_verification_uses_fixed_target_and_regression_selectors(self):
        result = verify_final(self.tools)
        self.assertTrue(result["resolved"])
        self.assertEqual([call[2] for call in self.eval_calls],
                         ["target", "regression"])


if __name__ == "__main__":
    unittest.main()
