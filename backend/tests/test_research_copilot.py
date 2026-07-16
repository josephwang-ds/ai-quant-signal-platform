"""Offline behavioral tests for the evidence-grounded Research Copilot."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_copilot as copilot_route
from app.research_copilot.citations import build_context_index, resolve_selected_citations
from app.research_copilot.context_assembler import ResearchContextAssembler
from app.research_copilot.fake_llm import (
    EmptyCitationFakeLlm,
    FabricatingFakeLlm,
    FakeLlmAdapter,
    UnknownCitationFakeLlm,
)
from app.research_copilot.llm_port import LlmPort
from app.research_copilot.llm_response import parse_structured_llm_response
from app.research_copilot.safety import evaluate_answer
from app.research_copilot.schemas import ResearchCopilotRequest
from app.research_copilot.service import ResearchCopilotError, ResearchCopilotService, resolve_llm_adapter
from app.research_evaluation.service import ResearchEvaluationService
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter
from app.research_validation.result_store import InMemoryValidationResultStore
from app.research_validation.service import ResearchValidationService

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"


@pytest.fixture()
def store() -> InMemoryValidationResultStore:
    return InMemoryValidationResultStore()


@pytest.fixture()
def validation_service(
    store: InMemoryValidationResultStore,
) -> ResearchValidationService:
    return ResearchValidationService(FixtureMarketDataAdapter(FIXTURE), store)


@pytest.fixture()
def validation_run_id(validation_service: ResearchValidationService) -> str:
    return validation_service.execute({})["validation_run_id"]


@pytest.fixture()
def copilot_service(store: InMemoryValidationResultStore) -> ResearchCopilotService:
    return ResearchCopilotService(
        store,
        ResearchEvaluationService(store),
        FakeLlmAdapter(),
    )


def _client(
    monkeypatch: pytest.MonkeyPatch, service: ResearchCopilotService
) -> TestClient:
    app = FastAPI()
    app.include_router(copilot_route.router)
    monkeypatch.setattr(copilot_route, "get_research_copilot_service", lambda: service)
    return TestClient(app)


def test_service_has_no_market_data_or_validation_execute_dependencies() -> None:
    source = inspect.getsource(ResearchCopilotService)
    assert "ResearchValidationService" not in source
    assert "MarketDataPort" not in source
    assert "yfinance" not in source


def test_runtime_has_no_fake_llm_environment_switch() -> None:
    service_source = inspect.getsource(
        __import__("app.research_copilot.service", fromlist=["service"])
    )
    route_source = inspect.getsource(copilot_route)
    assert "COPILOT_ALLOW_FAKE_LLM" not in service_source
    assert "resolve_llm_adapter_for_runtime" not in service_source
    assert "FakeLlmAdapter" not in route_source


def test_environment_cannot_enable_fake_llm_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COPILOT_ALLOW_FAKE_LLM", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with pytest.raises(ResearchCopilotError) as exc:
        resolve_llm_adapter()
    assert exc.value.status_code == 503


def test_explicit_fake_llm_injection_still_works(
    store: InMemoryValidationResultStore, validation_run_id: str
) -> None:
    service = ResearchCopilotService(
        store,
        ResearchEvaluationService(store),
        FakeLlmAdapter(),
    )
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "Why is evaluation incomplete?",
        }
    )
    assert result["model"] == "fake-copilot-v1"
    assert result["citations"]


def test_context_assembler_assigns_stable_citation_ids(
    validation_service: ResearchValidationService,
) -> None:
    validation = validation_service.execute({})
    evaluation = ResearchEvaluationService(validation_service.store).execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation["validation_run_id"],
        }
    )
    _, items = ResearchContextAssembler().assemble(
        research_id="ma-crossover-spy",
        question="How does the system prevent look-ahead bias?",
        validation=validation,
        evaluation=evaluation,
    )
    ids = {item.citation_id for item in items}
    assert "execution:metrics" in ids
    assert "validation:out_of_sample" in ids
    assert "evaluation:status" in ids
    assert "notebook:methodology" in ids
    assert "documentation:look_ahead_policy" in ids


def test_context_assembler_excludes_large_series(
    validation_service: ResearchValidationService,
) -> None:
    validation = validation_service.execute({})
    evaluation = ResearchEvaluationService(validation_service.store).execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation["validation_run_id"],
        }
    )
    structured, items = ResearchContextAssembler().assemble(
        research_id="ma-crossover-spy",
        question="Why is evaluation incomplete?",
        validation=validation,
        evaluation=evaluation,
    )
    encoded = json.dumps(structured, allow_nan=False)
    assert '"equity_curve"' not in encoded
    assert '"prices"' not in encoded
    assert '"daily_returns"' not in encoded
    assert any(item.source_type == "validation" for item in items)
    assert any(item.source_type == "documentation" for item in items)


def test_unknown_validation_run_id_returns_404(
    copilot_service: ResearchCopilotService,
) -> None:
    with pytest.raises(ResearchCopilotError) as exc:
        copilot_service.execute(
            {
                "research_id": "ma-crossover-spy",
                "validation_run_id": "val-missing",
                "question": "Why incomplete?",
            }
        )
    assert exc.value.status_code == 404


def test_oos_question_returns_only_relevant_citations(
    copilot_service: ResearchCopilotService, validation_run_id: str
) -> None:
    result = copilot_service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "What does the OOS evidence show?",
        }
    )
    labels = {citation["label"] for citation in result["citations"]}
    assert "Out-of-sample evidence" in labels
    assert "Outstanding evidence" not in labels
    assert "Evaluation status" not in labels
    assert result["grounding_status"] in {"grounded", "partially_grounded"}


def test_governance_question_returns_evaluation_citations(
    copilot_service: ResearchCopilotService, validation_run_id: str
) -> None:
    result = copilot_service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "Why is the current evaluation incomplete?",
        }
    )
    labels = {citation["label"] for citation in result["citations"]}
    assert "Evaluation status" in labels
    assert "Outstanding evidence" in labels
    assert "Out-of-sample evidence" not in labels


def test_unknown_citation_id_is_warned_not_returned(
    store: InMemoryValidationResultStore, validation_run_id: str
) -> None:
    service = ResearchCopilotService(
        store,
        ResearchEvaluationService(store),
        UnknownCitationFakeLlm(),
    )
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "Why is evaluation incomplete?",
        }
    )
    assert any(
        warning["code"].startswith("unknown_citation_id:")
        for warning in result["warnings"]
    )
    assert all(
        citation["label"] != "Out-of-sample evidence"
        for citation in result["citations"]
    )
    assert len(result["citations"]) == 1
    assert result["citations"][0]["label"] == "Evaluation status"


def test_empty_citation_list_cannot_be_grounded(
    store: InMemoryValidationResultStore, validation_run_id: str
) -> None:
    service = ResearchCopilotService(
        store,
        ResearchEvaluationService(store),
        EmptyCitationFakeLlm(),
    )
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "Why is evaluation incomplete?",
        }
    )
    assert result["citations"] == []
    assert result["grounding_status"] == "unavailable"
    assert any(warning["code"] == "missing_citations" for warning in result["warnings"])


def test_citations_resolve_only_to_supplied_context_items(
    validation_service: ResearchValidationService,
) -> None:
    validation = validation_service.execute({})
    evaluation = ResearchEvaluationService(validation_service.store).execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation["validation_run_id"],
        }
    )
    _, items = ResearchContextAssembler().assemble(
        research_id="ma-crossover-spy",
        question="What does the OOS evidence show?",
        validation=validation,
        evaluation=evaluation,
    )
    index = build_context_index(items)
    citations, warnings = resolve_selected_citations(
        ["validation:out_of_sample", "evaluation:status", "missing:id"],
        index,
    )
    assert len(citations) == 2
    assert warnings == ["unknown_citation_id:missing:id"]
    assert citations[0].label == "Out-of-sample evidence"
    assert citations[1].label == "Evaluation status"


def test_no_fixed_generic_citation_bundle_in_service() -> None:
    source = inspect.getsource(
        __import__("app.research_copilot.service", fromlist=["service"])
    )
    assert "_build_citations" not in source


def test_structured_llm_response_parsing() -> None:
    parsed = parse_structured_llm_response(
        json.dumps(
            {
                "answer": "OOS evidence is incomplete.",
                "citation_ids": ["validation:out_of_sample"],
            }
        )
    )
    assert parsed.answer == "OOS evidence is incomplete."
    assert parsed.citation_ids == ["validation:out_of_sample"]


def test_copilot_success_with_fake_llm(
    copilot_service: ResearchCopilotService, validation_run_id: str
) -> None:
    result = copilot_service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "Why is the current evaluation incomplete?",
        }
    )
    assert result["research_id"] == "ma-crossover-spy"
    assert result["answer"]
    assert result["citations"]
    assert result["grounding_status"] in {
        "grounded",
        "partially_grounded",
        "unavailable",
    }
    assert result["model"] == "fake-copilot-v1"
    encoded = json.dumps(result, allow_nan=False)
    assert "NaN" not in encoded


def test_prohibited_recommendation_is_blocked() -> None:
    verdict = evaluate_answer(
        "You should buy SPY now.",
        citations=[{"source_type": "evaluation", "source_id": "x", "label": "l", "excerpt": "e"}],
        context_blob="evaluation_status=incomplete",
    )
    assert verdict.safe is False
    assert verdict.grounding_status == "unavailable"
    assert "investment recommendations" in (verdict.sanitized_answer or "")


def test_fabricated_metric_response_is_blocked(
    store: InMemoryValidationResultStore, validation_run_id: str
) -> None:
    service = ResearchCopilotService(
        store,
        ResearchEvaluationService(store),
        FabricatingFakeLlm(),
    )
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "What should I do?",
        }
    )
    assert "buy" not in result["answer"].lower() or "cannot" in result["answer"].lower()
    assert result["grounding_status"] == "unavailable"


def test_api_invalid_research_id(
    monkeypatch: pytest.MonkeyPatch, copilot_service: ResearchCopilotService
) -> None:
    response = _client(monkeypatch, copilot_service).post(
        "/api/v1/research/copilot/query",
        json={
            "research_id": "other",
            "validation_run_id": "val-1",
            "question": "test",
        },
    )
    assert response.status_code == 400


def test_api_empty_question(
    monkeypatch: pytest.MonkeyPatch,
    copilot_service: ResearchCopilotService,
    validation_run_id: str,
) -> None:
    with pytest.raises(Exception):
        ResearchCopilotRequest(
            research_id="ma-crossover-spy",
            validation_run_id=validation_run_id,
            question="",
        )
    response = _client(monkeypatch, copilot_service).post(
        "/api/v1/research/copilot/query",
        json={
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "   ",
        },
    )
    assert response.status_code == 422 or response.status_code == 400


def test_api_success(
    monkeypatch: pytest.MonkeyPatch,
    copilot_service: ResearchCopilotService,
    validation_run_id: str,
) -> None:
    response = _client(monkeypatch, copilot_service).post(
        "/api/v1/research/copilot/query",
        json={
            "research_id": "ma-crossover-spy",
            "validation_run_id": validation_run_id,
            "question": "What does the OOS evidence show?",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert "Out-of-sample evidence" in {item["label"] for item in body["citations"]}
    assert "buy" not in body["answer"].lower() or "cannot" in body["answer"].lower()


def test_llm_port_is_injected_not_imported_from_provider_sdk() -> None:
    assert getattr(LlmPort, "_is_protocol", False) is True


def test_api_not_configured_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("COPILOT_ALLOW_FAKE_LLM", "true")
    copilot_route.set_research_copilot_service(None)
    app = FastAPI()
    app.include_router(copilot_route.router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/research/copilot/query",
        json={
            "research_id": "ma-crossover-spy",
            "validation_run_id": "val-1",
            "question": "test",
        },
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()