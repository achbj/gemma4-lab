"""Keep cloud module loading independent of the local checkout's path depth."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab.config import PROJECT_ROOT


class ContainerImportTests(unittest.TestCase):
    def test_real_modal_sdk_accepts_the_panel_decorator_without_network(self):
        import modal

        for filename in (
            "serve_smoke.py",
            "adapter_probe.py",
            "behavior_diagnostic.py",
            "validate_panel.py",
            "inventory_checkpoint.py",
            "inspect_numeric.py",
            "prepare_wsp.py",
        ):
            with self.subTest(module=filename):
                path = PROJECT_ROOT / "infrastructure/modal" / filename
                name = "gemma4_decorator_validation"
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                with (
                    patch.dict(sys.modules, {name: module}),
                    patch.object(modal, "is_local", return_value=False),
                ):
                    spec.loader.exec_module(module)
                self.assertEqual(module.ROOT, Path("/"))

    def test_remote_import_needs_no_local_paths_or_wheels(self):
        fake_modal = types.ModuleType("modal")
        fake_modal.is_local = lambda: False

        class FakeApp:
            def __init__(self, *args, **kwargs):
                self.resources = []

            def function(self, **kwargs):
                self.resources.append(kwargs)
                return lambda function: function

            def local_entrypoint(self):
                return lambda function: function

        fake_modal.App = FakeApp
        fake_modal.Volume = types.SimpleNamespace(from_name=lambda *args, **kwargs: object())
        for name in (
            "validate_compiler.py",
            "serve_smoke.py",
            "adapter_probe.py",
            "behavior_diagnostic.py",
            "validate_panel.py",
            "inventory_checkpoint.py",
            "inspect_numeric.py",
            "prepare_wsp.py",
        ):
            with self.subTest(module=name):
                source = (PROJECT_ROOT / "infrastructure/modal" / name).read_text()
                namespace = {"__file__": f"/root/{name}", "__name__": "cloud_import_test"}
                with patch.dict(sys.modules, {"modal": fake_modal}):
                    exec(compile(source, namespace["__file__"], "exec"), namespace)
                self.assertEqual(namespace["ROOT"], Path("/"))
                self.assertIsNone(namespace["image"])
                if name in {
                    "validate_panel.py",
                    "inventory_checkpoint.py",
                    "inspect_numeric.py",
                    "prepare_wsp.py",
                }:
                    resources = namespace["app"].resources
                    self.assertEqual(len(resources), 1)
                    self.assertNotIn("gpu", resources[0])
                    self.assertEqual(resources[0]["max_containers"], 1)
                    self.assertEqual(resources[0]["retries"], 0)
                    self.assertEqual(resources[0]["cpu"], 2)
                    expected = {
                        "validate_panel.py": (2048, 900),
                        "inventory_checkpoint.py": (4096, 120),
                        "inspect_numeric.py": (6144, 600),
                        "prepare_wsp.py": (4096, 300),
                    }[name]
                    self.assertEqual(resources[0]["memory"], expected[0])
                    self.assertEqual(resources[0]["timeout"], expected[1])
