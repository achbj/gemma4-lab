"""One shared, pinned serving configuration for single-case and panel runs."""

import json
from pathlib import Path

MODEL_ALIAS = "gemma-4-e4b-it-qat-w4a16-ct"
MODEL_SOURCE = f"google/gemma-4/Other/{MODEL_ALIAS}/2"
MODEL_PATH = Path("/cache/models/e4b-v2")
APPLICATION_PREFIXES = (
    "The capital of France is",
    "def add(a, b):\n    return",
    "To list files in a directory, run",
)


def adapter_submission(root: Path) -> Path | None:
    """Return the submission directory when it ships LoRA adapters, else None."""
    return root if (root / "adapters").is_dir() else None


def adapter_application(top_logprobs, base_model: str, adapters: list[str]) -> dict:
    """Show each served adapter changes next-token log-probabilities and the base repeats.

    top_logprobs(model, prompt) returns one top-k {token: logprob} mapping. Synthetic
    prefixes only; a listed adapter name alone is not evidence of application.
    """
    from gemma4_lab.adapter_probe import logprob_distance

    drift, effects = 0.0, {name: [] for name in adapters}
    for prompt in APPLICATION_PREFIXES:
        before = top_logprobs(base_model, prompt)
        for name in adapters:
            effects[name].append(logprob_distance(top_logprobs(name, prompt), before))
        drift = max(drift, logprob_distance(top_logprobs(base_model, prompt), before))
    threshold = max(0.001, 10 * drift)
    return {
        "passed": bool(adapters) and all(max(v) > threshold for v in effects.values()),
        "maximum_base_drift_nats": drift,
        "effect_threshold_nats": threshold,
        "effect_lower_bounds_nats": effects,
    }


def create_approved_server(
    *,
    submission_directory: Path | None = None,
    model_path: Path | None = None,
    tensor_parallel_size: int = 1,
):
    """Construct the official server remotely; caller owns start/stop and logs."""
    model_path = MODEL_PATH if model_path is None else model_path
    if type(tensor_parallel_size) is not int or tensor_parallel_size < 1:
        raise ValueError("Tensor parallel size must be a positive integer")
    source = json.loads((model_path / "source-manifest.json").read_text())
    if source["model"] != MODEL_SOURCE:
        raise ValueError("Cached model source differs from the approved checkpoint")
    import torch
    from adk_submission import VllmConfig, VllmServer

    lora_settings = {"enable_lora": False}
    server_settings = {}
    if submission_directory is not None:
        from adk_submission import discover_adapters
        from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS

        adapters = discover_adapters(
            str(submission_directory), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS
        )
        if not adapters.adapters:
            raise ValueError("Adapter serving requires discovered adapters")
        ranks = [info.rank for info in adapters.adapters.values() if info.rank and info.rank > 0]
        lora_settings.update(
            enable_lora=True,
            max_loras=max(1, len(adapters.adapters)),
            max_lora_rank=max(ranks) if ranks else 128,
        )
        server_settings["adapter_manifest"] = adapters

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
            scheduler_reserve_full_isl=False,
            tensor_parallel_size=tensor_parallel_size,
            startup_timeout=1200,
            **lora_settings,
        ),
        **server_settings,
    )
    return server, {
        "model": MODEL_SOURCE,
        "gpu": torch.cuda.get_device_name(0),
        "checkpoint_manifest": source,
        "server_command": server.build_cmd(),
    }
