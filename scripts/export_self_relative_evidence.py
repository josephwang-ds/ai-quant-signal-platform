"""Evidence for the issuer-relative layer, exported the way the rest already is.

Everything the self-relative pages and cards display is generated from these
files, so a number can be traced from the screen back to an artifact and from
the artifact back to a run. Nothing here is written by hand.

The studies exist because the design has three settings that were assumed rather
than derived, and each gets an artifact rather than a promise: how much issuer
history is enough (`history_depth_sensitivity`), whether calibration helps at all
(`calibration_comparison`), and where the reading threshold belongs
(`recommendation_thresholds`).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from filing_triage import pipeline, recommend, text_model
from filing_triage.calibration import (
    calibrated_walk_forward,
    calibration_comparison,
    within_fold_monotonicity,
)
from filing_triage.config import PipelineConfig
from filing_triage.fingerprint import environment, input_fingerprints
from filing_triage.ingest.prices import load_prices
from filing_triage.ingest.universe import load_membership
from filing_triage.self_relative import (
    HistoryPolicy,
    attention_percentile,
    feature_frame,
    issuer_relative_target,
    self_relative_frame,
)
from filing_triage.uncertainty import paired_pr_auc_difference

SHIPPED_CALIBRATION = "identity"

# The four rows the expansion plan asks for. Each adds one family to the one
# above it, so a difference is attributable to that family rather than to a
# combination nobody isolated.
ABLATION_GROUPS = ("structured", "deterministic_text", "transformer_text", "all")


def build_inputs(events, prices, membership, profile):
    """One pipeline run, then everything the self-relative layer needs from it."""
    result = pipeline.run(events, prices, membership, PipelineConfig(),
                          issuer_profile=profile, compute_importance=False,
                          compute_uncertainty=False)
    relative = self_relative_frame(result.events, result.features, result.labels)
    target = issuer_relative_target(result.events, result.labels).reindex(
        result.features.index)

    features = result.features.join(feature_frame(relative))
    features["self_attention_pct"] = attention_percentile(relative)

    features = features.select_dtypes(include=[np.number])

    # Held *beside* the shipped matrix, never joined into it. The ablation below
    # measured these columns as worse than not having them -- a negative interval
    # that separates from zero -- and a feature that failed its own ablation must
    # not reach the model that writes the cards. Keeping them in a separate frame
    # makes that structural: the only code that can use them is the code that
    # measures them.
    #
    # Absent by default. Without the optional stack or a built cache the frame is
    # empty and the ablation reports one row instead of four, rather than
    # quietly filling the columns with zeros.
    text_columns = pd.DataFrame(index=features.index)
    cache_path = Path("data/build/text_cache")
    if text_model.available() and (cache_path / "index.json").exists():
        cache = text_model.TextCache(cache_path)
        text = text_model.text_features(result.events, cache)
        # Joined on event_id, never by position: the feature matrix and the
        # event frame are built by different code paths, and a row order that
        # happens to agree today is not a guarantee. Misalignment here would
        # attach one filing's tone to another filing's outcome.
        text_columns = text.set_index(result.events["event_id"]).reindex(
            features.index).select_dtypes(include=[np.number])

    aligned = result.labels.set_index("event_id").reindex(result.features.index)
    indexed = result.events.set_index("event_id")
    return {
        "result": result,
        "relative": relative,
        "target": target,
        "features": features,
        "text_features": text_columns,
        "event_time": indexed.loc[result.features.index, "acceptance_time"],
        "label_end_time": pd.to_datetime(
            aligned["label_end_session"]
        ).dt.tz_localize(result.events["acceptance_time"].dt.tz),
        "items": indexed.loc[result.features.index, "items"],
        "session": indexed.loc[result.features.index, "entry_session"],
    }


def history_depth_sensitivity(data, predictions) -> pd.DataFrame:
    """Does the model behave differently at each history depth the policy names?

    The minimum-history cutoffs are a product decision made before any
    measurement. This is the measurement, and it does not say what the policy
    assumed. Discrimination does not improve with depth: relative to each band's
    own base rate the middle band ranks best and the deepest band does not lead.

    That is not an argument for dropping the bands. It is an argument for what
    they mean -- a confidence label describes how trustworthy the *percentile*
    is, which genuinely needs history, not how well the model ranks. Reporting
    lift beside PR-AUC is what makes the comparison fair, since PR-AUC rises with
    the base rate and the bands do not share one.
    """
    from sklearn.metrics import average_precision_score, roc_auc_score

    depth = data["relative"]["self_history_depth"].reindex(predictions.index)
    bands = [(0, 4, "0-4 (abstain)"), (5, 9, "5-9 (low)"),
             (10, 19, "10-19 (medium)"), (20, 10**9, "20+ (standard)")]
    rows = []
    for low, high, name in bands:
        mask = (depth >= low) & (depth <= high)
        group = predictions[mask]
        if len(group) < 30 or group["label"].nunique() < 2:
            rows.append({"band": name, "filings": len(group), "base_rate": np.nan,
                         "pr_auc": np.nan, "roc_auc": np.nan})
            continue
        y, p = group["label"].to_numpy(), group["probability"].to_numpy()
        base = float(y.mean())
        precision = float(average_precision_score(y, p))
        rows.append({"band": name, "filings": len(group), "base_rate": base,
                     "pr_auc": precision,
                     "pr_auc_lift": precision / base if base > 0 else np.nan,
                     "roc_auc": float(roc_auc_score(y, p))})
    return pd.DataFrame(rows)


def event_type_subgroups(data, predictions, minimum: int = 100) -> pd.DataFrame:
    """Performance per 8-K item code, for the codes with enough filings.

    Reported because an aggregate can hide a family the model reads badly, and
    a card that fires confidently on the one event type it cannot rank is worse
    than one that fires less often.
    """
    from sklearn.metrics import average_precision_score, roc_auc_score

    items = data["items"].reindex(predictions.index).fillna("").astype(str)
    codes = sorted({c.strip() for row in items for c in row.split(",") if c.strip()})
    rows = []
    for code in codes:
        mask = items.str.contains(rf"(?:^|,)\s*{code.replace('.', chr(92) + '.')}(?:,|$)",
                                  regex=True)
        group = predictions[mask]
        if len(group) < minimum or group["label"].nunique() < 2:
            continue
        y, p = group["label"].to_numpy(), group["probability"].to_numpy()
        base = float(y.mean())
        precision = float(average_precision_score(y, p))
        rows.append({"item": code, "filings": len(group), "base_rate": base,
                     "pr_auc": precision,
                     "pr_auc_lift": precision / base if base > 0 else np.nan,
                     "roc_auc": float(roc_auc_score(y, p))})
    return pd.DataFrame(rows).sort_values("filings", ascending=False)


def threshold_sweep(predictions, signals, policy: recommend.Policy) -> pd.DataFrame:
    """Precision, recall and volume across candidate thresholds.

    Published so the shipped threshold can be read against its neighbours. A
    policy whose precision collapses either side of the chosen point is fitted
    to the grid rather than to the problem, and this table is where that shows.
    """
    labels = predictions["label"].astype(float)
    rows = []
    for threshold in np.round(np.arange(0.15, 0.90, 0.05), 2):
        candidate = recommend.Policy(read_now=float(threshold),
                                     monitor=min(policy.monitor, float(threshold)),
                                     support=policy.support)
        states = recommend.recommend(predictions["probability"], signals,
                                     policy=candidate)
        fires = states["state"] == recommend.READ_NOW
        rows.append({
            "threshold": float(threshold),
            "read_now": int(fires.sum()),
            "share": float(fires.mean()),
            "precision": float(labels[fires].mean()) if fires.any() else np.nan,
            "recall": (float(labels[fires].sum()) / labels.sum()
                       if labels.sum() else np.nan),
            "shipped": bool(abs(threshold - policy.read_now) < 1e-9),
        })
    return pd.DataFrame(rows)


SCATTER_POINTS = 40


def _write_company_cards(path: Path, data, predictions, states, metrics,
                         policy) -> None:
    """Per-issuer card data for the company page, plus its self-history points.

    Written to `data/build` rather than `evidence/` because it is a page input,
    not a research artifact: it carries one issuer's latest decision and the
    scatter behind it, and it changes whenever the pages are rebuilt.

    Keeping `company_lens` out of `filing_triage`'s pipeline is the point. The
    page reads a file; it does not import a model, and a missing file degrades
    the page to its existing content rather than breaking the build.
    """
    relative = data["relative"]
    target = data["target"]
    events = data["result"].events.set_index("event_id")
    labels = data["result"].labels.set_index("event_id")

    cards: dict[str, dict] = {}
    for ticker, group in events.groupby("ticker"):
        eligible = group.index.intersection(predictions.index)
        if not len(eligible):
            continue
        latest = group.loc[eligible].sort_values("acceptance_time").index[-1]

        history = group.index.intersection(relative.index)
        points = []
        for event_id in history:
            novelty = relative.at[event_id, "self_novelty_pct"]
            reaction = labels["reaction"].get(event_id)
            if not (np.isfinite(novelty) and np.isfinite(reaction)):
                continue
            points.append({
                "novelty": round(float(novelty), 4),
                "reaction": round(float(reaction), 4),
                "date": str(pd.Timestamp(events.at[event_id, "acceptance_time"]).date()),
                "items": str(events.at[event_id, "items"] or ""),
                "current": bool(event_id == latest),
            })
        points = sorted(points, key=lambda x: x["date"])[-SCATTER_POINTS:]

        state = states.loc[latest]
        cards[str(ticker)] = {
            "event_id": str(latest),
            "accepted": str(pd.Timestamp(events.at[latest, "acceptance_time"])),
            "items": str(events.at[latest, "items"] or ""),
            "state": str(state["state"]),
            "reasons": list(state["reasons"]),
            "probability": (round(float(state["probability"]), 4)
                            if np.isfinite(state["probability"]) else None),
            "issuer_base_rate": (
                round(float(target["self_target"].reindex(history).mean()), 4)
                if len(history) else None),
            "confidence": str(target["self_target_confidence"].get(latest, "unknown")),
            "eligible_history": int(relative["self_history_depth"].get(latest, 0)),
            "resolved_history": int(relative["self_resolved_depth"].get(latest, 0)),
            "points": points,
        }

    payload = {
        "schema_version": "self-relative-card.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "model": {
            "estimator": metrics.get("estimator"),
            "calibration": metrics.get("calibration_method"),
            "policy": policy.describe(),
            "evaluated_through": str(pd.Timestamp(
                data["event_time"].max()).date()),
        },
        "boundary": ("Reaction magnitude, never direction. This is a reading "
                     "priority, not investment advice."),
        "companies": cards,
    }
    path.write_text(json.dumps(payload, indent=1, default=str) + "\n")
    print(f"  company cards for {len(cards)} issuers -> {path}")


def _text_fingerprint(data) -> dict | None:
    """What the transformer columns were built from, or None if they were not.

    Recorded next to the ablation that judged them so the page can state the
    corpus size without a number written into it by hand -- and so a rerun
    against a different model shows up as a changed fingerprint rather than as a
    quietly different table.
    """
    columns = data["text_features"]
    if columns.empty or not len(columns.columns):
        return None
    cache = text_model.TextCache(Path("data/build/text_cache"))
    fingerprint = cache.fingerprint()
    fingerprint["scored_filings"] = int(columns.notna().any(axis=1).sum())
    return fingerprint


def _feature_groups(features: pd.DataFrame) -> dict[str, list[str]]:
    """Which columns belong to which family.

    Assigned by prefix rather than by hand: a new feature joins the family its
    name says it belongs to, and a family cannot silently lose a column because
    someone forgot to add it to a list.
    """
    text_deterministic = {"novelty", "first_filing", "log_doc_chars",
                          "doc_chars_vs_median"}
    transformer = [c for c in features.columns if c.startswith("fin_")]
    deterministic = [c for c in features.columns if c in text_deterministic]
    structured = [c for c in features.columns
                  if c not in set(transformer) | set(deterministic)]
    return {"structured": structured, "deterministic_text": deterministic,
            "transformer_text": transformer}


def text_feature_ablation(data, groups=ABLATION_GROUPS) -> pd.DataFrame:
    """What each family of features is worth, added one at a time.

    The question is not whether a transformer improves the number. It is whether
    it improves it *beyond the deterministic text features already here*, which
    is why `deterministic_text` sits between the baseline and the transformer
    row rather than being folded into it. A transformer that only recovers what
    a hashing vectorizer already found has not earned an optional dependency
    weighing a hundred megabytes.

    Reported whichever way it comes out. "We measured it and it did not help" is
    a result, and a more useful one than an unmeasured feature that stays.
    """
    matrix = data["features"].join(data["text_features"])
    families = _feature_groups(matrix)
    if not families["transformer_text"]:
        return pd.DataFrame(columns=["group", "features", "pr_auc", "roc_auc",
                                     "brier", "n_scored"])

    layers = {
        "structured": families["structured"],
        "deterministic_text": families["structured"] + families["deterministic_text"],
        "transformer_text": families["structured"] + families["transformer_text"],
        "all": (families["structured"] + families["deterministic_text"]
                + families["transformer_text"]),
    }
    rows = []
    predictions: dict[str, pd.DataFrame] = {}
    for name in groups:
        selected = layers.get(name)
        if not selected:
            continue
        # Kept in the matrix's own order rather than concatenated by family. A
        # forest samples features by position, so the same columns in a
        # different order fit a different model: reordering alone moved average
        # precision by 0.0007 here, which is noise this table cannot afford to
        # mix into a 0.0055 effect. In matrix order the `deterministic_text` row
        # is exactly the shipped configuration.
        chosen = set(selected)
        columns = [c for c in matrix.columns if c in chosen]
        scored = calibrated_walk_forward(
            matrix[columns], data["target"]["self_target"],
            data["event_time"], data["label_end_time"],
            method=SHIPPED_CALIBRATION)
        if not scored.metrics:
            continue
        predictions[name] = scored.predictions
        rows.append({
            "group": name,
            "features": len(columns),
            "pr_auc": scored.metrics["pr_auc"],
            "roc_auc": scored.metrics["roc_auc"],
            "brier": scored.metrics["brier"],
            "n_scored": scored.metrics["n_scored"],
        })
    table = pd.DataFrame(rows)
    if table.empty or "structured" not in predictions:
        return table

    # The point estimates alone would let a reader treat a third of a percentage
    # point of average precision as a finding. Paired, session-clustered, and
    # reported as an interval, so the table can say "no measurable difference"
    # in the only way that means anything.
    baseline = predictions["structured"]
    table["pr_auc_vs_structured"] = table["pr_auc"] - float(
        table.loc[table["group"] == "structured", "pr_auc"].iloc[0])
    intervals = [paired_pr_auc_difference(baseline, predictions[name],
                                          data["session"])
                 for name in table["group"]]
    table["diff_ci_low"] = [i["low"] for i in intervals]
    table["diff_ci_high"] = [i["high"] for i in intervals]
    table["separates_from_zero"] = [
        bool(np.isfinite(i["low"]) and (i["low"] > 0 or i["high"] < 0))
        for i in intervals]
    return table

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=Path("data/build"))
    parser.add_argument("--out", type=Path, default=Path("evidence/real_run"))
    args = parser.parse_args()

    provenance = json.loads((args.build / "provenance.json").read_text())
    if provenance.get("source") != "edgar":
        raise ValueError("refusing to label a non-EDGAR build as real evidence")

    events = pd.read_parquet(args.build / "events.parquet")
    prices = load_prices(args.build / "prices.parquet")
    membership = load_membership(args.build / "membership.csv")
    profile_path = args.build / "issuer_profile.csv"
    profile = pd.read_csv(profile_path) if profile_path.exists() else None

    data = build_inputs(events, prices, membership, profile)
    args.out.mkdir(parents=True, exist_ok=True)

    comparison = calibration_comparison(
        data["features"], data["target"]["self_target"],
        data["event_time"], data["label_end_time"])
    comparison.to_csv(args.out / "calibration_comparison.csv", index=False)

    calibrated = calibrated_walk_forward(
        data["features"], data["target"]["self_target"],
        data["event_time"], data["label_end_time"], method=SHIPPED_CALIBRATION)
    predictions = calibrated.predictions

    calibrated.reliability.to_csv(args.out / "calibration_curve.csv", index=False)
    within_fold_monotonicity(calibrated).to_csv(
        args.out / "calibration_monotonicity.csv", index=False)

    signals = data["relative"].reindex(predictions.index)
    policy = recommend.select_thresholds(
        predictions["probability"], predictions["label"].astype(float),
        signals, predictions["fold"])
    states = recommend.recommend(
        predictions["probability"], signals,
        confidence=data["target"]["self_target_confidence"].reindex(predictions.index),
        policy=policy)

    recommend.evaluate(states, predictions["label"].astype(float)).to_csv(
        args.out / "recommendation_confusion.csv", index=False)
    threshold_sweep(predictions, signals, policy).to_csv(
        args.out / "recommendation_thresholds.csv", index=False)
    ablation = text_feature_ablation(data)
    if not ablation.empty:
        ablation.to_csv(args.out / "nlp_feature_ablation.csv", index=False)

    history_depth_sensitivity(data, predictions).to_csv(
        args.out / "history_depth_sensitivity.csv", index=False)
    event_type_subgroups(data, predictions).to_csv(
        args.out / "event_type_subgroups.csv", index=False)

    depth = data["relative"]["self_history_depth"]
    payload = {
        "schema_version": "self-relative.v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "target": {
            "definition": "|CAR| above the issuer's own prior resolved 80th percentile",
            "quantile": 0.80,
            "eligible": int(data["target"]["self_target"].notna().sum()),
            "total": len(data["target"]),
            "base_rate": float(data["target"]["self_target"].mean()),
        },
        "history": {
            "median_depth": float(depth.median()),
            "max_depth": int(depth.max()),
            "confidence_counts": data["relative"]["self_confidence"].value_counts().to_dict(),
            "policy": HistoryPolicy().__dict__,
        },
        "calibration": calibrated.metrics,
        "recommendation": {
            "policy": policy.describe(),
            "read_now_threshold": policy.read_now,
            "monitor_threshold": policy.monitor,
            "support_percentile": policy.support,
            "state_counts": states["state"].value_counts().to_dict(),
        },
        # The filing sample's own range, not the price history's. The prices go
        # back to 1962; quoting that as the sample would misdescribe what these
        # numbers were measured on.
        "sample": {
            "first_filing": str(events["acceptance_time"].min().date()),
            "last_filing": str(events["acceptance_time"].max().date()),
        },
        "text": _text_fingerprint(data),
        "inputs": input_fingerprints(events, prices, membership),
        "environment": environment(),
    }
    (args.out / "self_relative_metrics.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n")

    _write_company_cards(args.build / "self_relative_cards.json",
                         data, predictions, states, calibrated.metrics, policy)

    print(f"self-relative evidence written to {args.out}")
    print(f"  target base rate {payload['target']['base_rate']:.1%} on "
          f"{payload['target']['eligible']:,} filings")
    print(f"  shipped calibration {SHIPPED_CALIBRATION}, "
          f"read-now threshold {policy.read_now:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


