"""Check package boundaries and inspection gates without a local tensor runtime."""

import builtins
import copy
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab import wsp_adapter as adapter
from gemma4_lab.remote_serving import MODEL_SOURCE


def inspection_fixture():
    return {
        "completed": True,
        "inspection_passed": True,
        "runtime_identity_passed": True,
        "modal_image_id": "expected-image",
        "git_commit": "fixture",
        "settings": {
            "model": MODEL_SOURCE,
            "expected_runtime_image": "expected-image",
            "rank": 8,
            "target_layer": 41,
            "kv_source_layer": 23,
            "seed": 20261105,
            "relative_frobenius": 0.01,
        },
        "result": {
            "model": MODEL_SOURCE,
            "base_modified": False,
            "geometry": {
                "passed": True,
                "a": [1.0] + [0.0] * 4095,
                "b": [1.0] + [0.0] * 2559,
                "proposed_beta": 0.48,
            },
            "output_projection": {"frobenius_norm": 48.0},
            "projection_provenance": [{"module": adapter.EXPECTED_MODULE, "shape": [2560, 4096]}],
            "verified_model_sha256": {
                "config.json": "0" * 64,
                **{f"file-{i}": "1" * 64 for i in range(7)},
            },
        },
    }


class WSPAdapterTests(unittest.TestCase):
    def setUp(self):
        original = builtins.__import__

        def guard(name, *args, **kwargs):
            if name.split(".")[0] in {"torch", "safetensors", "adk_submission"}:
                raise AssertionError("Native/runtime import attempted before validation")
            return original(name, *args, **kwargs)

        self.guard = patch("builtins.__import__", guard)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_frozen_valid_vectors_need_no_tensor_runtime(self):
        a, b, beta = adapter._validated_vectors(inspection_fixture())
        self.assertEqual((len(a), len(b), beta), (4096, 2560, 0.48))

    def test_failed_inspection_identity_and_fixed_target_are_rejected_before_import(self):
        for key in ["completed", "inspection_passed", "runtime_identity_passed"]:
            fixture = inspection_fixture()
            fixture[key] = False
            with self.subTest(key=key), self.assertRaises(ValueError):
                adapter.prepare_intervention(fixture, "adapter: wsp_read")
        mutations = [
            ("model", "wrong-model"),
            ("rank", 1),
            ("target_layer", 40),
            ("kv_source_layer", 24),
            ("seed", True),
            ("relative_frobenius", 0.02),
        ]
        for key, value in mutations:
            fixture = inspection_fixture()
            fixture["settings"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                adapter.prepare_intervention(fixture, "adapter: wsp_read")

    def test_nonfinite_nonunit_mismatched_vectors_and_beta_are_rejected(self):
        for mutation in [
            "collinear_gate",
            "short_a",
            "nan_a",
            "nonunit_b",
            "negative_beta",
            "wrong_beta",
        ]:
            fixture = inspection_fixture()
            geometry = fixture["result"]["geometry"]
            if mutation == "collinear_gate":
                geometry["passed"] = False
            elif mutation == "short_a":
                geometry["a"].pop()
            elif mutation == "nan_a":
                geometry["a"][0] = math.nan
            elif mutation == "nonunit_b":
                geometry["b"][0] = 2
            else:
                geometry["proposed_beta"] = -0.48 if mutation == "negative_beta" else 0.4
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                adapter.prepare_intervention(fixture, "adapter: wsp_read")

    def test_base_modification_incomplete_hashes_and_wrong_module_are_rejected(self):
        for mutation in ["modified", "hashes", "module", "runtime"]:
            fixture = inspection_fixture()
            if mutation == "modified":
                fixture["result"]["base_modified"] = True
            elif mutation == "hashes":
                fixture["result"]["verified_model_sha256"].pop("config.json")
            elif mutation == "module":
                fixture["result"]["projection_provenance"][0]["shape"] = [2560, 2048]
            else:
                fixture["modal_image_id"] = "different"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                adapter.prepare_intervention(fixture, "adapter: wsp_read")

    def test_exact_seven_file_allowlist_and_hashes_protect_transport(self):
        files = {name: b"fixture" for name in adapter.PACKAGE_FILES}
        hashes = adapter.package_hashes(files)
        self.assertEqual(len(hashes), 7)
        for mutation in ["missing", "extra", "empty", "too_big"]:
            changed = copy.copy(files)
            if mutation == "missing":
                changed.pop("agent.yaml")
            elif mutation == "extra":
                changed["../escape"] = b"fixture"
            elif mutation == "empty":
                changed["agent.yaml"] = b""
            else:
                changed["agent.yaml"] = b"X" * adapter.MAX_PACKAGE_BYTES
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                adapter.package_hashes(changed)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            adapter.write_package(root, files, hashes)
            self.assertEqual((root / "agent.yaml").read_bytes(), files["agent.yaml"])
            files["agent.yaml"] = b"substituted"
            with self.assertRaises(ValueError):
                adapter.write_package(root, files, hashes)


if __name__ == "__main__":
    unittest.main()
