"""Model constructors for research ML experiments.

Each call builds a fresh unfitted estimator — never reuse a global fitted model.

Heavy optional backends (xgboost / lightgbm) are imported inside their
constructors so missing native libs on a local machine do not break logistic
or random-forest paths at import time.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def _logistic_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )


def _random_forest() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=4,
        random_state=42,
    )


def _xgboost() -> Any:
    from xgboost import XGBClassifier

    return XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        eval_metric="logloss",
        random_state=42,
    )


def _lightgbm() -> Any:
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )


def get_model_constructors() -> dict[str, Callable[[], Any]]:
    """Return name → zero-arg constructor. Callers must construct per run."""
    return {
        "logistic": _logistic_pipeline,
        "random_forest": _random_forest,
        "xgboost": _xgboost,
        "lightgbm": _lightgbm,
    }


def build_model(name: str) -> Any:
    constructors = get_model_constructors()
    if name not in constructors:
        raise ValueError(
            f"Unknown model '{name}'. Allowed: {', '.join(sorted(constructors))}."
        )
    return constructors[name]()


def feature_importance(model: Any, feature_names: list[str]) -> dict[str, float]:
    """
    Extract non-negative importances aligned to ``feature_names``.

    Tree models use ``feature_importances_``.
    Logistic regression (plain or Pipeline) uses normalised ``|coef_|``.
    """
    if len(feature_names) == 0:
        return {}

    importances: np.ndarray | None = None

    if hasattr(model, "feature_importances_"):
        importances = np.asarray(model.feature_importances_, dtype=float)
    elif isinstance(model, Pipeline):
        clf = model.named_steps.get("clf")
        if clf is not None and hasattr(clf, "coef_"):
            coef = np.asarray(clf.coef_, dtype=float)
            if coef.ndim == 2:
                coef = coef[0]
            abs_coef = np.abs(coef)
            total = float(abs_coef.sum())
            importances = abs_coef / total if total > 0 else abs_coef
    elif hasattr(model, "coef_"):
        coef = np.asarray(model.coef_, dtype=float)
        if coef.ndim == 2:
            coef = coef[0]
        abs_coef = np.abs(coef)
        total = float(abs_coef.sum())
        importances = abs_coef / total if total > 0 else abs_coef

    if importances is None:
        raise ValueError(
            "Model does not expose feature_importances_ or coef_ for importance extraction."
        )

    if len(importances) != len(feature_names):
        raise ValueError(
            f"Importance length {len(importances)} does not match "
            f"feature_names length {len(feature_names)}."
        )

    return {
        name: float(value)
        for name, value in zip(feature_names, importances)
    }
