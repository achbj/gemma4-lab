"""Fetch small official reference assets and record their provenance.

Kaggle is imported only for online commands. Downloaded code and wheels are
treated as data here; nothing is imported or executed from these assets.
"""

import hashlib
import json
import sys
from collections.abc import Callable
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

MAX_BOOTSTRAP_BYTES = 25 * 1024 * 1024
MAX_RUNTIME_BYTES = 1024 * 1024 * 1024
MAX_FIXTURE_BYTES = 128 * 1024 * 1024
HARNESS_PACKAGES = ("adk_eval_core-", "adk_submission-", "swegemma-")


def safe_destination(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or "\\" in name or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe asset path: {name!r}")
    destination = root.joinpath(*relative.parts).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError(f"Asset escapes its destination: {name!r}")
    return destination


def collect_pages(fetch_page: Callable[..., Any], *, size_field: str) -> list[dict[str, Any]]:
    """Read every API page, rejecting repeated cursors instead of looping forever."""
    files = []
    token = None
    seen = set()
    for _ in range(100):
        response = fetch_page(page_token=token, page_size=200)
        if response is None:
            raise ValueError("Kaggle returned no file inventory")
        error = getattr(response, "error_message", None)
        if error:
            raise ValueError(f"Kaggle inventory error: {error}")
        for item in response.files:
            size = getattr(item, size_field)
            if type(size) is not int or size < 0:
                raise ValueError(f"Invalid asset size for {item.name!r}")
            files.append({"name": item.name, "size_bytes": size})
        token = response.next_page_token
        if not token:
            return sorted(files, key=lambda item: item["name"])
        if token in seen:
            raise ValueError("Kaggle returned a repeated pagination cursor")
        seen.add(token)
    raise ValueError("Kaggle inventory exceeded 100 pages")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _kaggle_client() -> Any:
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    return api


def refresh_inventory(root: Path, sources: dict[str, str]) -> dict[str, Any]:
    api = _kaggle_client()
    inventory = {
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "competition": collect_pages(
            lambda **paging: api.competition_list_files(sources["competition"], **paging),
            size_field="total_bytes",
        ),
        "wheelhouse": collect_pages(
            lambda **paging: api.dataset_list_files(sources["wheelhouse"], **paging),
            size_field="total_bytes",
        ),
    }
    write_json(root / "inventory.json", inventory)
    return inventory


def select_bootstrap(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    selected = []
    for item in inventory["competition"]:
        name = item["name"]
        sample_text = (
            name.startswith("sample_submission/")
            and "/adapters/" not in name
            and PurePosixPath(name).suffix in {".yaml", ".yml", ".md", ".py", ".txt"}
        )
        if name in {"HARNESS_README.md", "tasks.jsonl"} or sample_text:
            selected.append({**item, "kind": "competition"})
    for item in inventory["wheelhouse"]:
        if item["name"].startswith(HARNESS_PACKAGES) and item["name"].endswith(".whl"):
            selected.append({**item, "kind": "wheelhouse"})
    required = {"HARNESS_README.md", "tasks.jsonl", "sample_submission/agent.yaml"}
    if not required.issubset({item["name"] for item in selected}):
        raise ValueError("Official inventory is missing required bootstrap files")
    for prefix in HARNESS_PACKAGES:
        if sum(item["name"].startswith(prefix) for item in selected) != 1:
            raise ValueError(f"Expected exactly one official wheel matching {prefix}")
    if any(type(item["size_bytes"]) is not int or item["size_bytes"] < 0 for item in selected):
        raise ValueError("Bootstrap contains an invalid asset size")
    if sum(item["size_bytes"] for item in selected) > MAX_BOOTSTRAP_BYTES:
        raise ValueError("Bootstrap would exceed the 25 MiB download allocation")
    return selected


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_bootstrap(root: Path, sources: dict[str, str], manifest_path: Path) -> dict[str, Any]:
    inventory = read_json(root / "inventory.json")
    if inventory["sources"] != sources:
        raise ValueError("Cached inventory belongs to different sources; refresh it first")
    selected = select_bootstrap(inventory)
    # Check all destination paths before authenticating or downloading anything.
    for item in selected:
        safe_destination(root / item["kind"], item["name"])
    api = _kaggle_client()
    records = []
    for item in selected:
        destination_root = root / item["kind"]
        destination_root.mkdir(parents=True, exist_ok=True)
        destination = safe_destination(destination_root, item["name"])
        # Kaggle prints public URLs even with quiet=True; keep JSON stdout clean.
        with redirect_stdout(sys.stderr):
            if item["kind"] == "competition":
                api.competition_download_file(
                    sources["competition"],
                    item["name"],
                    path=str(destination_root),
                    quiet=True,
                    unzip=True,
                )
            else:
                api.dataset_download_file(
                    sources["wheelhouse"],
                    item["name"],
                    path=str(destination_root),
                    quiet=True,
                    unzip=True,
                )
        if not destination.is_file() or destination.stat().st_size != item["size_bytes"]:
            raise ValueError(f"Downloaded asset does not match inventory: {item['name']}")
        records.append(
            {
                **item,
                "path": destination.relative_to(root.resolve()).as_posix(),
                "sha256": sha256(destination),
            }
        )
    manifest = {
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "files": records,
    }
    write_json(manifest_path, manifest)
    return manifest


def verify_assets(root: Path, manifest_path: Path) -> int:
    manifest = read_json(manifest_path)
    for item in manifest["files"]:
        path = safe_destination(root, item["path"])
        if path.stat().st_size != item["size_bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Asset checksum mismatch: {item['path']}")
    return len(manifest["files"])


def select_runtime_wheels(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """Bound the official Linux wheelhouse acquisition separately from bootstrap."""
    wheels = inventory["wheelhouse"]
    for item in wheels:
        safe_destination(Path("/wheelhouse"), item["name"])
        if not item["name"].endswith(".whl"):
            raise ValueError("Runtime inventory must contain wheels only")
        if type(item["size_bytes"]) is not int or item["size_bytes"] <= 0:
            raise ValueError("Runtime wheel has an invalid size")
    if not wheels or sum(item["size_bytes"] for item in wheels) > MAX_RUNTIME_BYTES:
        raise ValueError("Runtime wheelhouse exceeds the 1 GiB allocation or is empty")
    return wheels


def fetch_runtime_wheels(
    root: Path, sources: dict[str, str], manifest_path: Path
) -> dict[str, Any]:
    inventory = read_json(root / "inventory.json")
    if inventory["sources"] != sources:
        raise ValueError("Cached inventory belongs to different sources; refresh it first")
    selected = select_runtime_wheels(inventory)
    api = _kaggle_client()
    records = []
    for item in selected:
        destination = safe_destination(root / "wheelhouse", item["name"])
        if not destination.is_file() or destination.stat().st_size != item["size_bytes"]:
            with redirect_stdout(sys.stderr):
                api.dataset_download_file(
                    sources["wheelhouse"],
                    item["name"],
                    path=str(root / "wheelhouse"),
                    quiet=True,
                    unzip=True,
                )
        if not destination.is_file() or destination.stat().st_size != item["size_bytes"]:
            raise ValueError(f"Runtime download differs from inventory: {item['name']}")
        records.append({**item, "sha256": sha256(destination)})
    manifest = {"source": sources["wheelhouse"], "wheels": records}
    write_json(manifest_path, manifest)
    return manifest


def select_task_fixture(inventory: dict[str, Any], task: dict[str, Any]) -> list[dict[str, Any]]:
    stem = f"{task['repo'].split('/')[-1]}_{task['base_commit']}"
    required = {
        f"snapshots/{task['instance_id']}.tgz",
        f"graphs/{stem}.json",
        f"embeddings/{stem}.npz",
    }
    selected = [
        item
        for item in inventory["competition"]
        if item["name"] in required or item["name"].startswith("wheels/")
    ]
    if not required.issubset({item["name"] for item in selected}):
        raise ValueError("Task fixture is missing its snapshot, graph, or embeddings")
    for item in selected:
        safe_destination(Path("/fixtures"), item["name"])
    if sum(item["size_bytes"] for item in selected) > MAX_FIXTURE_BYTES:
        raise ValueError("Task fixture exceeds the 128 MiB allocation")
    return selected


def fetch_task_fixture(
    root: Path,
    sources: dict[str, str],
    task_id: str,
    manifest_path: Path,
) -> dict[str, Any]:
    inventory = read_json(root / "inventory.json")
    if inventory["sources"] != sources:
        raise ValueError("Cached inventory belongs to different sources")
    task = next(
        (
            json.loads(line)
            for line in (root / "competition/tasks.jsonl").read_text().splitlines()
            if line.strip() and json.loads(line)["instance_id"] == task_id
        ),
        None,
    )
    if task is None:
        raise ValueError(f"Unknown public task: {task_id}")
    selected = select_task_fixture(inventory, task)
    destination_root = safe_destination(root / "evaluation", task_id)
    records = []
    api = None
    for item in selected:
        path = safe_destination(destination_root, item["name"])
        if not path.is_file() or path.stat().st_size != item["size_bytes"]:
            if api is None:
                api = _kaggle_client()
            with redirect_stdout(sys.stderr):
                api.competition_download_file(
                    sources["competition"],
                    item["name"],
                    path=str(destination_root),
                    quiet=True,
                    unzip=True,
                )
        if not path.is_file() or path.stat().st_size != item["size_bytes"]:
            raise ValueError(f"Task fixture differs from inventory: {item['name']}")
        records.append({**item, "sha256": sha256(path)})
    manifest = {"source": sources["competition"], "task_id": task_id, "files": records}
    write_json(manifest_path, manifest)
    return manifest
