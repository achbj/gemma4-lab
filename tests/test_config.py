"""Ensure baseline planning cannot silently select another account or overspend."""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from gemma4_lab.config import PROJECT_ROOT, candidate_directory, estimate_run, load_config


class RunPlanTests(unittest.TestCase):
    def test_candidate_mount_cannot_escape_into_the_checkout_or_an_external_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "submissions/baseline"
            candidate.mkdir(parents=True)
            external = root / "external"
            external.mkdir()
            (root / "submissions/escape").symlink_to(external, target_is_directory=True)
            self.assertEqual(candidate_directory(root, "baseline"), candidate.resolve())
            for name in ("..", ".", "", "../external", "escape"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    candidate_directory(root, name)

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
        self.config["modal"]["profile"] = "onepiecification"
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
