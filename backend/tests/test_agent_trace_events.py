"""Unit tests for Governance Agent execution-trace helpers."""

from app.research_agent.trace_events import (
    append_trace_event,
    build_run_observability,
    normalize_trace,
)


def test_append_trace_sequence_is_monotonic() -> None:
    state: dict = {"trace": [], "llm_available": False}
    state["trace"] = append_trace_event(state, "load_research_context", "loaded")
    state["trace"] = append_trace_event(
        state, "request_tool_approval", "waiting", approval_required=True
    )
    state["trace"] = append_trace_event(
        state, "execute_approved_tools", "executed", "tools=2"
    )

    assert [item["sequence"] for item in state["trace"]] == [1, 2, 3]
    assert state["trace"][0]["authority"] == "system"
    assert state["trace"][1]["authority"] == "human"
    assert state["trace"][1]["status"] == "blocked"
    assert state["trace"][1]["approval_required"] is True
    assert state["trace"][2]["authority"] == "deterministic"


def test_llm_unavailable_is_not_workflow_failure() -> None:
    events = normalize_trace(
        [
            {
                "step": 1,
                "node": "review_evidence",
                "event": "reviewed",
                "detail": "Would have been LLM text",
            }
        ],
        llm_available=False,
    )
    assert events[0]["authority"] == "llm"
    assert events[0]["status"] == "unavailable"
    assert "unavailable" in events[0]["summary"].lower()
    assert events[0]["status"] != "failed"


def test_secrets_and_prompts_are_redacted_from_summaries() -> None:
    state: dict = {"trace": [], "llm_available": True}
    state["trace"] = append_trace_event(
        state,
        "handle_agent_error",
        "failed",
        "connection failed SUPABASE_DB_URL=postgres://user:pass@host/db",
    )
    assert "SUPABASE_DB_URL" not in state["trace"][0]["summary"]
    assert "postgres://" not in state["trace"][0]["summary"]


def test_observability_exposes_events_and_llm_used_false_without_key() -> None:
    payload = build_run_observability(
        {
            "llm_available": False,
            "trace": [
                {"step": 1, "node": "plan_tool_calls", "event": "planned", "detail": "tools=1"}
            ],
            "requested_tools": [{"tool_name": "run_validation"}],
            "pending_approval": {"type": "tool_plan"},
            "decision_review": {"deterministic_suggestion": "Hold"},
            "ai_interpretation": {},
            "knowledge_context": [{"version": "rulebook-v1"}],
            "graph_version": "governance-graph-v1",
        }
    )
    assert payload["llm_used"] is False
    assert payload["llm_interpretation_status"] == "unavailable"
    assert payload["deterministic_suggestion"] == "Hold"
    assert payload["approval_required"] is True
    assert payload["events"][0]["sequence"] == 1
