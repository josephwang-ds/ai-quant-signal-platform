"""POST /api/v1/research/evaluation transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_evaluation.schemas import (
    ResearchEvaluationRequest,
    ResearchEvaluationResponse,
)
from app.research_evaluation.service import (
    ResearchEvaluationError,
    ResearchEvaluationService,
)
from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter
from app.research_validation.service import ResearchValidationService

router = APIRouter(prefix="/api/v1/research", tags=["research-evaluation"])

_service: ResearchEvaluationService | None = None


def get_research_evaluation_service() -> ResearchEvaluationService:
    global _service
    if _service is None:
        validation_service = ResearchValidationService(
            YahooFinanceMarketDataAdapter()
        )
        _service = ResearchEvaluationService(validation_service)
    return _service


@router.post("/evaluation", response_model=ResearchEvaluationResponse)
def evaluate_research(
    body: ResearchEvaluationRequest,
) -> ResearchEvaluationResponse:
    """Summarize existing PR-009 evidence; never recalculates, never recommends."""
    try:
        result = get_research_evaluation_service().execute(body.model_dump())
    except ResearchEvaluationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchEvaluationResponse(**result)
