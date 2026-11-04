"""Prepare an E4B reference submission from the untouched official starter."""

import re
import shutil
from pathlib import Path

MODEL_LINE = re.compile(r"^([ \t]*)model:[^\n]*$", re.MULTILINE)
ADAPTER_LINE = re.compile(r"^[ \t]*adapter:[^\n]*\n?", re.MULTILINE)
E4B_MODEL = "gemma-4-e4b-it-qat-w4a16-ct"


def prepare_baseline(source: Path, destination: Path) -> int:
    """Copy starter text, remove 31B adapter references, and select E4B.

    Sampling, prompts, and task budgets are preserved. Refusing to overwrite an
    existing candidate prevents an accidental reset of an experiment.
    """
    if destination.exists():
        raise ValueError(f"Submission already exists: {destination}")
    if not (source / "agent.yaml").is_file():
        raise ValueError("Official starter agent.yaml is missing; fetch assets first")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("The source submission must not contain symlinks")
    model_files = {}
    for path in sorted(source.rglob("*")):
        if path.suffix not in {".yaml", ".yml"} or "adapters" in path.relative_to(source).parts:
            continue
        text = path.read_text(encoding="utf-8")
        if MODEL_LINE.search(text):
            text = MODEL_LINE.sub(rf"\g<1>model: {E4B_MODEL}", text)
            model_files[path.relative_to(source)] = ADAPTER_LINE.sub("", text)
    if Path("agent.yaml") not in model_files:
        raise ValueError("Starter root agent has no explicit model declaration")
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("adapters"))
    for relative, text in model_files.items():
        (destination / relative).write_text(text, encoding="utf-8")
    return len(model_files)
