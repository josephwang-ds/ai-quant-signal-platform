"""In-memory sliding-window rate limiter for a single demo instance."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Literal

from app.security.settings import get_demo_protection_settings

RateTier = Literal["llm", "expensive", "write", "read"]


@dataclass(frozen=True)
class RateLimitExceeded:
    tier: RateTier
    retry_after_seconds: int
    detail: str = "Too many requests. Please wait a moment and try again."


class InMemoryRateLimiter:
    """
    Process-local sliding window limiter.

    Suitable for a single-instance portfolio demo only. Multiple replicas do
    not share counters and will not enforce a global limit.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._hits: dict[tuple[str, RateTier], Deque[float]] = defaultdict(deque)

    def check(self, *, key: str, tier: RateTier) -> RateLimitExceeded | None:
        settings = get_demo_protection_settings()
        if not settings.rate_limit_enabled:
            return None

        limit = {
            "llm": settings.agent_rate_limit,
            "expensive": settings.expensive_rate_limit,
            "write": settings.write_rate_limit,
            "read": settings.read_rate_limit,
        }[tier]
        window = float(settings.rate_limit_window_seconds)
        now = time.monotonic()
        bucket_key = (key, tier)

        with self._lock:
            bucket = self._hits[bucket_key]
            while bucket and now - bucket[0] >= window:
                bucket.popleft()
            if len(bucket) >= limit:
                oldest = bucket[0]
                retry_after = max(1, int(window - (now - oldest)) + 1)
                return RateLimitExceeded(
                    tier=tier, retry_after_seconds=retry_after
                )
            bucket.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _limiter


def reset_rate_limiter_for_tests() -> None:
    _limiter.reset()


def check_rate_limit(*, client_key: str, tier: RateTier) -> RateLimitExceeded | None:
    return _limiter.check(key=client_key, tier=tier)


def classify_endpoint(method: str, path: str) -> RateTier:
    """Map HTTP method + path to a protection tier."""
    normalized = path.rstrip("/") or "/"
    upper = method.upper()

    if normalized == "/health":
        return "read"
    if normalized.endswith("/status") and upper == "GET":
        return "read"

    # LLM reviewer, Copilot, Governance Agent mutations — strictest.
    if "/research/copilot/" in normalized:
        return "llm"
    if "/research/reviewer/" in normalized:
        return "llm"
    if "/research/agent/" in normalized:
        if upper == "GET":
            return "read"
        return "llm"
    if "/research/guidance/" in normalized and upper == "POST":
        return "llm"

    # Expensive deterministic compute / provider fetch.
    if normalized in {
        "/api/v1/research/execution",
        "/api/v1/research/validation",
        "/api/v1/research/evaluation",
        "/api/v1/research/factor-validation",
    }:
        return "expensive"
    if "/factor-validation" in normalized:
        return "expensive"
    if normalized.startswith("/api/backtest"):
        return "expensive"
    if normalized in {"/api/market-watch", "/api/chart/compare"}:
        return "expensive"
    if normalized.startswith("/api/model") or "/feature-interpretation" in normalized:
        return "expensive"
    if normalized.startswith("/api/insights"):
        return "expensive"
    if normalized.startswith("/api/risk"):
        return "expensive"

    # Database / mutable paper state.
    if normalized.startswith("/api/experiments") and upper in {
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }:
        return "write"
    if normalized.startswith("/api/paper") and upper != "GET":
        return "write"

    if upper == "GET":
        return "read"
    return "write"
