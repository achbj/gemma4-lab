"""Run the frozen paired behavioral diagnostic in one bounded base-model container."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.panels import save_report
from gemma4_lab.remote_serving import MODEL_SOURCE

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
SETTINGS = {}
CONFIG = {}
PROMPTS = {}
CONTEXT = ""
ESTIMATE = {}
image = None
RESOURCES = {
    "gpu": "A10G",
    "cpu_cores": 2,
    "memory_gib": 16,
    "timeout_seconds": 1800,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
INPUT_HASHES = {}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.config import estimate_run, load_config
    from gemma4_lab.modal_runtime import build_runtime_image

    config_path = ROOT / "configs/behavior-diagnostic-v1.json"
    SETTINGS = json.loads(config_path.read_text())
    CONFIG = load_config(ROOT / SETTINGS["runtime_config"])
    ESTIMATE = estimate_run(CONFIG)
    RESOURCES = CONFIG["modal"]
    if CONFIG["sources"]["model"] != MODEL_SOURCE:
        raise ValueError("The diagnostic must use the approved E4B checkpoint")
    PROMPTS = {c["name"]: (ROOT / c["system_prompt"]).read_text() for c in SETTINGS["conditions"]}
    CONTEXT = (ROOT / SETTINGS["context_prompt"]).read_text()
    names = [
        "configs/behavior-diagnostic-v1.json",
        SETTINGS["runtime_config"],
        SETTINGS["context_prompt"],
        *[c["system_prompt"] for c in SETTINGS["conditions"]],
        "src/gemma4_lab/behavior_diagnostics.py",
        "src/gemma4_lab/behavior_inference.py",
        "src/gemma4_lab/remote_serving.py",
        "src/gemma4_lab/modal_runtime.py",
        "infrastructure/modal/behavior_diagnostic.py",
    ]
    INPUT_HASHES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-behavior-diagnostic-v1")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    gpu=RESOURCES["gpu"],
    cpu=RESOURCES["cpu_cores"],
    memory=RESOURCES["memory_gib"] * 1024,
    timeout=RESOURCES["timeout_seconds"],
    startup_timeout=RESOURCES["startup_timeout_seconds"],
    max_containers=1,
    min_containers=0,
    scaledown_window=RESOURCES["scaledown_seconds"],
    block_network=True,
    volumes={"/cache": volume},
    is_generator=True,
)
def diagnose(settings: dict, prompts: dict, context: str, execution_limit_seconds: int):
    from gemma4_lab.behavior_inference import run_diagnostic

    yield from run_diagnostic(settings, prompts, context, execution_limit_seconds)


@app.local_entrypoint()
def main():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=ach-bj100")
    destination = (
        ROOT
        / "artifacts/behavior-diagnostic-v1"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"))
        / "run.json"
    )
    if destination.exists():
        raise ValueError("Preserve the existing diagnostic report")
    report = {
        "completed": False,
        "stage": "behavior-diagnostic",
        "settings": SETTINGS,
        "run_config": CONFIG,
        "estimate": ESTIMATE,
        "input_sha256": INPUT_HASHES,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "events": [],
    }
    save_report(destination, report)
    try:
        for event in diagnose.remote_gen(SETTINGS, PROMPTS, CONTEXT, RESOURCES["timeout_seconds"]):
            report["events"].append(event)
            if event["stage"] == "finished":
                report["completed"] = event["completed"]
                report["valid_for_comparison"] = event["valid_for_comparison"]
            save_report(destination, report)
            row = event.get("result", {})
            print(
                json.dumps(
                    {
                        "stage": event["stage"],
                        **{k: row[k] for k in ("case_id", "condition", "stop_reason") if k in row},
                    }
                ),
                flush=True,
            )
    except Exception as exc:
        report["invocation_error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        save_report(destination, report)
        print(
            json.dumps({"completed": report["completed"], "report": str(destination)}), flush=True
        )
    if not report["completed"]:
        raise SystemExit(1)
