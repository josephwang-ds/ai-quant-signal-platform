"""Comparing model families without committing the one leak no guard can catch.

Choosing a model by looking at the out-of-sample metric is a selection leak
spanning the whole project. Every individual run is clean; the contamination
lives in which run was kept, and no per-row check can see it. The project already
refuses to answer this with a promise for the estimator's hyper-parameters -- it
answers with a sensitivity spread instead -- so a model comparison cannot arrive
and quietly reintroduce exactly that.

Two things are therefore reported, and they answer different questions.

`compare_candidates` scores each family on the ordinary purged walk-forward, with
a cluster-bootstrap interval on each. This is *descriptive*: it says how far
apart the families are, and whether they are distinguishable at all. If the
intervals overlap, picking the top row is chasing noise, and the honest reading
is that the choice does not matter.

`nested_selection_score` scores the *selection procedure*. Inside each outer
training block it runs its own purged split, picks the winner there, refits on
the full outer training block and predicts the outer test fold. No test fold ever
informs the choice made for it. The resulting number is what a reader would
actually get by running "try these, keep the best" -- which is almost always
below the best row of the descriptive table, and the gap between the two is the
selection premium the descriptive table would have handed you for free.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from filing_triage.candidates import CANDIDATES, build
from filing_triage.guards import PurgedWalkForward
from filing_triage.model import CV_EMBARGO, N_SPLITS
from filing_triage.uncertainty import bootstrap_ranking_metrics

INNER_SPLITS = 3


def _score_fold(pipeline, X, y, train, test) -> np.ndarray | None:
    """Fit on the training rows and score the test rows, or None if unlearnable."""
    if y[train].sum() == 0 or y[train].sum() == len(train):
        return None
    return build_and_predict(pipeline, X, y, train, test)


def build_and_predict(pipeline, X, y, train, test) -> np.ndarray:
    pipeline.fit(X[train], y[train])
    return pipeline.predict_proba(X[test])[:, 1]


def _oos_scores(name: str, X, y, event_time, label_end_time,
                n_splits: int = N_SPLITS) -> pd.DataFrame:
    """Out-of-sample scores for one candidate, on the ordinary walk-forward."""
    scores = np.full(len(y), np.nan)
    folds = np.full(len(y), -1)
    splitter = PurgedWalkForward(n_splits, CV_EMBARGO)
    for fold, (train, test) in enumerate(splitter.split(event_time, label_end_time)):
        predicted = _score_fold(build(name), X, y, train, test)
        if predicted is None:
            continue
        scores[test] = predicted
        folds[test] = fold
    return pd.DataFrame({"score": scores, "fold": folds, "label": y}).dropna(
        subset=["score"])


def compare_candidates(features: pd.DataFrame, labels: pd.Series,
                       event_time: pd.Series, label_end_time: pd.Series,
                       sessions: pd.Series | None = None,
                       names: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Each family on the same folds, with an interval on each.

    Descriptive, not a decision. The column worth reading first is the interval:
    two families whose intervals overlap are not distinguishable on this sample,
    and a table sorted by point estimate invites reading a ranking into noise
    that is not there.
    """
    X = features.to_numpy(dtype=float)
    y = labels.to_numpy(dtype=int)
    names = names or tuple(CANDIDATES)

    rows = []
    for name in names:
        predictions = _oos_scores(name, X, y, event_time, label_end_time)
        if predictions.empty or predictions["label"].nunique() < 2:
            continue
        predictions.index = features.index[predictions.index]
        row = {
            "candidate": name,
            "events_scored": len(predictions),
            "average_precision": average_precision_score(
                predictions["label"], predictions["score"]),
            "roc_auc": roc_auc_score(predictions["label"], predictions["score"]),
        }
        if sessions is not None:
            row.update(bootstrap_ranking_metrics(predictions, sessions))
        rows.append(row)
    return pd.DataFrame(rows)


def nested_selection_score(features: pd.DataFrame, labels: pd.Series,
                           event_time: pd.Series, label_end_time: pd.Series,
                           names: tuple[str, ...] | None = None,
                           n_splits: int = N_SPLITS,
                           inner_splits: int = INNER_SPLITS) -> dict:
    """What "try these and keep the best" is actually worth, measured honestly.

    The inner split runs entirely inside the outer training block and is purged
    and embargoed the same way, so the fold a model is judged on for a given
    outer test set never contains that test set. The outer score is therefore a
    score for the *procedure*, not for whichever family happened to win.

    `selected_per_fold` is reported because it is often the finding. A procedure
    that picks a different winner in every fold has not identified a better
    model; it has measured noise five times, and its nested score will sit near
    the middle of the descriptive table rather than at the top.
    """
    X = features.to_numpy(dtype=float)
    y = labels.to_numpy(dtype=int)
    names = names or tuple(CANDIDATES)

    scores = np.full(len(y), np.nan)
    chosen: list[str] = []
    outer = PurgedWalkForward(n_splits, CV_EMBARGO)

    for train, test in outer.split(event_time, label_end_time):
        inner_time = event_time.iloc[train]
        inner_end = label_end_time.iloc[train]
        inner = PurgedWalkForward(inner_splits, CV_EMBARGO)
        inner_folds = list(inner.split(inner_time, inner_end))
        if not inner_folds:
            continue

        best_name, best_score = None, -np.inf
        for name in names:
            fold_scores = []
            for inner_train, inner_test in inner_folds:
                # Positions are relative to the inner frame, so map back.
                tr, te = train[inner_train], train[inner_test]
                predicted = _score_fold(build(name), X, y, tr, te)
                if predicted is None or len(np.unique(y[te])) < 2:
                    continue
                fold_scores.append(average_precision_score(y[te], predicted))
            if fold_scores and np.mean(fold_scores) > best_score:
                best_name, best_score = name, float(np.mean(fold_scores))

        if best_name is None:
            continue
        predicted = _score_fold(build(best_name), X, y, train, test)
        if predicted is None:
            continue
        scores[test] = predicted
        chosen.append(best_name)

    measured = ~np.isnan(scores)
    if measured.sum() == 0 or len(np.unique(y[measured])) < 2:
        return {"selected_per_fold": chosen, "events_scored": int(measured.sum())}
    return {
        "selected_per_fold": chosen,
        "distinct_selections": len(set(chosen)),
        "events_scored": int(measured.sum()),
        "average_precision": float(
            average_precision_score(y[measured], scores[measured])),
        "roc_auc": float(roc_auc_score(y[measured], scores[measured])),
    }


def paired_candidate_differences(scored: dict[str, pd.DataFrame],
                                 sessions: pd.Series, *,
                                 reference: str,
                                 n_boot: int = 2000, seed: int = 7,
                                 alpha: float = 0.05) -> pd.DataFrame:
    """Each candidate against a reference, on one shared resample of sessions.

    The independent intervals in `compare_candidates` answer "how precisely is
    each family measured", which is not the question a reader asks of a
    comparison table. They ask whether one family is *better*, and two
    overlapping independent intervals do not settle that: the families saw the
    same events on the same days, so their difference is measured within a
    resample and is far better determined than either level.

    This is the same correction the operational baselines already get. Applying
    it to model families and not to baselines -- or the reverse -- would be the
    project criticising a mistake in one place while committing it in another.
    """
    rng = np.random.default_rng(seed)
    aligned = {}
    for name, frame in scored.items():
        joined = frame.assign(
            session=sessions.reindex(frame.index).to_numpy())
        aligned[name] = joined

    groups = {name: [g for _, g in frame.groupby("session", sort=True)]
              for name, frame in aligned.items()}
    n_groups = len(groups[reference])
    draws: dict[str, np.ndarray] = {name: np.full(n_boot, np.nan) for name in groups}

    for draw in range(n_boot):
        picked = rng.integers(0, n_groups, n_groups)
        for name, blocks in groups.items():
            sample = pd.concat([blocks[i] for i in picked], ignore_index=True)
            labels = sample["label"].to_numpy()
            if np.unique(labels).size < 2:
                continue
            draws[name][draw] = average_precision_score(
                labels, sample["score"].to_numpy())

    rows = []
    for name, values in draws.items():
        if name == reference:
            continue
        difference = values - draws[reference]
        finite = difference[np.isfinite(difference)]
        if finite.size == 0:
            continue
        rows.append({
            "candidate": name,
            "reference": reference,
            "average_precision": float(
                average_precision_score(aligned[name]["label"],
                                        aligned[name]["score"])),
            "difference": float(
                average_precision_score(aligned[name]["label"],
                                        aligned[name]["score"])
                - average_precision_score(aligned[reference]["label"],
                                          aligned[reference]["score"])),
            "difference_ci_low": float(np.percentile(finite, 100 * alpha / 2)),
            "difference_ci_high": float(np.percentile(finite, 100 * (1 - alpha / 2))),
            # The column that decides whether the ranking in the table is real.
            "draws_not_beating_reference": float(np.mean(finite <= 0)),
            "draws": int(finite.size),
        })
    return pd.DataFrame(rows)


def candidate_predictions(features: pd.DataFrame, labels: pd.Series,
                          event_time: pd.Series, label_end_time: pd.Series,
                          names: tuple[str, ...] | None = None,
                          ) -> dict[str, pd.DataFrame]:
    """Out-of-sample scores per candidate, keyed by event id for pairing."""
    X = features.to_numpy(dtype=float)
    y = labels.to_numpy(dtype=int)
    out = {}
    for name in names or tuple(CANDIDATES):
        predictions = _oos_scores(name, X, y, event_time, label_end_time)
        if predictions.empty:
            continue
        predictions.index = features.index[predictions.index]
        out[name] = predictions
    return out
