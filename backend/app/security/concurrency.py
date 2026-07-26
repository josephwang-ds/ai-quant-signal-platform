"""Bounded LLM concurrency — fail closed, never queue forever."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

from app.security.settings import get_demo_protection_settings


class LlmConcurrencyFullError(Exception):
    """Raised when the process-local LLM concurrency budget is exhausted."""

    def __init__(
        self,
        message: str = (
            "The language-model capacity for this demo is temporarily full. "
            "Please try again shortly."
        ),
        *,
        status_code: int = 503,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class _ResizableSemaphore:
    """Semaphore rebuilt when LLM_MAX_CONCURRENCY settings change in tests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._limit: int | None = None
        self._semaphore: threading.BoundedSemaphore | None = None

    def _ensure(self) -> threading.BoundedSemaphore:
        limit = get_demo_protection_settings().llm_max_concurrency
        with self._lock:
            if self._semaphore is None or self._limit != limit:
                self._limit = limit
                self._semaphore = threading.BoundedSemaphore(limit)
            return self._semaphore

    def try_acquire(self) -> bool:
        return self._ensure().acquire(blocking=False)

    def release(self) -> None:
        semaphore = self._ensure()
        try:
            semaphore.release()
        except ValueError:
            # Over-release guard for tests that reset mid-flight.
            pass

    def reset(self) -> None:
        with self._lock:
            self._limit = None
            self._semaphore = None


_llm_semaphore = _ResizableSemaphore()


def get_llm_semaphore() -> _ResizableSemaphore:
    return _llm_semaphore


def reset_llm_concurrency_for_tests() -> None:
    _llm_semaphore.reset()


@contextmanager
def acquire_llm_slot() -> Iterator[None]:
    """
    Non-blocking LLM slot acquisition.

    If the budget is full, raise immediately (no infinite queue).
    """
    if not _llm_semaphore.try_acquire():
        raise LlmConcurrencyFullError()
    try:
        yield
    finally:
        _llm_semaphore.release()
