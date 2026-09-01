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

from filing_triage import pipeline, recommend
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

SHIPPED_CALIBRATION = "identity"


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

    aligned = result.labels.set_index("event_id").reindex(result.features.index)
    indexed = result.events.set_index("event_id")
    return {
        "result": result,
        "relative": relative,
        "target": target,
        "features": features,
        "event_time": indexed.loc[result.features.index, "acceptance_time"],
        "label_end_time": pd.to_datetime(
            aligned["label_end_session"]
        ).dt.tz_localize(result.events["acceptance_time"].dt.tz),
        "items": indexed.loc[result.features.index, "items"],
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
        "inputs": input_fingerprints(events, prices, membership),
        "environment": environment(),
    }
    (args.out / "self_relative_metrics.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n")

    print(f"self-relative evidence written to {args.out}")
    print(f"  target base rate {payload['target']['base_rate']:.1%} on "
          f"{payload['target']['eligible']:,} filings")
    print(f"  shipped calibration {SHIPPED_CALIBRATION}, "
          f"read-now threshold {policy.read_now:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
