"""Pre-registered gate for weight-space study v2 plus the paired panel runner."""

import math
import tempfile
import time
import traceback
from pathlib import Path

from gemma4_lab.behavior_inference import _run_case, _seed_preflight, _skipped
from gemma4_lab.remote_serving import MODEL_PATH, create_approved_server

ARMS = ("base", "base_repeat", "zero", "random", "a", "neg", "read", "prompt")
ADAPTERS = {
    "zero": "wsp2_zero",
    "random": "wsp2_random",
    "a": "wsp2_a",
    "neg": "wsp2_neg",
    "read": "wsp_read",
}


def sign_test_p(wins: int, losses: int) -> float:
    """One-sided exact binomial P(X >= wins) with p = 0.5 over discordant pairs."""
    n = wins + losses
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(wins, n + 1)) / 2**n


def _done(row) -> bool:
    return bool(row and row.get("workflow_complete"))


def paired(rows, case_ids, left, right) -> dict:
    wins = sum(_done(rows.get((c, left))) and not _done(rows.get((c, right))) for c in case_ids)
    losses = sum(_done(rows.get((c, right))) and not _done(rows.get((c, left))) for c in case_ids)
    return {
        "wins": wins,
        "losses": losses,
        "net": wins - losses,
        "p_one_sided": sign_test_p(wins, losses),
        "left_completed": sum(_done(rows.get((c, left))) for c in case_ids),
        "right_completed": sum(_done(rows.get((c, right))) for c in case_ids),
    }


def assess_v2(
    rows: list[dict], cases: list[dict], application: dict | None = None, arms=ARMS
) -> dict:
    """Apply the frozen gates in docs/research/weight-space-study-v2.md verbatim."""
    indexed = {(r["case_id"], r["condition"]): r for r in rows}
    expected = {(c["id"], arm) for c in cases for arm in arms}
    valid = (
        len(rows) == len(expected) == len(indexed)
        and set(indexed) == expected
        and all(
            r.get("started") and r.get("completed") and r.get("valid_for_comparison") for r in rows
        )
    )
    target = [c["id"] for c in cases if c["family"] == "prefix_corruption"]
    other = [c["id"] for c in cases if c["family"] != "prefix_corruption"]
    controls = [c["id"] for c in cases if c["family"] == "passing_control"]
    comparisons = {arm: paired(indexed, target, "a", arm) for arm in arms if arm != "a"}
    gate2 = {
        arm: comparisons[arm]["net"] >= 6 and comparisons[arm]["p_one_sided"] < 0.05
        for arm in ("base", "base_repeat", "zero", "random")
        if arm in arms
    }
    gate3 = comparisons["neg"]["net"] >= 4
    nontarget_vs_base = paired(indexed, other, "a", "base")
    gate4 = nontarget_vs_base["losses"] <= 1
    gate1 = valid and all(_done(indexed.get((c, "a"))) for c in controls)
    noise = (
        paired(indexed, target, "base", "base_repeat")
        if "base_repeat" in arms
        else {"wins": 0, "losses": 0}
    )
    noise_flag = noise["wins"] + noise["losses"] > 3
    application_ok = bool(application and application.get("passed"))
    return {
        "valid_coverage": valid,
        "application_passed": application_ok,
        "gate1_valid_and_controls_preserved": gate1,
        "gate2_beats_base_repeat_zero_random": gate2,
        "gate3_beats_sign_flipped": gate3,
        "gate4_nontarget_losses_at_most_one": gate4,
        "primary_passed": bool(
            application_ok and gate1 and all(gate2.values()) and gate3 and gate4 and not noise_flag
        ),
        "base_vs_repeat_disagreements": noise["wins"] + noise["losses"],
        "noise_too_high": noise_flag,
        "target_comparisons_a_vs": comparisons,
        "nontarget_a_vs_base": nontarget_vs_base,
        "target_completed": {
            arm: sum(_done(indexed.get((c, arm))) for c in target) for arm in arms
        },
        "nontarget_completed": {
            arm: sum(_done(indexed.get((c, arm))) for c in other) for arm in arms
        },
        "first_reread_on_target": {
            arm: sum(
                bool(
                    ((indexed.get((c, arm)) or {}).get("actions") or [{}])[0].get("name")
                    == "read_file"
                )
                for c in target
            )
            for arm in arms
        },
    }


def assess_seeds(rows, cases, application, arms, seeds) -> dict:
    """Apply the v3 gate form independently to each sampling seed (amendment 1)."""
    by_seed = {
        str(seed): assess_v2([r for r in rows if r.get("seed") == seed], cases, application, arms)
        for seed in seeds
    }
    return {
        "by_seed": by_seed,
        "all_seeds_primary_passed": all(a["primary_passed"] for a in by_seed.values()),
        "target_completed_by_seed": {k: a["target_completed"] for k, a in by_seed.items()},
        "a_vs_base_by_seed": {k: a["target_comparisons_a_vs"]["base"] for k, a in by_seed.items()},
    }


def assess_application(token_cases, settings):
    from gemma4_lab.adapter_probe import logprob_distance

    names = tuple(settings["app_names"])
    if [c.get("prompt") for c in token_cases] != settings["application_prefixes"] or any(
        set(c.get("distributions", {})) != set(names)
        or any(len(v) != 2 for v in c["distributions"].values())
        for c in token_cases
    ):
        return {"passed": False, "reason": "Incomplete application controls"}
    drift, effects = 0.0, {n: [] for n in names if n not in ("base", "zero")}
    for case in token_cases:
        d = case["distributions"]
        for name in names:
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
        and all(max(v) > threshold for v in effects.values()),
        "maximum_control_drift_nats": drift,
        "effect_threshold_nats": threshold,
        "effect_lower_bounds_nats": effects,
    }


def run_panel(files, prepared, settings, prompts, context, cases, execution_limit_seconds):
    import platform
    from importlib.metadata import distributions

    import requests

    start, server, rows, token_cases = time.monotonic(), None, [], []
    final = {"stage": "finished", "completed": False}
    arms = settings["conditions"]
    seeds = settings.get("seeds", [settings["seed"]])
    schedule = [
        (case, condition, seed)
        for seed in seeds
        for i, case in enumerate(cases)
        for condition in (arms[i % len(arms) :] + arms[: i % len(arms)])
    ]
    try:
        if len(cases) != 36 or [a["name"] for a in arms] != settings.get(
            "expected_arms", list(ARMS)
        ):
            raise ValueError("Require 36 frozen cases and the frozen arm list")
        yield _seed_preflight({**settings, "cases": cases}, context)
        with tempfile.TemporaryDirectory(prefix="wsp-v2-") as directory:
            root = Path(directory)
            _write_files(root, files, prepared["file_sha256"])
            server, metadata = create_approved_server(submission_directory=root)
            server.start()
            metadata.update(
                python=platform.python_version(),
                packages={d.metadata["Name"]: d.version for d in distributions()},
                server_ready_seconds=time.monotonic() - start,
            )
            yield {"stage": "server-ready", "metadata": metadata}
            listed = requests.get(server.base_url + "/models", timeout=10)
            listed.raise_for_status()
            ids = {r["id"] for r in listed.json()["data"]}
            if not {str(MODEL_PATH), *ADAPTERS.values()}.issubset(ids):
                raise ValueError("Expected the base model and every adapter alias")
            models = {"base": str(MODEL_PATH), **{k: v for k, v in ADAPTERS.items()}}
            for prompt in settings["application_prefixes"]:
                case = {"prompt": prompt, "distributions": {n: [] for n in settings["app_names"]}}
                for name in settings["application_order"]:
                    if execution_limit_seconds - (time.monotonic() - start) < 60:
                        raise TimeoutError("Insufficient remaining execution allocation")
                    response = requests.post(
                        server.base_url + "/completions",
                        json={
                            "model": models[name],
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
                    case["distributions"][name].append(
                        body["choices"][0]["logprobs"]["top_logprobs"][0]
                    )
                    yield {"stage": "token-response", "condition": name, "prompt": prompt}
                token_cases.append(case)
            application = assess_application(token_cases, settings)
            yield {"stage": "application-assessment", "assessment": application}
            for case, condition, seed in schedule:
                remaining = execution_limit_seconds - (time.monotonic() - start)
                if remaining < settings["case_timeout_seconds"] + 30:
                    row = _skipped(case, condition["name"], "insufficient_execution_allocation")
                else:
                    name = condition["name"]
                    model = models.get(name, str(MODEL_PATH))
                    row = _run_case(
                        case,
                        name,
                        prompts[condition["prompt"]],
                        context,
                        {**settings, "seed": seed},
                        server.base_url,
                        model,
                        requests,
                    )
                row["seed"] = seed
                rows.append(row)
                yield {"stage": "case", "result": row}
            names = tuple(a["name"] for a in arms)
            final.update(
                completed=all(r["started"] and r["completed"] for r in rows),
                application=application,
                assessment=(
                    assess_seeds(rows, cases, application, names, seeds)
                    if "seeds" in settings
                    else assess_v2(rows, cases, application, names)
                ),
            )
    except Exception as exc:
        final.update(
            error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()
        )
        for case, condition, seed in schedule[len(rows) :]:
            row = _skipped(case, condition["name"], "run_error")
            row["seed"] = seed
            rows.append(row)
            yield {"stage": "case", "result": row}
    finally:
        if server is not None:
            try:
                log = Path(server.log_path)
                if log.is_file():
                    final["server_log"] = log.read_text(errors="replace")[-20000:]
            except Exception as exc:
                final["log_capture_error"] = str(exc)
            finally:
                try:
                    server.stop()
                except Exception as exc:
                    final["shutdown_error"] = str(exc)
    # Per-case rows already streamed; keep the terminal event small enough to return inline.
    final.update(case_count=len(rows), elapsed_seconds=time.monotonic() - start)
    yield final


def _write_files(root: Path, files: dict[str, bytes], expected: dict[str, str]) -> None:
    import hashlib

    if {n: hashlib.sha256(v).hexdigest() for n, v in sorted(files.items())} != expected:
        raise ValueError("Adapter package differs from CPU preparation")
    for name, value in files.items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Package path escapes its directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
