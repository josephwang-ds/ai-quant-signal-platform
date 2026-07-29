#!/usr/bin/env python3
"""Seed one professional PUBLISHED intelligence run for local demos.

Writes into the same filesystem registry the Phase 4.5 query layer reads
(``INTELLIGENCE_OUTPUT_DIR`` or default ``backend/outputs``).

This is an explicit operator action — never imported by the frontend and never
used as an automatic Published Workspace / Research Library fallback.

Usage (from ``backend/``):

    source .venv/bin/activate
    python scripts/seed_published_demo_run.py --dry-run
    python scripts/seed_published_demo_run.py

Then start the API and open ``/`` (Research Library).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/seed_published_demo_run.py` without installing the package.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.intelligence.schemas import ResearchArtifactType, ResearchRunStatus, ResearchRunType
from app.intelligence.snapshot_builders import (
    RESEARCH_SUMMARY_EVIDENCE_VERSION,
    SIGNAL_EVIDENCE_VERSION,
    ResearchSummarySnapshotBuilder,
    SignalSnapshotBuilder,
)
from app.intelligence.snapshot_contracts import SignalDirection, ValidationStatus
from app.intelligence.storage import IntelligenceStorage
from app.intelligence_serving.deps import build_intelligence_service


def seed_published_demo_run() -> str:
    storage = IntelligenceStorage()
    service = build_intelligence_service(storage)
    runs = service._runs
    artifacts = service._artifacts
    snapshots = service._snapshots

    created = runs.create_run(
        run_type=ResearchRunType.FACTOR,
        universe="US Liquid 31",
        dataset_version="demo-us-liquid-31-v1",
        feature_version="factor-momentum-v1",
        model_version="demo-rank-score-v1",
        training_window="2018-01-02/2023-12-29",
        prediction_window="2024-01-02/2024-06-28",
        environment="local-demo",
        random_seed=7,
        notes=(
            "Local demo seed for Research Library / Published Workspace. "
            "Research only — not investment advice."
        ),
    )
    run_id = created.run.run_id

    summary_art = artifacts.register_json_artifact(
        run_id,
        name="demo-summary-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={
            "schema_version": RESEARCH_SUMMARY_EVIDENCE_VERSION,
            "research_title": "Cross-Sectional Momentum Factor Review",
            "research_objective": (
                "Evaluate a deterministic cross-sectional momentum factor on a "
                "liquid US equity universe with preserved evidence contracts."
            ),
            "analysis_window": "2018-01-02 → 2024-06-28",
            "validation_status": ValidationStatus.PASSED.value,
            "as_of": "2024-06-28T00:00:00Z",
            "key_findings": [
                {
                    "statement": (
                        "Ranked momentum retained directional separation across "
                        "the documented evaluation window."
                    ),
                    "code": "MOM_RANK_SEPARATION",
                    "category": "factor",
                },
                {
                    "statement": (
                        "Validation checks passed for the seeded demo package; "
                        "consumer snapshots remain read-only."
                    ),
                    "code": "VALIDATION_PASSED",
                    "category": "validation",
                },
            ],
            "limitations": [
                {
                    "statement": (
                        "Synthetic local seed for portfolio demonstration only; "
                        "not a live production research publication."
                    ),
                    "code": "DEMO_SEED",
                },
                {
                    "statement": (
                        "No portfolio construction, expected return, or execution "
                        "claims are included in this package."
                    ),
                    "code": "NO_EXECUTION",
                },
            ],
        },
    )

    signal_art = artifacts.register_json_artifact(
        run_id,
        name="demo-signal-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={
            "schema_version": SIGNAL_EVIDENCE_VERSION,
            "universe": "US Liquid 31",
            "as_of": "2024-06-28T00:00:00Z",
            "signals": [
                {
                    "symbol": "AAPL",
                    "signal_name": "momentum_12_1",
                    "direction": SignalDirection.POSITIVE.value,
                    "score": 0.62,
                    "confidence": 0.71,
                    "horizon": "21d",
                    "evidence_artifact_ids": [],
                    "metadata": {},
                },
                {
                    "symbol": "MSFT",
                    "signal_name": "momentum_12_1",
                    "direction": SignalDirection.STRONG_POSITIVE.value,
                    "score": 0.81,
                    "confidence": 0.74,
                    "horizon": "21d",
                    "evidence_artifact_ids": [],
                    "metadata": {},
                },
                {
                    "symbol": "XOM",
                    "signal_name": "momentum_12_1",
                    "direction": SignalDirection.NEGATIVE.value,
                    "score": -0.44,
                    "confidence": 0.58,
                    "horizon": "21d",
                    "evidence_artifact_ids": [],
                    "metadata": {},
                },
                {
                    "symbol": "JNJ",
                    "signal_name": "momentum_12_1",
                    "direction": SignalDirection.NEUTRAL.value,
                    "score": 0.05,
                    "confidence": 0.41,
                    "horizon": "21d",
                    "evidence_artifact_ids": [],
                    "metadata": {},
                },
            ],
        },
    )

    ResearchSummarySnapshotBuilder(artifacts, snapshots).build_and_register(
        run_id,
        name="research-summary",
        source_artifact_ids=[summary_art.artifact_id],
    )
    SignalSnapshotBuilder(artifacts, snapshots).build_and_register(
        run_id,
        name="signal-board",
        source_artifact_ids=[signal_art.artifact_id],
    )

    runs.update_status(run_id, ResearchRunStatus.RUNNING)
    runs.update_status(run_id, ResearchRunStatus.VALIDATED)
    runs.publish_run(run_id)

    return run_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed one PUBLISHED intelligence run for local demos."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned seed action without writing to the registry.",
    )
    args = parser.parse_args(argv)

    storage = IntelligenceStorage()
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "would_create": "one PUBLISHED FACTOR research run",
                    "artifacts": [
                        "demo-summary-evidence (GENERIC_JSON)",
                        "demo-signal-evidence (GENERIC_JSON)",
                    ],
                    "snapshots": [
                        "research-summary (research_summary)",
                        "signal-board (signal)",
                    ],
                    "output_root": str(storage.root),
                    "library_path": "/",
                    "workspace_path_template": "/research/{run_id}",
                    "note": "No registry writes performed.",
                },
                indent=2,
            )
        )
        return 0

    run_id = seed_published_demo_run()
    payload = {
        "run_id": run_id,
        "status": "PUBLISHED",
        "output_root": str(storage.root),
        "library_path": "/",
        "workspace_path": f"/research/{run_id}",
        "note": (
            "Seeded explicitly. Restart or refresh the API if it was already "
            "running against an empty registry."
        ),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
