"""Research Copilot application service — evidence interpretation only."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from app.research_copilot.canonical_notebook import CANONICAL_RESEARCH_ID
from app.research_copilot.context_assembler import ResearchContextAssembler
from app.research_copilot.fake_llm import DEFAULT_FAKE_MODEL, FakeLlmAdapter
from app.research_copilot.llm_port import LlmPort
from app.research_copilot.openai_adapter import (
    OpenAiLlmAdapter,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.research_copilot.retrieval import RetrievalIndex
from app.research_copilot.safety import evaluate_answer
from app.research_copilot.schemas import EvidenceCitation
from app.research_copilot.system_policy import COPILOT_SYSTEM_POLICY
from app.research_evaluation.service import ResearchEvaluationService
from app.research_execution.market_data_port import utc_now_iso
from app.research_validation.result_store import ValidationResultStore

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 1000


class ResearchCopilotError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def resolve_llm_adapter() -> LlmPort:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        return OpenAiLlmAdapter(api_key=api_key)
    raise ResearchCopilotError(
        "Research Copilot is not configured for this deployment.",
        status_code=503,
    )


def resolve_llm_adapter_for_runtime(*, allow_fake: bool = False) -> LlmPort:
    try:
        return resolve_llm_adapter()
    except ResearchCopilotError:
        if allow_fake or os.getenv("COPILOT_ALLOW_FAKE_LLM", "").strip().lower() in {
            "1",
            "true",
            "yes",
        }:
            return FakeLlmAdapter()
        raise


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
        if research_id != CANONICAL_RESEARCH_ID:
            raise ResearchCopilotError(
                f"Unsupported research_id '{research_id}'. "
                f"Supported: ['{CANONICAL_RESEARCH_ID}']."
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
        except ProviderUnavailableError as exc:
            raise ResearchCopilotError(
                "Research Copilot provider is currently unavailable.",
                status_code=502,
            ) from exc

        citations = _build_citations(structured, evaluation, validation_run_id)
        verdict = evaluate_answer(
            llm_result.text,
            citations=[item.model_dump() for item in citations],
            context_blob=context_blob,
        )
        warnings = [
            {"code": warning, "message": _warning_message(warning)}
            for warning in verdict.warnings
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
                "grounding_status": verdict.grounding_status,
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
            "grounding_status": verdict.grounding_status,
            "model": llm_result.model,
            "generated_at": utc_now_iso(),
        }


def _build_citations(
    structured: dict[str, Any],
    evaluation: dict[str, Any],
    validation_run_id: str,
) -> list[EvidenceCitation]:
    citations: list[EvidenceCitation] = []
    eval_status = evaluation.get("evaluation_status")
    if eval_status:
        citations.append(
            EvidenceCitation(
                source_type="evaluation",
                source_id=validation_run_id,
                label="Evaluation status",
                excerpt=f"evaluation_status={eval_status}",
            )
        )
    outstanding = evaluation.get("outstanding_evidence") or []
    if outstanding:
        citations.append(
            EvidenceCitation(
                source_type="evaluation",
                source_id=validation_run_id,
                label="Outstanding evidence",
                excerpt="; ".join(str(item) for item in outstanding[:4]),
            )
        )
    for stage in structured.get("validation_evidence", {}).get("stages", [])[:4]:
        citations.append(
            EvidenceCitation(
                source_type="validation",
                source_id=validation_run_id,
                label=str(stage.get("label") or stage.get("stage")),
                excerpt=str(stage.get("summary") or stage.get("status")),
            )
        )
    if not citations:
        citations.append(
            EvidenceCitation(
                source_type="research_definition",
                source_id=CANONICAL_RESEARCH_ID,
                label="Research definition",
                excerpt=str(
                    structured.get("research_definition", {}).get(
                        "research_question", ""
                    )
                )[:240],
            )
        )
    return citations


def _warning_message(code: str) -> str:
    if code == "unsupported_numeric_claim":
        return (
            "The answer may include numbers not present in the assembled evidence."
        )
    if code == "missing_citations":
        return "The answer did not include enough explicit evidence citations."
    if code.startswith("prohibited_language"):
        return "Investment recommendation language was blocked."
    if code == "empty_answer":
        return "The language model returned an empty answer."
    return code
