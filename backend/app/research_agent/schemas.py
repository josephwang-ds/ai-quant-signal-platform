"""API schemas for the Quant Research Governance Agent."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security.limits import MAX_QUESTION_LENGTH, MAX_RATIONALE_LENGTH

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
    user_question: Optional[str] = Field(default=None, max_length=MAX_QUESTION_LENGTH)


class AgentRunSummaryResponse(BaseModel):
    agent_run_id: str
    status: AgentStatus
    current_node: str
    summary: str


class AgentResumeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ResumeAction
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def limit_payload_text_fields(cls, value: dict[str, Any]) -> dict[str, Any]:
        for key in ("rationale", "override_rationale", "notes", "question"):
            raw = value.get(key)
            if isinstance(raw, str) and len(raw) > MAX_RATIONALE_LENGTH:
                raise ValueError(
                    f"{key} must be at most {MAX_RATIONALE_LENGTH} characters"
                )
        return value


class AgentTraceEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    sequence: int
    timestamp: Optional[str] = None
    node: str
    event: str
    label: str
    authority: Literal["system", "deterministic", "llm", "human"]
    status: Literal[
        "pending", "running", "completed", "blocked", "unavailable", "failed"
    ]
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    methodology_citations: list[str] = Field(default_factory=list)
    tool_name: Optional[str] = None
    approval_required: bool = False
    # Legacy aliases
    step: Optional[int] = None
    detail: Optional[str] = None
    at: Optional[str] = None


class AgentRunDetailResponse(BaseModel):
    agent_run_id: str
    research_id: str
    intent: AgentIntent
    status: AgentStatus
    current_node: str
    summary: str
    research_type: str
    llm_available: bool
    llm_used: bool = False
    llm_interpretation_status: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    graph_version: str
    rulebook_version: Optional[str] = None
    protocol_version: Optional[str] = None
    tool_plan: list[dict[str, Any]] = Field(default_factory=list)
    approval_required: bool = False
    deterministic_suggestion: Optional[str] = None
    final_human_decision: Optional[dict[str, Any]] = None
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
    events: list[dict[str, Any]] = Field(default_factory=list)
    step_count: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
