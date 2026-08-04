"""Typed contracts for deterministic post-trade analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _finite(value: float) -> float:
    number = float(value)
    if not isfinite(number):
        raise ValueError("numeric values must be finite")
    return number


class InputDataKind(str, Enum):
    OPERATOR_SUPPLIED = "operator_supplied"
    SYNTHETIC_DEMO = "synthetic_demo"


class AttributionObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trade_id: str = Field(min_length=1, max_length=80)
    timestamp: datetime
    strategy: str = Field(min_length=1, max_length=80)
    venue: str = Field(min_length=1, max_length=40)
    notional_usd: float = Field(gt=0)
    gross_pnl_bps: float
    benchmark_pnl_bps: float = 0.0
    fees_bps: float = Field(ge=0)
    slippage_bps: float = Field(ge=0)

    @field_validator("timestamp")
    @classmethod
    def _timestamp(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @field_validator(
        "notional_usd",
        "gross_pnl_bps",
        "benchmark_pnl_bps",
        "fees_bps",
        "slippage_bps",
    )
    @classmethod
    def _numbers(cls, value: float) -> float:
        return _finite(value)

    @field_validator("trade_id", "strategy", "venue")
    @classmethod
    def _text(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("text fields must be unpadded")
        return value


class AttributionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[AttributionObservation] = Field(min_length=2, max_length=5_000)
    group_by: Literal["strategy", "venue"] = "venue"
    input_data_kind: InputDataKind = InputDataKind.OPERATOR_SUPPLIED

    @model_validator(mode="after")
    def _unique_trades(self) -> "AttributionRequest":
        trade_ids = [item.trade_id for item in self.observations]
        if len(trade_ids) != len(set(trade_ids)):
            raise ValueError("trade_id values must be unique")
        return self


class AttributionComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: Literal["gross_edge", "fees", "slippage", "net_active"]
    label: str
    contribution_bps: float
    contribution_usd: float


class AttributionGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group: str
    observation_count: int
    notional_usd: float
    gross_edge_bps: float
    fee_drag_bps: float
    slippage_drag_bps: float
    net_active_bps: float
    net_active_usd: float


class AttributionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology: str
    input_data_kind: InputDataKind
    group_by: Literal["strategy", "venue"]
    observation_count: int
    total_notional_usd: float
    gross_edge_bps: float
    fee_drag_bps: float
    slippage_drag_bps: float
    net_active_bps: float
    net_active_usd: float
    reconciliation_error_usd: float
    components: list[AttributionComponent]
    groups: list[AttributionGroup]


class DetectionDirection(str, Enum):
    HIGH = "high"
    LOW = "low"
    TWO_SIDED = "two_sided"


class MetricObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    metric: str = Field(min_length=1, max_length=80)
    entity: str = Field(min_length=1, max_length=80)
    value: float

    @field_validator("timestamp")
    @classmethod
    def _timestamp(cls, value: datetime) -> datetime:
        return _aware_utc(value)

    @field_validator("value")
    @classmethod
    def _value(cls, value: float) -> float:
        return _finite(value)

    @field_validator("metric", "entity")
    @classmethod
    def _text(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("text fields must be unpadded")
        return value


class AnomalyDetectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[MetricObservation] = Field(min_length=6, max_length=10_000)
    baseline_window: int = Field(default=12, ge=5, le=500)
    minimum_history: int = Field(default=5, ge=5, le=100)
    threshold: float = Field(default=3.5, ge=2.0, le=12.0)
    direction: DetectionDirection = DetectionDirection.HIGH
    input_data_kind: InputDataKind = InputDataKind.OPERATOR_SUPPLIED

    @model_validator(mode="after")
    def _window_consistency(self) -> "AnomalyDetectionRequest":
        if self.minimum_history > self.baseline_window:
            raise ValueError("minimum_history must be <= baseline_window")
        return self


class AnomalyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    metric: str
    entity: str
    value: float
    baseline_median: float
    robust_scale: float
    robust_z_score: float
    severity: Literal["warning", "critical"]
    history_count: int


class ScoredMetricPoint(BaseModel):
    """Per-observation detector trace for auditable monitoring charts."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    metric: str
    entity: str
    value: float
    baseline_median: Optional[float] = None
    upper_threshold: Optional[float] = None
    lower_threshold: Optional[float] = None
    robust_z_score: Optional[float] = None
    status: Literal["warmup", "normal", "warning", "critical"]


class MetricSeriesSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    entity: str
    observation_count: int
    scored_count: int
    anomaly_count: int
    latest_value: float
    latest_baseline_median: Optional[float] = None
    latest_robust_z_score: Optional[float] = None
    status: Literal["normal", "warning", "critical", "insufficient_history"]


class AnomalyDetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    methodology: str
    input_data_kind: InputDataKind
    baseline_window: int
    minimum_history: int
    threshold: float
    direction: DetectionDirection
    observation_count: int
    scored_count: int
    anomaly_count: int
    points: list[ScoredMetricPoint]
    anomalies: list[AnomalyEvent]
    series: list[MetricSeriesSummary]
