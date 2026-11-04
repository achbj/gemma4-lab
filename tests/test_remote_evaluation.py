"""Check fixture mounts without importing the remote tensor runtime."""

import tempfile
import unittest
from pathlib import Path

from gemma4_lab.assets import sha256
from gemma4_lab.remote_evaluation import fixture_identity


class FixtureIdentityTests(unittest.TestCase):
    def test_rejects_answer_files_and_same_size_fixture_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "snapshot.tgz"
            fixture.write_bytes(b"abc")
            manifest = {
                "files": [{"name": fixture.name, "size_bytes": 3, "sha256": sha256(fixture)}]
            }
            self.assertEqual(len(fixture_identity(root, manifest)), 64)
            answers = root / "tasks.jsonl"
            answers.write_text("evaluation-only data")
            with self.assertRaisesRegex(ValueError, "unexpected"):
                fixture_identity(root, manifest)
            answers.unlink()
            fixture.write_bytes(b"xyz")
            with self.assertRaisesRegex(ValueError, "checksum"):
                fixture_identity(root, manifest)
