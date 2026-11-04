"""Small explicit commands for source acquisition and baseline planning."""

import argparse
import json
import sys
from pathlib import Path

from gemma4_lab.assets import (
    fetch_bootstrap,
    fetch_runtime_wheels,
    fetch_task_fixture,
    refresh_inventory,
    verify_assets,
)
from gemma4_lab.config import PROJECT_ROOT, estimate_run, load_config
from gemma4_lab.submission import prepare_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/baseline.toml")
    parser.add_argument("--task-id", help="Public development task for fetch-task")
    parser.add_argument(
        "command",
        choices=(
            "plan",
            "inventory",
            "fetch",
            "fetch-runtime",
            "fetch-task",
            "verify",
            "prepare-baseline",
        ),
    )
    args = parser.parse_args()
    root = PROJECT_ROOT / "data/raw/official"
    manifest_path = PROJECT_ROOT / "docs/research/official-assets.json"
    try:
        config = load_config(args.config)
        if args.command == "plan":
            result = estimate_run(config)
        elif args.command == "inventory":
            inventory = refresh_inventory(root, config["sources"])
            result = {key: len(inventory[key]) for key in ("competition", "wheelhouse")}
        elif args.command == "fetch":
            manifest = fetch_bootstrap(root, config["sources"], manifest_path)
            result = {
                "downloaded_files": len(manifest["files"]),
                "total_bytes": sum(item["size_bytes"] for item in manifest["files"]),
            }
        elif args.command == "fetch-runtime":
            manifest = fetch_runtime_wheels(
                root, config["sources"], PROJECT_ROOT / "requirements/remote-runtime-wheels.json"
            )
            result = {
                "cached_wheels": len(manifest["wheels"]),
                "total_bytes": sum(item["size_bytes"] for item in manifest["wheels"]),
            }
        elif args.command == "fetch-task":
            if not args.task_id or Path(args.task_id).name != args.task_id:
                raise ValueError("fetch-task requires a safe --task-id")
            verify_assets(root, manifest_path)
            manifest = fetch_task_fixture(
                root,
                config["sources"],
                args.task_id,
                PROJECT_ROOT / "docs/research/fixtures" / f"{args.task_id}.json",
            )
            result = {"task_id": args.task_id, "files": len(manifest["files"])}
        elif args.command == "verify":
            result = {"verified_files": verify_assets(root, manifest_path)}
        else:
            verify_assets(root, manifest_path)
            changed = prepare_baseline(
                root / "competition/sample_submission", PROJECT_ROOT / "submissions/baseline"
            )
            result = {"submission": "submissions/baseline", "agent_models_selected": changed}
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0
