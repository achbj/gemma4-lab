"""Build a private offline Kaggle probe from an immutable prepared package."""

import argparse
import base64
import hashlib
import json
import subprocess
import zlib
from pathlib import Path

from gemma4_lab.adapter_probe import package_hashes
from gemma4_lab.config import PROJECT_ROOT
from gemma4_lab.remote_serving import MODEL_SOURCE

MODULES = (
    "__init__.py",
    "remote_serving.py",
    "adapter_probe.py",
    "adapter_serving_probe.py",
)
OFFICIAL_IMAGE = (
    "gcr.io/kaggle-private-byod/python@sha256:"
    "37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461"
)


def validate_metadata(metadata: dict) -> None:
    expected = {
        "is_private": True,
        "enable_internet": False,
        "enable_gpu": True,
        "enable_tpu": False,
        "competition_sources": ["gemma-4-developer-agent"],
        "dataset_sources": ["metric/gemma-4-developer-agent-wheelhouse"],
        "model_sources": [MODEL_SOURCE],
        "kernel_sources": [],
        "machine_shape": "NvidiaL4",
        "docker_image": OFFICIAL_IMAGE,
        "docker_image_pinning_type": "original",
        "code_file": "run_probe.py",
        "kernel_type": "script",
        "language": "python",
    }
    for key, value in expected.items():
        actual = metadata.get(key, [] if key == "kernel_sources" else None)
        if actual != value or (isinstance(value, bool) and actual is not value):
            raise ValueError(f"Unsafe or changed Kaggle metadata: {key}")
    if not metadata.get("id", "").startswith("bjacharya/"):
        raise ValueError("Kaggle probe must remain in the authorized account")


def encode_bundle(payload: dict) -> tuple[str, str]:
    raw = json.dumps(payload, sort_keys=True).encode()
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Self-contained Kaggle probe exceeds its 2 MiB allocation")
    return base64.b64encode(zlib.compress(raw)).decode(), hashlib.sha256(raw).hexdigest()


def build_probe(root: Path, preparation: Path, destination: Path) -> Path:
    artifacts = (root / "artifacts").resolve()
    preparation = preparation.resolve()
    destination = destination.resolve()
    if not preparation.is_relative_to(artifacts) or not destination.is_relative_to(artifacts):
        raise ValueError("Preparation and generated bundle must be inside artifacts/")
    if destination.exists():
        raise ValueError("Preserve the existing generated bundle")
    prepared = json.loads(preparation.read_text())
    if not prepared.get("passed") or not prepared.get("completed"):
        raise ValueError("Successful CPU preparation is required")
    package = (root / prepared["package_directory"]).resolve()
    if not package.is_relative_to(artifacts) or any(p.is_symlink() for p in package.rglob("*")):
        raise ValueError("Unsafe prepared package directory")
    files = {
        p.relative_to(package).as_posix(): p.read_bytes() for p in package.rglob("*") if p.is_file()
    }
    if package_hashes(files) != prepared["file_sha256"]:
        raise ValueError("Prepared adapter bytes changed")
    preparation_code = root / "src/gemma4_lab/adapter_probe.py"
    if (
        hashlib.sha256(preparation_code.read_bytes()).hexdigest()
        != prepared["preparation_source_sha256"]["src/gemma4_lab/adapter_probe.py"]
    ):
        raise ValueError("Adapter construction code changed after preparation")
    from tomllib import loads

    settings = loads((root / "configs/adapter-probe-v1.toml").read_text())
    if any(prepared["settings"].get(k) != v for k, v in settings.items()):
        raise ValueError("Fixed probe controls changed")
    infrastructure = root / "infrastructure/kaggle/adapter_probe"
    metadata = json.loads((infrastructure / "kernel-metadata.json").read_text())
    validate_metadata(metadata)
    modules = {
        f"gemma4_lab/{name}": (root / "src/gemma4_lab" / name).read_bytes() for name in MODULES
    }
    provenance = {
        "preparation_report": preparation.relative_to(root).as_posix(),
        "preparation_report_sha256": hashlib.sha256(preparation.read_bytes()).hexdigest(),
        "file_sha256": prepared["file_sha256"],
        "module_sha256": {k: hashlib.sha256(v).hexdigest() for k, v in modules.items()},
        "kernel_metadata_sha256": hashlib.sha256(
            json.dumps(metadata, sort_keys=True).encode()
        ).hexdigest(),
        "requested_image": OFFICIAL_IMAGE,
        "execution_timeout_seconds": 1800,
        "tensor_parallel_size": 4,
    }
    payload = {
        "files": {k: base64.b64encode(v).decode() for k, v in files.items()},
        "modules": {k: base64.b64encode(v).decode() for k, v in modules.items()},
        "prepared": {
            k: prepared[k] for k in ("file_sha256", "checkpoint_manifest", "base_config_sha256")
        },
        "settings": prepared["settings"],
        "wheel_manifest": json.loads(
            (root / "requirements/remote-runtime-wheels.json").read_text()
        ),
        "provenance": provenance,
    }
    encoded, bundle_hash = encode_bundle(payload)
    template = (infrastructure / "run_probe.py").read_text()
    script = f"_PACKED_BUNDLE = {encoded!r}\n_PACKED_BUNDLE_SHA256 = {bundle_hash!r}\n\n" + template
    compile(script, "run_probe.py", "exec")
    destination.mkdir(parents=True)
    (destination / "run_probe.py").write_text(script)
    (destination / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    provenance.update(
        bundle_sha256=bundle_hash,
        generated_script_sha256=hashlib.sha256(script.encode()).hexdigest(),
        entrypoint_template_sha256=hashlib.sha256(template.encode()).hexdigest(),
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
    )
    (destination / "build.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = build_probe(PROJECT_ROOT, args.preparation, args.output)
    print(json.dumps({"bundle": str(output), "uploaded": False}))


if __name__ == "__main__":
    main()
