"""Protect reserved issues and the identity of host-side grader controls."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from gemma4_lab.panels import json_identity, load_development_panel, qualified_tasks


class PanelTests(unittest.TestCase):
    def test_panel_rejects_reserved_issues_and_changed_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            tasks = root / "data/raw/official/competition/tasks.jsonl"
            tasks.parent.mkdir(parents=True)
            tasks.write_text("{}\n")
            split = {
                "source_sha256": hashlib.sha256(tasks.read_bytes()).hexdigest(),
                "partitions": {
                    "development": [{"instance_id": "dev", "repo": "a", "base_commit": "1"}],
                    "reserved_validation": [{"instance_id": "reserved"}],
                },
            }
            split_path = root / "configs/split.json"
            split_path.write_text(json.dumps(split))
            panel = {
                "name": "screen",
                "split_path": "configs/split.json",
                "split_sha256": hashlib.sha256(split_path.read_bytes()).hexdigest(),
                "minimum_qualified_tasks": 1,
                "task_ids": ["reserved"],
            }
            path = root / "configs/panel.json"
            path.write_text(json.dumps(panel))
            with self.assertRaisesRegex(ValueError, "only frozen development"):
                load_development_panel(root, path)
            panel["task_ids"] = ["dev"]
            path.write_text(json.dumps(panel))
            self.assertEqual(load_development_panel(root, path)["task_ids"], ["dev"])
            tasks.write_text('{"changed": true}\n')
            with self.assertRaisesRegex(ValueError, "Official tasks differ"):
                load_development_panel(root, path)

    def test_qualification_preserves_exclusions_and_rejects_stale_controls(self):
        panel = {"task_ids": ["a", "b", "c"], "minimum_qualified_tasks": 2}
        identities = {task: {"fixture": task} for task in panel["task_ids"]}
        controls = {
            "panel_sha256": json_identity(panel),
            "modal_image_id": "image",
            "cases": {
                task: {"identity": identities[task], "passed": task != "b"}
                for task in panel["task_ids"]
            },
        }
        self.assertEqual(qualified_tasks(panel, controls, identities, "image"), ["a", "c"])
        identities["a"] = {"fixture": "changed"}
        with self.assertRaisesRegex(ValueError, "changed grader control"):
            qualified_tasks(panel, controls, identities, "image")
        identities["a"] = controls["cases"]["a"]["identity"]
        controls["cases"].pop("b")
        with self.assertRaisesRegex(ValueError, "Missing"):
            qualified_tasks(panel, controls, identities, "image")
