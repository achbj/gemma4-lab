"""Skill-script probe: can a submitted script see and parse the task repository?

Standard library only. Read-only. Prints one short JSON object.
"""

import ast
import json
import os
import resource
import sys
import time


def find_workspace():
    """Return the first candidate directory that looks like the task checkout."""
    candidates = ["/workspace", os.environ.get("PWD", "")] + list(sys.path)
    for candidate in candidates:
        if candidate and os.path.isdir(os.path.join(candidate, ".git")):
            return candidate
    return None


def main():
    report = {
        "python": sys.version.split()[0],
        "cwd": os.getcwd(),
        "pwd_env": os.environ.get("PWD"),
        "sys_path0": sys.path[0] if sys.path else None,
        "workspace": find_workspace(),
    }
    root = report["workspace"]
    if root:
        started = time.perf_counter()
        files = parsed = failed = definitions = 0
        for directory, subdirectories, names in os.walk(root):
            subdirectories[:] = [d for d in subdirectories if not d.startswith(".")]
            for name in names:
                if not name.endswith(".py"):
                    continue
                files += 1
                try:
                    with open(os.path.join(directory, name), encoding="utf-8") as handle:
                        tree = ast.parse(handle.read())
                except (SyntaxError, UnicodeDecodeError, OSError):
                    failed += 1
                    continue
                parsed += 1
                definitions += sum(
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    for node in ast.walk(tree)
                )
        report.update(
            py_files=files,
            parsed=parsed,
            parse_failures=failed,
            definitions=definitions,
            parse_seconds=round(time.perf_counter() - started, 3),
        )
    report["max_rss_kb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print("REPO_PROBE " + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
