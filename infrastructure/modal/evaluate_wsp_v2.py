"""One bounded GPU panel for the pre-registered weight-space study v2 (eight arms, 36 cases)."""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.panels import save_report

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
SETTINGS, CASES, PROMPTS, INPUT_HASHES, RESOURCES = {}, [], {}, {}, {}
CONTEXT = ""
image = None
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.config import estimate_run, load_config
    from gemma4_lab.modal_runtime import build_runtime_image

    PANEL = os.environ.get("GEMMA4_PANEL", "configs/wsp-v2-panel.json")
    if PANEL not in (
        "configs/wsp-v2-panel.json",
        "configs/wsp-v3-panel.json",
        "configs/wsp-v3-seeds.json",
    ):
        raise ValueError("Unknown frozen panel file")
    SETTINGS = json.loads((ROOT / PANEL).read_text())
    CONFIG = load_config(ROOT / SETTINGS["runtime_config"])
    ESTIMATE, RESOURCES = estimate_run(CONFIG), CONFIG["modal"]
    CASES = [
        c
        for c in json.loads((ROOT / SETTINGS["cases"]).read_text())["cases"]
        if c["role"] == SETTINGS["case_role"]
    ]
    PROMPTS = {
        "base": (ROOT / SETTINGS["base_prompt"]).read_text(),
        "prompt": (ROOT / SETTINGS["prompt_control"]).read_text(),
    }
    CONTEXT = (ROOT / SETTINGS["context_prompt"]).read_text()
    names = [
        PANEL,
        SETTINGS["runtime_config"],
        SETTINGS["cases"],
        SETTINGS["base_prompt"],
        SETTINGS["prompt_control"],
        SETTINGS["context_prompt"],
        SETTINGS["protocol"],
        "src/gemma4_lab/wsp_v2_panel.py",
        "src/gemma4_lab/wsp_v2_adapter.py",
        "src/gemma4_lab/behavior_inference.py",
        "src/gemma4_lab/behavior_diagnostics.py",
        "src/gemma4_lab/remote_serving.py",
        "infrastructure/modal/evaluate_wsp_v2.py",
    ]
    INPUT_HASHES = {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-wsp-v2-panel")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    gpu=RESOURCES.get("gpu", "A10G"),
    cpu=RESOURCES.get("cpu_cores", 2),
    memory=RESOURCES.get("memory_gib", 16) * 1024,
    timeout=RESOURCES.get("timeout_seconds", 1800),
    startup_timeout=RESOURCES.get("startup_timeout_seconds", 900),
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    block_network=True,
    volumes={"/cache": volume},
    is_generator=True,
)
def panel(files, prepared, settings, prompts, context, cases, execution_limit_seconds):
    from gemma4_lab.wsp_v2_panel import run_panel

    yield from run_panel(
        files, prepared, settings, prompts, context, cases, execution_limit_seconds
    )


@app.local_entrypoint()
def main(prepared: str):
    from gemma4_lab.wsp_v2_adapter import ADAPTER_NAMES, package_hashes

    source = (ROOT / prepared).resolve()
    if not source.is_relative_to(ROOT / "artifacts/wsp-v2-prepare") or not source.is_file():
        raise ValueError("Use a preserved prepare.json under artifacts/wsp-v2-prepare")
    payload = json.loads(source.read_text())
    if payload.get("passed") is not True or payload["compiled_adapters"] != {
        n: n for n in ADAPTER_NAMES
    }:
        raise ValueError("Preparation or its compiled aliases did not pass")
    root = source.parent / "submission"
    files = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    if package_hashes(files) != payload["file_sha256"]:
        raise ValueError("Prepared package hashes changed")
    if len(CASES) != 36:
        raise ValueError("The frozen evaluation panel has 36 cases")
    destination = (
        ROOT
        / SETTINGS.get("artifact_dir", "artifacts/wsp-v2-panel")
        / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        / "run.json"
    )
    report = {
        "stage": "wsp-v2-panel",
        "completed": False,
        "settings": SETTINGS,
        "cases": CASES,
        "estimate": ESTIMATE,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prepared_path": source.relative_to(ROOT).as_posix(),
        "prepared_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "file_sha256": package_hashes(files),
        "input_sha256": INPUT_HASHES,
        "events": [],
    }
    save_report(destination, report)
    terminal = None
    try:
        for event in panel.remote_gen(
            files, payload, SETTINGS, PROMPTS, CONTEXT, CASES, RESOURCES["timeout_seconds"]
        ):
            report["events"].append(event)
            if event["stage"] == "finished":
                terminal = event
                report["completed"] = event.get("completed") is True
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
    finally:
        save_report(destination, report)
        print(json.dumps({"report": str(destination), "completed": report["completed"]}))
    if terminal is None:
        raise SystemExit(1)
    print(json.dumps(terminal.get("assessment"), indent=2))
