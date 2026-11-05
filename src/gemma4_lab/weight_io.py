"""Bounded CPU decoding through pinned libraries; native imports are remote-only."""

import hashlib


def tensor_sha256(tensor) -> str:
    """Hash contiguous raw tensor bytes, including BF16, without numeric conversion."""
    import torch

    raw = tensor.detach().cpu().contiguous().reshape(-1).view(torch.uint8)
    return hashlib.sha256(raw.numpy().tobytes()).hexdigest()


def _decode(packed, scale, shape):
    import torch
    from compressed_tensors.compressors.pack_quantized.helpers import unpack_from_int32
    from compressed_tensors.quantization import QuantizationArgs
    from compressed_tensors.quantization.lifecycle.forward import dequantize

    args = QuantizationArgs(num_bits=4, type="int", symmetric=True, strategy="group", group_size=32)
    quantized = unpack_from_int32(packed, 4, torch.Size(shape), packed_dim=1)
    return dequantize(quantized, scale.float(), args=args, dtype=torch.float32)


def load_projection(
    weights_safe_open, module: str, expected_shape: tuple[int, int], max_elements=16_777_216
):
    """Decode one symmetric, column-ordered INT4/group-32 projection on CPU."""
    if not isinstance(module, str) or not module or module.strip() != module:
        raise ValueError("Supply a nonempty exact module name")
    if (
        not isinstance(expected_shape, tuple)
        or len(expected_shape) != 2
        or any(type(n) is not int or n <= 0 for n in expected_shape)
        or type(max_elements) is not int
        or max_elements <= 0
    ):
        raise ValueError("Expected shape and element bound must be positive integers")
    rows, columns = expected_shape
    if rows * columns > max_elements or columns % 32:
        raise ValueError("Projection exceeds its element bound or is not group-32 aligned")
    prefix = module + "."
    names = {name[len(prefix) :] for name in weights_safe_open.keys() if name.startswith(prefix)}
    required = {"weight_packed", "weight_scale", "weight_shape"}
    if names != required:
        raise ValueError("Projection companions differ; zero points/permutations are unsupported")
    expected = {
        "weight_packed": ("I32", [rows, (columns + 7) // 8]),
        "weight_scale": ("BF16", [rows, columns // 32]),
        "weight_shape": ("I64", [2]),
    }
    for name, (dtype, shape) in expected.items():
        item = weights_safe_open.get_slice(prefix + name)
        if item.get_dtype() != dtype or list(item.get_shape()) != shape:
            raise ValueError(f"Unexpected dtype/header shape for {name}")

    import torch

    shape = weights_safe_open.get_tensor(prefix + "weight_shape")
    if (
        shape.device.type != "cpu"
        or shape.dtype != torch.int64
        or shape.tolist() != list(expected_shape)
    ):
        raise ValueError("Stored original shape differs from the declared projection")
    packed = weights_safe_open.get_tensor(prefix + "weight_packed")
    scale = weights_safe_open.get_tensor(prefix + "weight_scale")
    for name, tensor, dtype in [
        ("weight_packed", packed, torch.int32),
        ("weight_scale", scale, torch.bfloat16),
    ]:
        if (
            tensor.device.type != "cpu"
            or tensor.dtype != dtype
            or list(tensor.shape) != expected[name][1]
        ):
            raise ValueError(f"Unexpected loaded tensor layout for {name}")
    if not torch.isfinite(scale).all().item() or not (scale > 0).all().item():
        raise ValueError("Projection scales must be finite and positive")
    raw = {"weight_packed": packed, "weight_scale": scale, "weight_shape": shape}
    metadata = {
        "module": module,
        "shape": list(expected_shape),
        "output_dtype": "F32",
        "quantization": {
            "num_bits": 4,
            "symmetric": True,
            "group_size": 32,
            "packed_dim": 1,
            "scale_dtype": "BF16",
            "arithmetic_dtype": "F32",
        },
        "raw_sha256": {name: tensor_sha256(tensor) for name, tensor in raw.items()},
    }
    weight = _decode(packed, scale, expected_shape)
    if (
        weight.dtype != torch.float32
        or list(weight.shape) != list(expected_shape)
        or not torch.isfinite(weight).all().item()
    ):
        raise ValueError("Decoded projection must be finite FP32 with the expected shape")
    return weight, metadata


def decoder_self_test() -> dict:
    """Remote-only independent signed-nibble fixture; no checkpoint is accessed."""
    import tempfile
    from pathlib import Path

    import torch
    from compressed_tensors.compressors.pack_quantized.helpers import (
        pack_to_int32,
        unpack_from_int32,
    )
    from compressed_tensors.quantization import QuantizationArgs
    from compressed_tensors.quantization.lifecycle.forward import dequantize
    from safetensors import safe_open
    from safetensors.torch import save_file

    known = torch.tensor([list(range(-8, 8)) * 4], dtype=torch.int8)
    # 0x76543210 and signed 0xFEDCBA98 encode offset-binary nibbles 0..15.
    packed = torch.tensor([[1_985_229_328, -19_088_744] * 4], dtype=torch.int32)
    scale = torch.tensor([[0.1, 0.3]], dtype=torch.bfloat16)
    expected = known.float() * scale.float().repeat_interleave(32, dim=1)
    with tempfile.TemporaryDirectory(prefix="decoder-self-test-") as directory:
        fixture = str(Path(directory) / "fixture.safetensors")
        save_file(
            {
                "fixture.weight_packed": packed,
                "fixture.weight_scale": scale,
                "fixture.weight_shape": torch.tensor([1, 64], dtype=torch.int64),
            },
            fixture,
        )
        with safe_open(fixture, framework="pt", device="cpu") as reader:
            decoded, _ = load_projection(reader, "fixture", (1, 64), max_elements=64)
    args = QuantizationArgs(num_bits=4, type="int", symmetric=True, strategy="group", group_size=32)
    unpacked = unpack_from_int32(packed, 4, known.shape)
    native_bf16 = dequantize(unpacked, scale, args=args)
    packing_equal = torch.equal(pack_to_int32(known, 4), packed)
    unpacking_equal = torch.equal(unpacked, known)
    max_error = (decoded - expected).abs().max().item()
    bf16_difference = (native_bf16.float() - expected).abs().max().item()
    return {
        "passed": bool(
            packing_equal and unpacking_equal and max_error == 0 and bf16_difference > 0
        ),
        "packing_equal": packing_equal,
        "unpacking_equal": unpacking_equal,
        "max_error": max_error,
        "bf16_vs_fp32_max_abs_difference": bf16_difference,
        "shape": list(known.shape),
        "group_size": 32,
        "module_transport_validated": True,
        "checkpoint_accessed": False,
    }
