"""One bounded GPU screen of the frozen intervention, identity and random controls."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.panels import save_report
from gemma4_lab.remote_serving import MODEL_SOURCE
from gemma4_lab.wsp_adapter import ADAPTER_NAMES, MAX_PACKAGE_BYTES, PACKAGE_FILES, package_hashes

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
EXPECTED_IMAGE = "im-bEtC1IFnE2DCntpbAu56LW"
SETTINGS, CONFIG, PROMPTS, CASES, INPUT_HASHES, ESTIMATE = {}, {}, {}, [], {}, {}
CONTEXT = ""
image = None
RESOURCES = {
    "gpu": "A10G",
    "cpu_cores": 2,
    "memory_gib": 16,
    "timeout_seconds": 1800,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.config import estimate_run, load_config
    from gemma4_lab.modal_runtime import build_runtime_image

    SETTINGS = json.loads((ROOT / "configs/wsp-screen-v1.json").read_text())
    CONFIG = load_config(ROOT / SETTINGS["runtime_config"])
    ESTIMATE, RESOURCES = estimate_run(CONFIG), CONFIG["modal"]
    if CONFIG["sources"]["model"] != MODEL_SOURCE:
        raise ValueError("The screen requires the approved E4B base")
    CASES = json.loads((ROOT / SETTINGS["case_config"]).read_text())["cases"]
    PROMPTS = {
        "base": (ROOT / SETTINGS["base_prompt"]).read_text(),
        "prompt": (ROOT / SETTINGS["prompt_control"]).read_text(),
    }
    CONTEXT = (ROOT / SETTINGS["context_prompt"]).read_text()
    names = [
        "configs/wsp-screen-v1.json",
        SETTINGS["runtime_config"],
        SETTINGS["case_config"],
        SETTINGS["base_prompt"],
        SETTINGS["prompt_control"],
        SETTINGS["context_prompt"],
        "src/gemma4_lab/wsp_adapter.py",
        "src/gemma4_lab/wsp_evaluation.py",
        "src/gemma4_lab/behavior_diagnostics.py",
        "src/gemma4_lab/behavior_inference.py",
        "src/gemma4_lab/adapter_probe.py",
        "src/gemma4_lab/adapter_serving_probe.py",
        "src/gemma4_lab/remote_serving.py",
        "src/gemma4_lab/modal_runtime.py",
        "infrastructure/modal/evaluate_wsp.py",
    ]
    INPUT_HASHES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-wsp-intervention-screen")
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
def screen(files, prepared, settings, prompts, context, cases, execution_limit_seconds):
    from gemma4_lab.wsp_evaluation import run_screen

    yield from run_screen(
        files, prepared, settings, prompts, context, cases, execution_limit_seconds
    )


def _prepared_inputs(prepared: str):
    source = (ROOT / prepared).resolve()
    if (
        not source.is_relative_to(ROOT / "artifacts/wsp-read-v1")
        or source.name != "prepare.json"
        or not source.is_file()
    ):
        raise ValueError("Use a preserved prepare.json under artifacts/wsp-read-v1")
    payload = json.loads(source.read_text())
    if (
        any(payload.get(k) is not True for k in ("completed", "passed", "runtime_identity_passed"))
        or payload["modal_image_id"] != EXPECTED_IMAGE
        or payload["base_identity"]["runtime_image"] != EXPECTED_IMAGE
        or payload["base_identity"]["model"] != MODEL_SOURCE
        or payload["compiled_adapters"] != {name: name for name in ADAPTER_NAMES}
    ):
        raise ValueError("Preparation or its pinned runtime/compiled aliases did not pass")
    inspection = (ROOT / payload["inspection_path"]).resolve()
    if (
        not inspection.is_relative_to(ROOT / "artifacts/wsp-numeric-v1")
        or hashlib.sha256(inspection.read_bytes()).hexdigest() != payload["inspection_sha256"]
    ):
        raise ValueError("Numerical inspection differs from CPU preparation")
    for name, digest in payload["source_sha256"].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("CPU preparation source/template identity changed")
    root = source.parent / "submission"
    paths = {p.relative_to(root).as_posix(): p for p in root.rglob("*") if p.is_file()}
    if (
        set(paths) != PACKAGE_FILES
        or any(not p.resolve().is_relative_to(root.resolve()) for p in paths.values())
        or sum(p.stat().st_size for p in paths.values()) >= MAX_PACKAGE_BYTES
    ):
        raise ValueError("Prepared submission has unexpected files, paths or size")
    files = {name: path.read_bytes() for name, path in paths.items()}
    if (
        package_hashes(files) != payload["file_sha256"]
        or hashlib.sha256(files["agent.yaml"]).hexdigest() != payload["template_sha256"]
    ):
        raise ValueError("Prepared adapter package/template hashes changed")
    return source, payload, files


@app.local_entrypoint()
def main(prepared: str):
    if os.environ.get("MODAL_PROFILE") != "onepiecification" or image is None:
        raise ValueError("Use the local entrypoint with MODAL_PROFILE=onepiecification")
    if image.object_id != EXPECTED_IMAGE:
        raise ValueError("GPU screen runtime differs from the pinned image")
    source, payload, files = _prepared_inputs(prepared)
    destination = (
        ROOT / "artifacts/wsp-screen-v1" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") / "run.json"
    )
    if destination.exists():
        raise ValueError("Preserve prior screen reports")
    report = {
        "stage": "wsp-intervention-screen",
        "completed": False,
        "valid_for_comparison": False,
        "gate_passed": False,
        "settings": SETTINGS,
        "cases": CASES,
        "run_config": CONFIG,
        "estimate": ESTIMATE,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prepared_path": source.relative_to(ROOT).as_posix(),
        "prepared_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "prepared": payload,
        "file_sha256": package_hashes(files),
        "input_sha256": INPUT_HASHES,
        "events": [],
    }
    save_report(destination, report)
    terminal = None
    try:
        for event in screen.remote_gen(
            files, payload, SETTINGS, PROMPTS, CONTEXT, CASES, RESOURCES["timeout_seconds"]
        ):
            report["events"].append(event)
            if event["stage"] == "finished":
                terminal = event
                report["completed"] = event.get("completed") is True
                clean = not any(
                    event[k]
                    for k in event
                    if k.startswith("error") or k in ("shutdown_error", "traceback")
                )
                report["valid_for_comparison"] = (
                    report["completed"]
                    and clean
                    and event.get("assessment", {}).get("valid_coverage") is True
                )
                report["gate_passed"] = (
                    report["valid_for_comparison"] and event.get("gate_passed") is True
                )
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
        report["valid_for_comparison"] = False
        report["gate_passed"] = False
        raise
    finally:
        save_report(destination, report)
        print(
            json.dumps(
                {
                    "report": str(destination),
                    "completed": report["completed"],
                    "valid_for_comparison": report["valid_for_comparison"],
                    "gate_passed": report["gate_passed"],
                }
            ),
            flush=True,
        )
    if terminal is None or not report["valid_for_comparison"]:
        raise SystemExit(1)
