"""CPU packaging of the v2 keyed rank-one edit and its controls (no inference, no gradients).

Delta W = alpha * d (C^-1 k*)^T / (k*^T C^-1 k*), so Delta W k* = alpha d. It is stored as a
rank-1 component inside rank-8/alpha-8 PEFT on the frozen layer's `o_proj`.
"""

import hashlib
import json
import math
import tempfile
from pathlib import Path

from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_PATH

NEW_ADAPTERS = ("wsp2_zero", "wsp2_a", "wsp2_neg", "wsp2_random")
ADAPTER_NAMES = (*NEW_ADAPTERS, "wsp_read")
RANK = 8
RIDGE_RELATIVE = 1e-3
SEED = 20261108
MAX_PACKAGE_BYTES = 1024 * 1024
PACKAGE_FILES = frozenset(
    {"agent.yaml"}
    | {
        f"adapters/{name}/{file}"
        for name in ADAPTER_NAMES
        for file in ("adapter_config.json", "adapter_model.safetensors")
    }
)


def package_hashes(files: dict[str, bytes]) -> dict[str, str]:
    if set(files) != PACKAGE_FILES or any(
        not isinstance(v, bytes) or not v for v in files.values()
    ):
        raise ValueError("Package has missing, empty or unexpected files")
    if sum(map(len, files.values())) >= MAX_PACKAGE_BYTES:
        raise ValueError("Package must remain below 1 MiB")
    return {name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())}


def build_factors(capture_path: str, alpha: float, seed: int = SEED) -> dict:
    """Return bf16 LoRA factors, module name and realized-effect checks."""
    import torch
    from safetensors import safe_open

    with safe_open(capture_path, framework="pt") as handle:
        layer = int(handle.metadata()["layer"])
        k = handle.get_tensor(f"layer{layer}.k_star").double()
        d = handle.get_tensor(f"layer{layer}.d").double()
        c = handle.get_tensor("covariance").double()
    n = k.numel()
    ridge = RIDGE_RELATIVE * float(c.diag().mean())
    v = torch.linalg.solve(c + ridge * torch.eye(n, dtype=torch.float64), k)
    s = float(k @ v)
    if not math.isfinite(s) or s <= 0:
        raise ValueError("Keyed denominator is not positive")
    a_row, b_col = (v / s), alpha * d
    a = torch.zeros((RANK, n), dtype=torch.bfloat16)
    b = torch.zeros((d.numel(), RANK), dtype=torch.bfloat16)
    a[0], b[:, 0] = a_row.bfloat16(), b_col.bfloat16()
    realized = b[:, 0].double() * float(a[0].double() @ k)
    error = float((realized - alpha * d).norm() / (alpha * d).norm())
    generator = torch.Generator(device="cpu").manual_seed(seed)
    ra, rb = torch.randn(n, generator=generator), torch.randn(d.numel(), generator=generator)
    ar, br = torch.zeros_like(a), torch.zeros_like(b)
    ar[0] = (ra / ra.norm() * a[0].float().norm()).bfloat16()
    br[:, 0] = (rb / rb.norm() * b[:, 0].float().norm()).bfloat16()
    factors = {
        "wsp2_zero": (a.clone(), torch.zeros_like(b)),
        "wsp2_a": (a, b),
        "wsp2_neg": (a.clone(), -b),
        "wsp2_random": (ar, br),
    }
    norms = {}
    for name, (left, right) in factors.items():
        if torch.count_nonzero(left[1:]).item() or torch.count_nonzero(right[:, 1:]).item():
            raise ValueError("Inactive rank components must remain zero")
        norms[name] = {
            "a_norm": float(left[0].float().norm()),
            "b_norm": float(right[:, 0].float().norm()),
            "delta_frobenius_norm": float(left[0].float().norm() * right[:, 0].float().norm()),
        }
    if norms["wsp2_zero"]["delta_frobenius_norm"] != 0:
        raise ValueError("Zero control has a nonzero effect")
    ref = norms["wsp2_a"]["delta_frobenius_norm"]
    for name in ("wsp2_neg", "wsp2_random"):
        if abs(norms[name]["delta_frobenius_norm"] / ref - 1) > 0.005:
            raise ValueError(f"{name} delta norm is not matched to the edit")
    return {
        "layer": layer,
        "module": f"model.language_model.layers.{layer}.self_attn.o_proj",
        "factors": factors,
        "norms": norms,
        "alpha": alpha,
        "ridge": ridge,
        "denominator": s,
        "realized_relative_error": error,
        "cosine_d_realized": float((realized @ d) / (realized.norm() * d.norm())),
        "key_norm": float(k.norm()),
        "d_norm": float(d.norm()),
        "in_width": n,
        "out_width": d.numel(),
    }


def prepare_v2(capture_path: str, v1_files: dict[str, bytes], template: str, alpha: float) -> dict:
    import torch
    import yaml
    from adk_submission import (
        ModelRegistry,
        ToolRegistry,
        compile_submission,
        discover_adapters,
        validate_directory,
    )
    from google.adk.models.base_llm import BaseLlm
    from safetensors.torch import save_file
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, build_submission_limits
    from swegemma.harness.agent_runner import resolve_swegemma_adapter

    built = build_factors(capture_path, alpha)
    if built["realized_relative_error"] > 0.05:
        raise ValueError("Rounded factors do not reproduce the targeted shift within 5%")
    document = yaml.safe_load(template)
    if not isinstance(document, dict) or document.get("model") != MODEL_ALIAS:
        raise ValueError("Expected the base-model agent template")
    peft = {
        "base_model_name_or_path": str(MODEL_PATH),
        "bias": "none",
        "fan_in_fan_out": False,
        "inference_mode": True,
        "lora_alpha": RANK,
        "lora_dropout": 0.0,
        "peft_type": "LORA",
        "r": RANK,
        "target_modules": ["o_proj"],
        "task_type": "CAUSAL_LM",
        "use_dora": False,
        "use_rslora": False,
    }

    class CompileOnlyModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            raise RuntimeError("Inference is disabled during preparation")
            yield

    with tempfile.TemporaryDirectory(prefix="wsp-v2-prepare-") as directory:
        root = Path(directory)
        prefix = "base_model.model." + built["module"]
        for name, (left, right) in built["factors"].items():
            folder = root / "adapters" / name
            folder.mkdir(parents=True)
            (folder / "adapter_config.json").write_text(json.dumps(peft, indent=2) + "\n")
            save_file(
                {prefix + ".lora_A.weight": left, prefix + ".lora_B.weight": right},
                folder / "adapter_model.safetensors",
                metadata={"format": "pt"},
            )
        for relative, value in v1_files.items():
            if not relative.startswith("adapters/wsp_read/"):
                raise ValueError("Only the preserved v1 wsp_read adapter may be reused")
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        document["adapter"] = "wsp2_a"
        (root / "agent.yaml").write_text(yaml.safe_dump(document))
        limits, generation = build_submission_limits()
        validate_directory(root, limits=limits)
        adapters = discover_adapters(root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
        if set(adapters.adapters) != set(ADAPTER_NAMES):
            raise ValueError("Official discovery disagrees with the adapter aliases")
        models = ModelRegistry()
        for name in (MODEL_ALIAS, *ADAPTER_NAMES):
            models.register(name, CompileOnlyModel(model=name))
        compiled = {}
        for name in ADAPTER_NAMES:
            (root / "agent.yaml").write_text(yaml.safe_dump({**document, "adapter": name}))
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
            compiled[name] = agent.model.model
        (root / "agent.yaml").write_text(yaml.safe_dump({**document, "adapter": "wsp2_a"}))
        files = {name: (root / name).read_bytes() for name in PACKAGE_FILES}
    del torch
    report = {k: v for k, v in built.items() if k != "factors"}
    return {
        "passed": True,
        "files": files,
        "file_sha256": package_hashes(files),
        "package_size_bytes": sum(map(len, files.values())),
        "compiled_adapters": compiled,
        "construction": report,
        "base_modified": False,
        "model_forward_passes": 0,
        "gradient_steps": 0,
    }
