"""Importance diagnostics must not alter prediction / backtest metrics."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.models.feature_interpretation import build_importance_research


def _toy(n: int = 100):
    rng_x = pd.DataFrame(
        {
            "f0": [((i % 7) - 3) / 3 for i in range(n)],
            "f1": [((i % 5) - 2) / 2 for i in range(n)],
            "f2": [((i % 11) - 5) / 5 for i in range(n)],
        }
    )
    y = (rng_x["f0"] > 0).astype(int)
    return rng_x, y


def _core_metrics(pipe: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    pred = pipe.predict(X)
    accuracy = float((pred == y.to_numpy()).mean())
    # Surrogate return-like series for invariance (not marketed as real alpha).
    signal = pd.Series(pred, index=X.index).astype(float)
    rets = signal * 0.001
    total_return = float((1 + rets).prod() - 1)
    return {
        "directional_accuracy": accuracy,
        "total_return": total_return,
        "trade_count": int((signal.diff().fillna(signal).abs() > 0).sum()),
        "predictions": pred.tolist(),
    }


def test_importance_research_does_not_change_prediction_metrics():
    X, y = _toy()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X.iloc[:70], y.iloc[:70])
    X_test, y_test = X.iloc[70:], y.iloc[70:]

    before = _core_metrics(pipe, X_test, y_test)
    before_snapshot = deepcopy(before)

    research = build_importance_research(
        pipe,
        X_test=X_test,
        y_test=y_test,
        original_names=list(X.columns),
        paradigm="classifier",
        native_importance={"f0": 0.5, "f1": 0.3, "f2": 0.2},
    )
    assert research["disclaimer"]
    assert research["methods"]["coefficient"]["available"] is True

    after = _core_metrics(pipe, X_test, y_test)
    assert after == before_snapshot
