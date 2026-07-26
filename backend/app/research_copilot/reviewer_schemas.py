from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security.limits import MAX_PROMPT_LENGTH

ResearchType = Literal["trend_following", "cross_sectional_factor"]


class DraftResearchDefinitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_type: ResearchType
    symbol_or_universe: str = Field(min_length=1, max_length=200)
    parameters: dict[str, Any] = Field(default_factory=dict)
    date_range: dict[str, Optional[str]]
    benchmark: dict[str, str]
    transaction_cost: float = Field(ge=0)
    available_validation_methods: list[str] = Field(max_length=20)
    known_system_limitations: list[str] = Field(max_length=20)


class ProposedSuccessCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(min_length=1, max_length=120)
    metric: str = Field(min_length=1, max_length=100)
    operator: Literal["gte", "lte", "gt", "lt", "positive", "non_negative"]
    threshold: None = None
    severity: Literal["core", "supporting", "guardrail"]
    description: str = Field(min_length=1, max_length=500)
    source: Literal["ai_proposed"]
    threshold_guidance: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=500)


class FailureCriterionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=1, max_length=500)


class BenchmarkDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=500)


class DraftResearchDefinitionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_question: str = Field(min_length=1, max_length=1500)
    hypothesis: str = Field(min_length=1, max_length=1500)
    null_hypothesis: str = Field(min_length=1, max_length=1500)
    mechanism: str = Field(min_length=1, max_length=1500)
    primary_benchmark: BenchmarkDraft
    proposed_success_criteria: list[ProposedSuccessCriterion] = Field(
        max_length=12
    )
    failure_criteria: list[FailureCriterionDraft] = Field(max_length=12)
    required_validation: list[str] = Field(max_length=20)
    known_limitations: list[str] = Field(max_length=20)
    clarifications_needed: list[str] = Field(max_length=12)


class HypothesisReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_type: ResearchType
    research_question: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    hypothesis: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    null_hypothesis: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    benchmark: str = Field(min_length=1, max_length=500)
    success_criteria: list[dict[str, Any]] = Field(max_length=20)
    available_validation_methods: list[str] = Field(max_length=20)


class SuggestedHypothesisRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_question: str = Field(min_length=1, max_length=1500)
    hypothesis: str = Field(min_length=1, max_length=1500)
    null_hypothesis: str = Field(min_length=1, max_length=1500)


class HypothesisReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_testable: bool
    is_falsifiable: bool
    benchmark_is_defined: bool
    outcome_metrics_are_defined: bool
    strengths: list[str] = Field(max_length=12)
    problems: list[str] = Field(max_length=12)
    missing_elements: list[str] = Field(max_length=12)
    suggested_revision: SuggestedHypothesisRevision
    warnings: list[str] = Field(max_length=12)


class EvidenceReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_definition: dict[str, Any]
    configured_success_criteria: list[dict[str, Any]] = Field(max_length=20)
    benchmark_evaluation: dict[str, Any]
    deterministic_decision_support: dict[str, Any]
    validation_metrics: dict[str, Any]
    robustness_results: dict[str, Any]
    data_quality_findings: dict[str, Any]
    known_limitations: list[str] = Field(max_length=20)
    evidence_snapshot_timestamp: Optional[str] = None


class ReferencedEvidenceClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: str = Field(min_length=1, max_length=800)
    evidence_reference: str = Field(min_length=1, max_length=300)


class EvidenceReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=1, max_length=2000)
    hypothesis_assessment: Literal[
        "supported", "partially_supported", "not_supported", "inconclusive"
    ]
    benchmark_assessment: str = Field(min_length=1, max_length=1200)
    supporting_evidence: list[ReferencedEvidenceClaim] = Field(max_length=15)
    contradicting_evidence: list[ReferencedEvidenceClaim] = Field(max_length=15)
    robustness_concerns: list[str] = Field(max_length=15)
    data_quality_concerns: list[str] = Field(max_length=15)
    decision_considerations: list[str] = Field(max_length=15)
    recommended_additional_validation: list[str] = Field(max_length=15)
    limitations: list[str] = Field(max_length=20)


class CompletionReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    definition_completeness: dict[str, Any]
    experiment_status: str = Field(max_length=100)
    validation_status: str = Field(max_length=100)
    robustness_status: str = Field(max_length=100)
    benchmark_status: str = Field(max_length=100)
    decision_status: str = Field(max_length=100)
    limitations_acknowledged: bool
    missing_evidence: list[str] = Field(max_length=30)


class CompletionReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readiness_summary: str = Field(min_length=1, max_length=1500)
    completed_items: list[str] = Field(max_length=30)
    missing_items: list[str] = Field(max_length=30)
    blocking_issues: list[str] = Field(max_length=20)
    non_blocking_issues: list[str] = Field(max_length=20)
    recommended_next_steps: list[str] = Field(max_length=20)


class ResearchReviewerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "draft_definition",
        "review_hypothesis",
        "review_evidence",
        "identify_missing_steps",
    ]
    provider: str
    model: str
    generated_at: str
    evidence_snapshot_timestamp: Optional[str] = None
    result: dict[str, Any]

    @field_validator("provider", "model")
    @classmethod
    def nonempty_metadata(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Reviewer provider/model metadata must not be empty.")
        return value.strip()
