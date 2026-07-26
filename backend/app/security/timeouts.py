"""Explicit timeout helpers for long deterministic work."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable, TypeVar

T = TypeVar("T")


class OperationTimeoutError(Exception):
    def __init__(self, message: str, *, status_code: int = 504) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def run_with_timeout(
    fn: Callable[[], T],
    *,
    timeout_seconds: float,
    message: str,
) -> T:
    """
    Run a sync callable with a hard wall-clock timeout.

    Uses a worker thread so FastAPI sync routes can fail closed instead of
    hanging indefinitely. The worker may continue briefly after timeout; the
    HTTP response still returns a safe timeout error.
    """
    if timeout_seconds <= 0:
        return fn()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeout as exc:
            future.cancel()
            raise OperationTimeoutError(message, status_code=504) from exc
