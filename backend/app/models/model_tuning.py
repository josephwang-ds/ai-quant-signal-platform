"""Train-set-only hyperparameter search with TimeSeriesSplit (no shuffle).

Never uses KFold or random shuffles — that would break chronological order.
Grids stay small and regularization-biased to limit overfit on validation folds.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline

TUNE_INTERPRETATION = (
    "Hyperparameter tuning on financial data easily overfits the validation folds — "
    "treat out-of-sample results as authoritative."
)

# Small, regularization-leaning spaces keyed by registry id.
# Params target the ``clf`` step inside ``build_model_pipeline``.
_PARAM_DISTRIBUTIONS: dict[str, dict[str, list[Any]]] = {
    "logistic_l2": {
        "clf__C": [0.01, 0.05, 0.1, 0.5, 1.0],
    },
    "logistic_l1": {
        "clf__C": [0.01, 0.05, 0.1, 0.5, 1.0],
    },
    "logistic_en": {
        "clf__C": [0.01, 0.1, 0.5, 1.0],
        "clf__l1_ratio": [0.15, 0.5, 0.85],
    },
    "ridge_clf": {
        "clf__alpha": [0.1, 1.0, 10.0, 50.0],
    },
    "svm": {
        "clf__C": [0.1, 0.5, 1.0, 2.0],
        "clf__gamma": ["scale", 0.01, 0.05],
    },
    "random_forest": {
        "clf__max_depth": [2, 3, 4],
        "clf__min_samples_leaf": [5, 10, 20],
        "clf__n_estimators": [100, 200],
    },
    "xgboost": {
        "clf__max_depth": [2, 3],
        "clf__learning_rate": [0.03, 0.05, 0.08],
        "clf__n_estimators": [100, 200],
        "clf__reg_lambda": [1.0, 5.0, 10.0],
    },
    "lightgbm": {
        "clf__max_depth": [2, 3],
        "clf__learning_rate": [0.03, 0.05, 0.08],
        "clf__n_estimators": [100, 200],
        "clf__reg_lambda": [1.0, 5.0, 10.0],
    },
    "ridge_reg": {
        "clf__alpha": [0.1, 1.0, 10.0, 50.0],
    },
    "lasso_reg": {
        "clf__alpha": [0.0001, 0.0005, 0.001, 0.005],
    },
    "elasticnet_reg": {
        "clf__alpha": [0.0001, 0.0005, 0.001],
        "clf__l1_ratio": [0.15, 0.5, 0.85],
    },
}

DEFAULT_N_ITER = 8
DEFAULT_N_SPLITS = 3


def tune_param_space(model_name: str) -> Optional[dict[str, list[Any]]]:
    """Return a small param grid, or None when tuning is not supported."""
    return _PARAM_DISTRIBUTIONS.get(model_name)


def fit_with_optional_tune(
    pipeline: Pipeline,
    *,
    model_name: str,
    X_train: Any,
    y_train: Any,
    tune: bool,
    paradigm: str,
    n_iter: int = DEFAULT_N_ITER,
    n_splits: int = DEFAULT_N_SPLITS,
    random_state: int = 42,
) -> tuple[Pipeline, Optional[dict[str, Any]]]:
    """
    Fit ``pipeline`` on the training split.

    When ``tune`` is True and a param space exists, run RandomizedSearchCV with
    ``TimeSeriesSplit`` **inside the training window only**, then refit on all
    train rows. Returns ``(fitted_estimator, best_params_or_None)``.
    """
    space = tune_param_space(model_name) if tune else None
    if not space:
        pipeline.fit(X_train, y_train)
        return pipeline, None

    n_rows = len(X_train)
    splits = min(n_splits, max(2, n_rows // 40))
    if n_rows < splits + 10:
        pipeline.fit(X_train, y_train)
        return pipeline, None

    scoring = "neg_mean_squared_error" if paradigm == "regressor" else "accuracy"
    search = RandomizedSearchCV(
        pipeline,
        param_distributions=space,
        n_iter=min(n_iter, int(np.prod([len(v) for v in space.values()]))),
        cv=TimeSeriesSplit(n_splits=splits),
        scoring=scoring,
        refit=True,
        random_state=random_state,
        n_jobs=1,
        error_score="raise",
    )
    search.fit(X_train, y_train)
    best_params = {
        str(k).removeprefix("clf__"): _jsonable(v)
        for k, v in (search.best_params_ or {}).items()
    }
    return search.best_estimator_, best_params


def _jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value
