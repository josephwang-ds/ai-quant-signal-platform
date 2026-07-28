"""Transport contracts for Phase 3 cross-sectional modeling."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.cross_sectional.constants import (
    MAX_REQUEST_SYMBOLS,
    UNIVERSE_ID_LIQUID_31,
)
from app.cross_sectional.modeling.constants import (
    APPROVED_MODELS,
    DEFAULT_MIN_CROSS_SECTION_SIZE,
    DEFAULT_MIN_TRAIN_DATES,
    DEFAULT_PREDICTION_BLOCK_DATES,
    DEFAULT_PREDICTION_PREVIEW_LIMIT,
    DEFAULT_RANDOM_SEED,
    DEFAULT_RIDGE_ALPHAS,
    DEFAULT_SPLIT_MODE,
    DEFAULT_VALIDATION_DATES,
    MAX_PREDICTION_PREVIEW_LIMIT,
    MODELING_FEATURE_COLUMNS,
    MODELING_LABELS,
)


class CrossSectionalModelingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "cross-sectional-modeling-v1"
    universe_id: str = UNIVERSE_ID_LIQUID_31
    symbols: Optional[list[str]] = Field(default=None, max_length=MAX_REQUEST_SYMBOLS)
    start_date: str = "2019-01-01"
    end_date: Optional[str] = None
    feature_columns: Optional[list[str]] = None
    label: str = "forward_return_5d"
    model_names: list[str] = Field(default_factory=lambda: ["ridge", "lightgbm"])
    split_mode: str = DEFAULT_SPLIT_MODE
    minimum_train_dates: int = Field(default=DEFAULT_MIN_TRAIN_DATES, ge=10, le=500)
    validation_window: int = Field(default=DEFAULT_VALIDATION_DATES, ge=5, le=120)
    prediction_window: int = Field(default=DEFAULT_PREDICTION_BLOCK_DATES, ge=5, le=120)
    minimum_validation_dates: int = Field(default=5, ge=3, le=120)
    minimum_prediction_dates: int = Field(default=5, ge=3, le=120)
    embargo_rows: Optional[int] = Field(default=None, ge=0, le=60)
    minimum_cross_section_size: int = Field(
        default=DEFAULT_MIN_CROSS_SECTION_SIZE, ge=3, le=100
    )
    apply_liquidity_filter: bool = False
    ridge_alphas: Optional[list[float]] = None
    lightgbm_parameters: Optional[list[dict[str, Any]]] = None
    random_seed: int = Field(default=DEFAULT_RANDOM_SEED, ge=0, le=2_147_483_647)
    prediction_preview_limit: int = Field(
        default=DEFAULT_PREDICTION_PREVIEW_LIMIT, ge=0, le=MAX_PREDICTION_PREVIEW_LIMIT
    )
    liquidity_dollar_volume_floor: float = Field(default=5_000_000.0, ge=0)

    @field_validator("feature_columns")
    @classmethod
    def _validate_features(cls, value: Optional[list[str]]) -> Optional[list[str]]:
        if value is None:
            return value
        allowed = set(MODELING_FEATURE_COLUMNS)
        bad = [f for f in value if f not in allowed]
        if bad:
            raise ValueError(
                f"Unsupported feature_columns: {bad}. Allowed: {sorted(allowed)}"
            )
        if "liquidity_eligible" in value:
            raise ValueError(
                "liquidity_eligible is an eligibility filter, not a model feature."
            )
        if not value:
            raise ValueError("feature_columns must not be empty.")
        return value

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        if value not in MODELING_LABELS:
            raise ValueError(
                f"Unsupported label: {value}. Allowed: {sorted(MODELING_LABELS)}"
            )
        return value

    @field_validator("model_names")
    @classmethod
    def _validate_models(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("model_names must not be empty.")
        allowed = set(APPROVED_MODELS)
        bad = [m for m in value if m not in allowed]
        if bad:
            raise ValueError(
                f"Unsupported model_names: {bad}. Allowed: {sorted(allowed)}"
            )
        out: list[str] = []
        for m in value:
            if m not in out:
                out.append(m)
        return out

    @field_validator("split_mode")
    @classmethod
    def _validate_split(cls, value: str) -> str:
        if value != DEFAULT_SPLIT_MODE:
            raise ValueError(
                f"Unsupported split_mode: {value}. Allowed: [{DEFAULT_SPLIT_MODE!r}]"
            )
        return value

    @field_validator("ridge_alphas")
    @classmethod
    def _validate_alphas(cls, value: Optional[list[float]]) -> Optional[list[float]]:
        if value is None:
            return value
        if not value:
            raise ValueError("ridge_alphas must not be empty when provided.")
        for a in value:
            if not isinstance(a, (int, float)) or float(a) <= 0 or not float(a) == float(a):
                raise ValueError(f"Invalid ridge alpha: {a}. Must be finite and > 0.")
        return [float(a) for a in value]

    @model_validator(mode="after")
    def _validate_dates(self) -> "CrossSectionalModelingRequest":
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
        if self.validation_window < self.minimum_validation_dates:
            raise ValueError(
                "validation_window must be >= minimum_validation_dates."
            )
        if self.prediction_window < self.minimum_prediction_dates:
            raise ValueError(
                "prediction_window must be >= minimum_prediction_dates."
            )
        return self


class CrossSectionalModelingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    template: str
    evidence_kind: str
    research_run_id: str
    configuration: dict[str, Any]
    dataset_summary: dict[str, Any]
    eligibility_summary: dict[str, Any]
    split_summary: dict[str, Any]
    fold_summaries: list[dict[str, Any]]
    model_metadata: list[dict[str, Any]]
    preprocessing_metadata: list[dict[str, Any]]
    validation_summary: dict[str, Any]
    out_of_sample_evaluation: dict[str, Any]
    model_comparison: dict[str, Any]
    bounded_prediction_preview: list[dict[str, Any]]
    unavailable_evidence: list[str]
    warnings: list[str]
    limitations: list[str]
    artifact_reference: dict[str, Any]
    reproducibility: dict[str, Any]
