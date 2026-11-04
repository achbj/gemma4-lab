"""Controlled adapter packaging and numerical checks; ML imports are remote-only."""

import hashlib
import json
import math
from pathlib import Path

from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_PATH, MODEL_SOURCE

ADAPTER_NAMES = ("probe_zero", "probe_active")
PACKAGE_FILES = frozenset(
    {"agent.yaml"}
    | {
        f"adapters/{name}/{filename}"
        for name in ADAPTER_NAMES
        for filename in ("adapter_config.json", "adapter_model.safetensors")
    }
)
MAX_PACKAGE_BYTES = 1024 * 1024
REQUEST_ORDER = (
    "base_before",
    "zero_before",
    "active_before",
    "active_after",
    "zero_after",
    "base_after",
)


def package_hashes(files: dict[str, bytes]) -> dict[str, str]:
    if set(files) != PACKAGE_FILES:
        raise ValueError("Probe package has missing or unexpected files")
    if any(not isinstance(value, bytes) or not value for value in files.values()):
        raise ValueError("Probe package files must be nonempty bytes")
    if sum(map(len, files.values())) > MAX_PACKAGE_BYTES:
        raise ValueError("Probe package exceeds its 1 MiB allocation")
    return {name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())}


def write_package(root: Path, files: dict[str, bytes], expected: dict[str, str]) -> None:
    if package_hashes(files) != expected:
        raise ValueError("Probe package differs from CPU preparation")
    root.mkdir(parents=True, exist_ok=True)
    for name, value in files.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Probe package path escapes its directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def logprob_distance(left: dict[str, float], right: dict[str, float]) -> float:
    """Lower bound on maximum token log-probability change in two top-k lists."""
    for values in (left, right):
        if not values or any(not math.isfinite(v) or v > 1e-6 for v in values.values()):
            raise ValueError("Missing, nonfinite, or invalid token log-probabilities")
    bounds = [abs(left[token] - right[token]) for token in left.keys() & right.keys()]
    # An absent token has probability no greater than the smallest top-k entry.
    bounds.extend(max(0.0, left[token] - min(right.values())) for token in left.keys() - right)
    bounds.extend(max(0.0, right[token] - min(left.values())) for token in right.keys() - left)
    return max(bounds, default=0.0)


def assess_effect(cases: list[dict], settings: dict) -> dict:
    if len(cases) != len(settings["prompts"]):
        raise ValueError("All fixed synthetic prefixes must be measured")
    rows = []
    for prompt, case in zip(settings["prompts"], cases, strict=True):
        if case["prompt"] != prompt or set(case["distributions"]) != set(REQUEST_ORDER):
            raise ValueError("Unexpected synthetic prefix or missing control")
        d = case["distributions"]
        controls = {
            "base_repeat": logprob_distance(d["base_before"], d["base_after"]),
            "zero_repeat": logprob_distance(d["zero_before"], d["zero_after"]),
            "active_repeat": logprob_distance(d["active_before"], d["active_after"]),
            "zero_base_before": logprob_distance(d["base_before"], d["zero_before"]),
            "zero_base_after": logprob_distance(d["base_after"], d["zero_after"]),
        }
        effect = min(
            logprob_distance(d["active_before"], d["zero_before"]),
            logprob_distance(d["active_after"], d["zero_after"]),
        )
        rows.append({"prompt": prompt, "controls": controls, "effect_lower_bound_nats": effect})
    drift = max(v for row in rows for v in row["controls"].values())
    threshold = max(settings["minimum_effect_nats"], settings["effect_to_noise_ratio"] * drift)
    count = sum(row["effect_lower_bound_nats"] > threshold for row in rows)
    return {
        "passed": drift <= settings["control_tolerance_nats"]
        and count >= settings["required_effect_cases"],
        "maximum_control_drift_nats": drift,
        "effect_threshold_nats": threshold,
        "effect_cases": count,
        "cases": rows,
    }


def prepare_probe(template: str, settings: dict) -> dict:
    """Create two tiny diagnostic adapters on remote Linux without loading the base."""
    import tempfile

    import torch
    import yaml
    from adk_submission import (
        ModelRegistry,
        ToolRegistry,
        compile_submission,
        discover_adapters,
        discover_declared_models,
        validate_directory,
    )
    from google.adk.models.base_llm import BaseLlm
    from safetensors import safe_open
    from safetensors.torch import save_file
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, build_submission_limits
    from swegemma.harness.agent_runner import resolve_swegemma_adapter

    source = json.loads((MODEL_PATH / "source-manifest.json").read_text())
    config_bytes = (MODEL_PATH / "config.json").read_bytes()
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    if source["model"] != MODEL_SOURCE or config_hash != settings["base_config_sha256"]:
        raise ValueError("Probe checkpoint/config differs from the approved source")
    if source["files"]["config.json"]["sha256"] != config_hash:
        raise ValueError("Checkpoint config differs from its staging manifest")
    config = json.loads(config_bytes)["text_config"]
    layer = config["num_hidden_layers"] - 1
    head_dim = (
        config["global_head_dim"]
        if config["layer_types"][layer] == "full_attention"
        else config["head_dim"]
    )
    output_width = config["hidden_size"]
    input_width = config["num_attention_heads"] * head_dim
    checkpoints = sorted(MODEL_PATH.glob("*.safetensors"))
    if len(checkpoints) != 1:
        raise ValueError("Probe expects the staged single-file checkpoint")
    checkpoint = checkpoints[0]
    if checkpoint.stat().st_size != source["files"][checkpoint.name]["size_bytes"]:
        raise ValueError("Checkpoint file size differs from staging")
    module = f"model.language_model.layers.{layer}.self_attn.o_proj"
    with safe_open(checkpoint, framework="pt", device="cpu") as weights:
        packed = weights.get_slice(module + ".weight_packed")
        packed_shape = packed.get_shape()
        if packed.get_dtype() != "I32" or packed_shape != [
            output_width,
            math.ceil(input_width / 8),
        ]:
            raise ValueError("Actual int4 projection metadata disagrees with config dimensions")
        shape_key = module + ".weight_shape"
        if shape_key in weights.keys():
            if weights.get_tensor(shape_key).tolist() != [output_width, input_width]:
                raise ValueError("Stored projection shape disagrees with config dimensions")

    rank = settings["rank"]
    if rank != 8 or not 0 < rank <= min(input_width, output_width):
        raise ValueError("This diagnostic is fixed to rank 8")
    generator = torch.Generator(device="cpu").manual_seed(settings["seed"])
    a = (torch.randn(rank, input_width, generator=generator) / math.sqrt(input_width)).bfloat16()
    b = (torch.randn(output_width, rank, generator=generator) / math.sqrt(rank)).bfloat16()
    peft = {
        "base_model_name_or_path": str(MODEL_PATH),
        "bias": "none",
        "fan_in_fan_out": False,
        "inference_mode": True,
        "lora_alpha": rank,
        "lora_dropout": 0.0,
        "peft_type": "LORA",
        "r": rank,
        "target_modules": ["o_proj"],
        "task_type": "CAUSAL_LM",
        "use_dora": False,
        "use_rslora": False,
    }

    class CompileOnlyModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            raise RuntimeError("Inference is disabled during CPU preparation")
            yield

    with tempfile.TemporaryDirectory(prefix="gemma4-adapter-prepare-") as directory:
        root = Path(directory)
        (root / "agent.yaml").write_text(template)
        if yaml.safe_load(template).get("adapter") != "probe_active":
            raise ValueError("Unexpected probe agent template")
        for name in ADAPTER_NAMES:
            folder = root / "adapters" / name
            folder.mkdir(parents=True)
            (folder / "adapter_config.json").write_text(json.dumps(peft, indent=2) + "\n")
            prefix = "base_model.model." + module
            save_file(
                {
                    prefix + ".lora_A.weight": a,
                    prefix + ".lora_B.weight": torch.zeros_like(b) if name == "probe_zero" else b,
                },
                folder / "adapter_model.safetensors",
                metadata={"format": "pt"},
            )
        limits, generation = build_submission_limits()
        validate_directory(root, limits=limits)
        if discover_declared_models(root) != {MODEL_ALIAS}:
            raise ValueError("Unexpected declared base model")
        adapters = discover_adapters(root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
        if set(adapters.adapters) != set(ADAPTER_NAMES):
            raise ValueError("Official adapter discovery disagrees with the probe package")
        models = ModelRegistry()
        for alias in (MODEL_ALIAS, *ADAPTER_NAMES):
            models.register(alias, CompileOnlyModel(model=alias))
        compiled = {}
        for name in ADAPTER_NAMES:
            document = yaml.safe_load(template)
            document["adapter"] = name
            (root / "agent.yaml").write_text(yaml.safe_dump(document))
            agent = compile_submission(
                root,
                tool_registry=ToolRegistry(),
                model_registry=models,
                limits=limits,
                generation_constraints=generation,
                adapter_manifest=adapters,
                adapter_resolver_fn=lambda base, info: resolve_swegemma_adapter(base, info, models),
            )
            if agent.model.model != name:
                raise ValueError("Compiler did not resolve the expected adapter")
            compiled[name] = agent.model.model
        (root / "agent.yaml").write_text(template)
        files = {name: (root / name).read_bytes() for name in PACKAGE_FILES}
    return {
        "passed": True,
        "base_model": MODEL_SOURCE,
        "checkpoint_manifest": source,
        "base_config_sha256": config_hash,
        "projection": module,
        "packed_shape": packed_shape,
        "input_width": input_width,
        "output_width": output_width,
        "rank": rank,
        "seed": settings["seed"],
        "compiled_adapters": compiled,
        "file_sha256": package_hashes(files),
        "files": files,
    }
