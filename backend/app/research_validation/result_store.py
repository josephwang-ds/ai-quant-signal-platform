"""Storage port for produced ValidationResult payloads.

Evaluation must summarize an *existing* ValidationResult instead of
triggering a new Validation run. This module is the seam that makes that
possible: Validation saves its output once and hands back an opaque
``validation_run_id``; Evaluation loads the same payload by that id and
never calls ``ResearchValidationService.execute`` itself.

MVP scope: an in-memory store only. There is no Postgres, no Redis, and no
background worker here. Saved results are lost on backend restart —
persistent ValidationRun storage remains explicitly out of scope until a
future ADR revisits it.
"""

from __future__ import annotations

import uuid
from typing import Any, Protocol


class ValidationResultStore(Protocol):
    """Port implemented by any concrete ValidationResult storage backend."""

    def save(self, result: dict[str, Any]) -> str:
        """Persist a complete ValidationResult and return its run id."""
        ...

    def get(self, validation_run_id: str) -> dict[str, Any] | None:
        """Return the stored ValidationResult, or None if unknown."""
        ...


class InMemoryValidationResultStore:
    """Process-local ValidationResultStore. Not durable across restarts."""

    def __init__(self) -> None:
        self._results: dict[str, dict[str, Any]] = {}

    def save(self, result: dict[str, Any]) -> str:
        validation_run_id = f"val-{uuid.uuid4().hex[:20]}"
        stored = dict(result)
        stored["validation_run_id"] = validation_run_id
        self._results[validation_run_id] = stored
        return validation_run_id

    def get(self, validation_run_id: str) -> dict[str, Any] | None:
        stored = self._results.get(validation_run_id)
        return dict(stored) if stored is not None else None


_default_store: ValidationResultStore | None = None


def get_default_validation_result_store() -> ValidationResultStore:
    """Process-wide singleton shared by the Validation and Evaluation routes.

    Both routes must resolve to the same store instance: Validation writes
    to it, Evaluation only ever reads from it.
    """
    global _default_store
    if _default_store is None:
        _default_store = InMemoryValidationResultStore()
    return _default_store
