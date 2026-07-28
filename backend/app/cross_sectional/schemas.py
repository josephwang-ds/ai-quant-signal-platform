"""Transport contracts for the cross-sectional factor dataset API."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.cross_sectional.constants import (
    DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
    DEFAULT_PREVIEW_ROWS,
    MAX_PREVIEW_ROWS,
    MAX_REQUEST_SYMBOLS,
    MIN_HISTORY_DAYS,
    UNIVERSE_ID_LIQUID_31,
)


class CrossSectionalDatasetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "cross-sectional-equity-liquid-v1"
    universe_id: str = UNIVERSE_ID_LIQUID_31
    symbols: Optional[list[str]] = Field(default=None, max_length=MAX_REQUEST_SYMBOLS)
    benchmark: str = "SPY"
    start_date: str = "2019-01-01"
    end_date: Optional[str] = None
    min_history_days: int = Field(default=MIN_HISTORY_DAYS, ge=20, le=252)
    liquidity_dollar_volume_floor: float = Field(
        default=DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
        ge=0,
    )
    preview_rows: int = Field(default=DEFAULT_PREVIEW_ROWS, ge=0, le=MAX_PREVIEW_ROWS)

    @field_validator("symbols")
    @classmethod
    def _limit_symbols(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        if len(value) > MAX_REQUEST_SYMBOLS:
            raise ValueError(
                f"symbols must contain at most {MAX_REQUEST_SYMBOLS} tickers."
            )
        return value

    @model_validator(mode="after")
    def _validate_date_order(self) -> "CrossSectionalDatasetRequest":
        if self.end_date:
            try:
                start = date.fromisoformat(str(self.start_date).strip())
                end = date.fromisoformat(str(self.end_date).strip())
            except ValueError as exc:
                raise ValueError(
                    "start_date and end_date must be ISO dates (YYYY-MM-DD)."
                ) from exc
            if start >= end:
                raise ValueError("start_date must be earlier than end_date.")
        return self


class CrossSectionalDatasetResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    template: str
    evidence_kind: str
    dataset_run_id: str
    configuration: dict[str, Any]
    dataset_summary: dict[str, Any]
    quality_summary: dict[str, Any]
    coverage_summary: dict[str, Any]
    feature_metadata: list[dict[str, Any]]
    records_preview: list[dict[str, Any]]
    unavailable_evidence: list[str]
    warnings: list[str]
    provenance: dict[str, Any]
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)
    generated_at: str
    validation_status: str = "completed"
