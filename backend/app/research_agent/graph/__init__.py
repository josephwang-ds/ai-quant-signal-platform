"""Compile the Quant Research Governance Agent LangGraph."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.research_agent.graph.nodes import make_nodes
from app.research_agent.state import AgentState
from app.research_agent.tools.handlers import ToolExecutionContext

InterruptNode = Literal["request_tool_approval", "await_human_decision"]


def _route_after_classify(state: AgentState) -> str:
    if state.get("unsupported_request") or state.get("status") == "failed":
        return "handle_agent_error"
    return "load_research_context"


def _route_after_load(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "handle_agent_error"
    intent = state.get("intent")
    if intent == "review_definition":
        return "review_research_definition"
    return "retrieve_methodology"


def _route_after_definition(state: AgentState) -> str:
    return "retrieve_methodology"


def _route_after_plan(state: AgentState) -> str:
    if state.get("status") == "cancelled":
        return "finalize_agent_run"
    pending = state.get("pending_approval") or {}
    if pending.get("type") == "tool_approval" and pending.get("tools"):
        return "request_tool_approval"
    return "execute_approved_tools"


def _route_after_tool_approval(state: AgentState) -> str:
    if state.get("status") == "cancelled":
        return "finalize_agent_run"
    if state.get("status") == "awaiting_approval":
        return END  # type: ignore[return-value]
    return "execute_approved_tools"


def _route_after_execute(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "handle_agent_error"
    return "refresh_evidence_snapshot"


def _route_after_refresh(state: AgentState) -> str:
    if state.get("status") == "failed":
        return "handle_agent_error"
    intent = state.get("intent")
    if intent == "review_readiness":
        return "assess_research_completeness"
    if intent in {"review_evidence", "prepare_decision"}:
        return "review_evidence"
    return "assess_research_completeness"


def _route_after_review_evidence(state: AgentState) -> str:
    return "assess_research_completeness"


def _route_after_completeness(state: AgentState) -> str:
    intent = state.get("intent")
    if intent == "prepare_decision":
        return "prepare_decision_review"
    if intent == "review_definition":
        return "finalize_agent_run"
    if intent == "review_readiness":
        return "finalize_agent_run"
    # review_evidence
    return "finalize_agent_run"


def _route_after_decision_prep(state: AgentState) -> str:
    return "await_human_decision"


def _route_after_human_decision(state: AgentState) -> str:
    if state.get("status") == "cancelled":
        return "finalize_agent_run"
    if state.get("status") == "awaiting_approval":
        return END  # type: ignore[return-value]
    # additional validation loop (bounded by step_count)
    if any(
        str(m).startswith("additional_validation")
        for m in (state.get("missing_evidence") or [])
    ) and state.get("requested_tools"):
        return "execute_approved_tools"
    return "finalize_agent_run"


def build_governance_graph(
    *,
    llm: Any | None,
    tool_ctx: ToolExecutionContext,
    store: Any,
    checkpointer: MemorySaver | None = None,
):
    nodes = make_nodes(llm=llm, tool_ctx=tool_ctx, store=store)
    graph = StateGraph(AgentState)

    for name, fn in nodes.items():
        graph.add_node(name, fn)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {
            "handle_agent_error": "handle_agent_error",
            "load_research_context": "load_research_context",
        },
    )
    graph.add_conditional_edges(
        "load_research_context",
        _route_after_load,
        {
            "handle_agent_error": "handle_agent_error",
            "review_research_definition": "review_research_definition",
            "retrieve_methodology": "retrieve_methodology",
        },
    )
    graph.add_conditional_edges(
        "review_research_definition",
        _route_after_definition,
        {"retrieve_methodology": "retrieve_methodology"},
    )
    graph.add_edge("retrieve_methodology", "inspect_available_evidence")
    graph.add_conditional_edges(
        "inspect_available_evidence",
        lambda state: (
            "assess_research_completeness"
            if state.get("intent") == "review_definition"
            else "plan_tool_calls"
        ),
        {
            "assess_research_completeness": "assess_research_completeness",
            "plan_tool_calls": "plan_tool_calls",
        },
    )
    graph.add_conditional_edges(
        "plan_tool_calls",
        _route_after_plan,
        {
            "finalize_agent_run": "finalize_agent_run",
            "request_tool_approval": "request_tool_approval",
            "execute_approved_tools": "execute_approved_tools",
        },
    )
    graph.add_conditional_edges(
        "request_tool_approval",
        _route_after_tool_approval,
        {
            "finalize_agent_run": "finalize_agent_run",
            "execute_approved_tools": "execute_approved_tools",
            END: END,
        },
    )
    graph.add_conditional_edges(
        "execute_approved_tools",
        _route_after_execute,
        {
            "handle_agent_error": "handle_agent_error",
            "refresh_evidence_snapshot": "refresh_evidence_snapshot",
        },
    )
    graph.add_conditional_edges(
        "refresh_evidence_snapshot",
        _route_after_refresh,
        {
            "handle_agent_error": "handle_agent_error",
            "assess_research_completeness": "assess_research_completeness",
            "review_evidence": "review_evidence",
        },
    )
    graph.add_conditional_edges(
        "review_evidence",
        _route_after_review_evidence,
        {"assess_research_completeness": "assess_research_completeness"},
    )
    graph.add_conditional_edges(
        "assess_research_completeness",
        _route_after_completeness,
        {
            "prepare_decision_review": "prepare_decision_review",
            "finalize_agent_run": "finalize_agent_run",
        },
    )
    graph.add_conditional_edges(
        "prepare_decision_review",
        _route_after_decision_prep,
        {"await_human_decision": "await_human_decision"},
    )
    graph.add_conditional_edges(
        "await_human_decision",
        _route_after_human_decision,
        {
            "finalize_agent_run": "finalize_agent_run",
            "execute_approved_tools": "execute_approved_tools",
            END: END,
        },
    )
    graph.add_edge("finalize_agent_run", END)
    graph.add_edge("handle_agent_error", END)

    memory = checkpointer or MemorySaver()
    return graph.compile(
        checkpointer=memory,
        interrupt_before=["request_tool_approval", "await_human_decision"],
    )
