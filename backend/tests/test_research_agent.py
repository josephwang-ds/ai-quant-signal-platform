"""Tests for Quant Research Governance Agent — graph, tools, rulebook, safety."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_agent as agent_route
from app.research_agent.service import GovernanceAgentService
from app.research_agent.graph.nodes import _deterministic_suggestion
from app.research_agent.llm_bridge import generate_structured
from app.research_agent.llm_schemas import EvidenceReviewOutput
from app.research_agent.tools import ToolRegistryError, validate_tool_call, list_tools
from app.research_agent.tools.handlers import ToolExecutionContext, execute_tool
from app.research_agent.completeness import assess_research_completeness
from app.research_knowledge.retrieval import ResearchRulebookRetriever, retrieve_rulebook
from app.research_copilot.fake_llm import FakeLlmAdapter
from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.research_validation.result_store import InMemoryValidationResultStore
from app.research_validation.service import ResearchValidationService
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"


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


def test_real_trend_validation_snapshot_is_agent_compatible(
    store: InMemoryValidationResultStore,
) -> None:
    validation = ResearchValidationService(
        FixtureMarketDataAdapter(FIXTURE),
        store,
    ).execute({"research_id": "ma-crossover-spy"})
    assert isinstance(validation["stages"], list)

    service = GovernanceAgentService(store, llm=None, llm_available=False)
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "review_readiness",
            "research_type": "trend_following",
            "evidence_snapshot_id": validation["validation_run_id"],
            "research_definition": {
                "research_question": "Does MA20/60 improve historical outcomes?",
                "hypothesis": "The lagged trend filter improves configured outcomes.",
                "null_hypothesis": "It does not improve configured outcomes.",
                "benchmark": "SPY Buy and Hold",
                "symbol": "SPY",
                "evaluation_period": "2018 to latest",
                "success_criteria": [{"metric": "excess_return", "active": True}],
                "outcome_metrics": ["excess_return"],
                "known_limitations": ["Historical evidence only."],
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["status"] == "completed"
    assert detail["missing_evidence"] == []
    assert detail["completeness"]["decision_ready"] is True


def test_factor_contract_does_not_require_trend_evidence(
    store: InMemoryValidationResultStore,
) -> None:
    run_id = store.save(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "template": "cross_sectional_factor",
            "evidence_kind": "factor_validation",
            "validation_status": "completed",
            "ic": {"summary": {"mean_rank_ic": 0.03, "icir": 0.4}},
            "benchmark": {"verdict": "pass", "checks": []},
            "quantiles": {"n_rebalances": 24},
            "warnings": [],
        }
    )
    service = GovernanceAgentService(store, llm=None, llm_available=False)
    summary = service.create_run(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "intent": "review_readiness",
            "research_type": "factor",
            "evidence_snapshot_id": run_id,
            "research_definition": {
                "research_question": "Does the factor rank future returns?",
                "hypothesis": "RankIC is positive historically.",
                "null_hypothesis": "RankIC is not positive.",
                "benchmark": "Equal-weight universe",
                "universe": "us_sector_etfs",
                "evaluation_period": "2018 to latest",
                "success_criteria": [{"metric": "mean_rank_ic", "active": True}],
                "outcome_metrics": ["mean_rank_ic"],
                "known_limitations": ["Static universe."],
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["missing_evidence"] == []
    assert detail["completeness"]["decision_ready"] is True


def test_ai_assessment_cannot_change_deterministic_suggestion() -> None:
    base = {
        "completeness": {"decision_ready": True},
        "missing_evidence": [],
        "benchmark_evaluation": {"verdict": "pass"},
        "evidence_snapshot": {"availability": {"validation_failed": False}},
    }
    assert _deterministic_suggestion(
        {**base, "ai_interpretation": {"hypothesis_assessment": "not_supported"}}
    ) == "Promote"
    assert _deterministic_suggestion(
        {**base, "ai_interpretation": {"hypothesis_assessment": "supported"}}
    ) == "Promote"


def test_safety_scans_all_structured_fields_and_does_not_trust_output() -> None:
    class HiddenFabricationLlm(LlmPort):
        def generate(self, *, system_prompt, user_prompt, context):
            return LlmResult(
                text=json.dumps(
                    {
                        "executive_summary": "The supplied evidence remains inconclusive.",
                        "hypothesis_assessment": "inconclusive",
                        "benchmark_assessment": "No complete comparison is available.",
                        "supporting_evidence": [],
                        "contradicting_evidence": [],
                        "missing_evidence": [],
                        "robustness_concerns": [],
                        "data_quality_concerns": [],
                        "limitations": ["Invented Sharpe 9.99."],
                        "recommended_next_steps": ["Buy SPY now."],
                    }
                ),
                model="malicious",
            )

    payload, _, warnings = generate_structured(
        HiddenFabricationLlm(),
        user_prompt="Review supplied evidence.",
        response_model=EvidenceReviewOutput,
        trusted_context="No numerical evidence is available.",
    )
    assert payload["_safety_blocked"] is True
    assert any(
        warning.startswith("prohibited_language")
        or warning == "unsupported_numeric_claim"
        for warning in warnings
    )


def test_graph_step_limit_is_terminal(
    store: InMemoryValidationResultStore,
) -> None:
    service = GovernanceAgentService(store, llm=None, llm_available=False)
    summary = service.create_run(
        {
            "research_id": "cross-sectional-factor-sector-etfs",
            "intent": "review_evidence",
            "research_type": "factor",
            "research_definition": {
                "research_question": "q",
                "hypothesis": "h",
                "universe": "us_sector_etfs",
            },
        }
    )
    service.run_store.update(summary["agent_run_id"], step_count=24)
    detail = service.resume_run(summary["agent_run_id"], "skip", {})
    assert detail["status"] == "failed"
    assert "graph_step_limit_exceeded:24" in detail["errors"]


def test_invalid_human_decision_is_rejected(
    store: InMemoryValidationResultStore,
) -> None:
    service = GovernanceAgentService(store, llm=None, llm_available=False)
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "prepare_decision",
            "research_definition": {
                "research_question": "q",
                "hypothesis": "h",
                "null_hypothesis": "n",
                "benchmark": "SPY Buy and Hold",
                "symbol": "SPY",
                "success_criteria": [{"metric": "return", "active": True}],
                "known_limitations": ["Historical only."],
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    if detail["pending_approval"].get("type") == "tool_approval":
        detail = service.resume_run(summary["agent_run_id"], "skip", {})
    assert detail["pending_approval"].get("type") == "human_decision"
    detail = service.resume_run(
        summary["agent_run_id"],
        "record_decision",
        {"decision": "Maybe", "rationale": "Not a valid enum."},
    )
    assert detail["status"] == "awaiting_approval"
    assert any("decision must be" in error for error in detail["errors"])


def test_approved_validation_uses_saved_run_configuration(
    store: InMemoryValidationResultStore,
) -> None:
    class CapturingValidationService:
        def __init__(self) -> None:
            self.payload = None

        def execute(self, payload):
            self.payload = payload
            run_id = store.save(
                {
                    "research_id": payload["research_id"],
                    "validation_status": "completed",
                    "stages": [
                        {"stage": name, "status": "completed"}
                        for name in (
                            "historical_backtest",
                            "benchmark_comparison",
                            "out_of_sample",
                            "parameter_sensitivity",
                            "transaction_cost_sensitivity",
                            "data_quality",
                        )
                    ],
                    "benchmark_evaluation": {"verdict": "pass"},
                }
            )
            return {
                "validation_run_id": run_id,
                "validation_status": "completed",
            }

    validation_service = CapturingValidationService()
    service = GovernanceAgentService(
        store,
        llm=None,
        llm_available=False,
        validation_service=validation_service,
    )
    summary = service.create_run(
        {
            "research_id": "ma-crossover-spy",
            "intent": "review_evidence",
            "research_type": "trend_following",
            "research_definition": {
                "research_question": "q",
                "hypothesis": "h",
                "symbol": "QQQ",
                "run_configuration": {
                    "symbol": "QQQ",
                    "benchmark": "QQQ",
                    "startDate": "2020-01-01",
                    "endDate": "2025-01-01",
                    "shortWindow": 15,
                    "longWindow": 80,
                    "transactionCost": 0.002,
                    "riskFreeRate": 0.01,
                },
            },
        }
    )
    detail = service.get_run(summary["agent_run_id"])
    assert detail["pending_approval"]["type"] == "tool_approval"
    service.resume_run(summary["agent_run_id"], "approve", {})
    assert validation_service.payload == {
        "research_id": "ma-crossover-spy",
        "symbol": "QQQ",
        "benchmark": "QQQ",
        "start_date": "2020-01-01",
        "end_date": "2025-01-01",
        "short_window": 15,
        "long_window": 80,
        "transaction_cost": 0.002,
        "risk_free_rate": 0.01,
    }


def test_production_service_factory_injects_deterministic_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = InMemoryValidationResultStore()
    validation = object()
    factor_validation = object()
    execution = object()
    monkeypatch.setattr(
        agent_route, "get_default_validation_result_store", lambda: store
    )
    monkeypatch.setattr(
        agent_route, "get_research_validation_service", lambda: validation
    )
    monkeypatch.setattr(
        agent_route, "get_factor_validation_service", lambda: factor_validation
    )
    monkeypatch.setattr(
        agent_route, "get_research_execution_service", lambda: execution
    )
    agent_route.set_governance_agent_service(None)
    try:
        service = agent_route.get_governance_agent_service()
        assert service.tool_ctx.validation_service is validation
        assert service.tool_ctx.factor_validation_service is factor_validation
        assert service.tool_ctx.execution_service is execution
    finally:
        agent_route.set_governance_agent_service(None)
