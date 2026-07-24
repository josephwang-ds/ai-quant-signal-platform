"""LLM bridge — reuses research_copilot LlmPort; no second HTTP client."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.research_copilot.safety import evaluate_answer
from app.research_agent.prompts import GOVERNANCE_SYSTEM_V1

OutputModel = TypeVar("OutputModel", bound=BaseModel)


class AgentLlmUnavailable(Exception):
    pass


class AgentStructuredOutputError(ValueError):
    pass


def _json_object(raw_text: str) -> dict[str, Any]:
    normalized = raw_text.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:json)?\s*", "", normalized)
        normalized = re.sub(r"\s*```$", "", normalized)
    try:
        payload = json.loads(normalized)
    except (TypeError, json.JSONDecodeError) as exc:
        raise AgentStructuredOutputError("LLM returned invalid JSON.") from exc
    if not isinstance(payload, dict):
        raise AgentStructuredOutputError("LLM output must be a JSON object.")
    return payload


def _citation_records(payload: dict[str, Any]) -> list[dict[str, str]]:
    ids: list[str] = []

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, child_key)
        elif isinstance(value, list):
            if key in {"citation_ids", "evidence_ids", "knowledge_ids"}:
                ids.extend(str(item) for item in value if str(item).strip())
            else:
                for child in value:
                    visit(child, key)

    visit(payload)
    return [{"citation_id": item} for item in dict.fromkeys(ids)]


def generate_structured(
    llm: LlmPort | None,
    *,
    user_prompt: str,
    context_items: list[ContextItem] | None = None,
    system_prompt: str = GOVERNANCE_SYSTEM_V1,
    response_model: type[OutputModel] | None = None,
    trusted_context: str = "",
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
    raw_payload = _json_object(result.text)
    try:
        payload = (
            response_model.model_validate(raw_payload).model_dump()
            if response_model is not None
            else raw_payload
        )
    except ValidationError as exc:
        raise AgentStructuredOutputError(
            "LLM output did not match the requested action schema."
        ) from exc

    context_blob = json.dumps(
        [item.content for item in (context_items or [])],
        ensure_ascii=False,
    ) + trusted_context
    answer_text = json.dumps(payload, ensure_ascii=False)
    verdict = evaluate_answer(
        answer_text,
        citations=_citation_records(payload),
        context_blob=context_blob,
        allow_governance_hold=True,
    )
    if not verdict.safe or "unsupported_numeric_claim" in verdict.warnings:
        warnings.extend(verdict.warnings)
        payload["_safety_blocked"] = True
        payload["_sanitized_answer"] = verdict.sanitized_answer

    return payload, result, warnings


def context_from_dicts(items: list[dict[str, Any]]) -> list[ContextItem]:
    out: list[ContextItem] = []
    for item in items:
        out.append(
            ContextItem(
                citation_id=str(
                    item.get("citation_id")
                    or item.get("knowledge_id")
                    or item.get("id")
                    or "ctx"
                ),
                source_type=str(item.get("source_type") or "agent"),
                source_id=str(item.get("source_id") or item.get("knowledge_id") or "agent"),
                label=str(item.get("label") or item.get("title") or "context"),
                content=json.dumps(item, ensure_ascii=False)[:4000],
            )
        )
    return out
