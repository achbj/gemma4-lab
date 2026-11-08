"""Fresh evaluation cases for weight-space study v4 (pre-registered, disjoint from v1-v3)."""

import hashlib
import json
from pathlib import Path

from gemma4_lab.wsp_v2_cases import FACTORS, OFFSETS, used_pairs

LABEL = "wsp-v4-cases"
ALLOCATION = (
    ("eval", "prefix_corruption", 24),
    ("eval", "failing_assertion", 6),
    ("eval", "passing_control", 6),
)


def earlier_pairs(config_dir: Path) -> set[tuple[int, int]]:
    pairs = set()
    for name in ("wsp-v2-cases.json", "wsp-v3-cases.json"):
        for c in json.loads((config_dir / name).read_text())["cases"]:
            pairs.add((c["factor"], c["offset"]))
    return pairs


def _rank(pair: tuple[int, int]) -> str:
    return hashlib.sha256(f"{LABEL}:{pair[0]}:{pair[1]}".encode()).hexdigest()


def generate(used: set[tuple[int, int]]) -> dict:
    available = sorted(((f, o) for f in FACTORS for o in OFFSETS if (f, o) not in used), key=_rank)
    if len(available) < sum(count for *_, count in ALLOCATION):
        raise ValueError("Not enough unused coefficient pairs")
    cursor, cases = 0, []
    for role, family, count in ALLOCATION:
        for index in range(1, count + 1):
            factor, offset = available[cursor]
            cursor += 1
            cases.append(
                {
                    "id": f"v4-{role}-{family.split('_')[0]}-{index:02d}",
                    "role": role,
                    "family": family,
                    "factor": factor,
                    "offset": offset,
                }
            )
    return {"version": 1, "name": "wsp-v4-cases", "label": LABEL, "cases": cases}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    config_dir = root / "configs"
    document = generate(used_pairs(config_dir) | earlier_pairs(config_dir))
    destination = config_dir / "wsp-v4-cases.json"
    if destination.exists():
        raise FileExistsError("Frozen case file already exists; amend with a new name")
    destination.write_text(json.dumps(document, indent=1) + "\n")
    print(hashlib.sha256(destination.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
