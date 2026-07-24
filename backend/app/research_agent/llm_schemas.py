"""Strict, action-specific output contracts for Governance Agent LLM calls."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")


class DefinitionReviewOutput(AgentOutput):
    clarity: str = Field(min_length=1, max_length=1500)
    falsifiability: str = Field(min_length=1, max_length=1500)
    missing_elements: list[str] = Field(default_factory=list, max_length=20)
    unsupported_causal_wording: list[str] = Field(
        default_factory=list, max_length=20
    )
    possible_post_hoc_criteria: list[str] = Field(
        default_factory=list, max_length=20
    )
    summary: str = Field(min_length=1, max_length=2000)


class PlannedToolCall(AgentOutput):
    tool_name: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=500)
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False


class ToolPlanningOutput(AgentOutput):
    goal: str = Field(min_length=1, max_length=1000)
    tool_calls: list[PlannedToolCall] = Field(default_factory=list, max_length=8)
    expected_evidence: list[str] = Field(default_factory=list, max_length=20)
    stop_condition: str = Field(min_length=1, max_length=1000)


class EvidenceClaim(AgentOutput):
    claim: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)
    knowledge_ids: list[str] = Field(default_factory=list, max_length=20)


class EvidenceReviewOutput(AgentOutput):
    executive_summary: str = Field(min_length=1, max_length=2500)
    hypothesis_assessment: Literal[
        "supported", "partially_supported", "not_supported", "inconclusive"
    ]
    benchmark_assessment: str = Field(min_length=1, max_length=1500)
    supporting_evidence: list[EvidenceClaim] = Field(
        default_factory=list, max_length=20
    )
    contradicting_evidence: list[EvidenceClaim] = Field(
        default_factory=list, max_length=20
    )
    missing_evidence: list[str] = Field(default_factory=list, max_length=30)
    robustness_concerns: list[str] = Field(default_factory=list, max_length=20)
    data_quality_concerns: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=30)
    recommended_next_steps: list[str] = Field(default_factory=list, max_length=20)


class DecisionReviewOutput(AgentOutput):
    agent_interpretation: str = Field(min_length=1, max_length=2000)
    supporting_checks: list[str] = Field(default_factory=list, max_length=20)
    failed_checks: list[str] = Field(default_factory=list, max_length=20)
    conflicting_evidence: list[str] = Field(default_factory=list, max_length=20)
    missing_validation: list[str] = Field(default_factory=list, max_length=20)
    recommended_human_action: Literal[
        "review", "run_additional_validation", "record_decision"
    ]
    proposed_rationale_draft: str = Field(min_length=1, max_length=2000)
