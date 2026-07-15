"""Parse structured LLM output: answer + citation_ids."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class ParsedLlmResponse:
    answer: str
    citation_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _strip_code_fence(raw_text: str) -> str:
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def parse_structured_llm_response(raw_text: str) -> ParsedLlmResponse:
    """Safely parse provider output into answer and citation_ids."""
    normalized = _strip_code_fence(raw_text)
    if not normalized:
        return ParsedLlmResponse(
            answer="",
            warnings=["empty_answer"],
        )

    try:
        payload = json.loads(normalized)
    except json.JSONDecodeError:
        return ParsedLlmResponse(
            answer=normalized,
            warnings=["invalid_structured_output"],
        )

    if not isinstance(payload, dict):
        return ParsedLlmResponse(
            answer=normalized,
            warnings=["invalid_structured_output"],
        )

    answer = str(payload.get("answer") or "").strip()
    raw_ids = payload.get("citation_ids", [])
    citation_ids: list[str] = []
    if isinstance(raw_ids, list):
        citation_ids = [
            str(item).strip()
            for item in raw_ids
            if isinstance(item, (str, int)) and str(item).strip()
        ]

    warnings: list[str] = []
    if not answer:
        warnings.append("empty_answer")
    if "citation_ids" not in payload:
        warnings.append("missing_citation_ids")

    return ParsedLlmResponse(answer=answer, citation_ids=citation_ids, warnings=warnings)
