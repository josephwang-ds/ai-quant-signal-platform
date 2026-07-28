"""Transport contracts for Phase 2 cross-sectional factor research."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.cross_sectional.constants import (
    DEFAULT_CORRELATION_WARNING_THRESHOLD,
    DEFAULT_MIN_CROSS_SECTION_SIZE,
    DEFAULT_MIN_QUANTILE_SIZE,
    DEFAULT_MIN_STABILITY_PERIOD_DATES,
    DEFAULT_MIN_TURNOVER_OVERLAP,
    DEFAULT_QUANTILE_COUNT,
    DEFAULT_RESEARCH_PREVIEW_ROWS,
    LABEL_COLUMNS,
    MAX_REQUEST_SYMBOLS,
    MAX_RESEARCH_PREVIEW_ROWS,
    RESEARCH_FACTOR_COLUMNS,
    UNIVERSE_ID_LIQUID_31,
)


class CrossSectionalFactorResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "cross-sectional-factor-research-v1"
    universe_id: str = UNIVERSE_ID_LIQUID_31
    symbols: Optional[list[str]] = Field(default=None, max_length=MAX_REQUEST_SYMBOLS)
    start_date: str = "2019-01-01"
    end_date: Optional[str] = None
    factor_columns: Optional[list[str]] = None
    label_horizons: list[int] = Field(default_factory=lambda: [5, 20])
    quantile_count: int = Field(default=DEFAULT_QUANTILE_COUNT, ge=2, le=10)
    minimum_cross_section_size: int = Field(
        default=DEFAULT_MIN_CROSS_SECTION_SIZE, ge=3, le=100
    )
    minimum_quantile_size: int = Field(default=DEFAULT_MIN_QUANTILE_SIZE, ge=1, le=20)
    apply_liquidity_filter: bool = False
    correlation_warning_threshold: float = Field(
        default=DEFAULT_CORRELATION_WARNING_THRESHOLD, ge=0.0, le=1.0
    )
    minimum_turnover_overlap: int = Field(
        default=DEFAULT_MIN_TURNOVER_OVERLAP, ge=2, le=100
    )
    minimum_stability_period_dates: int = Field(
        default=DEFAULT_MIN_STABILITY_PERIOD_DATES, ge=1, le=252
    )
    preview_rows: int = Field(
        default=DEFAULT_RESEARCH_PREVIEW_ROWS, ge=0, le=MAX_RESEARCH_PREVIEW_ROWS
    )
    liquidity_dollar_volume_floor: float = Field(default=5_000_000.0, ge=0)

    @field_validator("factor_columns")
    @classmethod
    def _validate_factors(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        allowed = set(RESEARCH_FACTOR_COLUMNS)
        bad = [f for f in value if f not in allowed]
        if bad:
            raise ValueError(
                f"Unsupported factor_columns: {bad}. Allowed: {sorted(allowed)}"
            )
        if "liquidity_eligible" in value:
            raise ValueError(
                "liquidity_eligible is an eligibility filter, not a research factor."
            )
        return value

    @field_validator("label_horizons")
    @classmethod
    def _validate_horizons(cls, value: list[int]) -> list[int]:
        allowed = {5, 20}
        bad = [h for h in value if h not in allowed]
        if bad:
            raise ValueError(
                f"Unsupported label_horizons: {bad}. Allowed: {sorted(allowed)}"
            )
        if not value:
            raise ValueError("label_horizons must not be empty.")
        # preserve order, dedupe
        out: list[int] = []
        for h in value:
            if h not in out:
                out.append(h)
        return out

    @model_validator(mode="after")
    def _validate_dates_and_sizes(self) -> "CrossSectionalFactorResearchRequest":
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
        min_needed = self.quantile_count * self.minimum_quantile_size
        if self.minimum_cross_section_size < min_needed:
            raise ValueError(
                "minimum_cross_section_size must be >= quantile_count * minimum_quantile_size "
                f"({min_needed})."
            )
        return self


class CrossSectionalFactorResearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    template: str
    evidence_kind: str
    research_run_id: str
    configuration: dict[str, Any]
    dataset_summary: dict[str, Any]
    eligibility_summary: dict[str, Any]
    rank_ic_summary: dict[str, Any]
    quintile_summary: dict[str, Any]
    spread_summary: dict[str, Any]
    decay_summary: dict[str, Any]
    turnover_summary: dict[str, Any]
    correlation_summary: dict[str, Any]
    stability_summary: dict[str, Any]
    factor_summaries: list[dict[str, Any]]
    unavailable_evidence: list[str]
    previews: dict[str, Any]
    warnings: list[str]
    provenance: dict[str, Any]
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)
    generated_at: str
    validation_status: str = "completed"
