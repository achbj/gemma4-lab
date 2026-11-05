"""Check decoder preflight using metadata stubs, without importing native Torch."""

import builtins
import importlib
import types
import unittest
from unittest.mock import patch

from gemma4_lab import weight_io


class HeadersOnly:
    def __init__(self):
        self.headers = {
            "projection.weight_packed": ("I32", [2, 8]),
            "projection.weight_scale": ("BF16", [2, 2]),
            "projection.weight_shape": ("I64", [2]),
        }

    def keys(self):
        return self.headers.keys()

    def get_slice(self, name):
        dtype, shape = self.headers[name]
        return types.SimpleNamespace(get_dtype=lambda: dtype, get_shape=lambda: shape)

    def get_tensor(self, name):
        raise AssertionError("Invalid metadata must fail before any payload read")


class WeightIOTests(unittest.TestCase):
    def setUp(self):
        original = builtins.__import__

        def no_native(name, *args, **kwargs):
            if name.split(".")[0] in {"torch", "compressed_tensors", "safetensors"}:
                raise AssertionError("Local native tensor import attempted")
            return original(name, *args, **kwargs)

        self.guard = patch("builtins.__import__", no_native)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_module_import_is_stdlib_only(self):
        importlib.reload(weight_io)

    def test_invalid_module_shapes_and_size_bounds_fail_without_native_import(self):
        cases = [
            ("", (2, 64), 128),
            (None, (2, 64), 128),
            ("projection", [2, 64], 128),
            ("projection", (True, 64), 128),
            ("projection", (0, 64), 128),
            ("projection", (2, 33), 128),
            ("projection", (2, 64), 127),
            ("projection", (2, 64), True),
        ]
        for module, shape, bound in cases:
            with self.subTest(module=module, shape=shape, bound=bound):
                with self.assertRaises(ValueError):
                    weight_io.load_projection(HeadersOnly(), module, shape, bound)

    def test_missing_or_permuted_asymmetric_companions_fail_before_payload_read(self):
        for suffix in ["weight_g_idx", "weight_zero_point", "weight_global_scale", "bias"]:
            handle = HeadersOnly()
            handle.headers["projection." + suffix] = ("I32", [2])
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                weight_io.load_projection(handle, "projection", (2, 64))
        handle = HeadersOnly()
        del handle.headers["projection.weight_shape"]
        with self.assertRaises(ValueError):
            weight_io.load_projection(handle, "projection", (2, 64))

    def test_wrong_packing_scale_or_original_shape_metadata_fails_before_payload_read(self):
        cases = {
            "weight_packed": [("I64", [2, 8]), ("I32", [8, 2])],
            "weight_scale": [("F32", [2, 2]), ("BF16", [2, 1])],
            "weight_shape": [("I32", [2]), ("I64", [1])],
        }
        for suffix, headers in cases.items():
            for header in headers:
                handle = HeadersOnly()
                handle.headers["projection." + suffix] = header
                with self.subTest(suffix=suffix, header=header), self.assertRaises(ValueError):
                    weight_io.load_projection(handle, "projection", (2, 64))


if __name__ == "__main__":
    unittest.main()
