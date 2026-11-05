"""Package the frozen prototype intervention and its zero/random controls remotely."""

import hashlib
import json
import math
import tempfile
from pathlib import Path

from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_PATH, MODEL_SOURCE

ADAPTER_NAMES = ("wsp_zero", "wsp_read", "wsp_random")
EXPECTED_MODULE = "model.language_model.layers.41.self_attn.o_proj"
PACKAGE_FILES = frozenset(
    {"agent.yaml"}
    | {
        f"adapters/{name}/{file}"
        for name in ADAPTER_NAMES
        for file in ("adapter_config.json", "adapter_model.safetensors")
    }
)
MAX_PACKAGE_BYTES = 1024 * 1024


def package_hashes(files: dict[str, bytes]) -> dict[str, str]:
    if set(files) != PACKAGE_FILES or any(
        not isinstance(v, bytes) or not v for v in files.values()
    ):
        raise ValueError("Intervention package has missing, empty or unexpected files")
    if sum(map(len, files.values())) >= MAX_PACKAGE_BYTES:
        raise ValueError("Intervention package must remain below 1 MiB")
    return {name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())}


def write_package(root: Path, files: dict[str, bytes], expected: dict[str, str]) -> None:
    if package_hashes(files) != expected:
        raise ValueError("Intervention package differs from CPU preparation")
    for name, value in files.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Intervention path escapes its directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)


def _validated_vectors(inspection):
    if any(
        inspection.get(key) is not True
        for key in ("completed", "inspection_passed", "runtime_identity_passed")
    ):
        raise ValueError("A completed, successful numerical inspection is required")
    settings, result = inspection["settings"], inspection["result"]
    if (
        result["model"] != MODEL_SOURCE
        or settings["model"] != MODEL_SOURCE
        or inspection["modal_image_id"] != settings["expected_runtime_image"]
        or settings["rank"] != 8
        or settings["target_layer"] != 41
        or settings["kv_source_layer"] != 23
        or result["base_modified"] is not False
    ):
        raise ValueError(
            "Inspection model, runtime, target or rank differs from the frozen construction"
        )
    if type(settings["seed"]) is not int or not 0 <= settings["seed"] < 2**63:
        raise ValueError("Invalid fixed random-control seed")
    geometry = result["geometry"]
    if geometry.get("passed") is not True:
        raise ValueError("Numerical prototype geometry did not pass")
    vectors = []
    for name, width in (("a", 4096), ("b", 2560)):
        vector = geometry[name]
        if (
            not isinstance(vector, list)
            or len(vector) != width
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector)
            or not math.isclose(math.fsum(v * v for v in vector), 1.0, abs_tol=1e-5)
        ):
            raise ValueError(f"Expected a finite unit {name} vector of width {width}")
        vectors.append(vector)
    norm, beta = result["output_projection"]["frobenius_norm"], geometry["proposed_beta"]
    if (
        type(norm) not in (int, float)
        or not math.isfinite(norm)
        or norm <= 0
        or type(beta) not in (int, float)
        or not math.isfinite(beta)
        or beta <= 0
        or settings["relative_frobenius"] != 0.01
        or not math.isclose(beta, norm * settings["relative_frobenius"], rel_tol=1e-10)
    ):
        raise ValueError("Proposed beta differs from the frozen one-percent norm")
    projections = [p for p in result["projection_provenance"] if p["module"] == EXPECTED_MODULE]
    if len(projections) != 1 or projections[0]["shape"] != [2560, 4096]:
        raise ValueError("Inspected output projection differs from the fixed target")
    hashes = result["verified_model_sha256"]
    if (
        not isinstance(hashes, dict)
        or len(hashes) != 8
        or "config.json" not in hashes
        or any(
            not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v)
            for v in hashes.values()
        )
    ):
        raise ValueError("Complete verified base-file identities are required")
    return *vectors, float(beta)


def prepare_intervention(inspection: dict, template: str) -> dict:
    """Create/compile three adapters; no base checkpoint, gradients or inference."""
    a_values, b_values, beta = _validated_vectors(inspection)
    if not isinstance(template, str) or not template.strip():
        raise ValueError("A nonempty preserved agent template is required")
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
    from safetensors.torch import save_file
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, build_submission_limits
    from swegemma.harness.agent_runner import resolve_swegemma_adapter

    document = yaml.safe_load(template)
    if (
        not isinstance(document, dict)
        or document.get("adapter") != "wsp_read"
        or document.get("model") != MODEL_ALIAS
    ):
        raise ValueError("Expected the fixed base-model/wsp_read agent template")
    rank, input_width, output_width = 8, 4096, 2560
    a = torch.zeros((rank, input_width), dtype=torch.bfloat16)
    b = torch.zeros((output_width, rank), dtype=torch.bfloat16)
    a[0] = torch.tensor(a_values, dtype=torch.float32).bfloat16()
    b[:, 0] = (beta * torch.tensor(b_values, dtype=torch.float32)).bfloat16()
    a_norm, b_norm = a[0].float().norm().item(), b[:, 0].float().norm().item()
    target_norm = a_norm * b_norm
    if not math.isfinite(target_norm) or target_norm <= 0:
        raise ValueError("Rounded semantic factors have no finite nonzero effect")
    generator = torch.Generator(device="cpu").manual_seed(inspection["settings"]["seed"])
    random_a = torch.randn(input_width, generator=generator, dtype=torch.float32)
    random_b = torch.randn(output_width, generator=generator, dtype=torch.float32)
    ar, br = torch.zeros_like(a), torch.zeros_like(b)
    ar[0] = (random_a / random_a.norm() * a_norm).bfloat16()
    br[:, 0] = (random_b / random_b.norm() * (target_norm / ar[0].float().norm())).bfloat16()
    factors = {
        "wsp_zero": (a.clone(), torch.zeros_like(b)),
        "wsp_read": (a, b),
        "wsp_random": (ar, br),
    }
    norms = {}
    for name, (left, right) in factors.items():
        if torch.count_nonzero(left[1:]).item() or torch.count_nonzero(right[:, 1:]).item():
            raise ValueError("Inactive rank components must remain exactly zero")
        an, bn = left[0].float().norm().item(), right[:, 0].float().norm().item()
        if not math.isfinite(an) or not math.isfinite(bn) or an <= 0 or bn < 0:
            raise ValueError("Rounded adapter factors have invalid norms")
        norms[name] = {
            "a_norm": an,
            "b_norm": bn,
            "delta_frobenius_norm": an * bn,
            "relative_base_frobenius": an
            * bn
            / inspection["result"]["output_projection"]["frobenius_norm"],
            "inactive_components_zero": True,
        }
    match_error = abs(norms["wsp_random"]["delta_frobenius_norm"] / target_norm - 1)
    if (
        match_error > 0.005
        or abs(norms["wsp_random"]["a_norm"] / a_norm - 1) > 0.005
        or abs(norms["wsp_random"]["b_norm"] / b_norm - 1) > 0.005
    ):
        raise ValueError("Rounded random control does not match semantic factor/delta norms")
    if norms["wsp_zero"]["delta_frobenius_norm"] != 0:
        raise ValueError("Zero control has a nonzero factor effect")
    if not torch.equal(factors["wsp_zero"][0], factors["wsp_read"][0]):
        raise ValueError("Zero/read adapters must have identical A factors")
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
            raise RuntimeError("Inference is disabled during intervention preparation")
            yield

    with tempfile.TemporaryDirectory(prefix="wsp-adapter-prepare-") as directory:
        root = Path(directory)
        (root / "agent.yaml").write_text(template)
        prefix = "base_model.model." + EXPECTED_MODULE
        for name, (left, right) in factors.items():
            folder = root / "adapters" / name
            folder.mkdir(parents=True)
            (folder / "adapter_config.json").write_text(json.dumps(peft, indent=2) + "\n")
            save_file(
                {prefix + ".lora_A.weight": left, prefix + ".lora_B.weight": right},
                folder / "adapter_model.safetensors",
                metadata={"format": "pt"},
            )
        limits, generation = build_submission_limits()
        validate_directory(root, limits=limits)
        if discover_declared_models(root) != {MODEL_ALIAS}:
            raise ValueError("Unexpected declared model")
        adapters = discover_adapters(root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
        if set(adapters.adapters) != set(ADAPTER_NAMES):
            raise ValueError("Official discovery disagrees with the three adapter aliases")
        models = ModelRegistry()
        for name in (MODEL_ALIAS, *ADAPTER_NAMES):
            models.register(name, CompileOnlyModel(model=name))
        compiled = {}
        for name in ADAPTER_NAMES:
            selected = {**document, "adapter": name}
            (root / "agent.yaml").write_text(yaml.safe_dump(selected))
            validate_directory(root, limits=limits)
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
                raise ValueError("Compiler did not resolve the selected adapter")
            compiled[name] = agent.model.model
        (root / "agent.yaml").write_text(template)
        files = {name: (root / name).read_bytes() for name in PACKAGE_FILES}
    return {
        "passed": True,
        "files": files,
        "file_sha256": package_hashes(files),
        "adapter_names": list(ADAPTER_NAMES),
        "expected_module": EXPECTED_MODULE,
        "projection": EXPECTED_MODULE,
        "rank": rank,
        "input_width": input_width,
        "output_width": output_width,
        "package_size_bytes": sum(map(len, files.values())),
        "norms": norms,
        "random_norm_match_relative_error": match_error,
        "proposed_beta": beta,
        "seed": inspection["settings"]["seed"],
        "compiled_adapters": compiled,
        "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
        "base_identity": {
            "model": MODEL_SOURCE,
            "runtime_image": inspection["modal_image_id"],
            "verified_model_sha256": inspection["result"]["verified_model_sha256"],
            "inspection_git_commit": inspection["git_commit"],
        },
        "base_config_sha256": inspection["result"]["verified_model_sha256"]["config.json"],
        "inspection_identity_sha256": hashlib.sha256(
            json.dumps(inspection, sort_keys=True).encode()
        ).hexdigest(),
        "base_modified": False,
        "model_forward_passes": 0,
        "gradient_steps": 0,
    }
