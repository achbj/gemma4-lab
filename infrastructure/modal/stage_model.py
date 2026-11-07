"""Cache the exact approved checkpoint on CPU, without loading its tensors.

Only a short-lived URL for this specific model is passed to the private Modal
function. The user's Kaggle credentials are not uploaded or written to logs.
"""

import json
import os
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parents[2] if modal.is_local() else Path("/")
MODEL = "google/gemma-4/Other/gemma-4-e4b-it-qat-w4a16-ct/2"
VOLUME_NAME = "gemma4-competition-model-cache"
image = modal.Image.debian_slim(python_version="3.12").uv_pip_install("requests==2.34.2")
app = modal.App("gemma4-stage-approved-model")
volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True)


@app.function(
    image=image,
    cpu=2,
    memory=2048,
    timeout=900,
    startup_timeout=60,
    max_containers=1,
    min_containers=0,
    scaledown_window=2,
    retries=0,
    volumes={"/cache": volume},
)
def stage_model(download_url: str, expected_files: dict[str, int]) -> dict:
    import hashlib
    import shutil
    import tarfile
    import time
    import uuid
    from pathlib import PurePosixPath

    import requests

    if len(expected_files) > 30 or sum(expected_files.values()) > 14 * 1024**3:
        raise ValueError("Checkpoint metadata exceeds the staging allocation")
    final = Path("/cache/models/e4b-v2")
    if final.exists():
        manifest = json.loads((final / "source-manifest.json").read_text())
        if manifest["model"] != MODEL or any(
            not (final / name).is_file() or (final / name).stat().st_size != size
            for name, size in expected_files.items()
        ):
            raise ValueError("Existing checkpoint cache is incomplete or mismatched")
        return {"cached": True, "model": MODEL, "bytes": sum(expected_files.values())}

    started = time.monotonic()
    temporary = final.parent / (".e4b-v2-" + uuid.uuid4().hex)
    temporary.mkdir(parents=True)
    records = {}
    try:
        try:
            response = requests.get(download_url, stream=True, timeout=(20, 90))
            response.raise_for_status()
        except requests.RequestException:
            raise RuntimeError("Checkpoint download failed; signed URL omitted") from None
        with response, tarfile.open(fileobj=response.raw, mode="r|gz") as archive:
            for member in archive:
                if member.isdir():
                    continue
                name = PurePosixPath(member.name).as_posix()
                if (
                    not member.isfile()
                    or name not in expected_files
                    or name in records
                    or member.size != expected_files[name]
                ):
                    raise ValueError("Unexpected checkpoint archive member")
                destination = temporary / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError("Checkpoint member has no content")
                digest = hashlib.sha256()
                with source, destination.open("wb") as output:
                    while block := source.read(8 * 1024 * 1024):
                        digest.update(block)
                        output.write(block)
                if destination.stat().st_size != member.size:
                    raise ValueError("Incomplete checkpoint archive member")
                records[name] = {"size_bytes": member.size, "sha256": digest.hexdigest()}
        if set(records) != set(expected_files):
            raise ValueError("Checkpoint archive is missing expected files")
        (temporary / "source-manifest.json").write_text(
            json.dumps({"model": MODEL, "files": records}, indent=2) + "\n"
        )
        temporary.rename(final)
        volume.commit()
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {
        "cached": False,
        "model": MODEL,
        "bytes": sum(expected_files.values()),
        "staging_seconds": time.monotonic() - started,
        "tensor_runtime_loaded": False,
    }


@app.local_entrypoint()
def main():
    if os.environ.get("MODAL_PROFILE") != "onepiecification":
        raise ValueError("Run explicitly with MODAL_PROFILE=onepiecification")
    from datetime import UTC, datetime

    from kaggle.api.kaggle_api_extended import (
        ApiDownloadModelInstanceVersionRequest,
        KaggleApi,
        ModelFramework,
    )

    api = KaggleApi()
    api.authenticate()
    inventory = api.model_instance_version_files(MODEL, page_size=200)
    if inventory is None or inventory.next_page_token:
        raise ValueError("Checkpoint inventory is unavailable or unexpectedly paginated")
    expected = {item.name: item.size for item in inventory.files}
    if any(
        Path(name).is_absolute() or ".." in Path(name).parts or type(size) is not int or size < 0
        for name, size in expected.items()
    ):
        raise ValueError("Unsafe checkpoint inventory")
    owner, model, framework, variant, version = MODEL.split("/")
    request = ApiDownloadModelInstanceVersionRequest()
    request.owner_slug = owner
    request.model_slug = model
    request.framework = api.lookup_enum(
        ModelFramework, ModelFramework.MODEL_FRAMEWORK_API, framework
    )
    request.instance_slug = variant
    request.version_number = int(version)
    with api.build_kaggle_client() as client:
        response = client.models.model_api_client.download_model_instance_version(request)
    result = stage_model.remote(response.request.url, expected)
    result["volume"] = VOLUME_NAME
    destination = (
        ROOT
        / "artifacts/runtime-validation"
        / (datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-model-staging.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
