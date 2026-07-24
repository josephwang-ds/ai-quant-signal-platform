from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ResearchGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_type: Literal["trend_following", "cross_sectional_factor"]
    universe: str = Field(min_length=1, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    benchmark_type: Literal[
        "same_asset_buy_and_hold", "equal_weight_universe"
    ]
    start_date: str
    end_date: Optional[str] = None
    transaction_cost: float = Field(default=0.001, ge=0)
    available_validation: list[str] = Field(default_factory=list, max_length=20)
    known_limitations: list[str] = Field(default_factory=list, max_length=20)
    use_llm: bool = False


class GuidanceCriterion(BaseModel):
    metric: str
    operator: str
    threshold_placeholder: str
    reason: str


class ResearchGuidanceResponse(BaseModel):
    research_question: str
    hypothesis: str
    null_hypothesis: str
    mechanism: str
    primary_benchmark: str
    success_criteria: list[GuidanceCriterion]
    failure_criteria: list[str]
    required_validation: list[str]
    known_limitations: list[str]
    clarifications_needed: list[str]
    source: Literal["template", "llm"]
    model: Optional[str] = None
