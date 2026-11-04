"""One shared, pinned serving configuration for single-case and panel runs."""

import json
from pathlib import Path

MODEL_ALIAS = "gemma-4-e4b-it-qat-w4a16-ct"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL_ALIAS}/2"
MODEL_PATH = Path("/cache/models/e4b-v2")


def create_approved_server():
    """Construct the official server remotely; caller owns start/stop and logs."""
    source = json.loads((MODEL_PATH / "source-manifest.json").read_text())
    if source["model"] != MODEL_SOURCE:
        raise ValueError("Cached model source differs from the approved checkpoint")
    import torch
    from adk_submission import VllmConfig, VllmServer

    server = VllmServer(
        VllmConfig(
            model=str(MODEL_PATH),
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
    return server, {
        "model": MODEL_SOURCE,
        "gpu": torch.cuda.get_device_name(0),
        "checkpoint_manifest": source,
        "server_command": server.build_cmd(),
    }
