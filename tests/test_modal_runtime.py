"""Reject altered wheel inputs before constructing any cloud image."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab.modal_runtime import build_runtime_image


class RuntimeImageTests(unittest.TestCase):
    def test_unexpected_or_modified_wheel_is_rejected_before_image_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel_root = root / "data/raw/official/wheelhouse"
            wheel_root.mkdir(parents=True)
            requirements = root / "requirements"
            requirements.mkdir()
            content = b"pinned wheel contents"
            wheel = wheel_root / "official.whl"
            wheel.write_bytes(content)
            (requirements / "remote-runtime-wheels.json").write_text(
                json.dumps(
                    {
                        "wheels": [
                            {"name": wheel.name, "sha256": hashlib.sha256(content).hexdigest()}
                        ]
                    }
                )
            )
            with patch("gemma4_lab.modal_runtime.modal.Image.debian_slim") as image:
                wheel.write_bytes(b"modified")
                with self.assertRaisesRegex(ValueError, "checksum"):
                    build_runtime_image(root)
                wheel.write_bytes(content)
                (wheel_root / "unlisted.whl").write_bytes(b"unlisted")
                with self.assertRaisesRegex(ValueError, "unexpected"):
                    build_runtime_image(root)
                (wheel_root / "unlisted.whl").unlink()
                wheel.unlink()
                with self.assertRaisesRegex(ValueError, "missing"):
                    build_runtime_image(root)
                image.assert_not_called()
