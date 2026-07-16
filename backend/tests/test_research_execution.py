"""Offline unit + API tests for research execution (no live network)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_execution as research_execution_route
from app.research_execution.calculations import (
    metrics_to_dict,
    run_ma_crossover_research,
)
from app.research_execution.fixture_adapter import FixtureMarketDataAdapter
from app.research_execution.market_data_port import (
    MarketDataValidationError,
    validate_normalized_ohlcv,
)
from app.research_execution.service import (
    ResearchExecutionError,
    ResearchExecutionService,
)

FIXTURE = Path(__file__).parent / "fixtures" / "spy_daily_sample.csv"


@pytest.fixture()
def fixture_adapter() -> FixtureMarketDataAdapter:
    return FixtureMarketDataAdapter(FIXTURE)


@pytest.fixture()
def service(fixture_adapter: FixtureMarketDataAdapter) -> ResearchExecutionService:
    return ResearchExecutionService(fixture_adapter)


@pytest.fixture()
def api_client(
    monkeypatch: pytest.MonkeyPatch, fixture_adapter: FixtureMarketDataAdapter
) -> TestClient:
    svc = ResearchExecutionService(fixture_adapter)
    monkeypatch.setattr(
        research_execution_route, "get_research_execution_service", lambda: svc
    )
    app = FastAPI()
    app.include_router(research_execution_route.router)
    return TestClient(app)


def test_validate_normalized_ohlcv_rejects_empty() -> None:
    with pytest.raises(MarketDataValidationError):
        validate_normalized_ohlcv(pd.DataFrame(), symbol="SPY")


def test_validate_normalized_ohlcv_rejects_duplicates() -> None:
    df = pd.read_csv(FIXTURE).head(5)
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    with pytest.raises(MarketDataValidationError, match="Duplicate"):
        validate_normalized_ohlcv(df, symbol="SPY")


def test_validate_normalized_ohlcv_ok() -> None:
    df = validate_normalized_ohlcv(pd.read_csv(FIXTURE), symbol="SPY")
    assert list(df["date"]) == sorted(df["date"].tolist())
    assert (df["close"] > 0).all()


def test_signal_and_one_day_position_lag(fixture_adapter: FixtureMarketDataAdapter) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    result = run_ma_crossover_research(
        series.frame, short_window=20, long_window=60, transaction_cost=0.001
    )
    frame = result.frame
    price = series.frame.copy()
    price["ma_s"] = price["adjusted_close"].rolling(20).mean()
    price["ma_l"] = price["adjusted_close"].rolling(60).mean()
    price["sig"] = (price["ma_s"] > price["ma_l"]).astype(int)
    price["pos"] = price["sig"].shift(1)
    price["date"] = pd.to_datetime(price["date"])
    merged = frame.copy()
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.merge(price[["date", "sig", "pos"]], on="date", how="left")
    assert (merged["signal"].astype(int) == merged["sig"].astype(int)).all()
    assert (merged["position"].astype(float) == merged["pos"].astype(float)).all()


def test_transaction_cost_only_on_position_changes(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    result = run_ma_crossover_research(
        series.frame, short_window=20, long_window=60, transaction_cost=0.001
    )
    frame = result.frame
    assert (frame.loc[frame["turnover"] == 0, "transaction_cost"] == 0).all()
    changing = frame["turnover"] > 0
    assert (
        frame.loc[changing, "transaction_cost"]
        == frame.loc[changing, "turnover"] * 0.001
    ).all()


def test_metrics_cagr_vol_sharpe_drawdown_trades(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    result = run_ma_crossover_research(series.frame)
    m = result.strategy_metrics
    assert m.observation_count > 100
    assert m.total_return is not None
    assert m.cagr is not None
    assert m.annualized_volatility is not None and m.annualized_volatility > 0
    assert m.maximum_drawdown is not None and m.maximum_drawdown <= 0
    assert m.trade_count is not None and m.trade_count >= 0
    assert m.win_rate is None or 0 <= m.win_rate <= 1
    assert m.total_transaction_costs is not None and m.total_transaction_costs >= 0
    assert abs(float(result.frame["cumulative_strategy"].iloc[-1]) - 1 - m.total_return) < 1e-9


def test_trade_count_definition(fixture_adapter: FixtureMarketDataAdapter) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    result = run_ma_crossover_research(series.frame)
    expected = int((result.frame["turnover"] > 0).sum())
    assert result.strategy_metrics.trade_count == expected


def test_invalid_window_raises(fixture_adapter: FixtureMarketDataAdapter) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    with pytest.raises(ValueError, match="short_window"):
        run_ma_crossover_research(series.frame, short_window=60, long_window=20)


def test_insufficient_history_raises(fixture_adapter: FixtureMarketDataAdapter) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    short = series.frame.head(50)
    with pytest.raises(ValueError, match="Insufficient history"):
        run_ma_crossover_research(short, short_window=20, long_window=60)


def test_service_success(service: ResearchExecutionService) -> None:
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": "2018-01-01",
            "end_date": None,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0,
        }
    )
    assert result["research_id"] == "ma-crossover-spy"
    assert result["provenance"]["symbol"] == "SPY"
    assert result["provenance"]["actual_start"]
    assert result["supported_evidence"]["historical_backtest"] == "completed"
    assert result["supported_evidence"]["evaluation"] == "unavailable"


def test_service_rejects_bad_research_id(service: ResearchExecutionService) -> None:
    with pytest.raises(ResearchExecutionError) as exc:
        service.execute({"research_id": "not allowed / path"})
    assert exc.value.status_code == 400


def test_service_accepts_local_ma_research_id(
    service: ResearchExecutionService,
) -> None:
    result = service.execute(
        {
            "research_id": "research-local-demo",
            "symbol": "SPY",
            "benchmark": "SPY",
        }
    )
    assert result["research_id"] == "research-local-demo"


def test_api_success_with_fixture(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/research/execution",
        json={
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": "2018-01-01",
            "end_date": None,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["research_id"] == "ma-crossover-spy"
    assert body["provenance"]["provider"] == "fixture"
    assert body["metrics"]["observation_count"] > 0
    assert "generated_at" in body


def test_api_market_data_validation_maps_to_502(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.research_execution.market_data_port import MarketDataValidationError

    class BrokenAdapter:
        def get_daily_ohlcv(self, symbol, start_date, end_date=None):
            raise MarketDataValidationError(
                "Column 'open' must be positive and valid."
            )

    monkeypatch.setattr(
        research_execution_route,
        "get_research_execution_service",
        lambda: ResearchExecutionService(BrokenAdapter()),  # type: ignore[arg-type]
    )
    app = FastAPI()
    app.include_router(research_execution_route.router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/research/execution",
        json={
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
            "start_date": "2018-01-01",
            "end_date": None,
            "short_window": 20,
            "long_window": 60,
            "transaction_cost": 0.001,
            "risk_free_rate": 0,
        },
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Column 'open' must be positive and valid."


def test_yahoo_adapter_drops_incomplete_nan_bar(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter

    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(["2018-01-02", "2026-07-14"]),
            "Open": [235.0, float("nan")],
            "High": [236.0, float("nan")],
            "Low": [234.0, float("nan")],
            "Close": [235.5, float("nan")],
            "Volume": [1000, 0],
        }
    ).set_index("Date")

    monkeypatch.setattr(
        "app.research_execution.yahoo_adapter.yf.download",
        lambda *_args, **_kwargs: frame,
    )
    adapter = YahooFinanceMarketDataAdapter(
        cache=__import__(
            "app.research_execution.price_cache", fromlist=["PriceCache"]
        ).PriceCache(root=tmp_path)
    )
    series = adapter.get_daily_ohlcv("SPY", "2018-01-01")
    assert len(series.frame) == 1
    assert any("incomplete Yahoo Finance bar" in warning for warning in series.warnings)


def test_api_invalid_windows(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/research/execution",
        json={"short_window": 60, "long_window": 20},
    )
    assert response.status_code == 422


def test_json_safe_null_not_nan(fixture_adapter: FixtureMarketDataAdapter) -> None:
    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    # Constant prices → zero vol → Sharpe should be null with warning.
    flat = series.frame.copy()
    for col in ("open", "high", "low", "close", "adjusted_close"):
        flat[col] = 100.0
    result = run_ma_crossover_research(flat)
    payload = metrics_to_dict(result.strategy_metrics)
    assert payload["sharpe_ratio"] is None
    assert any("Sharpe" in w for w in result.warnings)
    for value in payload.values():
        if isinstance(value, float):
            assert value == value  # not NaN
            assert abs(value) != float("inf")


def test_api_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.research_execution.market_data_port import MarketDataError

    class BrokenAdapter:
        def get_daily_ohlcv(self, symbol, start_date, end_date=None, interval="1d"):
            raise MarketDataError("provider down")

    monkeypatch.setattr(
        research_execution_route,
        "get_research_execution_service",
        lambda: ResearchExecutionService(BrokenAdapter()),  # type: ignore[arg-type]
    )
    app = FastAPI()
    app.include_router(research_execution_route.router)
    client = TestClient(app)
    response = client.post("/api/v1/research/execution", json={})
    assert response.status_code == 502
    assert "provider" in response.json()["detail"].lower()


def test_cache_metadata_roundtrip(tmp_path) -> None:
    from app.research_execution.price_cache import PriceCache

    adapter = FixtureMarketDataAdapter(FIXTURE)
    series = adapter.get_daily_ohlcv("SPY", "2018-01-01")
    cache = PriceCache(root=tmp_path)
    key = PriceCache.make_key("fixture", "SPY", "2018-01-01", None)
    cache.put(key, series)
    hit, stale = cache.get(key)
    assert hit is not None
    assert stale is False
    assert hit.provenance.cache_hit is True
    assert hit.provenance.retrieved_at == series.provenance.retrieved_at


def test_benchmark_mismatch_rejected(service: ResearchExecutionService) -> None:
    with pytest.raises(ResearchExecutionError) as exc:
        service.execute(
            {
                "research_id": "ma-crossover-spy",
                "symbol": "SPY",
                "benchmark": "QQQ",
            }
        )
    assert exc.value.status_code == 400
    assert "same-asset buy-and-hold" in exc.value.message


def test_api_benchmark_mismatch_returns_400(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/research/execution",
        json={"symbol": "SPY", "benchmark": "QQQ"},
    )
    assert response.status_code == 400
    assert "same-asset buy-and-hold" in response.json()["detail"]


def test_response_benchmark_label_matches_calculated_series(
    service: ResearchExecutionService,
) -> None:
    result = service.execute(
        {
            "research_id": "ma-crossover-spy",
            "symbol": "SPY",
            "benchmark": "SPY",
        }
    )
    strategy = result["strategy"]
    assert strategy["symbol"] == "SPY"
    assert strategy["benchmark"] == "SPY"
    assert strategy["benchmark_type"] == "same_asset_buy_and_hold"
    assert strategy["benchmark_label"] == "SPY Buy & Hold"


def test_open_ended_request_excludes_incomplete_session_day(
    fixture_adapter: FixtureMarketDataAdapter,
) -> None:
    from datetime import date

    from app.research_execution.market_data_port import clip_to_completed_daily_bars

    series = fixture_adapter.get_daily_ohlcv("SPY", "2018-01-01")
    # Simulate a fixture that includes an incomplete "today" bar relative to a fixed as_of.
    frame = series.frame.copy()
    last = frame.iloc[-1].copy()
    incomplete_day = date(2024, 6, 15)
    last["date"] = pd.Timestamp(incomplete_day)
    # Avoid duplicate-date validation issues by replacing the last row date only after
    # constructing a synthetic series via clip with as_of that day.
    frame.loc[frame.index[-1], "date"] = pd.Timestamp(incomplete_day)
    # Ensure uniqueness: drop any prior row on that date.
    frame = frame[
        ~(
            (pd.to_datetime(frame["date"]).dt.date == incomplete_day)
            & (frame.index != frame.index[-1])
        )
    ].reset_index(drop=True)

    from app.research_execution.market_data_port import (
        DataProvenance,
        NormalizedMarketSeries,
        series_actual_bounds,
    )

    actual_start, actual_end = series_actual_bounds(frame)
    synthetic = NormalizedMarketSeries(
        symbol="SPY",
        frame=frame,
        provenance=DataProvenance(
            provider="fixture",
            symbol="SPY",
            source="Local Fixture",
            retrieved_at="2024-06-15T15:00:00Z",
            requested_start="2018-01-01",
            requested_end=None,
            actual_start=actual_start,
            actual_end=actual_end,
            interval="1d",
        ),
    )
    clipped = clip_to_completed_daily_bars(
        synthetic, end_date=None, as_of=incomplete_day
    )
    clipped_dates = pd.to_datetime(clipped.frame["date"]).dt.date
    assert incomplete_day not in set(clipped_dates)
    assert clipped.provenance.actual_end < incomplete_day.isoformat() or (
        clipped.provenance.actual_end != incomplete_day.isoformat()
    )
    assert clipped.provenance.actual_end == max(clipped_dates).isoformat()


def test_yahoo_timeout_maps_to_unavailable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    from app.research_execution.market_data_port import MarketDataUnavailableError
    from app.research_execution.yahoo_adapter import YahooFinanceMarketDataAdapter

    def _timeout(*_args, **_kwargs):
        raise TimeoutError("simulated provider timeout")

    monkeypatch.setattr("app.research_execution.yahoo_adapter.yf.download", _timeout)
    adapter = YahooFinanceMarketDataAdapter(cache=__import__(
        "app.research_execution.price_cache", fromlist=["PriceCache"]
    ).PriceCache(root=tmp_path), timeout_seconds=1.5)
    with pytest.raises(MarketDataUnavailableError, match="timed out"):
        adapter.get_daily_ohlcv("SPY", "2018-01-01")
