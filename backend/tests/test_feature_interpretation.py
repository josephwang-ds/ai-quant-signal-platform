"""Unit tests for Feature Interpretation importance helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.models.feature_interpretation import (
    CAUSALITY_DISCLAIMER,
    build_importance_research,
    coefficient_importance,
    compute_importance_stability,
    permutation_importance_map,
)


def _toy_frame(n: int = 80, n_features: int = 5):
    rng = np.random.RandomState(0)
    X = pd.DataFrame(
        rng.normal(size=(n, n_features)),
        columns=[f"f{i}" for i in range(n_features)],
    )
    # Linear signal in f0
    y = (X["f0"] + rng.normal(scale=0.3, size=n) > 0).astype(int)
    return X, pd.Series(y)


def test_coefficient_importance_for_logistic():
    X, y = _toy_frame()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X, y)
    result = coefficient_importance(pipe, list(X.columns))
    assert result["available"] is True
    assert set(result["values"]) == set(X.columns)
    assert abs(sum(result["values"].values()) - 1.0) < 1e-6
    assert "f0" in result["signed"]


def test_coefficient_unavailable_for_forest():
    X, y = _toy_frame()
    pipe = Pipeline(
        [("clf", RandomForestClassifier(n_estimators=20, random_state=0, max_depth=3))]
    )
    pipe.fit(X, y)
    result = coefficient_importance(pipe, list(X.columns))
    assert result["available"] is False


def test_permutation_and_research_payload():
    X, y = _toy_frame()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X.iloc[:60], y.iloc[:60])
    perm = permutation_importance_map(
        pipe, X.iloc[60:], y.iloc[60:], list(X.columns), paradigm="classifier"
    )
    assert perm["available"] is True
    research = build_importance_research(
        pipe,
        X_test=X.iloc[60:],
        y_test=y.iloc[60:],
        original_names=list(X.columns),
        paradigm="classifier",
        native_importance={"f0": 0.5, "f1": 0.5},
    )
    assert research["disclaimer"] == CAUSALITY_DISCLAIMER
    assert research["methods"]["coefficient"]["available"] is True
    assert research["methods"]["permutation"]["available"] is True
    assert len(research["ranking"]) >= 1


def test_importance_stability_flags():
    folds = [
        {"a": 0.5, "b": 0.3, "c": 0.2},
        {"a": 0.48, "b": 0.32, "c": 0.2},
        {"a": 0.1, "b": 0.1, "c": 0.8},
    ]
    stability = compute_importance_stability(folds)
    assert stability["available"] is True
    assert stability["disclaimer"] == CAUSALITY_DISCLAIMER
    assert "a" in stability["consistent_features"] or "b" in stability["consistent_features"]
    assert "c" in stability["unstable_features"] or stability["per_feature"]["c"]["unstable"]


def test_stability_requires_two_folds():
    stability = compute_importance_stability([{"a": 1.0}])
    assert stability["available"] is False


def test_shap_unavailable_without_package(monkeypatch):
    X, y = _toy_frame()
    pipe = Pipeline(
        [("clf", RandomForestClassifier(n_estimators=20, random_state=0, max_depth=3))]
    )
    pipe.fit(X.iloc[:60], y.iloc[:60])

    import builtins
    import sys

    real_import = builtins.__import__

    def _block_shap(name, *args, **kwargs):
        if name == "shap" or name.startswith("shap."):
            raise ImportError("shap blocked for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_shap)
    sys.modules.pop("shap", None)

    from app.models.feature_interpretation import shap_importance_map

    result = shap_importance_map(pipe, X.iloc[60:], list(X.columns))
    assert result["available"] is False
    assert result["values"] == {}
    assert "not installed" in result["note"].lower() or "shap" in result["note"].lower()


def test_shap_does_not_fabricate_values_for_linear():
    from app.models.feature_interpretation import shap_importance_map

    X, y = _toy_frame()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X, y)
    result = shap_importance_map(pipe, X, list(X.columns))
    assert result["available"] is False
    assert result["values"] == {}


def test_pca_limitation_note_present():
    from sklearn.decomposition import PCA

    X, y = _toy_frame(n_features=6)
    pipe = Pipeline(
        [
            ("preprocess", PCA(n_components=2, random_state=0)),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X.iloc[:60], y.iloc[:60])
    research = build_importance_research(
        pipe,
        X_test=X.iloc[60:],
        y_test=y.iloc[60:],
        original_names=list(X.columns),
        paradigm="classifier",
        native_importance={"pc_1": 0.6, "pc_2": 0.4},
    )
    assert any("PCA" in item for item in research.get("limitations") or [])


def test_fit_signal_unchanged_when_importance_built():
    """Importance is computed after predict; signal path must stay independent."""
    X, y = _toy_frame()
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    pipe.fit(X.iloc[:60], y.iloc[:60])
    X_test = X.iloc[60:]
    before = pipe.predict(X_test)
    _ = build_importance_research(
        pipe,
        X_test=X_test,
        y_test=y.iloc[60:],
        original_names=list(X.columns),
        paradigm="classifier",
        native_importance={"f0": 1.0},
    )
    after = pipe.predict(X_test)
    np.testing.assert_array_equal(before, after)
