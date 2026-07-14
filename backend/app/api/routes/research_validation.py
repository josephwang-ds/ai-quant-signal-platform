"""POST /api/v1/research/validation transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter
from app.research_validation.result_store import get_default_validation_result_store
from app.research_validation.schemas import (
    ResearchValidationRequest,
    ResearchValidationResponse,
)
from app.research_validation.service import (
    ResearchValidationError,
    ResearchValidationService,
)

router = APIRouter(prefix="/api/v1/research", tags=["research-validation"])

_service: ResearchValidationService | None = None


def get_research_validation_service() -> ResearchValidationService:
    global _service
    if _service is None:
        _service = ResearchValidationService(
            YahooFinanceMarketDataAdapter(),
            get_default_validation_result_store(),
        )
    return _service


@router.post("/validation", response_model=ResearchValidationResponse)
def validate_research(
    body: ResearchValidationRequest,
) -> ResearchValidationResponse:
    """Run deterministic validation; provider failures never fabricate evidence."""
    try:
        result = get_research_validation_service().execute(body.model_dump())
    except ResearchValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchValidationResponse(**result)
