"""Read-only Intelligence Query API (Phase 4.5)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.intelligence.schemas import ResearchRunStatus, ResearchRunType
from app.intelligence_serving.deps import get_intelligence_service
from app.intelligence_serving.dto import (
    ArtifactListDTO,
    IntelligenceErrorDTO,
    ResearchRunDetailDTO,
    RunListDTO,
    SnapshotContentDTO,
    SnapshotListDTO,
)
from app.intelligence_serving.errors import IntelligenceServingError
from app.intelligence_serving.service import IntelligenceService, parse_snapshot_type

router = APIRouter(prefix="/api/v1/intelligence", tags=["intelligence"])


def _http_error(exc: IntelligenceServingError) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail=IntelligenceErrorDTO(
            error_code=exc.error_code,
            message=exc.message,
            run_id=exc.run_id,
            resource_id=exc.resource_id,
        ).model_dump(exclude_none=True),
    )


@router.get("/runs", response_model=RunListDTO)
def list_runs(
    status: Optional[ResearchRunStatus] = Query(default=None),
    run_type: Optional[ResearchRunType] = Query(default=None),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> RunListDTO:
    try:
        return service.list_runs(status=status, run_type=run_type)
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc


@router.get("/runs/latest", response_model=ResearchRunDetailDTO)
def get_latest_run(
    service: IntelligenceService = Depends(get_intelligence_service),
) -> ResearchRunDetailDTO:
    """Static path must be registered before ``/runs/{run_id}``."""
    try:
        return service.get_latest_run()
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc


@router.get("/runs/{run_id}", response_model=ResearchRunDetailDTO)
def get_run(
    run_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> ResearchRunDetailDTO:
    try:
        return service.get_run(run_id)
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc


@router.get("/runs/{run_id}/artifacts", response_model=ArtifactListDTO)
def list_artifacts(
    run_id: str,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> ArtifactListDTO:
    try:
        return service.list_artifacts(run_id)
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc


@router.get("/runs/{run_id}/snapshots", response_model=SnapshotListDTO)
def list_snapshots(
    run_id: str,
    snapshot_type: Optional[str] = Query(default=None),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> SnapshotListDTO:
    try:
        parsed = parse_snapshot_type(snapshot_type)
        return service.list_snapshots(run_id, snapshot_type=parsed)
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/runs/{run_id}/snapshots/{snapshot_name_or_id}",
    response_model=SnapshotContentDTO,
)
def get_snapshot_content(
    run_id: str,
    snapshot_name_or_id: str,
    verify: bool = Query(default=False),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> SnapshotContentDTO:
    try:
        return service.get_snapshot_content(
            run_id,
            snapshot_name_or_id,
            verify=verify,
        )
    except IntelligenceServingError as exc:
        raise _http_error(exc) from exc
