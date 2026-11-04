"""Validate serving and optionally run one reference E4B repair case.

ML imports occur only inside the remote Linux function. --build-only constructs
the image without allocating a GPU. --task-id requests_7427 --controls-only runs
CPU grader controls; repeat without --controls-only for the bounded agent run.
"""

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import modal

from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_SOURCE

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
RESOURCES = {
    "gpu": "L4",
    "cpu_cores": 2,
    "memory_gib": 16,
    "timeout_seconds": 1800,
    "startup_timeout_seconds": 900,
    "scaledown_seconds": 2,
}
image = None
CONFIG = {}
CANDIDATE = "baseline"
if modal.is_local():
    if os.environ.get("MODAL_PROFILE") != "ach-bj100":
        raise ValueError("Run explicitly with MODAL_PROFILE=ach-bj100")
    from gemma4_lab.config import candidate_directory, estimate_run, load_config

    config_path = (ROOT / os.environ.get("GEMMA4_RUN_CONFIG", "configs/baseline.toml")).resolve()
    if not config_path.is_relative_to(ROOT / "configs"):
        raise ValueError("Run settings must be inside configs/")
    CONFIG = load_config(config_path)
    estimate_run(CONFIG)
    if CONFIG["sources"]["model"] != MODEL_SOURCE:
        raise ValueError("This smoke check is pinned to the approved E4B version 2")
    RESOURCES = CONFIG["modal"]
    CANDIDATE = os.environ.get("GEMMA4_CANDIDATE", "baseline")
    candidate_path = candidate_directory(ROOT, CANDIDATE)
    manifest = json.loads((ROOT / "requirements/remote-runtime-wheels.json").read_text())
    wheel_root = ROOT / "data/raw/official/wheelhouse"
    expected = {item["name"] for item in manifest["wheels"]}
    if {p.name for p in wheel_root.iterdir()} != expected:
        raise ValueError("Wheelhouse contains missing or unexpected files")
    for item in manifest["wheels"]:
        path = wheel_root / item["name"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Official runtime wheel checksum mismatch: {path.name}")
    # CUDA 12.8 wheels match the official vLLM wheel's Torch 2.10.0 requirement.
    image = (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git", "libnuma1", "libgl1", "libglib2.0-0", "build-essential")
        .uv_pip_install(
            "torch==2.10.0",
            "torchaudio==2.10.0",
            "torchvision==0.25.0",
            index_url="https://download.pytorch.org/whl/cu128",
        )
        .add_local_dir(wheel_root, "/opt/wheelhouse", copy=True)
        .add_local_file(
            ROOT / "requirements/remote-runtime-base.txt", "/opt/runtime-base.txt", copy=True
        )
        .uv_pip_install(
            requirements=[str(ROOT / "requirements/remote-runtime-base.txt")],
            extra_options="--no-build-isolation",
        )
        # Match the starter's no-dependency wheel overlay; metadata in the
        # supplied wheels is inconsistent even in the verified reference image.
        .uv_pip_install(
            *[f"/opt/wheelhouse/{name}" for name in sorted(expected)],
            extra_options="--no-deps --reinstall",
        )
        .run_commands(
            "python -c 'import adk_submission, transformers, litellm; "
            'print("runtime imports passed")\''
        )
        .uv_pip_install(requirements=[str(ROOT / "requirements/remote-evaluation-base.txt")])
        .env(
            {
                "TRANSFORMERS_NO_TF": "1",
                "TRANSFORMERS_NO_FLAX": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HF_HUB_OFFLINE": "1",
                "VLLM_NO_USAGE_STATS": "1",
                "VLLM_WORKER_MULTIPROC_METHOD": "spawn",
                "VLLM_ENGINE_READY_TIMEOUT_S": "1200",
                "VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS": "1",
                "NCCL_DEBUG": "WARN",
                "LITELLM_LOCAL_MODEL_COST_MAP": "True",
                "LITELLM_TELEMETRY": "False",
                "LITELLM_LOG": "WARNING",
                "OPENAI_API_KEY": "EMPTY",
                "LOCAL_API_KEY": "EMPTY",
                "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
                "OTEL_SDK_DISABLED": "true",
                "OTEL_PYTHON_DISABLED": "true",
            }
        )
    )
    image = image.add_local_python_source("gemma4_lab").add_local_dir(candidate_path, "/submission")
    if (ROOT / "data/raw/official/evaluation").is_dir():
        from gemma4_lab.remote_evaluation import fixture_identity

        for fixture_dir in (ROOT / "data/raw/official/evaluation").iterdir():
            fixture_manifest = ROOT / f"docs/research/fixtures/{fixture_dir.name}.json"
            if not fixture_dir.is_dir() or not fixture_manifest.is_file():
                raise ValueError("Every mounted fixture must have a recorded manifest")
            fixture_identity(fixture_dir, json.loads(fixture_manifest.read_text()))
        image = image.add_local_dir(ROOT / "data/raw/official/evaluation", "/fixtures")
app = modal.App("gemma4-e4b-serving-smoke")
volume = modal.Volume.from_name("gemma4-competition-model-cache")


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=900,
    startup_timeout=900,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    block_network=True,
)
def validate_fixture(task_payload: dict) -> dict:
    import time
    import traceback
    from importlib.metadata import distributions

    from adk_submission import ModelRegistry

    from gemma4_lab.remote_evaluation import evaluate_reference_task

    started = time.monotonic()
    result = {"stage": "grader-controls", "passed": False, "gpu_allocated": False}
    try:
        result["evaluation"] = evaluate_reference_task(
            task_payload, ModelRegistry(), controls_only=True
        )
        controls = result["evaluation"]["results"]
        result["passed"] = (
            not controls["unchanged"]["resolved"]
            and controls["unchanged"]["test_exit_code"] == 1
            and controls["reference"]["resolved"]
        )
    except Exception as exc:
        result.update(error=str(exc), traceback=traceback.format_exc())
    result["elapsed_seconds"] = time.monotonic() - started
    result["packages"] = {d.metadata["Name"]: d.version for d in distributions()}
    return result


@app.function(
    image=image,
    gpu=RESOURCES["gpu"],
    cpu=RESOURCES["cpu_cores"],
    memory=RESOURCES["memory_gib"] * 1024,
    timeout=RESOURCES["timeout_seconds"],
    startup_timeout=RESOURCES["startup_timeout_seconds"],
    max_containers=1,
    min_containers=0,
    scaledown_window=RESOURCES["scaledown_seconds"],
    retries=0,
    block_network=True,
    volumes={"/cache": volume},
)
def serve_smoke(task_payload: dict | None = None) -> dict:
    import platform
    import time
    import traceback
    from importlib.metadata import distributions

    import requests

    started = time.monotonic()
    server = None
    result = {
        "stage": "serving-smoke",
        "passed": False,
        "model": MODEL_SOURCE,
        "python": platform.python_version(),
        "gpu": None,
        "tensor_parallel_size": 1,
        "max_model_len": 32768,
        "packages": {d.metadata["Name"]: d.version for d in distributions()},
        "software_repair_score_measured": False,
    }
    try:
        from gemma4_lab.remote_serving import create_approved_server

        server, metadata = create_approved_server()
        result.update(metadata)
        server.start()
        result["server_ready_seconds"] = time.monotonic() - started
        print(json.dumps({"stage": "server-ready", "seconds": result["server_ready_seconds"]}))
        available = requests.get(server.base_url + "/models", timeout=10)
        available.raise_for_status()
        served_model = available.json()["data"][0]["id"]
        # A short protocol check, intentionally separate from the reference agent's
        # unchanged sampling settings. No issue or evaluation data is used here.
        payload = {
            "model": served_model,
            "messages": [
                {"role": "user", "content": "Call get_status now to inspect the task budget."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_status",
                        "description": "Inspect remaining task time and tool budget.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "additionalProperties": False,
                        },
                    },
                }
            ],
            "tool_choice": "auto",
            "temperature": 0.2,
            "top_p": 0.95,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        response = requests.post(server.base_url + "/chat/completions", json=payload, timeout=180)
        response.raise_for_status()
        result["request"] = payload
        result["response"] = response.json()
        calls = result["response"]["choices"][0]["message"].get("tool_calls") or []
        if (
            len(calls) == 1
            and calls[0]["function"]["name"] == "get_status"
            and json.loads(calls[0]["function"]["arguments"]) == {}
        ):
            followup = dict(payload)
            followup["messages"] = [
                *payload["messages"],
                result["response"]["choices"][0]["message"],
                {
                    "role": "tool",
                    "tool_call_id": calls[0]["id"],
                    "content": json.dumps(
                        {"status": "ready", "remaining_seconds": 60, "remaining_tool_calls": 9}
                    ),
                },
            ]
            reply = requests.post(server.base_url + "/chat/completions", json=followup, timeout=180)
            reply.raise_for_status()
            result["followup_response"] = reply.json()
            result["synthetic_tool_result"] = True
            final_message = result["followup_response"]["choices"][0]["message"]
            result["passed"] = bool(final_message.get("content")) and not final_message.get(
                "tool_calls"
            )
        result["protocol_passed"] = result["passed"]
        if task_payload is not None:
            # The strict synthetic probe also measures instruction following.
            # An empty or unexpected model answer is a behavioral observation,
            # not a transport failure or a reason to censor the repair attempt.
            # HTTP/schema failures above still abort through the exception path.
            from gemma4_lab.remote_evaluation import evaluate_reference_task

            result["stage"] = "reference-baseline"
            print(
                json.dumps(
                    {
                        "stage": "starting-reference-agent",
                        "task_id": task_payload["instance_id"],
                        "synthetic_probe_passed": result["protocol_passed"],
                    }
                )
            )
            models = server.create_model_registry(
                aliases=[MODEL_ALIAS], model_prefix="openai/", api_key="EMPTY"
            )
            result["evaluation"] = evaluate_reference_task(task_payload, models)
            outcome = result["evaluation"]["results"]["agent"]
            result["software_repair_score_measured"] = outcome["test_exit_code"] in (0, 1)
            result["passed"] = result["software_repair_score_measured"]
    except Exception as exc:
        result["passed"] = False
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["traceback"] = traceback.format_exc()
        if getattr(exc, "output", None):
            result["server_log"] = str(exc.output)[-150000:]
    finally:
        if server is not None:
            if Path(server.log_path).is_file():
                result["server_log"] = Path(server.log_path).read_text(errors="replace")[-150000:]
            # The official stop() removes its temporary log file.
            server.stop()
    result["elapsed_seconds"] = time.monotonic() - started
    return result


@app.function(
    image=image,
    gpu=RESOURCES["gpu"],
    cpu=RESOURCES["cpu_cores"],
    memory=RESOURCES["memory_gib"] * 1024,
    timeout=RESOURCES["timeout_seconds"],
    startup_timeout=RESOURCES["startup_timeout_seconds"],
    max_containers=1,
    min_containers=0,
    scaledown_window=RESOURCES["scaledown_seconds"],
    block_network=True,
    volumes={"/cache": volume},
    is_generator=True,
)
def evaluate_panel(task_payloads: list[dict], execution_limit_seconds: int):
    """Stream a fixed evaluation batch so completed cases survive a later failure."""
    import platform
    import time
    import traceback
    from importlib.metadata import distributions

    import yaml

    from gemma4_lab.remote_evaluation import evaluate_reference_task
    from gemma4_lab.remote_serving import create_approved_server

    started = time.monotonic()
    server = None
    completed = 0
    final = {"stage": "finished", "completed": False}
    try:
        if not 1 <= len(task_payloads) <= 4:
            raise ValueError("The fixed panel permits at most four cases")
        if any(task.get("patch") for task in task_payloads):
            raise ValueError("Reference solutions must be stripped before a GPU panel")
        server, metadata = create_approved_server()
        server.start()
        metadata.update(
            python=platform.python_version(),
            packages={d.metadata["Name"]: d.version for d in distributions()},
            server_ready_seconds=time.monotonic() - started,
        )
        yield {"stage": "server-ready", "metadata": metadata}
        models = server.create_model_registry(
            aliases=[MODEL_ALIAS], model_prefix="openai/", api_key="EMPTY"
        )
        settings = yaml.safe_load(Path("/submission/eval_config.yaml").read_text())["evaluation"]
        case_allowance_seconds = float(settings["max_time_minutes"]) * 60 + 450
        for task in task_payloads:
            # Reserve the configured agent time, 300-second verification,
            # two minutes for setup, and shutdown before beginning another case.
            if execution_limit_seconds - (time.monotonic() - started) < case_allowance_seconds:
                final["stop_reason"] = "Insufficient remaining execution allocation"
                break
            print(
                json.dumps({"stage": "starting-case", "task_id": task["instance_id"]}), flush=True
            )
            evaluation = evaluate_reference_task(task, models)
            outcome = evaluation["results"]["agent"]
            completed += 1
            yield {
                "stage": "case-result",
                "task_id": task["instance_id"],
                "resolved": outcome["resolved"],
                "evaluation": evaluation,
                "elapsed_seconds": time.monotonic() - started,
            }
        final["completed"] = completed == len(task_payloads)
    except Exception as exc:
        final.update(
            error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()
        )
        if getattr(exc, "output", None):
            final["server_log"] = str(exc.output)[-150000:]
    finally:
        if server is not None:
            if Path(server.log_path).is_file():
                final["server_log"] = Path(server.log_path).read_text(errors="replace")[-150000:]
            server.stop()
    final.update(completed_cases=completed, elapsed_seconds=time.monotonic() - started)
    yield final


@app.local_entrypoint()
def main(
    build_only: bool = False,
    task_id: str = "",
    controls_only: bool = False,
    panel: str = "",
):
    if build_only:
        print(json.dumps({"image": image.object_id, "gpu_allocated": False}))
        return
    launched_git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if panel:
        if task_id:
            raise ValueError("Select either --panel or --task-id")
        from gemma4_lab.panels import load_development_panel, run_agent_panel, run_control_panel

        settings = load_development_panel(ROOT, ROOT / panel)
        if controls_only:
            destination = run_control_panel(
                ROOT, settings, validate_fixture, image.object_id, launched_git_commit
            )
        else:
            staging = sorted((ROOT / "artifacts/runtime-validation").glob("*-model-staging.json"))
            if not staging or json.loads(staging[-1].read_text())["model"] != MODEL_SOURCE:
                raise ValueError("Stage the approved checkpoint before allocating a GPU")
            destination = run_agent_panel(
                ROOT,
                settings,
                evaluate_panel,
                image.object_id,
                launched_git_commit,
                CONFIG,
                CANDIDATE,
            )
        report = json.loads(destination.read_text())
        complete = report.get("passed", report["completed"])
        print(json.dumps({"completed": complete, "report": str(destination)}))
        if not complete:
            raise SystemExit(1)
        return
    if controls_only and not task_id:
        raise ValueError("--controls-only requires --task-id")
    task_payload = None
    identity = {}
    report_root = ROOT / "artifacts/runtime-validation"
    suffix = "serving-smoke"
    if task_id:
        if task_id not in {"requests_7505", "requests_7427"}:
            raise ValueError("The initial allocation covers only the recorded Requests fixtures")
        from gemma4_lab.remote_evaluation import fixture_identity

        fixture = json.loads((ROOT / f"docs/research/fixtures/{task_id}.json").read_text())
        task_payload = next(
            task
            for line in (ROOT / "data/raw/official/competition/tasks.jsonl")
            .read_text()
            .splitlines()
            if line.strip() and (task := json.loads(line))["instance_id"] == task_id
        )
        identity = {
            "source_task_sha256": hashlib.sha256(
                json.dumps(task_payload, sort_keys=True).encode()
            ).hexdigest(),
            "fixture_sha256": fixture_identity(
                ROOT / "data/raw/official/evaluation" / task_id, fixture
            ),
        }
        report_root = ROOT / "artifacts/baseline"
        report_root.mkdir(parents=True, exist_ok=True)
        suffix = f"{task_id}-{'controls' if controls_only else 'agent'}"
    if controls_only:
        result = validate_fixture.remote(task_payload)
    else:
        staging = sorted((ROOT / "artifacts/runtime-validation").glob("*-model-staging.json"))
        if not staging or json.loads(staging[-1].read_text())["model"] != MODEL_SOURCE:
            raise ValueError("Stage the approved checkpoint on CPU before allocating a GPU")
        if task_payload is not None:
            controls = sorted(report_root.glob(f"*-{task_id}-controls.json"))
            control = json.loads(controls[-1].read_text()) if controls else {}
            if not control.get("passed") or any(control.get(k) != v for k, v in identity.items()):
                raise ValueError("Matching grader controls must pass before the GPU agent run")
            # The agent invocation never receives the reference solution, even
            # in host task memory. Verification-only tests remain host-side.
            task_payload["patch"] = ""
        result = serve_smoke.remote(task_payload)
    result.update(identity)
    result["run_config"] = CONFIG
    result["candidate"] = CANDIDATE
    result["git_commit"] = launched_git_commit
    result["modal_image_id"] = image.object_id
    destination = report_root / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + f"-{suffix}.json")
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "report": str(destination)}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
