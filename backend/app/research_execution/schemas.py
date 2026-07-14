"""Pydantic request/response models for research execution."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ResearchExecutionRequest(BaseModel):
    research_id: str = Field(default="ma-crossover-spy")
    symbol: str = Field(default="SPY")
    benchmark: str = Field(default="SPY")
    start_date: str = Field(default="2018-01-01")
    end_date: Optional[str] = None
    short_window: int = Field(default=20, gt=0)
    long_window: int = Field(default=60, gt=0)
    transaction_cost: float = Field(default=0.001, ge=0)
    risk_free_rate: float = Field(default=0.0)

    @field_validator("symbol", "benchmark")
    @classmethod
    def upper_symbol(cls, value: str) -> str:
        return value.upper().strip()

    @model_validator(mode="after")
    def check_windows_and_dates(self) -> "ResearchExecutionRequest":
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be < long_window")
        if self.end_date and self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class ResearchExecutionResponse(BaseModel):
    research_id: str
    strategy: dict[str, Any]
    provenance: dict[str, Any]
    metrics: dict[str, Any]
    benchmark_metrics: dict[str, Any]
    series: list[dict[str, Any]]
    warnings: list[str]
    generated_at: str
    supported_evidence: dict[str, str]
