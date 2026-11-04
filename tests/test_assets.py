"""Regression checks for bounded downloads, complete inventories, and provenance."""

import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from gemma4_lab.assets import (
    MAX_BOOTSTRAP_BYTES,
    collect_pages,
    safe_destination,
    select_bootstrap,
    select_runtime_wheels,
    select_task_fixture,
    sha256,
    verify_assets,
    write_json,
)


def sample_inventory():
    return {
        "competition": [
            {"name": name, "size_bytes": 100}
            for name in ("HARNESS_README.md", "tasks.jsonl", "sample_submission/agent.yaml")
        ],
        "wheelhouse": [
            {"name": f"{name}-0.1-py3-none-any.whl", "size_bytes": 100}
            for name in ("adk_eval_core", "adk_submission", "swegemma")
        ],
    }


class AssetTests(unittest.TestCase):
    def test_task_fixture_is_scoped_and_size_bounded(self):
        task = {"repo": "psf/requests", "base_commit": "abc", "instance_id": "requests_1"}
        names = [
            "snapshots/requests_1.tgz",
            "graphs/requests_abc.json",
            "embeddings/requests_abc.npz",
            "wheels/pytest.whl",
            "snapshots/unrelated.tgz",
        ]
        inventory = {"competition": [{"name": name, "size_bytes": 10} for name in names]}
        self.assertEqual(len(select_task_fixture(inventory, task)), 4)
        inventory["competition"][0]["size_bytes"] = 200 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, "allocation"):
            select_task_fixture(inventory, task)

    def test_runtime_inventory_rejects_nonwheels_oversize_and_traversal(self):
        for wheel in (
            {"name": "model.safetensors", "size_bytes": 1},
            {"name": "vllm.whl", "size_bytes": 2**31},
            {"name": "../vllm.whl", "size_bytes": 1},
        ):
            with self.subTest(wheel=wheel), self.assertRaises(ValueError):
                select_runtime_wheels({"wheelhouse": [wheel]})
        self.assertEqual(len(select_runtime_wheels(sample_inventory())), 3)

    def test_all_pages_are_collected(self):
        calls = []

        def page(**kwargs):
            calls.append(kwargs["page_token"])
            name, cursor = ("first", "next") if len(calls) == 1 else ("last", None)
            return SimpleNamespace(
                files=[SimpleNamespace(name=name, total_bytes=3)],
                next_page_token=cursor,
            )

        self.assertEqual(len(collect_pages(page, size_field="total_bytes")), 2)
        self.assertEqual(calls, [None, "next"])

    def test_repeated_pagination_cursor_is_rejected(self):
        def page(**kwargs):
            return SimpleNamespace(files=[], next_page_token="same")

        with self.assertRaisesRegex(ValueError, "repeated"):
            collect_pages(page, size_field="total_bytes")

    def test_destination_rejects_traversal_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "assets"
            root.mkdir()
            (root / "linked").symlink_to(Path(tmp), target_is_directory=True)
            for name in ("../token", "/etc/passwd", "a/../../token", "a\\b", "linked/token"):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    safe_destination(root, name)

    def test_bootstrap_excludes_model_weights_and_dummy_adapters(self):
        inventory = sample_inventory()
        inventory["competition"].extend(
            [
                {"name": "model.safetensors", "size_bytes": 12_000_000_000},
                {"name": "sample_submission/adapters/main/adapter_config.json", "size_bytes": 50},
            ]
        )
        self.assertEqual(len(select_bootstrap(inventory)), 6)

    def test_bootstrap_rejects_large_or_incomplete_downloads(self):
        inventory = sample_inventory()
        inventory["competition"][0]["size_bytes"] = MAX_BOOTSTRAP_BYTES
        with self.assertRaisesRegex(ValueError, "allocation"):
            select_bootstrap(inventory)
        incomplete = sample_inventory()
        incomplete["competition"].pop()
        with self.assertRaisesRegex(ValueError, "required"):
            select_bootstrap(incomplete)
        duplicate = copy.deepcopy(sample_inventory())
        duplicate["wheelhouse"].append(duplicate["wheelhouse"][0])
        with self.assertRaisesRegex(ValueError, "exactly one"):
            select_bootstrap(duplicate)

    def test_checksum_detects_same_length_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            asset = root / "task.jsonl"
            asset.write_text("good", encoding="utf-8")
            manifest = root / "manifest.json"
            write_json(
                manifest,
                {
                    "files": [
                        {
                            "path": asset.name,
                            "size_bytes": 4,
                            "sha256": sha256(asset),
                        }
                    ]
                },
            )
            self.assertEqual(verify_assets(root, manifest), 1)
            asset.write_text("oops", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify_assets(root, manifest)
