"""Bounded remote inference for synthetic, seeded tool-feedback diagnostics.

Importing this module does not load the native model runtime. Official editing
and serving imports execute only in the remote run or through explicit stubs.
"""

import copy
import json
import platform
import time
import traceback
from importlib.metadata import distributions
from pathlib import Path

from gemma4_lab.behavior_diagnostics import native_edit
from gemma4_lab.remote_serving import create_approved_server

FIXED_LIMITS = {
    "max_actions": 6,
    "case_timeout_seconds": 60,
    "request_timeout_seconds": 30,
    "max_tokens": 1536,
    "temperature": 0,
    "top_p": 0.95,
    "seed": 20261105,
}


def native_calls(message: dict) -> list[tuple[str, str, dict]]:
    """Validate structured calls without interpreting plaintext model output."""
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise ValueError("Expected an assistant message")
    for key in ("content", "reasoning"):
        if message.get(key) is not None and not isinstance(message[key], str):
            raise ValueError(f"Assistant {key} must be text or null")
    calls = message.get("tool_calls")
    if calls is None:
        calls = []
    if not isinstance(calls, list):
        raise ValueError("tool_calls must be a list")
    parsed = []
    seen = set()
    for call in calls:
        if not isinstance(call, dict) or call.get("type") != "function":
            raise ValueError("Expected a native function tool call")
        call_id = call.get("id")
        if not isinstance(call_id, str) or not call_id or call_id in seen:
            raise ValueError("Tool call IDs must be nonempty and unique")
        function = call.get("function")
        if not isinstance(function, dict) or not isinstance(function.get("name"), str):
            raise ValueError("Tool function name must be text")
        arguments = function.get("arguments")
        if not isinstance(arguments, str):
            raise ValueError("Native tool arguments must be a JSON string")
        args = json.loads(arguments)
        if not isinstance(args, dict):
            raise ValueError("Native tool arguments must decode to an object")
        seen.add(call_id)
        parsed.append((call_id, function["name"], args))
    return parsed


def _identity(case: dict, condition: str) -> dict:
    return {
        "case_id": case["id"],
        "family": case["family"],
        "condition": condition,
        "case": case,
    }


def _skipped(case: dict, condition: str, reason: str) -> dict:
    return {
        **_identity(case, condition),
        "started": False,
        "completed": False,
        "skipped": True,
        "stop_reason": reason,
        "messages": [],
        "requests": [],
        "responses": [],
        "actions": [],
        "generation_requests": 0,
        "tool_calls_used": 0,
        "source_correct": None,
        "workflow_complete": False,
        "valid_for_comparison": False,
    }


def _seed_preflight(settings, context):
    from gemma4_lab.behavior_diagnostics import SeededSession

    expectations = {
        "prefix_corruption": ("syntax_error", 2),
        "failing_assertion": ("wrong", 1),
        "passing_control": ("correct", 0),
        "irrelevant_pass": ("wrong", 0),
    }
    seeds = []
    for case in settings["cases"]:
        session = SeededSession(case, native_edit)
        session.seed_messages(context, settings["max_actions"])
        summary = session.summary()
        expected_status, expected_exit = expectations[case["family"]]
        turn = session.seed_turns[-1]
        response = turn["response"]
        exit_code = response.get("exit_code", response.get("details", {}).get("exit_code"))
        command = (
            "pytest tests/test_smoke.py"
            if case["family"] == "irrelevant_pass"
            else "pytest tests/test_task.py"
        )
        expected_response_status = "ok" if expected_exit == 0 else "error"
        if (
            summary["source_status"] != expected_status
            or turn["name"] != "run_command"
            or turn["arguments"] != {"command": command}
            or response["status"] != expected_response_status
            or exit_code != expected_exit
            or summary["target_checked_current"] != (case["family"] == "passing_control")
            or session.submitted
            or session.actions
        ):
            raise ValueError(f"Seeded test precondition failed: {case['id']}")
        seeds.append(
            {
                "case_id": case["id"],
                "family": case["family"],
                "summary": summary,
                "seed_turns": session.seed_turns,
            }
        )
    return {"stage": "seed-preflight", "passed": True, "cases": seeds, "model_calls": 0}


def _run_case(case, condition, prompt, context, settings, base_url, model, http):
    from gemma4_lab.behavior_diagnostics import TOOL_DEFINITIONS, SeededSession

    started = time.monotonic()
    deadline = started + settings["case_timeout_seconds"]
    session = SeededSession(case, native_edit)
    messages = [
        {"role": "system", "content": prompt},
        *session.seed_messages(context, settings["max_actions"]),
    ]
    row = {
        **_identity(case, condition),
        "started": True,
        "completed": False,
        "skipped": False,
        "messages": messages,
        "requests": [],
        "responses": [],
        "finish_reasons": [],
        "generation_requests": 0,
        "tool_calls_used": 0,
        "length": False,
        "protocol_error": False,
        "api_error": False,
        "request_timeout": False,
        "case_timeout": False,
        "action_budget_exhausted": False,
        "generation_budget_exhausted": False,
        "unexpected_parallel_calls": False,
    }
    try:
        for _ in range(settings["max_actions"]):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                row.update(case_timeout=True, stop_reason="case_timeout")
                break
            if row["tool_calls_used"] >= settings["max_actions"]:
                row.update(action_budget_exhausted=True, stop_reason="action_budget")
                break
            payload = {
                "model": model,
                "messages": copy.deepcopy(messages),
                "tools": TOOL_DEFINITIONS,
                "tool_choice": "auto",
                "parallel_tool_calls": False,
                "temperature": settings["temperature"],
                "top_p": settings["top_p"],
                "max_tokens": settings["max_tokens"],
                "seed": settings["seed"],
                "stream": False,
            }
            row["requests"].append(payload)
            row["generation_requests"] += 1
            try:
                response = http.post(
                    base_url + "/chat/completions",
                    json=payload,
                    timeout=min(settings["request_timeout_seconds"], remaining),
                )
                if not response.ok:
                    row["responses"].append(
                        {"http_status": response.status_code, "body": response.text}
                    )
                response.raise_for_status()
                body = response.json()
                row["responses"].append(body)
            except Exception as exc:
                row.update(api_error=True, error_type=type(exc).__name__, error=str(exc))
                row["request_timeout"] = isinstance(exc, http.exceptions.Timeout)
                row["stop_reason"] = "request_timeout" if row["request_timeout"] else "api_error"
                break
            try:
                choice = body["choices"][0]
                finish_reason = choice.get("finish_reason")
                row["finish_reasons"].append(finish_reason)
                row["length"] = row["length"] or finish_reason == "length"
                message = choice["message"]
                calls = native_calls(message)
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                row.update(protocol_error=True, stop_reason="protocol_error", error=str(exc))
                break
            # Preserve native reasoning, content, call IDs, and argument strings.
            messages.append(copy.deepcopy(message))
            if finish_reason == "length":
                row["stop_reason"] = "length"
                break
            if time.monotonic() >= deadline:
                row.update(case_timeout=True, stop_reason="case_timeout")
                break
            if not calls:
                row["stop_reason"] = "length" if row["length"] else "assistant_finished"
                break
            row["unexpected_parallel_calls"] |= len(calls) > 1
            for call_id, name, args in calls:
                if session.submitted:
                    result = {
                        "status": "error",
                        "error_type": "AlreadySubmitted",
                        "error_message": "The diagnostic session has finished.",
                    }
                elif row["tool_calls_used"] >= settings["max_actions"]:
                    row["action_budget_exhausted"] = True
                    result = {
                        "status": "error",
                        "error_type": "BudgetExceeded",
                        "error_message": "The diagnostic tool-action budget is exhausted.",
                    }
                elif time.monotonic() >= deadline:
                    row["case_timeout"] = True
                    result = {
                        "status": "error",
                        "error_type": "TimeoutExceeded",
                        "error_message": "The diagnostic case deadline has elapsed.",
                    }
                else:
                    row["tool_calls_used"] += 1
                    result = session.dispatch(name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            if session.submitted:
                row["stop_reason"] = "submitted"
                break
            if row["case_timeout"]:
                row["stop_reason"] = "case_timeout"
                break
        else:
            row.update(generation_budget_exhausted=True, stop_reason="generation_budget")
        row["action_budget_exhausted"] |= (
            row["tool_calls_used"] >= settings["max_actions"] and not session.submitted
        )
    except Exception as exc:
        row.update(
            error_type=type(exc).__name__,
            error=str(exc),
            traceback=traceback.format_exc(),
            stop_reason="execution_error",
        )
    row.update(session.summary())
    row.update(
        actions=session.actions,
        source=session.source,
        submitted=session.submitted,
        elapsed_seconds=time.monotonic() - started,
        completed=True,
        valid_for_comparison=not (
            row["api_error"] or row["protocol_error"] or row.get("stop_reason") == "execution_error"
        ),
    )
    return row


def run_diagnostic(
    settings: dict, prompts: dict[str, str], context: str, execution_limit_seconds: int
):
    """Stream all fixed rows, retaining skipped cases and bounded error records."""
    import requests

    started = time.monotonic()
    server = None
    results = []
    schedule = []
    final = {"stage": "finished", "completed": False}
    try:
        conditions = [item["name"] for item in settings["conditions"]]
        for index, case in enumerate(settings["cases"]):
            ordered = conditions if index % 2 == 0 else list(reversed(conditions))
            schedule.extend((case, condition) for condition in ordered)
        if len(schedule) != 24 or len(conditions) != 2 or len(set(conditions)) != 2:
            raise ValueError("The diagnostic requires twelve cases and two distinct conditions")
        if any(settings.get(key) != value for key, value in FIXED_LIMITS.items()):
            raise ValueError("Diagnostic generation settings differ from the fixed limits")
        if set(prompts) != set(conditions):
            raise ValueError("System prompts must match the two configured conditions")
        yield _seed_preflight(settings, context)
        server, metadata = create_approved_server()
        server.start()
        metadata.update(
            python=platform.python_version(),
            packages={d.metadata["Name"]: d.version for d in distributions()},
            server_ready_seconds=time.monotonic() - started,
        )
        yield {"stage": "server-ready", "metadata": metadata}
        listing = requests.get(server.base_url + "/models", timeout=10)
        listing.raise_for_status()
        models = listing.json()["data"]
        if len(models) != 1:
            raise ValueError("The unchanged diagnostic requires exactly one served base model")
        model = models[0]["id"]
        final["served_model"] = model
        for case, condition in schedule:
            remaining = execution_limit_seconds - (time.monotonic() - started)
            if remaining < settings["case_timeout_seconds"] + 30:
                row = _skipped(case, condition, "insufficient_execution_allocation")
            else:
                row = _run_case(
                    case,
                    condition,
                    prompts[condition],
                    context,
                    settings,
                    server.base_url,
                    model,
                    requests,
                )
            results.append(row)
            yield {"stage": "case", "result": row}
        final["completed"] = all(row["started"] and row["completed"] for row in results)
    except Exception as exc:
        error = {
            "error_type": type(exc).__name__,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }
        final.update(error)
        yield {"stage": "error", **error}
        for case, condition in schedule[len(results) :]:
            row = _skipped(case, condition, "run_error")
            results.append(row)
            yield {"stage": "case", "result": row}
    finally:
        if server is not None:
            try:
                log_path = Path(server.log_path)
                if log_path.is_file():
                    final["server_log"] = log_path.read_text(errors="replace")[-150000:]
            except Exception as exc:
                final["log_capture_error"] = str(exc)
            finally:
                try:
                    server.stop()
                except Exception as exc:
                    error = {
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                    final.update(error)
                    yield {"stage": "error", **error}
    final.update(
        results=results,
        completed_cases=sum(bool(row.get("completed")) for row in results),
        started_cases=sum(bool(row.get("started")) for row in results),
        elapsed_seconds=time.monotonic() - started,
        valid_for_comparison=bool(results)
        and not final.get("error")
        and all(row.get("valid_for_comparison", False) for row in results),
    )
    yield final
