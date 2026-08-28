"""Export a small, reviewable evidence package from the local real-data build.

Raw filing text and prices remain ignored. The exported JSON/CSV files are the
minimum needed to trace README claims to one corrected pipeline execution.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from filing_triage import experiments, pipeline
from filing_triage.config import PipelineConfig
from filing_triage.fingerprint import environment, input_fingerprints
from filing_triage.ingest.prices import load_prices
from filing_triage.ingest.universe import load_membership


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=Path("data/build"))
    parser.add_argument("--out", type=Path, default=Path("evidence/real_run"))
    parser.add_argument("--skip-model-comparison", action="store_true",
                        help="skip the candidate sweep, which dominates runtime")
    args = parser.parse_args()

    provenance = json.loads((args.build / "provenance.json").read_text())
    if provenance.get("source") != "edgar":
        raise ValueError("refusing to label a non-EDGAR build as real evidence")

    events = pd.read_parquet(args.build / "events.parquet")
    prices = load_prices(args.build / "prices.parquet")
    membership = load_membership(args.build / "membership.csv")
    profile_path = args.build / "issuer_profile.csv"
    profile = pd.read_csv(profile_path) if profile_path.exists() else None
    result = pipeline.run(
        events, prices, membership, PipelineConfig(),
        issuer_profile=profile, compute_importance=True
    )
    result.audit.raise_if_failed()

    args.out.mkdir(parents=True, exist_ok=True)
    _write_json(args.out / "metrics.json", result.metrics)
    _write_json(args.out / "integrity.json", result.integrity)
    _write_json(args.out / "provenance.json", provenance)
    result.by_fold.to_csv(args.out / "fold_metrics.csv", index=False)
    result.importance.to_csv(args.out / "oos_importance.csv", index=False)
    result.audit.to_frame().to_csv(args.out / "audit.csv", index=False)
    result.baseline_comparisons.to_csv(args.out / "baseline_intervals.csv", index=False)

    # The three studies a reader is most likely to want to check by hand: what
    # each baseline comparison survives, how much of the reaction was already in
    # the opening print, and whether the headline depends on the estimator's
    # constants. All are reproducible from the same build.
    experiments.reaction_capture_profile(events, prices).to_csv(
        args.out / "reaction_capture.csv", index=False)
    experiments.anchoring_study(events, prices, membership, issuer_profile=profile).to_csv(
        args.out / "anchoring_study.csv", index=False)
    experiments.hyperparameter_sensitivity(
        events, prices, membership, issuer_profile=profile).to_csv(
        args.out / "hyperparameter_sensitivity.csv", index=False)

    # k is how many filings someone reads, and the project assumed five rather
    # than deriving it. Reporting the sweep turns that assumption into something
    # a reader can check: the lift swings from 2.6x to 1.1x across capacities,
    # while the share of achievable span the model captures barely moves.
    experiments.capacity_profile(result.predictions, result.events).to_csv(
        args.out / "capacity_profile.csv", index=False)
    experiments.session_material_counts(result.predictions, result.events).to_csv(
        args.out / "session_material_counts.csv", index=False)

    # Whether the model family matters, answered rather than asserted. The
    # project's argument rests on it mattering far less than the validation
    # scheme; a comparison is how that stops being a claim.
    if not args.skip_model_comparison:
        table, paired, nested = experiments.model_comparison(
            events, prices, membership, issuer_profile=profile)
        table.to_csv(args.out / "model_comparison.csv", index=False)
        paired.to_csv(args.out / "model_comparison_paired.csv", index=False)
        _write_json(args.out / "nested_selection.json", nested)

    # Recomputed here rather than copied out of data/build. The copy was whatever
    # `make run` last wrote, so changing the estimator and re-exporting produced a
    # package whose headline came from one model and whose ladder came from
    # another -- both plausible, disagreeing, and silent about it. The ladder is
    # five extra pipeline runs; a self-consistent evidence package is worth them.
    study = experiments.run_leakage_study(events, prices, membership, issuer_profile=profile)
    study.to_csv(args.out / "leakage_study.csv", index=False)

    # The ladder's last rung is the honest pipeline, which is the same
    # configuration the headline metrics came from. If those two ever disagree,
    # the package is describing two different runs and every comparison a reader
    # makes across its files is void.
    honest = float(study.iloc[-1]["average_precision"])
    if abs(honest - result.metrics["average_precision"]) > 1e-9:
        raise ValueError(
            f"ladder's honest rung scores {honest:.6f} but the headline metrics "
            f"say {result.metrics['average_precision']:.6f}; the evidence package "
            "would be internally inconsistent"
        )

    _write_json(args.out / "manifest.json", {
        "schema_version": "1.1",
        "exported_at": datetime.now(UTC).isoformat(),
        "pipeline_config": {
            "reaction_threshold": result.config.reaction_threshold,
            "event_window_sessions": result.config.event_window_sessions,
            "estimation_sessions": result.config.estimation_sessions,
            "estimation_gap_sessions": result.config.estimation_gap_sessions,
            "validation": "purged_embargoed_walk_forward",
            "reaction_measured_from": ("prior close (market-model event study "
                                       "convention); see reaction_capture.csv"),
        },
        "uncertainty": {
            "method": "cluster bootstrap over sessions; paired for baselines",
            "draws": result.metrics.get("bootstrap_draws"),
            "sessions": result.metrics.get("bootstrap_sessions"),
        },
        # What the numbers were computed from, and on what. Without these a
        # rerun that disagrees cannot be diagnosed: EDGAR grows, vendor prices
        # are re-adjusted retroactively, and the dependency floors are `>=`, so
        # "the code changed" and "the inputs changed" look identical.
        "inputs": input_fingerprints(events, prices, membership),
        "environment": environment(),
        "files": [
            "metrics.json",
            "integrity.json",
            "provenance.json",
            "fold_metrics.csv",
            "oos_importance.csv",
            "audit.csv",
            "leakage_study.csv",
            "baseline_intervals.csv",
            "reaction_capture.csv",
            "anchoring_study.csv",
            "hyperparameter_sensitivity.csv",
            "capacity_profile.csv",
            "session_material_counts.csv",
            "model_comparison.csv",
            "model_comparison_paired.csv",
            "nested_selection.json",
        ],
        "raw_data_committed": False,
        "note": "Metrics are real-data results; the convenience universe has survivorship bias.",
    })
    print(f"real-run evidence written to {args.out}")
    return 0


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n")


def _json_default(value):
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"cannot serialize {type(value).__name__}")


if __name__ == "__main__":
    raise SystemExit(main())
