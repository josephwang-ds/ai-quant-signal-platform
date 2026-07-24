"""Tests for Quant Research Governance Agent — graph, tools, rulebook, safety."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_agent as agent_route
from app.research_agent.service import GovernanceAgentService
from app.research_agent.tools import ToolRegistryError, validate_tool_call, list_tools
from app.research_agent.tools.handlers import ToolExecutionContext, execute_tool
from app.research_agent.completeness import assess_research_completeness
from app.research_knowledge.retrieval import ResearchRulebookRetriever, retrieve_rulebook
from app.research_copilot.fake_llm import FakeLlmAdapter
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.research_validation.result_store import InMemoryValidationResultStore


class GroundedGovernanceFakeLlm(LlmPort):
    def generate(self, *, system_prompt, user_prompt, context):
        if "tool_calls" in user_prompt.lower() or "approved registry" in user_prompt.lower():
            text = json.dumps(
                {
                    "goal": "inspect evidence",
                    "tool_calls": [
                        {
                            "tool_name": "get_latest_evidence_snapshot",
                            "reason": "read snapshot",
                            "arguments": {},
                            "requires_approval": False,
                        }
                    ],
                    "expected_evidence": [],
                    "stop_condition": "done",
                }
            )
        elif "hypothesis_assessment" in user_prompt or "Interpret ONLY" in user_prompt:
            text = json.dumps(
                {
                    "executive_summary": "Evidence is incomplete; RankIC unavailable remains unavailable.",
                    "hypothesis_assessment": "inconclusive",
                    "benchmark_assessment": "Benchmark not fully assessed.",
                    "supporting_evidence": [],
                    "contradicting_evidence": [],
                    "missing_evidence": ["factor_validation"],
                    "robustness_concerns": [],
                    "data_quality_concerns": [],
                    "limitations": ["Historical only"],
                    "recommended_next_steps": ["Run factor validation"],
                }
            )
        elif "deterministic_suggestion" in user_prompt:
            text = json.dumps(
                {
                    "agent_interpretation": "Hold is safer until validation completes.",
                    "supporting_checks": [],
                    "failed_checks": [],
                    "conflicting_evidence": [],
                    "missing_validation": ["factor_validation"],
                    "recommended_human_action": "run_additional_validation",
                    "proposed_rationale_draft": "Wait for coherent evidence.",
                }
            )
        else:
            text = json.dumps(
                {
                    "clarity": "Clear enough for a research draft.",
                    "falsifiability": "Hypothesis is testable.",
                    "missing_elements": ["null_hypothesis"],
                    "unsupported_causal_wording": [],
                    "possible_post_hoc_criteria": [],
                    "summary": "Definition needs a null hypothesis.",
                    "answer": "Definition needs a null hypothesis.",
                    "citation_ids": [],
                }
            )
        return LlmResult(text=text, model="fake-governance", latency_ms=1)


class FabricatingGovernanceFakeLlm(LlmPort):
    def generate(self, *, system_prompt, user_prompt, context):
        return LlmResult(
            text=json.dumps(
                {
                    "executive_summary": "Buy SPY now for guaranteed profit with Sharpe 9.99.",
                    "hypothesis_assessment": "supported",
                    "benchmark_assessment": "Excellent",
                    "supporting_evidence": [
                        {
                            "claim": "Invented",
                            "evidence_ids": ["evidence:does_not_exist"],
                            "knowledge_ids": ["kb.does_not_exist"],
                        }
                    ],
                    "contradicting_evidence": [],
                    "missing_evidence": [],
                    "robustness_concerns": [],
                    "data_quality_concerns": [],
                    "limitations": [],
                    "recommended_next_steps": ["Deploy live"],
                    "answer": "Buy SPY now for guaranteed profit with Sharpe 9.99.",
                    "citation_ids": [],
                }
            ),
            model="fabricating-governance",
            latency_ms=1,
        )


@pytest.fixture()
def store() -> InMemoryValidationResultStore:
    return InMemoryValidationResultStore()


@pytest.fixture()
def service(store: InMemoryValidationResultStore) -> GovernanceAgentService:
    return GovernanceAgentService(
        store,
        llm=GroundedGovernanceFakeLlm(),
        llm_available=True,
        llm_provider="fake",
        llm_model="fake-governance",
    )


def test_supported_intent_routes(service: GovernanceAgentService) -> None:
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "review_definition",
            "research_type": "trend_following",
            "research_definition": {
                "research_question": "Does MA20/60 beat buy-and-hold?",
                "hypothesis": "Trend filter improves risk-adjusted return historically.",
                "null_hypothesis": "No improvement vs buy-and-hold.",
                "benchmark": "Buy-and-Hold SPY",
                "symbol": "SPY",
                "evaluation_period": "2018-2024",
                "success_criteria": [{"name": "oos_completed", "status": "active"}],
                "outcome_metrics": ["sharpe", "max_drawdown"],
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["status"] in {"completed", "awaiting_approval", "running"}
    assert detail["definition_review"]
    assert detail["knowledge_context"]
    assert detail["completeness"]["label"] == "Research Workflow Completion"
    assert "AI Confidence" not in json.dumps(detail)


def test_unsupported_intent_fails_safely(service: GovernanceAgentService) -> None:
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "review_evidence",
            "user_question": "What stock should I buy?",
            "research_definition": {"research_question": "x"},
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["status"] == "failed"
    assert detail["errors"]


def test_tool_registry_rejects_unknown_and_invalid_args() -> None:
    with pytest.raises(ToolRegistryError):
        validate_tool_call("hack_the_broker", {})
    with pytest.raises(ToolRegistryError):
        validate_tool_call("get_research_definition", {"evil": 1})
    assert any(t["name"] == "run_factor_validation" for t in list_tools())


def test_read_only_tool_does_not_mutate_store(store: InMemoryValidationResultStore) -> None:
    run_id = store.save(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "evidence_kind": "factor_validation",
            "ic": {"summary": {"mean_rank_ic": 0.1, "icir": 0.5}},
            "benchmark": {"decision": "hold"},
        }
    )
    before = store.get(run_id)
    ctx = ToolExecutionContext(store=store)
    result = execute_tool(
        "get_validation_results",
        {"evidence_snapshot_id": run_id},
        state={
            "research_id": "cross-sectional-factor-sector-etfs",
            "evidence_snapshot_id": run_id,
        },
        ctx=ctx,
    )
    after = store.get(run_id)
    assert result["status"] == "completed"
    assert after == before


def test_write_sensitive_tool_does_not_silently_apply(store: InMemoryValidationResultStore) -> None:
    ctx = ToolExecutionContext(store=store)
    result = execute_tool(
        "apply_research_definition_draft",
        {"research_id": "ma-crossover-spy", "draft": {"hypothesis": "x"}},
        state={"research_id": "ma-crossover-spy"},
        ctx=ctx,
    )
    assert result["status"] == "awaiting_human_confirmation"


def test_rulebook_factor_vs_trend_retrieval() -> None:
    factor_hits = retrieve_rulebook(
        query="RankIC ICIR quantile factor validation",
        research_type="factor",
        top_k=3,
    )
    assert factor_hits
    assert any("factor" in h["knowledge_id"] or "rank_ic" in h["knowledge_id"] for h in factor_hits)
    assert all(h["status"] == "active" for h in factor_hits)

    trend_hits = retrieve_rulebook(
        query="trend following moving average buy-and-hold lag",
        research_type="trend_following",
        top_k=3,
    )
    assert trend_hits
    assert any("trend" in h["knowledge_id"] for h in trend_hits)


def test_deprecated_knowledge_excluded() -> None:
    hits = ResearchRulebookRetriever().retrieve(query="deprecated example", top_k=10)
    assert all(h.knowledge_id != "kb.deprecated_example.v0" for h in hits)


def test_completeness_is_not_ai_confidence() -> None:
    result = assess_research_completeness(
        research_definition={"research_question": "q", "hypothesis": "h"},
        evidence_snapshot={"availability": {}},
        research_type="trend_following",
    )
    assert result["overall"] == "incomplete"
    assert "confidence" not in result["label"].lower()


def test_tool_approval_pauses_and_resume_skip(
    store: InMemoryValidationResultStore,
) -> None:
    service = GovernanceAgentService(
        store,
        llm=GroundedGovernanceFakeLlm(),
        llm_available=True,
        llm_provider="fake",
        llm_model="fake-governance",
    )
    summary = service.create_run(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "intent": "review_evidence",
            "research_type": "factor",
            "research_definition": {
                "research_question": "Does momentum RankIC stay positive?",
                "hypothesis": "Momentum has positive historical RankIC.",
                "universe": "us_sector_etfs",
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["status"] == "awaiting_approval"
    assert (detail.get("pending_approval") or {}).get("type") == "tool_approval"

    resumed = service.resume_run(summary["agent_run_id"], "skip", {})
    assert resumed["status"] in {"completed", "awaiting_approval", "running"}
    assert any(str(m).startswith("skipped:") for m in resumed.get("missing_evidence") or [])


def test_prepare_decision_records_without_overwrite(
    store: InMemoryValidationResultStore,
) -> None:
    service = GovernanceAgentService(
        store,
        llm=GroundedGovernanceFakeLlm(),
        llm_available=True,
        llm_provider="fake",
        llm_model="fake-governance",
    )
    run_id = store.save(
        {
            "research_id": "ma-crossover-spy",
            "validation_status": "completed",
            "stages": {
                "out_of_sample": {"status": "completed"},
                "parameter_sensitivity": {"status": "completed"},
                "transaction_cost_sensitivity": {"status": "completed"},
                "data_quality": {"status": "completed"},
            },
            "benchmark": {"decision": "hold"},
            "metrics": {"sharpe_ratio": 0.5},
        }
    )
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "prepare_decision",
            "research_type": "trend_following",
            "evidence_snapshot_id": run_id,
            "previous_decisions": [
                {"decision": "Hold", "rationale": "Earlier hold", "recorded_at": "2026-01-01"}
            ],
            "research_definition": {
                "research_question": "q",
                "hypothesis": "h",
                "null_hypothesis": "n",
                "benchmark": "Buy-and-Hold",
                "symbol": "SPY",
                "evaluation_period": "2018-2024",
                "success_criteria": [{"status": "active"}],
                "outcome_metrics": ["sharpe"],
                "known_limitations": ["demo"],
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    # May pause for tool approval or human decision depending on missing tools
    if detail["status"] == "awaiting_approval" and detail["pending_approval"].get("type") == "tool_approval":
        detail = service.resume_run(summary["agent_run_id"], "skip", {})
    if detail["status"] == "awaiting_approval" and detail["pending_approval"].get("type") == "human_decision":
        detail = service.resume_run(
            summary["agent_run_id"],
            "record_decision",
            {
                "decision": "Promote",
                "rationale": "Human accepts with caveats.",
                "override_rationale": "Override Hold suggestion after review.",
            },
        )
    assert detail["status"] in {"completed", "awaiting_approval"}
    prior = service.decision_log["ma-crossover-spy"]
    assert prior[0]["decision"] == "Hold"
    if detail.get("human_decision", {}).get("decision"):
        assert prior[-1]["decision"] == "Promote"
        assert len(prior) >= 2


def test_fabricating_review_is_blocked_or_sanitized(
    store: InMemoryValidationResultStore,
) -> None:
    service = GovernanceAgentService(
        store,
        llm=FabricatingGovernanceFakeLlm(),
        llm_available=True,
        llm_provider="fake",
        llm_model="fabricating",
    )
    run_id = store.save(
        {
            "research_id": "ma-crossover-spy",
            "validation_status": "completed",
            "stages": {"out_of_sample": {"status": "completed"}},
            "benchmark": {"decision": "hold"},
        }
    )
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "review_evidence",
            "evidence_snapshot_id": run_id,
            "research_definition": {"research_question": "q", "hypothesis": "h", "symbol": "SPY"},
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    if detail["status"] == "awaiting_approval":
        detail = service.resume_run(summary["agent_run_id"], "skip", {})
    text = json.dumps(detail.get("ai_interpretation") or {}).lower()
    assert "guaranteed profit" not in text or detail["ai_interpretation"].get("blocked")
    claims = (detail.get("ai_interpretation") or {}).get("supporting_evidence") or []
    for claim in claims:
        assert "evidence:does_not_exist" not in claim.get("evidence_ids", [])


def test_agent_api_and_no_key_still_runs_deterministically(
    monkeypatch: pytest.MonkeyPatch, store: InMemoryValidationResultStore
) -> None:
    service = GovernanceAgentService(
        store,
        llm=None,
        llm_available=False,
    )
    app = FastAPI()
    app.include_router(agent_route.router)
    monkeypatch.setattr(agent_route, "get_governance_agent_service", lambda: service)
    client = TestClient(app)
    response = client.post(
        "/api/v1/research/agent/runs",
        json={
            "research_id": "ma-crossover-spy",
            "intent": "review_readiness",
            "research_definition": {
                "research_question": "q",
                "hypothesis": "h",
                "symbol": "SPY",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    detail = client.get(f"/api/v1/research/agent/runs/{body['agent_run_id']}").json()
    if detail["status"] == "awaiting_approval":
        detail = client.post(
            f"/api/v1/research/agent/runs/{body['agent_run_id']}/resume",
            json={"action": "skip", "payload": {}},
        ).json()
    assert detail["llm_available"] is False
    assert detail["completeness"]
    assert detail["knowledge_context"]


def test_cancel_agent_run(service: GovernanceAgentService) -> None:
    summary = service.create_run(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "intent": "review_evidence",
            "research_type": "factor",
            "research_definition": {"research_question": "q", "hypothesis": "h", "universe": "etfs"},
        }
    )
    cancelled = service.cancel_run(summary["agent_run_id"])
    assert cancelled["status"] == "cancelled"


def test_copilot_fake_still_importable() -> None:
    assert FakeLlmAdapter().model == "fake-copilot-v1"
