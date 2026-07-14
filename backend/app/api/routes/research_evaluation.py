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
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-evaluation"])

_service: ResearchEvaluationService | None = None


def get_research_evaluation_service() -> ResearchEvaluationService:
    global _service
    if _service is None:
        # Evaluation depends only on the shared ValidationResultStore — it
        # has no MarketDataPort and no ResearchValidationService dependency,
        # so it cannot trigger a new Validation run.
        _service = ResearchEvaluationService(get_default_validation_result_store())
    return _service


@router.post("/evaluation", response_model=ResearchEvaluationResponse)
def evaluate_research(
    body: ResearchEvaluationRequest,
) -> ResearchEvaluationResponse:
    """Summarize an existing PR-009 ValidationResult; never recalculates."""
    try:
        result = get_research_evaluation_service().execute(body.model_dump())
    except ResearchEvaluationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchEvaluationResponse(**result)
