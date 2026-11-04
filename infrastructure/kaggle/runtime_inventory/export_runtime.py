"""Export the starter image's packages before and after its official wheel overlay."""

import json
import os
import subprocess
import sys
from importlib.metadata import distributions
from pathlib import Path


def snapshot() -> dict[str, str]:
    return {distribution.metadata["Name"]: distribution.version for distribution in distributions()}


before = snapshot()
wheelhouse = Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse")
if not wheelhouse.is_dir():
    raise FileNotFoundError("Official wheelhouse is not attached")
restored = Path("/tmp/official-wheelhouse")
restored.mkdir(exist_ok=True)
for wheel in wheelhouse.glob("*.whl"):
    if "cutlass" in wheel.name.lower():
        continue
    name = wheel.name
    if "cu128" in name and "+" not in name:
        name = name.replace("cu128", "+cu128")
    target = restored / name
    if not target.exists():
        os.symlink(wheel, target)
subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--force-reinstall",
        "-q",
        *map(str, sorted(restored.glob("*.whl"))),
    ],
    check=True,
)
result = {"python": sys.version, "before": before, "after": snapshot()}
Path("/kaggle/working/runtime-inventory.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"python": sys.version, "packages": len(result["after"])}))
