"""Transport contracts for factor validation API."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class FactorValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = "cross-sectional-factor-sector-etfs"
    universe_id: str = "us_sector_etfs"
    factor_id: Literal["momentum", "low_volatility", "value"] = "momentum"
    rebalance_frequency: Literal["monthly"] = "monthly"
    holding_period_months: int = Field(default=1, ge=1, le=12)
    start_date: str = "2018-01-01"
    end_date: Optional[str] = None
    transaction_cost: float = Field(default=0.001, ge=0)
    min_mean_rank_ic: float = 0.0
    min_positive_ic_ratio: float = Field(default=0.5, ge=0, le=1)
    min_net_long_short_return: float = 0.0
    min_q5_excess_return: float = 0.0
    max_mean_turnover: float = Field(default=2.0, ge=0)
    min_observations: int = Field(default=24, ge=1)
    min_icir: float = 0.0
    benchmark_symbol: str = "SPY"


class FactorValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    template: str
    universe_id: str
    factor_id: str
    rebalance_frequency: str
    holding_period_months: int
    ic: dict[str, Any]
    quantiles: dict[str, Any]
    long_short: dict[str, Any]
    benchmark: dict[str, Any]
    capm: dict[str, Any]
    portfolio_risk: dict[str, Any]
    warnings: list[str]
    provenance: dict[str, Any]
    generated_at: str
    validation_run_id: str
    evidence_kind: str = "factor_validation"
    validation_status: str = "completed"
    reproducibility_manifest: dict[str, Any] = Field(default_factory=dict)
