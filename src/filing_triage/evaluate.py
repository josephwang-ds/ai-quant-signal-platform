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
                              k: int = 5) -> tuple[float, int, int]:
    """The product metric: of the k filings we surface each morning, how many mattered?

    Returns (mean precision, days counted, days available).

    **Only days with more than k filings are counted**, and that restriction is
    the whole correctness of this metric. When a session has k or fewer filings,
    the top k is every filing, the ranking cannot affect the result, and the
    figure collapses to "what fraction of that day was material" -- which a
    reversed model and a random model score identically. Those days do not
    measure ranking, and averaging them in inflates the result badly: a day with
    one filing that happened to matter contributes a precision of 1.0.

    A universe small enough that most days fall below k cannot support this
    metric at all, so the caller is told how many days actually qualified.
    """
    frame = predictions.assign(session=sessions.reindex(predictions.index).to_numpy())
    daily, available = [], 0
    for _, group in frame.groupby("session"):
        available += 1
        if len(group) <= k:
            continue
        daily.append(precision_at_k(group["label"].to_numpy(),
                                    group["score"].to_numpy(), k))
    if not daily:
        return float("nan"), 0, available
    return float(np.mean(daily)), len(daily), available


def mean_daily_random_precision_at_k(predictions: pd.DataFrame, sessions: pd.Series,
                                     k: int = 5) -> tuple[float, int, int]:
    """Expected precision of reading k random filings on the same eligible days.

    Within a session, the expected precision of a random sample is that session's
    material-event rate. Averaging those rates over the exact sessions counted by
    the model is deterministic and avoids comparing the model with a pooled base
    rate drawn from a different mix of thin and crowded days.
    """
    frame = predictions.assign(session=sessions.reindex(predictions.index).to_numpy())
    daily, available = [], 0
    for _, group in frame.groupby("session"):
        available += 1
        if len(group) <= k:
            continue
        daily.append(float(group["label"].mean()))
    if not daily:
        return float("nan"), 0, available
    return float(np.mean(daily)), len(daily), available


BASELINES = ("model", "random", "arrival", "item_202")


def daily_baseline_table(predictions: pd.DataFrame, events: pd.DataFrame,
                         k: int = 5) -> pd.DataFrame:
    """One row per eligible session: what each selection rule scored that day.

    The session is the unit of analysis everywhere downstream -- the aggregate
    below averages these rows, and the bootstrap resamples them. Both read the
    same table rather than each rebuilding it, because the day one of them
    silently counts a different set of sessions than the other is the day the
    comparison stops meaning anything.
    """
    metadata = events.set_index("event_id")[["entry_session", "acceptance_time", "items"]]
    frame = predictions.join(metadata, how="left")
    if frame[["entry_session", "acceptance_time"]].isna().any().any():
        raise ValueError("predictions contain event IDs missing from the event metadata")

    rows = []
    for session, group in frame.groupby("entry_session"):
        if len(group) <= k:
            continue
        labels = group["label"].to_numpy()

        arrival = group.sort_values("acceptance_time", kind="stable").head(k)
        item = group.assign(
            is_item_202=group["items"].fillna("").astype(str).str.contains(
                r"(?:^|,)\s*2\.02(?:,|$)", regex=True
            )
        ).sort_values(
            ["is_item_202", "acceptance_time"], ascending=[False, True], kind="stable"
        ).head(k)

        rows.append({
            "session": session,
            "filings": len(group),
            "material": int(labels.sum()),
            # What a perfect ranker would score here, which is not 1.0 and is
            # usually far from it: a session with one material filing caps
            # precision@5 at 0.2 however good the model is. Reported so the
            # model's number can be read against what was achievable rather
            # than against an unreachable 100%.
            "oracle": min(int(labels.sum()), k) / k,
            "model": precision_at_k(labels, group["score"].to_numpy(), k),
            # Within a session the expected precision of a random draw is that
            # session's own material rate -- exact, so no simulated draw needed.
            "random": float(group["label"].mean()),
            "arrival": float(arrival["label"].mean()),
            "item_202": float(item["label"].mean()),
        })
    return pd.DataFrame(
        rows, columns=["session", "filings", "material", "oracle", *BASELINES])


def operational_baselines(predictions: pd.DataFrame, events: pd.DataFrame,
                          k: int = 5) -> dict[str, float | int]:
    """Compare the model with workflows an analyst could actually use.

    All methods see the same out-of-sample events on the same sessions. Arrival
    order reads the first filings accepted. The item heuristic reads Item 2.02
    earnings filings first, then falls back to arrival order. Random is the exact
    expected precision within each eligible session rather than a simulated draw.
    """
    table = daily_baseline_table(predictions, events, k)
    sessions = len(table)
    if not sessions:
        return {f"operational_sessions_at_{k}": 0}

    model_precision = float(table["model"].mean())
    random_precision = float(table["random"].mean())
    arrival_precision = float(table["arrival"].mean())
    item_precision = float(table["item_202"].mean())
    oracle_precision = float(table["oracle"].mean())
    return {
        f"operational_sessions_at_{k}": sessions,
        f"daily_model_precision_at_{k}": model_precision,
        f"daily_random_precision_at_{k}": random_precision,
        f"daily_arrival_precision_at_{k}": arrival_precision,
        f"daily_item_202_precision_at_{k}": item_precision,
        f"daily_oracle_precision_at_{k}": oracle_precision,
        # Where the model sits between the floor and the ceiling, which is the
        # only reading of precision@k that survives changing k. The raw
        # precision falls as k grows and so does the ceiling, so the ratio moves
        # far less than either -- see `experiments.capacity_profile`.
        f"daily_span_captured_at_{k}": _ratio(
            model_precision - random_precision, oracle_precision - random_precision),
        f"daily_lift_vs_random_at_{k}": _ratio(model_precision, random_precision),
        f"daily_lift_vs_arrival_at_{k}": _ratio(model_precision, arrival_precision),
        f"daily_lift_vs_item_202_at_{k}": _ratio(model_precision, item_precision),
    }


def queue_sizes(predictions: pd.DataFrame, sessions: pd.Series) -> dict:
    """How crowded the daily queue actually is.

    Reported alongside the daily metrics so a reader can see immediately whether
    there was ever a triage decision to make. Ranking five filings out of two is
    not triage.
    """
    counts = (predictions.assign(session=sessions.reindex(predictions.index).to_numpy())
              .groupby("session").size())
    return {
        "sessions": len(counts),
        "filings_per_session_median": float(counts.median()),
        "filings_per_session_p90": float(counts.quantile(0.90)),
        "filings_per_session_max": int(counts.max()),
    }


def evaluate(predictions: pd.DataFrame, ks: tuple[int, ...] = DEFAULT_KS,
             sessions: pd.Series | None = None,
             events: pd.DataFrame | None = None) -> dict:
    """Headline metrics over all out-of-sample predictions."""
    labels = predictions["label"].to_numpy()
    scores = predictions["score"].to_numpy()

    metrics = {
        "n_events": len(labels),
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
        metrics.update(queue_sizes(predictions, sessions))
        for k in (3, 5, 10):
            precision, counted, available = mean_daily_precision_at_k(
                predictions, sessions, k)
            random_precision, random_counted, _ = mean_daily_random_precision_at_k(
                predictions, sessions, k)
            if random_counted != counted:
                raise RuntimeError("model and random baselines counted different sessions")
            metrics[f"daily_precision_at_{k}"] = precision
            metrics[f"daily_random_precision_at_{k}"] = random_precision
            metrics[f"daily_lift_at_{k}"] = _ratio(precision, random_precision)
            metrics[f"daily_sessions_at_{k}"] = counted
            # Below this the metric is measuring the calendar, not the ranker.
            metrics[f"daily_usable_at_{k}"] = bool(counted >= 30
                                                   and counted >= 0.1 * available)
    if events is not None:
        metrics.update(operational_baselines(predictions, events, k=5))
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


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator and np.isfinite(denominator) else float("nan")
