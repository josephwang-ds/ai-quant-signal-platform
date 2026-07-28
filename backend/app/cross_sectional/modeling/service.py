"""Phase 3 cross-sectional modeling orchestration."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd
import sklearn

from app.cross_sectional.constants import (
    MAX_REQUEST_SYMBOLS,
    UNIVERSE_ID_LIQUID_31,
)
from app.cross_sectional.dataset import (
    CrossSectionalDatasetError,
    CrossSectionalDatasetService,
    _as_jsonable,
)
from app.cross_sectional.modeling.comparison import compare_models
from app.cross_sectional.modeling.constants import (
    APPROVED_MODELS,
    DEFAULT_LGBM_GRID,
    DEFAULT_MIN_CROSS_SECTION_SIZE,
    DEFAULT_MIN_TRAIN_DATES,
    DEFAULT_PREDICTION_BLOCK_DATES,
    DEFAULT_PREDICTION_PREVIEW_LIMIT,
    DEFAULT_RANDOM_SEED,
    DEFAULT_RIDGE_ALPHAS,
    DEFAULT_SPLIT_MODE,
    DEFAULT_VALIDATION_DATES,
    FEATURE_VERSION,
    MAX_PREDICTION_PREVIEW_LIMIT,
    MODELING_FEATURE_COLUMNS,
    MODELING_IMPL_VERSION,
    MODELING_LABELS,
)
from app.cross_sectional.modeling.invariants import (
    LeakageInvariantError,
    assert_prediction_oos_invariants,
    assert_purge_boundary,
)
from app.cross_sectional.modeling.eligibility import (
    model_eligible_mask,
    summarize_eligibility,
)
from app.cross_sectional.modeling.evaluation import (
    evaluate_prediction_frame,
    score_predictions_for_selection,
)
from app.cross_sectional.modeling.lightgbm_model import (
    LIGHTGBM_AVAILABLE,
    LIGHTGBM_VERSION,
    LightGBMUnavailableError,
    fit_lightgbm,
    predict_lightgbm,
    select_lightgbm_config,
)
from app.cross_sectional.modeling.metadata import build_fit_metadata, make_fit_id
from app.cross_sectional.modeling.prediction import (
    add_cross_sectional_scores,
    predictions_to_records,
)
from app.cross_sectional.modeling.ridge import fit_ridge, predict_ridge, select_ridge_alpha
from app.cross_sectional.modeling.splits import (
    build_expanding_walk_forward_folds,
    collect_unique_dates,
    fold_masks,
    folds_as_dicts,
)
from app.cross_sectional.universe import configured_universe_version, universe_disclosures
from app.research_execution.market_data_port import MarketDataPort, utc_now_iso
from app.research_reproducibility import build_reproducibility_manifest
from app.research_validation.result_store import (
    InMemoryValidationResultStore,
    ValidationResultStore,
)

RESEARCH_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-_]{1,63}$")
EVIDENCE_KIND = "cross_sectional_modeling"
TEMPLATE_ID = "cross_sectional_factor"


class CrossSectionalModelingError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _bounded(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    return [{k: _as_jsonable(v) for k, v in row.items()} for row in rows[:limit]]


class CrossSectionalModelingService:
    """Train leakage-safe models and emit OOS daily stock scores (no portfolio)."""

    def __init__(
        self,
        market_data: MarketDataPort,
        result_store: ValidationResultStore | None = None,
        dataset_service: CrossSectionalDatasetService | None = None,
    ) -> None:
        store = result_store or InMemoryValidationResultStore()
        self._result_store = store
        self._dataset = dataset_service or CrossSectionalDatasetService(
            market_data, InMemoryValidationResultStore()
        )

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(
            payload.get("research_id") or "cross-sectional-modeling-v1"
        ).strip()
        if not RESEARCH_ID_PATTERN.match(research_id):
            raise CrossSectionalModelingError(
                "research_id must be 2–64 chars of lowercase letters, digits, -, _."
            )

        features = list(payload.get("feature_columns") or list(MODELING_FEATURE_COLUMNS))
        allowed_feat = set(MODELING_FEATURE_COLUMNS)
        bad_f = [f for f in features if f not in allowed_feat]
        if bad_f:
            raise CrossSectionalModelingError(
                f"Unsupported feature_columns: {bad_f}. Allowed: {sorted(allowed_feat)}"
            )
        if "liquidity_eligible" in features:
            raise CrossSectionalModelingError(
                "liquidity_eligible is an eligibility filter, not a model feature."
            )

        label = str(payload.get("label") or "forward_return_5d")
        if label not in MODELING_LABELS:
            raise CrossSectionalModelingError(
                f"Unsupported label: {label}. Allowed: {sorted(MODELING_LABELS)}"
            )
        label_horizon = int(MODELING_LABELS[label])
        extra_embargo = int(payload.get("embargo_rows") or 0)
        if extra_embargo < 0:
            raise CrossSectionalModelingError("embargo_rows must be >= 0.")
        # Purge uses trading-row label horizon + optional extra embargo rows.
        purge_horizon = label_horizon + extra_embargo
        horizon = label_horizon

        model_names = list(payload.get("model_names") or list(APPROVED_MODELS))
        bad_m = [m for m in model_names if m not in APPROVED_MODELS]
        if bad_m:
            raise CrossSectionalModelingError(
                f"Unsupported model_names: {bad_m}. Allowed: {list(APPROVED_MODELS)}"
            )
        if "lightgbm" in model_names and not LIGHTGBM_AVAILABLE:
            raise CrossSectionalModelingError(
                "LightGBM dependency is missing. Install lightgbm>=4.3,<5.0. "
                "XGBoost is not substituted.",
                status_code=500,
            )

        split_mode = str(payload.get("split_mode") or DEFAULT_SPLIT_MODE)
        if split_mode != DEFAULT_SPLIT_MODE:
            raise CrossSectionalModelingError(
                f"Unsupported split_mode: {split_mode}."
            )

        min_train = int(payload.get("minimum_train_dates", DEFAULT_MIN_TRAIN_DATES))
        val_window = int(payload.get("validation_window", DEFAULT_VALIDATION_DATES))
        pred_window = int(payload.get("prediction_window", DEFAULT_PREDICTION_BLOCK_DATES))
        min_cs = int(
            payload.get("minimum_cross_section_size", DEFAULT_MIN_CROSS_SECTION_SIZE)
        )
        apply_liq = bool(payload.get("apply_liquidity_filter", False))
        seed = int(payload.get("random_seed", DEFAULT_RANDOM_SEED))
        if seed < 0:
            raise CrossSectionalModelingError("random_seed must be >= 0.")
        preview_limit = int(
            payload.get("prediction_preview_limit", DEFAULT_PREDICTION_PREVIEW_LIMIT)
        )
        if preview_limit < 0 or preview_limit > MAX_PREDICTION_PREVIEW_LIMIT:
            raise CrossSectionalModelingError(
                f"prediction_preview_limit must be 0..{MAX_PREDICTION_PREVIEW_LIMIT}."
            )

        alphas = list(payload.get("ridge_alphas") or list(DEFAULT_RIDGE_ALPHAS))
        for a in alphas:
            if float(a) <= 0 or not np.isfinite(float(a)):
                raise CrossSectionalModelingError(f"Invalid ridge alpha: {a}")
        lgbm_grid = payload.get("lightgbm_parameters") or list(DEFAULT_LGBM_GRID)

        universe_id = str(
            payload.get("universe_id") or UNIVERSE_ID_LIQUID_31
        ).strip().lower()
        symbols_override = payload.get("symbols")
        if symbols_override is not None and len(symbols_override) > MAX_REQUEST_SYMBOLS:
            raise CrossSectionalModelingError(
                f"symbols must contain at most {MAX_REQUEST_SYMBOLS} tickers."
            )

        try:
            panel, dataset_meta = self._dataset.load_panel(
                {
                    "universe_id": universe_id,
                    "symbols": symbols_override,
                    "start_date": payload.get("start_date", "2019-01-01"),
                    "end_date": payload.get("end_date"),
                    "liquidity_dollar_volume_floor": payload.get(
                        "liquidity_dollar_volume_floor", 5_000_000.0
                    ),
                }
            )
        except CrossSectionalDatasetError as exc:
            raise CrossSectionalModelingError(exc.message, status_code=exc.status_code) from exc

        mask, reasons = model_eligible_mask(
            panel,
            features=features,
            label=label,
            apply_liquidity_filter=apply_liq,
        )
        eligible = panel.loc[mask].copy().sort_values(["date", "symbol"]).reset_index(drop=True)
        eligibility_summary = summarize_eligibility(panel, mask, reasons)

        dates = collect_unique_dates(eligible)
        folds = build_expanding_walk_forward_folds(
            dates,
            label_horizon=purge_horizon,
            min_train_dates=min_train,
            validation_dates=val_window,
            prediction_block_dates=pred_window,
        )
        if not folds:
            raise CrossSectionalModelingError(
                "Insufficient eligible dates for the requested walk-forward windows "
                f"(eligible_dates={len(dates)}, min_train={min_train}, "
                f"validation={val_window}, prediction={pred_window}, horizon={horizon})."
            )

        research_run_id = f"{research_id}-{utc_now_iso().replace(':', '').replace('-', '')}"
        universe_version = configured_universe_version(universe_id)
        warnings = list(universe_disclosures(universe_id))
        warnings.extend(dataset_meta.get("warnings") or [])

        all_pred_parts: list[pd.DataFrame] = []
        model_metadata: list[dict[str, Any]] = []
        preprocessing_metadata: list[dict[str, Any]] = []
        fold_summaries: list[dict[str, Any]] = []
        validation_by_model: dict[str, list[dict[str, Any]]] = {m: [] for m in model_names}
        fold_failures: list[dict[str, Any]] = []

        def _score_fn(preds: np.ndarray, val_df: pd.DataFrame) -> dict[str, Any]:
            return score_predictions_for_selection(
                preds,
                val_df,
                label=label,
                horizon=horizon,
                minimum_cross_section_size=min_cs,
            )

        for fold in folds:
            fold_dict = folds_as_dicts([fold])[0]
            masks = fold_masks(eligible["date"], fold)
            train_df = eligible.loc[masks["train"]]
            val_df = eligible.loc[masks["validation"]]
            pred_df = eligible.loc[masks["prediction"]]
            fold_info = {
                **fold_dict,
                "train_rows": int(len(train_df)),
                "validation_rows": int(len(val_df)),
                "prediction_rows": int(len(pred_df)),
            }
            # Thin cross-sections: still record fold; models may skip.
            if len(train_df) < min_cs or len(val_df) < min_cs:
                fold_info["status"] = "skipped_thin_split"
                fold_summaries.append(fold_info)
                fold_failures.append(
                    {
                        "fold_id": fold.fold_id,
                        "reason": "thin_train_or_validation",
                        "train_rows": int(len(train_df)),
                        "validation_rows": int(len(val_df)),
                    }
                )
                continue
            fold_info["status"] = "ok"
            fold_summaries.append(fold_info)
            training_cutoff = fold.effective_purged_train_end_date

            # Refit on history through prediction start, purged by label horizon.
            pred_start = pd.Timestamp(fold.prediction_start_date)
            try:
                pred_start_idx = dates.index(pred_start)
            except ValueError:
                pred_start_idx = next(
                    i for i, d in enumerate(dates) if d >= pred_start
                )
            from app.cross_sectional.modeling.splits import purged_train_end_index

            refit_max_idx = purged_train_end_index(pred_start_idx, purge_horizon)
            refit_cutoff = (
                str(dates[refit_max_idx].date()) if refit_max_idx >= 0 else training_cutoff
            )
            refit_mask = pd.to_datetime(eligible["date"]) <= pd.Timestamp(refit_cutoff)
            refit_df = eligible.loc[refit_mask]

            for model_name in model_names:
                try:
                    if model_name == "ridge":
                        best_alpha, candidates = select_ridge_alpha(
                            train_df,
                            val_df,
                            features=features,
                            label=label,
                            alphas=alphas,
                            training_cutoff=training_cutoff,
                            score_fn=_score_fn,
                        )
                        # Refit selected alpha on purged train∪val (no prediction rows).
                        model, prep, fit_meta = fit_ridge(
                            refit_df,
                            features=features,
                            label=label,
                            alpha=best_alpha,
                            training_cutoff=refit_cutoff,
                        )
                        raw = predict_ridge(model, prep, pred_df)
                        hyper = {"alpha": best_alpha, "alpha_candidates": alphas}
                        val_best = next(
                            (c for c in candidates if c["alpha"] == best_alpha),
                            candidates[0] if candidates else {},
                        )
                        validation_by_model[model_name].append(
                            val_best.get("validation_metrics") or {}
                        )
                        lib_versions = {
                            "sklearn": sklearn.__version__,
                            "lightgbm": LIGHTGBM_VERSION,
                        }
                    else:
                        best_params, candidates = select_lightgbm_config(
                            train_df,
                            val_df,
                            features=features,
                            label=label,
                            grid=lgbm_grid,
                            training_cutoff=training_cutoff,
                            random_seed=seed,
                            score_fn=_score_fn,
                        )
                        model, prep, fit_meta = fit_lightgbm(
                            refit_df,
                            features=features,
                            label=label,
                            params=best_params,
                            training_cutoff=refit_cutoff,
                            random_seed=seed,
                            validation=None,
                            early_stopping_rounds=None,
                        )
                        raw = predict_lightgbm(model, prep, pred_df)
                        hyper = dict(best_params)
                        val_best = next(
                            (
                                c
                                for c in candidates
                                if c.get("hyperparameters") == best_params
                            ),
                            candidates[0] if candidates else {},
                        )
                        validation_by_model[model_name].append(
                            val_best.get("validation_metrics") or {}
                        )
                        lib_versions = {
                            "sklearn": sklearn.__version__,
                            "lightgbm": LIGHTGBM_VERSION,
                        }

                    fit_id = make_fit_id(
                        research_run_id=research_run_id,
                        fold_id=fold.fold_id,
                        model_name=model_name,
                        training_cutoff=refit_cutoff,
                        label=label,
                    )
                    pred_part = pd.DataFrame(
                        {
                            "as_of_date": pd.to_datetime(pred_df["date"]).map(
                                lambda d: str(pd.Timestamp(d).date())
                            ),
                            "symbol": pred_df["symbol"].astype(str).to_numpy(),
                            "label": label,
                            "horizon": horizon,
                            "model_name": model_name,
                            "model_version": MODELING_IMPL_VERSION,
                            "fit_id": fit_id,
                            "fold_id": fold.fold_id,
                            "training_cutoff": refit_cutoff,
                            "raw_prediction": raw,
                            "actual_forward_return": pd.to_numeric(
                                pred_df[label], errors="coerce"
                            ).to_numpy(dtype=float),
                            "prediction_status": "available",
                        }
                    )
                    all_pred_parts.append(pred_part)
                    prep_dict = (
                        fit_meta.preprocessing
                        if hasattr(fit_meta, "preprocessing")
                        else fit_meta.to_dict().get("preprocessing", {})
                    )
                    preprocessing_metadata.append(
                        {
                            "fit_id": fit_id,
                            "fold_id": fold.fold_id,
                            "model_name": model_name,
                            **prep_dict,
                        }
                    )
                    meta = build_fit_metadata(
                        research_run_id=research_run_id,
                        fit_id=fit_id,
                        fold_id=fold.fold_id,
                        model_name=model_name,
                        selected_features=features,
                        label=label,
                        label_horizon=horizon,
                        universe_version=universe_version,
                        requested_symbols=list(
                            dataset_meta.get("requested_symbols")
                            or dataset_meta.get("symbols")
                            or []
                        ),
                        data_date_range={
                            "start": str(dates[0].date()) if dates else "",
                            "end": str(dates[-1].date()) if dates else "",
                        },
                        fold_summary={
                            **fold_dict,
                            "effective_purged_train_end_date": refit_cutoff,
                        },
                        preprocessing=prep_dict,
                        model_hyperparameters=hyper,
                        random_seed=seed,
                        library_versions=lib_versions,
                        row_counts={
                            "train": int(len(train_df)),
                            "validation": int(len(val_df)),
                            "refit": int(len(refit_df)),
                            "prediction": int(len(pred_df)),
                        },
                        date_counts={
                            "train": int(fold.train_date_count),
                            "validation": int(fold.validation_date_count),
                            "prediction": int(fold.prediction_date_count),
                        },
                        symbol_counts={
                            "train": int(train_df["symbol"].nunique()),
                            "validation": int(val_df["symbol"].nunique()),
                            "prediction": int(pred_df["symbol"].nunique()),
                        },
                        dataset_quality_summary=dataset_meta.get("quality"),
                    )
                    meta["fit_result"] = fit_meta.to_dict()
                    meta["selection_candidates"] = candidates
                    model_metadata.append(meta)
                except LightGBMUnavailableError as exc:
                    fold_failures.append(
                        {"fold_id": fold.fold_id, "model": model_name, "error": str(exc)}
                    )
                except Exception as exc:  # noqa: BLE001 — surface partial fold failure
                    fold_failures.append(
                        {
                            "fold_id": fold.fold_id,
                            "model": model_name,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

        if not all_pred_parts:
            raise CrossSectionalModelingError(
                "No out-of-sample predictions were produced. "
                f"Fold failures: {fold_failures[:5]}"
            )

        preds = add_cross_sectional_scores(pd.concat(all_pred_parts, ignore_index=True))
        try:
            assert_prediction_oos_invariants(preds, fold_summaries)
            for fold in folds:
                assert_purge_boundary(
                    dates=dates,
                    purged_train_end_date=fold.effective_purged_train_end_date,
                    boundary_start_date=fold.validation_start_date,
                    label_horizon=int(fold.label_horizon),
                )
                assert_purge_boundary(
                    dates=dates,
                    purged_train_end_date=fold.effective_purged_train_end_date,
                    boundary_start_date=fold.prediction_start_date,
                    label_horizon=int(fold.label_horizon),
                )
        except LeakageInvariantError as exc:
            raise CrossSectionalModelingError(
                f"Leakage invariant failure: {exc}", status_code=500
            ) from exc
        # Every prediction row must fall inside its fold prediction window.
        for fold in folds:
            fold_preds = preds.loc[preds["fold_id"] == fold.fold_id]
            if fold_preds.empty:
                continue
            too_early = fold_preds["as_of_date"].astype(str) < fold.prediction_start_date
            too_late = fold_preds["as_of_date"].astype(str) > fold.prediction_end_date
            if bool(too_early.any() or too_late.any()):
                raise CrossSectionalModelingError(
                    f"Internal error: predictions escaped fold window {fold.fold_id}."
                )

        oos_by_model: dict[str, dict[str, Any]] = {}
        daily_by_model: dict[str, list[dict[str, Any]]] = {}
        for model_name in model_names:
            sub = preds.loc[preds["model_name"] == model_name]
            daily, summary = evaluate_prediction_frame(
                sub, minimum_cross_section_size=min_cs
            )
            oos_by_model[model_name] = summary
            daily_by_model[model_name] = daily

        # Aggregate validation selection metrics (mean across folds).
        val_summary: dict[str, Any] = {}
        for model_name, metrics_list in validation_by_model.items():
            if not metrics_list:
                val_summary[model_name] = {
                    "mean_rank_ic": None,
                    "fold_count": 0,
                }
                continue
            means = [m.get("mean_rank_ic") for m in metrics_list if m.get("mean_rank_ic") is not None]
            medians = [
                m.get("median_rank_ic") for m in metrics_list if m.get("median_rank_ic") is not None
            ]
            pos = [
                m.get("positive_ic_ratio")
                for m in metrics_list
                if m.get("positive_ic_ratio") is not None
            ]
            maes = [m.get("mae") for m in metrics_list if m.get("mae") is not None]
            val_summary[model_name] = {
                "mean_rank_ic": float(np.mean(means)) if means else None,
                "median_rank_ic": float(np.mean(medians)) if medians else None,
                "positive_ic_ratio": float(np.mean(pos)) if pos else None,
                "mae": float(np.mean(maes)) if maes else None,
                "fold_count": len(metrics_list),
                "note": "Aggregated from validation folds only; test/OOS not used for selection.",
            }

        # Common OOS dates across models.
        date_sets = []
        for model_name, daily in daily_by_model.items():
            date_sets.append(
                {r["date"] for r in daily if r.get("status") == "available"}
            )
        common_dates = sorted(set.intersection(*date_sets)) if date_sets else []
        coverage = {
            m: float(oos_by_model[m].get("prediction_coverage") or 0.0) for m in model_names
        }
        comparison = compare_models(
            oos_by_model,
            validation_selection=val_summary,
            common_dates=common_dates,
            coverage_by_model=coverage,
            label=label,
            universe_version=universe_version,
            feature_version=FEATURE_VERSION,
        )
        warnings.extend(comparison.get("warnings") or [])
        if fold_failures:
            warnings.append(
                f"{len(fold_failures)} fold/model failure(s) recorded in unavailable_evidence."
            )

        preview_records = predictions_to_records(
            preds.sort_values(["as_of_date", "model_name", "rank", "symbol"])
        )
        limitations = [
            "Static research universe; survivorship and listing bias not corrected.",
            "Scores are model outputs, not guaranteed expected returns.",
            "No causal claims; multivariate RankIC is associative evidence only.",
            "No portfolio weights, Top-K selection, costs, or backtest in Phase 3.",
            "Artifacts are process-local in ValidationResultStore and lost on restart.",
            "Complete-case eligibility on selected features may shrink the sample.",
            "Configuration reproducible; deterministic under recorded environment; "
            "best-effort environment capture — not a byte-for-byte claim.",
        ]
        unavailable = [
            "portfolio_weights",
            "transaction_costs",
            "sharpe",
            "cagr",
            "drawdown",
            "full_prediction_history",
            "serialized_model_binaries",
        ]
        for fail in fold_failures:
            unavailable.append(
                f"fold_failure:{fail.get('fold_id')}:{fail.get('model')}:{fail.get('error') or fail.get('reason')}"
            )

        split_summary = {
            "split_mode": split_mode,
            "label_horizon": horizon,
            "purge_convention": (
                "train label window must end before validation/prediction start "
                "(trading-row index: i_max = start_idx - horizon - 1)"
            ),
            "eligible_dates": len(dates),
            "fold_count": len(folds),
            "folds_executed": sum(1 for f in fold_summaries if f.get("status") == "ok"),
            "rank_convention": (
                "Phase 3 rank 1 = highest model score; "
                "Phase 2 Q1 = lowest factor value — do not mix."
            ),
        }

        configuration = {
            "research_id": research_id,
            "universe_id": universe_id,
            "universe_version": universe_version,
            "feature_columns": features,
            "feature_version": FEATURE_VERSION,
            "label": label,
            "label_horizon": horizon,
            "model_names": model_names,
            "split_mode": split_mode,
            "minimum_train_dates": min_train,
            "validation_window": val_window,
            "prediction_window": pred_window,
            "minimum_cross_section_size": min_cs,
            "apply_liquidity_filter": apply_liq,
            "ridge_alphas": alphas,
            "random_seed": seed,
            "modeling_implementation_version": MODELING_IMPL_VERSION,
            "missing_data_policy": "complete_case_selected_features",
            "selection_metric": "mean_daily_prediction_RankIC",
            "selection_tie_break": [
                "mean_rank_ic",
                "median_rank_ic",
                "positive_ic_ratio",
                "lower_mae",
                "simpler_model",
            ],
        }

        artifact = {
            "research_run_id": research_run_id,
            "evidence_kind": EVIDENCE_KIND,
            "storage": "process_local_ValidationResultStore",
            "restart_loss": True,
            "includes": [
                "configuration",
                "fold_definitions",
                "preprocessing_metadata",
                "model_metadata",
                "prediction_summary",
                "bounded_prediction_preview",
                "evaluation_summary",
                "model_comparison",
                "limitations",
            ],
        }

        response = {
            "research_id": research_id,
            "template": TEMPLATE_ID,
            "evidence_kind": EVIDENCE_KIND,
            "research_run_id": research_run_id,
            "configuration": configuration,
            "dataset_summary": {
                "universe_version": universe_version,
                "row_count": int(len(panel)),
                "eligible_row_count": int(len(eligible)),
                "date_count": int(panel["date"].nunique()) if not panel.empty else 0,
                "symbol_count": int(panel["symbol"].nunique()) if not panel.empty else 0,
                "quality": dataset_meta.get("quality"),
            },
            "eligibility_summary": eligibility_summary,
            "split_summary": split_summary,
            "fold_summaries": fold_summaries,
            "model_metadata": [_as_jsonable(m) for m in model_metadata],
            "preprocessing_metadata": [_as_jsonable(p) for p in preprocessing_metadata],
            "validation_summary": val_summary,
            "out_of_sample_evaluation": {
                model: _as_jsonable(summary) for model, summary in oos_by_model.items()
            },
            "model_comparison": _as_jsonable(comparison),
            "bounded_prediction_preview": _bounded(preview_records, preview_limit),
            "unavailable_evidence": unavailable,
            "warnings": warnings,
            "limitations": limitations,
            "artifact_reference": artifact,
            "reproducibility": {
                **build_reproducibility_manifest(),
                "claim": (
                    "configuration reproducible; deterministic under recorded "
                    "environment; best-effort environment capture"
                ),
            },
        }

        # Persist bounded summary only (no model binaries, no full panel).
        stored_id = self._result_store.save(
            {
                "template": TEMPLATE_ID,
                "evidence_kind": EVIDENCE_KIND,
                "research_run_id": research_run_id,
                "configuration": configuration,
                "eligibility_summary": eligibility_summary,
                "split_summary": split_summary,
                "fold_summaries": fold_summaries,
                "validation_summary": val_summary,
                "out_of_sample_evaluation": response["out_of_sample_evaluation"],
                "model_comparison": response["model_comparison"],
                "bounded_prediction_preview": response["bounded_prediction_preview"],
                "limitations": limitations,
                "created_at": utc_now_iso(),
            }
        )
        response["artifact_reference"]["validation_run_id"] = stored_id
        response["research_run_id"] = stored_id
        return response
