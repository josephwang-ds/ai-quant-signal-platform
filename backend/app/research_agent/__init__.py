"""Quant Research Governance Agent — controlled LangGraph workflow."""

GRAPH_VERSION = "governance_agent_graph_v1"
MAX_TOOL_CALLS = 8
MAX_LLM_PLANNING_CYCLES = 2
MAX_GRAPH_STEPS = 24

__all__ = [
    "GRAPH_VERSION",
    "MAX_TOOL_CALLS",
    "MAX_LLM_PLANNING_CYCLES",
    "MAX_GRAPH_STEPS",
]
