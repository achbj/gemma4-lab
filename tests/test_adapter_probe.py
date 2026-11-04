"""Exercise false-positive controls without importing a native tensor runtime."""

import math
import tempfile
import unittest
from pathlib import Path

from gemma4_lab.adapter_probe import (
    PACKAGE_FILES,
    REQUEST_ORDER,
    assess_effect,
    logprob_distance,
    package_hashes,
    write_package,
)


class AdapterProbeTests(unittest.TestCase):
    def test_missing_top_tokens_are_only_a_conservative_difference_bound(self):
        self.assertEqual(logprob_distance({"a": -0.1, "b": -5.0}, {"a": -0.1, "c": -7.0}), 2.0)
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            logprob_distance({"a": math.nan}, {"a": -0.1})

    def test_ignored_adapter_and_control_drift_cannot_pass_as_an_effect(self):
        settings = {
            "prompts": ["prefix"],
            "minimum_effect_nats": 0.2,
            "effect_to_noise_ratio": 10.0,
            "control_tolerance_nats": 0.05,
            "required_effect_cases": 1,
        }
        d = {name: {"token_id:1": -1.0} for name in REQUEST_ORDER}
        case = {"prompt": "prefix", "distributions": d}
        self.assertFalse(assess_effect([case], settings)["passed"])
        for name in ("active_before", "active_after"):
            d[name] = {"token_id:1": -1.5}
        self.assertTrue(assess_effect([case], settings)["passed"])
        d["zero_after"] = {"token_id:1": -1.2}
        self.assertFalse(assess_effect([case], settings)["passed"])

    def test_package_hashes_and_allowlist_block_substitution_or_path_escape(self):
        files = {name: b"diagnostic" for name in PACKAGE_FILES}
        expected = package_hashes(files)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_package(root, files, expected)
            files["agent.yaml"] = b"substituted"
            with self.assertRaisesRegex(ValueError, "CPU preparation"):
                write_package(root, files, expected)
            files["../escape"] = b"escape"
            with self.assertRaisesRegex(ValueError, "unexpected"):
                package_hashes(files)
