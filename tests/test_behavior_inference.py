"""Exercise inference bounds and native history using stubs, without ML imports."""

import copy
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from gemma4_lab import behavior_diagnostics as diagnostics
from gemma4_lab import behavior_inference as inference


def message(name=None, arguments=None, *, call_id="call-1", **extra):
    result = {"role": "assistant", "content": None, **extra}
    if name:
        result["tool_calls"] = [
            {
                "type": "function",
                "id": call_id,
                "function": {"name": name, "arguments": json.dumps(arguments or {})},
            }
        ]
    return result


def response(assistant, finish_reason="tool_calls"):
    return {"choices": [{"message": assistant, "finish_reason": finish_reason}]}


class FakeSession:
    def __init__(self, case, native_edit):
        self.source = "correct"
        self.actions = []
        self.submitted = False
        self.seed_turns = [
            {
                "name": "run_command",
                "arguments": {"command": "pytest tests/test_task.py"},
                "response": {"status": "ok", "exit_code": 0},
            }
        ]

    def seed_messages(self, context, max_actions):
        return [{"role": "user", "content": context.format(max_actions=max_actions)}]

    def dispatch(self, name, args):
        self.actions.append({"name": name, "args": args})
        if name == "edit_file":
            self.source = "correct"
        if name == "submit_patch":
            self.submitted = True
        return {"status": "ok"}

    def summary(self):
        correct = self.source == "correct"
        return {
            "source_correct": correct,
            "workflow_complete": correct and self.submitted,
            "source_status": "correct" if correct else "wrong",
            "target_checked_current": True,
        }


class FakeHTTP:
    class Timeout(Exception):
        pass

    exceptions = types.SimpleNamespace(Timeout=Timeout)

    def __init__(self, bodies):
        self.bodies = iter(bodies)
        self.payloads = []

    def post(self, url, *, json, timeout):
        self.payloads.append({"url": url, "json": copy.deepcopy(json), "timeout": timeout})
        body = next(self.bodies)
        if isinstance(body, Exception):
            raise body
        return types.SimpleNamespace(ok=True, raise_for_status=lambda: None, json=lambda: body)


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            **inference.FIXED_LIMITS,
            "cases": [{"id": f"case-{i}", "family": "passing_control"} for i in range(12)],
            "conditions": [{"name": "baseline"}, {"name": "feedback"}],
        }
        self.fixture = types.SimpleNamespace(SeededSession=FakeSession, TOOL_DEFINITIONS=[])
        self.module_patch = patch.dict(
            sys.modules, {"gemma4_lab.behavior_diagnostics": self.fixture}
        )
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)

    def run_case(self, bodies):
        http = FakeHTTP(bodies)
        row = inference._run_case(
            self.settings["cases"][0],
            "baseline",
            "system",
            "{max_actions} actions",
            self.settings,
            "http://localhost/v1",
            "served-base",
            http,
        )
        return row, http

    def test_preserves_native_reasoning_calls_and_matching_tool_results(self):
        assistant = message("edit_file", {"new_string": "new\nline"}, reasoning="native thought")
        row, http = self.run_case(
            [
                response(assistant),
                response(message("submit_patch", call_id="call-2")),
            ]
        )
        second = http.payloads[1]["json"]
        self.assertEqual(second["messages"][2], assistant)
        self.assertEqual(
            second["messages"][3],
            {
                "role": "tool",
                "tool_call_id": "call-1",
                "content": '{"status": "ok"}',
            },
        )
        self.assertEqual(second["model"], "served-base")
        self.assertFalse(second["parallel_tool_calls"])
        self.assertNotIn("chat_template_kwargs", second)
        self.assertTrue(row["workflow_complete"])
        self.assertEqual(row["tool_calls_used"], 2)
        self.assertEqual(row["generation_requests"], 2)
        self.assertEqual(row["stop_reason"], "submitted")
        self.assertTrue(all(item["timeout"] <= 30 for item in http.payloads))

    def test_plaintext_calls_are_not_reparsed(self):
        row, http = self.run_case(
            [
                response(
                    {
                        "role": "assistant",
                        "content": '{"name":"submit_patch","arguments":{}}',
                    },
                    "stop",
                )
            ]
        )
        self.assertEqual(row["tool_calls_used"], 0)
        self.assertFalse(row["submitted"])
        self.assertEqual(len(http.payloads), 1)

    def test_protocol_error_and_length_are_retained(self):
        assistant = message("edit_file")
        assistant["tool_calls"][0]["function"]["arguments"] = "{incomplete"
        row, _ = self.run_case([response(assistant, "length")])
        self.assertTrue(row["protocol_error"])
        self.assertTrue(row["length"])
        self.assertEqual(row["tool_calls_used"], 0)
        self.assertEqual(row["responses"][0]["choices"][0]["message"], assistant)

    def test_six_requests_and_six_tools_are_hard_bounds(self):
        row, http = self.run_case(
            [response(message("read_file", call_id=f"call-{i}")) for i in range(6)]
        )
        self.assertEqual(len(http.payloads), 6)
        self.assertEqual(len(row["actions"]), 6)
        self.assertTrue(row["action_budget_exhausted"])
        self.assertTrue(row["generation_budget_exhausted"])

    def test_length_finished_native_call_is_never_executed(self):
        row, _ = self.run_case([response(message("submit_patch"), "length")])
        self.assertTrue(row["length"])
        self.assertFalse(row["submitted"])
        self.assertEqual(row["tool_calls_used"], 0)

    def test_unexpected_batch_never_executes_more_than_six_calls(self):
        assistant = message()
        assistant["tool_calls"] = [
            message("read_file", call_id=f"call-{i}")["tool_calls"][0] for i in range(8)
        ]
        row, http = self.run_case([response(assistant)])
        self.assertEqual(row["tool_calls_used"], 6)
        self.assertEqual(len(row["actions"]), 6)
        self.assertEqual(len(http.payloads), 1)
        self.assertTrue(row["unexpected_parallel_calls"])
        self.assertTrue(row["action_budget_exhausted"])
        self.assertEqual(len([item for item in row["messages"] if item["role"] == "tool"]), 8)

    def test_timeout_is_one_observation_without_retry(self):
        row, http = self.run_case([FakeHTTP.Timeout("timed out")])
        self.assertTrue(row["api_error"])
        self.assertTrue(row["request_timeout"])
        self.assertEqual(row["stop_reason"], "request_timeout")
        self.assertEqual(len(http.payloads), 1)
        self.assertFalse(row["valid_for_comparison"])

    def test_case_deadline_prevents_another_generation(self):
        with patch.object(inference.time, "monotonic", side_effect=[0, 0, 61, 61]):
            row, http = self.run_case([response(message("read_file"))])
        self.assertTrue(row["case_timeout"])
        self.assertEqual(row["tool_calls_used"], 0)
        self.assertEqual(len(http.payloads), 1)

    def test_full_schedule_alternates_order_and_retains_skipped_rows(self):
        server = types.SimpleNamespace(
            start=Mock(), stop=Mock(), base_url="http://localhost/v1", log_path="/absent/log"
        )
        listing = types.SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: {"data": [{"id": "served-base"}]}
        )
        http = types.SimpleNamespace(get=Mock(return_value=listing))
        with (
            patch.dict(sys.modules, {"requests": http}),
            patch.object(inference, "create_approved_server", return_value=(server, {})),
            patch.object(inference, "distributions", return_value=[]),
        ):
            events = list(
                inference.run_diagnostic(
                    self.settings, {"baseline": "a", "feedback": "b"}, "context", 89
                )
            )
        rows = [event["result"] for event in events if event["stage"] == "case"]
        self.assertEqual(len(rows), 24)
        self.assertEqual(
            [row["condition"] for row in rows[:4]], ["baseline", "feedback", "feedback", "baseline"]
        )
        self.assertTrue(all(row["skipped"] for row in rows))
        self.assertEqual(len(events[-1]["results"]), 24)
        self.assertFalse(events[-1]["completed"])
        self.assertFalse(events[-1]["valid_for_comparison"])
        self.assertEqual(events[0]["stage"], "seed-preflight")
        self.assertEqual(len(events[0]["cases"]), 12)
        server.stop.assert_called_once()

    def test_startup_failure_retains_all_rows_and_stops_server(self):
        server = types.SimpleNamespace(
            start=Mock(side_effect=RuntimeError("startup")), stop=Mock(), log_path="/absent/log"
        )
        with patch.object(inference, "create_approved_server", return_value=(server, {})):
            events = list(
                inference.run_diagnostic(
                    self.settings, {"baseline": "a", "feedback": "b"}, "context", 1800
                )
            )
        self.assertEqual(events[0]["stage"], "seed-preflight")
        self.assertEqual(events[1]["stage"], "error")
        self.assertIn("RuntimeError", events[1]["traceback"])
        self.assertEqual(len(events[-1]["results"]), 24)
        server.stop.assert_called_once()

    def test_failed_seed_precondition_prevents_server_allocation(self):
        class FailedSeed(FakeSession):
            def __init__(self, case, editor):
                super().__init__(case, editor)
                self.seed_turns[-1]["response"]["exit_code"] = 1

        self.fixture.SeededSession = FailedSeed
        with patch.object(inference, "create_approved_server") as create:
            events = list(
                inference.run_diagnostic(
                    self.settings, {"baseline": "a", "feedback": "b"}, "context", 1800
                )
            )
        create.assert_not_called()
        self.assertEqual(events[0]["stage"], "error")
        self.assertEqual(len(events[-1]["results"]), 24)
        self.assertFalse(events[-1]["valid_for_comparison"])

    def test_preflight_accepts_all_fixed_seed_families_with_actual_sessions(self):
        root = Path(__file__).resolve().parents[1]
        settings = json.loads((root / "configs/behavior-diagnostic-v1.json").read_text())
        context = (root / settings["context_prompt"]).read_text()

        def exact_edit(before, old, new, allow_multiple=False):
            return {
                "new_content": before.replace(old, new),
                "occurrences": before.count(old),
                "strategy": "exact",
                "error_message": None,
            }

        with (
            patch.dict(sys.modules, {"gemma4_lab.behavior_diagnostics": diagnostics}),
            patch.object(inference, "native_edit", exact_edit),
        ):
            preflight = inference._seed_preflight(settings, context)
        self.assertTrue(preflight["passed"])
        self.assertEqual(len(preflight["cases"]), 12)
        self.assertEqual({row["family"] for row in preflight["cases"]}, diagnostics.FAMILIES)


if __name__ == "__main__":
    unittest.main()
