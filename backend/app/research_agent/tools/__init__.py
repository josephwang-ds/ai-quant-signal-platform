"""Approved tool registry for the Governance Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ToolKind = Literal["read", "execution", "write"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    kind: ToolKind
    description: str
    requires_approval: bool
    allowed_args: frozenset[str]


TOOL_REGISTRY: dict[str, ToolSpec] = {
    # Read-only
    "get_research_definition": ToolSpec(
        "get_research_definition",
        "read",
        "Load the stored research definition.",
        False,
        frozenset({"research_id"}),
    ),
    "get_active_success_criteria": ToolSpec(
        "get_active_success_criteria",
        "read",
        "Load active success criteria from the definition.",
        False,
        frozenset({"research_id"}),
    ),
    "get_latest_evidence_snapshot": ToolSpec(
        "get_latest_evidence_snapshot",
        "read",
        "Load the latest evidence snapshot for this research.",
        False,
        frozenset({"research_id", "evidence_snapshot_id"}),
    ),
    "get_benchmark_evaluation": ToolSpec(
        "get_benchmark_evaluation",
        "read",
        "Load benchmark evaluation from the evidence snapshot.",
        False,
        frozenset({"evidence_snapshot_id"}),
    ),
    "get_validation_results": ToolSpec(
        "get_validation_results",
        "read",
        "Load validation stage results from the evidence snapshot.",
        False,
        frozenset({"evidence_snapshot_id"}),
    ),
    "get_robustness_results": ToolSpec(
        "get_robustness_results",
        "read",
        "Summarize robustness-related validation stages.",
        False,
        frozenset({"evidence_snapshot_id"}),
    ),
    "get_feature_interpretation": ToolSpec(
        "get_feature_interpretation",
        "read",
        "Load feature interpretation if present on the research context.",
        False,
        frozenset({"research_id"}),
    ),
    "get_known_limitations": ToolSpec(
        "get_known_limitations",
        "read",
        "Load known limitations from definition and rulebook.",
        False,
        frozenset({"research_id"}),
    ),
    "get_previous_decisions": ToolSpec(
        "get_previous_decisions",
        "read",
        "Load previously recorded human decisions (append-only references).",
        False,
        frozenset({"research_id"}),
    ),
    "retrieve_research_rulebook": ToolSpec(
        "retrieve_research_rulebook",
        "read",
        "Retrieve versioned Research Rulebook sections.",
        False,
        frozenset({"query", "research_type", "topic", "top_k"}),
    ),
    # Deterministic execution (approval required)
    "run_research_execution": ToolSpec(
        "run_research_execution",
        "execution",
        "Run deterministic research execution / backtest.",
        True,
        frozenset({"research_id"}),
    ),
    "run_benchmark_evaluation": ToolSpec(
        "run_benchmark_evaluation",
        "execution",
        "Recompute benchmark checks from stored evidence.",
        True,
        frozenset({"evidence_snapshot_id"}),
    ),
    "run_oos_validation": ToolSpec(
        "run_oos_validation",
        "execution",
        "Request OOS validation via Research Validation service.",
        True,
        frozenset({"research_id"}),
    ),
    "run_parameter_sensitivity": ToolSpec(
        "run_parameter_sensitivity",
        "execution",
        "Request parameter sensitivity via Research Validation service.",
        True,
        frozenset({"research_id"}),
    ),
    "run_cost_sensitivity": ToolSpec(
        "run_cost_sensitivity",
        "execution",
        "Request transaction-cost sensitivity via Research Validation service.",
        True,
        frozenset({"research_id"}),
    ),
    "run_data_quality_check": ToolSpec(
        "run_data_quality_check",
        "execution",
        "Request data-quality checks via Research Validation service.",
        True,
        frozenset({"research_id"}),
    ),
    "run_factor_validation": ToolSpec(
        "run_factor_validation",
        "execution",
        "Run Factor Validation (RankIC + quantiles).",
        True,
        frozenset({"research_id", "factor_id"}),
    ),
    "build_decision_readiness": ToolSpec(
        "build_decision_readiness",
        "execution",
        "Build deterministic decision readiness / completeness.",
        True,
        frozenset({"research_id", "evidence_snapshot_id"}),
    ),
    # Write-sensitive — approval only, never auto-execute from model
    "apply_research_definition_draft": ToolSpec(
        "apply_research_definition_draft",
        "write",
        "Apply a research definition draft after human approval.",
        True,
        frozenset({"research_id", "draft"}),
    ),
    "accept_success_criteria": ToolSpec(
        "accept_success_criteria",
        "write",
        "Accept success criteria after human approval.",
        True,
        frozenset({"research_id", "criteria"}),
    ),
    "record_human_decision": ToolSpec(
        "record_human_decision",
        "write",
        "Record a human decision after explicit confirmation.",
        True,
        frozenset(
            {
                "research_id",
                "decision",
                "rationale",
                "override_rationale",
                "evidence_snapshot_id",
            }
        ),
    ),
    "archive_research": ToolSpec(
        "archive_research",
        "write",
        "Archive research after human confirmation.",
        True,
        frozenset({"research_id", "rationale"}),
    ),
}


class ToolRegistryError(ValueError):
    pass


def get_tool(name: str) -> ToolSpec:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        raise ToolRegistryError(f"Unknown tool '{name}' is not in the approved registry.")
    return tool


def validate_tool_call(tool_name: str, arguments: dict[str, Any] | None) -> ToolSpec:
    tool = get_tool(tool_name)
    args = arguments or {}
    if not isinstance(args, dict):
        raise ToolRegistryError(f"Tool '{tool_name}' arguments must be an object.")
    unknown = set(args.keys()) - set(tool.allowed_args)
    if unknown:
        raise ToolRegistryError(
            f"Tool '{tool_name}' received unsupported arguments: {sorted(unknown)}"
        )
    return tool


def list_tools(*, kind: ToolKind | None = None) -> list[dict[str, Any]]:
    tools = TOOL_REGISTRY.values()
    if kind:
        tools = [t for t in tools if t.kind == kind]  # type: ignore[assignment]
    return [
        {
            "name": t.name,
            "kind": t.kind,
            "description": t.description,
            "requires_approval": t.requires_approval,
            "allowed_args": sorted(t.allowed_args),
        }
        for t in tools
    ]
