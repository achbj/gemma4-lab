"""Remote-only entry points around the unchanged official SWE evaluation harness.

Heavy imports stay inside the function; importing this module does not load ML.
Task answers stay in host memory and are never written into the agent workspace.
"""

import asyncio
import json
import time
from pathlib import Path


def evaluate_reference_task(task_payload: dict, models, *, controls_only: bool = False) -> dict:
    import yaml
    from adk_submission import validate_directory
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from swegemma.config import EvalConfig, build_submission_limits
    from swegemma.evaluate import Evaluator
    from swegemma.harness.verification import verify_task
    from swegemma.models import Task

    task = Task(**task_payload)
    fixture_root = Path("/fixtures") / task.instance_id
    settings = yaml.safe_load(Path("/submission/eval_config.yaml").read_text())["evaluation"]
    limits, generation = build_submission_limits()
    validate_directory("/submission", limits=limits)
    results_dir = Path("/runs") / task.instance_id
    results_dir.mkdir(parents=True, exist_ok=True)
    config = EvalConfig(
        # evaluate_task accepts the task in memory; no answers file is mounted.
        tasks_path=fixture_root / "not-mounted-tasks.jsonl",
        snapshots_dir=fixture_root / "snapshots",
        results_dir=results_dir,
        submission_dir=Path("/submission"),
        models=models,
        sandbox="subprocess",
        wheels_dir=fixture_root / "wheels",
        graph_dir=str(fixture_root / "graphs"),
        embeddings_dir=str(fixture_root / "embeddings"),
        verification_timeout_seconds=300,
        limits=limits,
        generation_constraints=generation,
        context_cache_config=ContextCacheConfig(
            min_tokens=2048, ttl_seconds=1800, cache_intervals=10
        ),
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=15,
            overlap_size=2,
            token_threshold=14336,
            event_retention_size=5,
        ),
        display_mode="quiet",
        **settings,
    )
    evaluator = Evaluator(config)
    configure_workspace_imports(evaluator.docker)

    async def run():
        if not controls_only:
            result = await evaluator.evaluate_task(task)
            return {"agent": result.model_dump(mode="json", exclude={"trace"})}
        # Separate sandboxes and a separate CPU invocation: neither control is
        # an agent input, and reference edits never enter a GPU agent container.
        controls = {}
        for name, patch in (("unchanged", ""), ("reference", task.patch)):
            result = await verify_task(
                evaluator.docker,
                config,
                task,
                config.snapshots_dir / f"{task.instance_id}.tgz",
                agent_patch=patch,
                start_time=time.perf_counter(),
            )
            controls[name] = result.model_dump(mode="json", exclude={"trace"})
        return controls

    try:
        results = asyncio.run(run())
    finally:
        evaluator.docker.cleanup_all()
    artifacts = {}
    total = 0
    for path in sorted(results_dir.rglob("*")):
        if path.is_file():
            total += path.stat().st_size
            if total > 10 * 1024 * 1024:
                raise ValueError("Evaluation artifacts exceed the 10 MiB return allocation")
            artifacts[path.relative_to(results_dir).as_posix()] = path.read_text()
    return {
        "task_id": task.instance_id,
        "evaluation_settings": settings,
        "verification_timeout_seconds": 300,
        "controls_only": controls_only,
        "runtime_adaptation": "per-sandbox workspace/src import path; see baseline.md",
        "results": results,
        "artifacts": artifacts,
        "submission_sha256": submission_hashes(),
    }


def configure_workspace_imports(manager) -> None:
    """Restore checkout imports skipped by the official subprocess backend.

    The official wheel is untouched. Its original start()/start_async() lifecycle
    still creates the venv; only that venv receives the workspace-path .pth file.
    This is a documented development adaptation, not official scorer parity.
    """
    original_start = manager.start

    def start_workspace_sandbox():
        sandbox_id = original_start()
        paths = manager.sandboxes[sandbox_id]
        workspace = paths["workspace"].resolve()
        for site_packages in paths["venv"].glob("lib/python*/site-packages"):
            # .pth files are processed after the host site-packages path. Put
            # the checkout first to avoid an already installed package winning.
            content = (
                "import sys; "
                f"sys.path.insert(0, {str(workspace)!r}); "
                f"sys.path.insert(0, {str(workspace / 'src')!r})\n"
            )
            (site_packages / "workspace_paths.pth").write_text(content)
        return sandbox_id

    manager.start = start_workspace_sandbox


def submission_hashes() -> dict[str, str]:
    import hashlib

    root = Path("/submission")
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def fixture_identity(root: Path, manifest: dict) -> str:
    """Verify exact fixture membership and content before a remote mount."""
    from gemma4_lab.assets import safe_destination, sha256

    expected = {item["name"] for item in manifest["files"]}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("Fixture directory contains missing or unexpected files")
    for item in manifest["files"]:
        path = safe_destination(root, item["name"])
        if path.stat().st_size != item["size_bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"Fixture checksum mismatch: {item['name']}")
    import hashlib

    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
