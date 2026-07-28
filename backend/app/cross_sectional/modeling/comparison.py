"""Descriptive model comparison (evidence labels, not deployment approval)."""

from __future__ import annotations

from typing import Any

from app.cross_sectional.modeling.ridge import _selection_key


def compare_models(
    model_evals: dict[str, dict[str, Any]],
    *,
    validation_selection: dict[str, dict[str, Any]],
    common_dates: list[str] | None = None,
    coverage_by_model: dict[str, float] | None = None,
    label: str,
    universe_version: str,
    feature_version: str,
) -> dict[str, Any]:
    """
    Compare Ridge vs LightGBM (and optional factor notes).

    Evidence labels only: best_validation_ranker, best_oos_ranker,
    simplest_baseline, insufficient_evidence — not deployment approvals.
    """
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    coverages = coverage_by_model or {}
    if coverages:
        vals = list(coverages.values())
        if len(vals) >= 2 and max(vals) - min(vals) > 0.05:
            warnings.append(
                "Model coverage differs by more than 5%; RankIC comparisons "
                "may not share identical evaluation dates."
            )

    best_val_name: str | None = None
    best_val_key: tuple | None = None
    best_oos_name: str | None = None
    best_oos_key: tuple | None = None

    for name, oos in model_evals.items():
        val = validation_selection.get(name) or {}
        row = {
            "model": name,
            "validation_selection_metric": val.get("mean_rank_ic"),
            "out_of_sample_mean_rank_ic": oos.get("mean_rank_ic"),
            "median_rank_ic": oos.get("median_rank_ic"),
            "icir": oos.get("icir"),
            "positive_ic_ratio": oos.get("positive_ic_ratio"),
            "mae": oos.get("mae"),
            "rmse": oos.get("rmse"),
            "coverage": oos.get("prediction_coverage"),
            "prediction_dates": oos.get("prediction_date_count"),
            "complexity_note": "linear_ridge" if name == "ridge" else "lightgbm_trees",
            "limitations": [
                "Scores are not expected returns.",
                "No portfolio construction or transaction-cost evaluation.",
            ],
        }
        rows.append(row)

        vkey = _selection_key(
            {
                "mean_rank_ic": val.get("mean_rank_ic"),
                "median_rank_ic": val.get("median_rank_ic"),
                "positive_ic_ratio": val.get("positive_ic_ratio"),
                "mae": val.get("mae"),
            },
            complexity_rank=0 if name == "ridge" else 1,
        )
        if best_val_key is None or vkey > best_val_key:
            best_val_key = vkey
            best_val_name = name

        okey = _selection_key(
            {
                "mean_rank_ic": oos.get("mean_rank_ic"),
                "median_rank_ic": oos.get("median_rank_ic"),
                "positive_ic_ratio": oos.get("positive_ic_ratio"),
                "mae": oos.get("mae"),
            },
            complexity_rank=0 if name == "ridge" else 1,
        )
        if best_oos_key is None or okey > best_oos_key:
            best_oos_key = okey
            best_oos_name = name

    evidence_labels: list[str] = []
    if best_val_name and (validation_selection.get(best_val_name) or {}).get(
        "mean_rank_ic"
    ) is not None:
        evidence_labels.append(f"best_validation_ranker:{best_val_name}")
    else:
        evidence_labels.append("insufficient_evidence")
    if best_oos_name and (model_evals.get(best_oos_name) or {}).get(
        "mean_rank_ic"
    ) is not None:
        evidence_labels.append(f"best_oos_ranker:{best_oos_name}")
    evidence_labels.append("simplest_baseline:ridge")

    return {
        "models": rows,
        "evidence_labels": evidence_labels,
        "common_evaluation_dates": common_dates or [],
        "label": label,
        "universe_version": universe_version,
        "feature_version": feature_version,
        "warnings": warnings,
        "note": (
            "Evidence labels are descriptive only — not deployment approvals. "
            "Do not treat best_oos_ranker as production readiness."
        ),
    }
