"""Protect reserved issues and the identity of host-side grader controls."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gemma4_lab.panels import (
    json_identity,
    load_development_panel,
    qualified_tasks,
    run_agent_panel,
)


class PanelTests(unittest.TestCase):
    def test_interrupted_batch_preserves_results_and_never_sends_reference_solutions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "submissions/baseline"
            (candidate / "configs").mkdir(parents=True)
            for name in ("eval_config.yaml", "configs/sampling.yaml"):
                (candidate / name).write_text("unchanged settings")
            hashes = {
                p.relative_to(candidate).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in candidate.rglob("*")
                if p.is_file()
            }
            panel = {"name": "screen", "task_ids": ["a", "b"], "minimum_qualified_tasks": 2}
            identities = {name: {"fixture": name} for name in panel["task_ids"]}
            controls = {
                "completed": True,
                "panel_sha256": json_identity(panel),
                "modal_image_id": "image",
                "cases": {
                    name: {
                        "identity": identities[name],
                        "passed": True,
                        "evaluation": {"submission_sha256": hashes},
                    }
                    for name in panel["task_ids"]
                },
            }
            reports = root / "artifacts/panels/screen"
            reports.mkdir(parents=True)
            (reports / "1-controls.json").write_text(json.dumps(controls))
            compilation = root / "artifacts/runtime-validation"
            compilation.mkdir()
            (compilation / "1-compiler.json").write_text(
                json.dumps({"passed": True, "submission_sha256": hashes})
            )
            tasks = [
                {"instance_id": name, "patch": "reference answer"} for name in panel["task_ids"]
            ]
            sent = []

            class InterruptedRemote:
                def remote_gen(self, payloads, execution_limit_seconds):
                    sent.extend(payloads)
                    yield {"stage": "case-result", "task_id": "a", "resolved": False}
                    raise RuntimeError("connection lost")

            with (
                patch("gemma4_lab.panels.load_task_payloads", return_value=tasks),
                patch(
                    "gemma4_lab.panels.task_identity",
                    side_effect=lambda root, t: identities[t["instance_id"]],
                ),
                self.assertRaisesRegex(RuntimeError, "connection lost"),
            ):
                run_agent_panel(
                    root,
                    panel,
                    InterruptedRemote(),
                    "image",
                    "commit",
                    {"modal": {"timeout_seconds": 1800}},
                    "baseline",
                )
            self.assertTrue(all(task["patch"] == "" for task in sent))
            result = json.loads(next(p for p in reports.glob("*-baseline.json")).read_text())
            self.assertFalse(result["completed"])
            self.assertEqual(result["events"][0]["task_id"], "a")
            self.assertEqual(result["invocation_error"]["message"], "connection lost")

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
            "completed": True,
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
