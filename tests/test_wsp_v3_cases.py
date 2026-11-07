import json
import unittest
from collections import Counter
from pathlib import Path

from gemma4_lab.behavior_diagnostics import SeededSession
from gemma4_lab.wsp_v2_cases import used_pairs
from gemma4_lab.wsp_v3_cases import generate, v2_pairs
from tests.test_wsp_v2_cases import exact_edit

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


class WspV3CasesTest(unittest.TestCase):
    def setUp(self):
        self.used = used_pairs(CONFIGS) | v2_pairs(CONFIGS)
        self.document = generate(self.used)

    def test_counts_and_disjointness(self):
        cases = self.document["cases"]
        pairs = [(c["factor"], c["offset"]) for c in cases]
        self.assertEqual(len(cases), 36)
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertFalse(set(pairs) & self.used)
        counts = Counter(c["family"] for c in cases)
        self.assertEqual(counts["prefix_corruption"], 24)
        self.assertEqual(counts["failing_assertion"], 6)
        self.assertEqual(counts["passing_control"], 6)
        self.assertTrue(all(c["role"] == "eval" for c in cases))

    def test_ids_do_not_collide_with_v2(self):
        v2 = {c["id"] for c in json.loads((CONFIGS / "wsp-v2-cases.json").read_text())["cases"]}
        self.assertFalse(v2 & {c["id"] for c in self.document["cases"]})

    def test_seed_preconditions_hold(self):
        for case in self.document["cases"]:
            SeededSession(case, native_edit=exact_edit)

    def test_committed_file_matches_generator(self):
        path = CONFIGS / "wsp-v3-cases.json"
        if path.exists():
            self.assertEqual(json.loads(path.read_text()), self.document)


if __name__ == "__main__":
    unittest.main()
