import json
import unittest

from gemma4_lab.trace_summary import summarize_trace


def step(name, status, model="m"):
    return {
        "source": "agent",
        "message": "thinking",
        "model_name": model,
        "tool_calls": [{"function_name": name, "arguments": {}}],
        "observation": {
            "content": json.dumps(
                {"status": "ok"} if status == "ok" else {"status": "error", "error_type": status}
            )
        },
    }


class TraceSummaryTests(unittest.TestCase):
    def test_counts_failed_edits_and_the_next_call(self):
        trace = {
            "steps": [
                {"source": "system", "message": "prompt"},
                step("edit_file", "FileEditError"),
                step("read_file", "ok"),
                step("edit_file", "FileEditError"),
                step("edit_file", "ok"),
                {"source": "agent", "message": "", "model_name": "m"},
                step("edit_file", "BudgetExceeded"),
            ]
        }
        summary = summarize_trace(trace)
        self.assertEqual(summary["edit_calls"], 4)
        self.assertEqual(summary["failed_edits"], 2)
        self.assertEqual(summary["failed_edit_then_read"], 1)
        self.assertEqual(summary["empty_responses"], 1)
        self.assertEqual(summary["models"], ["m"])
        self.assertEqual(summary["tools"][:2], ["edit_file", "read_file"])
