"""Environment-driven demo protection settings.

The in-memory rate limiter and concurrency gate are for a single-instance
portfolio demo (for example one Render web process). They are not a
distributed, multi-replica exact limiter.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_int(name: str, default: int, *, minimum: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}.")
    return value


def _env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean.")


def _env_csv(name: str) -> frozenset[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return frozenset()
    values = {part.strip() for part in raw.split(",") if part.strip()}
    return frozenset(values)


@dataclass(frozen=True)
class DemoProtectionSettings:
    """Operational knobs for public-demo security and cost protection."""

    max_request_body_bytes: int
    agent_rate_limit: int
    expensive_rate_limit: int
    write_rate_limit: int
    read_rate_limit: int
    rate_limit_window_seconds: int
    rate_limit_enabled: bool
    llm_max_concurrency: int
    llm_timeout_seconds: float
    provider_fetch_timeout_seconds: float
    validation_timeout_seconds: float
    trusted_proxy_ips: frozenset[str]


@lru_cache(maxsize=1)
def get_demo_protection_settings() -> DemoProtectionSettings:
    return DemoProtectionSettings(
        max_request_body_bytes=_env_int(
            "MAX_REQUEST_BODY_BYTES", 1_048_576, minimum=1024
        ),
        agent_rate_limit=_env_int("AGENT_RATE_LIMIT", 10, minimum=1),
        expensive_rate_limit=_env_int("EXPENSIVE_RATE_LIMIT", 30, minimum=1),
        write_rate_limit=_env_int("WRITE_RATE_LIMIT", 20, minimum=1),
        read_rate_limit=_env_int("READ_RATE_LIMIT", 120, minimum=1),
        rate_limit_window_seconds=_env_int(
            "RATE_LIMIT_WINDOW_SECONDS", 60, minimum=1
        ),
        rate_limit_enabled=_env_bool("RATE_LIMIT_ENABLED", True),
        llm_max_concurrency=_env_int("LLM_MAX_CONCURRENCY", 2, minimum=1),
        llm_timeout_seconds=_env_float("LLM_TIMEOUT_SECONDS", 45.0, minimum=1.0),
        provider_fetch_timeout_seconds=_env_float(
            "PROVIDER_FETCH_TIMEOUT_SECONDS", 30.0, minimum=1.0
        ),
        validation_timeout_seconds=_env_float(
            "VALIDATION_TIMEOUT_SECONDS", 120.0, minimum=5.0
        ),
        trusted_proxy_ips=_env_csv("TRUSTED_PROXY_IPS"),
    )


def clear_demo_protection_settings_cache() -> None:
    get_demo_protection_settings.cache_clear()
