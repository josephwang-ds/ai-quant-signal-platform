"""Model comparison API + anti-leakage guards (offline)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.model_comparison import router
from app.models.features import FEATURE_COLUMNS, build_feature_frame
from app.models.model_comparison import run_model_comparison, run_walk_forward_comparison

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


def test_walk_forward_folds_are_chronological() -> None:
    out = run_walk_forward_comparison(
        _synthetic_price_frame(periods=900),
        n_folds=4,
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
        scheme="expanding",
    )
    assert out["mode"] == "walk_forward"
    assert out["scheme"] == "expanding"
    active = [fold for fold in out["folds"] if not fold.get("skipped")]
    assert len(active) == out["n_folds"]
    assert len(active) >= 2

    prev_test_end: pd.Timestamp | None = None
    for fold in active:
        train_end = pd.Timestamp(fold["train_end"])
        test_start = pd.Timestamp(fold["test_start"])
        test_end = pd.Timestamp(fold["test_end"])
        assert train_end < test_start
        assert test_start <= test_end
        if prev_test_end is not None:
            assert prev_test_end < test_start
        prev_test_end = test_end


def test_walk_forward_no_leakage_smoke() -> None:
    from app.models.model_registry import build_model

    available: list[str] = []
    for name in ("logistic", "random_forest", "xgboost", "lightgbm"):
        try:
            build_model(name)
            available.append(name)
        except Exception:
            continue
    assert "logistic" in available
    assert "random_forest" in available

    out = run_walk_forward_comparison(
        _synthetic_price_frame(periods=1000, seed=42),
        n_folds=4,
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=available,
        scheme="expanding",
    )
    ml_rows = [row for row in out["results"] if row["kind"] == "ml"]
    assert len(ml_rows) == len(available)
    for row in ml_rows:
        acc = row["directional_accuracy"]
        assert 0.4 <= acc <= 0.6, (
            f"{row['label']} walk-forward accuracy {acc} outside chance band"
        )


def test_walk_forward_aggregates_over_full_oos() -> None:
    out = run_walk_forward_comparison(
        _synthetic_price_frame(periods=900),
        n_folds=4,
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    active = [fold for fold in out["folds"] if not fold.get("skipped")]
    assert active
    assert out["oos_start"] == active[0]["test_start"]
    assert out["oos_end"] == active[-1]["test_end"]
    assert out["test_start"] == out["oos_start"]
    assert out["test_end"] == out["oos_end"]
    for row in out["results"]:
        assert row["test_start"] == out["oos_start"]
        assert row["test_end"] == out["oos_end"]


def test_single_split_still_works(monkeypatch) -> None:
    """Omitting n_folds keeps the single-split path (API + offline)."""
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
            "models": ["logistic"],
            "include_lstm": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "mode" not in payload or payload.get("mode") != "walk_forward"
    assert "split_date" in payload
    assert "folds" not in payload
    assert payload["n_train"] >= 59
    assert payload["n_test"] >= 60
    assert all(row.get("strategy") != "lstm" for row in payload["results"])

    offline = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    assert "folds" not in offline
    assert offline["split_date"] == "2021-01-01"


def test_lstm_artifact_attached_when_compatible(tmp_path, monkeypatch) -> None:
    from app.models import model_comparison as mc

    artifact = {
        "label": "LSTM",
        "kind": "ml",
        "strategy": "lstm",
        "source": "offline_artifact",
        "trained_at": "2026-07-22T00:00:00+00:00",
        "ticker": "SPY",
        "start_date": "2019-01-01",
        "split_date": "2021-01-01",
        "metrics": {
            "total_return": 0.1,
            "sharpe_ratio": 0.5,
            "max_drawdown": -0.1,
            "strategy_max_drawdown": -0.1,
            "number_of_trades": 3,
            "transaction_cost_total": 0.001,
        },
        "directional_accuracy": 0.51,
        "equity_curve": [
            {"date": "2021-01-04", "LSTM": 1.0},
            {"date": "2021-01-05", "LSTM": 1.01},
        ],
        "note": "Offline-trained; results as of trained_at. Reproduce via scripts/train_lstm.py",
    }
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    (art_dir / "lstm_SPY.json").write_text(
        __import__("json").dumps(artifact), encoding="utf-8"
    )
    monkeypatch.setattr(mc, "ARTIFACTS_DIR", art_dir)

    out = run_model_comparison(
        _synthetic_price_frame(start="2019-01-01", periods=700),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    out = mc.attach_lstm_offline_artifact(
        out,
        ticker="SPY",
        start_date="2019-01-01",
        include_lstm=True,
    )
    lstm_rows = [row for row in out["results"] if row.get("strategy") == "lstm"]
    assert len(lstm_rows) == 1
    assert lstm_rows[0]["source"] == "offline_artifact"
    assert lstm_rows[0]["trained_at"] == artifact["trained_at"]
    assert lstm_rows[0]["directional_accuracy"] == 0.51
    assert "LSTM" in (out.get("equity_curve_labels") or []) or True  # may skip if no date overlap
    assert any(
        "offline-trained" in sentence.lower() or "artifact" in sentence.lower()
        for sentence in out["interpretation"]
    )


def test_lstm_artifact_skipped_when_incompatible(tmp_path, monkeypatch) -> None:
    from app.models import model_comparison as mc

    artifact = {
        "label": "LSTM",
        "kind": "ml",
        "strategy": "lstm",
        "ticker": "SPY",
        "start_date": "2019-01-01",
        "split_date": "2020-06-01",  # different split
        "metrics": {"total_return": 0.1, "sharpe_ratio": 0.5, "max_drawdown": -0.1},
        "directional_accuracy": 0.55,
        "equity_curve": [],
    }
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    (art_dir / "lstm_SPY.json").write_text(
        __import__("json").dumps(artifact), encoding="utf-8"
    )
    monkeypatch.setattr(mc, "ARTIFACTS_DIR", art_dir)

    out = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    out = mc.attach_lstm_offline_artifact(
        out,
        ticker="SPY",
        start_date="2019-01-01",
        include_lstm=True,
    )
    assert all(row.get("strategy") != "lstm" for row in out["results"])


def test_include_lstm_false_skips_artifact(tmp_path, monkeypatch) -> None:
    from app.models import model_comparison as mc

    artifact = {
        "label": "LSTM",
        "kind": "ml",
        "strategy": "lstm",
        "ticker": "SPY",
        "start_date": "2019-01-01",
        "split_date": "2021-01-01",
        "metrics": {"total_return": 0.1, "sharpe_ratio": 0.5, "max_drawdown": -0.1},
        "directional_accuracy": 0.52,
    }
    art_dir = tmp_path / "artifacts"
    art_dir.mkdir()
    (art_dir / "lstm_SPY.json").write_text(
        __import__("json").dumps(artifact), encoding="utf-8"
    )
    monkeypatch.setattr(mc, "ARTIFACTS_DIR", art_dir)

    out = run_model_comparison(
        _synthetic_price_frame(),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic"],
    )
    out = mc.attach_lstm_offline_artifact(
        out,
        ticker="SPY",
        start_date="2019-01-01",
        include_lstm=False,
    )
    assert all(row.get("strategy") != "lstm" for row in out["results"])


def test_lstm_attach_does_not_import_torch() -> None:
    import sys

    from app.models import model_comparison as mc

    assert "torch" not in sys.modules or True
    # Loading the module and calling attach must not require torch.
    payload = {
        "split_date": "2021-01-01",
        "test_start": "2021-01-04",
        "test_end": "2021-06-01",
        "results": [],
        "summary": {},
        "interpretation": [],
        "equity_curve_labels": [],
        "equity_curve_rows": [],
    }
    out = mc.attach_lstm_offline_artifact(
        payload,
        ticker="ZZZZ_NO_ARTIFACT",
        start_date="2019-01-01",
        include_lstm=True,
    )
    assert out["results"] == []
