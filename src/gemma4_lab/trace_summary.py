"""Count edit failures and recoveries in official ATIF traces; no ML imports."""

import json


def _status(observation) -> str:
    try:
        result = json.loads((observation or {}).get("content", ""))
        return result.get("error_type") or result.get("status", "")
    except (ValueError, AttributeError):
        return ""


def summarize_trace(trace: dict) -> dict:
    """Tool order, edit_file calls the editor rejected, and what the agent called next.

    Budget-exhaustion errors are not edit failures and are not counted.
    """
    calls, empty, models = [], 0, set()
    for step in trace["steps"]:
        if step.get("source") != "agent":
            continue
        if step.get("model_name"):
            models.add(step["model_name"])
        made = step.get("tool_calls") or []
        if not made and not (step.get("message") or "").strip():
            empty += 1
        # One observation per step: with parallel calls only the last gets a status.
        for index, call in enumerate(made):
            last = index == len(made) - 1
            calls.append((call["function_name"], _status(step.get("observation")) if last else ""))
    failed = [
        i
        for i, (name, status) in enumerate(calls)
        if name == "edit_file" and status == "FileEditError"
    ]
    return {
        "tools": [name for name, _ in calls],
        "edit_calls": sum(name == "edit_file" for name, _ in calls),
        "failed_edits": len(failed),
        "failed_edit_then_read": sum(
            i + 1 < len(calls) and calls[i + 1][0] == "read_file" for i in failed
        ),
        "empty_responses": empty,
        "models": sorted(models),
    }
