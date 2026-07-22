"""Model constructors for research ML experiments.

Paradigms (do not conflate):
- classifier: next-day up/down
- regressor: next-day return → sign → signal
- timeseries: ARIMA on returns only (no FEATURE_COLUMNS)

Each call builds a fresh unfitted estimator — never reuse a global fitted model.
Heavy optional backends (xgboost / lightgbm) are imported inside constructors.
"""

from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import (
    ElasticNet,
    Lasso,
    LogisticRegression,
    Ridge,
    RidgeClassifier,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ModelParadigm = Literal["classifier", "regressor", "timeseries"]

# Sensible default subset when the client omits ``models``.
DEFAULT_MODELS: list[str] = [
    "logistic_l2",
    "random_forest",
    "xgboost",
    "lightgbm",
    "ridge_reg",
]

# Backward-compatible aliases → canonical registry ids.
MODEL_ALIASES: dict[str, str] = {
    "logistic": "logistic_l2",
}


def _logistic_l2() -> LogisticRegression:
    return LogisticRegression(max_iter=2000, random_state=42)


def _logistic_l1() -> LogisticRegression:
    return LogisticRegression(
        penalty="l1",
        solver="liblinear",
        max_iter=2000,
        random_state=42,
    )


def _logistic_en() -> LogisticRegression:
    return LogisticRegression(
        penalty="elasticnet",
        solver="saga",
        l1_ratio=0.5,
        max_iter=4000,
        random_state=42,
    )


def _ridge_clf() -> RidgeClassifier:
    return RidgeClassifier(random_state=42)


def _svm() -> SVC:
    return SVC(kernel="rbf", probability=True, random_state=42)


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


def _ridge_reg() -> Ridge:
    return Ridge(random_state=42)


def _lasso_reg() -> Lasso:
    return Lasso(alpha=0.0005, max_iter=4000, random_state=42)


def _elasticnet_reg() -> ElasticNet:
    return ElasticNet(alpha=0.0005, l1_ratio=0.5, max_iter=4000, random_state=42)


def _arima_placeholder() -> None:
    """ARIMA is fitted via ``fit_arima_direction_signals`` — not a sklearn estimator."""
    raise RuntimeError("ARIMA has no sklearn constructor; use fit_arima_direction_signals.")


def _offline_dl_placeholder() -> None:
    """CNN/LSTM ship as JSON artifacts — never fitted at request time."""
    raise RuntimeError(
        "Offline deep-learning models have no runtime constructor; "
        "load committed JSON via attach_offline_artifacts."
    )


MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "logistic_l2": {
        "constructor": _logistic_l2,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "Logistic L2",
    },
    "logistic_l1": {
        "constructor": _logistic_l1,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "Logistic L1",
    },
    "logistic_en": {
        "constructor": _logistic_en,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "Logistic ElasticNet",
    },
    "ridge_clf": {
        "constructor": _ridge_clf,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "Ridge Classifier",
    },
    "svm": {
        "constructor": _svm,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "SVM (RBF)",
    },
    "random_forest": {
        "constructor": _random_forest,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "Random Forest",
    },
    "xgboost": {
        "constructor": _xgboost,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "XGBoost",
    },
    "lightgbm": {
        "constructor": _lightgbm,
        "paradigm": "classifier",
        "uses_features": True,
        "label": "LightGBM",
    },
    "ridge_reg": {
        "constructor": _ridge_reg,
        "paradigm": "regressor",
        "uses_features": True,
        "label": "Ridge Regression",
    },
    "lasso_reg": {
        "constructor": _lasso_reg,
        "paradigm": "regressor",
        "uses_features": True,
        "label": "Lasso Regression",
    },
    "elasticnet_reg": {
        "constructor": _elasticnet_reg,
        "paradigm": "regressor",
        "uses_features": True,
        "label": "ElasticNet Regression",
    },
    "arima": {
        "constructor": _arima_placeholder,
        "paradigm": "timeseries",
        "uses_features": False,
        "label": "ARIMA",
    },
    "lstm": {
        "constructor": _offline_dl_placeholder,
        "paradigm": "offline_dl",
        "uses_features": True,
        "label": "LSTM",
    },
    "cnn": {
        "constructor": _offline_dl_placeholder,
        "paradigm": "offline_dl",
        "uses_features": True,
        "label": "CNN",
    },
    "rl": {
        "constructor": _offline_dl_placeholder,
        "paradigm": "offline_dl",
        "uses_features": True,
        "label": "RL (experimental)",
    },
}


def canonicalize_model_name(name: str) -> str:
    cleaned = name.strip()
    return MODEL_ALIASES.get(cleaned, cleaned)


def get_model_meta(name: str) -> dict[str, Any]:
    canonical = canonicalize_model_name(name)
    if canonical not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model '{name}'. Allowed: {', '.join(sorted(MODEL_REGISTRY))}."
        )
    return MODEL_REGISTRY[canonical]


def get_model_constructors() -> dict[str, Callable[[], Any]]:
    """Name → zero-arg constructor for feature-using sklearn estimators."""
    return {
        name: meta["constructor"]
        for name, meta in MODEL_REGISTRY.items()
        if meta["paradigm"] not in ("timeseries", "offline_dl")
    }


def list_model_ids() -> list[str]:
    return list(MODEL_REGISTRY.keys())


def build_classifier(name: str) -> Any:
    """Fresh unfitted feature-using estimator (classifier or regressor)."""
    meta = get_model_meta(name)
    if meta["paradigm"] in ("timeseries", "offline_dl"):
        raise ValueError(
            f"Model '{name}' is a {meta['paradigm']} paradigm and has no sklearn constructor."
        )
    return meta["constructor"]()


def build_estimator(name: str) -> Any:
    """Alias for ``build_classifier`` (covers regressors too)."""
    return build_classifier(name)


def build_model(name: str) -> Any:
    """
    Backward-compatible default: StandardScaler → estimator.

    Prefer ``build_model_pipeline`` when optional PCA / selection is needed.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", build_estimator(name)),
        ]
    )


def feature_importance(model: Any, feature_names: list[str]) -> dict[str, float]:
    """
    Extract non-negative importances aligned to ``feature_names``.

    Tree models use ``feature_importances_``.
    Linear models use normalised ``|coef_|``.
    When unavailable (e.g. RBF SVM), return ``{}`` — do not raise.
    """
    if len(feature_names) == 0:
        return {}

    importances: np.ndarray | None = None
    estimator = model
    if isinstance(model, Pipeline):
        estimator = model.named_steps.get("clf", model)

    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_, dtype=float)
        if coef.ndim == 2:
            coef = np.abs(coef).mean(axis=0)
        else:
            coef = np.abs(coef)
        total = float(coef.sum())
        importances = coef / total if total > 0 else coef

    if importances is None:
        return {}

    if len(importances) != len(feature_names):
        return {}

    return {
        name: float(value)
        for name, value in zip(feature_names, importances)
    }


def fit_arima_direction_signals(
    returns: pd.Series,
    train_index: Sequence[Any],
    test_index: Sequence[Any],
    *,
    order: tuple[int, int, int] = (1, 0, 1),
) -> pd.Series:
    """
    Expanding one-step ARIMA forecasts on the return series.

    At each test bar ``t`` (after close), append ``return[t]`` then forecast
    ``return[t+1]``; signal = 1 iff forecast > 0. Matches classifier timing
    (predict next-day move). Does not use FEATURE_COLUMNS.
    """
    from statsmodels.tsa.arima.model import ARIMA

    history = [float(x) for x in returns.loc[list(train_index)].astype(float).tolist()]
    signals: list[int] = []

    for idx in test_index:
        history.append(float(returns.loc[idx]))
        try:
            fitted = ARIMA(
                history,
                order=order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(method_kwargs={"maxiter": 50})
            forecast = fitted.forecast(1)
            pred = float(np.asarray(forecast).ravel()[0])
            signals.append(1 if pred > 0.0 else 0)
        except Exception:
            # Convergence / singular failures — safe neutral signal.
            signals.append(0)

    return pd.Series(signals, index=list(test_index), name="model_signal", dtype=int)
