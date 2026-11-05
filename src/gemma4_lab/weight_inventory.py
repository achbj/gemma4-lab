"""Transport checkpoint structure without reading or interpreting tensor payloads."""

import hashlib
import json
import os
from collections import Counter
from pathlib import Path

MAX_HEADER_BYTES = 16 * 1024 * 1024
MAX_METADATA_BYTES = 4 * 1024 * 1024


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _metadata_bytes(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_METADATA_BYTES + 1)
    if len(raw) > MAX_METADATA_BYTES:
        raise ValueError("JSON metadata exceeds the bounded allocation")
    return raw


def read_safetensors_header(path: Path, *, max_header_bytes=MAX_HEADER_BYTES) -> dict:
    """Read exactly the length prefix and JSON header; offsets are payload-relative."""
    with path.open("rb", buffering=0) as stream:
        file_size = os.fstat(stream.fileno()).st_size
        prefix = stream.read(8)
        if len(prefix) != 8:
            raise ValueError("Truncated safetensors length prefix")
        size = int.from_bytes(prefix, "little")
        if not 2 <= size <= max_header_bytes or size > file_size - 8:
            raise ValueError("Safetensors header length is outside file/allocation bounds")
        raw = stream.read(size)
    if len(raw) != size or not raw.startswith(b"{"):
        raise ValueError("Invalid or truncated safetensors JSON header")
    header = json.loads(raw, object_pairs_hook=_object)
    tensors, intervals = {}, []
    payload_size = file_size - 8 - size
    for name, item in header.items():
        if name == "__metadata__":
            if not isinstance(item, dict) or any(not isinstance(v, str) for v in item.values()):
                raise ValueError("Safetensors metadata must contain strings only")
            continue
        if not isinstance(item, dict) or set(item) != {"dtype", "shape", "data_offsets"}:
            raise ValueError("Invalid tensor metadata fields")
        dtype, shape, offsets = item["dtype"], item["shape"], item["data_offsets"]
        if not isinstance(dtype, str) or not dtype:
            raise ValueError("Tensor dtype must be a nonempty string")
        if not isinstance(shape, list) or any(
            type(n) is not int or not 0 <= n < 2**64 for n in shape
        ):
            raise ValueError("Tensor dimensions must be nonnegative unsigned integers")
        if (
            not isinstance(offsets, list)
            or len(offsets) != 2
            or any(type(n) is not int for n in offsets)
            or not 0 <= offsets[0] <= offsets[1] <= payload_size
        ):
            raise ValueError("Tensor offsets are outside payload bounds")
        tensors[name] = item
        intervals.append(tuple(offsets))
    cursor = 0
    for start, end in sorted(intervals):
        if start != cursor:
            raise ValueError("Tensor offsets overlap or leave unindexed bytes")
        cursor = end
    if cursor != payload_size:
        raise ValueError("Tensor offsets do not cover the declared file payload")
    return {
        "file_size_bytes": file_size,
        "header_size_bytes": size,
        "data_start": 8 + size,
        "header_sha256": hashlib.sha256(raw).hexdigest(),
        "tensor_count": len(tensors),
        "dtype_counts": dict(Counter(item["dtype"] for item in tensors.values())),
        "tensors": tensors,
        "tensor_payload_read": False,
    }


def inventory_checkpoint(model_dir: Path, expected_model: str) -> dict:
    """Verify staging metadata and inventory the single checkpoint's header only."""
    source = json.loads(
        _metadata_bytes(model_dir / "source-manifest.json"), object_pairs_hook=_object
    )
    if not isinstance(expected_model, str) or not expected_model:
        raise ValueError("Expected model must be a nonempty source identifier")
    if not isinstance(source, dict) or source.get("model") != expected_model:
        raise ValueError("Checkpoint source differs from the expected model")
    records = source.get("files", {})
    if not isinstance(records, dict):
        raise ValueError("Invalid checkpoint file manifest")
    config_raw = _metadata_bytes(model_dir / "config.json")
    config_hash = hashlib.sha256(config_raw).hexdigest()
    record = records.get("config.json", {})
    if (
        not isinstance(record, dict)
        or record.get("sha256") != config_hash
        or record.get("size_bytes") != len(config_raw)
    ):
        raise ValueError("Config differs from its staging size/SHA-256")
    config = json.loads(config_raw, object_pairs_hook=_object)
    if not isinstance(config, dict):
        raise ValueError("Config must be a JSON object")
    checkpoints = list(model_dir.glob("*.safetensors"))
    declared = [name for name in records if name.endswith(".safetensors")]
    if len(checkpoints) != 1 or declared != [checkpoints[0].name]:
        raise ValueError("Expected exactly the staged single safetensors checkpoint")
    checkpoint = checkpoints[0]
    if (
        not isinstance(records[checkpoint.name], dict)
        or records[checkpoint.name].get("size_bytes") != checkpoint.stat().st_size
    ):
        raise ValueError("Checkpoint size differs from staging")
    return {
        "model": expected_model,
        "config_sha256": config_hash,
        "config": config,
        "checkpoint_name": checkpoint.name,
        "checkpoint": read_safetensors_header(checkpoint),
        "checkpoint_payload_sha256_verified": False,
    }
