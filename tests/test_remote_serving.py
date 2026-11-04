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
                self.assertNotIn("max_lora_rank", settings)
                manifest.write_text(json.dumps({"model": "unexpected checkpoint"}))
                with self.assertRaisesRegex(ValueError, "approved checkpoint"):
                    remote_serving.create_approved_server()

    def test_adapter_manifest_controls_serving_and_empty_discovery_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source-manifest.json").write_text(
                json.dumps({"model": remote_serving.MODEL_SOURCE})
            )
            manifest = types.SimpleNamespace(
                adapters={
                    "probe_zero": types.SimpleNamespace(rank=8),
                    "probe_active": types.SimpleNamespace(rank=8),
                }
            )
            settings = {}
            server_options = {}

            def config(**kwargs):
                settings.update(kwargs)
                return kwargs

            def server(config, **kwargs):
                server_options.update(kwargs)
                return types.SimpleNamespace(build_cmd=lambda: ["server", "--enable-lora"])

            fake_adk = types.SimpleNamespace(
                VllmConfig=config,
                VllmServer=server,
                discover_adapters=lambda path, **kwargs: manifest,
            )
            modules = {
                "torch": types.SimpleNamespace(
                    cuda=types.SimpleNamespace(get_device_name=lambda index: "fake GPU")
                ),
                "adk_submission": fake_adk,
                "swegemma.config": types.SimpleNamespace(
                    ALLOWED_ADAPTER_EXTENSIONS=frozenset({".safetensors"})
                ),
            }
            with (
                patch.object(remote_serving, "MODEL_PATH", root),
                patch.dict(sys.modules, modules),
            ):
                remote_serving.create_approved_server(submission_directory=root / "submission")
                self.assertTrue(settings["enable_lora"])
                self.assertEqual(settings["max_loras"], 2)
                self.assertEqual(settings["max_lora_rank"], 8)
                self.assertIs(server_options["adapter_manifest"], manifest)
                manifest.adapters.clear()
                with self.assertRaisesRegex(ValueError, "discovered adapters"):
                    remote_serving.create_approved_server(submission_directory=root / "submission")
