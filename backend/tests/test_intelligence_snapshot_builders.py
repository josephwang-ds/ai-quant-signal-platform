"""Phase 4.4 — deterministic artifact-to-snapshot builder tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.errors import (
    SnapshotArtifactPayloadError,
    SnapshotSourceError,
    UnsupportedArtifactContractError,
)
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ResearchArtifactType,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
)
from app.intelligence.snapshot_builders import (
    RESEARCH_SUMMARY_EVIDENCE_VERSION,
    SIGNAL_EVIDENCE_VERSION,
    ResearchSummarySnapshotBuilder,
    SignalSnapshotBuilder,
    stable_snapshot_content,
)
from app.intelligence.snapshot_contracts import (
    SignalDirection,
    SignalRecord,
    SnapshotFinding,
    SnapshotLimitation,
    ValidationStatus,
)
from app.intelligence.snapshot_registry import ResearchSnapshotRegistry
from app.intelligence.storage import IntelligenceStorage


@pytest.fixture
def run_registry(tmp_path: Path) -> ResearchRunRegistry:
    return ResearchRunRegistry(storage=IntelligenceStorage(root=tmp_path / "outputs"))


@pytest.fixture
def artifacts(run_registry: ResearchRunRegistry) -> ResearchArtifactRegistry:
    return ResearchArtifactRegistry(run_registry)


@pytest.fixture
def snapshots(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
) -> ResearchSnapshotRegistry:
    return ResearchSnapshotRegistry(run_registry, artifact_registry=artifacts)


@pytest.fixture
def created_run(run_registry: ResearchRunRegistry) -> str:
    return run_registry.create_run(
        run_type=ResearchRunType.FACTOR,
        universe="US Liquid 31",
    ).run.run_id


def _summary_payload(**overrides: object) -> dict:
    base = {
        "schema_version": RESEARCH_SUMMARY_EVIDENCE_VERSION,
        "research_title": "Momentum evidence",
        "research_objective": "Document factor IC",
        "analysis_window": "2020-01 to 2024-12",
        "validation_status": "passed",
        "key_findings": [
            {"code": "ic", "statement": "Mean RankIC positive", "category": "factor"}
        ],
        "limitations": [{"code": "n", "statement": "Small universe"}],
        "as_of": "2026-07-28T12:00:00Z",
    }
    base.update(overrides)
    return base


def _signal_payload(**overrides: object) -> dict:
    base = {
        "schema_version": SIGNAL_EVIDENCE_VERSION,
        "universe": "US Liquid 31",
        "as_of": "2026-07-28T12:00:00Z",
        "signals": [
            {
                "symbol": "AAPL",
                "signal_name": "mom_5d",
                "direction": "positive",
                "score": 0.4,
                "confidence": 0.8,
                "horizon": "5D",
                "evidence_artifact_ids": [],
                "metadata": {},
            }
        ],
    }
    base.update(overrides)
    return base


def test_research_summary_builder_maps_supported_artifact(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="summary-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    snap = builder.build(created_run, source_artifact_ids=[ref.artifact_id])
    assert snap.research_title == "Momentum evidence"
    assert snap.research_objective == "Document factor IC"
    assert snap.analysis_window == "2020-01 to 2024-12"
    assert snap.validation_status == ValidationStatus.PASSED
    assert snap.universe == "US Liquid 31"
    assert snap.run_type == ResearchRunType.FACTOR
    assert snap.key_findings[0].statement == "Mean RankIC positive"
    assert snap.limitations[0].statement == "Small universe"
    assert snap.artifact_summary[0].artifact_id == ref.artifact_id
    assert snap.provenance.source_artifact_ids == [ref.artifact_id]
    assert snap.provenance.builder == ResearchSummarySnapshotBuilder.BUILDER_ID


def test_research_summary_deterministic_excluding_identity(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="summary-stable",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    fixed = datetime(2026, 7, 28, 15, 0, 0, tzinfo=timezone.utc)
    left = builder.build(
        created_run, source_artifact_ids=[ref.artifact_id], now=fixed
    )
    right = builder.build(
        created_run, source_artifact_ids=[ref.artifact_id], now=fixed
    )
    assert left.model_dump(mode="json") == right.model_dump(mode="json")
    other_time = datetime(2026, 7, 28, 16, 0, 0, tzinfo=timezone.utc)
    shifted = builder.build(
        created_run, source_artifact_ids=[ref.artifact_id], now=other_time
    )
    assert stable_snapshot_content(left.model_dump(mode="json")) == stable_snapshot_content(
        shifted.model_dump(mode="json")
    )


def test_research_summary_unsupported_and_malformed(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    bad = artifacts.register_json_artifact(
        created_run,
        name="unsupported",
        artifact_type=ResearchArtifactType.FACTOR_METRICS,
        payload={"schema_version": "factor-metrics/v1", "mean_ic": 0.1},
    )
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    with pytest.raises(UnsupportedArtifactContractError):
        builder.build(created_run, source_artifact_ids=[bad.artifact_id])

    malformed = artifacts.register_json_artifact(
        created_run,
        name="malformed",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={
            "schema_version": RESEARCH_SUMMARY_EVIDENCE_VERSION,
            "key_findings": [{"statement": "   "}],
        },
    )
    with pytest.raises(SnapshotArtifactPayloadError):
        builder.build(created_run, source_artifact_ids=[malformed.artifact_id])


def test_research_summary_missing_and_cross_run_source(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    with pytest.raises(SnapshotSourceError):
        builder.build(created_run, source_artifact_ids=["artifact_deadbeef"])

    other = run_registry.create_run(run_type=ResearchRunType.MODEL).run.run_id
    other_art = artifacts.register_json_artifact(
        other,
        name="other-summary",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    with pytest.raises(SnapshotSourceError):
        builder.build(created_run, source_artifact_ids=[other_art.artifact_id])


def test_research_summary_strict_verification_and_permissive(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="tamper-summary",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    path.write_bytes(path.read_bytes() + b" ")
    strict = ResearchSummarySnapshotBuilder(
        artifacts, snapshots, require_artifact_verification=True
    )
    with pytest.raises(SnapshotSourceError):
        strict.build(created_run, source_artifact_ids=[ref.artifact_id])
    permissive = ResearchSummarySnapshotBuilder(
        artifacts, snapshots, require_artifact_verification=False
    )
    # Tampered JSON may fail decode or still parse — write valid JSON with different bytes.
    path.write_text(
        json.dumps(_summary_payload(research_title="tampered"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(SnapshotSourceError):
        strict.build(created_run, source_artifact_ids=[ref.artifact_id])
    # Permissive mode does not verify checksum; payload still maps.
    snap = permissive.build(created_run, source_artifact_ids=[ref.artifact_id])
    assert snap.research_title == "tampered"


def test_research_summary_build_has_no_side_effects(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="no-side-effects",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    before = run_registry.get_run(created_run)
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    builder.build(created_run, source_artifact_ids=[ref.artifact_id])
    after = run_registry.get_run(created_run)
    assert after.run.status == before.run.status == ResearchRunStatus.CREATED
    assert after.snapshots == []
    assert not run_registry.storage.snapshots_dir(created_run).exists() or list(
        run_registry.storage.snapshots_dir(created_run).glob("*.json")
    ) == []


def test_research_summary_build_and_register_round_trip(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="register-summary",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    builder = ResearchSummarySnapshotBuilder(artifacts, snapshots)
    registered = builder.build_and_register(
        created_run,
        name="summary-snap",
        source_artifact_ids=[ref.artifact_id],
    )
    assert isinstance(registered, ResearchSnapshotReference)
    assert registered.source_artifact_ids == [ref.artifact_id]
    assert snapshots.verify_snapshot(created_run, registered.snapshot_id).valid is True
    loaded = snapshots.get_snapshot(created_run, "summary-snap")
    assert loaded.checksum == registered.checksum


def test_signal_builder_all_directions_and_optionals(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    signals = [
        {
            "symbol": f"S{i}",
            "signal_name": "demo",
            "direction": direction.value,
            "score": None if direction == SignalDirection.NEUTRAL else 0.1 * i,
            "confidence": None if direction == SignalDirection.NEUTRAL else 0.5,
            "evidence_artifact_ids": ["artifact_aaaaaaaa"],
            "metadata": {},
        }
        for i, direction in enumerate(SignalDirection)
    ]
    ref = artifacts.register_json_artifact(
        created_run,
        name="all-directions",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(signals=signals),
    )
    builder = SignalSnapshotBuilder(artifacts, snapshots)
    snap = builder.build(created_run, source_artifact_ids=[ref.artifact_id])
    assert {row.direction for row in snap.signals} == set(SignalDirection)
    assert snap.as_of is not None
    assert snap.provenance.builder == SignalSnapshotBuilder.BUILDER_ID
    assert any(row.evidence_artifact_ids == ["artifact_aaaaaaaa"] for row in snap.signals)


def test_signal_builder_rejects_invalid_direction_and_nonfinite(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    builder = SignalSnapshotBuilder(artifacts, snapshots)
    invalid_dir = artifacts.register_json_artifact(
        created_run,
        name="bad-dir",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(
            signals=[
                {
                    "symbol": "AAPL",
                    "signal_name": "x",
                    "direction": "buy",
                    "metadata": {},
                    "evidence_artifact_ids": [],
                }
            ]
        ),
    )
    with pytest.raises(SnapshotArtifactPayloadError):
        builder.build(created_run, source_artifact_ids=[invalid_dir.artifact_id])

    for label, value in [
        ("nan", float("nan")),
        ("pos-inf", float("inf")),
        ("neg-inf", float("-inf")),
    ]:
        # serialize_artifact_json rejects NaN/Inf at registration time.
        with pytest.raises(Exception):
            artifacts.register_json_artifact(
                created_run,
                name=f"bad-{label}",
                artifact_type=ResearchArtifactType.GENERIC_JSON,
                payload=_signal_payload(
                    signals=[
                        {
                            "symbol": "AAPL",
                            "signal_name": "x",
                            "direction": "neutral",
                            "score": value,
                            "metadata": {},
                            "evidence_artifact_ids": [],
                        }
                    ]
                ),
            )


def test_signal_builder_rejects_nan_via_raw_file(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    """Register opaque bytes that look like JSON with NaN (invalid JSON actually).

    Use a valid JSON null score then mutate file to inject Infinity token via
    a pre-registered payload that uses a string we replace — instead validate
    SignalRecord path by constructing evidence with invalid float through
    model validation after reading crafted JSON without NaN literals.
    """
    ref = artifacts.register_json_artifact(
        created_run,
        name="signal-finite",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(
            signals=[
                {
                    "symbol": "AAPL",
                    "signal_name": "x",
                    "direction": "neutral",
                    "score": 1.0,
                    "metadata": {},
                    "evidence_artifact_ids": [],
                }
            ]
        ),
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    text = path.read_text(encoding="utf-8").replace("1.0", "Infinity", 1)
    path.write_text(text, encoding="utf-8")
    # Checksum no longer matches; permissive read still parses JSON with Infinity
    # which json.loads accepts in Python — then SignalEvidence validation must reject.
    builder = SignalSnapshotBuilder(artifacts, snapshots, require_artifact_verification=False)
    with pytest.raises(SnapshotArtifactPayloadError):
        builder.build(created_run, source_artifact_ids=[ref.artifact_id])


def test_signal_builder_unsupported_contract_and_determinism(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    bad = artifacts.register_json_artifact(
        created_run,
        name="pred-table",
        artifact_type=ResearchArtifactType.PREDICTION_TABLE,
        payload=[{"symbol": "AAPL", "score": 0.1}],
    )
    builder = SignalSnapshotBuilder(artifacts, snapshots)
    with pytest.raises(UnsupportedArtifactContractError):
        builder.build(created_run, source_artifact_ids=[bad.artifact_id])

    good = artifacts.register_json_artifact(
        created_run,
        name="signal-good",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(),
    )
    fixed = datetime(2026, 7, 28, 18, 0, 0, tzinfo=timezone.utc)
    left = builder.build(created_run, source_artifact_ids=[good.artifact_id], now=fixed)
    right = builder.build(created_run, source_artifact_ids=[good.artifact_id], now=fixed)
    assert left.model_dump(mode="json") == right.model_dump(mode="json")


def test_signal_build_side_effects_and_register_provenance_agree(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="signal-register",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(),
    )
    builder = SignalSnapshotBuilder(artifacts, snapshots)
    builder.build(created_run, source_artifact_ids=[ref.artifact_id])
    assert run_registry.get_run(created_run).snapshots == []

    registered = builder.build_and_register(
        created_run,
        name="signal-snap",
        source_artifact_ids=[ref.artifact_id],
    )
    assert registered.source_artifact_ids == [ref.artifact_id]
    path = run_registry.storage.resolve_run_relative_path(
        created_run, registered.relative_path
    )
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["provenance"]["source_artifact_ids"] == registered.source_artifact_ids
    assert snapshots.verify_snapshot(created_run, registered.name).valid is True


def test_signal_strict_verification_rejects_tamper(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="signal-tamper",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(),
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    path.write_bytes(path.read_bytes() + b"\n")
    builder = SignalSnapshotBuilder(
        artifacts, snapshots, require_artifact_verification=True
    )
    with pytest.raises(SnapshotSourceError):
        builder.build(created_run, source_artifact_ids=[ref.artifact_id])


def test_phase43_convenience_builders_still_work(
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="legacy-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"opaque": True},
    )
    summary = snapshots.build_research_summary_snapshot(
        created_run,
        name="legacy-summary",
        source_artifact_ids=[ref.artifact_id],
        key_findings=[SnapshotFinding(statement="explicit")],
        limitations=[SnapshotLimitation(statement="explicit limit")],
    )
    signal = snapshots.build_signal_snapshot(
        created_run,
        name="legacy-signal",
        source_artifact_ids=[ref.artifact_id],
        signals=[
            SignalRecord(
                symbol="MSFT",
                signal_name="mom",
                direction=SignalDirection.NEGATIVE,
            )
        ],
    )
    assert summary.name == "legacy-summary"
    assert signal.name == "legacy-signal"
    assert snapshots.verify_snapshot(created_run, summary.snapshot_id).valid
    assert snapshots.verify_snapshot(created_run, signal.snapshot_id).valid
