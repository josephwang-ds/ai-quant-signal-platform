"""LLM port — Application-owned abstraction; no provider SDK imports here."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ContextItem:
    citation_id: str
    source_type: str
    source_id: str
    label: str
    content: str


@dataclass
class LlmResult:
    text: str
    model: str
    latency_ms: int = 0
    raw_finish_reason: str | None = None


class LlmPort(Protocol):
    """Generate grounded explanations from assembled workspace context."""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult: ...
