"""Deterministic research completeness evaluator — not AI confidence."""

from __future__ import annotations

from typing import Any, Literal

CompletenessStatus = Literal["complete", "incomplete", "blocked", "not_applicable"]


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _active_success_criteria(definition: dict[str, Any]) -> list[dict[str, Any]]:
    criteria = definition.get("success_criteria") or []
    return [
        item
        for item in criteria
        if isinstance(item, dict)
        and (
            item.get("active") is True
            or str(item.get("status") or "").lower() == "active"
        )
    ]


def assess_research_completeness(
    *,
    research_definition: dict[str, Any] | None,
    evidence_snapshot: dict[str, Any] | None,
    research_type: str,
    decision_recorded: bool = False,
) -> dict[str, Any]:
    definition = research_definition or {}
    snapshot = evidence_snapshot or {}
    available = snapshot.get("availability") or {}

    active_criteria = _active_success_criteria(definition)
    items = [
        {
            "id": "research_question",
            "label": "Research Question",
            "status": "complete" if _has_text(definition.get("research_question")) else "incomplete",
        },
        {
            "id": "hypothesis",
            "label": "Hypothesis",
            "status": "complete" if _has_text(definition.get("hypothesis")) else "incomplete",
        },
        {
            "id": "null_hypothesis",
            "label": "Null Hypothesis",
            "status": "complete"
            if _has_text(definition.get("null_hypothesis"))
            else "incomplete",
        },
        {
            "id": "benchmark",
            "label": "Benchmark",
            "status": "complete"
            if _has_text(definition.get("benchmark"))
            or available.get("benchmark") is True
            else "incomplete",
        },
        {
            "id": "success_criteria",
            "label": "Active Success Criteria",
            "status": "complete"
            if active_criteria
            else "incomplete",
        },
        {
            "id": "experiment",
            "label": "Experiment",
            "status": "complete"
            if available.get("execution") is True
            or available.get("factor_validation") is True
            else "incomplete",
        },
        {
            "id": "validation",
            "label": "Validation",
            "status": "complete"
            if (
                available.get("validation") is True
                or available.get("factor_validation") is True
            )
            else "incomplete",
        },
        {
            "id": "robustness",
            "label": "Robustness",
            "status": "complete"
            if available.get("robustness") is True
            else "not_applicable"
            if research_type == "factor"
            else "incomplete",
        },
        {
            "id": "known_limitations",
            "label": "Known Limitations",
            "status": "complete"
            if definition.get("known_limitations")
            else "incomplete",
        },
        {
            "id": "decision",
            "label": "Decision",
            "status": "complete" if decision_recorded else "incomplete",
        },
    ]

    for item in items:
        if item["status"] == "blocked":
            continue
        if item["id"] == "validation" and available.get("validation_failed"):
            item["status"] = "blocked"

    countable = [i for i in items if i["status"] != "not_applicable"]
    pre_decision = [i for i in countable if i["id"] != "decision"]
    completed = sum(1 for i in countable if i["status"] == "complete")
    total = len(countable)
    decision_ready = bool(pre_decision) and all(
        item["status"] == "complete" for item in pre_decision
    )
    overall: CompletenessStatus
    if any(i["status"] == "blocked" for i in items):
        overall = "blocked"
    elif completed == total and total > 0:
        overall = "complete"
    else:
        overall = "incomplete"

    return {
        "overall": overall,
        "workflow_completion_pct": round(100.0 * completed / total, 1) if total else 0.0,
        "completed_count": completed,
        "total_count": total,
        "decision_ready": decision_ready,
        "pre_decision_completed_count": sum(
            1 for item in pre_decision if item["status"] == "complete"
        ),
        "pre_decision_total_count": len(pre_decision),
        "items": items,
        "label": "Research Workflow Completion",
        "note": "Workflow completeness only — not probability of success or AI confidence.",
    }
