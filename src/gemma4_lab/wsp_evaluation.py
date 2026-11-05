"""Fixed numerical application controls and paired behavioral WSP screening."""

import tempfile
import time
import traceback
from pathlib import Path

from gemma4_lab.adapter_probe import logprob_distance
from gemma4_lab.behavior_inference import _run_case, _seed_preflight, _skipped
from gemma4_lab.remote_serving import MODEL_ALIAS, MODEL_PATH, create_approved_server
from gemma4_lab.wsp_adapter import ADAPTER_NAMES, write_package


def assess_application(cases, settings):
    if [case.get("prompt") for case in cases] != settings["application_prefixes"] or any(
        set(case.get("distributions", {})) != {"base", "zero", "read", "random"}
        or any(len(values) != 2 for values in case["distributions"].values())
        for case in cases
    ):
        return {"passed": False, "reason": "Incomplete numerical application controls"}
    drift, effects = 0.0, {"read": [], "random": []}
    for case in cases:
        d = case["distributions"]
        for name in ("base", "zero", "read", "random"):
            drift = max(drift, logprob_distance(*d[name]))
        for i in (0, 1):
            drift = max(drift, logprob_distance(d["base"][i], d["zero"][i]))
        for name in effects:
            effects[name].append(min(logprob_distance(d[name][i], d["zero"][i]) for i in (0, 1)))
    threshold = max(
        settings["minimum_application_effect_nats"],
        settings["application_effect_to_noise_ratio"] * drift,
    )
    return {
        "passed": drift <= settings["control_tolerance_nats"]
        and all(max(values) > threshold for values in effects.values()),
        "maximum_control_drift_nats": drift,
        "effect_threshold_nats": threshold,
        "effect_lower_bounds_nats": effects,
    }


def assess_screen(rows, cases, settings, application):
    names = {c["name"] for c in settings["conditions"]}
    indexed = {(r["case_id"], r["condition"]): r for r in rows}
    expected = {(c["id"], name) for c in cases for name in names}
    valid = (
        len(rows) == len(expected) == len(indexed)
        and set(indexed) == expected
        and all(
            r.get("started") and r.get("completed") and r.get("valid_for_comparison") for r in rows
        )
    )
    counts = {
        name: {
            "workflow_complete": 0,
            "source_correct": 0,
            "passing_controls": 0,
            "prefix_first_source_read": 0,
            "premature_submissions": 0,
        }
        for name in names
    }
    for r in rows:
        if r["condition"] not in counts:
            continue
        c = counts[r["condition"]]
        c["workflow_complete"] += bool(r.get("workflow_complete"))
        c["source_correct"] += bool(r.get("source_correct"))
        c["passing_controls"] += r["family"] == "passing_control" and bool(
            r.get("workflow_complete")
        )
        c["premature_submissions"] += bool(r.get("premature_submit"))
        first = (r.get("actions") or [{}])[0]
        c["prefix_first_source_read"] += bool(
            r["family"] == "prefix_corruption"
            and first.get("name") == "read_file"
            and first.get("response", {}).get("status") == "ok"
            and first.get("response", {}).get("filepath") == "task.py"
        )
    identity, wins, losses = True, 0, 0
    for case in cases:
        base = indexed.get((case["id"], "base"), {})
        zero = indexed.get((case["id"], "zero"), {})
        read = indexed.get((case["id"], "read"), {})
        identity &= all(
            base.get(k) == zero.get(k) for k in ("actions", "source", "workflow_complete")
        )
        wins += (
            case["family"] == "prefix_corruption"
            and bool(read.get("workflow_complete"))
            and not base.get("workflow_complete")
        )
        losses += bool(base.get("workflow_complete")) and not read.get("workflow_complete")
    gate = settings["screening_gate"]
    advantage = counts["read"]["workflow_complete"] - counts["random"]["workflow_complete"]
    passed = (
        valid
        and application["passed"]
        and identity
        and wins >= gate["minimum_prefix_workflow_wins_over_base"]
        and counts["read"]["prefix_first_source_read"] >= gate["minimum_prefix_first_read_count"]
        and advantage >= gate["minimum_total_workflow_advantage_over_random"]
        and losses <= gate["maximum_workflow_losses_to_base"]
        and counts["read"]["passing_controls"] == gate["required_passing_controls"]
        and counts["read"]["premature_submissions"] <= gate["maximum_premature_submissions"]
    )
    return {
        "gate_passed": passed,
        "valid_coverage": valid,
        "identity_behavior_passed": identity,
        "counts": counts,
        "prefix_workflow_wins_over_base": wins,
        "workflow_losses_to_base": losses,
        "workflow_advantage_over_random": advantage,
    }


def run_screen(files, prepared, settings, prompts, context, cases, execution_limit_seconds):
    import platform
    from importlib.metadata import distributions

    import requests

    from gemma4_lab.adapter_serving_probe import compiled_route

    start, server, rows, token_cases = time.monotonic(), None, [], []
    final = {"stage": "finished", "completed": False, "gate_passed": False}

    def reserve(seconds):
        if execution_limit_seconds - (time.monotonic() - start) < seconds:
            raise TimeoutError("Insufficient remaining execution allocation")

    schedule = [
        (case, condition)
        for i, case in enumerate(cases)
        for condition in (settings["conditions"][i % 5 :] + settings["conditions"][: i % 5])
    ]
    try:
        if len(cases) != 12 or len(settings["conditions"]) != 5:
            raise ValueError("Require twelve cases and five frozen conditions")
        yield _seed_preflight({**settings, "cases": cases}, context)
        with tempfile.TemporaryDirectory(prefix="wsp-intervention-") as directory:
            root = Path(directory)
            write_package(root, files, prepared["file_sha256"])
            server, metadata = create_approved_server(submission_directory=root)
            actual = metadata["checkpoint_manifest"]["files"]
            expected = prepared["base_identity"]["verified_model_sha256"]
            if set(actual) != set(expected) or any(
                actual[n]["sha256"] != h for n, h in expected.items()
            ):
                raise ValueError("Served checkpoint manifest differs from numerical inspection")
            server.start()
            metadata.update(
                python=platform.python_version(),
                packages={d.metadata["Name"]: d.version for d in distributions()},
                server_ready_seconds=time.monotonic() - start,
            )
            yield {"stage": "server-ready", "metadata": metadata}
            response = requests.get(server.base_url + "/models", timeout=10)
            response.raise_for_status()
            ids = {r["id"] for r in response.json()["data"]}
            if not {str(MODEL_PATH), *ADAPTER_NAMES}.issubset(ids):
                raise ValueError("Expected base and all three adapter aliases")
            models = {
                "base": str(MODEL_PATH),
                "zero": "wsp_zero",
                "read": "wsp_read",
                "random": "wsp_random",
            }
            for prompt in settings["application_prefixes"]:
                case = {"prompt": prompt, "distributions": {name: [] for name in models}}
                for condition in settings["application_order"]:
                    reserve(60)
                    response = requests.post(
                        server.base_url + "/completions",
                        json={
                            "model": models[condition],
                            "prompt": prompt,
                            "temperature": 0,
                            "seed": settings["seed"],
                            "max_tokens": 1,
                            "logprobs": 20,
                            "return_tokens_as_token_ids": True,
                        },
                        timeout=30,
                    )
                    response.raise_for_status()
                    body = response.json()
                    case["distributions"][condition].append(
                        body["choices"][0]["logprobs"]["top_logprobs"][0]
                    )
                    yield {
                        "stage": "token-response",
                        "condition": condition,
                        "prompt": prompt,
                        "response": body,
                    }
                token_cases.append(case)
            application = assess_application(token_cases, settings)
            yield {"stage": "application-assessment", "assessment": application}
            registry = server.create_model_registry(
                aliases=[MODEL_ALIAS], model_prefix="openai/", api_key="EMPTY"
            )
            template = (root / "agent.yaml").read_text()
            routes = []
            for name in ADAPTER_NAMES:
                reserve(120)
                import asyncio

                from adk_submission import discover_adapters
                from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS

                adapters = discover_adapters(root, adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)
                route = asyncio.run(
                    compiled_route(
                        root, template, name, adapters, registry, {"routing_timeout_seconds": 90}
                    )
                )
                routes.append(route)
                yield {"stage": "compiled-route", "route": route}
            for case, condition in schedule:
                remaining = execution_limit_seconds - (time.monotonic() - start)
                if remaining < settings["case_timeout_seconds"] + 30:
                    row = _skipped(case, condition["name"], "insufficient_execution_allocation")
                else:
                    model = str(MODEL_PATH) if condition["model"] == "base" else condition["model"]
                    row = _run_case(
                        case,
                        condition["name"],
                        prompts[condition["prompt"]],
                        context,
                        settings,
                        server.base_url,
                        model,
                        requests,
                    )
                rows.append(row)
                yield {"stage": "case", "result": row}
            final.update(
                completed=all(r["started"] and r["completed"] for r in rows),
                application=application,
                routes=routes,
                assessment=assess_screen(rows, cases, settings, application),
            )
            final["gate_passed"] = final["assessment"]["gate_passed"] and all(
                r["passed"] for r in routes
            )
    except Exception as exc:
        final.update(
            error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()
        )
        for case, condition in schedule[len(rows) :]:
            row = _skipped(case, condition["name"], "run_error")
            rows.append(row)
            yield {"stage": "case", "result": row}
    finally:
        if server is not None:
            try:
                log = Path(server.log_path)
                if log.is_file():
                    final["server_log"] = log.read_text(errors="replace")[-150000:]
            except Exception as exc:
                final["log_capture_error"] = str(exc)
            finally:
                try:
                    server.stop()
                except Exception as exc:
                    final["shutdown_error"] = str(exc)
                    final["gate_passed"] = False
    final.update(results=rows, token_cases=token_cases, elapsed_seconds=time.monotonic() - start)
    yield final
