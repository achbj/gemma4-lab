"""Check that switching models cannot carry incompatible dummy adapters along."""

import tempfile
import unittest
from pathlib import Path

from gemma4_lab.submission import E4B_MODEL, prepare_baseline


class SubmissionTests(unittest.TestCase):
    def test_baseline_preserves_source_and_sampling_and_removes_dummy_adapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            original = "name: coder\nmodel: old-model\nadapter: main_lora\n"
            (source / "agent.yaml").write_text(original, encoding="utf-8")
            (source / "sampling.yaml").write_text("temperature: 0.2\n", encoding="utf-8")
            (source / "adapters").mkdir()
            (source / "adapters/dummy.safetensors").write_bytes(b"dummy")
            destination = Path(tmp) / "baseline"
            self.assertEqual(prepare_baseline(source, destination), 1)
            self.assertEqual((source / "agent.yaml").read_text(), original)
            self.assertIn(E4B_MODEL, (destination / "agent.yaml").read_text())
            self.assertNotIn("adapter:", (destination / "agent.yaml").read_text())
            self.assertFalse((destination / "adapters").exists())
            self.assertEqual(
                (destination / "sampling.yaml").read_bytes(),
                (source / "sampling.yaml").read_bytes(),
            )
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare_baseline(source, destination)

    def test_symlink_source_is_rejected_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            external = Path(tmp) / "elsewhere"
            external.write_text("model: old-model\n", encoding="utf-8")
            (source / "agent.yaml").symlink_to(external)
            with self.assertRaises(ValueError):
                prepare_baseline(source, Path(tmp) / "output")
