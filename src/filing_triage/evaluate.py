"""Ranking metrics.

The product is a queue: an analyst reads down it until they run out of morning.
So the question is never "what fraction of filings did we classify correctly" --
answering "none of them are material" scores 90% and is worth nothing. The
question is how much of the day's real news is sitting in the top handful.

  precision@k   of the k filings we put at the top, how many actually mattered
  lift@k        how much better than reading k at random
  recall@k      how much of the day's material news those k filings captured
  NDCG@k        the same, but rewarding a good ordering within the top k
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

DEFAULT_KS = (5, 10, 20, 50)


def precision_at_k(labels: np.ndarray, scores: np.ndarray, k: int) -> float:
    k = min(k, len(labels))
    if k == 0:
        return float("nan")
    top = np.argsort(-scores, kind="stable")[:k]
    return float(labels[top].mean())


def recall_at_k(labels: np.ndarray, scores: np.ndarray, k: int) -> float:
    positives = labels.sum()
    if positives == 0:
        return float("nan")
    k = min(k, len(labels))
    top = np.argsort(-scores, kind="stable")[:k]
    return float(labels[top].sum() / positives)


def lift_at_k(labels: np.ndarray, scores: np.ndarray, k: int) -> float:
    base = labels.mean()
    if base == 0:
        return float("nan")
    return precision_at_k(labels, scores, k) / base


def ndcg_at_k(labels: np.ndarray, scores: np.ndarray, k: int) -> float:
    k = min(k, len(labels))
    if k == 0:
        return float("nan")
    discount = 1.0 / np.log2(np.arange(2, k + 2))
    actual = labels[np.argsort(-scores, kind="stable")[:k]]
    ideal = np.sort(labels)[::-1][:k]
    best = float((ideal * discount).sum())
    return float((actual * discount).sum() / best) if best > 0 else float("nan")


def mean_daily_precision_at_k(predictions: pd.DataFrame, sessions: pd.Series,
                              k: int = 5) -> float:
    """The product metric: of the k filings we surface each morning, how many mattered?

    Pooled precision@k over the whole sample answers a question nobody has -- it
    ranks three years of filings against each other and reads the global top ten.
    An analyst ranks *today's* filings and reads today's top few. Averaging the
    daily figure is both what the product does and far less jumpy, since it
    averages hundreds of small samples instead of reporting one.
    """
    frame = predictions.assign(session=sessions.reindex(predictions.index).to_numpy())
    daily = []
    for _, group in frame.groupby("session"):
        if group["label"].sum() == 0 and len(group) < k:
            continue
        daily.append(precision_at_k(group["label"].to_numpy(),
                                    group["score"].to_numpy(), k))
    return float(np.mean(daily)) if daily else float("nan")


def mean_daily_lift_at_k(predictions: pd.DataFrame, sessions: pd.Series,
                         k: int = 5) -> float:
    base = predictions["label"].mean()
    if base == 0:
        return float("nan")
    return mean_daily_precision_at_k(predictions, sessions, k) / base


def evaluate(predictions: pd.DataFrame, ks: tuple[int, ...] = DEFAULT_KS,
             sessions: pd.Series | None = None) -> dict:
    """Headline metrics over all out-of-sample predictions."""
    labels = predictions["label"].to_numpy()
    scores = predictions["score"].to_numpy()

    metrics = {
        "n_events": int(len(labels)),
        "base_rate": float(labels.mean()),
        "roc_auc": _safe(roc_auc_score, labels, scores),
        "average_precision": _safe(average_precision_score, labels, scores),
    }
    for k in ks:
        metrics[f"precision_at_{k}"] = precision_at_k(labels, scores, k)
        metrics[f"recall_at_{k}"] = recall_at_k(labels, scores, k)
        metrics[f"lift_at_{k}"] = lift_at_k(labels, scores, k)
        metrics[f"ndcg_at_{k}"] = ndcg_at_k(labels, scores, k)

    if sessions is not None:
        for k in (3, 5, 10):
            metrics[f"daily_precision_at_{k}"] = mean_daily_precision_at_k(
                predictions, sessions, k)
            metrics[f"daily_lift_at_{k}"] = mean_daily_lift_at_k(
                predictions, sessions, k)
    return metrics


def evaluate_by_fold(predictions: pd.DataFrame, k: int = 50) -> pd.DataFrame:
    """Per-fold breakdown. A metric that only holds in one fold is not a result.

    Average precision leads here rather than precision@k. Each fold holds a few
    hundred events, and a top-10 slice of a few hundred is a handful of rows --
    it swings between 0.1 and 0.8 fold to fold on noise alone, which tells the
    reader nothing about stability, which is the only reason this table exists.

    Walk-forward folds are ordered in time, so this doubles as a decay check: if
    the ranker only works in the earliest fold, it has decayed.
    """
    rows = []
    for fold, group in predictions.groupby("fold"):
        labels = group["label"].to_numpy()
        scores = group["score"].to_numpy()
        rows.append({
            "fold": int(fold),
            "events": len(group),
            "base rate": float(labels.mean()),
            "avg precision": _safe(average_precision_score, labels, scores),
            "ROC AUC": _safe(roc_auc_score, labels, scores),
            f"lift@{k}": lift_at_k(labels, scores, k),
        })
    return pd.DataFrame(rows)


def daily_queue(predictions: pd.DataFrame, events: pd.DataFrame,
                top_n: int = 10) -> pd.DataFrame:
    """The deliverable: each session's filings, ranked, truncated to a readable queue.

    This is what the product actually emits -- the metrics above exist to say how
    much you should trust it.
    """
    joined = predictions.join(
        events.set_index("event_id")[["ticker", "entry_session", "items",
                                      "acceptance_time", "session_state"]],
        how="left")
    joined["rank"] = (joined.groupby("entry_session")["score"]
                      .rank(ascending=False, method="first"))
    return (joined[joined["rank"] <= top_n]
            .sort_values(["entry_session", "rank"])
            .reset_index()
            .rename(columns={"index": "event_id"}))


def _safe(fn, labels: np.ndarray, scores: np.ndarray) -> float:
    if len(np.unique(labels)) < 2:
        return float("nan")
    return float(fn(labels, scores))
