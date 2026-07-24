"""Tool handlers — call existing deterministic services; never recalculate metrics."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from app.research_agent.completeness import assess_research_completeness
from app.research_agent.tools import ToolRegistryError, validate_tool_call
from app.research_execution.market_data_port import utc_now_iso
from app.research_knowledge.retrieval import retrieve_rulebook


class ToolExecutionContext:
    """Dependencies injected by GovernanceAgentService."""

    def __init__(
        self,
        *,
        store: Any,
        validation_service: Any | None = None,
        factor_validation_service: Any | None = None,
        execution_service: Any | None = None,
        decision_log: Optional[dict[str, list[dict[str, Any]]]] = None,
    ) -> None:
        self.store = store
        self.validation_service = validation_service
        self.factor_validation_service = factor_validation_service
        self.execution_service = execution_service
        self.decision_log = decision_log if decision_log is not None else {}


def _result(
    *,
    tool_name: str,
    status: str,
    input_parameters: dict[str, Any],
    result_reference: Any = None,
    evidence_ids_created: list[str] | None = None,
    error: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    return {
        "tool_call_id": f"tool-{uuid.uuid4().hex[:12]}",
        "tool_name": tool_name,
        "status": status,
        "started_at": started_at or utc_now_iso(),
        "completed_at": completed_at or utc_now_iso(),
        "input_parameters": input_parameters,
        "result_reference": result_reference,
        "evidence_ids_created": evidence_ids_created or [],
        "error": error,
    }


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any] | None,
    *,
    state: dict[str, Any],
    ctx: ToolExecutionContext,
) -> dict[str, Any]:
    started = utc_now_iso()
    try:
        validate_tool_call(tool_name, arguments)
    except ToolRegistryError as exc:
        return _result(
            tool_name=tool_name,
            status="failed",
            input_parameters=arguments or {},
            error=str(exc),
            started_at=started,
        )

    handler = HANDLERS.get(tool_name)
    if handler is None:
        return _result(
            tool_name=tool_name,
            status="failed",
            input_parameters=arguments or {},
            error=f"No handler registered for '{tool_name}'.",
            started_at=started,
        )
    try:
        return handler(arguments or {}, state=state, ctx=ctx, started_at=started)
    except Exception as exc:  # noqa: BLE001 — recorded honestly on the tool result
        return _result(
            tool_name=tool_name,
            status="failed",
            input_parameters=arguments or {},
            error=str(exc),
            started_at=started,
        )


def _get_snapshot(state: dict[str, Any], ctx: ToolExecutionContext, snapshot_id: str | None):
    run_id = snapshot_id or state.get("evidence_snapshot_id")
    if not run_id:
        return None, None
    return run_id, ctx.store.get(run_id)


def _handle_get_research_definition(args, *, state, ctx, started_at):
    definition = state.get("research_definition") or {"research_id": args.get("research_id")}
    return _result(
        tool_name="get_research_definition",
        status="completed",
        input_parameters=args,
        result_reference=definition,
        started_at=started_at,
    )


def _handle_get_active_success_criteria(args, *, state, ctx, started_at):
    definition = state.get("research_definition") or {}
    criteria = definition.get("success_criteria") or []
    active = [
        item
        for item in criteria
        if isinstance(item, dict) and item.get("status") == "active"
    ]
    return _result(
        tool_name="get_active_success_criteria",
        status="completed",
        input_parameters=args,
        result_reference={"active_success_criteria": active, "count": len(active)},
        started_at=started_at,
    )


def _handle_get_latest_evidence_snapshot(args, *, state, ctx, started_at):
    run_id, stored = _get_snapshot(state, ctx, args.get("evidence_snapshot_id"))
    if stored is None:
        return _result(
            tool_name="get_latest_evidence_snapshot",
            status="completed",
            input_parameters=args,
            result_reference={"available": False, "evidence_snapshot_id": None},
            started_at=started_at,
        )
    return _result(
        tool_name="get_latest_evidence_snapshot",
        status="completed",
        input_parameters=args,
        result_reference={
            "available": True,
            "evidence_snapshot_id": run_id,
            "evidence_kind": stored.get("evidence_kind") or stored.get("template"),
            "generated_at": stored.get("generated_at"),
            "validation_status": stored.get("validation_status"),
        },
        started_at=started_at,
    )


def _handle_get_benchmark_evaluation(args, *, state, ctx, started_at):
    _, stored = _get_snapshot(state, ctx, args.get("evidence_snapshot_id"))
    if stored is None:
        return _result(
            tool_name="get_benchmark_evaluation",
            status="completed",
            input_parameters=args,
            result_reference={"available": False},
            started_at=started_at,
        )
    benchmark = stored.get("benchmark") or {}
    return _result(
        tool_name="get_benchmark_evaluation",
        status="completed",
        input_parameters=args,
        result_reference={"available": True, "benchmark": benchmark},
        started_at=started_at,
    )


def _handle_get_validation_results(args, *, state, ctx, started_at):
    _, stored = _get_snapshot(state, ctx, args.get("evidence_snapshot_id"))
    if stored is None:
        return _result(
            tool_name="get_validation_results",
            status="completed",
            input_parameters=args,
            result_reference={"available": False},
            started_at=started_at,
        )
    payload = {
        "available": True,
        "stages": stored.get("stages"),
        "ic": (stored.get("ic") or {}).get("summary") if stored.get("ic") else None,
        "quantiles_turnover": ((stored.get("quantiles") or {}).get("turnover")),
        "long_short": stored.get("long_short"),
        "validation_status": stored.get("validation_status"),
    }
    return _result(
        tool_name="get_validation_results",
        status="completed",
        input_parameters=args,
        result_reference=payload,
        started_at=started_at,
    )


def _handle_get_robustness_results(args, *, state, ctx, started_at):
    _, stored = _get_snapshot(state, ctx, args.get("evidence_snapshot_id"))
    if stored is None:
        return _result(
            tool_name="get_robustness_results",
            status="completed",
            input_parameters=args,
            result_reference={"available": False},
            started_at=started_at,
        )
    stages = stored.get("stages") or {}
    robustness = {
        key: stages.get(key)
        for key in (
            "out_of_sample",
            "parameter_sensitivity",
            "transaction_cost_sensitivity",
            "data_quality",
        )
        if key in stages
    }
    return _result(
        tool_name="get_robustness_results",
        status="completed",
        input_parameters=args,
        result_reference={"available": bool(robustness), "stages": robustness},
        started_at=started_at,
    )


def _handle_get_feature_interpretation(args, *, state, ctx, started_at):
    definition = state.get("research_definition") or {}
    fi = definition.get("feature_interpretation")
    return _result(
        tool_name="get_feature_interpretation",
        status="completed",
        input_parameters=args,
        result_reference={
            "available": fi is not None,
            "feature_interpretation": fi,
            "note": "Feature importance does not imply causality.",
        },
        started_at=started_at,
    )


def _handle_get_known_limitations(args, *, state, ctx, started_at):
    definition = state.get("research_definition") or {}
    limitations = definition.get("known_limitations") or definition.get("known_weaknesses") or []
    rulebook = retrieve_rulebook(query="known limitations", topic="limitations", top_k=1)
    return _result(
        tool_name="get_known_limitations",
        status="completed",
        input_parameters=args,
        result_reference={
            "definition_limitations": limitations,
            "rulebook": rulebook,
        },
        started_at=started_at,
    )


def _handle_get_previous_decisions(args, *, state, ctx, started_at):
    research_id = str(args.get("research_id") or state.get("research_id") or "")
    decisions = list(ctx.decision_log.get(research_id) or [])
    return _result(
        tool_name="get_previous_decisions",
        status="completed",
        input_parameters=args,
        result_reference={"decisions": decisions, "count": len(decisions)},
        started_at=started_at,
    )


def _handle_retrieve_research_rulebook(args, *, state, ctx, started_at):
    hits = retrieve_rulebook(
        query=str(args.get("query") or state.get("intent") or "research protocol"),
        research_type=args.get("research_type") or state.get("research_type"),
        topic=args.get("topic"),
        top_k=int(args.get("top_k") or 4),
    )
    return _result(
        tool_name="retrieve_research_rulebook",
        status="completed",
        input_parameters=args,
        result_reference={"hits": hits},
        started_at=started_at,
    )


def _handle_run_validation_family(tool_name: str, args, *, state, ctx, started_at):
    if ctx.validation_service is None:
        return _result(
            tool_name=tool_name,
            status="failed",
            input_parameters=args,
            error="ResearchValidationService is not configured for this agent run.",
            started_at=started_at,
        )
    result = ctx.validation_service.execute({"research_id": args.get("research_id") or state.get("research_id")})
    run_id = result.get("validation_run_id")
    return _result(
        tool_name=tool_name,
        status="completed",
        input_parameters=args,
        result_reference={"validation_run_id": run_id, "validation_status": result.get("validation_status")},
        evidence_ids_created=[run_id] if run_id else [],
        started_at=started_at,
    )


def _handle_run_factor_validation(args, *, state, ctx, started_at):
    if ctx.factor_validation_service is None:
        return _result(
            tool_name="run_factor_validation",
            status="failed",
            input_parameters=args,
            error="FactorValidationService is not configured for this agent run.",
            started_at=started_at,
        )
    payload = {
        "research_id": args.get("research_id") or state.get("research_id"),
        "factor_id": args.get("factor_id") or "momentum",
    }
    result = ctx.factor_validation_service.execute(payload)
    run_id = result.get("validation_run_id")
    return _result(
        tool_name="run_factor_validation",
        status="completed",
        input_parameters=args,
        result_reference={"validation_run_id": run_id},
        evidence_ids_created=[run_id] if run_id else [],
        started_at=started_at,
    )


def _handle_run_research_execution(args, *, state, ctx, started_at):
    if ctx.execution_service is None:
        return _result(
            tool_name="run_research_execution",
            status="failed",
            input_parameters=args,
            error="ResearchExecutionService is not configured for this agent run.",
            started_at=started_at,
        )
    result = ctx.execution_service.execute({"research_id": args.get("research_id") or state.get("research_id")})
    return _result(
        tool_name="run_research_execution",
        status="completed",
        input_parameters=args,
        result_reference={
            "metrics": result.get("metrics"),
            "generated_at": result.get("generated_at"),
        },
        started_at=started_at,
    )


def _handle_run_benchmark_evaluation(args, *, state, ctx, started_at):
    _, stored = _get_snapshot(state, ctx, args.get("evidence_snapshot_id"))
    if stored is None:
        return _result(
            tool_name="run_benchmark_evaluation",
            status="failed",
            input_parameters=args,
            error="No evidence snapshot available for benchmark evaluation.",
            started_at=started_at,
        )
    return _result(
        tool_name="run_benchmark_evaluation",
        status="completed",
        input_parameters=args,
        result_reference={"benchmark": stored.get("benchmark") or {}, "note": "Read from stored snapshot; metrics not recalculated by agent."},
        started_at=started_at,
    )


def _handle_build_decision_readiness(args, *, state, ctx, started_at):
    completeness = assess_research_completeness(
        research_definition=state.get("research_definition"),
        evidence_snapshot=state.get("evidence_snapshot"),
        research_type=str(state.get("research_type") or "trend_following"),
        decision_recorded=bool((state.get("human_decision") or {}).get("decision")),
    )
    return _result(
        tool_name="build_decision_readiness",
        status="completed",
        input_parameters=args,
        result_reference=completeness,
        started_at=started_at,
    )


def _handle_write_pending(tool_name: str, args, *, state, ctx, started_at):
    """Write tools never mutate silently — they only prepare pending approval records."""
    return _result(
        tool_name=tool_name,
        status="awaiting_human_confirmation",
        input_parameters=args,
        result_reference={
            "pending_write": True,
            "tool_name": tool_name,
            "message": "Write-sensitive action requires explicit human confirmation; not applied.",
        },
        started_at=started_at,
    )


def _handle_record_human_decision(args, *, state, ctx, started_at):
    research_id = str(args.get("research_id") or state.get("research_id") or "")
    decision = str(args.get("decision") or "").strip()
    rationale = str(args.get("rationale") or "").strip()
    if not decision or not rationale:
        return _result(
            tool_name="record_human_decision",
            status="failed",
            input_parameters=args,
            error="decision and rationale are required.",
            started_at=started_at,
        )
    existing = list(ctx.decision_log.get(research_id) or [])
    record = {
        "decision": decision,
        "rationale": rationale,
        "override_rationale": args.get("override_rationale"),
        "evidence_snapshot_id": args.get("evidence_snapshot_id")
        or state.get("evidence_snapshot_id"),
        "agent_run_id": state.get("agent_run_id"),
        "recorded_at": utc_now_iso(),
        "prompt_versions": state.get("prompt_versions"),
        "model": state.get("llm_model"),
        "provider": state.get("llm_provider"),
    }
    # Append-only — never overwrite prior human decisions
    existing.append(record)
    ctx.decision_log[research_id] = existing
    return _result(
        tool_name="record_human_decision",
        status="completed",
        input_parameters=args,
        result_reference={"recorded": True, "decision_index": len(existing) - 1, "record": record},
        started_at=started_at,
    )


HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "get_research_definition": _handle_get_research_definition,
    "get_active_success_criteria": _handle_get_active_success_criteria,
    "get_latest_evidence_snapshot": _handle_get_latest_evidence_snapshot,
    "get_benchmark_evaluation": _handle_get_benchmark_evaluation,
    "get_validation_results": _handle_get_validation_results,
    "get_robustness_results": _handle_get_robustness_results,
    "get_feature_interpretation": _handle_get_feature_interpretation,
    "get_known_limitations": _handle_get_known_limitations,
    "get_previous_decisions": _handle_get_previous_decisions,
    "retrieve_research_rulebook": _handle_retrieve_research_rulebook,
    "run_research_execution": _handle_run_research_execution,
    "run_benchmark_evaluation": _handle_run_benchmark_evaluation,
    "run_oos_validation": lambda a, **kw: _handle_run_validation_family("run_oos_validation", a, **kw),
    "run_parameter_sensitivity": lambda a, **kw: _handle_run_validation_family(
        "run_parameter_sensitivity", a, **kw
    ),
    "run_cost_sensitivity": lambda a, **kw: _handle_run_validation_family(
        "run_cost_sensitivity", a, **kw
    ),
    "run_data_quality_check": lambda a, **kw: _handle_run_validation_family(
        "run_data_quality_check", a, **kw
    ),
    "run_factor_validation": _handle_run_factor_validation,
    "build_decision_readiness": _handle_build_decision_readiness,
    "apply_research_definition_draft": lambda a, **kw: _handle_write_pending(
        "apply_research_definition_draft", a, **kw
    ),
    "accept_success_criteria": lambda a, **kw: _handle_write_pending(
        "accept_success_criteria", a, **kw
    ),
    "record_human_decision": _handle_record_human_decision,
    "archive_research": lambda a, **kw: _handle_write_pending("archive_research", a, **kw),
}
