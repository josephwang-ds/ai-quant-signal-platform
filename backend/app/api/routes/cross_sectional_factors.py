"""POST /api/v1/research/cross-sectional/factors transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cross_sectional.research.schemas import (
    CrossSectionalFactorResearchRequest,
    CrossSectionalFactorResearchResponse,
)
from app.cross_sectional.research.service import (
    CrossSectionalFactorResearchError,
    CrossSectionalFactorResearchService,
)
from app.research_execution.market_data_router import build_default_market_data_port
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-cross-sectional-factors"])

_service: CrossSectionalFactorResearchService | None = None


def get_cross_sectional_factor_research_service() -> CrossSectionalFactorResearchService:
    global _service
    if _service is None:
        _service = CrossSectionalFactorResearchService(
            build_default_market_data_port(),
            get_default_validation_result_store(),
        )
    return _service


@router.post(
    "/cross-sectional/factors",
    response_model=CrossSectionalFactorResearchResponse,
)
def run_cross_sectional_factor_research(
    body: CrossSectionalFactorResearchRequest,
) -> CrossSectionalFactorResearchResponse:
    """Deterministic factor research on a Phase 1 panel — no model training."""
    from app.security.settings import get_demo_protection_settings
    from app.security.timeouts import OperationTimeoutError, run_with_timeout

    payload = body.model_dump()
    timeout = get_demo_protection_settings().validation_timeout_seconds
    try:
        result = run_with_timeout(
            lambda: get_cross_sectional_factor_research_service().execute(payload),
            timeout_seconds=timeout,
            message=(
                "Cross-sectional factor research exceeded the demo time budget. "
                "Narrow factors, universe, or date range and retry shortly."
            ),
        )
    except OperationTimeoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except CrossSectionalFactorResearchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return CrossSectionalFactorResearchResponse(**result)
