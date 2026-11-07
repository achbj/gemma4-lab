"""Seeded, disjoint case sets for weight-space study v2 (pre-registered).

Coefficients are ranked by SHA-256 of a fixed label and allocated without
replacement, so the design set, evaluation panel and every earlier screen
share no (factor, offset) pair.
"""

import hashlib
import json
from pathlib import Path

LABEL = "wsp-v2-cases"
FACTORS = [f for f in range(-7, 8) if abs(f) >= 2]
OFFSETS = [o for o in range(-9, 10) if o != 0]
# (role, family, count), allocated in this order from one ranked list.
ALLOCATION = (
    ("eval", "prefix_corruption", 24),
    ("design", "prefix_corruption", 12),
    ("eval", "failing_assertion", 6),
    ("design", "failing_assertion", 6),
    ("eval", "passing_control", 6),
    ("design", "passing_control", 6),
)
PRIOR_CONFIGS = ("behavior-diagnostic-v1.json", "behavior-diagnostic-v2.json")


def used_pairs(config_dir: Path) -> set[tuple[int, int]]:
    pairs = set()
    for name in PRIOR_CONFIGS:
        for case in json.loads((config_dir / name).read_text())["cases"]:
            pairs.add((case["factor"], case["offset"]))
    return pairs


def _rank(pair: tuple[int, int]) -> str:
    return hashlib.sha256(f"{LABEL}:{pair[0]}:{pair[1]}".encode()).hexdigest()


def generate(used: set[tuple[int, int]]) -> dict:
    available = sorted(((f, o) for f in FACTORS for o in OFFSETS if (f, o) not in used), key=_rank)
    needed = sum(count for _, _, count in ALLOCATION)
    if len(available) < needed:
        raise ValueError("Not enough unused coefficient pairs")
    cursor, cases = 0, []
    for role, family, count in ALLOCATION:
        for index in range(1, count + 1):
            factor, offset = available[cursor]
            cursor += 1
            cases.append(
                {
                    "id": f"{role}-{family.split('_')[0]}-{index:02d}",
                    "role": role,
                    "family": family,
                    "factor": factor,
                    "offset": offset,
                }
            )
    return {"version": 1, "name": "wsp-v2-cases", "label": LABEL, "cases": cases}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    document = generate(used_pairs(root / "configs"))
    destination = root / "configs/wsp-v2-cases.json"
    if destination.exists():
        raise FileExistsError("Frozen case file already exists; amend with a new name")
    destination.write_text(json.dumps(document, indent=1) + "\n")
    print(hashlib.sha256(destination.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
