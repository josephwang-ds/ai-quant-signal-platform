"""Risk review API tests (offline — monkeypatch load_price_data)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.risk_review import (
    COMPONENT_KEYS,
    build_risk_monitor_input,
    router,
)
from app.backtest.metrics import TRADING_DAYS_PER_YEAR
from app.risk.risk_monitor import calculate_drawdown_level, calculate_overall_risk_level
from app.risk.risk_profile import (
    AGGRESSIVE_PROFILE,
    CONSERVATIVE_PROFILE,
    HISTORICAL_DRAWDOWN_LEVELS,
    MODERATE_PROFILE,
    resolve_risk_profile,
)

risk_app = FastAPI()
risk_app.include_router(router)
client = TestClient(risk_app)

REVIEW_URL = "/api/v1/risk/review"


def _sample_price_frame() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=120, freq="B")
    # Mild oscillation so MA crossover produces some trades without inventing metrics.
    close = pd.Series(
        [100 + ((i % 20) - 10) * 0.8 + i * 0.05 for i in range(120)],
        index=dates,
        dtype=float,
    )
    return pd.DataFrame(
        {
            "date": dates,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1_000_000,
            "data_source": "yahoo",
        }
    )


def _synthetic_backtest_in_drawdown(
    *,
    latest_drawdown: float = -0.05,
    max_drawdown: float = -0.28,
    n: int = 120,
) -> tuple[dict, pd.DataFrame]:
    """Build metrics + frame ending mid-drawdown with controllable vol regime."""
    rng = np.random.default_rng(7)
    # Calm early regime, then amplified shocks — recent vol >> full-period avg.
    early = rng.normal(0.0, 0.003, size=n - 50)
    late = rng.normal(0.0, 0.03, size=50)
    daily = np.concatenate([early, late])
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    close = 100.0 * np.cumprod(1.0 + daily)
    drawdown = np.linspace(0.0, latest_drawdown, n)

    backtest_df = pd.DataFrame(
        {
            "date": dates,
            "close": close,
            "daily_return": daily,
            "strategy_drawdown": drawdown,
            "trade_action": [None] * n,
            "strategy_return_before_cost": daily,
            "strategy_return": daily,
            "cost": 0.0,
            "trade": 0,
            "cumulative_strategy": np.cumprod(1.0 + daily),
            "cumulative_benchmark": np.cumprod(1.0 + daily),
        }
    )
    full_vol = float(np.std(daily) * math.sqrt(TRADING_DAYS_PER_YEAR))
    metrics = {
        "max_drawdown": max_drawdown,
        "strategy_max_drawdown": max_drawdown,
        "volatility": full_vol,
        "sharpe_ratio": 0.4,
        "transaction_cost_total": 0.0,
        "total_return": float(backtest_df["cumulative_strategy"].iloc[-1] - 1.0),
    }
    return metrics, backtest_df


def test_risk_review_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.risk_review.load_price_data",
        lambda *args, **kwargs: _sample_price_frame(),
    )

    response = client.post(
        REVIEW_URL,
        json={
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 5,
            "long_window": 20,
            "transaction_cost": 0.001,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["strategy"] == "ma_crossover"
    assert payload["drawdown_mode"] == "current"
    assert payload["risk_profile"] == "aggressive"
    assert "metrics" in payload
    assert "volatility" in payload["metrics"]
    assert "max_drawdown" in payload["metrics"]
    assert "sharpe_ratio" in payload["metrics"]

    risk = payload["risk"]
    assert 1 <= risk["risk_level"] <= 5
    assert isinstance(risk["risk_label"], str) and risk["risk_label"]
    assert isinstance(risk["allowed_action"], str) and risk["allowed_action"]
    assert isinstance(risk["risk_reasons"], list)
    assert set(risk["component_levels"].keys()) == set(COMPONENT_KEYS)
    for key in COMPONENT_KEYS:
        assert 1 <= risk["component_levels"][key] <= 5


def test_risk_review_missing_optional_metrics_degrade_to_level_one() -> None:
    """Absent optional inputs must not raise; related components stay at level 1."""
    metrics = {
        "max_drawdown": 0.0,
        "strategy_max_drawdown": 0.0,
        # volatility / sharpe intentionally omitted
        "transaction_cost_total": 0.0,
        "total_return": 0.0,
    }
    empty_df = pd.DataFrame(
        {
            "close": [100.0, 101.0],
            "trade_action": [None, None],
            "strategy_return_before_cost": [0.0, 0.0],
        }
    )
    assessment = calculate_overall_risk_level(
        build_risk_monitor_input(metrics, empty_df)
    )
    assert assessment.risk_level >= 1
    assert assessment.component_levels["volatility"] == 1
    assert assessment.component_levels["sharpe_decline"] == 1
    assert assessment.component_levels["signal_conflict"] == 1
    assert assessment.component_levels["cost_drag"] == 1
    assert assessment.component_levels["single_trade_loss"] == 1
    assert assessment.component_levels["consecutive_losses"] == 1


def test_risk_review_no_price_data_returns_404(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise ValueError("No price data found for ticker 'ZZZZ' (2023-01-01 → latest).")

    monkeypatch.setattr("app.api.routes.risk_review.load_price_data", _raise)

    response = client.post(
        REVIEW_URL,
        json={
            "ticker": "ZZZZ",
            "start_date": "2023-01-01",
            "strategy": "ma_crossover",
            "short_window": 5,
            "long_window": 20,
        },
    )

    assert response.status_code == 404
    assert "No price data found" in response.json()["detail"]


def test_current_drawdown_mode_tracks_latest_not_pinned_at_five() -> None:
    metrics, frame = _synthetic_backtest_in_drawdown(
        latest_drawdown=-0.05,
        max_drawdown=-0.40,
    )
    monitor = build_risk_monitor_input(metrics, frame, drawdown_mode="current")
    assert abs(monitor.current_drawdown - (-0.05)) < 1e-9
    assessment = calculate_overall_risk_level(monitor, profile=AGGRESSIVE_PROFILE)
    dd_level = assessment.component_levels["drawdown"]
    assert dd_level == calculate_drawdown_level(-0.05, AGGRESSIVE_PROFILE)
    assert dd_level != 5
    assert 1 <= dd_level <= 4


def test_historical_drawdown_mode_uses_recalibrated_thresholds() -> None:
    metrics, frame = _synthetic_backtest_in_drawdown(
        latest_drawdown=-0.05,
        max_drawdown=-0.25,
    )
    monitor = build_risk_monitor_input(metrics, frame, drawdown_mode="historical")
    assert abs(monitor.current_drawdown - (-0.25)) < 1e-9

    profile = resolve_risk_profile("aggressive", drawdown_mode="historical")
    assert profile.drawdown_levels == HISTORICAL_DRAWDOWN_LEVELS
    assessment = calculate_overall_risk_level(monitor, profile=profile)
    dd_level = assessment.component_levels["drawdown"]
    # -0.25 sits between -0.20 and -0.35 → level 3 under historical thresholds.
    assert dd_level == calculate_drawdown_level(-0.25, profile)
    assert dd_level == 3
    assert dd_level != 5


def test_recent_volatility_elevation_raises_component() -> None:
    metrics, frame = _synthetic_backtest_in_drawdown()
    monitor = build_risk_monitor_input(metrics, frame, drawdown_mode="current")
    assert monitor.volatility is not None
    assert monitor.baseline_volatility is not None
    assert monitor.volatility > monitor.baseline_volatility * 1.1
    assessment = calculate_overall_risk_level(monitor, profile=AGGRESSIVE_PROFILE)
    assert assessment.component_levels["volatility"] > 1


def test_all_risk_profiles_run_with_components_in_range(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.risk_review.load_price_data",
        lambda *args, **kwargs: _sample_price_frame(),
    )
    for name, expected in (
        ("conservative", CONSERVATIVE_PROFILE.name),
        ("moderate", MODERATE_PROFILE.name),
        ("aggressive", AGGRESSIVE_PROFILE.name),
    ):
        response = client.post(
            REVIEW_URL,
            json={
                "ticker": "AAPL",
                "start_date": "2023-01-01",
                "strategy": "ma_crossover",
                "short_window": 5,
                "long_window": 20,
                "risk_profile": name,
                "drawdown_mode": "current",
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["risk_profile"] == expected
        levels = payload["risk"]["component_levels"]
        assert set(levels.keys()) == set(COMPONENT_KEYS)
        for key in COMPONENT_KEYS:
            assert 1 <= levels[key] <= 5
