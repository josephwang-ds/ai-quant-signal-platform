"""Serializable LangGraph state for the Governance Agent."""

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

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

ResearchType = Literal["trend_following", "factor"]


class TraceEvent(TypedDict, total=False):
    step: int
    node: str
    event: str
    detail: str
    at: str


class AgentState(TypedDict, total=False):
    agent_run_id: str
    research_id: str
    research_type: ResearchType
    intent: AgentIntent
    current_node: str
    status: AgentStatus
    research_definition: dict[str, Any]
    definition_review: dict[str, Any]
    knowledge_context: list[dict[str, Any]]
    requested_tools: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    evidence_snapshot_id: Optional[str]
    evidence_snapshot: dict[str, Any]
    benchmark_evaluation: dict[str, Any]
    decision_readiness: dict[str, Any]
    ai_interpretation: dict[str, Any]
    missing_evidence: list[str]
    recommended_next_steps: list[str]
    pending_approval: dict[str, Any]
    approval_action: Optional[str]
    approval_payload: dict[str, Any]
    human_decision: dict[str, Any]
    decision_review: dict[str, Any]
    completeness: dict[str, Any]
    llm_available: bool
    llm_provider: Optional[str]
    llm_model: Optional[str]
    prompt_versions: dict[str, str]
    graph_version: str
    planning_cycles: int
    step_count: int
    errors: list[str]
    trace: list[dict[str, Any]]
    summary: str
    unsupported_request: bool
    user_question: Optional[str]
