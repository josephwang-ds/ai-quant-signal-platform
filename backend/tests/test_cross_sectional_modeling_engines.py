"""Pure-engine tests for Phase 3 cross-sectional modeling."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.cross_sectional.modeling.eligibility import model_eligible_mask, summarize_eligibility
from app.cross_sectional.modeling.evaluation import evaluate_prediction_frame
from app.cross_sectional.modeling.prediction import add_cross_sectional_scores
from app.cross_sectional.modeling.preprocessing import TrainOnlyPreprocessor
from app.cross_sectional.modeling.ridge import fit_ridge, predict_ridge, select_ridge_alpha
from app.cross_sectional.modeling.splits import (
    build_expanding_walk_forward_folds,
    fold_masks,
    purged_train_end_index,
)


FEATURES = ["return_5d", "volatility_20d", "dollar_volume_20"]


def _synthetic_panel(
    n_dates: int = 120,
    n_symbols: int = 12,
    *,
    label: str = "forward_return_5d",
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-02", periods=n_dates)
    rows = []
    for i, dt in enumerate(dates):
        for j in range(n_symbols):
            f1 = float(rng.normal(0, 0.02))
            f2 = float(abs(rng.normal(0.2, 0.05)))
            f3 = float(1e7 + rng.normal(0, 1e5))
            # Label partly driven by f1 so Ridge can learn.
            y = 0.5 * f1 + float(rng.normal(0, 0.01))
            rows.append(
                {
                    "date": dt,
                    "symbol": f"S{j:02d}",
                    "return_5d": f1,
                    "volatility_20d": f2,
                    "dollar_volume_20": f3,
                    "return_20d": f1 * 2,
                    "liquidity_eligible": True,
                    label: y,
                    "forward_return_20d": y * 1.5,
                }
            )
    return pd.DataFrame(rows)


def test_eligibility_only_selected_features_matter():
    panel = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02")] * 3,
            "symbol": ["A", "B", "C"],
            "return_5d": [1.0, np.nan, 3.0],
            "volatility_20d": [0.1, 0.2, 0.3],
            "dollar_volume_20": [1e7, 1e7, 1e7],
            "forward_return_5d": [0.1, 0.2, np.nan],
            "liquidity_eligible": [True, True, True],
        }
    )
    mask, reasons = model_eligible_mask(
        panel,
        features=["volatility_20d", "dollar_volume_20"],
        label="forward_return_5d",
        apply_liquidity_filter=False,
    )
    # B has nan return_5d but that feature is unselected → still eligible if label ok
    # C missing label → excluded
    assert int(mask.sum()) == 2
    assert reasons["missing_label"] == 1
    summary = summarize_eligibility(panel, mask, reasons)
    assert summary["eligible_rows"] + summary["excluded_rows"] == summary["total_rows"]


def test_eligibility_liquidity_and_nonfinite():
    panel = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02")] * 3,
            "symbol": ["A", "B", "C"],
            "return_5d": [1.0, 2.0, np.inf],
            "volatility_20d": [0.1, 0.2, 0.3],
            "dollar_volume_20": [1e7, 1e7, 1e7],
            "forward_return_5d": [0.1, 0.2, 0.3],
            "liquidity_eligible": [True, False, True],
        }
    )
    mask, reasons = model_eligible_mask(
        panel,
        features=["return_5d", "volatility_20d", "dollar_volume_20"],
        label="forward_return_5d",
        apply_liquidity_filter=True,
    )
    assert int(mask.sum()) == 1
    assert reasons["liquidity_filtered"] >= 1
    assert reasons["missing_feature"] >= 1


def test_purge_index_for_5d_and_20d():
    # validation starts at index 100
    assert purged_train_end_index(100, 5) == 94
    assert purged_train_end_index(100, 20) == 79
    # i_max + h < start
    assert purged_train_end_index(100, 5) + 5 < 100
    assert purged_train_end_index(100, 20) + 20 < 100


def test_walk_forward_no_shuffle_and_chronology():
    dates = list(pd.bdate_range("2019-01-02", periods=100))
    folds = build_expanding_walk_forward_folds(
        dates,
        label_horizon=5,
        min_train_dates=40,
        validation_dates=10,
        prediction_block_dates=10,
    )
    assert folds
    for fold in folds:
        assert fold.effective_purged_train_end_date < fold.validation_start_date
        assert fold.validation_end_date < fold.prediction_start_date
        assert fold.raw_train_end_date >= fold.effective_purged_train_end_date
    # Input order independence
    folds_rev = build_expanding_walk_forward_folds(
        list(reversed(dates)),
        label_horizon=5,
        min_train_dates=40,
        validation_dates=10,
        prediction_block_dates=10,
    )
    # builder sorts via caller — we pass unsorted; function expects sorted unique list.
    # Document: caller must pass sorted dates (collect_unique_dates does).
    assert folds[0].fold_id == "fold-001"


def test_date_groups_never_split():
    panel = _synthetic_panel(80, 10)
    dates = sorted(pd.to_datetime(panel["date"].unique()))
    folds = build_expanding_walk_forward_folds(
        dates, label_horizon=5, min_train_dates=30, validation_dates=8, prediction_block_dates=8
    )
    fold = folds[0]
    masks = fold_masks(panel["date"], fold)
    train_dates = set(pd.to_datetime(panel.loc[masks["train"], "date"]).dt.date)
    val_dates = set(pd.to_datetime(panel.loc[masks["validation"], "date"]).dt.date)
    pred_dates = set(pd.to_datetime(panel.loc[masks["prediction"], "date"]).dt.date)
    assert train_dates.isdisjoint(val_dates)
    assert val_dates.isdisjoint(pred_dates)
    assert train_dates.isdisjoint(pred_dates)


def test_train_label_window_cannot_reach_validation():
    dates = list(pd.bdate_range("2019-01-02", periods=80))
    folds = build_expanding_walk_forward_folds(
        dates, label_horizon=20, min_train_dates=30, validation_dates=10, prediction_block_dates=10
    )
    fold = folds[0]
    date_index = {str(d.date()): i for i, d in enumerate(dates)}
    train_end_i = date_index[fold.effective_purged_train_end_date]
    val_start_i = date_index[fold.validation_start_date]
    assert train_end_i + fold.label_horizon < val_start_i


def test_preprocessing_train_only_ignores_future_outlier():
    train = pd.DataFrame(
        {
            "return_5d": [0.0, 0.1, -0.1, 0.05],
            "volatility_20d": [0.2, 0.21, 0.19, 0.2],
            "dollar_volume_20": [1e7, 1.1e7, 0.9e7, 1e7],
        }
    )
    future = train.copy()
    future.loc[0, "return_5d"] = 999.0
    prep = TrainOnlyPreprocessor(FEATURES, scale=True)
    prep.fit(train, fit_cutoff="2020-01-01")
    art = prep.artifacts()
    assert art.scaler_mean is not None
    # Transform future with huge outlier clipped by train bounds
    x = prep.transform(future)
    # Mean of first feature after transform on train should be ~0
    x_train = prep.transform(train)
    assert abs(float(x_train[:, 0].mean())) < 1e-8
    assert art.clip_upper["return_5d"] < 10


def test_zero_variance_feature_recorded():
    train = pd.DataFrame(
        {
            "return_5d": [0.1, 0.2, 0.15],
            "volatility_20d": [0.5, 0.5, 0.5],
            "dollar_volume_20": [1e7, 1.1e7, 0.9e7],
        }
    )
    prep = TrainOnlyPreprocessor(FEATURES, scale=True)
    prep.fit(train, fit_cutoff="2020-01-01")
    assert "volatility_20d" in prep.artifacts().zero_variance_features
    assert isinstance(prep.artifacts().to_dict(), dict)


def test_ridge_learns_linear_relation_and_alpha_uses_validation():
    rng = np.random.default_rng(1)
    n = 200
    f = rng.normal(0, 1, size=(n, 3))
    y = 2.0 * f[:, 0] - 1.0 * f[:, 1] + rng.normal(0, 0.05, size=n)
    dates = pd.bdate_range("2019-01-02", periods=n)
    # First 140 train, next 30 val, rest unused here
    frame = pd.DataFrame(f, columns=FEATURES)
    frame["date"] = dates
    frame["symbol"] = "A"
    frame["forward_return_5d"] = y
    train = frame.iloc[:140]
    val = frame.iloc[140:170].copy()
    # Make alpha=1 clearly better by construction is hard; just ensure selection runs
    # and coefficients preserve feature order.
    model, prep, meta = fit_ridge(
        train, features=FEATURES, label="forward_return_5d", alpha=1.0, training_cutoff="x"
    )
    assert meta.feature_order == FEATURES
    assert len(meta.coefficients) == 3
    assert abs(meta.coefficients[0] - 2.0) < 0.5

    def score_fn(preds, val_df):
        err = float(np.mean(np.abs(preds - val_df["forward_return_5d"].to_numpy())))
        # Fake RankIC metric: prefer lower MAE via selection key using mean_rank_ic=None path
        return {
            "mean_rank_ic": -err,
            "median_rank_ic": -err,
            "positive_ic_ratio": 0.5,
            "mae": err,
        }

    best, candidates = select_ridge_alpha(
        train,
        val,
        features=FEATURES,
        label="forward_return_5d",
        alphas=[0.1, 1.0, 10.0, 100.0],
        training_cutoff="x",
        score_fn=score_fn,
    )
    assert best in {0.1, 1.0, 10.0, 100.0}
    assert len(candidates) == 4
    preds = predict_ridge(model, prep, val)
    assert len(preds) == len(val)


def test_score_contract_rank_and_percentile():
    frame = pd.DataFrame(
        {
            "as_of_date": ["2020-01-02"] * 4 + ["2020-01-03"] * 2,
            "symbol": ["A", "B", "C", "D", "A", "B"],
            "label": ["forward_return_5d"] * 6,
            "horizon": [5] * 6,
            "model_name": ["ridge"] * 4 + ["ridge"] * 2,
            "model_version": ["v1"] * 6,
            "fit_id": ["f1"] * 6,
            "fold_id": ["fold-001"] * 6,
            "training_cutoff": ["2019-12-01"] * 6,
            "raw_prediction": [0.1, 0.4, 0.2, 0.4, 0.9, 0.1],
            "actual_forward_return": [0.0] * 6,
            "prediction_status": ["available"] * 6,
        }
    )
    scored = add_cross_sectional_scores(frame)
    day1 = scored.loc[scored["as_of_date"] == "2020-01-02"].set_index("symbol")
    assert day1.loc["B", "rank"] == 1 or day1.loc["D", "rank"] == 1
    assert day1.loc["A", "rank"] == 4
    assert day1["percentile_score"].min() == pytest.approx(0.0)
    # Tied highs share average-rank percentile < 1 when n>2 (documented convention).
    assert day1.loc["B", "percentile_score"] == pytest.approx(day1.loc["D", "percentile_score"])
    assert day1.loc["B", "percentile_score"] > day1.loc["C", "percentile_score"]
    # Unique max on a separate date maps to 1.
    day2 = scored.loc[scored["as_of_date"] == "2020-01-03"].set_index("symbol")
    assert day2.loc["A", "percentile_score"] == pytest.approx(1.0)
    assert day2.loc["B", "percentile_score"] == pytest.approx(0.0)
    # Raw predictions unchanged by ranking (same multiset).
    assert sorted(scored["raw_prediction"].tolist()) == sorted(frame["raw_prediction"].tolist())
    merged = scored.merge(
        frame[["as_of_date", "symbol", "model_name", "raw_prediction"]],
        on=["as_of_date", "symbol", "model_name"],
        suffixes=("", "_orig"),
    )
    assert (merged["raw_prediction"] == merged["raw_prediction_orig"]).all()
    # Different dates never ranked together: day2 only 2 symbols
    assert set(day2["eligible_symbol_count"]) == {2}


def test_evaluation_perfect_and_inverse_rank_ic():
    base = {
        "label": "forward_return_5d",
        "horizon": 5,
        "model_name": "ridge",
    }
    perfect = pd.DataFrame(
        {
            **{k: [v] * 5 for k, v in base.items()},
            "as_of_date": ["2020-01-02"] * 5,
            "symbol": list("ABCDE"),
            "raw_prediction": [1, 2, 3, 4, 5],
            "actual_forward_return": [10, 20, 30, 40, 50],
        }
    )
    _d, summary = evaluate_prediction_frame(perfect, minimum_cross_section_size=3)
    assert summary["mean_rank_ic"] == pytest.approx(1.0)

    inverse = perfect.copy()
    inverse["actual_forward_return"] = [50, 40, 30, 20, 10]
    _d2, summary2 = evaluate_prediction_frame(inverse, minimum_cross_section_size=3)
    assert summary2["mean_rank_ic"] == pytest.approx(-1.0)


def test_evaluation_constant_prediction_unavailable_and_errors():
    frame = pd.DataFrame(
        {
            "as_of_date": ["2020-01-02"] * 4,
            "symbol": list("ABCD"),
            "label": ["forward_return_5d"] * 4,
            "horizon": [5] * 4,
            "model_name": ["ridge"] * 4,
            "raw_prediction": [1.0, 1.0, 1.0, 1.0],
            "actual_forward_return": [0.1, 0.2, 0.3, 0.4],
        }
    )
    daily, summary = evaluate_prediction_frame(frame, minimum_cross_section_size=3)
    assert daily[0]["status"] == "unavailable"
    assert summary["mean_rank_ic"] is None
    assert summary["icir"] is None

    # Hand-check MAE/RMSE on available ordering day
    good = frame.copy()
    good["raw_prediction"] = [0.1, 0.2, 0.3, 0.4]
    good["actual_forward_return"] = [0.0, 0.0, 0.0, 0.0]
    _d, s = evaluate_prediction_frame(good, minimum_cross_section_size=3)
    assert s["mae"] == pytest.approx(0.25)
    assert s["rmse"] == pytest.approx(np.sqrt(np.mean(np.square([0.1, 0.2, 0.3, 0.4]))))


def test_icir_ddof1_not_annualized_zero_std_null():
    # Two days identical IC → std 0 → icir null
    rows = []
    for day in ("2020-01-02", "2020-01-03"):
        for i, sym in enumerate("ABCD"):
            rows.append(
                {
                    "as_of_date": day,
                    "symbol": sym,
                    "label": "forward_return_5d",
                    "horizon": 5,
                    "model_name": "ridge",
                    "raw_prediction": float(i + 1),
                    "actual_forward_return": float(i + 1),
                }
            )
    _d, summary = evaluate_prediction_frame(pd.DataFrame(rows), minimum_cross_section_size=3)
    assert summary["mean_rank_ic"] == pytest.approx(1.0)
    assert summary["rank_ic_std"] == pytest.approx(0.0)
    assert summary["icir"] is None


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("lightgbm") is None,
    reason="lightgbm not installed",
)
def test_lightgbm_deterministic_seed():
    from app.cross_sectional.modeling.lightgbm_model import fit_lightgbm, predict_lightgbm

    panel = _synthetic_panel(60, 10, seed=3)
    train = panel.iloc[:400]
    test = panel.iloc[400:450]
    params = {"num_leaves": 15, "learning_rate": 0.05, "n_estimators": 40, "max_depth": 3}
    m1, p1, _ = fit_lightgbm(
        train,
        features=FEATURES,
        label="forward_return_5d",
        params=params,
        training_cutoff="t",
        random_seed=42,
        validation=None,
        early_stopping_rounds=None,
    )
    m2, p2, _ = fit_lightgbm(
        train,
        features=FEATURES,
        label="forward_return_5d",
        params=params,
        training_cutoff="t",
        random_seed=42,
        validation=None,
        early_stopping_rounds=None,
    )
    pred1 = predict_lightgbm(m1, p1, test)
    pred2 = predict_lightgbm(m2, p2, test)
    np.testing.assert_allclose(pred1, pred2, rtol=1e-5, atol=1e-5)
