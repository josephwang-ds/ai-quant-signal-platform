"""The ranker.

A gradient-boosted classifier over the features, scored strictly out-of-sample.
The model is deliberately unremarkable -- swapping it for something fancier moves
the metric by a rounding error, while the validation scheme moves it by a lot.
That asymmetry is the point of the project, so the interesting code is the split,
not the estimator.

`config.purged_cv` selects between the two schemes:

  purged walk-forward   train only on events whose outcome windows closed before
                        the test fold opened, plus an embargo. Honest.
  shuffled K-fold       the default in every tutorial. Trains on the future and,
                        because outcome windows overlap, smuggles test-period
                        returns into training labels. Flattering and wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import KFold

from filing_triage.config import PipelineConfig
from filing_triage.guards import LeakageAudit, PurgedWalkForward

N_SPLITS = 5
CV_EMBARGO = timedelta(days=5)


@dataclass
class TriageModel:
    config: PipelineConfig
    n_splits: int = N_SPLITS
    random_state: int = 7
    oos_importance_: pd.DataFrame = field(default_factory=pd.DataFrame, init=False,
                                          repr=False)

    def _estimator(self) -> HistGradientBoostingClassifier:
        return HistGradientBoostingClassifier(
            max_depth=4,
            max_iter=200,
            learning_rate=0.06,
            min_samples_leaf=30,
            l2_regularization=1.0,
            random_state=self.random_state,
        )

    def fit_predict_oos(self, features: pd.DataFrame, labels: pd.Series,
                        event_time: pd.Series, label_end_time: pd.Series,
                        audit: LeakageAudit | None = None,
                        compute_importance: bool = False) -> pd.DataFrame:
        """Out-of-sample score for every event, from the fold that held it out."""
        X = features.to_numpy(dtype=float)
        y = labels.to_numpy(dtype=int)

        scores = np.full(len(y), np.nan)
        folds = np.full(len(y), -1)
        fold_importance = []

        for fold, (train, test) in enumerate(self._splits(event_time, label_end_time)):
            if y[train].sum() == 0 or y[train].sum() == len(train):
                continue      # a fold with one class cannot teach anything
            model = self._estimator().fit(X[train], y[train])
            scores[test] = model.predict_proba(X[test])[:, 1]
            folds[test] = fold

            if compute_importance and np.unique(y[test]).size > 1:
                importance = permutation_importance(
                    model,
                    features.iloc[test],
                    labels.iloc[test],
                    n_repeats=3,
                    random_state=self.random_state + fold,
                )
                importance["fold"] = fold
                fold_importance.append(importance)

            if audit is not None and self.config.purged_cv:
                audit.purged_split(
                    train_end=label_end_time.iloc[train],
                    test_start=event_time.iloc[test],
                    embargo=CV_EMBARGO,
                )

        self.oos_importance_ = _aggregate_importance(fold_importance)

        return pd.DataFrame(
            {"score": scores, "fold": folds, "label": y},
            index=features.index,
        ).dropna(subset=["score"])

    def _splits(self, event_time: pd.Series, label_end_time: pd.Series):
        if self.config.purged_cv:
            yield from PurgedWalkForward(self.n_splits, CV_EMBARGO).split(
                event_time, label_end_time)
        else:
            # The bug, on purpose: shuffling destroys the time ordering entirely.
            yield from KFold(self.n_splits, shuffle=True,
                             random_state=self.random_state).split(event_time)

    def fit_full(self, features: pd.DataFrame, labels: pd.Series):
        """Refit on everything, for scoring genuinely new filings."""
        return self._estimator().fit(features.to_numpy(dtype=float),
                                     labels.to_numpy(dtype=int))


def permutation_importance(model, features: pd.DataFrame, labels: pd.Series,
                           n_repeats: int = 5, random_state: int = 7) -> pd.DataFrame:
    """Which features the ranker actually leans on.

    Permutation rather than split-gain: gain is biased towards high-cardinality
    columns, and here the continuous features would beat the binary item flags
    for reasons that have nothing to do with usefulness.
    """
    from sklearn.inspection import permutation_importance as sk_permutation

    result = sk_permutation(
        model, features.to_numpy(dtype=float), labels.to_numpy(dtype=int),
        n_repeats=n_repeats, random_state=random_state, scoring="average_precision",
    )
    return (pd.DataFrame({
        "feature": features.columns,
        "importance": result.importances_mean,
        "std": result.importances_std,
    }).sort_values("importance", ascending=False).reset_index(drop=True))


def _aggregate_importance(folds: list[pd.DataFrame]) -> pd.DataFrame:
    """Average permutation importance measured only on held-out fold rows."""
    if not folds:
        return pd.DataFrame(columns=["feature", "importance", "std", "folds"])
    combined = pd.concat(folds, ignore_index=True)
    return (
        combined.groupby("feature", as_index=False)
        .agg(importance=("importance", "mean"), std=("importance", "std"),
             folds=("fold", "nunique"))
        .fillna({"std": 0.0})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
