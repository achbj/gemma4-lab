"""Remote GPU measurements for the fixed synthetic adapter compatibility probe."""

import asyncio
import tempfile
import time
import traceback
from pathlib import Path

from gemma4_lab.adapter_probe import ADAPTER_NAMES, REQUEST_ORDER, assess_effect, write_package
from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_PATH, create_approved_server


async def compiled_route(root, template, name, adapters, models, settings):
    import yaml
    from adk_submission import ToolRegistry, compile_submission
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    from swegemma.config import build_submission_limits
    from swegemma.harness.agent_runner import resolve_swegemma_adapter

    document = yaml.safe_load(template)
    document["adapter"] = name
    (root / "agent.yaml").write_text(yaml.safe_dump(document))
    limits, generation = build_submission_limits()
    agent = compile_submission(
        root,
        tool_registry=ToolRegistry(),
        model_registry=models,
        limits=limits,
        generation_constraints=generation,
        adapter_manifest=adapters,
        adapter_resolver_fn=lambda base, info: resolve_swegemma_adapter(base, info, models),
    )
    resolved = agent.model.model
    if resolved != f"openai/{name}":
        raise ValueError("Compiled agent did not resolve the intended adapter alias")
    runner = InMemoryRunner(agent=agent, app_name="adapter_compatibility_probe")
    texts = []
    count = 0
    async with asyncio.timeout(settings["routing_timeout_seconds"]):
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="synthetic_probe"
        )
        async for event in runner.run_async(
            user_id="synthetic_probe",
            session_id=session.id,
            new_message=types.Content(
                role="user", parts=[types.Part(text="Reply with the word READY.")]
            ),
        ):
            count += 1
            if event.content:
                texts.extend(
                    part.text
                    for part in event.content.parts or []
                    if part.text and not getattr(part, "thought", False)
                )
    text = "\n".join(texts)
    return {
        "adapter": name,
        "resolved_model": resolved,
        "events": count,
        "text": text,
        "passed": bool(text.strip()),
    }


def run_probe(files: dict, prepared: dict, settings: dict, execution_limit_seconds: int):
    import platform
    from importlib.metadata import distributions

    import requests
    from adk_submission import discover_adapters, validate_directory
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, build_submission_limits

    started = time.monotonic()
    server = None
    cases = []
    routes = []
    final = {"stage": "finished", "completed": False, "passed": False}

    def reserve(seconds):
        if execution_limit_seconds - (time.monotonic() - started) < seconds:
            raise TimeoutError("Insufficient remaining probe execution allocation")

    try:
        with tempfile.TemporaryDirectory(prefix="gemma4-adapter-probe-") as directory:
            root = Path(directory)
            write_package(root, files, prepared["file_sha256"])
            template = (root / "agent.yaml").read_text()
            limits, _ = build_submission_limits()
            validate_directory(root, limits=limits)
            adapters = discover_adapters(root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
            if set(adapters.adapters) != set(ADAPTER_NAMES):
                raise ValueError("GPU adapter discovery differs from CPU preparation")
            server, metadata = create_approved_server(submission_directory=root)
            if metadata["checkpoint_manifest"] != prepared["checkpoint_manifest"]:
                raise ValueError("Checkpoint manifest changed after CPU preparation")
            yield {"stage": "package-validated", "adapter_names": sorted(adapters.adapters)}
            server.start()
            metadata.update(
                server_ready_seconds=time.monotonic() - started,
                python=platform.python_version(),
                packages={d.metadata["Name"]: d.version for d in distributions()},
            )
            yield {"stage": "server-ready", "metadata": metadata}
            listing = requests.get(server.base_url + "/models", timeout=10)
            listing.raise_for_status()
            ids = {item["id"] for item in listing.json()["data"]}
            if not {str(MODEL_PATH), *ADAPTER_NAMES}.issubset(ids):
                raise ValueError("Expected base/adapter models are absent from the server")
            for index, prompt in enumerate(settings["prompts"]):
                case = {"prompt": prompt, "distributions": {}}
                for condition in REQUEST_ORDER:
                    reserve(
                        settings["request_timeout_seconds"]
                        + 2 * settings["routing_timeout_seconds"]
                        + 30
                    )
                    name = condition.split("_")[0]
                    model = str(MODEL_PATH) if name == "base" else f"probe_{name}"
                    response = requests.post(
                        server.base_url + "/completions",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "temperature": 0,
                            "seed": settings["seed"],
                            "max_tokens": 1,
                            "logprobs": settings["logprobs"],
                            "return_tokens_as_token_ids": True,
                        },
                        timeout=settings["request_timeout_seconds"],
                    )
                    response.raise_for_status()
                    body = response.json()
                    case["distributions"][condition] = body["choices"][0]["logprobs"][
                        "top_logprobs"
                    ][0]
                    yield {
                        "stage": "token-response",
                        "prefix_index": index,
                        "condition": condition,
                        "response": body,
                    }
                cases.append(case)
                yield {"stage": "prefix-result", "case": case}
            effect = assess_effect(cases, settings)
            yield {"stage": "effect-assessment", "assessment": effect}
            models = server.create_model_registry(
                aliases=[MODEL_ALIAS], model_prefix="openai/", api_key="EMPTY"
            )
            for name in ADAPTER_NAMES:
                reserve(settings["routing_timeout_seconds"] + 30)
                try:
                    route = asyncio.run(
                        compiled_route(root, template, name, adapters, models, settings)
                    )
                except Exception as exc:
                    route = {
                        "adapter": name,
                        "passed": False,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                routes.append(route)
                yield {"stage": "compiled-route", "route": route}
            final.update(
                completed=True, passed=effect["passed"] and all(r["passed"] for r in routes)
            )
    except Exception as exc:
        final.update(
            error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()
        )
    finally:
        if server is not None:
            try:
                server.stop()
            except Exception as exc:
                final.update(passed=False, shutdown_error=str(exc))
            log_path = getattr(server, "log_path", None)
            if log_path and Path(log_path).is_file():
                final["server_log"] = Path(log_path).read_text()[-150000:]
        final.update(elapsed_seconds=time.monotonic() - started, completed_prefixes=len(cases))
    yield final
