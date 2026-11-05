"""Reject false intervention wins, identity drift and incomplete comparisons."""

import copy
import json
import unittest
from pathlib import Path

from gemma4_lab.wsp_evaluation import assess_application, assess_screen

ROOT = Path(__file__).resolve().parents[1]


class ScreenTests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads((ROOT / "configs/wsp-screen-v1.json").read_text())
        self.cases = json.loads((ROOT / self.settings["case_config"]).read_text())["cases"]
        self.rows = []
        for case in self.cases:
            for condition in self.settings["conditions"]:
                name = condition["name"]
                complete = (
                    case["family"] != "prefix_corruption"
                    or case["id"].endswith("03")
                    or name in {"read", "prompt"}
                )
                actions = [
                    {"name": "read_file", "response": {"status": "ok", "filepath": "task.py"}}
                ]
                if name != "read":
                    actions = []
                self.rows.append(
                    {
                        "case_id": case["id"],
                        "condition": name,
                        "family": case["family"],
                        "started": True,
                        "completed": True,
                        "valid_for_comparison": True,
                        "workflow_complete": complete,
                        "source_correct": complete,
                        "source": "correct" if complete else "wrong",
                        "actions": actions,
                        "premature_submit": False,
                    }
                )

    def assess(self, rows=None):
        return assess_screen(
            self.rows if rows is None else rows, self.cases, self.settings, {"passed": True}
        )

    def test_two_prefix_wins_with_identity_and_random_controls_can_pass(self):
        result = self.assess()
        self.assertTrue(result["gate_passed"])
        self.assertEqual(result["prefix_workflow_wins_over_base"], 2)

    def test_equal_random_success_cannot_be_attributed_to_semantic_weights(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            if row["condition"] == "random":
                row["workflow_complete"] = True
        self.assertFalse(self.assess(rows)["gate_passed"])

    def test_zero_identity_drift_and_incomplete_coverage_block_claim(self):
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r["condition"] == "zero")["source"] = "different"
        self.assertFalse(self.assess(rows)["gate_passed"])
        self.assertFalse(self.assess(self.rows[:-1])["gate_passed"])
        rows = copy.deepcopy(self.rows)
        rows[0]["valid_for_comparison"] = False
        self.assertFalse(self.assess(rows)["gate_passed"])

    def test_failure_to_reread_source_or_passing_control_regression_blocks_gate(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            if row["condition"] == "read":
                row["actions"][0]["response"]["filepath"] = "tests/test_task.py"
        self.assertFalse(self.assess(rows)["gate_passed"])
        rows = copy.deepcopy(self.rows)
        next(r for r in rows if r["condition"] == "read" and r["family"] == "passing_control")[
            "workflow_complete"
        ] = False
        self.assertFalse(self.assess(rows)["gate_passed"])

    def test_no_numerical_effect_or_unstable_identity_cannot_pass_application(self):
        cases = [
            {
                "prompt": prompt,
                "distributions": {
                    name: [{"token:1": -1.0}, {"token:1": -1.0}]
                    for name in ("base", "zero", "read", "random")
                },
            }
            for prompt in self.settings["application_prefixes"]
        ]
        self.assertFalse(assess_application(cases, self.settings)["passed"])
        for case in cases:
            for name in ("read", "random"):
                case["distributions"][name] = [{"token:1": -1.1}, {"token:1": -1.1}]
        self.assertTrue(assess_application(cases, self.settings)["passed"])
        incomplete = copy.deepcopy(cases)
        incomplete[0]["distributions"]["read"].pop()
        self.assertFalse(assess_application(incomplete, self.settings)["passed"])
        incorrect = copy.deepcopy(cases)
        incorrect[0]["prompt"] = "different prefix"
        self.assertFalse(assess_application(incorrect, self.settings)["passed"])
        cases[0]["distributions"]["zero"][0] = {"token:1": -1.2}
        self.assertFalse(assess_application(cases, self.settings)["passed"])
