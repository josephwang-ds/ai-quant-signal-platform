"""Process-local agent run metadata store (not durable across restarts)."""

from __future__ import annotations

from typing import Any


class InMemoryAgentRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}

    def save(self, agent_run_id: str, payload: dict[str, Any]) -> None:
        self._runs[agent_run_id] = dict(payload)

    def get(self, agent_run_id: str) -> dict[str, Any] | None:
        stored = self._runs.get(agent_run_id)
        return dict(stored) if stored is not None else None

    def update(self, agent_run_id: str, **fields: Any) -> dict[str, Any] | None:
        stored = self._runs.get(agent_run_id)
        if stored is None:
            return None
        stored.update(fields)
        return dict(stored)


_default_store: InMemoryAgentRunStore | None = None


def get_default_agent_run_store() -> InMemoryAgentRunStore:
    global _default_store
    if _default_store is None:
        _default_store = InMemoryAgentRunStore()
    return _default_store
