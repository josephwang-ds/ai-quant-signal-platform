"""POST /api/v1/research/copilot/query transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_copilot.schemas import ResearchCopilotRequest, ResearchCopilotResponse
from app.research_copilot.service import ResearchCopilotError, ResearchCopilotService
from app.research_evaluation.service import ResearchEvaluationService
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-copilot"])

_service: ResearchCopilotService | None = None
_llm_override = None


def get_research_copilot_service() -> ResearchCopilotService:
    global _service, _llm_override
    if _service is None:
        from app.research_copilot.service import resolve_llm_adapter_for_runtime

        llm = _llm_override or resolve_llm_adapter_for_runtime()
        store = get_default_validation_result_store()
        _service = ResearchCopilotService(
            store,
            ResearchEvaluationService(store),
            llm,
        )
    return _service


def set_research_copilot_service(service: ResearchCopilotService | None) -> None:
    global _service, _llm_override
    _service = service
    _llm_override = None


def set_research_copilot_llm_override(llm) -> None:
    global _llm_override, _service
    _llm_override = llm
    _service = None


@router.post("/copilot/query", response_model=ResearchCopilotResponse)
def query_research_copilot(
    body: ResearchCopilotRequest,
) -> ResearchCopilotResponse:
    """Explain existing workspace evidence; never calculates or recommends."""
    try:
        result = get_research_copilot_service().execute(body.model_dump())
    except ResearchCopilotError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchCopilotResponse(**result)
