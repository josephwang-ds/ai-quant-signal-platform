"""Train-only feature preprocessing (scaler → optional reduce/select → model).

Fit exclusively on the training split; apply ``transform`` to OOS rows.
Never fit on the test set — that would leak evaluation labels/structure.
"""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectFromModel, SelectKBest, f_classif, f_regression
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.models.model_registry import build_estimator, feature_importance

PREPROCESSING_METHODS = ("none", "pca", "select_kbest", "l1_select")

DEFAULT_PCA_COMPONENTS = 5
DEFAULT_SELECT_K = 10


def resolve_pca_components(
    requested: Optional[int],
    *,
    n_features: int,
    n_samples: int,
) -> int:
    """Cap PCA components to a feasible train-set size."""
    upper = max(1, min(n_features, max(1, n_samples - 1)))
    if requested is None:
        return min(DEFAULT_PCA_COMPONENTS, upper)
    if requested < 1:
        raise ValueError("pca_components must be >= 1")
    return min(int(requested), upper)


def resolve_select_k(requested: Optional[int], *, n_features: int) -> int:
    if requested is None:
        return min(DEFAULT_SELECT_K, n_features)
    if requested < 1:
        raise ValueError("select_k must be >= 1")
    return min(int(requested), n_features)


def make_preprocessor(
    method: str,
    *,
    n_features: int,
    n_train_samples: int,
    pca_components: Optional[int] = None,
    select_k: Optional[int] = None,
    paradigm: str = "classifier",
) -> Any | None:
    cleaned = (method or "none").strip().lower()
    if cleaned not in PREPROCESSING_METHODS:
        raise ValueError(
            f'preprocessing must be one of {", ".join(PREPROCESSING_METHODS)}; got {method!r}'
        )
    if cleaned == "none":
        return None
    if cleaned == "pca":
        n_comp = resolve_pca_components(
            pca_components, n_features=n_features, n_samples=n_train_samples
        )
        return PCA(n_components=n_comp, random_state=42)
    if cleaned == "select_kbest":
        k = resolve_select_k(select_k, n_features=n_features)
        score_func = f_regression if paradigm == "regressor" else f_classif
        return SelectKBest(score_func=score_func, k=k)
    # l1_select — paradigm-matched sparse selector
    if paradigm == "regressor":
        return SelectFromModel(
            Lasso(alpha=0.0005, max_iter=4000, random_state=42)
        )
    return SelectFromModel(
        LogisticRegression(
            penalty="l1",
            solver="liblinear",
            max_iter=2000,
            random_state=42,
        )
    )


def build_model_pipeline(
    model_name: str,
    *,
    preprocessing: str = "none",
    n_features: int,
    n_train_samples: int,
    pca_components: Optional[int] = None,
    select_k: Optional[int] = None,
    paradigm: str = "classifier",
) -> Pipeline:
    """
    Build ``StandardScaler → [preprocess] → estimator``.

    The optional preprocess step is inserted after scaling and before the model.
    """
    steps: list[tuple[str, Any]] = [("scaler", StandardScaler())]
    preprocessor = make_preprocessor(
        preprocessing,
        n_features=n_features,
        n_train_samples=n_train_samples,
        pca_components=pca_components,
        select_k=select_k,
        paradigm=paradigm,
    )
    if preprocessor is not None:
        steps.append(("preprocess", preprocessor))
    steps.append(("clf", build_estimator(model_name)))
    return Pipeline(steps)


def resolve_feature_names_after_preprocess(
    pipeline: Pipeline,
    original_names: list[str],
) -> list[str]:
    """Names aligned with the classifier input after optional preprocess."""
    preprocess = pipeline.named_steps.get("preprocess")
    if preprocess is None:
        return list(original_names)
    if isinstance(preprocess, PCA):
        n = int(getattr(preprocess, "n_components_", preprocess.n_components))
        return [f"pc_{i + 1}" for i in range(n)]
    if hasattr(preprocess, "get_support"):
        mask = np.asarray(preprocess.get_support(), dtype=bool)
        return [name for name, keep in zip(original_names, mask) if keep]
    return list(original_names)


def extract_preprocessing_report(
    pipeline: Pipeline,
    original_names: list[str],
    method: str,
) -> dict[str, Any]:
    """Serialize fitted preprocess diagnostics for the API / UI."""
    cleaned = (method or "none").strip().lower()
    preprocess = pipeline.named_steps.get("preprocess")

    if cleaned == "none" or preprocess is None:
        return {"method": "none", "pca": None, "selection": None}

    if cleaned == "pca" and isinstance(preprocess, PCA):
        ratios = [float(x) for x in np.asarray(preprocess.explained_variance_ratio_)]
        cumulative = float(sum(ratios))
        return {
            "method": "pca",
            "pca": {
                "n_components": int(len(ratios)),
                "explained_variance_ratio": ratios,
                "cumulative": cumulative,
            },
            "selection": None,
        }

    if hasattr(preprocess, "get_support"):
        mask = np.asarray(preprocess.get_support(), dtype=bool)
        selected = [name for name, keep in zip(original_names, mask) if keep]
        dropped = [name for name, keep in zip(original_names, mask) if not keep]
        selection: dict[str, Any] = {
            "selected_features": selected,
            "dropped_features": dropped,
        }
        if hasattr(preprocess, "scores_"):
            scores = np.asarray(preprocess.scores_, dtype=float)
            selection["scores"] = {
                name: float(score)
                for name, score, keep in zip(original_names, scores, mask)
                if keep and np.isfinite(score)
            }
        return {
            "method": cleaned,
            "pca": None,
            "selection": selection,
        }

    return {"method": cleaned, "pca": None, "selection": None}


def merge_preprocessing_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-fold preprocess reports for walk-forward."""
    if not reports:
        return {"method": "none", "pca": None, "selection": None}

    method = str(reports[0].get("method") or "none")
    if method == "none":
        return {"method": "none", "pca": None, "selection": None}

    if method == "pca":
        ratio_lists = [
            list((r.get("pca") or {}).get("explained_variance_ratio") or [])
            for r in reports
            if r.get("pca")
        ]
        if not ratio_lists:
            return {"method": "pca", "pca": None, "selection": None}
        n = min(len(item) for item in ratio_lists)
        means = [
            float(sum(item[i] for item in ratio_lists) / len(ratio_lists))
            for i in range(n)
        ]
        return {
            "method": "pca",
            "pca": {
                "n_components": n,
                "explained_variance_ratio": means,
                "cumulative": float(sum(means)),
            },
            "selection": None,
        }

    selected_sets = [
        set((r.get("selection") or {}).get("selected_features") or [])
        for r in reports
        if r.get("selection")
    ]
    if not selected_sets:
        return {"method": method, "pca": None, "selection": None}
    selected = sorted(set.intersection(*selected_sets))
    all_names: set[str] = set()
    for r in reports:
        sel = r.get("selection") or {}
        all_names.update(sel.get("selected_features") or [])
        all_names.update(sel.get("dropped_features") or [])
    dropped = sorted(all_names - set(selected))
    return {
        "method": method,
        "pca": None,
        "selection": {
            "selected_features": selected,
            "dropped_features": dropped,
        },
    }


def importance_for_pipeline(
    pipeline: Pipeline,
    original_names: list[str],
) -> dict[str, float]:
    names = resolve_feature_names_after_preprocess(pipeline, original_names)
    return feature_importance(pipeline, names)
