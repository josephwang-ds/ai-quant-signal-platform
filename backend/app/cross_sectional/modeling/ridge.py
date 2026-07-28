"""Ridge regression baseline with validation-only alpha selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from app.cross_sectional.modeling.constants import DEFAULT_RIDGE_ALPHAS, MODELING_IMPL_VERSION
from app.cross_sectional.modeling.preprocessing import TrainOnlyPreprocessor


@dataclass
class RidgeFitResult:
    alpha: float
    coefficients: list[float]
    intercept: float
    feature_order: list[str]
    preprocessing: dict[str, Any]
    training_cutoff: str
    model_name: str = "ridge"
    model_implementation_version: str = MODELING_IMPL_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_implementation_version": self.model_implementation_version,
            "alpha": self.alpha,
            "coefficients": self.coefficients,
            "intercept": self.intercept,
            "feature_order": self.feature_order,
            "preprocessing": self.preprocessing,
            "training_cutoff": self.training_cutoff,
            "complexity_note": "linear_ridge",
        }


def fit_ridge(
    train: pd.DataFrame,
    *,
    features: list[str],
    label: str,
    alpha: float,
    training_cutoff: str,
    clip_q_low: float = 0.01,
    clip_q_high: float = 0.99,
) -> tuple[Ridge, TrainOnlyPreprocessor, RidgeFitResult]:
    prep = TrainOnlyPreprocessor(
        features, clip_q_low=clip_q_low, clip_q_high=clip_q_high, scale=True
    )
    prep.fit(train, fit_cutoff=training_cutoff)
    x = prep.transform(train)
    y = pd.to_numeric(train[label], errors="coerce").to_numpy(dtype=float)
    model = Ridge(alpha=float(alpha))
    model.fit(x, y)
    result = RidgeFitResult(
        alpha=float(alpha),
        coefficients=[float(c) for c in model.coef_],
        intercept=float(model.intercept_),
        feature_order=list(features),
        preprocessing=prep.artifacts().to_dict(),
        training_cutoff=training_cutoff,
    )
    return model, prep, result


def predict_ridge(
    model: Ridge,
    prep: TrainOnlyPreprocessor,
    frame: pd.DataFrame,
) -> np.ndarray:
    x = prep.transform(frame)
    return np.asarray(model.predict(x), dtype=float)


def select_ridge_alpha(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    *,
    features: list[str],
    label: str,
    alphas: list[float] | tuple[float, ...],
    training_cutoff: str,
    score_fn,
) -> tuple[float, list[dict[str, Any]]]:
    """
    Fit each alpha on train; score on validation via score_fn(preds, val_df).

    Selection uses validation evidence only (no test).
    """
    candidates: list[dict[str, Any]] = []
    best_alpha: float | None = None
    best_key: tuple | None = None
    for alpha in alphas:
        model, prep, meta = fit_ridge(
            train,
            features=features,
            label=label,
            alpha=float(alpha),
            training_cutoff=training_cutoff,
        )
        preds = predict_ridge(model, prep, validation)
        metrics = score_fn(preds, validation)
        entry = {
            "alpha": float(alpha),
            "validation_metrics": metrics,
        }
        candidates.append(entry)
        key = _selection_key(metrics, complexity_rank=0)
        if best_key is None or key > best_key:
            best_key = key
            best_alpha = float(alpha)
    if best_alpha is None:
        best_alpha = float(alphas[0]) if alphas else float(DEFAULT_RIDGE_ALPHAS[0])
    return best_alpha, candidates


def _selection_key(metrics: dict[str, Any], *, complexity_rank: int) -> tuple:
    """
    Higher is better. Tie-break:
    1 mean RankIC  2 median RankIC  3 positive-IC ratio
    4 lower MAE (negated)  5 simpler model (higher when complexity_rank lower)
    """
    mean_ic = metrics.get("mean_rank_ic")
    median_ic = metrics.get("median_rank_ic")
    pos_ratio = metrics.get("positive_ic_ratio")
    mae = metrics.get("mae")
    return (
        mean_ic is not None,
        float(mean_ic) if mean_ic is not None else float("-inf"),
        float(median_ic) if median_ic is not None else float("-inf"),
        float(pos_ratio) if pos_ratio is not None else float("-inf"),
        -float(mae) if mae is not None else float("-inf"),
        -int(complexity_rank),
    )
