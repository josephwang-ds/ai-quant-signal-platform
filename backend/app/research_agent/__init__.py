"""Quant Research Governance Agent — controlled LangGraph workflow."""

GRAPH_VERSION = "governance_agent_graph_v2"
MAX_TOOL_CALLS = 8
MAX_GRAPH_STEPS = 24


class GraphStepLimitError(RuntimeError):
    """Raised before a graph node would exceed the configured hard limit."""


__all__ = [
    "GRAPH_VERSION",
    "MAX_TOOL_CALLS",
    "MAX_GRAPH_STEPS",
    "GraphStepLimitError",
]
