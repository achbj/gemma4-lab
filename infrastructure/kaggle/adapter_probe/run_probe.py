"""Remote entrypoint template; build the self-contained script with kaggle_probe."""

import base64
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import traceback
import zlib
from pathlib import Path

TIMEOUT_SECONDS = 1800


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def digest(path, deadline):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            if time.monotonic() > deadline:
                raise TimeoutError("Checkpoint/wheel verification exceeded execution allocation")
            result.update(chunk)
    return result.hexdigest()


def install_wheels(manifest, work, deadline):
    candidates = (
        Path("/kaggle/input/datasets/metric/gemma-4-developer-agent-wheelhouse"),
        Path("/kaggle/input/gemma-4-developer-agent-wheelhouse"),
    )
    wheelhouse = next((p for p in candidates if p.is_dir()), None)
    if wheelhouse is None:
        raise FileNotFoundError("Official wheelhouse is not attached")
    available = {}
    for path in wheelhouse.glob("*.whl"):
        name = path.name
        if "cu128" in name and "+" not in name:
            name = name.replace("cu128", "+cu128")
        if name in available:
            raise ValueError("Duplicate normalized official wheel name")
        available[name] = path
    restored = work / "verified-wheels"
    restored.mkdir()
    for item in manifest["wheels"]:
        path = available[item["name"]]
        if path.stat().st_size != item["size_bytes"] or digest(path, deadline) != item["sha256"]:
            raise ValueError(f"Official wheel changed: {path.name}")
        (restored / item["name"]).symlink_to(path)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            "-q",
            *map(str, sorted(restored.glob("*.whl"))),
        ],
        check=True,
        timeout=min(300, max(1, int(deadline - time.monotonic()))),
    )


def checkpoint_view(prepared, work, deadline):
    config_hash = prepared["base_config_sha256"]
    roots = [Path("/kaggle/input/models"), Path("/kaggle/input/gemma-4")]
    roots.extend(p for p in Path("/kaggle/input").iterdir() if p.name.startswith("gemma-4-e4b"))
    matches = set()
    for root in roots:
        if root.is_dir():
            for config in root.rglob("config.json"):
                if digest(config, deadline) == config_hash:
                    matches.add(config.parent.resolve())
    if len(matches) != 1:
        raise ValueError("Expected exactly one attached approved checkpoint config")
    model = matches.pop()
    view = work / "approved-model"
    view.mkdir()
    verified = {}
    for name, expected in prepared["checkpoint_manifest"]["files"].items():
        if Path(name).name != name:
            raise ValueError("Unexpected nested checkpoint file")
        path = model / name
        if (
            path.stat().st_size != expected["size_bytes"]
            or digest(path, deadline) != expected["sha256"]
        ):
            raise ValueError(f"Attached checkpoint file changed: {name}")
        verified[name] = expected
        (view / name).symlink_to(path)
    (view / "source-manifest.json").write_text(json.dumps(prepared["checkpoint_manifest"]))
    return view, {"attached_directory": str(model), "verified_files": verified}


def main(encoded, expected_hash):
    started = time.monotonic()
    deadline = started + TIMEOUT_SECONDS
    work = Path("/kaggle/working/adapter-probe")
    work.mkdir(exist_ok=True)
    output = work / "kaggle-gpu.json"
    report = {"completed": False, "passed": False, "events": [], "python": sys.version}
    save(output, report)

    def timeout_handler(signum, frame):
        raise TimeoutError("Kaggle probe exceeded its 1800-second execution limit")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    try:
        raw = zlib.decompress(base64.b64decode(encoded, validate=True))
        if len(raw) > 2 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError("Embedded probe bundle failed integrity checks")
        bundle = json.loads(raw)
        report["bundle_sha256"] = expected_hash
        report["provenance"] = bundle["provenance"]
        os.environ.update(
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
        install_wheels(bundle["wheel_manifest"], work, deadline)
        report["wheel_overlay_completed"] = True
        save(output, report)
        code = work / "code"
        for name, value in bundle["modules"].items():
            path = code / name
            if not path.resolve().is_relative_to(code.resolve()):
                raise ValueError("Embedded code path escapes its root")
            path.parent.mkdir(parents=True, exist_ok=True)
            content = base64.b64decode(value, validate=True)
            if hashlib.sha256(content).hexdigest() != bundle["provenance"]["module_sha256"][name]:
                raise ValueError("Embedded module changed")
            path.write_bytes(content)
        sys.path.insert(0, str(code))
        import torch

        from gemma4_lab.adapter_probe import package_hashes
        from gemma4_lab.adapter_serving_probe import run_probe

        devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
        report["devices"] = devices
        if len(devices) != 4 or any("L4" not in name for name in devices):
            raise ValueError("Official validation requires exactly four L4 devices")
        files = {
            name: base64.b64decode(value, validate=True) for name, value in bundle["files"].items()
        }
        prepared = bundle["prepared"]
        if package_hashes(files) != prepared["file_sha256"]:
            raise ValueError("Diagnostic adapter package changed")
        view, verification = checkpoint_view(prepared, work, deadline)
        report["checkpoint_verification"] = verification
        save(output, report)
        remaining = int(deadline - time.monotonic()) - 30
        if remaining < 300:
            raise TimeoutError("Insufficient execution allocation after preparation")
        for event in run_probe(
            files, prepared, bundle["settings"], remaining, model_path=view, tensor_parallel_size=4
        ):
            report["events"].append(event)
            if event["stage"] == "finished":
                report.update(completed=event["completed"], passed=event["passed"])
            save(output, report)
            print(
                json.dumps(
                    {k: event[k] for k in ("stage", "prefix_index", "condition") if k in event}
                ),
                flush=True,
            )
    except Exception as exc:
        report.update(
            passed=False,
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
        )
    finally:
        signal.alarm(0)
        report["elapsed_seconds"] = time.monotonic() - started
        save(output, report)
        print(json.dumps({"passed": report["passed"], "report": str(output)}), flush=True)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main(globals()["_PACKED_BUNDLE"], globals()["_PACKED_BUNDLE_SHA256"])
