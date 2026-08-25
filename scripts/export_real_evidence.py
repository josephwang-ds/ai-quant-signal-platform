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

from filing_triage import pipeline
from filing_triage.config import PipelineConfig
from filing_triage.ingest.prices import load_prices
from filing_triage.ingest.universe import load_membership


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
    result = pipeline.run(
        events, prices, membership, PipelineConfig(), compute_importance=True
    )
    result.audit.raise_if_failed()

    args.out.mkdir(parents=True, exist_ok=True)
    _write_json(args.out / "metrics.json", result.metrics)
    _write_json(args.out / "integrity.json", result.integrity)
    _write_json(args.out / "provenance.json", provenance)
    result.by_fold.to_csv(args.out / "fold_metrics.csv", index=False)
    result.importance.to_csv(args.out / "oos_importance.csv", index=False)
    result.audit.to_frame().to_csv(args.out / "audit.csv", index=False)

    leakage_path = args.build / "leakage_study.csv"
    if not leakage_path.exists():
        raise ValueError("data/build/leakage_study.csv is missing; run `make run` first")
    pd.read_csv(leakage_path).to_csv(args.out / "leakage_study.csv", index=False)

    _write_json(args.out / "manifest.json", {
        "schema_version": "1.0",
        "exported_at": datetime.now(UTC).isoformat(),
        "pipeline_config": {
            "reaction_threshold": result.config.reaction_threshold,
            "event_window_sessions": result.config.event_window_sessions,
            "estimation_sessions": result.config.estimation_sessions,
            "estimation_gap_sessions": result.config.estimation_gap_sessions,
            "validation": "purged_embargoed_walk_forward",
        },
        "files": [
            "metrics.json",
            "integrity.json",
            "provenance.json",
            "fold_metrics.csv",
            "oos_importance.csv",
            "audit.csv",
            "leakage_study.csv",
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
