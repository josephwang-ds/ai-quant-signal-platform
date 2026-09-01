"""Turning a model score into a probability someone can act on.

A gradient-boosted score between 0 and 1 is not a probability. It is monotone in
the right direction and nothing more: a filing scoring 0.64 does not react
unusually 64% of the time, and a recommendation rule written against raw scores
is a threshold on an arbitrary scale that moves whenever the model is retrained.
Calibration is what makes `0.64` mean *sixty-four in a hundred*, and without it
the reading policy downstream cannot be stated in language a reader can check.

**The calibrator gets its own slice of the past, and this is the trap.**

Fitting the calibrator on the same rows the model was fitted on teaches it to
correct scores the model has already memorised, so it learns a mapping that does
not apply to anything new -- and the reliability curve comes out beautiful. Fitting
it on the test fold is worse and more obvious. So each outer fold splits its own
training block in two, in time order: the earlier part fits the model, the later
part fits the calibrator, and the test fold sees neither. That costs training
data, which is the honest price of a probability that means what it says.

**Which calibrator is a measurement, not an assumption.** Isotonic is the usual
choice for tree ensembles -- it assumes only monotonicity, where a sigmoid assumes
one shape of distortion. It is also the one that made things worse here: on this
target a random forest's raw scores came out at 0.012 expected calibration error
and isotonic pushed them to 0.027. Averaging over trees is already a calibrating
operation, and fitting a flexible monotone map on a limited slice added more noise
than it removed.

So three methods are available and `calibration_comparison` scores all of them on
the same folds. `identity` -- ship the raw scores untouched -- is one of them, and
on this sample it wins. A calibration stage that is assumed rather than checked is
how a project ends up shipping a step function it never looked at.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from filing_triage.candidates import build
from filing_triage.guards import PurgedWalkForward
from filing_triage.model import CV_EMBARGO, N_SPLITS
from filing_triage.self_relative import assert_no_outcome_features

# How much of each training block is held back to fit the calibrator. A third is
# enough for isotonic regression not to degenerate into steps at these sizes,
# and leaves the model the majority of its data.
CALIBRATION_SHARE = 0.30
RELIABILITY_BINS = 10
CALIBRATION_METHODS = ("identity", "isotonic", "sigmoid")


@dataclass
class CalibratedResult:
    """Out-of-sample probabilities, plus what they were judged on."""

    predictions: pd.DataFrame
    metrics: dict = field(default_factory=dict)
    reliability: pd.DataFrame = field(default_factory=pd.DataFrame)


def _split_training_block(train: np.ndarray, share: float) -> tuple[np.ndarray, np.ndarray]:
    """Earlier part fits the model, later part fits the calibrator.

    In time order, never at random: a calibrator fitted on rows interleaved with
    the model's own training data is being asked to correct scores on filings the
    model has seen, which is the failure this split exists to avoid.
    """
    cut = int(len(train) * (1.0 - share))
    cut = max(1, min(cut, len(train) - 1))
    return train[:cut], train[cut:]


def expected_calibration_error(y: np.ndarray, p: np.ndarray,
                               bins: int = RELIABILITY_BINS) -> float:
    """Average gap between stated and observed frequency, weighted by bin size.

    Weighted, because an empty-ish bin at the top of the range would otherwise
    dominate a simple mean of per-bin errors -- and the top of the range is
    exactly where a recommendation threshold sits.
    """
    edges = np.linspace(0.0, 1.0, bins + 1)
    index = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    error = 0.0
    for b in range(bins):
        mask = index == b
        if not mask.any():
            continue
        error += mask.mean() * abs(float(p[mask].mean()) - float(y[mask].mean()))
    return float(error)


def reliability_curve(y: np.ndarray, p: np.ndarray,
                      bins: int = RELIABILITY_BINS) -> pd.DataFrame:
    """Stated probability against observed frequency, one row per bin.

    The count column is not decoration. A bin holding nine filings can sit far
    off the diagonal on noise alone, and a reliability plot drawn without it
    invites reading that wobble as miscalibration.
    """
    edges = np.linspace(0.0, 1.0, bins + 1)
    index = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    rows = []
    for b in range(bins):
        mask = index == b
        rows.append({
            "bin_low": edges[b],
            "bin_high": edges[b + 1],
            "count": int(mask.sum()),
            "mean_predicted": float(p[mask].mean()) if mask.any() else np.nan,
            "observed_rate": float(y[mask].mean()) if mask.any() else np.nan,
        })
    return pd.DataFrame(rows)


def _calibrate(method: str, calib_scores: np.ndarray, calib_y: np.ndarray,
               test_scores: np.ndarray) -> np.ndarray:
    """Map raw scores to probabilities, or decline to.

    `identity` is a first-class option rather than an absent one. A model whose
    raw scores are already well calibrated is made worse by a fitted map, and
    "we checked and left them alone" is a result the pipeline should be able to
    express.
    """
    if method == "identity":
        return test_scores
    if method == "isotonic":
        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        calibrator.fit(calib_scores, calib_y)
        return calibrator.predict(test_scores)
    if method == "sigmoid":
        calibrator = LogisticRegression(max_iter=1000)
        calibrator.fit(calib_scores.reshape(-1, 1), calib_y)
        return calibrator.predict_proba(test_scores.reshape(-1, 1))[:, 1]
    raise ValueError(f"unknown calibration method: {method!r}")


def calibrated_walk_forward(features: pd.DataFrame, target: pd.Series,
                            event_time: pd.Series, label_end_time: pd.Series,
                            estimator: str = "random_forest",
                            method: str = "identity",
                            n_splits: int = N_SPLITS,
                            calibration_share: float = CALIBRATION_SHARE,
                            ) -> CalibratedResult:
    """Score every event out of sample, with a probability fitted before it.

    Rows whose target is unknown -- an issuer without enough resolved history to
    have a threshold -- are dropped from fitting and from scoring rather than
    filled. They are not negatives, and a model taught that unknown means
    ordinary will call every new issuer ordinary.
    """
    # Checked here rather than trusted upstream: this is the last point before
    # the matrix becomes a numpy array and column names stop existing.
    assert_no_outcome_features(features.columns)

    usable = target.notna()
    features = features.loc[usable]
    y_all = target.loc[usable].to_numpy(dtype=int)
    event_time = event_time.loc[usable]
    label_end_time = label_end_time.loc[usable]

    X = features.to_numpy(dtype=float)
    probabilities = np.full(len(y_all), np.nan)
    raw_scores = np.full(len(y_all), np.nan)
    folds = np.full(len(y_all), -1)

    splitter = PurgedWalkForward(n_splits, CV_EMBARGO)
    for fold, (train, test) in enumerate(splitter.split(event_time, label_end_time)):
        fit_rows, calib_rows = _split_training_block(train, calibration_share)
        if len(np.unique(y_all[fit_rows])) < 2 or len(np.unique(y_all[calib_rows])) < 2:
            continue

        model = build(estimator).fit(X[fit_rows], y_all[fit_rows])
        test_scores = model.predict_proba(X[test])[:, 1]
        raw_scores[test] = test_scores
        probabilities[test] = _calibrate(
            method, model.predict_proba(X[calib_rows])[:, 1],
            y_all[calib_rows], test_scores)
        folds[test] = fold

    scored = np.isfinite(probabilities)
    predictions = pd.DataFrame(
        {"probability": probabilities[scored], "raw_score": raw_scores[scored],
         "fold": folds[scored], "label": y_all[scored]},
        index=features.index[scored],
    )
    if predictions.empty or predictions["label"].nunique() < 2:
        return CalibratedResult(predictions=predictions)

    y = predictions["label"].to_numpy()
    p = predictions["probability"].to_numpy()
    raw = predictions["raw_score"].to_numpy()
    metrics = {
        "n_scored": len(predictions),
        "base_rate": float(y.mean()),
        "pr_auc": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, p)),
        # The reference point that makes a Brier score readable: predicting the
        # base rate for everything. A model above this is worse than a constant.
        "brier_base_rate": float(brier_score_loss(y, np.full_like(p, y.mean()))),
        "ece": expected_calibration_error(y, p),
        "ece_uncalibrated": expected_calibration_error(y, raw),
        "calibration_share": calibration_share,
        "calibration_method": method,
        "estimator": estimator,
    }
    metrics["brier_skill"] = (
        1.0 - metrics["brier"] / metrics["brier_base_rate"]
        if metrics["brier_base_rate"] > 0 else float("nan"))
    return CalibratedResult(predictions=predictions, metrics=metrics,
                            reliability=reliability_curve(y, p))


def calibration_comparison(features: pd.DataFrame, target: pd.Series,
                           event_time: pd.Series, label_end_time: pd.Series,
                           estimator: str = "random_forest",
                           methods: tuple[str, ...] = CALIBRATION_METHODS,
                           ) -> pd.DataFrame:
    """Every calibration method on the same folds, so the choice has evidence.

    Discrimination is *not* identical across methods, and the reason is worth
    stating because the opposite is the natural assumption. Calibration is a
    monotone map, so within one fold it cannot reorder anything. These metrics
    are pooled across five folds, each with its own fitted calibrator, and five
    different monotone maps stitched together are not one monotone map: a filing
    from fold 1 and a filing from fold 4 can swap places. Isotonic also creates
    ties by flattening regions, which moves AUC on its own.

    So PR-AUC and ROC AUC are reported here as information rather than as a
    constant. The columns that decide are the Brier score and the calibration
    error.
    """
    rows = []
    for method in methods:
        result = calibrated_walk_forward(
            features, target, event_time, label_end_time,
            estimator=estimator, method=method)
        if not result.metrics:
            continue
        rows.append({
            "method": method,
            "brier": result.metrics["brier"],
            "brier_skill": result.metrics["brier_skill"],
            "ece": result.metrics["ece"],
            "pr_auc": result.metrics["pr_auc"],
            "roc_auc": result.metrics["roc_auc"],
            "n_scored": result.metrics["n_scored"],
        })
    return pd.DataFrame(rows)


def within_fold_monotonicity(result: CalibratedResult) -> pd.DataFrame:
    """Check that calibration preserved the ranking inside each fold.

    The property that must hold: a calibrator is monotone, so within the fold it
    was fitted for, sorting by raw score and sorting by probability must agree.
    Across folds it need not, because each fold has its own map -- which is why
    this is checked per fold rather than on the pooled column, and why the pooled
    AUC legitimately moves.

    A violation means a calibrator is not monotone, which for isotonic or a
    sigmoid means something is wrong with the fitting rather than with the data.
    """
    rows = []
    for fold, group in result.predictions.groupby("fold"):
        raw = group["raw_score"].to_numpy()
        prob = group["probability"].to_numpy()
        order = np.argsort(raw, kind="mergesort")
        rows.append({
            "fold": int(fold),
            "rows": len(group),
            "monotone": bool(np.all(np.diff(prob[order]) >= -1e-9)),
        })
    return pd.DataFrame(rows)
