"""LightGBM regression candidate with a small validation-selected grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.modeling.constants import (
    DEFAULT_LGBM_GRID,
    MODELING_IMPL_VERSION,
)
from app.cross_sectional.modeling.preprocessing import TrainOnlyPreprocessor
from app.cross_sectional.modeling.ridge import _selection_key

try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
    LIGHTGBM_VERSION = getattr(lgb, "__version__", "unknown")
except ImportError:  # pragma: no cover - exercised when dep missing
    lgb = None  # type: ignore[assignment]
    LIGHTGBM_AVAILABLE = False
    LIGHTGBM_VERSION = None


class LightGBMUnavailableError(RuntimeError):
    """Raised when LightGBM is requested but not installed."""


@dataclass
class LightGBMFitResult:
    hyperparameters: dict[str, Any]
    feature_order: list[str]
    preprocessing: dict[str, Any]
    training_cutoff: str
    random_seed: int
    best_iteration: int | None
    library_version: str | None
    model_name: str = "lightgbm"
    model_implementation_version: str = MODELING_IMPL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_implementation_version": self.model_implementation_version,
            "hyperparameters": self.hyperparameters,
            "feature_order": self.feature_order,
            "preprocessing": self.preprocessing,
            "training_cutoff": self.training_cutoff,
            "random_seed": self.random_seed,
            "best_iteration": self.best_iteration,
            "library_version": self.library_version,
            "complexity_note": "lightgbm_trees",
        }


def _require_lgbm() -> None:
    if not LIGHTGBM_AVAILABLE:
        raise LightGBMUnavailableError(
            "LightGBM is not installed. Install the pinned project dependency "
            "`lightgbm>=4.3,<5.0` — XGBoost is not substituted."
        )


def fit_lightgbm(
    train: pd.DataFrame,
    *,
    features: list[str],
    label: str,
    params: dict[str, Any],
    training_cutoff: str,
    random_seed: int,
    validation: pd.DataFrame | None = None,
    early_stopping_rounds: int | None = 20,
) -> tuple[Any, TrainOnlyPreprocessor, LightGBMFitResult]:
    _require_lgbm()
    # LightGBM needs no StandardScaler; still clip using train-only bounds.
    prep = TrainOnlyPreprocessor(features, scale=False)
    prep.fit(train, fit_cutoff=training_cutoff)
    x_train = pd.DataFrame(prep.transform(train), columns=features)
    y_train = pd.to_numeric(train[label], errors="coerce").to_numpy(dtype=float)

    hyper = {
        "objective": "regression",
        "metric": "l2",
        "verbosity": -1,
        "force_col_wise": True,
        "n_jobs": 1,
        "seed": int(random_seed),
        "feature_fraction_seed": int(random_seed),
        "bagging_seed": int(random_seed),
        "deterministic": True,
        "num_leaves": int(params.get("num_leaves", 15)),
        "learning_rate": float(params.get("learning_rate", 0.05)),
        "n_estimators": int(params.get("n_estimators", 80)),
        "max_depth": int(params.get("max_depth", 4)),
        "min_child_samples": int(params.get("min_child_samples", 10)),
        "subsample": float(params.get("subsample", 1.0)),
        "colsample_bytree": float(params.get("colsample_bytree", 1.0)),
    }
    model = lgb.LGBMRegressor(**hyper)
    fit_kwargs: dict[str, Any] = {}
    best_iteration: int | None = None
    if validation is not None and early_stopping_rounds:
        x_val = pd.DataFrame(prep.transform(validation), columns=features)
        y_val = pd.to_numeric(validation[label], errors="coerce").to_numpy(dtype=float)
        fit_kwargs["eval_set"] = [(x_val, y_val)]
        fit_kwargs["callbacks"] = [
            lgb.early_stopping(int(early_stopping_rounds), verbose=False),
            lgb.log_evaluation(period=0),
        ]
    model.fit(x_train, y_train, **fit_kwargs)
    if hasattr(model, "best_iteration_") and model.best_iteration_ is not None:
        best_iteration = int(model.best_iteration_)
    result = LightGBMFitResult(
        hyperparameters=hyper,
        feature_order=list(features),
        preprocessing=prep.artifacts().to_dict(),
        training_cutoff=training_cutoff,
        random_seed=int(random_seed),
        best_iteration=best_iteration,
        library_version=LIGHTGBM_VERSION,
    )
    return model, prep, result


def predict_lightgbm(model: Any, prep: TrainOnlyPreprocessor, frame: pd.DataFrame) -> np.ndarray:
    x = pd.DataFrame(prep.transform(frame), columns=prep.features)
    return np.asarray(model.predict(x), dtype=float)


def select_lightgbm_config(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    features: list[str],
    label: str,
    grid: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    training_cutoff: str,
    random_seed: int,
    score_fn,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require_lgbm()
    configs = list(grid) if grid else list(DEFAULT_LGBM_GRID)
    candidates: list[dict[str, Any]] = []
    best_params: dict[str, Any] | None = None
    best_key: tuple | None = None
    for params in configs:
        model, prep, _meta = fit_lightgbm(
            train,
            features=features,
            label=label,
            params=params,
            training_cutoff=training_cutoff,
            random_seed=random_seed,
            validation=validation,
            early_stopping_rounds=20,
        )
        preds = predict_lightgbm(model, prep, validation)
        metrics = score_fn(preds, validation)
        entry = {"hyperparameters": dict(params), "validation_metrics": metrics}
        candidates.append(entry)
        key = _selection_key(metrics, complexity_rank=1)
        if best_key is None or key > best_key:
            best_key = key
            best_params = dict(params)
    if best_params is None:
        best_params = dict(configs[0])
    return best_params, candidates
