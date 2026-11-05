"""Prevent accidental publication or mutation of the diagnostic notebook bundle."""

import base64
import copy
import hashlib
import json
import unittest
import zlib

from gemma4_lab.config import PROJECT_ROOT
from gemma4_lab.kaggle_probe import encode_bundle, validate_metadata


class KaggleProbeTests(unittest.TestCase):
    def test_private_offline_competition_and_model_requirements_are_enforced(self):
        metadata = json.loads(
            (PROJECT_ROOT / "infrastructure/kaggle/adapter_probe/kernel-metadata.json").read_text()
        )
        validate_metadata(metadata)
        for key, value in (
            ("is_private", False),
            ("enable_internet", True),
            ("competition_sources", []),
            ("model_sources", ["unapproved/model/other/version/1"]),
            ("machine_shape", "NvidiaTeslaT4"),
            ("docker_image", "unversioned"),
        ):
            with self.subTest(field=key):
                changed = copy.deepcopy(metadata)
                changed[key] = value
                with self.assertRaisesRegex(ValueError, key):
                    validate_metadata(changed)

    def test_encoded_payload_preserves_exact_binary_contents_and_hash(self):
        payload = {"files": {"adapter": base64.b64encode(bytes(range(256))).decode()}}
        encoded, digest = encode_bundle(payload)
        raw = zlib.decompress(base64.b64decode(encoded))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        self.assertEqual(json.loads(raw), payload)
        with self.assertRaisesRegex(ValueError, "2 MiB"):
            encode_bundle({"excess": "x" * (2 * 1024 * 1024)})
