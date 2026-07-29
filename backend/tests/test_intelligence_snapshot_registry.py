"""Phase 4.3 — consumer snapshot contracts + registry tests."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.intelligence.artifact_registry import (
    ResearchArtifactRegistry,
    serialize_artifact_json,
)
from app.intelligence.errors import (
    IntelligenceStorageError,
    InvalidRunTransitionError,
    SnapshotAlreadyExistsError,
    SnapshotNotFoundError,
    SnapshotSourceError,
)
from app.intelligence.manifest import manifest_from_dict, manifest_to_dict
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ArtifactReference,
    ResearchArtifactType,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
    generate_snapshot_id,
    is_valid_snapshot_id,
    utc_now,
)
from app.intelligence.snapshot_contracts import (
    RESEARCH_SUMMARY_SCHEMA_VERSION,
    SIGNAL_SNAPSHOT_SCHEMA_VERSION,
    ResearchSummarySnapshot,
    SignalDirection,
    SignalRecord,
    SignalSnapshot,
    SnapshotContentProvenance,
    SnapshotFinding,
    SnapshotLimitation,
    ValidationStatus,
)
from app.intelligence.snapshot_registry import (
    ResearchSnapshotRegistry,
    build_research_summary_snapshot,
    build_signal_snapshot,
)
from app.intelligence.storage import IntelligenceStorage, calculate_sha256


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


@pytest.fixture
def source_artifact(
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> ArtifactReference:
    return artifacts.register_json_artifact(
        created_run,
        name="factor-metrics",
        artifact_type=ResearchArtifactType.FACTOR_METRICS,
        payload={"mean_ic": 0.02},
    )


def test_snapshot_id_format_and_uniqueness() -> None:
    snapshot_id = generate_snapshot_id()
    assert is_valid_snapshot_id(snapshot_id)
    assert snapshot_id.startswith("snapshot_")
    assert not is_valid_snapshot_id("snapshot_SPY")
    assert not is_valid_snapshot_id("artifact_aaaaaaaa")
    ids = {generate_snapshot_id() for _ in range(200)}
    assert len(ids) == 200


def test_research_summary_snapshot_validation() -> None:
    stamp = datetime(2026, 7, 28, 4, 15, 30, tzinfo=timezone.utc)
    snap = ResearchSummarySnapshot(
        generated_at=stamp,
        research_title="Momentum screen",
        validation_status=ValidationStatus.PASSED,
        key_findings=[SnapshotFinding(code="ic", statement="Mean IC positive")],
        limitations=[SnapshotLimitation(statement="Small universe")],
        provenance=SnapshotContentProvenance(
            source_artifact_ids=["artifact_aaaaaaaa"],
            builder="test",
        ),
    )
    assert snap.schema_version == RESEARCH_SUMMARY_SCHEMA_VERSION
    with pytest.raises(ValidationError):
        SnapshotFinding(statement="   ")
    with pytest.raises(ValidationError):
        ResearchSummarySnapshot(
            generated_at=datetime(2026, 7, 28, 4, 15, 30),
            provenance=SnapshotContentProvenance(
                source_artifact_ids=[],
                builder="test",
            ),
        )


def test_signal_snapshot_and_direction_enum_validation() -> None:
    stamp = utc_now()
    signal = SignalRecord(
        symbol="AAPL",
        signal_name="mom_5d",
        direction=SignalDirection.POSITIVE,
        score=0.4,
        confidence=0.7,
        horizon="5D",
        evidence_artifact_ids=["artifact_aaaaaaaa"],
    )
    snap = SignalSnapshot(
        generated_at=stamp,
        universe="US Liquid 31",
        signals=[signal],
        provenance=SnapshotContentProvenance(
            source_artifact_ids=["artifact_aaaaaaaa"],
            builder="test",
        ),
    )
    assert snap.schema_version == SIGNAL_SNAPSHOT_SCHEMA_VERSION
    assert SignalDirection.STRONG_NEGATIVE.value == "strong_negative"
    with pytest.raises(ValidationError):
        SignalRecord(
            symbol="AAPL",
            signal_name="x",
            direction="buy",  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        SignalRecord(
            symbol="AAPL",
            signal_name="x",
            direction=SignalDirection.NEUTRAL,
            confidence=1.5,
        )


def test_no_nan_or_infinity_in_signal_scores() -> None:
    with pytest.raises(ValidationError):
        SignalRecord(
            symbol="AAPL",
            signal_name="x",
            direction=SignalDirection.NEUTRAL,
            score=float("nan"),
        )
    with pytest.raises(ValidationError):
        SignalRecord(
            symbol="AAPL",
            signal_name="x",
            direction=SignalDirection.NEUTRAL,
            confidence=float("inf"),
        )


def test_timezone_aware_timestamps_required() -> None:
    with pytest.raises(ValidationError):
        ResearchSnapshotReference(
            snapshot_id="snapshot_aaaaaaaa",
            name="s",
            snapshot_type="research_summary",
            relative_path="snapshots/s.json",
            checksum="a" * 64,
            size_bytes=1,
            created_at=datetime(2026, 7, 28, 4, 15, 30),
        )


def test_deterministic_serialization_excluding_identity_time(
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    findings = [SnapshotFinding(code="a", statement="Stable finding")]
    fixed = datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)
    left = snapshots.build_research_summary_snapshot(
        created_run,
        name="summary-a",
        source_artifact_ids=[source_artifact.artifact_id],
        research_title="Title",
        key_findings=findings,
        now=fixed,
        as_of=fixed,
    )
    right = snapshots.build_research_summary_snapshot(
        created_run,
        name="summary-b",
        source_artifact_ids=[source_artifact.artifact_id],
        research_title="Title",
        key_findings=findings,
        now=fixed,
        as_of=fixed,
    )
    assert left.snapshot_id != right.snapshot_id
    left_payload = json.loads(
        snapshots._storage.resolve_run_relative_path(created_run, left.relative_path).read_text(
            encoding="utf-8"
        )
    )
    right_payload = json.loads(
        snapshots._storage.resolve_run_relative_path(created_run, right.relative_path).read_text(
            encoding="utf-8"
        )
    )
    # Identity/time may differ across rebuilds; with identical explicit stamp they match.
    assert left_payload == right_payload
    # Stable key order from serialize_artifact_json
    encoded = serialize_artifact_json(left_payload)
    assert encoded == serialize_artifact_json(dict(reversed(list(left_payload.items()))))


def test_snapshot_stored_under_run_snapshots(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    ref = snapshots.build_research_summary_snapshot(
        created_run,
        name="under-snapshots",
        source_artifact_ids=[source_artifact.artifact_id],
    )
    assert ref.relative_path.startswith("snapshots/")
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    assert path.is_file()
    assert path.parent.name == "snapshots"
    assert created_run in str(path)


def test_missing_and_cross_run_source_rejected(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    with pytest.raises(SnapshotSourceError):
        snapshots.build_research_summary_snapshot(
            created_run,
            name="missing-source",
            source_artifact_ids=["artifact_deadbeef"],
        )
    other = run_registry.create_run(run_type=ResearchRunType.MODEL).run.run_id
    other_art = artifacts.register_json_artifact(
        other,
        name="other-metrics",
        artifact_type=ResearchArtifactType.MODEL_EVALUATION,
        payload={"auc": 0.6},
    )
    with pytest.raises(SnapshotSourceError):
        snapshots.build_signal_snapshot(
            created_run,
            name="cross-run",
            source_artifact_ids=[other_art.artifact_id],
            signals=[
                SignalRecord(
                    symbol="MSFT",
                    signal_name="model",
                    direction=SignalDirection.POSITIVE,
                )
            ],
        )
    # Valid same-run source still works.
    snapshots.build_research_summary_snapshot(
        created_run,
        name="same-run-ok",
        source_artifact_ids=[source_artifact.artifact_id],
    )


def test_modified_source_artifact_with_verification_setting(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    path = run_registry.storage.resolve_run_relative_path(
        created_run, source_artifact.relative_path
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(SnapshotSourceError):
        snapshots.build_research_summary_snapshot(
            created_run,
            name="verify-required",
            source_artifact_ids=[source_artifact.artifact_id],
            require_artifact_verification=True,
        )
    # Without verification, builder still accepts the registered id.
    snapshots.build_research_summary_snapshot(
        created_run,
        name="verify-optional",
        source_artifact_ids=[source_artifact.artifact_id],
        require_artifact_verification=False,
    )


def test_duplicate_name_and_destination_overwrite_rejected(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = snapshots.build_research_summary_snapshot(
        created_run,
        name="dup-name",
        source_artifact_ids=[source_artifact.artifact_id],
    )
    with pytest.raises(SnapshotAlreadyExistsError):
        snapshots.build_research_summary_snapshot(
            created_run,
            name="dup-name",
            source_artifact_ids=[source_artifact.artifact_id],
        )

    dest = run_registry.storage.resolve_run_relative_path(created_run, first.relative_path)
    # Force a colliding destination path by patching filename helper.
    monkeypatch.setattr(
        "app.intelligence.snapshot_registry._snapshot_filename",
        lambda name, snapshot_id: Path(first.relative_path).name,
    )
    with pytest.raises(SnapshotAlreadyExistsError):
        snapshots.build_research_summary_snapshot(
            created_run,
            name="other-name",
            source_artifact_ids=[source_artifact.artifact_id],
        )
    assert dest.is_file()


@pytest.mark.parametrize(
    "status",
    [
        ResearchRunStatus.CREATED,
        ResearchRunStatus.RUNNING,
        ResearchRunStatus.VALIDATED,
    ],
)
def test_writable_statuses_allow_snapshot_creation(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
    status: ResearchRunStatus,
) -> None:
    run_id = run_registry.create_run(run_type=ResearchRunType.GENERAL).run.run_id
    if status == ResearchRunStatus.RUNNING:
        run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
    elif status == ResearchRunStatus.VALIDATED:
        run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
        run_registry.update_status(run_id, ResearchRunStatus.VALIDATED)
    art = artifacts.register_json_artifact(
        run_id,
        name=f"src-{status.value.lower()}",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"status": status.value},
    )
    registry = ResearchSnapshotRegistry(run_registry, artifact_registry=artifacts)
    ref = registry.build_research_summary_snapshot(
        run_id,
        name=f"snap-{status.value.lower()}",
        source_artifact_ids=[art.artifact_id],
    )
    assert ref.name.startswith("snap-")


def test_published_failed_archived_reject_snapshot_creation(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
) -> None:
    published = run_registry.create_run(run_type=ResearchRunType.FACTOR)
    run_id = published.run.run_id
    art = artifacts.register_json_artifact(
        run_id,
        name="pub-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"x": 1},
    )
    run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
    run_registry.update_status(run_id, ResearchRunStatus.VALIDATED)
    run_registry.publish_run(run_id)
    snaps = ResearchSnapshotRegistry(run_registry, artifact_registry=artifacts)
    with pytest.raises(InvalidRunTransitionError):
        snaps.build_research_summary_snapshot(
            run_id,
            name="after-publish",
            source_artifact_ids=[art.artifact_id],
        )

    failed = run_registry.create_run(run_type=ResearchRunType.TREND)
    f_art = artifacts.register_json_artifact(
        failed.run.run_id,
        name="fail-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"x": 1},
    )
    run_registry.mark_failed(failed.run.run_id, "boom")
    with pytest.raises(InvalidRunTransitionError):
        snaps.build_signal_snapshot(
            failed.run.run_id,
            name="after-fail",
            source_artifact_ids=[f_art.artifact_id],
            signals=[],
        )

    archived = run_registry.create_run(run_type=ResearchRunType.GENERAL)
    a_art = artifacts.register_json_artifact(
        archived.run.run_id,
        name="arch-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"x": 1},
    )
    run_registry.mark_failed(archived.run.run_id, "x")
    run_registry.archive_run(archived.run.run_id)
    with pytest.raises(InvalidRunTransitionError):
        snaps.build_research_summary_snapshot(
            archived.run.run_id,
            name="after-archive",
            source_artifact_ids=[a_art.artifact_id],
        )


def test_get_list_by_name_and_id(
    snapshots: ResearchSnapshotRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    ref = snapshots.build_research_summary_snapshot(
        created_run,
        name="lookup-me",
        source_artifact_ids=[source_artifact.artifact_id],
    )
    assert snapshots.get_snapshot(created_run, "lookup-me").snapshot_id == ref.snapshot_id
    assert snapshots.get_snapshot(created_run, ref.snapshot_id).name == "lookup-me"
    assert len(snapshots.list_snapshots(created_run)) == 1
    with pytest.raises(SnapshotNotFoundError):
        snapshots.get_snapshot(created_run, "missing")


def test_checksum_size_and_verification(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    ref = build_signal_snapshot(
        snapshots,
        created_run,
        name="signal-one",
        source_artifact_ids=[source_artifact.artifact_id],
        signals=[
            SignalRecord(
                symbol="AAPL",
                signal_name="mom",
                direction=SignalDirection.STRONG_POSITIVE,
                score=None,
                confidence=0.8,
                evidence_artifact_ids=[source_artifact.artifact_id],
            ),
            SignalRecord(
                symbol="MSFT",
                signal_name="mom",
                direction=SignalDirection.NEGATIVE,
            ),
        ],
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    payload = path.read_bytes()
    assert ref.checksum == hashlib.sha256(payload).hexdigest()
    assert ref.size_bytes == len(payload)
    assert calculate_sha256(path) == ref.checksum

    ok = snapshots.verify_snapshot(created_run, ref.snapshot_id)
    assert ok.valid is True
    assert ok.checksum_matches is True
    assert ok.size_matches is True
    assert ok.errors == []

    path.write_bytes(payload + b" ")
    bad = snapshots.verify_snapshot(created_run, "signal-one")
    assert bad.valid is False
    assert bad.checksum_matches is False
    # verification is read-only
    stored = snapshots.get_snapshot(created_run, "signal-one")
    assert stored.checksum == ref.checksum


def test_verify_missing_snapshot_file(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
) -> None:
    ref = snapshots.build_research_summary_snapshot(
        created_run,
        name="will-delete",
        source_artifact_ids=[source_artifact.artifact_id],
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    path.unlink()
    result = snapshots.verify_snapshot(created_run, ref.name)
    assert result.exists is False
    assert result.valid is False
    assert "missing" in " ".join(result.errors).lower()


def test_manifest_write_failure_rolls_back_new_snapshot(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    source_artifact: ArtifactReference,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = snapshots.build_research_summary_snapshot(
        created_run,
        name="keep-snap",
        source_artifact_ids=[source_artifact.artifact_id],
    )
    first_path = run_registry.storage.resolve_run_relative_path(
        created_run, first.relative_path
    )
    assert first_path.is_file()

    original = run_registry._write_manifest

    def boom(manifest: Any) -> None:
        raise IntelligenceStorageError("simulated manifest failure")

    monkeypatch.setattr(run_registry, "_write_manifest", boom)
    with pytest.raises(IntelligenceStorageError):
        snapshots.build_research_summary_snapshot(
            created_run,
            name="rollback-snap",
            source_artifact_ids=[source_artifact.artifact_id],
        )

    monkeypatch.setattr(run_registry, "_write_manifest", original)
    remaining = snapshots.list_snapshots(created_run)
    assert [item.name for item in remaining] == ["keep-snap"]
    assert first_path.is_file()
    snap_dir = run_registry.storage.snapshots_dir(created_run)
    leftovers = [p for p in snap_dir.iterdir() if p.is_file() and "rollback" in p.name]
    assert leftovers == []


def test_manifest_round_trip_and_artifact_alias(
    snapshots: ResearchSnapshotRegistry,
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> None:
    # Compatibility alias still constructs the same model.
    assert ArtifactReference is not None
    art = artifacts.register_json_artifact(
        created_run,
        name="alias-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"ok": True},
        metadata={"source": "unit-test"},
    )
    assert isinstance(art, ArtifactReference)

    build_research_summary_snapshot(
        snapshots,
        created_run,
        name="round-trip-snap",
        source_artifact_ids=[art.artifact_id],
        research_title="Round trip",
        validation_status=ValidationStatus.PASSED,
        limitations=[SnapshotLimitation(code="n", statement="Demo only")],
        metadata={"publisher": "phase-4.3-test"},
    )
    original = run_registry.get_run(created_run)
    restored = manifest_from_dict(manifest_to_dict(original))
    assert len(restored.snapshots) == 1
    assert restored.snapshots[0].name == "round-trip-snap"
    assert restored.snapshots[0].source_artifact_ids == [art.artifact_id]
    assert restored.snapshots[0].metadata == {"publisher": "phase-4.3-test"}
    assert restored.artifacts[0].checksum == original.artifacts[0].checksum
