"""CPU-only compilation of the reference YAML using official compiler wheels.

Run with MODAL_PROFILE=onepiecification. No model is loaded or called. Model and tool
registries are deliberately inert; passing this check is not scorer validation.
"""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
WHEEL_MANIFEST = {}
TOOL_NAMES = (
    "run_command",
    "read_file",
    "edit_file",
    "write_file",
    "get_status",
    "submit_patch",
    "get_code_neighbors",
    "search_similar_code",
    "get_code_subgraph",
)

image = None
CANDIDATE = "baseline"
if modal.is_local():
    from gemma4_lab.config import candidate_directory

    CANDIDATE = os.environ.get("GEMMA4_CANDIDATE", "baseline")
    candidate_path = candidate_directory(ROOT, CANDIDATE)
    WHEEL_MANIFEST = json.loads((ROOT / "requirements/remote-compiler-wheels.json").read_text())
    image = modal.Image.debian_slim(python_version="3.12")
    wheel_paths = []
    for wheel in WHEEL_MANIFEST["wheels"]:
        path = ROOT / "data/raw/official/wheelhouse" / wheel["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != wheel["sha256"]:
            raise ValueError(f"Official compiler wheel checksum mismatch: {path.name}")
        remote_path = f"/opt/compiler-wheels/{path.name}"
        image = image.add_local_file(path, remote_path, copy=True)
        wheel_paths.append(remote_path)
    image = image.uv_pip_install(*wheel_paths).add_local_dir(candidate_path, "/submission")
app = modal.App("gemma4-compiler-validation")


@app.function(
    image=image,
    cpu=1,
    memory=2048,
    timeout=120,
    startup_timeout=600,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
)
def validate_compiler() -> dict:
    import platform
    import time
    from importlib.metadata import distributions

    from adk_submission import (
        ModelRegistry,
        SubmissionLimits,
        ToolRegistry,
        compile_submission,
        discover_declared_models,
        validate_directory,
    )
    from google.adk.models.base_llm import BaseLlm

    class CompileOnlyModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            raise RuntimeError("Inference is disabled during compiler validation")
            yield  # Makes this an async generator, as required by BaseLlm.

    def inert_tool(name):
        def unavailable() -> str:
            raise RuntimeError("Tool execution is disabled during compiler validation")

        unavailable.__name__ = name
        return unavailable

    started = time.monotonic()
    limits = SubmissionLimits()
    validate_directory("/submission", limits=limits)
    declared = discover_declared_models("/submission")
    expected = {"gemma-4-e4b-it-qat-w4a16-ct"}
    if declared != expected:
        raise ValueError(f"Unexpected model declaration: {sorted(declared)}")
    models = ModelRegistry()
    for alias in sorted(declared):
        models.register(alias, CompileOnlyModel(model=alias))
    tools = ToolRegistry()
    for name in TOOL_NAMES:
        tools.register(name, inert_tool(name))
    agent = compile_submission(
        submission_dir="/submission",
        tool_registry=tools,
        model_registry=models,
        limits=limits,
    )
    return {
        "stage": "compiler-only",
        "passed": True,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "root_agent_name": agent.name,
        "root_agent_class": type(agent).__name__,
        "effective_root_generation_config": agent.generate_content_config.model_dump(
            mode="json", exclude_none=True
        )
        if agent.generate_content_config is not None
        else None,
        "declared_models": sorted(declared),
        "model_calls": 0,
        "tool_calls": 0,
        "competition_limits_applied": False,
        "inference_or_scoring_validated": False,
        "validation_seconds": time.monotonic() - started,
        "packages": {d.metadata["Name"]: d.version for d in distributions()},
    }


@app.local_entrypoint()
def main():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    if image is None:
        raise RuntimeError("Compiler validation must start from the local entry point")
    result = validate_compiler.remote()
    result["candidate"] = CANDIDATE
    result["profile"] = "onepiecification"
    result["git_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    result["modal_image_id"] = image.object_id
    result["official_wheels"] = WHEEL_MANIFEST
    result["submission_sha256"] = {
        path.relative_to(ROOT / "submissions" / CANDIDATE).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted((ROOT / "submissions" / CANDIDATE).rglob("*"))
        if path.is_file()
    }
    destination = (
        ROOT
        / "artifacts/runtime-validation"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{CANDIDATE}-compiler.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "report": str(destination)}, indent=2))
