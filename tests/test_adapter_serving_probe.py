"""A failed server must preserve the stream result and release its resources."""

import sys
import types
import unittest
from unittest.mock import Mock, patch

from gemma4_lab.adapter_probe import ADAPTER_NAMES, PACKAGE_FILES, package_hashes
from gemma4_lab.adapter_serving_probe import run_probe


class AdapterServingProbeTests(unittest.TestCase):
    def test_startup_failure_is_retained_and_server_is_stopped(self):
        files = {name: b"diagnostic" for name in PACKAGE_FILES}
        prepared = {"file_sha256": package_hashes(files), "checkpoint_manifest": {"model": "test"}}
        server = types.SimpleNamespace(
            start=Mock(side_effect=RuntimeError("startup failed")), stop=Mock(), log_path=None
        )
        modules = {
            "adk_submission": types.SimpleNamespace(
                validate_directory=lambda *args, **kwargs: None,
                discover_adapters=lambda *args, **kwargs: types.SimpleNamespace(
                    adapters=dict.fromkeys(ADAPTER_NAMES)
                ),
            ),
            "swegemma.config": types.SimpleNamespace(
                ALLOWED_ADAPTER_EXTENSIONS=frozenset({".safetensors"}),
                build_submission_limits=lambda: (object(), object()),
            ),
        }
        with (
            patch.dict(sys.modules, modules),
            patch(
                "gemma4_lab.adapter_serving_probe.create_approved_server",
                return_value=(server, {"checkpoint_manifest": prepared["checkpoint_manifest"]}),
            ),
        ):
            events = list(run_probe(files, prepared, {}, 1800))
        self.assertEqual(events[0]["stage"], "package-validated")
        self.assertEqual(events[-1]["stage"], "finished")
        self.assertFalse(events[-1]["passed"])
        self.assertFalse(events[-1]["completed"])
        self.assertEqual(events[-1]["error"], "startup failed")
        server.stop.assert_called_once()
