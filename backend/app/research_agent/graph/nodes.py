"""LangGraph node implementations for the Governance Agent."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from app.research_agent import GRAPH_VERSION, MAX_GRAPH_STEPS, MAX_TOOL_CALLS
from app.research_agent.completeness import assess_research_completeness
from app.research_agent.llm_bridge import (
    AgentLlmUnavailable,
    context_from_dicts,
    generate_structured,
)
from app.research_agent.prompts import (
    DEFINITION_REVIEW_V1,
    DECISION_REVIEW_V1,
    EVIDENCE_REVIEW_V1,
    GOVERNANCE_SYSTEM_V1,
    PROMPT_VERSIONS,
    TOOL_PLANNING_V1,
)
from app.research_agent.state import AgentState
from app.research_agent.tools import ToolRegistryError, validate_tool_call
from app.research_agent.tools.handlers import ToolExecutionContext, execute_tool
from app.research_execution.market_data_port import utc_now_iso
from app.research_knowledge.retrieval import retrieve_rulebook

UNSUPPORTED_PATTERNS = (
    re.compile(r"\bwhat stock should i buy\b", re.I),
    re.compile(r"\bpredict\b.*\breturn\b", re.I),
    re.compile(r"\bexecute this strategy\b", re.I),
    re.compile(r"\bincrease leverage\b", re.I),
    re.compile(r"\bbuy\s+(spy|qqq|stock)\b", re.I),
)


def _trace(state: AgentState, node: str, event: str, detail: str = "") -> list[dict[str, Any]]:
    trace = list(state.get("trace") or [])
    trace.append(
        {
            "step": len(trace) + 1,
            "node": node,
            "event": event,
            "detail": detail,
            "at": utc_now_iso(),
        }
    )
    return trace


def _bump(state: AgentState, node: str) -> dict[str, Any]:
    step_count = int(state.get("step_count") or 0) + 1
    return {
        "current_node": node,
        "step_count": step_count,
        "status": "failed" if step_count > MAX_GRAPH_STEPS else state.get("status", "running"),
    }


def make_nodes(
    *,
    llm: Any | None,
    tool_ctx: ToolExecutionContext,
    store: Any,
) -> dict[str, Callable[[AgentState], dict[str, Any]]]:
    def classify_intent(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "classify_intent")
        question = state.get("user_question") or ""
        for pattern in UNSUPPORTED_PATTERNS:
            if pattern.search(question):
                return {
                    **updates,
                    "unsupported_request": True,
                    "status": "failed",
                    "errors": list(state.get("errors") or [])
                    + ["Unsupported request: trading/prediction/execution asks are rejected."],
                    "summary": "Rejected unsupported trading or prediction request.",
                    "trace": _trace(state, "classify_intent", "rejected_unsupported", question[:120]),
                }
        intent = state.get("intent")
        if intent not in {
            "review_definition",
            "review_readiness",
            "review_evidence",
            "prepare_decision",
        }:
            return {
                **updates,
                "unsupported_request": True,
                "status": "failed",
                "errors": list(state.get("errors") or []) + [f"Unsupported intent: {intent}"],
                "summary": "Unsupported intent.",
                "trace": _trace(state, "classify_intent", "rejected_intent", str(intent)),
            }
        return {
            **updates,
            "unsupported_request": False,
            "status": "running",
            "prompt_versions": dict(PROMPT_VERSIONS),
            "graph_version": GRAPH_VERSION,
            "trace": _trace(state, "classify_intent", "classified", str(intent)),
            "summary": f"Intent classified as {intent}.",
        }

    def load_research_context(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "load_research_context")
        definition = dict(state.get("research_definition") or {})
        definition.setdefault("research_id", state.get("research_id"))
        snapshot_id = state.get("evidence_snapshot_id")
        snapshot: dict[str, Any] = {}
        if snapshot_id:
            stored = store.get(snapshot_id)
            if stored and stored.get("research_id") == state.get("research_id"):
                snapshot = _build_evidence_availability(stored, research_type=state.get("research_type"))
            elif stored:
                return {
                    **updates,
                    "status": "failed",
                    "errors": list(state.get("errors") or [])
                    + ["Evidence snapshot does not belong to this research_id."],
                    "trace": _trace(state, "load_research_context", "snapshot_mismatch", str(snapshot_id)),
                    "summary": "Stopped: mixed/unrelated evidence snapshot.",
                }
        return {
            **updates,
            "research_definition": definition,
            "evidence_snapshot": snapshot,
            "trace": _trace(
                state,
                "load_research_context",
                "loaded",
                f"snapshot={snapshot_id or 'none'}",
            ),
            "summary": "Loaded research definition and evidence context.",
        }

    def review_research_definition(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "review_research_definition")
        definition = state.get("research_definition") or {}
        deterministic = {
            "question_exists": bool(str(definition.get("research_question") or "").strip()),
            "hypothesis_exists": bool(str(definition.get("hypothesis") or "").strip()),
            "null_hypothesis_exists": bool(str(definition.get("null_hypothesis") or "").strip()),
            "benchmark_exists": bool(str(definition.get("benchmark") or "").strip()),
            "outcome_metrics_exist": bool(definition.get("outcome_metrics")),
            "success_criteria_exist": bool(definition.get("success_criteria")),
            "evaluation_period_exists": bool(str(definition.get("evaluation_period") or "").strip()),
            "asset_or_universe_exists": bool(
                str(definition.get("symbol") or definition.get("universe") or "").strip()
            ),
            "hypothesis_testable": "guaranteed" not in str(definition.get("hypothesis") or "").lower(),
        }
        ai_review: dict[str, Any] = {"available": False}
        if state.get("llm_available") and llm is not None:
            try:
                payload, _, warnings = generate_structured(
                    llm,
                    user_prompt=DEFINITION_REVIEW_V1
                    + "\n\nDefinition JSON:\n"
                    + json.dumps(definition, ensure_ascii=False)[:6000],
                    system_prompt=GOVERNANCE_SYSTEM_V1 + "\n" + DEFINITION_REVIEW_V1,
                )
                if payload.get("_safety_blocked"):
                    ai_review = {
                        "available": False,
                        "blocked": True,
                        "warnings": warnings,
                    }
                else:
                    ai_review = {"available": True, "review": payload, "warnings": warnings}
            except AgentLlmUnavailable:
                ai_review = {"available": False, "reason": "llm_unavailable"}
        review = {"deterministic_checks": deterministic, "ai_review": ai_review}
        return {
            **updates,
            "definition_review": review,
            "trace": _trace(state, "review_research_definition", "reviewed"),
            "summary": "Completed research definition review.",
        }

    def retrieve_methodology(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "retrieve_methodology")
        intent = state.get("intent") or "review_evidence"
        query_map = {
            "review_definition": "research protocol hypothesis falsifiability",
            "review_readiness": "research protocol robustness decision readiness",
            "review_evidence": "validation robustness benchmark transaction costs",
            "prepare_decision": "decision rules promote hold reject archive",
        }
        research_type = state.get("research_type") or "trend_following"
        if research_type == "factor":
            query_map["review_evidence"] = "factor RankIC ICIR quantile validation"
        hits = retrieve_rulebook(
            query=query_map.get(intent, "research protocol"),
            research_type=research_type,
            top_k=4,
        )
        return {
            **updates,
            "knowledge_context": hits,
            "trace": _trace(
                state,
                "retrieve_methodology",
                "retrieved",
                ",".join(h["knowledge_id"] for h in hits),
            ),
            "summary": f"Retrieved {len(hits)} Research Rulebook sections.",
        }

    def inspect_available_evidence(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "inspect_available_evidence")
        snapshot = state.get("evidence_snapshot") or {}
        availability = snapshot.get("availability") or {}
        missing = [
            key
            for key, present in {
                "execution": availability.get("execution"),
                "benchmark": availability.get("benchmark"),
                "validation": availability.get("validation"),
                "factor_validation": availability.get("factor_validation"),
                "oos": availability.get("oos"),
                "parameter_sensitivity": availability.get("parameter_sensitivity"),
                "cost_sensitivity": availability.get("cost_sensitivity"),
                "data_quality": availability.get("data_quality"),
                "rank_ic": availability.get("rank_ic"),
            }.items()
            if not present
        ]
        # For factor studies, MA stages may be N/A
        if state.get("research_type") == "factor":
            missing = [m for m in missing if m not in {"execution", "oos", "parameter_sensitivity", "validation"}]
            if not availability.get("factor_validation"):
                missing = list(dict.fromkeys(missing + ["factor_validation", "rank_ic"]))
        return {
            **updates,
            "missing_evidence": missing,
            "trace": _trace(
                state,
                "inspect_available_evidence",
                "inspected",
                f"missing={len(missing)}",
            ),
            "summary": "Inspected available evidence without inventing metrics.",
        }

    def plan_tool_calls(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "plan_tool_calls")
        cycles = int(state.get("planning_cycles") or 0) + 1
        missing = list(state.get("missing_evidence") or [])
        intent = state.get("intent")
        planned: list[dict[str, Any]] = [
            {
                "tool_name": "retrieve_research_rulebook",
                "reason": "Refresh methodology citations for the current intent.",
                "arguments": {
                    "query": str(intent),
                    "research_type": state.get("research_type"),
                },
                "requires_approval": False,
            },
            {
                "tool_name": "get_latest_evidence_snapshot",
                "reason": "Confirm coherent evidence snapshot.",
                "arguments": {
                    "research_id": state.get("research_id"),
                    "evidence_snapshot_id": state.get("evidence_snapshot_id"),
                },
                "requires_approval": False,
            },
        ]
        if intent in {"review_readiness", "prepare_decision"}:
            planned.append(
                {
                    "tool_name": "build_decision_readiness",
                    "reason": "Compute deterministic workflow completeness.",
                    "arguments": {
                        "research_id": state.get("research_id"),
                        "evidence_snapshot_id": state.get("evidence_snapshot_id"),
                    },
                    "requires_approval": False,
                }
            )
        if "factor_validation" in missing and state.get("research_type") == "factor":
            planned.append(
                {
                    "tool_name": "run_factor_validation",
                    "reason": "Factor validation evidence is missing.",
                    "arguments": {"research_id": state.get("research_id"), "factor_id": "momentum"},
                    "requires_approval": True,
                }
            )
        if "validation" in missing or "oos" in missing:
            if state.get("research_type") == "trend_following":
                planned.append(
                    {
                        "tool_name": "run_oos_validation",
                        "reason": "OOS/validation evidence is missing.",
                        "arguments": {"research_id": state.get("research_id")},
                        "requires_approval": True,
                    }
                )
        if "cost_sensitivity" in missing and state.get("research_type") == "trend_following":
            planned.append(
                {
                    "tool_name": "run_cost_sensitivity",
                    "reason": "Transaction-cost sensitivity evidence is missing.",
                    "arguments": {"research_id": state.get("research_id")},
                    "requires_approval": True,
                }
            )

        # Optional LLM refinement (bounded)
        if state.get("llm_available") and llm is not None and cycles <= 2:
            try:
                payload, _, _ = generate_structured(
                    llm,
                    user_prompt=TOOL_PLANNING_V1
                    + "\n\nMissing evidence:\n"
                    + json.dumps(missing)
                    + "\nIntent:\n"
                    + str(intent),
                    system_prompt=GOVERNANCE_SYSTEM_V1 + "\n" + TOOL_PLANNING_V1,
                )
                llm_calls = payload.get("tool_calls")
                if isinstance(llm_calls, list):
                    for call in llm_calls[:MAX_TOOL_CALLS]:
                        if not isinstance(call, dict):
                            continue
                        name = str(call.get("tool_name") or "")
                        try:
                            validate_tool_call(name, call.get("arguments") or {})
                        except ToolRegistryError:
                            continue
                        planned.append(
                            {
                                "tool_name": name,
                                "reason": str(call.get("reason") or "LLM planned tool"),
                                "arguments": call.get("arguments") or {},
                                "requires_approval": bool(
                                    call.get("requires_approval")
                                    or validate_tool_call(name, call.get("arguments") or {}).requires_approval
                                ),
                            }
                        )
            except Exception:  # noqa: BLE001
                pass

        # Dedupe by tool name, cap
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for call in planned:
            name = call["tool_name"]
            if name in seen:
                continue
            seen.add(name)
            deduped.append(call)
            if len(deduped) >= MAX_TOOL_CALLS:
                break

        needs_approval = [c for c in deduped if c.get("requires_approval")]
        pending = {}
        status = "running"
        if needs_approval:
            pending = {
                "type": "tool_approval",
                "tools": needs_approval,
                "message": "Approve expensive deterministic tool runs before execution.",
            }
            status = "awaiting_approval"

        return {
            **updates,
            "planning_cycles": cycles,
            "requested_tools": deduped,
            "pending_approval": pending,
            "status": status,
            "trace": _trace(state, "plan_tool_calls", "planned", f"tools={len(deduped)}"),
            "summary": "Planned approved-registry tool calls.",
        }

    def request_tool_approval(state: AgentState) -> dict[str, Any]:
        """Interrupt node — state already set to awaiting_approval when needed."""
        updates = _bump(state, "request_tool_approval")
        action = state.get("approval_action")
        pending = state.get("pending_approval") or {}
        if not pending.get("tools"):
            return {
                **updates,
                "status": "running",
                "trace": _trace(state, "request_tool_approval", "no_approval_needed"),
            }
        if action in {None, ""}:
            return {
                **updates,
                "status": "awaiting_approval",
                "trace": _trace(state, "request_tool_approval", "waiting"),
                "summary": "Awaiting human approval for deterministic tools.",
            }
        if action == "cancel":
            return {
                **updates,
                "status": "cancelled",
                "summary": "Agent run cancelled by researcher.",
                "trace": _trace(state, "request_tool_approval", "cancelled"),
            }
        if action == "skip":
            skipped = [t.get("tool_name") for t in pending.get("tools") or []]
            remaining = [
                t for t in (state.get("requested_tools") or []) if not t.get("requires_approval")
            ]
            return {
                **updates,
                "status": "running",
                "requested_tools": remaining,
                "pending_approval": {},
                "approval_action": None,
                "missing_evidence": list(
                    dict.fromkeys(list(state.get("missing_evidence") or []) + [f"skipped:{n}" for n in skipped])
                ),
                "trace": _trace(state, "request_tool_approval", "skipped", ",".join(map(str, skipped))),
                "summary": "Skipped approval-required tools; evidence remains missing.",
            }
        # approve / edit / run_additional_validation
        tools = list(pending.get("tools") or [])
        payload = state.get("approval_payload") or {}
        if action == "edit" and isinstance(payload.get("tools"), list):
            tools = payload["tools"]
        return {
            **updates,
            "status": "running",
            "requested_tools": [
                *(t for t in (state.get("requested_tools") or []) if not t.get("requires_approval")),
                *tools,
            ],
            "pending_approval": {},
            "approval_action": None,
            "trace": _trace(state, "request_tool_approval", "approved"),
            "summary": "Human approved deterministic tool execution.",
        }

    def execute_approved_tools(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "execute_approved_tools")
        results = list(state.get("tool_results") or [])
        evidence_ids = []
        for call in state.get("requested_tools") or []:
            result = execute_tool(
                str(call.get("tool_name")),
                call.get("arguments") or {},
                state=dict(state),
                ctx=tool_ctx,
            )
            results.append(result)
            evidence_ids.extend(result.get("evidence_ids_created") or [])
        snapshot_id = state.get("evidence_snapshot_id")
        if evidence_ids:
            snapshot_id = evidence_ids[-1]
        return {
            **updates,
            "tool_results": results,
            "evidence_snapshot_id": snapshot_id,
            "requested_tools": [],
            "trace": _trace(
                state,
                "execute_approved_tools",
                "executed",
                f"results={len(results)}",
            ),
            "summary": "Executed approved tools via deterministic services.",
        }

    def refresh_evidence_snapshot(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "refresh_evidence_snapshot")
        snapshot_id = state.get("evidence_snapshot_id")
        if not snapshot_id:
            return {
                **updates,
                "evidence_snapshot": state.get("evidence_snapshot") or {},
                "trace": _trace(state, "refresh_evidence_snapshot", "no_snapshot"),
                "summary": "No evidence snapshot to refresh.",
            }
        stored = store.get(snapshot_id)
        if stored is None:
            return {
                **updates,
                "status": "failed",
                "errors": list(state.get("errors") or []) + ["Evidence snapshot missing after tools."],
                "trace": _trace(state, "refresh_evidence_snapshot", "missing"),
                "summary": "Failed: evidence snapshot missing.",
            }
        if stored.get("research_id") != state.get("research_id"):
            return {
                **updates,
                "status": "failed",
                "errors": list(state.get("errors") or []) + ["Stale or mixed evidence snapshot detected."],
                "trace": _trace(state, "refresh_evidence_snapshot", "stale_or_mixed"),
                "summary": "Inconclusive: mixed evidence across runs.",
            }
        snapshot = _build_evidence_availability(stored, research_type=state.get("research_type"))
        benchmark = stored.get("benchmark") or {}
        return {
            **updates,
            "evidence_snapshot": snapshot,
            "benchmark_evaluation": benchmark if isinstance(benchmark, dict) else {},
            "trace": _trace(state, "refresh_evidence_snapshot", "refreshed", snapshot_id),
            "summary": "Refreshed coherent evidence snapshot.",
        }

    def review_evidence(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "review_evidence")
        snapshot = state.get("evidence_snapshot") or {}
        knowledge = state.get("knowledge_context") or []
        evidence_ids = set(snapshot.get("evidence_ids") or [])
        knowledge_ids = {str(k.get("knowledge_id")) for k in knowledge}

        interpretation: dict[str, Any]
        if not state.get("llm_available") or llm is None:
            interpretation = {
                "available": False,
                "reason": "llm_unavailable",
                "executive_summary": "AI interpretation unavailable. Deterministic evidence remains unchanged.",
                "hypothesis_assessment": "inconclusive",
                "missing_evidence": list(state.get("missing_evidence") or []),
                "recommended_next_steps": [
                    "Configure LLM_PROVIDER/LLM_API_KEY for DeepSeek interpretation, or continue with deterministic Decision Center."
                ],
            }
        else:
            try:
                ctx_items = context_from_dicts(
                    [
                        {"citation_id": eid, "source_type": "evidence", "source_id": eid, "label": eid, "id": eid}
                        for eid in evidence_ids
                    ]
                    + [
                        {
                            "citation_id": k.get("knowledge_id"),
                            "knowledge_id": k.get("knowledge_id"),
                            "source_type": "knowledge",
                            "title": k.get("title"),
                            "excerpt": k.get("excerpt"),
                        }
                        for k in knowledge
                    ]
                    + [{"citation_id": "snapshot", "source_type": "evidence", "label": "snapshot", "content": snapshot}]
                )
                payload, result, warnings = generate_structured(
                    llm,
                    user_prompt=EVIDENCE_REVIEW_V1
                    + "\n\nSnapshot:\n"
                    + json.dumps(snapshot, ensure_ascii=False)[:8000]
                    + "\n\nKnowledge IDs:\n"
                    + json.dumps(sorted(knowledge_ids)),
                    context_items=ctx_items,
                    system_prompt=GOVERNANCE_SYSTEM_V1 + "\n" + EVIDENCE_REVIEW_V1,
                )
                if payload.get("_safety_blocked"):
                    interpretation = {
                        "available": False,
                        "blocked": True,
                        "warnings": warnings,
                        "hypothesis_assessment": "inconclusive",
                        "executive_summary": payload.get("_sanitized_answer")
                        or "AI output blocked by safety policy.",
                    }
                else:
                    interpretation = _validate_evidence_review(payload, evidence_ids, knowledge_ids)
                    interpretation["available"] = True
                    interpretation["warnings"] = warnings
                    if result:
                        interpretation["model"] = result.model
            except AgentLlmUnavailable:
                interpretation = {
                    "available": False,
                    "reason": "llm_unavailable",
                    "hypothesis_assessment": "inconclusive",
                }

        return {
            **updates,
            "ai_interpretation": interpretation,
            "recommended_next_steps": list(interpretation.get("recommended_next_steps") or []),
            "missing_evidence": list(
                dict.fromkeys(
                    list(state.get("missing_evidence") or [])
                    + list(interpretation.get("missing_evidence") or [])
                )
            ),
            "trace": _trace(state, "review_evidence", "reviewed"),
            "summary": "Completed evidence review (AI interprets; metrics unchanged).",
        }

    def assess_completeness_node(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "assess_research_completeness")
        completeness = assess_research_completeness(
            research_definition=state.get("research_definition"),
            evidence_snapshot=state.get("evidence_snapshot"),
            research_type=str(state.get("research_type") or "trend_following"),
            decision_recorded=bool((state.get("human_decision") or {}).get("decision")),
        )
        return {
            **updates,
            "completeness": completeness,
            "decision_readiness": completeness,
            "trace": _trace(
                state,
                "assess_research_completeness",
                "assessed",
                completeness.get("overall", ""),
            ),
            "summary": f"Research Workflow Completion: {completeness.get('workflow_completion_pct')}%.",
        }

    def prepare_decision_review(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "prepare_decision_review")
        deterministic_suggestion = _deterministic_suggestion(state)
        agent_part: dict[str, Any] = {"available": False}
        if state.get("llm_available") and llm is not None:
            try:
                payload, _, warnings = generate_structured(
                    llm,
                    user_prompt=DECISION_REVIEW_V1
                    + "\n\ndeterministic_suggestion="
                    + deterministic_suggestion
                    + "\ncompleteness="
                    + json.dumps(state.get("completeness") or {})
                    + "\nai_interpretation="
                    + json.dumps(state.get("ai_interpretation") or {})[:4000],
                    system_prompt=GOVERNANCE_SYSTEM_V1 + "\n" + DECISION_REVIEW_V1,
                )
                if not payload.get("_safety_blocked"):
                    agent_part = {
                        "available": True,
                        "agent_interpretation": payload.get("agent_interpretation"),
                        "supporting_checks": payload.get("supporting_checks") or [],
                        "failed_checks": payload.get("failed_checks") or [],
                        "conflicting_evidence": payload.get("conflicting_evidence") or [],
                        "missing_validation": payload.get("missing_validation") or [],
                        "recommended_human_action": payload.get("recommended_human_action")
                        or "review",
                        "proposed_rationale_draft": payload.get("proposed_rationale_draft"),
                        "warnings": warnings,
                    }
            except AgentLlmUnavailable:
                agent_part = {"available": False, "reason": "llm_unavailable"}

        decision_review = {
            "deterministic_suggestion": deterministic_suggestion,
            "agent_interpretation": agent_part.get("agent_interpretation")
            or "AI decision interpretation unavailable; use deterministic suggestion and Decision Center.",
            "supporting_checks": agent_part.get("supporting_checks") or [],
            "failed_checks": agent_part.get("failed_checks") or [],
            "conflicting_evidence": agent_part.get("conflicting_evidence") or [],
            "missing_validation": agent_part.get("missing_validation")
            or list(state.get("missing_evidence") or []),
            "recommended_human_action": agent_part.get("recommended_human_action") or "review",
            "proposed_rationale_draft": agent_part.get("proposed_rationale_draft")
            or f"Deterministic suggestion is {deterministic_suggestion}. Final decision remains human-owned.",
            "ai_available": bool(agent_part.get("available")),
        }
        pending = {
            "type": "human_decision",
            "message": "Record Promote / Hold / Reject / Archive, run additional validation, or cancel.",
            "deterministic_suggestion": deterministic_suggestion,
        }
        return {
            **updates,
            "decision_review": decision_review,
            "pending_approval": pending,
            "status": "awaiting_approval",
            "trace": _trace(state, "prepare_decision_review", "prepared"),
            "summary": "Prepared decision review; awaiting human decision.",
        }

    def await_human_decision(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "await_human_decision")
        action = state.get("approval_action")
        payload = state.get("approval_payload") or {}
        if action in {None, ""}:
            return {
                **updates,
                "status": "awaiting_approval",
                "trace": _trace(state, "await_human_decision", "waiting"),
            }
        if action == "cancel":
            return {
                **updates,
                "status": "cancelled",
                "pending_approval": {},
                "summary": "Agent run cancelled before recording a decision.",
                "trace": _trace(state, "await_human_decision", "cancelled"),
            }
        if action == "run_additional_validation":
            return {
                **updates,
                "status": "running",
                "pending_approval": {},
                "approval_action": None,
                "missing_evidence": list(
                    dict.fromkeys(list(state.get("missing_evidence") or []) + ["additional_validation_requested"])
                ),
                "requested_tools": [
                    {
                        "tool_name": "run_oos_validation"
                        if state.get("research_type") == "trend_following"
                        else "run_factor_validation",
                        "reason": "Human requested additional validation.",
                        "arguments": {"research_id": state.get("research_id")},
                        "requires_approval": False,
                    }
                ],
                "trace": _trace(state, "await_human_decision", "additional_validation"),
                "summary": "Routing to additional deterministic validation.",
            }
        if action == "record_decision":
            decision = str(payload.get("decision") or "").strip()
            rationale = str(payload.get("rationale") or "").strip()
            suggestion = (state.get("decision_review") or {}).get("deterministic_suggestion")
            override = str(payload.get("override_rationale") or "").strip()
            if not decision or not rationale:
                return {
                    **updates,
                    "status": "awaiting_approval",
                    "errors": list(state.get("errors") or [])
                    + ["record_decision requires decision and rationale."],
                    "trace": _trace(state, "await_human_decision", "missing_rationale"),
                }
            if suggestion and decision != suggestion and not override:
                return {
                    **updates,
                    "status": "awaiting_approval",
                    "errors": list(state.get("errors") or [])
                    + ["Override rationale required when human decision differs from deterministic suggestion."],
                    "trace": _trace(state, "await_human_decision", "override_required"),
                }
            result = execute_tool(
                "record_human_decision",
                {
                    "research_id": state.get("research_id"),
                    "decision": decision,
                    "rationale": rationale,
                    "override_rationale": override or None,
                    "evidence_snapshot_id": state.get("evidence_snapshot_id"),
                },
                state=dict(state),
                ctx=tool_ctx,
            )
            human = {
                "decision": decision,
                "rationale": rationale,
                "override_rationale": override or None,
                "deterministic_suggestion": suggestion,
                "evidence_snapshot_id": state.get("evidence_snapshot_id"),
                "agent_run_id": state.get("agent_run_id"),
                "recorded_at": utc_now_iso(),
            }
            return {
                **updates,
                "human_decision": human,
                "tool_results": list(state.get("tool_results") or []) + [result],
                "pending_approval": {},
                "approval_action": None,
                "status": "running",
                "trace": _trace(state, "await_human_decision", "recorded", decision),
                "summary": f"Human decision recorded: {decision}.",
            }
        # approve/skip/edit at this node treated as continue without decision
        return {
            **updates,
            "status": "running",
            "pending_approval": {},
            "approval_action": None,
            "trace": _trace(state, "await_human_decision", "continued_without_decision"),
            "summary": "Continued without recording a new human decision.",
        }

    def finalize_agent_run(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "finalize_agent_run")
        status = state.get("status")
        if status in {"cancelled", "failed"}:
            return {
                **updates,
                "status": status,
                "trace": _trace(state, "finalize_agent_run", status or "done"),
            }
        return {
            **updates,
            "status": "completed",
            "pending_approval": {},
            "summary": state.get("summary") or "Governance agent run completed.",
            "trace": _trace(state, "finalize_agent_run", "completed"),
        }

    def handle_agent_error(state: AgentState) -> dict[str, Any]:
        updates = _bump(state, "handle_agent_error")
        return {
            **updates,
            "status": "failed",
            "summary": "Agent run failed.",
            "trace": _trace(state, "handle_agent_error", "failed"),
        }

    return {
        "classify_intent": classify_intent,
        "load_research_context": load_research_context,
        "review_research_definition": review_research_definition,
        "retrieve_methodology": retrieve_methodology,
        "inspect_available_evidence": inspect_available_evidence,
        "plan_tool_calls": plan_tool_calls,
        "request_tool_approval": request_tool_approval,
        "execute_approved_tools": execute_approved_tools,
        "refresh_evidence_snapshot": refresh_evidence_snapshot,
        "review_evidence": review_evidence,
        "assess_research_completeness": assess_completeness_node,
        "prepare_decision_review": prepare_decision_review,
        "await_human_decision": await_human_decision,
        "finalize_agent_run": finalize_agent_run,
        "handle_agent_error": handle_agent_error,
    }


def _build_evidence_availability(stored: dict[str, Any], *, research_type: str | None) -> dict[str, Any]:
    stages = stored.get("stages") or {}
    ic_summary = ((stored.get("ic") or {}).get("summary")) or {}
    availability = {
        "execution": bool(stored.get("execution") or stored.get("metrics")),
        "benchmark": bool(stored.get("benchmark")),
        "validation": stored.get("validation_status") == "completed" or bool(stages),
        "factor_validation": stored.get("evidence_kind") == "factor_validation"
        or stored.get("template") == "cross_sectional_factor",
        "oos": bool(stages.get("out_of_sample")),
        "parameter_sensitivity": bool(stages.get("parameter_sensitivity")),
        "cost_sensitivity": bool(stages.get("transaction_cost_sensitivity")),
        "data_quality": bool(stages.get("data_quality")),
        "rank_ic": ic_summary.get("mean_rank_ic") is not None,
        "robustness": bool(
            stages.get("out_of_sample")
            or stages.get("parameter_sensitivity")
            or stages.get("transaction_cost_sensitivity")
        ),
        "known_limitations": True,
    }
    evidence_ids = ["snapshot:root"]
    if availability["rank_ic"]:
        evidence_ids.extend(["evidence:mean_rank_ic", "evidence:icir"])
    if availability["benchmark"]:
        evidence_ids.append("evidence:benchmark")
    for stage_name, present in {
        "oos": availability["oos"],
        "parameter_sensitivity": availability["parameter_sensitivity"],
        "cost_sensitivity": availability["cost_sensitivity"],
        "data_quality": availability["data_quality"],
    }.items():
        if present:
            evidence_ids.append(f"evidence:{stage_name}")
    return {
        "validation_run_id": stored.get("validation_run_id"),
        "generated_at": stored.get("generated_at"),
        "evidence_kind": stored.get("evidence_kind") or stored.get("template"),
        "research_type": research_type,
        "availability": availability,
        "evidence_ids": evidence_ids,
        "ic_summary": ic_summary or None,
        "benchmark": stored.get("benchmark"),
        "warnings": stored.get("warnings") or [],
        # Keep metrics read-only references — agent must not edit
        "metric_refs": {
            "mean_rank_ic": ic_summary.get("mean_rank_ic"),
            "icir": ic_summary.get("icir"),
            "stages_present": sorted(stages.keys()) if isinstance(stages, dict) else [],
        },
    }


def _validate_evidence_review(
    payload: dict[str, Any],
    evidence_ids: set[str],
    knowledge_ids: set[str],
) -> dict[str, Any]:
    def _filter_claims(items: Any) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        if not isinstance(items, list):
            return out
        for item in items:
            if not isinstance(item, dict):
                continue
            eids = [e for e in (item.get("evidence_ids") or []) if e in evidence_ids]
            kids = [k for k in (item.get("knowledge_ids") or []) if k in knowledge_ids]
            out.append(
                {
                    "claim": str(item.get("claim") or ""),
                    "evidence_ids": eids,
                    "knowledge_ids": kids,
                }
            )
        return out

    assessment = str(payload.get("hypothesis_assessment") or "inconclusive")
    if assessment not in {
        "supported",
        "partially_supported",
        "not_supported",
        "inconclusive",
    }:
        assessment = "inconclusive"
    return {
        "executive_summary": str(payload.get("executive_summary") or ""),
        "hypothesis_assessment": assessment,
        "benchmark_assessment": str(payload.get("benchmark_assessment") or ""),
        "supporting_evidence": _filter_claims(payload.get("supporting_evidence")),
        "contradicting_evidence": _filter_claims(payload.get("contradicting_evidence")),
        "missing_evidence": [str(x) for x in (payload.get("missing_evidence") or [])],
        "robustness_concerns": [str(x) for x in (payload.get("robustness_concerns") or [])],
        "data_quality_concerns": [str(x) for x in (payload.get("data_quality_concerns") or [])],
        "limitations": [str(x) for x in (payload.get("limitations") or [])],
        "recommended_next_steps": [str(x) for x in (payload.get("recommended_next_steps") or [])],
    }


def _deterministic_suggestion(state: AgentState) -> str:
    completeness = state.get("completeness") or {}
    overall = completeness.get("overall")
    missing = state.get("missing_evidence") or []
    interpretation = state.get("ai_interpretation") or {}
    assessment = interpretation.get("hypothesis_assessment")
    if overall == "blocked":
        return "Reject"
    if missing or overall == "incomplete":
        return "Hold"
    if assessment == "not_supported":
        return "Reject"
    if assessment in {"supported", "partially_supported"} and overall == "complete":
        return "Promote"
    return "Hold"
