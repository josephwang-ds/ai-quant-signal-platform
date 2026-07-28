"""POST /api/v1/research/cross-sectional/models transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cross_sectional.modeling.schemas import (
    CrossSectionalModelingRequest,
    CrossSectionalModelingResponse,
)
from app.cross_sectional.modeling.service import (
    CrossSectionalModelingError,
    CrossSectionalModelingService,
)
from app.research_execution.market_data_router import build_default_market_data_port
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-cross-sectional-models"])

_service: CrossSectionalModelingService | None = None


def get_cross_sectional_modeling_service() -> CrossSectionalModelingService:
    global _service
    if _service is None:
        _service = CrossSectionalModelingService(
            build_default_market_data_port(),
            get_default_validation_result_store(),
        )
    return _service


@router.post(
    "/cross-sectional/models",
    response_model=CrossSectionalModelingResponse,
)
def run_cross_sectional_modeling(
    body: CrossSectionalModelingRequest,
) -> CrossSectionalModelingResponse:
    """Leakage-safe walk-forward modeling → OOS daily stock scores (no portfolio)."""
    from app.security.settings import get_demo_protection_settings
    from app.security.timeouts import OperationTimeoutError, run_with_timeout

    payload = body.model_dump()
    timeout = get_demo_protection_settings().validation_timeout_seconds
    try:
        result = run_with_timeout(
            lambda: get_cross_sectional_modeling_service().execute(payload),
            timeout_seconds=timeout,
            message=(
                "Cross-sectional modeling exceeded the demo time budget. "
                "Narrow universe, date range, or model set and retry shortly."
            ),
        )
    except OperationTimeoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except CrossSectionalModelingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return CrossSectionalModelingResponse(**result)
