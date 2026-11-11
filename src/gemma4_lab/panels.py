"""Frozen development panels and host-side qualification; no ML imports."""

import hashlib
import json
from datetime import UTC, datetime
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
    manifest = json.loads((root / f"configs/fixtures/{task_id}.json").read_text())
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
    if not controls.get("completed"):
        raise ValueError("Grader control panel is incomplete")
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


def controls_qualify(result: dict) -> bool:
    controls = result.get("evaluation", {}).get("results", {})
    unchanged = controls.get("unchanged", {})
    reference = controls.get("reference", {})
    return (
        unchanged.get("resolved") is False
        and unchanged.get("test_exit_code") in (1, 124)
        and reference.get("resolved") is True
        and reference.get("test_exit_code") == 0
    )


def reclassify_controls(root: Path, panel: dict, source_path: Path) -> Path:
    """Apply the documented pre-agent timeout amendment without rerunning tests."""
    report = json.loads(source_path.read_text())
    if not report["completed"] or report["panel"]["task_ids"] != panel["task_ids"]:
        raise ValueError("Reclassification requires the same completed fixed panel")
    if report["panel"]["split_sha256"] != panel["split_sha256"]:
        raise ValueError("Reclassification cannot change the frozen split")
    for task in load_task_payloads(root, panel["task_ids"]):
        case = report["cases"][task["instance_id"]]
        if case["identity"] != task_identity(root, task):
            raise ValueError("Control source or runtime changed; rerun qualification")
        case["prior_qualification_passed"] = case["passed"]
        case["passed"] = controls_qualify(case)
    report["qualification_amendment"] = {
        "version": 2,
        "source_report": source_path.relative_to(root).as_posix(),
        "source_report_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "reason": (
            "Accept an unchanged test timeout when the reference fix resolves; "
            "no agent outcomes used"
        ),
        "source_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    report["panel"] = panel
    report["panel_sha256"] = json_identity(panel)
    report["qualified_task_ids"] = [i for i in panel["task_ids"] if report["cases"][i]["passed"]]
    report["passed"] = len(report["qualified_task_ids"]) >= panel["minimum_qualified_tasks"]
    destination = source_path.parent / (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-controls.json"
    )
    if destination == source_path:
        raise ValueError("Preserve the original control report")
    save_report(destination, report)
    return destination


def run_control_panel(root: Path, panel: dict, function, image_id: str, git_commit: str) -> Path:
    """Run the four preregistered CPU controls and retain each result immediately."""
    destination = (
        root
        / "artifacts/panels"
        / panel["name"]
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-controls.json")
    )
    report = {
        "stage": "panel-grader-controls",
        "panel": panel,
        "panel_sha256": json_identity(panel),
        "modal_image_id": image_id,
        "git_commit": git_commit,
        "cases": {},
        "completed": False,
    }
    save_report(destination, report)
    for task in load_task_payloads(root, panel["task_ids"]):
        task_id = task["instance_id"]
        identity = task_identity(root, task)
        result = function.remote(task)
        result["runner_qualification_passed"] = result["passed"]
        result["passed"] = controls_qualify(result)
        result["identity"] = identity
        report["cases"][task_id] = result
        save_report(destination, report)
        print(
            json.dumps({"stage": "grader-control", "task_id": task_id, "passed": result["passed"]})
        )
    report["completed"] = True
    report["qualified_task_ids"] = [i for i in panel["task_ids"] if report["cases"][i]["passed"]]
    report["passed"] = len(report["qualified_task_ids"]) >= panel["minimum_qualified_tasks"]
    save_report(destination, report)
    return destination


def run_agent_panel(
    root: Path,
    panel: dict,
    function,
    image_id: str,
    git_commit: str,
    run_config: dict,
    candidate: str,
) -> Path:
    from gemma4_lab.config import candidate_directory

    controls_paths = sorted((root / "artifacts/panels" / panel["name"]).glob("*-controls.json"))
    if not controls_paths:
        raise ValueError("Run all panel grader controls before allocating a GPU")
    controls = json.loads(controls_paths[-1].read_text())
    tasks = load_task_payloads(root, panel["task_ids"])
    identities = {task["instance_id"]: task_identity(root, task) for task in tasks}
    qualified = qualified_tasks(panel, controls, identities, image_id)
    candidate_root = candidate_directory(root, candidate)
    candidate_hashes = {
        path.relative_to(candidate_root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(candidate_root.rglob("*"))
        if path.is_file()
    }
    control_hashes = controls["cases"][qualified[0]]["evaluation"]["submission_sha256"]
    for name in ("eval_config.yaml", "configs/sampling.yaml"):
        if candidate_hashes[name] != control_hashes[name]:
            raise ValueError("Panel evaluation and sampling settings must match the controls")
    compilations = [
        json.loads(path.read_text())
        for path in (root / "artifacts/runtime-validation").glob("*-compiler.json")
    ]
    if not any(
        item.get("passed")
        and item.get("candidate", "baseline") == candidate
        and item.get("submission_sha256") == candidate_hashes
        for item in compilations
    ):
        raise ValueError("Matching candidate compilation is required before a GPU panel")
    payloads = []
    for task in tasks:
        if task["instance_id"] in qualified:
            # Reference solutions never enter the GPU invocation, even as host
            # task memory. Evaluation-only tests stay out of agent workspace files.
            payloads.append({**task, "patch": ""})
    destination = (
        root
        / "artifacts/panels"
        / panel["name"]
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{candidate}.json")
    )
    report = {
        "stage": "panel-agents",
        "candidate": candidate,
        "panel_sha256": json_identity(panel),
        "qualified_task_ids": qualified,
        "excluded_task_ids": [i for i in panel["task_ids"] if i not in qualified],
        "identities": identities,
        "submission_sha256": candidate_hashes,
        "modal_image_id": image_id,
        "git_commit": git_commit,
        "run_config": run_config,
        "events": [],
        "completed": False,
    }
    save_report(destination, report)
    try:
        for event in function.remote_gen(
            payloads, execution_limit_seconds=run_config["modal"]["timeout_seconds"]
        ):
            report["events"].append(event)
            if event["stage"] == "finished":
                report["completed"] = event["completed"]
            save_report(destination, report)
            print(
                json.dumps(
                    {key: event[key] for key in ("stage", "task_id", "resolved") if key in event}
                ),
                flush=True,
            )
    except Exception as exc:
        report["invocation_error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        save_report(destination, report)
    return destination
