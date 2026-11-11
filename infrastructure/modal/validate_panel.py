"""CPU-only fixture controls: this entrypoint declares no GPU functions."""

import json
import os
import subprocess
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
image = None
CANDIDATE = "baseline-3m"
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.config import candidate_directory
    from gemma4_lab.modal_runtime import build_runtime_image
    from gemma4_lab.remote_evaluation import fixture_identity

    CANDIDATE = os.environ.get("GEMMA4_CANDIDATE", CANDIDATE)
    fixtures = ROOT / "data/raw/official/evaluation"
    for directory in fixtures.iterdir():
        manifest = ROOT / f"configs/fixtures/{directory.name}.json"
        if not directory.is_dir() or not manifest.is_file():
            raise ValueError("Every mounted fixture requires a provenance manifest")
        fixture_identity(directory, json.loads(manifest.read_text()))
    image = (
        build_runtime_image(ROOT)
        .add_local_python_source("gemma4_lab")
        .add_local_dir(fixtures, "/fixtures")
        .add_local_dir(candidate_directory(ROOT, CANDIDATE), "/submission")
    )

app = modal.App("gemma4-panel-cpu-controls")


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=900,
    startup_timeout=900,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
)
def validate_fixture(task_payload: dict) -> dict:
    import time
    import traceback
    from importlib.metadata import distributions

    from adk_submission import ModelRegistry

    from gemma4_lab.panels import controls_qualify
    from gemma4_lab.remote_evaluation import evaluate_reference_task

    started = time.monotonic()
    result = {"stage": "grader-controls", "passed": False, "gpu_allocated": False}
    try:
        result["evaluation"] = evaluate_reference_task(
            task_payload, ModelRegistry(), controls_only=True
        )
        result["passed"] = controls_qualify(result)
    except Exception as exc:
        result.update(error=str(exc), traceback=traceback.format_exc())
    result["elapsed_seconds"] = time.monotonic() - started
    result["packages"] = {d.metadata["Name"]: d.version for d in distributions()}
    return result


@app.local_entrypoint()
def main(panel: str):
    if os.environ.get("MODAL_PROFILE") != "onepiecification" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=onepiecification")
    from gemma4_lab.panels import load_development_panel, run_control_panel

    settings = load_development_panel(ROOT, ROOT / panel)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    destination = run_control_panel(ROOT, settings, validate_fixture, image.object_id, commit)
    print(
        json.dumps({"report": str(destination), "candidate": CANDIDATE, "gpu_allocated": False}),
        flush=True,
    )
