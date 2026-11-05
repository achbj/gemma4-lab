"""CPU-only packaging of the fixed numerical intervention and its controls."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.panels import save_report

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
EXPECTED_IMAGE = "im-bEtC1IFnE2DCntpbAu56LW"
TEMPLATE = "submissions/wsp-read-v1/agent.yaml"
image = None
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.modal_runtime import build_runtime_image

    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-wsp-cpu-preparation")


@app.function(
    image=image,
    cpu=2,
    memory=4096,
    timeout=300,
    startup_timeout=900,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
)
def prepare(inspection: dict, template: str):
    import time
    import traceback

    from gemma4_lab.wsp_adapter import prepare_intervention

    start = time.monotonic()
    try:
        result = prepare_intervention(inspection, template)
    except Exception as exc:
        result = {
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    return {**result, "elapsed_seconds": time.monotonic() - start, "gpu_allocated": False}


@app.local_entrypoint()
def main(inspection: str):
    if os.environ.get("MODAL_PROFILE") != "ach-bj100" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.wsp_adapter import write_package

    source = (ROOT / inspection).resolve()
    if not source.is_relative_to(ROOT / "artifacts/wsp-numeric-v1") or not source.is_file():
        raise ValueError("Use a preserved numerical inspection under artifacts/wsp-numeric-v1")
    payload = json.loads(source.read_text())
    destination = ROOT / "artifacts/wsp-read-v1" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if destination.exists():
        raise ValueError("Preserve prior preparation reports")
    report = {
        "completed": False,
        "passed": False,
        "stage": "wsp-intervention-preparation",
        "modal_image_id": image.object_id,
        "runtime_identity_passed": image.object_id == EXPECTED_IMAGE,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "inspection_path": source.relative_to(ROOT).as_posix(),
        "inspection_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                TEMPLATE,
                "src/gemma4_lab/wsp_adapter.py",
                "src/gemma4_lab/modal_runtime.py",
                "infrastructure/modal/prepare_wsp.py",
            )
        },
    }
    save_report(destination / "prepare.json", report)
    try:
        if not report["runtime_identity_passed"]:
            raise ValueError("Preparation runtime differs from the frozen image")
        result = prepare.remote(payload, (ROOT / TEMPLATE).read_text())
        files = result.pop("files", None)
        report.update(result)
        if result.get("passed"):
            write_package(destination / "submission", files, result["file_sha256"])
        report["completed"] = True
    finally:
        save_report(destination / "prepare.json", report)
        print(json.dumps({"report": str(destination / "prepare.json"), "passed": report["passed"]}))
    if not report["passed"] or not report["runtime_identity_passed"]:
        raise SystemExit(1)
