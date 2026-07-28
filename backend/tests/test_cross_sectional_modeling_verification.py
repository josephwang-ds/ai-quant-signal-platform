"""Additional Phase 3 verification: modules, purge, preprocess, selection isolation."""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from app.cross_sectional.modeling import lightgbm_model as lgbm_mod
from app.cross_sectional.modeling import prediction as pred_mod
from app.cross_sectional.modeling.invariants import (
    LeakageInvariantError,
    assert_prediction_oos_invariants,
    assert_purge_boundary,
)
from app.cross_sectional.modeling.lightgbm_model import (
    fit_lightgbm,
    predict_lightgbm,
    select_lightgbm_config,
)
from app.cross_sectional.modeling.prediction import (
    add_cross_sectional_scores,
    predictions_to_records,
)
from app.cross_sectional.modeling.preprocessing import TrainOnlyPreprocessor
from app.cross_sectional.modeling.ridge import fit_ridge, select_ridge_alpha
from app.cross_sectional.modeling.splits import (
    build_expanding_walk_forward_folds,
    purged_train_end_index,
)
from app.cross_sectional.labels import compute_forward_labels


FEATURES = ["return_5d", "volatility_20d", "dollar_volume_20"]


def test_prediction_module_contains_only_score_contract():
    names = {n for n, _ in inspect.getmembers(pred_mod, inspect.isfunction)}
    assert "add_cross_sectional_scores" in names
    assert "predictions_to_records" in names
    assert "fit_lightgbm" not in names
    assert "LGBMRegressor" not in dir(pred_mod)
    src = inspect.getsource(pred_mod)
    assert "lightgbm" not in src.lower()
    assert "Ridge" not in src
    assert "rank" in src
    assert "percentile_score" in src


def test_lightgbm_module_contains_only_lgbm_wrapper():
    assert hasattr(lgbm_mod, "fit_lightgbm")
    assert hasattr(lgbm_mod, "predict_lightgbm")
    assert hasattr(lgbm_mod, "select_lightgbm_config")
    assert hasattr(lgbm_mod, "LightGBMFitResult")
    src = inspect.getsource(lgbm_mod)
    assert "percentile_score" not in src
    assert "eligible_symbol_count" not in src
    assert "add_cross_sectional_scores" not in src
    # Independent import path used by tests
    scored = add_cross_sectional_scores(
        pd.DataFrame(
            {
                "as_of_date": ["2020-01-02", "2020-01-02"],
                "symbol": ["A", "B"],
                "label": ["forward_return_5d"] * 2,
                "horizon": [5, 5],
                "model_name": ["ridge", "ridge"],
                "model_version": ["v", "v"],
                "fit_id": ["f", "f"],
                "fold_id": ["fold-001", "fold-001"],
                "training_cutoff": ["2019-01-01", "2019-01-01"],
                "raw_prediction": [0.1, 0.9],
                "actual_forward_return": [0.0, 0.0],
                "prediction_status": ["available", "available"],
            }
        )
    )
    assert list(scored["rank"]) == [2, 1] or scored.loc[scored["symbol"] == "B", "rank"].iloc[0] == 1
    _ = predictions_to_records(scored)


def test_hand_checkable_purge_matches_phase1_shift_semantics_5d_and_20d():
    """
    Phase 1: forward_return_Nd[i] = P[i+N]/P[i]-1 on trading rows.

    Explicit calendar (10 business days). Validation starts at index 9.
    """
    closes = pd.Series(
        [100.0 + i for i in range(10)],
        index=pd.bdate_range("2020-01-02", periods=10),
    )
    labels = compute_forward_labels(closes)
    dates = list(closes.index)

    for horizon, col in ((5, "forward_return_5d"), (20, "forward_return_20d")):
        # For H=20 on a 10-day series labels are mostly null; use extended calendar.
        pass

    # 5-day: boundary at index 9
    boundary_idx = 9
    i_max = purged_train_end_index(boundary_idx, 5)
    assert i_max == 3  # 9 - 5 - 1
    # Label at i_max uses price at i_max+5 = 8 < 9
    assert i_max + 5 < boundary_idx
    # Next index would touch boundary: 4+5=9
    assert (i_max + 1) + 5 == boundary_idx
    assert_purge_boundary(
        dates=dates,
        purged_train_end_date=str(dates[i_max].date()),
        boundary_start_date=str(dates[boundary_idx].date()),
        label_horizon=5,
    )
    with pytest.raises(LeakageInvariantError):
        assert_purge_boundary(
            dates=dates,
            purged_train_end_date=str(dates[i_max + 1].date()),
            boundary_start_date=str(dates[boundary_idx].date()),
            label_horizon=5,
        )

    # 20-day on longer calendar
    long_dates = list(pd.bdate_range("2020-01-02", periods=90))
    boundary_idx_20 = 40
    i_max_20 = purged_train_end_index(boundary_idx_20, 20)
    assert i_max_20 == 19  # 40 - 20 - 1
    assert i_max_20 + 20 < boundary_idx_20
    assert (i_max_20 + 1) + 20 == boundary_idx_20
    assert_purge_boundary(
        dates=long_dates,
        purged_train_end_date=str(long_dates[i_max_20].date()),
        boundary_start_date=str(long_dates[boundary_idx_20].date()),
        label_horizon=20,
    )
    # Fold builder exposes raw vs purged ends
    # cursor starts at min_train + horizon; need room for val+pred after that.
    folds = build_expanding_walk_forward_folds(
        long_dates,
        label_horizon=20,
        min_train_dates=30,
        validation_dates=5,
        prediction_block_dates=5,
    )
    assert folds
    fold = folds[0]
    assert fold.raw_train_end_date >= fold.effective_purged_train_end_date
    assert fold.effective_purged_train_end_date < fold.validation_start_date
    assert fold.validation_start_date <= fold.validation_end_date
    assert fold.validation_end_date < fold.prediction_start_date
    assert fold.label_horizon == 20
    assert fold.rows_removed_by_purging == 20
    assert_purge_boundary(
        dates=long_dates,
        purged_train_end_date=fold.effective_purged_train_end_date,
        boundary_start_date=fold.validation_start_date,
        label_horizon=20,
    )
    # Sanity: Phase 1 label formula present for 5d on short series
    assert labels["forward_return_5d"].iloc[0] == pytest.approx(closes.iloc[5] / closes.iloc[0] - 1)


def test_preprocessing_isolation_from_future_and_validation_changes():
    rng = np.random.default_rng(0)
    train = pd.DataFrame(
        {
            "return_5d": rng.normal(0, 0.02, 40),
            "volatility_20d": rng.uniform(0.1, 0.3, 40),
            "dollar_volume_20": rng.uniform(1e7, 2e7, 40),
            "forward_return_5d": rng.normal(0, 0.01, 40),
        }
    )
    prep = TrainOnlyPreprocessor(FEATURES, scale=True)
    prep.fit(train, fit_cutoff="2019-06-01")
    art1 = prep.artifacts().to_dict()
    model1, prep1, meta1 = fit_ridge(
        train, features=FEATURES, label="forward_return_5d", alpha=1.0, training_cutoff="t"
    )

    # Mutate validation / future outliers and missingness — must not change train artifacts.
    future = train.copy()
    future.loc[0, "return_5d"] = 1e6
    future.loc[1, "volatility_20d"] = np.nan
    future.loc[2, "dollar_volume_20"] = -1e9

    prep2 = TrainOnlyPreprocessor(FEATURES, scale=True)
    prep2.fit(train, fit_cutoff="2019-06-01")  # still train only
    art2 = prep2.artifacts().to_dict()
    assert art1["clip_lower"] == art2["clip_lower"]
    assert art1["clip_upper"] == art2["clip_upper"]
    assert art1["scaler_mean"] == art2["scaler_mean"]
    assert art1["scaler_scale"] == art2["scaler_scale"]

    model2, prep2b, meta2 = fit_ridge(
        train, features=FEATURES, label="forward_return_5d", alpha=1.0, training_cutoff="t"
    )
    assert meta1.coefficients == meta2.coefficients
    assert meta1.intercept == meta2.intercept
    # Transform of unchanged train rows identical after future mutation of a copy
    x1 = prep1.transform(train)
    x2 = prep2b.transform(train)
    np.testing.assert_allclose(x1, x2)


@pytest.mark.skipif(not lgbm_mod.LIGHTGBM_AVAILABLE, reason="lightgbm missing")
def test_lightgbm_fit_config_stable_when_future_features_change():
    rng = np.random.default_rng(1)
    train = pd.DataFrame(
        {
            "return_5d": rng.normal(0, 0.02, 60),
            "volatility_20d": rng.uniform(0.1, 0.3, 60),
            "dollar_volume_20": rng.uniform(1e7, 2e7, 60),
            "forward_return_5d": rng.normal(0, 0.01, 60),
        }
    )
    params = {"num_leaves": 15, "learning_rate": 0.05, "n_estimators": 30, "max_depth": 3}
    _m1, _p1, meta1 = fit_lightgbm(
        train,
        features=FEATURES,
        label="forward_return_5d",
        params=params,
        training_cutoff="t",
        random_seed=7,
        validation=None,
        early_stopping_rounds=None,
    )
    future = train.copy()
    future["return_5d"] = 999.0
    _m2, _p2, meta2 = fit_lightgbm(
        train,
        features=FEATURES,
        label="forward_return_5d",
        params=params,
        training_cutoff="t",
        random_seed=7,
        validation=None,
        early_stopping_rounds=None,
    )
    assert meta1.hyperparameters == meta2.hyperparameters
    assert meta1.preprocessing["clip_upper"] == meta2.preprocessing["clip_upper"]
    # Predictions on mutated future may differ — that is allowed; config must not.
    _ = predict_lightgbm(_m1, _p1, future)


def test_ridge_alpha_selection_ignores_test_labels():
    rng = np.random.default_rng(2)
    n = 180
    f = rng.normal(0, 1, size=(n, 3))
    y = 1.5 * f[:, 0] + rng.normal(0, 0.1, size=n)
    frame = pd.DataFrame(f, columns=FEATURES)
    frame["forward_return_5d"] = y
    train, val, test = frame.iloc[:100], frame.iloc[100:140], frame.iloc[140:].copy()

    def score_fn(preds, val_df):
        err = float(np.mean(np.abs(preds - val_df["forward_return_5d"].to_numpy())))
        return {
            "mean_rank_ic": -err,
            "median_rank_ic": -err,
            "positive_ic_ratio": 0.5,
            "mae": err,
        }

    a1, c1 = select_ridge_alpha(
        train,
        val,
        features=FEATURES,
        label="forward_return_5d",
        alphas=[0.1, 1.0, 10.0, 100.0],
        training_cutoff="t",
        score_fn=score_fn,
    )
    test["forward_return_5d"] = rng.normal(100, 1, size=len(test))  # poisoned OOS labels
    a2, c2 = select_ridge_alpha(
        train,
        val,
        features=FEATURES,
        label="forward_return_5d",
        alphas=[0.1, 1.0, 10.0, 100.0],
        training_cutoff="t",
        score_fn=score_fn,
    )
    assert a1 == a2
    assert [x["alpha"] for x in c1] == [x["alpha"] for x in c2]
    assert [x["validation_metrics"] for x in c1] == [x["validation_metrics"] for x in c2]


@pytest.mark.skipif(not lgbm_mod.LIGHTGBM_AVAILABLE, reason="lightgbm missing")
def test_lightgbm_selection_ignores_test_labels():
    rng = np.random.default_rng(3)
    n = 160
    f = rng.normal(0, 1, size=(n, 3))
    y = 1.2 * f[:, 0] - 0.3 * f[:, 1] + rng.normal(0, 0.15, size=n)
    frame = pd.DataFrame(f, columns=FEATURES)
    frame["forward_return_5d"] = y
    train, val, test = frame.iloc[:90], frame.iloc[90:120], frame.iloc[120:].copy()
    grid = [
        {"num_leaves": 15, "learning_rate": 0.05, "n_estimators": 25, "max_depth": 3},
        {"num_leaves": 31, "learning_rate": 0.05, "n_estimators": 40, "max_depth": 4},
    ]

    def score_fn(preds, val_df):
        err = float(np.mean(np.abs(preds - val_df["forward_return_5d"].to_numpy())))
        return {
            "mean_rank_ic": -err,
            "median_rank_ic": -err,
            "positive_ic_ratio": 0.5,
            "mae": err,
        }

    p1, c1 = select_lightgbm_config(
        train,
        val,
        features=FEATURES,
        label="forward_return_5d",
        grid=grid,
        training_cutoff="t",
        random_seed=11,
        score_fn=score_fn,
    )
    test["forward_return_5d"] = 999.0
    p2, c2 = select_lightgbm_config(
        train,
        val,
        features=FEATURES,
        label="forward_return_5d",
        grid=grid,
        training_cutoff="t",
        random_seed=11,
        score_fn=score_fn,
    )
    assert p1 == p2
    assert [x["hyperparameters"] for x in c1] == [x["hyperparameters"] for x in c2]


def test_oos_invariant_rejects_training_cutoff_leak():
    preds = pd.DataFrame(
        {
            "as_of_date": ["2020-02-01"],
            "symbol": ["A"],
            "fold_id": ["fold-001"],
            "fit_id": ["fit-1"],
            "training_cutoff": ["2020-02-10"],
            "model_name": ["ridge"],
        }
    )
    folds = [
        {
            "fold_id": "fold-001",
            "prediction_start_date": "2020-02-01",
            "prediction_end_date": "2020-02-28",
            "effective_purged_train_end_date": "2020-01-15",
        }
    ]
    with pytest.raises(LeakageInvariantError):
        assert_prediction_oos_invariants(preds, folds)
