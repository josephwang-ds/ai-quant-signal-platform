"""Research Copilot application service — evidence interpretation only."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from app.research_copilot.canonical_notebook import CANONICAL_RESEARCH_ID
from app.research_copilot.citations import (
    build_context_index,
    resolve_selected_citations,
)
from app.research_copilot.context_assembler import ResearchContextAssembler
from app.research_copilot.llm_config import (
    LlmConfigurationError,
    resolve_llm_provider_settings,
)
from app.research_copilot.llm_port import LlmPort
from app.research_copilot.llm_response import parse_structured_llm_response
from app.research_copilot.openai_adapter import (
    OpenAiCompatibleLlmAdapter,
    ProviderAuthenticationError,
    ProviderMalformedResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.research_copilot.retrieval import RetrievalIndex
from app.research_copilot.safety import evaluate_answer
from app.research_copilot.system_policy import COPILOT_SYSTEM_POLICY
from app.research_evaluation.service import ResearchEvaluationService
from app.research_execution.market_data_port import utc_now_iso
from app.research_execution.service import RESEARCH_ID_PATTERN
from app.research_validation.result_store import ValidationResultStore

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000


class ResearchCopilotError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def resolve_llm_adapter() -> LlmPort:
    """Resolve the single configured OpenAI-compatible Copilot provider."""
    try:
        settings = resolve_llm_provider_settings()
    except LlmConfigurationError as exc:
        raise ResearchCopilotError(str(exc), status_code=503) from exc
    return OpenAiCompatibleLlmAdapter(settings=settings)


class ResearchCopilotService:
    """Explain assembled workspace evidence — never calculates or mutates it."""

    def __init__(
        self,
        store: ValidationResultStore,
        evaluation_service: ResearchEvaluationService,
        llm: LlmPort,
        *,
        assembler: ResearchContextAssembler | None = None,
    ) -> None:
        self.store = store
        self.evaluation_service = evaluation_service
        self.llm = llm
        self.assembler = assembler or ResearchContextAssembler(RetrievalIndex())

    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        research_id = str(request.get("research_id", CANONICAL_RESEARCH_ID) or "").strip()
        if not RESEARCH_ID_PATTERN.fullmatch(research_id):
            raise ResearchCopilotError(
                "research_id must contain 1-128 letters, numbers, dots, "
                "underscores, or hyphens."
            )

        question = str(request.get("question") or "").strip()
        if not question:
            raise ResearchCopilotError("question is required.")
        if len(question) > MAX_QUESTION_LENGTH:
            raise ResearchCopilotError(
                f"question must be at most {MAX_QUESTION_LENGTH} characters."
            )

        validation_run_id = str(request.get("validation_run_id") or "").strip()
        if not validation_run_id:
            raise ResearchCopilotError(
                "validation_run_id is required. Run or load Validation evidence "
                "before asking evidence-specific questions.",
                status_code=400,
            )

        stored = self.store.get(validation_run_id)
        if stored is None:
            raise ResearchCopilotError(
                f"Unknown validation_run_id '{validation_run_id}'. Run or load "
                "Validation evidence before asking evidence-specific questions.",
                status_code=404,
            )
        if stored.get("research_id") != research_id:
            raise ResearchCopilotError(
                "validation_run_id does not belong to the requested research_id.",
                status_code=400,
            )

        evaluation = self.evaluation_service.execute(
            {
                "research_id": research_id,
                "validation_run_id": validation_run_id,
            }
        )
        structured, context_items = self.assembler.assemble(
            research_id=research_id,
            question=question,
            validation=stored,
            evaluation=evaluation,
        )
        context_index = build_context_index(context_items)
        context_blob = json.dumps(structured, ensure_ascii=False)

        history = request.get("conversation") or []
        history_lines = []
        for turn in history[-4:]:
            if isinstance(turn, dict):
                history_lines.append(
                    f"{turn.get('role', 'user')}: {turn.get('content', '')}"
                )
        user_prompt = question
        if history_lines:
            user_prompt = (
                "Recent conversation:\n"
                + "\n".join(history_lines)
                + f"\n\nCurrent question:\n{question}"
            )

        try:
            llm_result = self.llm.generate(
                system_prompt=COPILOT_SYSTEM_POLICY,
                user_prompt=user_prompt,
                context=context_items,
            )
        except ProviderTimeoutError as exc:
            raise ResearchCopilotError(
                "Research Copilot timed out while waiting for the language model.",
                status_code=504,
            ) from exc
        except ProviderAuthenticationError as exc:
            raise ResearchCopilotError(
                "Research Copilot provider authentication failed.",
                status_code=502,
            ) from exc
        except ProviderMalformedResponseError as exc:
            raise ResearchCopilotError(
                "Research Copilot provider returned a malformed response.",
                status_code=502,
            ) from exc
        except ProviderUnavailableError as exc:
            message = str(exc).strip() or (
                "Research Copilot provider is currently unavailable."
            )
            if "rate limited" in message.lower():
                raise ResearchCopilotError(
                    "Research Copilot provider is rate limited.",
                    status_code=502,
                ) from exc
            raise ResearchCopilotError(
                "Research Copilot provider is currently unavailable.",
                status_code=502,
            ) from exc

        parsed = parse_structured_llm_response(llm_result.text)
        citations, citation_warnings = resolve_selected_citations(
            parsed.citation_ids,
            context_index,
        )

        verdict = evaluate_answer(
            parsed.answer,
            citations=[item.model_dump() for item in citations],
            context_blob=context_blob,
        )

        warning_codes = list(parsed.warnings) + citation_warnings + verdict.warnings
        grounding_status = verdict.grounding_status
        if (
            parsed.citation_ids
            and not citations
            and parsed.answer
            and len(parsed.answer) > 80
            and grounding_status == "grounded"
        ):
            grounding_status = "partially_grounded"
            warning_codes.append("unresolved_citation_ids")

        warnings = [
            {"code": warning, "message": _warning_message(warning)}
            for warning in _dedupe(warning_codes)
        ]
        answer = verdict.sanitized_answer or (
            "Research Copilot could not return a safe grounded answer."
        )

        logger.info(
            "research_copilot_query",
            extra={
                "request_id": request_id,
                "research_id": research_id,
                "model": llm_result.model,
                "grounding_status": grounding_status,
                "latency_ms": llm_result.latency_ms,
                "citation_count": len(citations),
                "failure_category": None if verdict.safe else "policy_block",
            },
        )

        return {
            "research_id": research_id,
            "answer": answer,
            "citations": [item.model_dump() for item in citations],
            "warnings": warnings,
            "grounding_status": grounding_status,
            "model": llm_result.model,
            "generated_at": utc_now_iso(),
        }


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _warning_message(code: str) -> str:
    if code == "unsupported_numeric_claim":
        return (
            "The answer may include numbers not present in the assembled evidence."
        )
    if code == "missing_citations":
        return "The answer did not include valid evidence citations."
    if code == "missing_citation_ids":
        return "The model response did not include citation_ids."
    if code == "invalid_structured_output":
        return "The model response was not valid structured JSON."
    if code == "unresolved_citation_ids":
        return "None of the cited evidence IDs matched the assembled context."
    if code.startswith("unknown_citation_id:"):
        return "The model cited evidence that was not present in the assembled context."
    if code.startswith("prohibited_language"):
        return "Investment recommendation language was blocked."
    if code == "empty_answer":
        return "The language model returned an empty answer."
    return code
