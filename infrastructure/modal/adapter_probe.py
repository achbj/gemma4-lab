"""Prepare the package on CPU, then explicitly run its bounded GPU probe."""

import hashlib
import json
import os
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.adapter_probe import package_hashes, write_package
from gemma4_lab.panels import save_report
from gemma4_lab.remote_serving import MODEL_SOURCE

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
SETTINGS = {}
CONFIG = {}
TEMPLATE = ""
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
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.config import estimate_run, load_config
    from gemma4_lab.modal_runtime import build_runtime_image

    SETTINGS = tomllib.loads((ROOT / "configs/adapter-probe-v1.toml").read_text())
    CONFIG = load_config(ROOT / SETTINGS["runtime_config"])
    RESOURCES = CONFIG["modal"]
    estimate_run(CONFIG)
    if CONFIG["sources"]["model"] != MODEL_SOURCE:
        raise ValueError("Adapter probe must use the approved E4B checkpoint")
    TEMPLATE = (ROOT / SETTINGS["submission_template"]).read_text()
    SETTINGS["base_config_sha256"] = hashlib.sha256(
        (ROOT / "artifacts/runtime-validation/adapter-base-config.json").read_bytes()
    ).hexdigest()
    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-adapter-compatibility")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


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
    volumes={"/cache": volume},
)
def prepare(template: str, settings: dict) -> dict:
    import platform
    import time
    import traceback
    from importlib.metadata import distributions

    from gemma4_lab.adapter_probe import prepare_probe

    started = time.monotonic()
    try:
        result = prepare_probe(template, settings)
    except Exception as exc:
        result = {
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    result.update(
        elapsed_seconds=time.monotonic() - started,
        python=platform.python_version(),
        packages={d.metadata["Name"]: d.version for d in distributions()},
    )
    return result


def preparation_source_hashes() -> dict[str, str]:
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "src/gemma4_lab/adapter_probe.py",
            "src/gemma4_lab/remote_serving.py",
            "src/gemma4_lab/modal_runtime.py",
        )
    }


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
def probe(files: dict, prepared: dict, settings: dict, execution_limit_seconds: int):
    from gemma4_lab.adapter_serving_probe import run_probe

    yield from run_probe(files, prepared, settings, execution_limit_seconds)


def run_gpu(preflight: str) -> None:
    path = (ROOT / preflight).resolve()
    artifacts = (ROOT / "artifacts").resolve()
    if not path.is_relative_to(artifacts):
        raise ValueError("Preparation report must be inside artifacts/")
    prepared = json.loads(path.read_text())
    if not prepared.get("passed") or not prepared.get("completed"):
        raise ValueError("Successful completed CPU preparation is required")
    if prepared["settings"] != SETTINGS:
        raise ValueError("Probe settings changed after preparation")
    if prepared["preparation_source_sha256"] != preparation_source_hashes():
        raise ValueError("Preparation or serving code changed; repeat CPU preparation")
    if prepared["template_sha256"] != hashlib.sha256(TEMPLATE.encode()).hexdigest():
        raise ValueError("Probe template changed after preparation")
    if prepared["modal_image_id"] != image.object_id:
        raise ValueError("Runtime image changed after preparation")
    package = (ROOT / prepared["package_directory"]).resolve()
    if not package.is_relative_to(artifacts) or any(p.is_symlink() for p in package.rglob("*")):
        raise ValueError("Unsafe probe package directory")
    files = {
        p.relative_to(package).as_posix(): p.read_bytes() for p in package.rglob("*") if p.is_file()
    }
    if package_hashes(files) != prepared["file_sha256"]:
        raise ValueError("Prepared package file hashes changed")
    folder = ROOT / "artifacts/adapter-probe-v1" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = folder / "gpu.json"
    if destination.exists():
        raise ValueError("Preserve the existing GPU report")
    report = {
        "stage": "adapter-runtime-probe",
        "completed": False,
        "passed": False,
        "preparation_report": path.relative_to(ROOT).as_posix(),
        "preparation_report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "settings": SETTINGS,
        "run_config": CONFIG,
        "modal_image_id": image.object_id,
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "runtime_probe_source_sha256": hashlib.sha256(
            (ROOT / "src/gemma4_lab/adapter_serving_probe.py").read_bytes()
        ).hexdigest(),
        "events": [],
    }
    save_report(destination, report)
    try:
        for event in probe.remote_gen(files, prepared, SETTINGS, RESOURCES["timeout_seconds"]):
            report["events"].append(event)
            if event["stage"] == "finished":
                report.update(completed=event["completed"], passed=event["passed"])
            save_report(destination, report)
            print(
                json.dumps(
                    {k: event[k] for k in ("stage", "prefix_index", "condition") if k in event}
                ),
                flush=True,
            )
    except Exception as exc:
        report["invocation_error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        save_report(destination, report)
        print(json.dumps({"passed": report["passed"], "report": str(destination)}))
    if not report["passed"]:
        raise SystemExit(1)


@app.local_entrypoint()
def main(prepare_only: bool = False, preflight: str = ""):
    if os.environ.get("MODAL_PROFILE") != "ach-bj100" or image is None:
        raise ValueError("Start from the local entrypoint with MODAL_PROFILE=ach-bj100")
    if prepare_only == bool(preflight):
        raise ValueError("Select exactly one of --prepare-only or --preflight REPORT")
    if preflight:
        run_gpu(preflight)
        return
    folder = ROOT / "artifacts/adapter-probe-v1" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = folder / "prepare.json"
    if destination.exists():
        raise ValueError("Preserve the existing preparation report")
    report = {
        "stage": "adapter-preparation",
        "completed": False,
        "passed": False,
        "settings": SETTINGS,
        "template_sha256": hashlib.sha256(TEMPLATE.encode()).hexdigest(),
        "preparation_source_sha256": preparation_source_hashes(),
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    }
    save_report(destination, report)
    try:
        result = prepare.remote(TEMPLATE, SETTINGS)
        files = result.pop("files", None)
        report.update(result, completed=True, modal_image_id=image.object_id)
        report["runtime_identity_passed"] = image.object_id == SETTINGS["expected_runtime_image"]
        if files is not None:
            package = folder / "submission"
            write_package(package, files, report["file_sha256"])
            report["package_directory"] = package.relative_to(ROOT).as_posix()
        if not report["runtime_identity_passed"]:
            report.update(passed=False, error="Runtime image changed; investigate before GPU use")
    except Exception as exc:
        report.update(
            passed=False, invocation_error={"type": type(exc).__name__, "message": str(exc)}
        )
        raise
    finally:
        save_report(destination, report)
        print(json.dumps({"passed": report["passed"], "report": str(destination)}))
    if not report["passed"]:
        raise SystemExit(1)
