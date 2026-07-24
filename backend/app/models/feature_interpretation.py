"""Feature Interpretation research — importance methods without changing predictions.

Computes diagnostic importances after a model is already fitted.
Does not alter signals, backtests, or training objectives.

Disclaimer (always surfaced to clients):
Feature importance does not imply causality.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

from app.models.model_registry import feature_importance
from app.models.preprocessing import resolve_feature_names_after_preprocess

CAUSALITY_DISCLAIMER = "Feature importance does not imply causality."

# Keep permutation cheap on the request path.
_PERMUTATION_REPEATS = 5
_SHAP_MAX_ROWS = 200
_STABILITY_CV_THRESHOLD = 0.75  # std/mean above → unstable
_STABILITY_RANK_STD_THRESHOLD = 2.5


def _estimator(pipeline: Any) -> Any:
    if isinstance(pipeline, Pipeline):
        return pipeline.named_steps.get("clf", pipeline)
    return pipeline


def _is_tree_estimator(estimator: Any) -> bool:
    return hasattr(estimator, "feature_importances_")


def _is_linear_estimator(estimator: Any) -> bool:
    return hasattr(estimator, "coef_") and not _is_tree_estimator(estimator)


def _normalize_abs(values: np.ndarray) -> np.ndarray:
    abs_v = np.abs(values.astype(float))
    total = float(abs_v.sum())
    if total <= 0 or not np.isfinite(total):
        return np.zeros_like(abs_v, dtype=float)
    return abs_v / total


def _dict_from_arrays(
    names: list[str], values: np.ndarray
) -> dict[str, float]:
    if len(names) != len(values):
        return {}
    return {name: float(v) for name, v in zip(names, values) if np.isfinite(v)}


def _ranking(values: dict[str, float], *, method: str) -> list[dict[str, Any]]:
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    return [
        {"rank": i + 1, "feature": name, "score": float(score), "method": method}
        for i, (name, score) in enumerate(ordered)
    ]


def coefficient_importance(
    pipeline: Any, original_names: list[str]
) -> dict[str, Any]:
    """Signed coefficients for linear models; unavailable otherwise."""
    names = resolve_feature_names_after_preprocess(pipeline, original_names)
    estimator = _estimator(pipeline)
    if not _is_linear_estimator(estimator):
        return {
            "available": False,
            "values": {},
            "signed": {},
            "note": "Coefficient importance applies to linear models only.",
        }
    coef = np.asarray(estimator.coef_, dtype=float)
    if coef.ndim == 2:
        # Multi-class: use class-0 vs rest mean signed effect carefully —
        # for binary classifiers sklearn stores shape (1, n).
        if coef.shape[0] == 1:
            coef = coef.ravel()
        else:
            coef = coef.mean(axis=0)
    else:
        coef = coef.ravel()
    if len(coef) != len(names):
        return {
            "available": False,
            "values": {},
            "signed": {},
            "note": "Coefficient length did not match feature names.",
        }
    abs_norm = _normalize_abs(coef)
    signed = {
        name: float(c) for name, c in zip(names, coef) if np.isfinite(c)
    }
    return {
        "available": True,
        "values": _dict_from_arrays(names, abs_norm),
        "signed": signed,
        "note": "Absolute coefficients normalised to sum to 1; signed values are raw coef_.",
    }


def permutation_importance_map(
    pipeline: Any,
    X: pd.DataFrame,
    y: pd.Series,
    original_names: list[str],
    *,
    paradigm: str,
) -> dict[str, Any]:
    """sklearn permutation importance on the held-out window (diagnostic only)."""
    if X.empty or len(X) < 5:
        return {
            "available": False,
            "values": {},
            "note": "Too few test rows for permutation importance.",
        }
    try:
        scoring = "r2" if paradigm == "regressor" else "accuracy"
        result = permutation_importance(
            pipeline,
            X,
            y,
            n_repeats=_PERMUTATION_REPEATS,
            random_state=42,
            scoring=scoring,
            n_jobs=1,
        )
    except Exception as exc:  # pragma: no cover - estimator-specific failures
        return {
            "available": False,
            "values": {},
            "note": f"Permutation importance unavailable: {exc}",
        }

    names = list(original_names)
    if len(result.importances_mean) != len(names):
        # After selection/PCA, map to resolved names when possible.
        names = resolve_feature_names_after_preprocess(pipeline, original_names)
        if len(result.importances_mean) != len(names):
            return {
                "available": False,
                "values": {},
                "note": "Permutation importance length did not match feature names.",
            }

    raw = np.maximum(result.importances_mean.astype(float), 0.0)
    values = _dict_from_arrays(names, _normalize_abs(raw))
    return {
        "available": bool(values),
        "values": values,
        "note": f"Permutation importance (n_repeats={_PERMUTATION_REPEATS}, scoring={scoring}).",
    }


def shap_importance_map(
    pipeline: Any,
    X: pd.DataFrame,
    original_names: list[str],
) -> dict[str, Any]:
    """Mean |SHAP| for tree models when the shap package is installed."""
    estimator = _estimator(pipeline)
    if not _is_tree_estimator(estimator):
        return {
            "available": False,
            "values": {},
            "note": "SHAP TreeExplainer applies to tree models only.",
        }
    try:
        import shap  # type: ignore
    except ImportError:
        return {
            "available": False,
            "values": {},
            "note": "SHAP package not installed; tree native importance still available.",
        }

    try:
        # Transform through preprocessing steps so TreeExplainer sees model input.
        Xt: Any = X
        names = list(original_names)
        if isinstance(pipeline, Pipeline):
            for step_name, step in pipeline.steps[:-1]:
                Xt = step.transform(Xt)
            names = resolve_feature_names_after_preprocess(pipeline, original_names)
        if hasattr(Xt, "toarray"):
            Xt = Xt.toarray()
        Xt = np.asarray(Xt, dtype=float)
        if Xt.ndim != 2 or Xt.shape[0] == 0:
            return {
                "available": False,
                "values": {},
                "note": "Empty matrix for SHAP.",
            }
        if Xt.shape[0] > _SHAP_MAX_ROWS:
            rng = np.random.RandomState(42)
            idx = rng.choice(Xt.shape[0], size=_SHAP_MAX_ROWS, replace=False)
            Xt = Xt[idx]

        explainer = shap.TreeExplainer(estimator)
        shap_values = explainer.shap_values(Xt)
        if isinstance(shap_values, list):
            # Multi-output / multi-class: average abs across outputs.
            stacked = np.stack([np.abs(np.asarray(sv, dtype=float)) for sv in shap_values], axis=0)
            mean_abs = stacked.mean(axis=(0, 1))
        else:
            arr = np.asarray(shap_values, dtype=float)
            if arr.ndim == 3:
                mean_abs = np.abs(arr).mean(axis=(0, 1))
            else:
                mean_abs = np.abs(arr).mean(axis=0)

        if len(mean_abs) != len(names):
            return {
                "available": False,
                "values": {},
                "note": "SHAP value length did not match feature names.",
            }
        values = _dict_from_arrays(names, _normalize_abs(mean_abs))
        return {
            "available": bool(values),
            "values": values,
            "note": "Mean absolute SHAP values (TreeExplainer), normalised.",
        }
    except Exception as exc:
        return {
            "available": False,
            "values": {},
            "note": f"SHAP unavailable: {exc}",
        }


def build_importance_research(
    pipeline: Any | None,
    *,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    original_names: list[str],
    paradigm: str,
    native_importance: dict[str, float],
) -> dict[str, Any]:
    """Assemble multi-method importance payload for one fitted model."""
    if pipeline is None or paradigm in {"timeseries", "offline_dl"}:
        return {
            "disclaimer": CAUSALITY_DISCLAIMER,
            "methods": {
                "native": {
                    "available": False,
                    "values": {},
                    "note": "Model does not expose tabular feature importance.",
                },
                "permutation": {"available": False, "values": {}, "note": "N/A"},
                "shap": {"available": False, "values": {}, "note": "N/A"},
                "coefficient": {"available": False, "values": {}, "signed": {}, "note": "N/A"},
            },
            "ranking": [],
            "stability": None,
            "limitations": [],
        }

    limitations: list[str] = []
    if isinstance(pipeline, Pipeline):
        preprocess = pipeline.named_steps.get("preprocess")
        if isinstance(preprocess, PCA):
            limitations.append(
                "PCA transforms original features into components (pc_*). "
                "Native/SHAP attributions are for components, not original market features."
            )
        elif preprocess is not None and hasattr(preprocess, "get_support"):
            limitations.append(
                "Feature selection dropped some inputs; importance covers selected features only."
            )

    native = {
        "available": bool(native_importance),
        "values": dict(native_importance),
        "note": "Tree feature_importances_ or normalised |coef_|.",
    }
    coefficient = coefficient_importance(pipeline, original_names)
    permutation = permutation_importance_map(
        pipeline, X_test, y_test, original_names, paradigm=paradigm
    )
    shap_map = shap_importance_map(pipeline, X_test, original_names)

    # Prefer permutation for ranking when available; else native; else coefficient.
    primary_method = "native"
    primary_values = native["values"]
    if permutation.get("available") and permutation.get("values"):
        primary_method = "permutation"
        primary_values = permutation["values"]  # type: ignore[assignment]
    elif native["available"] and native["values"]:
        primary_method = "native"
        primary_values = native["values"]
    elif coefficient.get("available") and coefficient.get("values"):
        primary_method = "coefficient"
        primary_values = coefficient["values"]  # type: ignore[assignment]

    return {
        "disclaimer": CAUSALITY_DISCLAIMER,
        "methods": {
            "native": native,
            "permutation": permutation,
            "shap": shap_map,
            "coefficient": coefficient,
        },
        "ranking": _ranking(primary_values, method=primary_method),
        "stability": None,
        "limitations": limitations,
    }


def compute_importance_stability(
    fold_importances: list[dict[str, float]],
) -> dict[str, Any]:
    """
    Compare importance magnitudes across OOS folds.

    consistent: low coefficient of variation and stable rank
    unstable: high CV or large rank swing across folds
    """
    if len(fold_importances) < 2:
        return {
            "available": False,
            "n_folds": len(fold_importances),
            "consistent_features": [],
            "unstable_features": [],
            "per_feature": {},
            "note": "Walk-forward with ≥2 folds is required for importance stability.",
            "disclaimer": CAUSALITY_DISCLAIMER,
        }

    keys: set[str] = set()
    for part in fold_importances:
        keys.update(part.keys())
    if not keys:
        return {
            "available": False,
            "n_folds": len(fold_importances),
            "consistent_features": [],
            "unstable_features": [],
            "per_feature": {},
            "note": "No fold importances available.",
            "disclaimer": CAUSALITY_DISCLAIMER,
        }

    # Rank each fold (1 = highest importance).
    fold_ranks: list[dict[str, float]] = []
    for part in fold_importances:
        ordered = sorted(part.items(), key=lambda item: item[1], reverse=True)
        ranks = {name: float(i + 1) for i, (name, _) in enumerate(ordered)}
        for key in keys:
            ranks.setdefault(key, float(len(keys)))
        fold_ranks.append(ranks)

    per_feature: dict[str, Any] = {}
    consistent: list[str] = []
    unstable: list[str] = []

    for key in sorted(keys):
        series = np.asarray(
            [float(part.get(key, 0.0)) for part in fold_importances], dtype=float
        )
        rank_series = np.asarray(
            [float(ranks.get(key, len(keys))) for ranks in fold_ranks], dtype=float
        )
        mean = float(series.mean())
        std = float(series.std(ddof=1)) if len(series) > 1 else 0.0
        cv = float(std / mean) if mean > 1e-12 else (float("inf") if std > 0 else 0.0)
        rank_mean = float(rank_series.mean())
        rank_std = float(rank_series.std(ddof=1)) if len(rank_series) > 1 else 0.0
        is_unstable = (np.isfinite(cv) and cv >= _STABILITY_CV_THRESHOLD) or (
            rank_std >= _STABILITY_RANK_STD_THRESHOLD
        )
        # "Consistently matters" = relatively high mean rank position and not unstable
        consistently_matters = (not is_unstable) and rank_mean <= max(3.0, len(keys) * 0.35)
        entry = {
            "mean": mean,
            "std": std,
            "cv": None if not np.isfinite(cv) else cv,
            "rank_mean": rank_mean,
            "rank_std": rank_std,
            "consistent": consistently_matters,
            "unstable": is_unstable,
        }
        per_feature[key] = entry
        if consistently_matters:
            consistent.append(key)
        if is_unstable:
            unstable.append(key)

    consistent.sort(
        key=lambda name: per_feature[name]["rank_mean"]
    )
    unstable.sort(
        key=lambda name: -(per_feature[name]["cv"] or 0.0)
    )

    return {
        "available": True,
        "n_folds": len(fold_importances),
        "consistent_features": consistent,
        "unstable_features": unstable,
        "per_feature": per_feature,
        "note": (
            "Consistent = relatively high mean rank with low fold-to-fold volatility. "
            "Unstable = high CV or large rank swings across OOS windows."
        ),
        "disclaimer": CAUSALITY_DISCLAIMER,
    }
