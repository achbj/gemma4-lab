"""Keep cloud module loading independent of the local checkout's path depth."""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab.config import PROJECT_ROOT


class ContainerImportTests(unittest.TestCase):
    def test_remote_import_needs_no_local_paths_or_wheels(self):
        fake_modal = types.ModuleType("modal")
        fake_modal.is_local = lambda: False

        class FakeApp:
            def __init__(self, *args, **kwargs):
                pass

            def function(self, **kwargs):
                return lambda function: function

            def local_entrypoint(self):
                return lambda function: function

        fake_modal.App = FakeApp
        fake_modal.Volume = types.SimpleNamespace(from_name=lambda *args, **kwargs: object())
        for name in ("validate_compiler.py", "serve_smoke.py"):
            with self.subTest(module=name):
                source = (PROJECT_ROOT / "infrastructure/modal" / name).read_text()
                namespace = {"__file__": f"/root/{name}", "__name__": "cloud_import_test"}
                with patch.dict(sys.modules, {"modal": fake_modal}):
                    exec(compile(source, namespace["__file__"], "exec"), namespace)
                self.assertEqual(namespace["ROOT"], Path("/"))
                self.assertIsNone(namespace["image"])
