"""Reproducibility metadata helpers for model fits."""

from __future__ import annotations

import hashlib
from typing import Any

from app.cross_sectional.modeling.constants import (
    FEATURE_VERSION,
    MODELING_IMPL_VERSION,
)
from app.research_reproducibility import build_reproducibility_manifest


def make_fit_id(
    *,
    research_run_id: str,
    fold_id: str,
    model_name: str,
    training_cutoff: str,
    label: str,
) -> str:
    raw = f"{research_run_id}|{fold_id}|{model_name}|{training_cutoff}|{label}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"fit-{model_name}-{fold_id}-{digest}"


def build_fit_metadata(
    *,
    research_run_id: str,
    fit_id: str,
    fold_id: str,
    model_name: str,
    selected_features: list[str],
    label: str,
    label_horizon: int,
    universe_version: str,
    requested_symbols: list[str],
    data_date_range: dict[str, str],
    fold_summary: dict[str, Any],
    preprocessing: dict[str, Any],
    model_hyperparameters: dict[str, Any],
    random_seed: int,
    library_versions: dict[str, str | None],
    row_counts: dict[str, int],
    date_counts: dict[str, int],
    symbol_counts: dict[str, int],
    dataset_quality_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    repro = build_reproducibility_manifest()
    return {
        "research_run_id": research_run_id,
        "fit_id": fit_id,
        "fold_id": fold_id,
        "model_name": model_name,
        "model_implementation_version": MODELING_IMPL_VERSION,
        "feature_version": FEATURE_VERSION,
        "selected_features": selected_features,
        "label": label,
        "label_horizon": label_horizon,
        "universe_version": universe_version,
        "requested_symbols": requested_symbols,
        "data_date_range": data_date_range,
        "raw_train_range": {
            "end": fold_summary.get("raw_train_end_date"),
        },
        "effective_purged_train_range": {
            "end": fold_summary.get("effective_purged_train_end_date"),
        },
        "validation_range": {
            "start": fold_summary.get("validation_start_date"),
            "end": fold_summary.get("validation_end_date"),
        },
        "prediction_range": {
            "start": fold_summary.get("prediction_start_date"),
            "end": fold_summary.get("prediction_end_date"),
        },
        "training_cutoff": fold_summary.get("effective_purged_train_end_date"),
        "preprocessing_configuration": preprocessing,
        "model_hyperparameters": model_hyperparameters,
        "random_seed": random_seed,
        "library_versions": library_versions,
        "row_counts": row_counts,
        "date_counts": date_counts,
        "symbol_counts": symbol_counts,
        "dataset_quality_summary": dataset_quality_summary,
        "reproducibility": {
            **repro,
            "claim": (
                "configuration reproducible; deterministic under recorded "
                "environment; best-effort environment capture"
            ),
        },
        "purge": {
            "label_horizon": fold_summary.get("label_horizon"),
            "purge_rows": fold_summary.get("purge_rows"),
            "rows_removed_by_purging": fold_summary.get("rows_removed_by_purging"),
        },
    }
