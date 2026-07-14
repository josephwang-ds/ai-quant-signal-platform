"""POST /api/v1/research/execution"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.research_execution.schemas import (
    ResearchExecutionRequest,
    ResearchExecutionResponse,
)
from app.research_execution.service import (
    ResearchExecutionError,
    ResearchExecutionService,
)
from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter

router = APIRouter(prefix="/api/v1/research", tags=["research-execution"])

_service: ResearchExecutionService | None = None


def get_research_execution_service() -> ResearchExecutionService:
    global _service
    if _service is None:
        _service = ResearchExecutionService(YahooFinanceMarketDataAdapter())
    return _service


@router.post("/execution", response_model=ResearchExecutionResponse)
def execute_research(body: ResearchExecutionRequest) -> ResearchExecutionResponse:
    """
    Run the canonical MA crossover research execution on historical market data.

    Synchronous MVP. Provider failures never invent fallback metrics.
    """
    service = get_research_execution_service()
    try:
        result = service.execute(body.model_dump())
    except ResearchExecutionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return ResearchExecutionResponse(**result)
