"""CPU-only checkpoint metadata export; never read learned tensor payloads."""

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
    "memory_gib": 4,
    "timeout_seconds": 120,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.modal_runtime import build_runtime_image

    SETTINGS = tomllib.loads((ROOT / "configs/wsp-inspection-v1.toml").read_text())
    RESOURCES = SETTINGS["modal"]
    if (
        RESOURCES["profile"] != "ach-bj100"
        or RESOURCES["max_containers"] != 1
        or SETTINGS["model"] != MODEL_SOURCE
        or SETTINGS["stage"] != "metadata-only"
    ):
        raise ValueError("Unexpected profile, model or metadata-only resource settings")
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-checkpoint-metadata")
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
def inventory() -> dict:
    import time

    from gemma4_lab.weight_inventory import inventory_checkpoint

    started = time.monotonic()
    result = inventory_checkpoint(MODEL_PATH, MODEL_SOURCE)
    return {
        "passed": True,
        "inventory": result,
        "elapsed_seconds": time.monotonic() - started,
        "tensor_payload_read": False,
        "gpu_allocated": False,
    }


@app.local_entrypoint()
def main():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=ach-bj100")
    destination = (
        ROOT
        / "artifacts/wsp-inspection-v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
        / "metadata.json"
    )
    if destination.exists():
        raise ValueError("Preserve existing inventory reports")
    report = {
        "completed": False,
        "stage": "metadata-only",
        "settings": SETTINGS,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "configs/wsp-inspection-v1.toml",
                "src/gemma4_lab/weight_inventory.py",
                "infrastructure/modal/inventory_checkpoint.py",
                "src/gemma4_lab/modal_runtime.py",
            )
        },
    }
    save_report(destination, report)
    try:
        report.update(inventory.remote(), completed=True)
        report["runtime_identity_passed"] = image.object_id == SETTINGS["expected_runtime_image"]
    except Exception as exc:
        report["invocation_error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        save_report(destination, report)
        print(json.dumps({"completed": report["completed"], "report": str(destination)}))
    if not report.get("passed") or not report["runtime_identity_passed"]:
        raise SystemExit(1)
