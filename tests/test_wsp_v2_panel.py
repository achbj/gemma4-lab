import json
import unittest
from pathlib import Path

from gemma4_lab.wsp_v2_panel import ARMS, assess_v2, sign_test_p

CASES = json.loads((Path(__file__).resolve().parents[1] / "configs/wsp-v2-cases.json").read_text())[
    "cases"
]
EVAL = [c for c in CASES if c["role"] == "eval"]


def rows_for(done):
    """done(case, arm) -> workflow_complete; all rows valid."""
    return [
        {
            "case_id": c["id"],
            "condition": arm,
            "family": c["family"],
            "started": True,
            "completed": True,
            "valid_for_comparison": True,
            "workflow_complete": done(c, arm),
            "actions": [{"name": "read_file" if done(c, arm) else "edit_file"}],
        }
        for c in EVAL
        for arm in ARMS
    ]


PASS_APP = {"passed": True}


class SignTestTest(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(sign_test_p(7, 1), 9 / 256)
        self.assertEqual(sign_test_p(0, 0), 1.0)
        self.assertAlmostEqual(sign_test_p(6, 0), 1 / 64)
        self.assertAlmostEqual(sign_test_p(3, 3), 42 / 64)


class GateTest(unittest.TestCase):
    def setUp(self):
        self.target = [c["id"] for c in EVAL if c["family"] == "prefix_corruption"]

    def test_panel_shape(self):
        self.assertEqual(len(EVAL), 36)
        self.assertEqual(len(self.target), 24)

    def test_clear_win_passes(self):
        winners = set(self.target[:14])

        def done(c, arm):
            if c["family"] != "prefix_corruption":
                return True
            return c["id"] in winners if arm in ("a", "prompt") else c["id"] in self.target[:6]

        result = assess_v2(rows_for(done), EVAL, PASS_APP)
        self.assertTrue(result["primary_passed"], result)
        self.assertEqual(result["target_completed"]["a"], 14)

    def test_no_effect_fails(self):
        result = assess_v2(rows_for(lambda c, arm: arm == "prompt"), EVAL, PASS_APP)
        self.assertFalse(result["primary_passed"])

    def test_gate_four_non_target_losses(self):
        winners = set(self.target[:14])

        def done(c, arm):
            if c["family"] != "prefix_corruption":
                return not (arm == "a" and c["id"] in {x["id"] for x in EVAL[24:27]})
            return c["id"] in winners if arm == "a" else False

        result = assess_v2(rows_for(done), EVAL, PASS_APP)
        self.assertFalse(result["gate4_nontarget_losses_at_most_one"])
        self.assertFalse(result["primary_passed"])

    def test_incomplete_coverage_fails(self):
        rows = rows_for(lambda c, arm: True)[:-1]
        result = assess_v2(rows, EVAL, PASS_APP)
        self.assertFalse(result["valid_coverage"])
        self.assertFalse(result["primary_passed"])

    def test_application_failure_blocks(self):
        winners = set(self.target[:14])

        def done(c, arm):
            if c["family"] != "prefix_corruption":
                return True
            return c["id"] in winners if arm == "a" else False

        result = assess_v2(rows_for(done), EVAL, {"passed": False})
        self.assertFalse(result["primary_passed"])


if __name__ == "__main__":
    unittest.main()


class SixArmTest(unittest.TestCase):
    def test_six_arm_gate_without_repeat_or_read(self):
        v3 = ("base", "zero", "random", "a", "neg", "prompt")
        target = [c["id"] for c in EVAL if c["family"] == "prefix_corruption"]
        winners = set(target[:12])
        rows = [
            {
                "case_id": c["id"],
                "condition": arm,
                "family": c["family"],
                "started": True,
                "completed": True,
                "valid_for_comparison": True,
                "workflow_complete": (
                    True
                    if c["family"] != "prefix_corruption"
                    else (c["id"] in winners if arm in ("a", "prompt") else False)
                ),
                "actions": [{"name": "read_file"}],
            }
            for c in EVAL
            for arm in v3
        ]
        result = assess_v2(rows, EVAL, PASS_APP, v3)
        self.assertTrue(result["primary_passed"], result)
        self.assertNotIn("base_repeat", result["target_comparisons_a_vs"])
