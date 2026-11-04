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
        source = (PROJECT_ROOT / "infrastructure/modal/validate_compiler.py").read_text()
        namespace = {"__file__": "/root/validate_compiler.py", "__name__": "cloud_import_test"}
        with patch.dict(sys.modules, {"modal": fake_modal}):
            exec(compile(source, namespace["__file__"], "exec"), namespace)
        self.assertEqual(namespace["ROOT"], Path("/"))
        self.assertIsNone(namespace["image"])
        self.assertEqual(namespace["WHEEL_MANIFEST"], {})
