"""Shared immutable Linux runtime recipe; no local tensor-runtime imports."""

import hashlib
import json
from pathlib import Path

import modal


def build_runtime_image(root: Path):
    """Verify official wheels and reproduce the established image layer order."""
    manifest = json.loads((root / "requirements/remote-runtime-wheels.json").read_text())
    wheel_root = root / "data/raw/official/wheelhouse"
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
            root / "requirements/remote-runtime-base.txt", "/opt/runtime-base.txt", copy=True
        )
        .uv_pip_install(
            requirements=[str(root / "requirements/remote-runtime-base.txt")],
            extra_options="--no-build-isolation",
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
        .uv_pip_install(requirements=[str(root / "requirements/remote-evaluation-base.txt")])
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
    return image
