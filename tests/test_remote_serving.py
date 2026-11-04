"""Check serving invariants with stubs; never load the native tensor runtime."""

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab import remote_serving


class ServingTests(unittest.TestCase):
    def test_approved_checkpoint_and_serving_flags_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "source-manifest.json"
            manifest.write_text(json.dumps({"model": remote_serving.MODEL_SOURCE}))
            settings = {}

            def config(**kwargs):
                settings.update(kwargs)
                return kwargs

            fake_torch = types.SimpleNamespace(
                cuda=types.SimpleNamespace(get_device_name=lambda index: "fake GPU")
            )
            fake_adk = types.SimpleNamespace(
                VllmConfig=config,
                VllmServer=lambda config: types.SimpleNamespace(build_cmd=lambda: ["server"]),
            )
            with (
                patch.object(remote_serving, "MODEL_PATH", root),
                patch.dict(sys.modules, {"torch": fake_torch, "adk_submission": fake_adk}),
            ):
                _, metadata = remote_serving.create_approved_server()
                self.assertEqual(metadata["model"], remote_serving.MODEL_SOURCE)
                self.assertEqual(settings["tool_call_parser"], "gemma4")
                self.assertEqual(settings["reasoning_parser"], "gemma4")
                self.assertEqual(settings["max_model_len"], 32768)
                self.assertEqual(settings["dtype"], "bfloat16")
                self.assertEqual(settings["tensor_parallel_size"], 1)
                self.assertFalse(settings["enable_lora"])
                manifest.write_text(json.dumps({"model": "unexpected checkpoint"}))
                with self.assertRaisesRegex(ValueError, "approved checkpoint"):
                    remote_serving.create_approved_server()
