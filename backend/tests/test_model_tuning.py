"""Train-set TimeSeriesSplit tuning guards."""

from __future__ import annotations

from app.models.model_comparison import TUNE_INTERPRETATION, run_model_comparison
from app.models.model_tuning import fit_with_optional_tune, tune_param_space
from app.models.preprocessing import build_model_pipeline
from tests.test_model_comparison import _synthetic_price_frame


def test_tune_param_space_covers_online_models() -> None:
    for name in ("logistic_l2", "random_forest", "ridge_reg", "svm"):
        assert tune_param_space(name) is not None
    assert tune_param_space("arima") is None
    assert tune_param_space("lstm") is None


def test_fit_with_optional_tune_returns_best_params() -> None:
    from app.models.features import FEATURE_COLUMNS, build_feature_frame

    X, y, aligned = build_feature_frame(_synthetic_price_frame(periods=400))
    n = len(X) // 2
    X_train = X.iloc[:n]
    y_train = y.iloc[:n]
    pipe = build_model_pipeline(
        "logistic_l2",
        preprocessing="none",
        n_features=len(FEATURE_COLUMNS),
        n_train_samples=len(X_train),
    )
    fitted, best = fit_with_optional_tune(
        pipe,
        model_name="logistic_l2",
        X_train=X_train,
        y_train=y_train,
        tune=True,
        paradigm="classifier",
        n_iter=4,
        n_splits=3,
    )
    assert fitted is not None
    assert isinstance(best, dict)
    assert "C" in best


def test_run_model_comparison_tune_exposes_best_params_and_note() -> None:
    out = run_model_comparison(
        _synthetic_price_frame(periods=700),
        split_date="2021-01-01",
        transaction_cost=0.001,
        short_window=20,
        long_window=60,
        momentum_window=60,
        models=["logistic_l2"],
        tune=True,
    )
    assert out["tune"] is True
    assert TUNE_INTERPRETATION in out["interpretation"]
    ml = next(row for row in out["results"] if row["strategy"] == "logistic_l2")
    assert ml.get("tuned") is True
    assert isinstance(ml.get("best_params"), dict)
    assert "C" in ml["best_params"]
