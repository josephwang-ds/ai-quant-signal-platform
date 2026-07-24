"""API schemas for the Quant Research Governance Agent."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AgentIntent = Literal[
    "review_definition",
    "review_readiness",
    "review_evidence",
    "prepare_decision",
]

AgentStatus = Literal[
    "running",
    "awaiting_approval",
    "completed",
    "failed",
    "cancelled",
]

ResumeAction = Literal[
    "approve",
    "edit",
    "skip",
    "cancel",
    "record_decision",
    "run_additional_validation",
]


class AgentRunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str = Field(min_length=1, max_length=128)
    intent: AgentIntent
    research_type: Literal["trend_following", "factor"] = "trend_following"
    research_definition: dict[str, Any] = Field(default_factory=dict)
    evidence_snapshot_id: Optional[str] = None
    previous_decisions: list[dict[str, Any]] = Field(default_factory=list)
    user_question: Optional[str] = Field(default=None, max_length=1000)


class AgentRunSummaryResponse(BaseModel):
    agent_run_id: str
    status: AgentStatus
    current_node: str
    summary: str


class AgentResumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ResumeAction
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunDetailResponse(BaseModel):
    agent_run_id: str
    research_id: str
    intent: AgentIntent
    status: AgentStatus
    current_node: str
    summary: str
    research_type: str
    llm_available: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    graph_version: str
    evidence_snapshot_id: Optional[str] = None
    knowledge_context: list[dict[str, Any]] = Field(default_factory=list)
    requested_tools: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    definition_review: dict[str, Any] = Field(default_factory=dict)
    completeness: dict[str, Any] = Field(default_factory=dict)
    ai_interpretation: dict[str, Any] = Field(default_factory=dict)
    decision_review: dict[str, Any] = Field(default_factory=dict)
    pending_approval: dict[str, Any] = Field(default_factory=dict)
    human_decision: dict[str, Any] = Field(default_factory=dict)
    missing_evidence: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    step_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
