"""Transport contracts for deterministic research validation."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResearchValidationRequest(BaseModel):
    """RunValidation input; domain invariants are checked by the service."""

    model_config = ConfigDict(extra="forbid")

    research_id: str = "ma-crossover-spy"
    symbol: str = "SPY"
    benchmark: str = "SPY"
    start_date: str = "2018-01-01"
    end_date: Optional[str] = None
    short_window: int = 20
    long_window: int = 60
    transaction_cost: float = 0.001
    risk_free_rate: float = 0.0
    in_sample_ratio: float = 0.7
    min_excess_return: float = 0.0
    min_sharpe_difference: float = 0.0
    min_drawdown_improvement: float = Field(default=0.05, ge=0)
    min_cost_adjusted_return: float = 0.0
    min_robust_parameter_ratio: float = Field(default=0.5, ge=0, le=1)
    min_observations: int = Field(default=252, ge=1)


class ValidationStage(BaseModel):
    """Common stage envelope shared by all six deterministic stages."""

    stage: str
    label: str
    status: str
    summary: str
    evidence: dict[str, Any]
    rules: list[str]
    warnings: list[str]
    blockers: list[str]
    generated_at: str
    provenance: dict[str, Any]


class ResearchValidationResponse(BaseModel):
    research_id: str
    strategy: dict[str, Any]
    provenance: dict[str, Any]
    validation_status: str
    evidence_complete: bool
    stages: list[ValidationStage]
    oos: dict[str, Any]
    parameter_sensitivity: dict[str, Any]
    transaction_cost_sensitivity: dict[str, Any]
    data_quality: dict[str, Any]
    benchmark_evaluation: dict[str, Any]
    warnings: list[str]
    generated_at: str
    # Opaque id under which this exact ValidationResult was saved. Evaluation
    # loads evidence by this id instead of re-running Validation.
    validation_run_id: str
