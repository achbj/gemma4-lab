"""Check the algebraic construction without importing a local tensor runtime."""

import math
import unittest

from gemma4_lab.weight_program import gate_directions


class DirectionTests(unittest.TestCase):
    def test_success_prototype_is_orthogonal_and_error_response_positive(self):
        r = gate_directions([1, 2, 1], [1, 0, 0], [1, 2], [0, 1], [2, -1], [1, 3])
        self.assertTrue(r["passed"])
        self.assertAlmostEqual(r["success_response"], 0)
        self.assertGreater(r["error_response"], 0)
        self.assertAlmostEqual(sum(x * x for x in r["a"]), 1)
        self.assertAlmostEqual(sum(x * x for x in r["b"]), 1)
        self.assertGreater(r["b"][0], 0)
        self.assertLess(r["b"][1], 0)

    def test_collinear_or_nonfinite_prototypes_cannot_pass(self):
        self.assertFalse(gate_directions([1, 0], [2, 0], [1], [0], [1], [1])["passed"])
        with self.assertRaises(ValueError):
            gate_directions([math.nan, 0], [1, 0], [1], [0], [1], [1])
        with self.assertRaises(ValueError):
            gate_directions([1, 0], [0, 1], [0], [0], [1], [1])

    def test_mismatched_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            gate_directions([1, 0], [0, 1], [1, 2], [0], [1, 1], [1, 1])
