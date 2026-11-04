"""Ensure baseline planning cannot silently select another account or overspend."""

import unittest
from decimal import Decimal

from gemma4_lab.config import PROJECT_ROOT, estimate_run, load_config


class RunPlanTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(PROJECT_ROOT / "configs/baseline.toml")

    def test_baseline_includes_startup_and_idle_time(self):
        result = estimate_run(self.config)
        self.assertEqual(result["bounded_seconds"], 2702)
        self.assertLess(Decimal(result["estimated_compute_usd"]), Decimal("2"))
        self.assertFalse(result["launches_compute"])

    def test_a10g_cannot_reuse_the_cheaper_l4_rate(self):
        self.config["modal"]["gpu"] = "A10G"
        with self.assertRaisesRegex(ValueError, "underestimates"):
            estimate_run(self.config)
        self.config["rates_usd_per_second"]["gpu"] = "0.000305556"
        self.assertLess(Decimal(estimate_run(self.config)["estimated_compute_usd"]), Decimal("2"))

    def test_wrong_account_and_multiple_gpus_are_rejected(self):
        self.config["modal"]["profile"] = "other-account"
        with self.assertRaisesRegex(ValueError, "authorized"):
            estimate_run(self.config)
        self.config["modal"]["profile"] = "ach-bj100"
        self.config["modal"]["gpu_count"] = 4
        with self.assertRaisesRegex(ValueError, "one GPU"):
            estimate_run(self.config)

    def test_timeout_and_allocation_cannot_exceed_budget(self):
        self.config["modal"]["timeout_seconds"] = 100_000
        with self.assertRaisesRegex(ValueError, "allocation"):
            estimate_run(self.config)
        self.config["modal"]["timeout_seconds"] = 1800
        self.config["budget"]["initial_run_usd"] = "100"
        with self.assertRaisesRegex(ValueError, "allocation"):
            estimate_run(self.config)

    def test_invalid_resource_and_rate_values_are_rejected(self):
        self.config["modal"]["timeout_seconds"] = True
        with self.assertRaisesRegex(ValueError, "positive integer"):
            estimate_run(self.config)
        self.config["modal"]["timeout_seconds"] = 1800
        for value in ("NaN", "Infinity", "-1", "nonsense"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.config["rates_usd_per_second"]["gpu"] = value
                estimate_run(self.config)
