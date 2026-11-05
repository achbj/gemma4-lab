"""Use invented files only; prove header transport never reads tensor bytes."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab import weight_inventory as inventory


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.checkpoint = self.root / "model.safetensors"
        self.tensor = {"dtype": "F32", "shape": [2], "data_offsets": [0, 8]}
        self.write_header({"invented_tensor": self.tensor})

    def write_header(self, header, payload=b"PAYLOAD!"):
        raw = header if isinstance(header, bytes) else json.dumps(header).encode()
        self.checkpoint.write_bytes(len(raw).to_bytes(8, "little") + raw + payload)
        return raw

    def manifest(self):
        config = {"model_type": "invented", "text_config": {"hidden_size": 4}}
        raw = json.dumps(config).encode()
        (self.root / "config.json").write_bytes(raw)
        manifest = {
            "model": "test/model/1",
            "files": {
                "config.json": {"size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
                "model.safetensors": {
                    "size_bytes": self.checkpoint.stat().st_size,
                    "sha256": "not-read-or-verified",
                },
            },
        }
        self.save_manifest(manifest)
        return manifest, config

    def save_manifest(self, manifest):
        (self.root / "source-manifest.json").write_text(json.dumps(manifest))

    def test_inventory_reads_only_prefix_and_header_including_padding(self):
        raw = self.write_header({"invented_tensor": self.tensor})
        raw += b" " * (-len(raw) % 8)
        self.write_header(raw)
        self.manifest()
        limit = 8 + len(raw)
        requests = []
        original_open = Path.open
        checkpoint = self.checkpoint

        class Guard:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def fileno(self):
                return self.stream.fileno()

            def read(self, size=-1):
                if size < 0 or self.stream.tell() + size > limit:
                    raise AssertionError("Attempted to read learned tensor payload")
                requests.append(size)
                return self.stream.read(size)

        def guarded_open(path, *args, **kwargs):
            if path == checkpoint:
                self.assertEqual(kwargs.get("buffering"), 0, "Read-ahead must be disabled")
            stream = original_open(path, *args, **kwargs)
            return Guard(stream) if path == checkpoint else stream

        with patch.object(Path, "open", guarded_open):
            result = inventory.inventory_checkpoint(self.root, "test/model/1")
        header = result["checkpoint"]
        self.assertEqual(requests, [8, len(raw)])
        self.assertEqual(header["tensors"], {"invented_tensor": self.tensor})
        self.assertEqual(header["dtype_counts"], {"F32": 1})
        self.assertEqual(header["tensor_count"], 1)
        self.assertEqual(header["header_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(header["data_start"], limit)
        self.assertFalse(header["tensor_payload_read"])
        self.assertFalse(result["checkpoint_payload_sha256_verified"])
        self.assertEqual(result["config"]["model_type"], "invented")

    def test_scalar_and_empty_tensors_are_structural_metadata(self):
        self.write_header(
            {
                "scalar": {"dtype": "U8", "shape": [], "data_offsets": [0, 1]},
                "empty": {"dtype": "F32", "shape": [0, 2], "data_offsets": [1, 1]},
                "__metadata__": {"format": "pt"},
            },
            b"X",
        )
        result = inventory.read_safetensors_header(self.checkpoint)
        self.assertEqual(result["tensor_count"], 2)
        self.assertEqual(result["tensors"]["scalar"]["shape"], [])

    def test_malformed_truncated_oversized_or_duplicate_headers_are_rejected(self):
        malformed = [
            b"short",
            (999).to_bytes(8, "little") + b"{}",
            (inventory.MAX_HEADER_BYTES + 1).to_bytes(8, "little"),
            (0).to_bytes(8, "little"),
            (3).to_bytes(8, "little") + b"{xx",
            (2).to_bytes(8, "little") + b"[]",
        ]
        for raw in malformed:
            with self.subTest(raw=raw):
                self.checkpoint.write_bytes(raw)
                with self.assertRaises(ValueError):
                    inventory.read_safetensors_header(self.checkpoint)
        self.write_header(b'{"x": {}, "x": {}}')
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            inventory.read_safetensors_header(self.checkpoint)

    def test_invalid_shapes_offsets_and_metadata_fields_are_rejected(self):
        bad = [{"shape": value} for value in [-1, [-1], [True], [1.5], [2**64], ["2"]]]
        bad += [{"data_offsets": value} for value in [[-1, 8], [0, 9], [8, 0], [0], [False, 8]]]
        bad += [{"dtype": value} for value in [None, "", 32]]
        bad += [{"unexpected": 1}]
        for change in bad:
            with self.subTest(change=change):
                self.write_header({"invented_tensor": {**self.tensor, **change}})
                with self.assertRaises(ValueError):
                    inventory.read_safetensors_header(self.checkpoint)

    def test_overlaps_gaps_and_unindexed_trailing_bytes_are_rejected(self):
        cases = [
            ({"a": self.tensor, "b": {**self.tensor, "data_offsets": [4, 12]}}, 12),
            ({"a": {**self.tensor, "data_offsets": [1, 8]}}, 8),
            ({"a": self.tensor}, 9),
        ]
        for header, size in cases:
            with self.subTest(header=header, size=size):
                self.write_header(header, b"X" * size)
                with self.assertRaises(ValueError):
                    inventory.read_safetensors_header(self.checkpoint)

    def test_manifest_model_config_hash_and_checkpoint_size_are_checked(self):
        for corruption in ["model", "config_hash", "config_size", "checkpoint_size"]:
            with self.subTest(corruption=corruption):
                manifest, _ = self.manifest()
                if corruption == "model":
                    manifest["model"] = "other"
                elif corruption == "config_hash":
                    manifest["files"]["config.json"]["sha256"] = "bad"
                else:
                    name = "config.json" if corruption == "config_size" else "model.safetensors"
                    manifest["files"][name]["size_bytes"] += 1
                self.save_manifest(manifest)
                with self.assertRaises(ValueError):
                    inventory.inventory_checkpoint(self.root, "test/model/1")

    def test_single_file_checkpoint_must_match_manifest(self):
        self.manifest()
        extra = self.root / "extra.safetensors"
        extra.write_bytes(b"invented")
        with self.assertRaisesRegex(ValueError, "single"):
            inventory.inventory_checkpoint(self.root, "test/model/1")
        extra.unlink()
        self.checkpoint.rename(extra)
        with self.assertRaisesRegex(ValueError, "single"):
            inventory.inventory_checkpoint(self.root, "test/model/1")


if __name__ == "__main__":
    unittest.main()
