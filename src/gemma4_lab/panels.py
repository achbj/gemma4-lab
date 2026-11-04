"""Frozen development panels and host-side qualification; no ML imports."""

import hashlib
import json
from pathlib import Path

from gemma4_lab.remote_evaluation import fixture_identity


def json_identity(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load_development_panel(root: Path, path: Path) -> dict:
    path = path.resolve()
    if not path.is_relative_to((root / "configs").resolve()):
        raise ValueError("Panel settings must be inside configs/")
    panel = json.loads(path.read_text())
    split_path = root / panel["split_path"]
    if hashlib.sha256(split_path.read_bytes()).hexdigest() != panel["split_sha256"]:
        raise ValueError("Frozen task split differs from the panel's source")
    split = json.loads(split_path.read_text())
    tasks_path = root / "data/raw/official/competition/tasks.jsonl"
    if hashlib.sha256(tasks_path.read_bytes()).hexdigest() != split["source_sha256"]:
        raise ValueError("Official tasks differ from the frozen split")
    development = {task["instance_id"]: task for task in split["partitions"]["development"]}
    ids = panel["task_ids"]
    if not 1 <= len(ids) <= 4 or len(ids) != len(set(ids)):
        raise ValueError("A screening panel requires at most four distinct tasks")
    if any(task_id not in development for task_id in ids):
        raise ValueError("Panel may contain only frozen development tasks")
    groups = {(development[i]["repo"], development[i]["base_commit"]) for i in ids}
    if len(groups) != len(ids):
        raise ValueError("Panel tasks must use distinct repository/base-commit groups")
    if not 1 <= panel["minimum_qualified_tasks"] <= len(ids):
        raise ValueError("Invalid minimum qualified task count")
    if Path(panel["name"]).name != panel["name"] or panel["name"] in {"", ".", ".."}:
        raise ValueError("Unsafe panel name")
    return panel


def load_task_payloads(root: Path, task_ids: list[str]) -> list[dict]:
    selected = {}
    for line in (root / "data/raw/official/competition/tasks.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row["instance_id"] in task_ids:
                if row["instance_id"] in selected:
                    raise ValueError("Duplicate official task ID")
                selected[row["instance_id"]] = row
    if set(selected) != set(task_ids):
        raise ValueError("Unknown task ID")
    return [selected[task_id] for task_id in task_ids]


def task_identity(root: Path, task: dict) -> dict:
    task_id = task["instance_id"]
    manifest = json.loads((root / f"docs/research/fixtures/{task_id}.json").read_text())
    if manifest["task_id"] != task_id:
        raise ValueError("Fixture manifest belongs to another task")
    return {
        "source_task_sha256": json_identity(task),
        "fixture_sha256": fixture_identity(
            root / "data/raw/official/evaluation" / task_id, manifest
        ),
        "runtime_helper_sha256": hashlib.sha256(
            (root / "src/gemma4_lab/remote_evaluation.py").read_bytes()
        ).hexdigest(),
    }


def qualified_tasks(panel: dict, controls: dict, identities: dict, image_id: str) -> list[str]:
    if controls.get("panel_sha256") != json_identity(panel):
        raise ValueError("Grader controls belong to a different panel")
    if controls.get("modal_image_id") != image_id:
        raise ValueError("Grader controls used a different runtime image")
    qualified = []
    for task_id in panel["task_ids"]:
        result = controls.get("cases", {}).get(task_id)
        if result is None or result.get("identity") != identities[task_id]:
            raise ValueError(f"Missing or changed grader control: {task_id}")
        if result.get("passed"):
            qualified.append(task_id)
    if len(qualified) < panel["minimum_qualified_tasks"]:
        raise ValueError(
            "Insufficient qualified cases; preserve exclusions and repair the environment"
        )
    return qualified


def save_report(path: Path, value: dict) -> None:
    """Persist partial remote outputs before waiting for the next case."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)
