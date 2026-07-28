"""POST /api/v1/research/cross-sectional/dataset transport adapter."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cross_sectional.dataset import (
    CrossSectionalDatasetError,
    CrossSectionalDatasetService,
)
from app.cross_sectional.schemas import (
    CrossSectionalDatasetRequest,
    CrossSectionalDatasetResponse,
)
from app.research_execution.market_data_router import build_default_market_data_port
from app.research_validation.result_store import get_default_validation_result_store

router = APIRouter(prefix="/api/v1/research", tags=["research-cross-sectional-dataset"])

_service: CrossSectionalDatasetService | None = None


def get_cross_sectional_dataset_service() -> CrossSectionalDatasetService:
    global _service
    if _service is None:
        _service = CrossSectionalDatasetService(
            build_default_market_data_port(),
            get_default_validation_result_store(),
        )
    return _service


@router.post(
    "/cross-sectional/dataset",
    response_model=CrossSectionalDatasetResponse,
)
def build_cross_sectional_dataset(
    body: CrossSectionalDatasetRequest,
) -> CrossSectionalDatasetResponse:
    """Build a deterministic date×symbol factor panel with quality report."""
    from app.security.settings import get_demo_protection_settings
    from app.security.timeouts import OperationTimeoutError, run_with_timeout

    payload = body.model_dump()
    timeout = get_demo_protection_settings().validation_timeout_seconds
    try:
        result = run_with_timeout(
            lambda: get_cross_sectional_dataset_service().execute(payload),
            timeout_seconds=timeout,
            message=(
                "Cross-sectional dataset build exceeded the demo time budget. "
                "Narrow the universe or date range and retry shortly."
            ),
        )
    except OperationTimeoutError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except CrossSectionalDatasetError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return CrossSectionalDatasetResponse(**result)
