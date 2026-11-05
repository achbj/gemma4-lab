"""Numerical weight inspection and a fixed, untested read-recovery construction."""

import json
import math
from pathlib import Path

from gemma4_lab.assets import sha256
from gemma4_lab.remote_serving import MODEL_SOURCE
from gemma4_lab.weight_inventory import inventory_checkpoint


def gate_directions(error, success, read, edit, post_gain, final_gain, max_cosine=0.95):
    """Algebraic prototype construction, not evidence of a functioning circuit."""

    def dot(a, b):
        return math.fsum(x * y for x, y in zip(a, b, strict=True))

    def unit(vector):
        norm = math.sqrt(dot(vector, vector))
        if not math.isfinite(norm) or norm < 1e-8:
            raise ValueError("Degenerate or nonfinite prototype")
        return [x / norm for x in vector]

    error, success = list(error), list(success)
    if not error or len(error) != len(success) or not read:
        raise ValueError("Mismatched or empty prototype dimensions")
    cosine = dot(unit(error), unit(success))
    if abs(cosine) >= max_cosine:
        return {"passed": False, "reason": "Value prototypes too collinear", "cosine": cosine}
    coefficient = dot(error, success) / dot(success, success)
    a = unit([e - coefficient * s for e, s in zip(error, success, strict=True)])
    b = unit(
        [p * f * (r - e) for r, e, p, f in zip(read, edit, post_gain, final_gain, strict=True)]
    )
    return {
        "passed": True,
        "value_prototype_cosine": cosine,
        "a": a,
        "b": b,
        "error_response": dot(a, error),
        "success_response": dot(a, success),
        "caution": "Prototype consistency only; actual hidden-state selectivity is untested.",
    }


def inspect_numeric(model_dir: Path, settings: dict) -> dict:
    """Read actual tensors on Linux; no full-model forward, gradients or base writes."""
    import torch
    from safetensors import safe_open
    from transformers import AutoTokenizer

    from gemma4_lab.weight_io import decoder_self_test, load_projection, tensor_sha256

    torch.set_num_threads(2)
    decoder = decoder_self_test()
    if not decoder["passed"]:
        raise ValueError("Official decoder failed the independent numerical fixture")
    inventory = inventory_checkpoint(model_dir, MODEL_SOURCE)
    if inventory["checkpoint"]["header_sha256"] != settings["expected_header_sha256"]:
        raise ValueError("Checkpoint header differs from the frozen inventory")
    manifest = json.loads((model_dir / "source-manifest.json").read_text())
    verified = {}
    for name, record in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe staged checkpoint filename")
        path = model_dir / name
        digest = sha256(path)
        if path.stat().st_size != record["size_bytes"] or digest != record["sha256"]:
            raise ValueError(f"Staged model file differs: {name}")
        verified[name] = digest
    config = inventory["config"]
    q = config["quantization_config"]["config_groups"]["group_0"]["weights"]
    if any(
        q[k] != v
        for k, v in {
            "num_bits": 4,
            "symmetric": True,
            "strategy": "group",
            "group_size": 32,
            "actorder": None,
            "type": "int",
            "dynamic": False,
        }.items()
    ):
        raise ValueError("Unexpected quantization scheme")
    text = config["text_config"]
    target, source = settings["target_layer"], settings["kv_source_layer"]
    first_shared = text["num_hidden_layers"] - text["num_kv_shared_layers"]
    previous = text["layer_types"][:first_shared]
    expected_source = len(previous) - 1 - previous[::-1].index(text["layer_types"][target])
    if target != text["num_hidden_layers"] - 1 or source != expected_source:
        raise ValueError("Target/shared-value layer disagrees with pinned architecture")
    if not config["tie_word_embeddings"] or text["layer_types"][target] != "full_attention":
        raise ValueError("The fixed construction requires tied embeddings and full attention")
    width, head = text["hidden_size"], text["global_head_dim"]
    heads, kv_heads = text["num_attention_heads"], text["num_key_value_heads"]
    if heads % kv_heads:
        raise ValueError("Unexpected grouped-query attention dimensions")
    prefix = "model.language_model"
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    with safe_open(model_dir / inventory["checkpoint_name"], framework="pt", device="cpu") as f:
        value, vmeta = load_projection(
            f, f"{prefix}.layers.{source}.self_attn.v_proj", (kv_heads * head, width)
        )
        output, ometa = load_projection(
            f, f"{prefix}.layers.{target}.self_attn.o_proj", (width, heads * head)
        )

        def gain(name):
            t = f.get_tensor(name)
            if list(t.shape) != [width] or not torch.isfinite(t).all():
                raise ValueError(f"Invalid norm gain: {name}")
            return t.float(), {
                "name": name,
                "sha256": tensor_sha256(t),
                "sample": t[:16].float().tolist(),
            }

        input_gain, imeta = gain(f"{prefix}.layers.{source}.input_layernorm.weight")
        post_gain, pmeta = gain(f"{prefix}.layers.{target}.post_attention_layernorm.weight")
        final_gain, fmeta = gain(f"{prefix}.norm.weight")
        scalar = f.get_tensor(f"{prefix}.layers.{target}.layer_scalar")
        scalar_value = scalar.float().item()
        if not math.isfinite(scalar_value) or abs(scalar_value) < 1e-6:
            raise ValueError("Degenerate final layer scalar")
        embedding = f.get_slice(f"{prefix}.embed_tokens.weight")
        labels, raw_embeddings, projected = {}, {}, {}
        eps = text["rms_norm_eps"]
        for label in settings["labels"]:
            ids = tokenizer.encode(label, add_special_tokens=False)
            if not 1 <= len(ids) <= 8 or any(not 0 <= i < text["vocab_size"] for i in ids):
                raise ValueError("Unexpected label tokenization")
            rows = [embedding[i : i + 1].squeeze(0) for i in ids]
            e = torch.stack(rows).float().mean(0)
            x = e / torch.sqrt(e.square().mean() + eps) * input_gain
            v = (value @ x).reshape(kv_heads, head)
            v = v / torch.sqrt(v.square().mean(-1, keepdim=True) + eps)
            v = v.repeat_interleave(heads // kv_heads, dim=0).flatten()
            raw_embeddings[label], projected[label] = e, v
            labels[label] = {
                "token_ids": ids,
                "tokens": tokenizer.convert_ids_to_tokens(ids),
                "embedding_norm": e.norm().item(),
                "value_norm": v.norm().item(),
                "embedding_sample": e[:16].tolist(),
                "value_sample": v[:16].tolist(),
                "row_sha256": [tensor_sha256(row) for row in rows],
            }

        def stats(matrix):
            norms = matrix.norm(dim=0)
            values, indices = norms.topk(8)
            return {
                "shape": list(matrix.shape),
                "frobenius_norm": matrix.norm().item(),
                "mean": matrix.mean().item(),
                "std": matrix.std().item(),
                "minimum": matrix.min().item(),
                "maximum": matrix.max().item(),
                "sample": matrix[:4, :8].tolist(),
                "top_column_indices": indices.tolist(),
                "top_column_norms": values.tolist(),
                "median_column_norm": norms.median().item(),
            }

        geometry = gate_directions(
            projected["error"].tolist(),
            projected["ok"].tolist(),
            raw_embeddings["read_file"].tolist(),
            raw_embeddings["edit_file"].tolist(),
            (post_gain * math.copysign(1, scalar_value)).tolist(),
            final_gain.tolist(),
            settings["maximum_value_cosine"],
        )
        output_stats, value_stats = stats(output), stats(value)
        geometry["proposed_beta"] = settings["relative_frobenius"] * output_stats["frobenius_norm"]
    return {
        "model": MODEL_SOURCE,
        "decoder_self_test": decoder,
        "verified_model_sha256": verified,
        "projection_provenance": [vmeta, ometa],
        "norm_provenance": [imeta, pmeta, fmeta],
        "layer_scalar": {"value": scalar_value, "sha256": tensor_sha256(scalar)},
        "value_projection": value_stats,
        "output_projection": output_stats,
        "labels": labels,
        "geometry": geometry,
        "learned_values_read": True,
        "model_forward_passes": 0,
        "gradient_steps": 0,
        "linear_prototype_projections": len(settings["labels"]),
        "base_modified": False,
        "scope": (
            "Token prototypes projected through learned value weights; "
            "not actual layer-23 activations."
        ),
    }
