"""Model comparison API + anti-leakage guards (offline)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.model_comparison import router
from app.models.features import FEATURE_COLUMNS, build_feature_frame
from app.models.model_comparison import run_model_comparison

compare_app = FastAPI()
compare_app.include_router(router)
client = TestClient(compare_app)

COMPARE_URL = "/api/v1/models/compare"

METRIC_KEYS = ("total_return", "sharpe_ratio", "max_drawdown", "number_of_trades")


def _synthetic_price_frame(
    *,
    start: str = "2019-01-01",
    periods: int = 700,
    seed: int | None = None,
) -> pd.DataFrame:
    dates = pd.date_range(start, periods=periods, freq="B")
    if seed is None:
        close = pd.Series(
            [100 + ((i % 30) - 15) * 0.4 + i * 0.015 for i in range(periods)],
            dtype=float,
        )
    else:
        rng = np.random.default_rng(seed)
        # Unpredictable random walk — future shocks must not leak into features.
        shocks = rng.normal(0.0, 0.01, size=periods)
        close = pd.Series(100.0 * np.cumprod(1.0 + shocks), dtype=float)

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


def test_compare_endpoint_happy_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.routes.model_comparison.load_price_data",
        lambda *args, **kwargs: _synthetic_price_frame(),
    )

    response = client.post(
        COMPARE_URL,
        json={
            "ticker": "SPY",
            "start_date": "2019-01-01",
            "split_date": "2021-01-01",
            "short_window": 20,
            "long_window": 60,
            "momentum_window": 60,
            "transaction_cost": 0.001,
            "models": ["logistic", "random_forest"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "SPY"
    assert payload["n_train"] >= 59
    assert payload["n_test"] >= 60
    assert "summary" in payload
    assert "interpretation" in payload
    assert any(row["kind"] == "ml" for row in payload["results"])
    assert any(row["kind"] == "rule" for row in payload["results"])


def test_compare_no_price_data_returns_404(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise ValueError("No price data found for ticker 'ZZZZ' (2019-01-01 → latest).")

    monkeypatch.setattr("app.api.routes.model_comparison.load_price_data", _raise)

    response = client.post(
        COMPARE_URL,
        json={
            "ticker": "ZZZZ",
            "start_date": "2019-01-01",
            "split_date": "2021-01-01",
            "models": ["logistic"],
        },
    )
    assert response.status_code == 404
    assert "No price data found" in response.json()["detail"]


def test_split_is_chronological_and_no_overlap() -> None:
    price = _synthetic_price_frame()
    split_date = "2021-01-01"
    split_ts = pd.Timestamp(split_date)

    _X, _y, aligned = build_feature_frame(price)
    dates = pd.to_datetime(aligned["date"])
    train_mask = dates < split_ts
    test_mask = dates >= split_ts
    assert train_mask.any() and test_mask.any()
    assert dates[train_mask].max() < dates[test_mask].min()

    raw_train = int(train_mask.sum())
    out = run_model_comparison(
        price,
        split_date=split_date,
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )

    # Embargo drops the last training row whose label uses the first test-day close.
    assert out["n_train"] == raw_train - 1
    assert out["n_test"] == int(test_mask.sum())
    assert pd.Timestamp(out["test_start"]) >= split_ts
    assert pd.Timestamp(out["test_start"]) <= pd.Timestamp(out["test_end"])


def test_features_have_no_future_columns() -> None:
    for name in FEATURE_COLUMNS:
        assert not name.startswith("y_")
        assert "next_" not in name
        assert "future_" not in name
        assert name != "close"

    price = _synthetic_price_frame()
    X, y, aligned = build_feature_frame(price)
    assert "y_next_up" not in X.columns
    assert y.name == "y_next_up"
    for col in X.columns:
        assert not col.startswith("y_")
        assert "next_" not in col
        assert "future_" not in col

    # Feature values must not equal a raw forward close shift.
    future_close = aligned["close"].shift(-1)
    for col in FEATURE_COLUMNS:
        equal_ratio = float((X[col] == future_close.loc[X.index]).mean())
        assert equal_ratio < 0.05, f"{col} looks like close.shift(-1)"

    out = run_model_comparison(
        price,
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    for row in out["results"]:
        if row["kind"] != "ml":
            continue
        for key in row["feature_importance"]:
            assert not key.startswith("y_")
            assert "next_" not in key
            assert "future_" not in key


def test_all_strategies_share_same_oos_window() -> None:
    out = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic", "random_forest"],
    )
    starts = {row["test_start"] for row in out["results"]}
    ends = {row["test_end"] for row in out["results"]}
    assert starts == {out["test_start"]}
    assert ends == {out["test_end"]}
    assert len(out["results"]) >= 2


def test_no_lookahead_smoke() -> None:
    """On a random walk, ML directional accuracy must stay near chance — not >0.9."""
    from app.models.model_registry import build_model

    available: list[str] = []
    for name in ("logistic", "random_forest", "xgboost", "lightgbm"):
        try:
            build_model(name)
            available.append(name)
        except Exception:
            # Native backends (xgboost/lightgbm) may be unavailable without OpenMP.
            continue
    assert "logistic" in available
    assert "random_forest" in available

    price = _synthetic_price_frame(periods=900, seed=42)
    out = run_model_comparison(
        price,
        split_date="2021-06-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=available,
    )
    ml_rows = [row for row in out["results"] if row["kind"] == "ml"]
    assert len(ml_rows) == len(available)
    for row in ml_rows:
        acc = row["directional_accuracy"]
        assert acc < 0.9, f"{row['label']} accuracy {acc} suggests look-ahead leakage"
        assert 0.4 <= acc <= 0.6, (
            f"{row['label']} accuracy {acc} outside chance band on random walk"
        )


def test_model_output_shape() -> None:
    out = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    kinds = {row["kind"] for row in out["results"]}
    assert kinds == {"ml", "rule"}
    for row in out["results"]:
        metrics = row["metrics"]
        for key in METRIC_KEYS:
            assert key in metrics
        if row["kind"] == "ml":
            assert "directional_accuracy" in row
            assert "feature_importance" in row


def test_equity_curve_rows_aligned_and_normalized() -> None:
    out = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    labels = out["equity_curve_labels"]
    rows = out["equity_curve_rows"]
    assert labels
    assert rows
    assert set(labels) == {row["label"] for row in out["results"]}
    assert "Buy & Hold" in labels

    first = rows[0]
    assert "date" in first
    for label in labels:
        assert label in first
        assert abs(float(first[label]) - 1.0) < 1e-9

    for row in rows:
        assert set(row.keys()) == {"date", *labels}
        for label in labels:
            assert isinstance(row[label], float)
            assert math.isfinite(row[label])
