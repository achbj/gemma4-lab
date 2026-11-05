"""Bounded CPU numerical inspection after the owner's Ultra confirmation."""

import hashlib
import json
import os
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.panels import save_report
from gemma4_lab.remote_serving import MODEL_PATH, MODEL_SOURCE

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
SETTINGS = {}
image = None
RESOURCES = {
    "cpu_cores": 2,
    "memory_gib": 6,
    "timeout_seconds": 600,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.modal_runtime import build_runtime_image

    SETTINGS = tomllib.loads((ROOT / "configs/wsp-numeric-v1.toml").read_text())
    RESOURCES = SETTINGS["modal"]
    if SETTINGS["model"] != MODEL_SOURCE or RESOURCES["max_containers"] != 1:
        raise ValueError("Unexpected checkpoint or resource count")
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-numerical-weight-inspection")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    cpu=RESOURCES["cpu_cores"],
    memory=RESOURCES["memory_gib"] * 1024,
    timeout=RESOURCES["timeout_seconds"],
    startup_timeout=RESOURCES["startup_timeout_seconds"],
    max_containers=1,
    min_containers=0,
    scaledown_window=RESOURCES["scaledown_seconds"],
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def inspect(settings: dict):
    import time
    import traceback

    from gemma4_lab.weight_program import inspect_numeric

    start = time.monotonic()
    try:
        result = {"inspection_passed": True, "result": inspect_numeric(MODEL_PATH, settings)}
    except Exception as exc:
        result = {
            "inspection_passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    return {**result, "elapsed_seconds": time.monotonic() - start, "gpu_allocated": False}


@app.local_entrypoint()
def main():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=ach-bj100")
    destination = (
        ROOT
        / "artifacts/wsp-numeric-v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
        / "inspection.json"
    )
    if destination.exists():
        raise ValueError("Preserve prior numerical reports")
    report = {
        "completed": False,
        "stage": "numerical-weight-inspection",
        "settings": SETTINGS,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "configs/wsp-numeric-v1.toml",
                "src/gemma4_lab/weight_io.py",
                "src/gemma4_lab/weight_program.py",
                "src/gemma4_lab/weight_inventory.py",
                "src/gemma4_lab/modal_runtime.py",
                "infrastructure/modal/inspect_numeric.py",
            )
        },
    }
    save_report(destination, report)
    try:
        report.update(inspect.remote(SETTINGS), completed=True)
        report["runtime_identity_passed"] = image.object_id == SETTINGS["expected_runtime_image"]
    finally:
        save_report(destination, report)
        print(
            json.dumps(
                {"report": str(destination), "inspection_passed": report.get("inspection_passed")}
            )
        )
    if not report.get("inspection_passed") or not report["runtime_identity_passed"]:
        raise SystemExit(1)
