"""Read and check the bounded baseline plan without contacting cloud services."""

import tomllib
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def candidate_directory(root: Path, name: str) -> Path:
    """Resolve one candidate without allowing a mount of its parent checkout."""
    parent = (root / "submissions").resolve()
    if name in {"", ".", ".."} or Path(name).name != name:
        raise ValueError("Select a candidate directly under submissions/")
    directory = (parent / name).resolve()
    if directory.parent != parent or not directory.is_dir():
        raise ValueError("Select an existing candidate directly under submissions/")
    return directory


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _positive_decimal(value: object, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a positive decimal") from exc
    if not number.is_finite() or number <= 0:
        raise ValueError(f"{label} must be a positive finite decimal")
    return number


def estimate_run(config: dict[str, Any]) -> dict[str, Any]:
    """Reject an unbounded plan and estimate its requested compute allocation.

    This is a preflight estimate, not a provider-enforced billing limit. Startup
    and idle time are included; builds, staging, storage, and egress are excluded.
    """
    modal = config["modal"]
    if modal["profile"] != "ach-bj100":
        raise ValueError("Only Modal profile ach-bj100 is authorized for this project")
    checked_hourly_rates = {"L4": Decimal("0.80"), "A10G": Decimal("1.10")}
    if modal["gpu"] not in checked_hourly_rates:
        raise ValueError("Only documented L4/A10G baseline plans are supported")
    for field in (
        "gpu_count",
        "cpu_cores",
        "memory_gib",
        "timeout_seconds",
        "startup_timeout_seconds",
        "scaledown_seconds",
        "max_containers",
    ):
        if type(modal[field]) is not int or modal[field] <= 0:
            raise ValueError(f"modal.{field} must be a positive integer")
    if modal["gpu_count"] != 1 or modal["max_containers"] != 1:
        raise ValueError("The initial baseline is limited to one container with one GPU")
    rates = config["rates_usd_per_second"]
    if _positive_decimal(rates["gpu"], "rate.gpu") * 3600 < checked_hourly_rates[modal["gpu"]]:
        raise ValueError("GPU rate underestimates the checked hourly rate for this hardware")
    per_second = sum(
        _positive_decimal(rates[rate], f"rate.{rate}") * modal[quantity]
        for rate, quantity in (
            ("gpu", "gpu_count"),
            ("cpu_core", "cpu_cores"),
            ("memory_gib", "memory_gib"),
        )
    )
    seconds = sum(
        modal[field]
        for field in ("timeout_seconds", "startup_timeout_seconds", "scaledown_seconds")
    )
    estimate = per_second * seconds
    ceiling = _positive_decimal(config["budget"]["initial_run_usd"], "initial_run_usd")
    if ceiling > Decimal("2.00") or estimate > ceiling:
        raise ValueError(f"Compute estimate ${estimate:.4f} exceeds the initial allocation")
    return {
        "profile": modal["profile"],
        "gpu": modal["gpu"],
        "gpu_count": modal["gpu_count"],
        "bounded_seconds": seconds,
        "estimated_compute_usd": f"{estimate:.6f}",
        "allocation_usd": str(ceiling),
        "excluded_costs": ["image builds", "data staging", "storage", "network egress"],
        "launches_compute": False,
    }
