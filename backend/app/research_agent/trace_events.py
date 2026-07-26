"""Typed execution-trace helpers for the Governance Agent.

Events are result summaries only — never chain-of-thought, prompts, or secrets.
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

Authority = Literal["system", "deterministic", "llm", "human"]
EventStatus = Literal[
    "pending",
    "running",
    "completed",
    "blocked",
    "unavailable",
    "failed",
]

_SECRET_RE = re.compile(
    r"(api[_-]?key|secret|password|token|supabase_db_url|postgres://|postgresql://)",
    re.I,
)

# node → default authority for workflow steps
_NODE_AUTHORITY: dict[str, Authority] = {
    "classify_intent": "system",
    "load_research_context": "system",
    "review_research_definition": "llm",
    "retrieve_methodology": "system",
    "inspect_available_evidence": "deterministic",
    "plan_tool_calls": "system",
    "request_tool_approval": "human",
    "execute_approved_tools": "deterministic",
    "refresh_evidence_snapshot": "deterministic",
    "review_evidence": "llm",
    "assess_research_completeness": "deterministic",
    "prepare_decision_review": "deterministic",
    "await_human_decision": "human",
    "finalize_agent_run": "system",
    "handle_agent_error": "system",
}

_EVENT_LABELS: dict[tuple[str, str], str] = {
    ("classify_intent", "classified"): "Classified review intent",
    ("classify_intent", "rejected_unsupported"): "Rejected unsupported request",
    ("classify_intent", "rejected_intent"): "Rejected unsupported intent",
    ("load_research_context", "loaded"): "Loaded research context",
    ("load_research_context", "snapshot_mismatch"): "Evidence snapshot mismatch",
    ("review_research_definition", "reviewed"): "Reviewed research definition",
    ("retrieve_methodology", "retrieved"): "Retrieved methodology",
    ("inspect_available_evidence", "inspected"): "Inspected available evidence",
    ("plan_tool_calls", "planned"): "Planned deterministic tools",
    ("request_tool_approval", "waiting"): "Approval required for validation",
    ("request_tool_approval", "approved"): "Human approved tool plan",
    ("request_tool_approval", "skipped"): "Human skipped tools",
    ("request_tool_approval", "cancelled"): "Human cancelled approval",
    ("request_tool_approval", "no_approval_needed"): "No approval required",
    ("execute_approved_tools", "executed"): "Executed approved tools",
    ("refresh_evidence_snapshot", "refreshed"): "Refreshed evidence snapshot",
    ("refresh_evidence_snapshot", "no_snapshot"): "No evidence snapshot yet",
    ("refresh_evidence_snapshot", "missing"): "Evidence snapshot missing",
    ("refresh_evidence_snapshot", "stale_or_mixed"): "Evidence snapshot stale",
    ("review_evidence", "reviewed"): "LLM evidence interpretation",
    ("assess_research_completeness", "assessed"): "Assessed research completeness",
    ("prepare_decision_review", "prepared"): "Prepared decision review",
    ("await_human_decision", "waiting"): "Waiting for human decision",
    ("await_human_decision", "recorded"): "Human decision recorded",
    ("await_human_decision", "cancelled"): "Human cancelled decision wait",
    ("await_human_decision", "additional_validation"): "Additional validation requested",
    ("finalize_agent_run", "completed"): "Agent run finalized",
    ("handle_agent_error", "failed"): "Agent workflow failed",
}


def _safe_summary(text: str, *, limit: int = 240) -> str:
    cleaned = " ".join(str(text or "").split())
    if _SECRET_RE.search(cleaned):
        return "Sensitive detail redacted."
    if len(cleaned) > limit:
        return cleaned[: limit - 1] + "…"
    return cleaned


def authority_for(node: str, event: str) -> Authority:
    if event in {"waiting", "approved", "skipped", "cancelled", "recorded"}:
        if node in {"request_tool_approval", "await_human_decision"}:
            return "human"
    if event in {"reviewed"} and node in {
        "review_research_definition",
        "review_evidence",
    }:
        return "llm"
    return _NODE_AUTHORITY.get(node, "system")


def status_for(event: str, *, llm_available: bool, node: str) -> EventStatus:
    if event in {"waiting"}:
        return "blocked"
    if event in {
        "failed",
        "rejected_unsupported",
        "rejected_intent",
        "invalid_decision",
        "missing_rationale",
        "override_required",
        "snapshot_mismatch",
        "stale_or_mixed",
        "missing",
    }:
        return "failed" if event in {"failed", "rejected_unsupported", "rejected_intent"} else "blocked"
    if node in {"review_research_definition", "review_evidence"} and not llm_available:
        if event in {"reviewed", "unavailable"}:
            return "unavailable"
    if event in {"cancelled"}:
        return "failed"
    return "completed"


def label_for(node: str, event: str) -> str:
    return _EVENT_LABELS.get((node, event), f"{node}: {event}")


def append_trace_event(
    state: dict[str, Any],
    node: str,
    event: str,
    detail: str = "",
    *,
    evidence_ids: Optional[list[str]] = None,
    methodology_citations: Optional[list[str]] = None,
    tool_name: Optional[str] = None,
    approval_required: bool = False,
) -> list[dict[str, Any]]:
    """Append one monotonic execution-trace event (backward-compatible fields included)."""
    trace = list(state.get("trace") or [])
    sequence = len(trace) + 1
    llm_available = bool(state.get("llm_available"))
    authority = authority_for(node, event)
    status = status_for(event, llm_available=llm_available, node=node)
    if (
        authority == "llm"
        and not llm_available
        and status == "completed"
    ):
        status = "unavailable"
    summary = _safe_summary(detail) if detail else label_for(node, event)
    if authority == "llm" and not llm_available:
        summary = "LLM interpretation unavailable (deterministic path continues)."
        status = "unavailable"

    entry = {
        "id": f"evt-{sequence:04d}",
        "sequence": sequence,
        "timestamp": None,  # filled below via utc import in caller path
        "node": node,
        "event": event,
        "label": label_for(node, event),
        "authority": authority,
        "status": status,
        "summary": summary,
        "evidence_ids": list(evidence_ids or []),
        "methodology_citations": list(methodology_citations or []),
        "tool_name": tool_name,
        "approval_required": bool(approval_required) or event == "waiting",
        # Legacy fields kept for existing tests/UI
        "step": sequence,
        "detail": _safe_summary(detail) if detail else "",
        "at": None,
    }
    from app.research_execution.market_data_port import utc_now_iso

    now = utc_now_iso()
    entry["timestamp"] = now
    entry["at"] = now
    trace.append(entry)
    return trace


def normalize_trace(trace: list[dict[str, Any]], *, llm_available: bool) -> list[dict[str, Any]]:
    """Ensure API responses always expose the typed execution-trace contract."""
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(trace or [], start=1):
        if not isinstance(raw, dict):
            continue
        node = str(raw.get("node") or "unknown")
        event = str(raw.get("event") or "event")
        sequence = int(raw.get("sequence") or raw.get("step") or index)
        authority = raw.get("authority") or authority_for(node, event)
        status = raw.get("status") or status_for(
            event, llm_available=llm_available, node=node
        )
        if authority == "llm" and not llm_available and status == "completed":
            status = "unavailable"
        detail = str(raw.get("detail") or raw.get("summary") or "")
        summary = _safe_summary(
            str(raw.get("summary") or detail or label_for(node, event))
        )
        if authority == "llm" and not llm_available:
            summary = "LLM interpretation unavailable (deterministic path continues)."
            status = "unavailable"
        timestamp = raw.get("timestamp") or raw.get("at")
        normalized.append(
            {
                "id": str(raw.get("id") or f"evt-{sequence:04d}"),
                "sequence": sequence,
                "timestamp": timestamp,
                "node": node,
                "event": event,
                "label": str(raw.get("label") or label_for(node, event)),
                "authority": authority,
                "status": status,
                "summary": summary,
                "evidence_ids": list(raw.get("evidence_ids") or []),
                "methodology_citations": list(raw.get("methodology_citations") or []),
                "tool_name": raw.get("tool_name"),
                "approval_required": bool(raw.get("approval_required")),
                "step": sequence,
                "detail": _safe_summary(detail) if detail else "",
                "at": timestamp,
            }
        )
    normalized.sort(key=lambda item: int(item["sequence"]))
    return normalized


def build_run_observability(state: dict[str, Any]) -> dict[str, Any]:
    """Extra metadata for Agent API detail responses."""
    decision_review = state.get("decision_review") or {}
    pending = state.get("pending_approval") or {}
    llm_available = bool(state.get("llm_available"))
    ai = state.get("ai_interpretation") or {}
    llm_used = bool(llm_available and ai.get("available") is True)
    interpretation_status = (
        "completed"
        if llm_used
        else ("unavailable" if not llm_available or ai.get("available") is False else "pending")
    )
    return {
        "llm_used": llm_used,
        "llm_interpretation_status": interpretation_status,
        "rulebook_version": (
            (state.get("knowledge_context") or [{}])[0].get("version")
            if state.get("knowledge_context")
            else None
        ),
        "protocol_version": state.get("graph_version"),
        "tool_plan": state.get("requested_tools") or [],
        "approval_required": bool(pending),
        "deterministic_suggestion": decision_review.get("deterministic_suggestion"),
        "final_human_decision": state.get("human_decision") or None,
        "events": normalize_trace(state.get("trace") or [], llm_available=llm_available),
    }
