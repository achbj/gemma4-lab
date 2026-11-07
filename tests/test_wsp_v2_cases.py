import json
import unittest
from collections import Counter
from pathlib import Path

from gemma4_lab.behavior_diagnostics import SeededSession
from gemma4_lab.wsp_v2_cases import ALLOCATION, generate, used_pairs

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def exact_edit(before, old, new, allow_multiple=False):
    """Offline stand-in for the official exact-match editor."""
    if before.count(old) != 1:
        return {"error_message": "no unique match", "new_content": before}
    return {
        "error_message": None,
        "new_content": before.replace(old, new),
        "occurrences": 1,
        "strategy": "exact",
    }


class WspV2CasesTest(unittest.TestCase):
    def setUp(self):
        self.used = used_pairs(CONFIGS)
        self.document = generate(self.used)

    def test_counts_and_disjointness(self):
        cases = self.document["cases"]
        self.assertEqual(len(cases), sum(count for *_, count in ALLOCATION))
        pairs = [(c["factor"], c["offset"]) for c in cases]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertFalse(set(pairs) & self.used)
        ids = [c["id"] for c in cases]
        self.assertEqual(len(ids), len(set(ids)))
        counts = Counter((c["role"], c["family"]) for c in cases)
        self.assertEqual(counts[("eval", "prefix_corruption")], 24)
        self.assertEqual(counts[("design", "prefix_corruption")], 12)

    def test_deterministic(self):
        self.assertEqual(self.document, generate(self.used))

    def test_seed_preconditions_hold_for_every_case(self):
        for case in self.document["cases"]:
            SeededSession(case, native_edit=exact_edit)

    def test_committed_file_matches_generator(self):
        path = CONFIGS / "wsp-v2-cases.json"
        if path.exists():
            self.assertEqual(json.loads(path.read_text()), self.document)


if __name__ == "__main__":
    unittest.main()
