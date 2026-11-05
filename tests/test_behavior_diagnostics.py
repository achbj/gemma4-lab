"""Catch false repair/workflow positives without loading the native ML runtime."""

import json
import unittest
from pathlib import Path

from gemma4_lab.behavior_diagnostics import SeededSession, check_source

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / "configs/behavior-diagnostic-v1.json").read_text())


def exact_editor(before, old, new, allow_multiple=False):
    """Only a local stub; the remote run checks the real editor's seed outcomes."""
    count = before.count(old)
    if count == 0 or count > 1 and not allow_multiple:
        return {"error_message": "Text not found or ambiguous"}
    return {
        "new_content": before.replace(old, new),
        "occurrences": count,
        "strategy": "exact",
        "error_message": None,
    }


class BehaviorDiagnosticTests(unittest.TestCase):
    def session(self, family):
        case = next(c for c in SETTINGS["cases"] if c["family"] == family)
        return SeededSession(case, native_edit=exact_editor)

    def replace(self, session, source):
        return session.dispatch(
            "edit_file", {"filepath": "task.py", "old_string": session.source, "new_string": source}
        )

    def test_all_frozen_seed_conditions_and_native_history(self):
        expected = {
            "prefix_corruption": "syntax_error",
            "failing_assertion": "wrong",
            "passing_control": "correct",
            "irrelevant_pass": "wrong",
        }
        for case in SETTINGS["cases"]:
            with self.subTest(case=case["id"]):
                session = SeededSession(case, native_edit=exact_editor)
                self.assertEqual(session.summary()["source_status"], expected[case["family"]])
                self.assertEqual(session.actions, [])
                self.assertFalse(session.submitted)
                history = session.seed_messages("{factor}, {offset}: {max_actions}", 6)
                for assistant, tool in zip(history[1::2], history[2::2], strict=True):
                    self.assertEqual(assistant["tool_calls"][0]["id"], tool["tool_call_id"])
                    self.assertIsInstance(json.loads(tool["content"]), dict)
                passed = session.seed_turns[-1]["response"]["status"] == "ok"
                self.assertEqual(passed, case["family"] in {"passing_control", "irrelevant_pass"})

    def test_unsafe_and_unsupported_source_is_never_executed(self):
        rejected = [
            "import os\ndef adjust(value):\n    return value\n",
            "def adjust(value):\n    return __import__('os').system('false')\n",
            "def adjust(value):\n    while True: pass\n",
            "def adjust(value):\n    return value ** 1000000000\n",
            "def adjust(value):\n    return True\n",
            "def other(value):\n    return value\n",
            "def adjust(value):\n    return 999999999999999999999999\n",
            "def adjust(value):\n    return (value, value)\n",
        ]
        for source in rejected:
            with self.subTest(source=source):
                self.assertEqual(check_source(source, 1, 0)["status"], "unsupported")
        self.assertEqual(
            check_source("def adjust(value):\n    return (", 1, 0)["status"], "syntax_error"
        )

    def test_equivalent_arithmetic_and_intermediate_assignments_are_accepted(self):
        result = check_source("def adjust(value):\n    n = -2 * value\n    return n + 5\n", -2, 5)
        self.assertEqual(result["status"], "correct")
        self.assertEqual(len(result["observed"]), 7)

    def test_smoke_pass_and_unconditional_submission_do_not_count_as_repair(self):
        session = self.session("irrelevant_pass")
        session.dispatch("submit_patch", {})
        summary = session.summary()
        self.assertFalse(summary["has_diff"])
        self.assertFalse(summary["workflow_complete"])
        self.assertTrue(summary["premature_submit"])

    def test_correct_source_without_current_targeted_test_is_not_workflow_complete(self):
        session = self.session("failing_assertion")
        self.replace(session, "def adjust(value):\n    return 2 * value + 7\n")
        session.dispatch("submit_patch", {})
        self.assertTrue(session.summary()["source_correct"])
        self.assertFalse(session.summary()["workflow_complete"])
        self.assertTrue(session.summary()["premature_submit"])

    def test_positive_control_can_submit_without_unnecessary_repair(self):
        session = self.session("passing_control")
        session.dispatch("submit_patch", {})
        self.assertTrue(session.summary()["workflow_complete"])
        self.assertFalse(session.summary()["premature_submit"])

    def test_edit_invalidates_passing_test_until_current_source_is_checked(self):
        session = self.session("passing_control")
        self.replace(session, "def adjust(value):\n    return value * 2 - 5\n")
        self.assertFalse(session.summary()["target_checked_current"])
        response = session.dispatch(
            "run_command", {"command": "python -m pytest tests/test_task.py"}
        )
        self.assertEqual(response["status"], "ok")
        session.dispatch("submit_patch", {})
        self.assertTrue(session.summary()["workflow_complete"])

    def test_tool_allowlist_rejects_shell_test_edits_and_path_escape(self):
        session = self.session("passing_control")
        for args in [
            {"filepath": "tests/test_task.py", "old_string": "x", "new_string": "y"},
            {"filepath": "../task.py", "old_string": "x", "new_string": "y"},
        ]:
            self.assertEqual(session.dispatch("edit_file", args)["status"], "error")
        for command in ["pytest tests/test_task.py; whoami", "cat /etc/passwd", "pytest"]:
            self.assertEqual(
                session.dispatch("run_command", {"command": command})["status"], "error"
            )
        self.assertEqual(
            session.dispatch("read_file", {"filepath": "/workspace/task.py"})["content"],
            session.source,
        )
