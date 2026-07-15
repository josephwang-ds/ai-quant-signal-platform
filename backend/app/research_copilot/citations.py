"""Resolve answer-specific citations from LLM-selected citation IDs."""

from __future__ import annotations

import json
from typing import Any

from app.research_copilot.llm_port import ContextItem
from app.research_copilot.schemas import EvidenceCitation

MAX_EXCERPT_CHARS = 240


def build_context_index(context_items: list[ContextItem]) -> dict[str, ContextItem]:
    return {item.citation_id: item for item in context_items}


def _excerpt_from_content(content: str) -> str:
    stripped = content.strip()
    if len(stripped) <= MAX_EXCERPT_CHARS:
        return stripped
    return stripped[: MAX_EXCERPT_CHARS - 3] + "..."


def context_item_to_citation(item: ContextItem) -> EvidenceCitation:
    return EvidenceCitation(
        source_type=item.source_type,
        source_id=item.source_id,
        label=item.label,
        excerpt=_excerpt_from_content(item.content),
    )


def resolve_selected_citations(
    citation_ids: list[str],
    context_index: dict[str, ContextItem],
) -> tuple[list[EvidenceCitation], list[str]]:
    """Return resolved citations and warning codes for unknown IDs."""
    citations: list[EvidenceCitation] = []
    warnings: list[str] = []
    seen: set[str] = set()

    for citation_id in citation_ids:
        if citation_id in seen:
            continue
        seen.add(citation_id)
        item = context_index.get(citation_id)
        if item is None:
            warnings.append(f"unknown_citation_id:{citation_id}")
            continue
        citations.append(context_item_to_citation(item))

    return citations, warnings


def summarize_stage(stage: dict[str, Any] | None) -> str:
    if not stage:
        return "Evidence unavailable for this stage."
    return json.dumps(stage, ensure_ascii=False)
