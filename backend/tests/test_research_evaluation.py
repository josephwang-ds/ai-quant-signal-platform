"""Offline behavioral tests for the research evaluation governance layer.

PR-010 evaluation never recalculates strategy performance, and — after the
ValidationResultStore refactor — never re-runs Validation either. These
tests assert that boundary explicitly:

- ResearchEvaluationService has no ResearchValidationService dependency.
- Evaluation reads exactly one stored ValidationResult per request.
- Evaluation never calls MarketDataPort or ResearchValidationService.execute,
  proven with a spy/failing-dependency monkeypatch, not just by inspection.
- No MA-crossover / OOS / sensitivity / cost function is imported by
  app.research_evaluation.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError

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
from app.research_validation.result_store import (
    InMemoryValidationResultStore,
    ValidationResultStore,
)
from app.research_validation.service import ResearchValidationService, STAGE_ORDER

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"


class CountingStore:
    """Wraps a real store to assert Evaluation performs exactly one read."""

    def __init__(self, delegate: ValidationResultStore) -> None:
        self.delegate = delegate
        self.get_calls = 0
        self.save_calls = 0

    def save(self, result: dict) -> str:
        self.save_calls += 1
        return self.delegate.save(result)

    def get(self, validation_run_id: str) -> dict | None:
        self.get_calls += 1
        return self.delegate.get(validation_run_id)


@pytest.fixture()
def fixture_adapter() -> FixtureMarketDataAdapter:
    return FixtureMarketDataAdapter(FIXTURE)


@pytest.fixture()
def store() -> InMemoryValidationResultStore:
    return InMemoryValidationResultStore()


@pytest.fixture()
def validation_service(
    fixture_adapter: FixtureMarketDataAdapter,
    store: InMemoryValidationResultStore,
) -> ResearchValidationService:
    return ResearchValidationService(fixture_adapter, store)


@pytest.fixture()
def validation(validation_service: ResearchValidationService) -> dict:
    """One real Validation run, saved to the shared store exactly once."""
    return validation_service.execute({})


@pytest.fixture()
def validation_run_id(validation: dict) -> str:
    return validation["validation_run_id"]


@pytest.fixture()
def service(store: InMemoryValidationResultStore) -> ResearchEvaluationService:
    return ResearchEvaluationService(store)


def _client(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> TestClient:
    monkeypatch.setattr(
        evaluation_route, "get_research_evaluation_service", lambda: service
    )
    app = FastAPI()
    app.include_router(evaluation_route.router)
    return TestClient(app)


def test_validation_run_id_is_required_by_the_request_contract() -> None:
    with pytest.raises(PydanticValidationError):
        ResearchEvaluationRequest()
    request = ResearchEvaluationRequest(validation_run_id="val-abc123")
    assert request.model_dump() == {
        "research_id": "ma-crossover-spy",
        "validation_run_id": "val-abc123",
    }


def test_evaluation_service_has_no_validation_service_dependency() -> None:
    """The constructor signature is the architectural boundary itself:
    ResearchEvaluationService cannot depend on ResearchValidationService or
    MarketDataPort because neither name appears as a constructor parameter."""
    params = inspect.signature(ResearchEvaluationService.__init__).parameters
    assert list(params) == ["self", "store"]

    instance = ResearchEvaluationService(InMemoryValidationResultStore())
    assert not hasattr(instance, "validation_service")
    assert not hasattr(instance, "market_data")


def test_no_calculation_or_validation_execution_imports_in_evaluation_module() -> None:
    """Evaluation must aggregate; it must never import calculation or
    validation-execution code, nor any concrete market-data adapter."""
    source = inspect.getsource(evaluation_service_module)
    forbidden_imports = [
        "import pandas",
        "import pd",
        "from app.research_execution.calculations import",
        "from app.research_execution.yahoo_adapter import",
        "from app.research_execution.fixture_adapter import",
        "from app.research_validation.service import ResearchValidationService",
        "MarketDataPort",
    ]
    for snippet in forbidden_imports:
        assert snippet not in source, f"Evaluation must not reference {snippet!r}"


def test_evaluation_never_touches_market_data_or_validation_service(
    monkeypatch: pytest.MonkeyPatch,
    store: InMemoryValidationResultStore,
    validation_run_id: str,
) -> None:
    """Spy/failing-dependency test: any attempt by Evaluation to call
    MarketDataPort or ResearchValidationService must fail this test.

    validation_run_id is resolved by fixtures (i.e. Validation already ran)
    before these monkeypatches are installed, so this only proves that the
    Evaluation call itself never reaches either dependency.
    """

    def fail_market_data(*args, **kwargs):
        raise AssertionError("Evaluation must never call a MarketDataPort adapter.")

    def fail_validation_execute(*args, **kwargs):
        raise AssertionError(
            "Evaluation must never call ResearchValidationService.execute."
        )

    monkeypatch.setattr(FixtureMarketDataAdapter, "get_daily_ohlcv", fail_market_data)
    monkeypatch.setattr(
        "app.research_validation.service.ResearchValidationService.execute",
        fail_validation_execute,
    )

    result = ResearchEvaluationService(store).execute(
        {"validation_run_id": validation_run_id}
    )
    assert result["evaluation_status"] in {"completed", "incomplete", "blocked"}


def test_evaluation_reads_exactly_one_stored_validation_result(
    store: InMemoryValidationResultStore,
    validation_run_id: str,
) -> None:
    counting_store = CountingStore(store)
    ResearchEvaluationService(counting_store).execute(
        {"validation_run_id": validation_run_id}
    )
    assert counting_store.get_calls == 1
    assert counting_store.save_calls == 0


def test_no_duplicate_validation_execution_occurs(
    fixture_adapter: FixtureMarketDataAdapter,
    store: InMemoryValidationResultStore,
) -> None:
    class CountingValidationService(ResearchValidationService):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.execute_calls = 0

        def execute(self, request: dict) -> dict:
            self.execute_calls += 1
            return super().execute(request)

    counting_validation = CountingValidationService(fixture_adapter, store)
    run_id = counting_validation.execute({})["validation_run_id"]
    assert counting_validation.execute_calls == 1

    evaluation = ResearchEvaluationService(store)
    evaluation.execute({"validation_run_id": run_id})
    evaluation.execute({"validation_run_id": run_id})
    assert counting_validation.execute_calls == 1


def test_unknown_validation_run_id_is_handled_clearly(
    service: ResearchEvaluationService,
) -> None:
    with pytest.raises(ResearchEvaluationError) as exc:
        service.execute({"validation_run_id": "val-does-not-exist"})
    assert exc.value.status_code == 404
    assert "Unknown validation_run_id" in exc.value.message


def test_api_unknown_validation_run_id_is_404(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation",
        json={"validation_run_id": "val-does-not-exist"},
    )
    assert response.status_code == 404


def test_missing_validation_run_id_is_400(
    service: ResearchEvaluationService,
) -> None:
    with pytest.raises(ResearchEvaluationError) as exc:
        service.execute({})
    assert exc.value.status_code == 400
    assert "validation_run_id is required" in exc.value.message


def test_api_missing_validation_run_id_is_422(
    monkeypatch: pytest.MonkeyPatch, service: ResearchEvaluationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation", json={}
    )
    assert response.status_code == 422


def test_research_id_mismatch_is_rejected(
    store: InMemoryValidationResultStore,
) -> None:
    """A validation_run_id from another research_id must never be accepted,
    even though only one research_id is currently supported for requests."""
    other_run_id = store.save(
        {
            "research_id": "some-other-research",
            "stages": [],
            "generated_at": "2026-07-14T00:00:00Z",
            "provenance": {"provider": "fixture"},
        }
    )
    with pytest.raises(ResearchEvaluationError) as exc:
        ResearchEvaluationService(store).execute(
            {"research_id": "ma-crossover-spy", "validation_run_id": other_run_id}
        )
    assert exc.value.status_code == 400
    assert "belongs to research" in exc.value.message


def test_api_research_id_mismatch_is_400(
    monkeypatch: pytest.MonkeyPatch,
    store: InMemoryValidationResultStore,
    service: ResearchEvaluationService,
) -> None:
    other_run_id = store.save(
        {
            "research_id": "some-other-research",
            "stages": [],
            "generated_at": "2026-07-14T00:00:00Z",
            "provenance": {"provider": "fixture"},
        }
    )
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation",
        json={"research_id": "ma-crossover-spy", "validation_run_id": other_run_id},
    )
    assert response.status_code == 400
    assert "belongs to research" in response.json()["detail"]


def test_evidence_summary_is_verbatim_passthrough_of_validation_stages(
    service: ResearchEvaluationService,
    validation: dict,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
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
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
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
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
    assert result["evaluation_status"] in {"completed", "incomplete", "blocked"}
    assert len(result["completed_stages"]) + len(result["incomplete_stages"]) == 6
    if result["evaluation_status"] == "completed":
        assert result["incomplete_stages"] == []
        assert result["evidence_coverage"]["coverage_percentage"] == 100.0


def test_evaluation_status_uses_only_allowed_vocabulary(
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
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
    fixture_adapter: FixtureMarketDataAdapter,
    store: InMemoryValidationResultStore,
) -> None:
    """A truncated fixture makes OOS incomplete; blockers must reuse that text."""

    class TruncatedAdapter:
        def get_daily_ohlcv(self, symbol, start_date, end_date=None):
            series = fixture_adapter.get_daily_ohlcv(symbol, start_date, end_date)
            frame = series.frame.head(150).copy()
            from dataclasses import replace

            from app.research_execution.market_data_port import (
                NormalizedMarketSeries,
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

    truncated_validation = ResearchValidationService(TruncatedAdapter(), store)
    run_id = truncated_validation.execute({})["validation_run_id"]

    result = ResearchEvaluationService(store).execute({"validation_run_id": run_id})
    assert result["evaluation_status"] == "incomplete"
    assert any("Insufficient OOS history" in blocker for blocker in result["blockers"])
    assert "Out-of-sample validation" in result["incomplete_stages"]


def test_failed_stage_stored_as_validation_evidence_is_summarized_as_blocked(
    monkeypatch: pytest.MonkeyPatch,
    fixture_adapter: FixtureMarketDataAdapter,
    store: InMemoryValidationResultStore,
) -> None:
    """Any degraded evidence (including provider-adjacent calculation
    failures) that already made it into a stored ValidationResult must be
    summarized correctly by Evaluation, without Evaluation re-deriving it."""

    def fail_segment(*args, **kwargs):
        raise ValueError("simulated segment calculation failure")

    monkeypatch.setattr(
        "app.research_validation.service.summarize_return_segment",
        fail_segment,
    )
    failing_validation = ResearchValidationService(fixture_adapter, store)
    run_id = failing_validation.execute({})["validation_run_id"]

    result = ResearchEvaluationService(store).execute({"validation_run_id": run_id})
    assert result["evaluation_status"] == "blocked"
    assert any(
        "simulated segment calculation failure" in blocker
        for blocker in result["blockers"]
    )


def test_limitations_are_fixed_and_informational(
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
    assert result["limitations"] == list(LIMITATIONS)
    assert "Stress testing is not implemented." in result["limitations"]
    assert "Paper trading is unavailable." in result["limitations"]


def test_outstanding_evidence_lists_unavailable_capabilities_not_advice(
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
    assert result["outstanding_evidence"] == list(OUTSTANDING_EVIDENCE)
    assert result["unavailable_stages"] == list(UNAVAILABLE_STAGES)
    forbidden_phrases = ["improve sharpe", "increase return", "buy", "sell"]
    encoded = " ".join(result["outstanding_evidence"]).lower()
    for phrase in forbidden_phrases:
        assert phrase not in encoded


def test_provenance_references_validation_without_duplicating_payload(
    service: ResearchEvaluationService,
    validation: dict,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
    assert result["provenance"]["validation_run_id"] == validation_run_id
    assert result["provenance"]["validation_generated_at"] == validation["generated_at"]
    assert result["provenance"]["market_data_provenance"] == validation["provenance"]
    # No duplication of full validation payload (oos/sensitivity/etc.).
    assert "oos" not in result
    assert "parameter_sensitivity" not in result
    assert "transaction_cost_sensitivity" not in result
    assert "data_quality" not in result
    assert "stages" not in result


def test_response_is_strict_json_safe(
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    result = service.execute({"validation_run_id": validation_run_id})
    encoded = json.dumps(result, allow_nan=False)
    assert "NaN" not in encoded
    assert "Infinity" not in encoded


def test_api_success_uses_isolated_router(
    monkeypatch: pytest.MonkeyPatch,
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation",
        json={"validation_run_id": validation_run_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["research_id"] == "ma-crossover-spy"
    assert body["evaluation_status"] in {"completed", "incomplete", "blocked"}
    assert len(body["evidence_summary"]) == 6
    assert body["provenance"]["validation_run_id"] == validation_run_id


def test_unsupported_research_id_is_400(
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    with pytest.raises(ResearchEvaluationError) as exc:
        service.execute(
            {
                "research_id": "rs-ma-crossover-001",
                "validation_run_id": validation_run_id,
            }
        )
    assert exc.value.status_code == 400
    assert "Unsupported research_id" in exc.value.message


def test_api_unsupported_research_id_is_400(
    monkeypatch: pytest.MonkeyPatch,
    service: ResearchEvaluationService,
    validation_run_id: str,
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/evaluation",
        json={"research_id": "unknown", "validation_run_id": validation_run_id},
    )
    assert response.status_code == 400
    assert "Unsupported research_id" in response.json()["detail"]


def test_evaluation_never_imports_implemented_stage_labels_count_from_stages() -> None:
    """Guard against silently drifting the coverage denominator: implemented
    stage count must stay pinned to the six PR-009 stages."""
    assert len(IMPLEMENTED_STAGE_LABELS) == 6
