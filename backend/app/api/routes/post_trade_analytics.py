"""Deterministic post-trade analytics API."""

from fastapi import APIRouter

from app.post_trade.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AttributionRequest,
    AttributionResult,
)
from app.post_trade.service import detect_anomalies, run_performance_attribution

router = APIRouter(prefix="/api/v1/post-trade", tags=["post-trade-analytics"])


@router.post("/attribution", response_model=AttributionResult)
def performance_attribution(request: AttributionRequest) -> AttributionResult:
    return run_performance_attribution(request)


@router.post("/anomalies", response_model=AnomalyDetectionResult)
def anomaly_detection(request: AnomalyDetectionRequest) -> AnomalyDetectionResult:
    return detect_anomalies(request)
