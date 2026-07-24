"""LLM bridge — reuses research_copilot LlmPort; no second HTTP client."""

from __future__ import annotations

import json
from typing import Any, Optional

from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.research_copilot.llm_response import parse_structured_llm_response
from app.research_copilot.safety import evaluate_answer
from app.research_agent.prompts import GOVERNANCE_SYSTEM_V1


class AgentLlmUnavailable(Exception):
    pass


def generate_structured(
    llm: LlmPort | None,
    *,
    user_prompt: str,
    context_items: list[ContextItem] | None = None,
    system_prompt: str = GOVERNANCE_SYSTEM_V1,
) -> tuple[dict[str, Any], LlmResult | None, list[str]]:
    """
    Call the shared LlmPort and parse JSON. Returns (payload, llm_result, warnings).
    """
    warnings: list[str] = []
    if llm is None:
        raise AgentLlmUnavailable("Governance Agent LLM is not configured.")

    result = llm.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        context=context_items or [],
    )
    parsed = parse_structured_llm_response(result.text)
    warnings.extend(parsed.warnings)

    # Try to expose full JSON object when the model returned more fields
    payload: dict[str, Any] = {"answer": parsed.answer, "citation_ids": parsed.citation_ids}
    try:
        raw = json.loads(result.text)
        if isinstance(raw, dict):
            payload = raw
    except (TypeError, json.JSONDecodeError):
        warnings.append("invalid_structured_output")

    context_blob = json.dumps(
        [item.content for item in (context_items or [])],
        ensure_ascii=False,
    )
    answer_text = str(payload.get("executive_summary") or payload.get("answer") or "")
    verdict = evaluate_answer(
        answer_text,
        citations=[],
        context_blob=context_blob + " " + result.text,
    )
    if not verdict.safe:
        warnings.extend(verdict.warnings)
        payload["_safety_blocked"] = True
        payload["_sanitized_answer"] = verdict.sanitized_answer

    if parsed.factor_fields:
        payload.setdefault("_factor_fields", parsed.factor_fields)

    return payload, result, warnings


def context_from_dicts(items: list[dict[str, Any]]) -> list[ContextItem]:
    out: list[ContextItem] = []
    for item in items:
        out.append(
            ContextItem(
                citation_id=str(item.get("citation_id") or item.get("knowledge_id") or item.get("id") or "ctx"),
                source_type=str(item.get("source_type") or "agent"),
                source_id=str(item.get("source_id") or item.get("knowledge_id") or "agent"),
                label=str(item.get("label") or item.get("title") or "context"),
                content=json.dumps(item, ensure_ascii=False)[:4000],
            )
        )
    return out
