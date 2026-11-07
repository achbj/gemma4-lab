"""CPU-only packaging of the v2 edit and controls from the preserved design-set capture."""

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
CAPTURE = "/cache/wsp-v2/capture-v1.safetensors"
TEMPLATE = "submissions/wsp-read-v1/agent.yaml"
image = None
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from gemma4_lab.modal_runtime import build_runtime_image

    image = build_runtime_image(ROOT).add_local_python_source("gemma4_lab")

app = modal.App("gemma4-wsp-v2-cpu-preparation")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    cpu=2,
    memory=8192,
    timeout=600,
    startup_timeout=900,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def prepare(v1_files: dict, template: str, alpha: float, expected_capture_sha256: str):
    import time
    import traceback

    from gemma4_lab.wsp_v2_adapter import prepare_v2

    start = time.monotonic()
    try:
        if hashlib.sha256(Path(CAPTURE).read_bytes()).hexdigest() != expected_capture_sha256:
            raise ValueError("Capture tensors differ from the preserved report")
        result = prepare_v2(CAPTURE, v1_files, template, alpha)
    except Exception as exc:
        result = {
            "passed": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
    return {**result, "elapsed_seconds": time.monotonic() - start, "gpu_allocated": False}


@app.local_entrypoint()
def main(capture_report: str, v1_prepare: str, alpha: float = 1.0):
    report_path = (ROOT / capture_report).resolve()
    capture = json.loads(report_path.read_text())
    if "failed" in capture or not report_path.is_relative_to(ROOT / "artifacts/wsp-v2-capture"):
        raise ValueError("Use a successful report under artifacts/wsp-v2-capture")
    v1_root = (ROOT / v1_prepare).resolve().parent
    v1_files = {
        p.relative_to(v1_root / "submission").as_posix(): p.read_bytes()
        for p in (v1_root / "submission/adapters/wsp_read").iterdir()
    }
    tag = "alpha" + str(alpha).replace(".", "p")
    destination = (
        ROOT
        / "artifacts/wsp-v2-prepare"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + tag)
    )
    result = prepare.remote(
        v1_files, (ROOT / TEMPLATE).read_text(), alpha, capture["output_sha256"]
    )
    files = result.pop("files", None)
    report = {
        "stage": "wsp-v2-preparation",
        "alpha": alpha,
        "capture_report": report_path.relative_to(ROOT).as_posix(),
        "capture_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "v1_prepare_sha256": hashlib.sha256((ROOT / v1_prepare).read_bytes()).hexdigest(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "src/gemma4_lab/wsp_v2_adapter.py",
                "infrastructure/modal/prepare_wsp_v2.py",
            )
        },
        **result,
    }
    if result.get("passed"):
        for name, value in files.items():
            path = destination / "submission" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "prepare.json").write_text(json.dumps(report, indent=2) + "\n")
    summary = {
        k: report.get(k) for k in ("passed", "error", "compiled_adapters", "package_size_bytes")
    }
    summary["report"] = str(destination / "prepare.json")
    print(json.dumps({**summary, "construction": report.get("construction")}, indent=2))
    if not result.get("passed"):
        sys.exit(1)
