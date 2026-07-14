"""Offline behavioral tests for the research evaluation governance layer.

PR-010 evaluation never recalculates strategy performance. These tests assert
that behavior explicitly: the validation service is invoked exactly once per
evaluation request, and no MA-crossover / OOS / sensitivity / cost function is
imported or called by app.research_evaluation.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_evaluation as evaluation_route
from app.research_evaluation import service as evaluation_service_module
from app.research_evaluation.schemas import ResearchEvaluationRequest
from app.research_evaluation.service import (
    IMPLEMENTED_STAGE_LABELS,
    LIMITATIONS,
    OUTSTANDING_EVIDENCE,
    UNAVAILABLE_STAGES,
    ResearchEvaluationError,
    ResearchEvaluationService,
)
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter
from app.research_execution.market_data_port import (
    MarketDataUnavailableError,
    NormalizedMarketSeries,
)
from app.research_validation.service import (
    ResearchValidationService,
    STAGE_ORDER,
)

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"


class CountingValidationService:
    """Wraps the real validation service to assert single-call reuse."""

    def __init__(self, delegate: ResearchValidationService) -> None:
        self.delegate = delegate
        self.calls = 0

    def execute(self, request: dict) -> dict:
        self.calls += 1
        return self.delegate.execute(request)


@pytest.fixture()
def fixture_adapter() -> FixtureMarketDataAdapter:
    return FixtureMarketDataAdapter(FIXTURE)


@pytest.fixture()
def validation_service(
    fixture_adapter: FixtureMarketDataAdapter,
) -> ResearchValidationService:
    return ResearchValidationService(fixture_adapter)


@pytest.fixture()
def service(
    validation_service: ResearchValidationService,
) -> ResearchEvaluationService:
    return ResearchEvaluationService(validation_service)


def _client(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> TestClient:
    monkeypatch.setattr(
        evaluation_route, "get_research_evaluation_service", lambda: service
    )
    app = FastAPI()
    app.include_router(evaluation_route.router)
    return TestClient(app)


def test_request_defaults_are_the_canonical_contract() -> None:
    request = ResearchEvaluationRequest()
    assert request.model_dump() == {"research_id": "ma-crossover-spy"}


def test_no_calculation_functions_are_imported_by_evaluation() -> None:
    """Evaluation must aggregate; it must never import calculation code."""
    source = inspect.getsource(evaluation_service_module)
    forbidden = [
        "run_ma_crossover_research",
        "summarize_return_segment",
        "MarketDataPort",
        "pandas",
        "import pd",
    ]
    for symbol in forbidden:
        assert symbol not in source, f"Evaluation must not reference {symbol!r}"


def test_validation_service_is_called_exactly_once(
    validation_service: ResearchValidationService,
) -> None:
    counting = CountingValidationService(validation_service)
    ResearchEvaluationService(counting).execute({})
    assert counting.calls == 1


def test_evidence_summary_is_verbatim_passthrough_of_validation_stages(
    service: ResearchEvaluationService,
    validation_service: ResearchValidationService,
) -> None:
    validation = validation_service.execute({})
    result = service.execute({})
    assert [item["stage"] for item in result["evidence_summary"]] == list(STAGE_ORDER)
    for item, stage in zip(result["evidence_summary"], validation["stages"]):
        assert item["stage"] == stage["stage"]
        assert item["label"] == stage["label"]
        assert item["status"] == stage["status"]
        assert item["summary"] == stage["summary"]
        # Evidence summary must not carry numeric evidence — only status text.
        assert set(item.keys()) == {"stage", "label", "status", "summary"}


def test_coverage_is_implementation_only_not_confidence(
    service: ResearchEvaluationService,
) -> None:
    result = service.execute({})
    coverage = result["evidence_coverage"]
    assert coverage["implemented_stage_count"] == 6
    assert coverage["completed_stage_count"] == len(result["completed_stages"])
    expected_percentage = round(
        coverage["completed_stage_count"] / coverage["implemented_stage_count"] * 100,
        2,
    )
    assert coverage["coverage_percentage"] == expected_percentage
    # Coverage is bounded and is not a quality/confidence score in disguise.
    assert 0 <= coverage["coverage_percentage"] <= 100


def test_completed_and_status_are_completed_when_all_stages_completed(
    service: ResearchEvaluationService,
) -> None:
    result = service.execute({})
    assert result["evaluation_status"] in {"completed", "incomplete", "blocked"}
    assert len(result["completed_stages"]) + len(result["incomplete_stages"]) == 6
    if result["evaluation_status"] == "completed":
        assert result["incomplete_stages"] == []
        assert result["evidence_coverage"]["coverage_percentage"] == 100.0


def test_evaluation_status_uses_only_allowed_vocabulary(
    service: ResearchEvaluationService,
) -> None:
    result = service.execute({})
    assert result["evaluation_status"] in {"completed", "incomplete", "blocked"}
    banned_terms = [
        "passed",
        "failed strategy",
        "robust",
        "good",
        "excellent",
        "approved",
        "recommend",
    ]
    encoded = json.dumps(result).lower()
    for term in banned_terms:
        assert term not in encoded, f"Evaluation must never use {term!r}"
    # "buy" may only appear inside the reused "buy-and-hold" benchmark phrase,
    # never as a standalone buy/sell investment directive.
    import re

    for match in re.finditer(r"\bbuy\b|\bsell\b", encoded):
        window = encoded[max(0, match.start() - 5) : match.end() + 10]
        assert "buy-and-hold" in window, f"Unexpected trading directive near: {window!r}"


def test_incomplete_stage_produces_incomplete_status_and_deterministic_blocker(
    monkeypatch: pytest.MonkeyPatch,
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    """A truncated fixture makes OOS incomplete; blockers must reuse that text."""

    class TruncatedAdapter:
        def get_daily_ohlcv(self, symbol, start_date, end_date=None):
            series = fixture_adapter.get_daily_ohlcv(symbol, start_date, end_date)
            frame = series.frame.head(150).copy()
            from dataclasses import replace

            from app.research_execution.market_data_port import (
                series_actual_bounds,
            )

            actual_start, actual_end = series_actual_bounds(frame)
            return NormalizedMarketSeries(
                symbol=series.symbol,
                frame=frame,
                provenance=replace(
                    series.provenance,
                    actual_start=actual_start,
                    actual_end=actual_end,
                ),
                warnings=list(series.warnings),
            )

    validation_service = ResearchValidationService(TruncatedAdapter())
    result = ResearchEvaluationService(validation_service).execute({})
    assert result["evaluation_status"] == "incomplete"
    assert any("Insufficient OOS history" in blocker for blocker in result["blockers"])
    assert "Out-of-sample validation" in result["incomplete_stages"]


def test_failed_stage_produces_blocked_status(
    monkeypatch: pytest.MonkeyPatch,
    validation_service: ResearchValidationService,
) -> None:
    def fail_segment(*args, **kwargs):
        raise ValueError("simulated segment calculation failure")

    monkeypatch.setattr(
        "app.research_validation.service.summarize_return_segment",
        fail_segment,
    )
    result = ResearchEvaluationService(validation_service).execute({})
    assert result["evaluation_status"] == "blocked"
    assert any(
        "simulated segment calculation failure" in blocker
        for blocker in result["blockers"]
    )


def test_provider_unavailable_becomes_blocked_without_http_error() -> None:
    class UnavailableAdapter:
        def get_daily_ohlcv(self, symbol, start_date, end_date=None):
            raise MarketDataUnavailableError("provider unavailable")

    validation_service = ResearchValidationService(UnavailableAdapter())
    result = ResearchEvaluationService(validation_service).execute({})
    assert result["evaluation_status"] == "blocked"
    assert result["blockers"] == ["Provider unavailable: provider unavailable"]
    assert result["completed_stages"] == []
    assert result["incomplete_stages"] == list(IMPLEMENTED_STAGE_LABELS.values())
    assert result["evidence_coverage"]["coverage_percentage"] == 0.0
    json.dumps(result, allow_nan=False)


def test_limitations_are_fixed_and_informational(
    service: ResearchEvaluationService,
) -> None:
    result = service.execute({})
    assert result["limitations"] == list(LIMITATIONS)
    assert "Stress testing is not implemented." in result["limitations"]
    assert "Paper trading is unavailable." in result["limitations"]


def test_outstanding_evidence_lists_unavailable_capabilities_not_advice(
    service: ResearchEvaluationService,
) -> None:
    result = service.execute({})
    assert result["outstanding_evidence"] == list(OUTSTANDING_EVIDENCE)
    assert result["unavailable_stages"] == list(UNAVAILABLE_STAGES)
    forbidden_phrases = ["improve sharpe", "increase return", "buy", "sell"]
    encoded = " ".join(result["outstanding_evidence"]).lower()
    for phrase in forbidden_phrases:
        assert phrase not in encoded


def test_provenance_references_validation_without_duplicating_payload(
    validation_service: ResearchValidationService,
) -> None:
    captured: dict = {}
    original_execute = validation_service.execute

    def capturing_execute(request: dict) -> dict:
        validation = original_execute(request)
        captured["validation"] = validation
        return validation

    validation_service.execute = capturing_execute  # type: ignore[method-assign]
    result = ResearchEvaluationService(validation_service).execute({})
    validation = captured["validation"]
    assert result["provenance"]["validation_generated_at"] == validation["generated_at"]
    assert result["provenance"]["market_data_provenance"] == validation["provenance"]
    # No duplication of full validation payload (oos/sensitivity/etc.).
    assert "oos" not in result
    assert "parameter_sensitivity" not in result
    assert "transaction_cost_sensitivity" not in result
    assert "data_quality" not in result
    assert "stages" not in result


def test_response_is_strict_json_safe(service: ResearchEvaluationService) -> None:
    result = service.execute({})
    encoded = json.dumps(result, allow_nan=False)
    assert "NaN" not in encoded
    assert "Infinity" not in encoded


def test_api_success_uses_isolated_router(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation", json={}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["research_id"] == "ma-crossover-spy"
    assert body["evaluation_status"] in {"completed", "incomplete", "blocked"}
    assert len(body["evidence_summary"]) == 6


def test_unsupported_research_id_is_400(
    service: ResearchEvaluationService,
) -> None:
    with pytest.raises(ResearchEvaluationError) as exc:
        service.execute({"research_id": "rs-ma-crossover-001"})
    assert exc.value.status_code == 400
    assert "Unsupported research_id" in exc.value.message


def test_api_unsupported_research_id_is_400(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation", json={"research_id": "unknown"}
    )
    assert response.status_code == 400
    assert "Unsupported research_id" in response.json()["detail"]
