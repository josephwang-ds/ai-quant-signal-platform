"""POST /api/v1/research/factor-validation transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.factor_validation.schemas import (
    FactorValidationRequest,
    FactorValidationResponse,
)
from app.factor_validation.service import (
    FactorValidationError,
    FactorValidationService,
)
from app.research_execution.market_data_router import build_default_market_data_port
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-factor-validation"])

_service: FactorValidationService | None = None


def get_factor_validation_service() -> FactorValidationService:
    global _service
    if _service is None:
        _service = FactorValidationService(
            build_default_market_data_port(),
            get_default_validation_result_store(),
        )
    return _service


@router.post("/factor-validation", response_model=FactorValidationResponse)
def validate_factor_research(
    body: FactorValidationRequest,
) -> FactorValidationResponse:
    """Run deterministic factor validation; never fabricates evidence."""
    try:
        result = get_factor_validation_service().execute(body.model_dump())
    except FactorValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return FactorValidationResponse(**result)
