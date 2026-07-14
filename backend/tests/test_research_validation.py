"""Offline behavioral tests for deterministic research validation."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_validation as validation_route
from app.research_execution.calculations import (
    run_ma_crossover_research,
    summarize_return_segment,
)
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter
from app.research_execution.market_data_port import (
    MarketDataUnavailableError,
    NormalizedMarketSeries,
    series_actual_bounds,
)
from app.research_execution.service import SAME_ASSET_BENCHMARK_MESSAGE
from app.research_validation.result_store import InMemoryValidationResultStore
from app.research_validation.schemas import ResearchValidationRequest
from app.research_validation.service import (
    ResearchValidationError,
    ResearchValidationService,
)

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"
STAGE_ORDER = [
    "historical_backtest",
    "benchmark_comparison",
    "out_of_sample",
    "parameter_sensitivity",
    "transaction_cost_sensitivity",
    "data_quality",
]


class CountingAdapter:
    def __init__(
        self,
        delegate: FixtureMarketDataAdapter,
        *,
        row_limit: int | None = None,
        warnings: list[str] | None = None,
    ) -> None:
        self.delegate = delegate
        self.row_limit = row_limit
        self.warnings = warnings
        self.calls = 0

    def get_daily_ohlcv(
        self, symbol: str, start_date: str, end_date: str | None = None
    ) -> NormalizedMarketSeries:
        self.calls += 1
        series = self.delegate.get_daily_ohlcv(symbol, start_date, end_date)
        frame = (
            series.frame.head(self.row_limit).copy()
            if self.row_limit is not None
            else series.frame.copy()
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
            warnings=(
                list(self.warnings)
                if self.warnings is not None
                else list(series.warnings)
            ),
        )


@pytest.fixture()
def fixture_adapter() -> FixtureMarketDataAdapter:
    return FixtureMarketDataAdapter(FIXTURE)


@pytest.fixture()
def service(fixture_adapter: FixtureMarketDataAdapter) -> ResearchValidationService:
    return ResearchValidationService(fixture_adapter)


def _client(
    monkeypatch: pytest.MonkeyPatch, service: ResearchValidationService
) -> TestClient:
    monkeypatch.setattr(
        validation_route, "get_research_validation_service", lambda: service
    )
    app = FastAPI()
    app.include_router(validation_route.router)
    return TestClient(app)


def test_request_defaults_are_the_canonical_contract() -> None:
    request = ResearchValidationRequest()
    assert request.model_dump() == {
        "research_id": "ma-crossover-spy",
        "symbol": "SPY",
        "benchmark": "SPY",
        "start_date": "2018-01-01",
        "end_date": None,
        "short_window": 20,
        "long_window": 60,
        "transaction_cost": 0.001,
        "risk_free_rate": 0.0,
        "in_sample_ratio": 0.7,
    }


def test_split_is_deterministic_and_uses_first_raw_oos_date(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    market = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    result = ResearchValidationService(fixture_adapter).execute({})
    split_index = math.floor(len(market.frame) * 0.7)
    expected_date = pd.Timestamp(market.frame.iloc[split_index]["date"]).date().isoformat()
    assert result["oos"]["split_observation_index"] == split_index
    assert result["oos"]["split_date"] == expected_date


def test_oos_preserves_warmup_and_slices_full_run_return_rows(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    market = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    baseline = run_ma_crossover_research(market.frame)
    response = ResearchValidationService(fixture_adapter).execute({})
    split = pd.Timestamp(response["oos"]["split_date"])
    valid_dates = pd.to_datetime(baseline.frame["date"])
    assert response["oos"]["in_sample_observation_count"] == int(
        (valid_dates < split).sum()
    )
    assert response["oos"]["out_of_sample_observation_count"] == int(
        (valid_dates >= split).sum()
    )
    assert response["oos"]["out_of_sample_metrics"]["start_date"] >= (
        response["oos"]["split_date"]
    )
    assert any(
        "valid OOS return rows" in rule for rule in response["stages"][2]["rules"]
    )


def test_segment_metrics_rebase_without_resetting_boundary_cost(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    market = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    baseline = run_ma_crossover_research(market.frame)
    changing_rows = baseline.frame.index[baseline.frame["turnover"] > 0]
    boundary_index = int(changing_rows[len(changing_rows) // 2])
    segment = baseline.frame.loc[boundary_index:].copy()
    expected_turnover = float(segment.iloc[0]["turnover"])
    expected_cost = float(segment.iloc[0]["transaction_cost"])
    rebased = summarize_return_segment(segment)
    assert float(rebased.frame.iloc[0]["turnover"]) == expected_turnover
    assert float(rebased.frame.iloc[0]["transaction_cost"]) == expected_cost
    assert expected_cost == pytest.approx(expected_turnover * 0.001)
    assert rebased.frame.iloc[-1]["cumulative_strategy"] == pytest.approx(
        (1 + segment["net_strategy_return"]).prod()
    )


def test_oos_parameters_remain_fixed(service: ResearchValidationService) -> None:
    result = service.execute(
        {
            "short_window": 10,
            "long_window": 50,
            "transaction_cost": 0.002,
            "risk_free_rate": 0.01,
        }
    )
    assert result["oos"]["fixed_parameters"] == {
        "short_window": 10,
        "long_window": 50,
        "transaction_cost": 0.002,
        "risk_free_rate": 0.01,
    }


def test_insufficient_oos_is_incomplete_not_http_error(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    adapter = CountingAdapter(fixture_adapter, row_limit=150, warnings=[])
    result = ResearchValidationService(adapter).execute({})
    assert result["oos"]["status"] == "incomplete"
    assert result["stages"][2]["status"] == "incomplete"
    assert result["validation_status"] == "incomplete"
    assert result["evidence_complete"] is False
    assert "Insufficient OOS history" in result["oos"]["warnings"][0]


def test_parameter_grid_order_canonical_and_descriptive_summary(
    service: ResearchValidationService,
) -> None:
    result = service.execute({})
    sensitivity = result["parameter_sensitivity"]
    pairs = [
        (item["short_window"], item["long_window"])
        for item in sensitivity["results"]
    ]
    assert pairs == [
        (10, 50),
        (10, 60),
        (10, 100),
        (20, 50),
        (20, 60),
        (20, 100),
        (30, 50),
        (30, 60),
        (30, 100),
    ]
    assert len(pairs) <= 9
    canonical = [item for item in sensitivity["results"] if item["is_canonical"]]
    assert [(item["short_window"], item["long_window"]) for item in canonical] == [
        (20, 60)
    ]
    assert sensitivity["valid_combination_count"] == 9
    assert 0 <= sensitivity["profitable_combination_count"] <= 9
    assert 0 <= sensitivity["positive_sharpe_count"] <= 9
    assert sensitivity["canonical_percentile_by_sharpe"] is not None
    assert "summary" not in sensitivity
    assert all("metrics" not in item for item in sensitivity["results"])
    assert "best" not in sensitivity
    assert "recommendation" not in sensitivity


def test_all_stages_reuse_one_market_data_call(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    adapter = CountingAdapter(fixture_adapter)
    ResearchValidationService(adapter).execute({})
    assert adapter.calls == 1


def test_cost_degradation_uses_zero_cost_baseline(
    service: ResearchValidationService,
) -> None:
    costs = service.execute({})["transaction_cost_sensitivity"]
    assert [item["transaction_cost"] for item in costs["results"]] == [
        0.0,
        0.001,
        0.002,
        0.005,
    ]
    assert costs["results"][0]["return_degradation_from_zero"] == pytest.approx(0)
    assert costs["results"][0]["sharpe_degradation_from_zero"] == pytest.approx(0)
    assert all(
        item["return_degradation_from_zero"] >= 0 for item in costs["results"]
    )
    assert costs["canonical_cost"] == 0.001
    assert costs["canonical_cost_result"]["transaction_cost"] == 0.001
    assert costs["mathematically_valid"] if "mathematically_valid" in costs else True


def test_partial_cost_grid_is_incomplete_without_aborting_response(
    monkeypatch: pytest.MonkeyPatch,
    service: ResearchValidationService,
) -> None:
    original = run_ma_crossover_research

    def fail_one_cost(*args, **kwargs):
        if kwargs.get("transaction_cost") == 0.002:
            raise ValueError("simulated cost-level failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        "app.research_validation.service.run_ma_crossover_research",
        fail_one_cost,
    )
    result = service.execute({})
    costs = result["transaction_cost_sensitivity"]
    failed_row = next(
        item for item in costs["results"] if item["transaction_cost"] == 0.002
    )
    assert costs["status"] == "incomplete"
    assert result["stages"][4]["status"] == "incomplete"
    assert result["validation_status"] == "incomplete"
    assert failed_row["total_return"] is None
    assert failed_row["return_degradation_from_zero"] is None
    assert failed_row["mathematically_valid"] is False
    assert "simulated cost-level failure" in failed_row["warnings"][0]
    json.dumps(result, allow_nan=False)


def test_cost_grid_failed_when_no_level_executes(
    monkeypatch: pytest.MonkeyPatch,
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    market = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    baseline = run_ma_crossover_research(market.frame)
    service = ResearchValidationService(fixture_adapter)
    parameters = service._validate_request({})

    def fail_all_costs(*args, **kwargs):
        raise ValueError("simulated all-cost failure")

    monkeypatch.setattr(
        "app.research_validation.service.run_ma_crossover_research",
        fail_all_costs,
    )
    payload, stage = service._build_cost_sensitivity(
        market.frame,
        baseline,
        parameters,
        "2026-07-14T00:00:00Z",
        {
            "provider": "fixture",
            "symbol": "SPY",
            "source": "Local Fixture",
        },
    )
    assert payload["status"] == "failed"
    assert stage["status"] == "failed"
    assert len(payload["results"]) == 4
    assert payload["canonical_cost_result"]["total_return"] is None
    assert all(item["total_return"] is None for item in payload["results"])
    assert all(
        item["return_degradation_from_zero"] is None
        for item in payload["results"]
    )
    assert all(not item["mathematically_valid"] for item in payload["results"])
    json.dumps(payload, allow_nan=False)


def test_oos_calculation_failure_becomes_failed_stage(
    monkeypatch: pytest.MonkeyPatch,
    service: ResearchValidationService,
) -> None:
    def fail_segment(*args, **kwargs):
        raise ValueError("simulated segment calculation failure")

    monkeypatch.setattr(
        "app.research_validation.service.summarize_return_segment",
        fail_segment,
    )
    result = service.execute({})
    assert result["oos"]["status"] == "failed"
    assert result["oos"]["in_sample_metrics"] is None
    assert result["oos"]["out_of_sample_metrics"] is None
    assert result["stages"][2]["status"] == "failed"
    assert result["validation_status"] == "failed"
    assert result["evidence_complete"] is False
    assert any(
        "simulated segment calculation failure" in blocker
        for blocker in result["stages"][2]["blockers"]
    )
    json.dumps(result, allow_nan=False)


def test_data_quality_keeps_provider_warning_nonfatal(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    adapter = CountingAdapter(
        fixture_adapter,
        warnings=["Provider is research-grade, not exchange-grade."],
    )
    quality = ResearchValidationService(adapter).execute({})["data_quality"]
    assert quality["status"] == "incomplete"
    assert quality["fatal_issues"] == []
    assert "Provider is research-grade, not exchange-grade." in quality["warnings"]
    fatal_checks = [
        check for check in quality["checks"] if check["severity"] == "fatal"
    ]
    assert fatal_checks
    assert all(check["status"] == "passed" for check in fatal_checks)
    assert not any(check["status"] == "failed" for check in quality["checks"])


def test_data_quality_completes_without_nonfatal_limitations(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    adapter = CountingAdapter(fixture_adapter, warnings=[])
    quality = ResearchValidationService(adapter).execute(
        {"end_date": "2021-01-01"}
    )["data_quality"]
    assert quality["fatal_issues"] == []
    assert quality["warnings"] == []
    assert quality["status"] == "completed"


def test_stage_order_common_fields_statuses_and_provenance(
    service: ResearchValidationService,
) -> None:
    result = service.execute({})
    assert [stage["stage"] for stage in result["stages"]] == STAGE_ORDER
    common = {
        "stage",
        "label",
        "status",
        "summary",
        "evidence",
        "rules",
        "warnings",
        "blockers",
        "generated_at",
        "provenance",
    }
    for stage in result["stages"]:
        assert set(stage) == common
        assert stage["status"] in {"completed", "incomplete", "failed"}
        assert stage["provenance"] == result["provenance"]
    assert result["provenance"]["provider"] == "fixture"


def test_response_is_bounded_and_strict_json_safe(
    service: ResearchValidationService,
) -> None:
    result = service.execute({})
    encoded = json.dumps(result, allow_nan=False)
    assert "NaN" not in encoded
    assert "Infinity" not in encoded
    assert "series" not in result
    assert "prices" not in result


def test_api_success_uses_isolated_router(
    monkeypatch: pytest.MonkeyPatch, service: ResearchValidationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/validation", json={}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["research_id"] == "ma-crossover-spy"
    assert [stage["stage"] for stage in body["stages"]] == STAGE_ORDER
    assert isinstance(body["validation_run_id"], str) and body["validation_run_id"]


def test_execute_saves_the_complete_result_and_returns_its_run_id(
    service: ResearchValidationService,
) -> None:
    """Validation must save its own output so Evaluation can load it later
    without re-running Validation."""
    result = service.execute({})
    validation_run_id = result["validation_run_id"]
    assert isinstance(validation_run_id, str) and validation_run_id
    stored = service.store.get(validation_run_id)
    assert stored == result


def test_each_validation_run_is_saved_under_a_distinct_run_id(
    service: ResearchValidationService,
) -> None:
    first = service.execute({})
    second = service.execute({})
    assert first["validation_run_id"] != second["validation_run_id"]
    assert service.store.get(first["validation_run_id"])["generated_at"] == (
        first["generated_at"]
    )
    assert service.store.get(second["validation_run_id"])["generated_at"] == (
        second["generated_at"]
    )


def test_unknown_validation_run_id_is_not_found(
    service: ResearchValidationService,
) -> None:
    assert service.store.get("val-does-not-exist") is None


def test_service_without_explicit_store_still_saves_results(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    """A store is not required at call sites that only need the calculation
    (e.g. focused unit tests): each service instance gets its own private
    in-memory store by default."""
    service = ResearchValidationService(fixture_adapter)
    assert isinstance(service.store, InMemoryValidationResultStore)
    result = service.execute({})
    assert service.store.get(result["validation_run_id"]) == result


@pytest.mark.parametrize("ratio", [0.49, 0.91])
def test_ratio_domain_error_maps_400(
    monkeypatch: pytest.MonkeyPatch,
    service: ResearchValidationService,
    ratio: float,
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/validation", json={"in_sample_ratio": ratio}
    )
    assert response.status_code == 400
    assert "0.5" in response.json()["detail"]


def test_benchmark_mismatch_uses_pr008b_exact_message(
    service: ResearchValidationService,
) -> None:
    with pytest.raises(ResearchValidationError) as exc:
        service.execute({"benchmark": "QQQ"})
    assert exc.value.status_code == 400
    assert exc.value.message == SAME_ASSET_BENCHMARK_MESSAGE


def test_api_benchmark_mismatch_is_400(
    monkeypatch: pytest.MonkeyPatch, service: ResearchValidationService
) -> None:
    response = _client(monkeypatch, service).post(
        "/api/v1/research/validation",
        json={"symbol": "SPY", "benchmark": "QQQ"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == SAME_ASSET_BENCHMARK_MESSAGE


def test_provider_unavailable_maps_502(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnavailableAdapter:
        def get_daily_ohlcv(
            self, symbol: str, start_date: str, end_date: str | None = None
        ) -> NormalizedMarketSeries:
            raise MarketDataUnavailableError("provider unavailable")

    service = ResearchValidationService(UnavailableAdapter())
    response = _client(monkeypatch, service).post(
        "/api/v1/research/validation", json={}
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "provider unavailable"


def test_insufficient_full_sample_is_400(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    service = ResearchValidationService(
        CountingAdapter(fixture_adapter, row_limit=61, warnings=[])
    )
    with pytest.raises(ResearchValidationError) as exc:
        service.execute({})
    assert exc.value.status_code == 400
    assert "Insufficient history" in exc.value.message


def test_partial_parameter_grid_is_incomplete(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    result = ResearchValidationService(
        CountingAdapter(fixture_adapter, row_limit=80, warnings=[])
    ).execute({})
    sensitivity = result["parameter_sensitivity"]
    assert sensitivity["status"] == "incomplete"
    assert 0 < sensitivity["valid_combination_count"] < 9
    assert any(item["status"] == "incomplete" for item in sensitivity["results"])


def test_canonical_cost_result_exists_outside_fixed_grid(
    service: ResearchValidationService,
) -> None:
    costs = service.execute({"transaction_cost": 0.003})[
        "transaction_cost_sensitivity"
    ]
    assert len(costs["results"]) == 4
    assert costs["canonical_cost"] == 0.003
    assert costs["canonical_cost_result"]["transaction_cost"] == 0.003


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"research_id": "rs-ma-crossover-001"}, "Unsupported research_id"),
        ({"short_window": 60, "long_window": 20}, "short_window must be"),
        ({"transaction_cost": -0.1}, "transaction_cost must be"),
        ({"start_date": "2024-02-30"}, "YYYY-MM-DD"),
        (
            {"start_date": "2024-02-01", "end_date": "2024-01-01"},
            "start_date must be",
        ),
    ],
)
def test_invalid_domain_parameters_are_400(
    service: ResearchValidationService,
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ResearchValidationError) as exc:
        service.execute(payload)
    assert exc.value.status_code == 400
    assert message in exc.value.message
