"""Build the official-wheel runtime and perform one bounded E4B tool-call check.

ML imports occur only inside the remote Linux function. --build-only constructs
the image without allocating a GPU. This check is not a software-repair score.
"""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL_ALIAS = "gemma-4-e4b-it-qat-w4a16-ct"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL_ALIAS}/2"
RESOURCES = {
    "gpu": "L4",
    "cpu_cores": 2,
    "memory_gib": 16,
    "timeout_seconds": 1800,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
image = None
CONFIG = {}
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.config import estimate_run, load_config

    CONFIG = load_config(ROOT / "configs/baseline.toml")
    estimate_run(CONFIG)
    if CONFIG["sources"]["model"] != MODEL_SOURCE:
        raise ValueError("This smoke check is pinned to the approved E4B version 2")
    RESOURCES = CONFIG["modal"]
    manifest = json.loads((ROOT / "requirements/remote-runtime-wheels.json").read_text())
    wheel_root = ROOT / "data/raw/official/wheelhouse"
    expected = {item["name"] for item in manifest["wheels"]}
    if {p.name for p in wheel_root.iterdir()} != expected:
        raise ValueError("Wheelhouse contains missing or unexpected files")
    for item in manifest["wheels"]:
        path = wheel_root / item["name"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Official runtime wheel checksum mismatch: {path.name}")
    # CUDA 12.8 wheels match the official vLLM wheel's Torch 2.10.0 requirement.
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git", "libnuma1", "libgl1", "libglib2.0-0", "build-essential")
        .uv_pip_install(
            "torch==2.10.0",
            "torchaudio==2.10.0",
            "torchvision==0.25.0",
            index_url="https://download.pytorch.org/whl/cu128",
        )
        .add_local_dir(wheel_root, "/opt/wheelhouse", copy=True)
        .add_local_file(
            ROOT / "requirements/remote-runtime-base.txt", "/opt/runtime-base.txt", copy=True
        )
        .uv_pip_install(
            requirements=["/opt/runtime-base.txt"], extra_options="--no-build-isolation"
        )
        # Match the starter's no-dependency wheel overlay; metadata in the
        # supplied wheels is inconsistent even in the verified reference image.
        .uv_pip_install(
            *[f"/opt/wheelhouse/{name}" for name in sorted(expected)],
            extra_options="--no-deps --reinstall",
        )
        .run_commands(
            "python -c 'import adk_submission, transformers, litellm; "
            'print("runtime imports passed")\''
        )
        .env(
            {
                "TRANSFORMERS_NO_TF": "1",
                "TRANSFORMERS_NO_FLAX": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HF_HUB_OFFLINE": "1",
                "VLLM_NO_USAGE_STATS": "1",
                "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
                "VLLM_ENGINE_READY_TIMEOUT_S": "1200",
                "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
                "NCCL_DEBUG": "WARN",
                "LITELLM_LOCAL_MODEL_COST_MAP": "True",
                "LITELLM_TELEMETRY": "False",
                "LITELLM_LOG": "WARNING",
                "OPENAI_API_KEY": "EMPTY",
                "LOCAL_API_KEY": "EMPTY",
                "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
                "OTEL_SDK_DISABLED": "true",
                "OTEL_PYTHON_DISABLED": "true",
            }
        )
    )
app = modal.App("gemma4-e4b-serving-smoke")
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
    retries=0,
    volumes={"/cache": volume},
)
def serve_smoke() -> dict:
    import platform
    import time
    import traceback
    from importlib.metadata import distributions

    import requests

    started = time.monotonic()
    server = None
    result = {
        "stage": "serving-smoke",
        "passed": False,
        "model": MODEL_SOURCE,
        "python": platform.python_version(),
        "gpu": None,
        "tensor_parallel_size": 1,
        "max_model_len": 32768,
        "packages": {d.metadata["Name"]: d.version for d in distributions()},
        "software_repair_score_measured": False,
    }
    try:
        import torch
        from adk_submission import VllmConfig, VllmServer

        result["gpu"] = torch.cuda.get_device_name(0)
        model_path = Path("/cache/models/e4b-v2")
        source = json.loads((model_path / "source-manifest.json").read_text())
        if source["model"] != MODEL_SOURCE:
            raise ValueError("Cached model source differs from the approved checkpoint")
        result["checkpoint_manifest"] = source
        server = VllmServer(
            VllmConfig(
                model=str(model_path),
                host="127.0.0.1",
                port=8000,
                tool_call_parser="gemma4",
                reasoning_parser="gemma4",
                max_model_len=32768,
                dtype="bfloat16",
                gpu_memory_utilization=0.90,
                enable_auto_tool_choice=True,
                enable_lora=False,
                scheduler_reserve_full_isl=False,
                tensor_parallel_size=1,
                startup_timeout=1200,
            )
        )
        result["server_command"] = server.build_cmd()
        server.start()
        result["server_ready_seconds"] = time.monotonic() - started
        available = requests.get(server.base_url + "/models", timeout=10)
        available.raise_for_status()
        served_model = available.json()["data"][0]["id"]
        # A short protocol check, intentionally separate from the reference agent's
        # unchanged sampling settings. No issue or evaluation data is used here.
        payload = {
            "model": served_model,
            "messages": [
                {"role": "user", "content": "Call get_status now to inspect the task budget."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_status",
                        "description": "Inspect remaining task time and tool budget.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                }
            ],
            "tool_choice": "auto",
            "temperature": 0.2,
            "top_p": 0.95,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        response = requests.post(server.base_url + "/chat/completions", json=payload, timeout=180)
        response.raise_for_status()
        result["request"] = payload
        result["response"] = response.json()
        calls = result["response"]["choices"][0]["message"].get("tool_calls") or []
        if (
            len(calls) == 1
            and calls[0]["function"]["name"] == "get_status"
            and json.loads(calls[0]["function"]["arguments"]) == {}
        ):
            followup = dict(payload)
            followup["messages"] = [
                *payload["messages"],
                result["response"]["choices"][0]["message"],
                {
                    "role": "tool",
                    "tool_call_id": calls[0]["id"],
                    "content": json.dumps(
                        {"status": "ready", "remaining_seconds": 60, "remaining_tool_calls": 9}
                    ),
                },
            ]
            reply = requests.post(server.base_url + "/chat/completions", json=followup, timeout=180)
            reply.raise_for_status()
            result["followup_response"] = reply.json()
            result["synthetic_tool_result"] = True
            final_message = result["followup_response"]["choices"][0]["message"]
            result["passed"] = bool(final_message.get("content")) and not final_message.get(
                "tool_calls"
            )
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()
    finally:
        if server is not None:
            server.stop()
            if Path(server.log_path).is_file():
                result["server_log"] = Path(server.log_path).read_text(errors="replace")[-150000:]
    result["elapsed_seconds"] = time.monotonic() - started
    return result


@app.local_entrypoint()
def main(build_only: bool = False):
    if build_only:
        print(json.dumps({"image": image.object_id, "gpu_allocated": False}))
        return
    staging = sorted((ROOT / "artifacts/runtime-validation").glob("*-model-staging.json"))
    if not staging or json.loads(staging[-1].read_text())["model"] != MODEL_SOURCE:
        raise ValueError("Stage and verify the approved checkpoint on CPU before allocating a GPU")
    result = serve_smoke.remote()
    result["git_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    result["modal_image_id"] = image.object_id
    destination = (
        ROOT
        / "artifacts/runtime-validation"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-serving-smoke.json")
    )
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "report": str(destination)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
