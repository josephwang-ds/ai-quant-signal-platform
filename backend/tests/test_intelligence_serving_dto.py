"""Phase 4.5 — DTO projection tests."""

from __future__ import annotations

from datetime import datetime, timezone

from app.intelligence.schemas import (
    ResearchArtifactReference,
    ResearchArtifactType,
    ResearchRunManifest,
    ResearchRunMetadata,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
    ResearchSnapshotType,
    ValidationRecord,
)
from app.intelligence.snapshot_contracts import (
    ResearchSummarySnapshot,
    SignalDirection,
    SignalRecord,
    SignalSnapshot,
    SnapshotContentProvenance,
    SnapshotFinding,
)
from app.intelligence_serving.mappers import (
    to_artifact_reference_dto,
    to_run_detail_dto,
    to_run_summary_dto,
    to_snapshot_content_dto,
    to_snapshot_reference_dto,
)


def _stamp() -> datetime:
    return datetime(2026, 7, 28, 12, 0, 0, tzinfo=timezone.utc)


def _manifest() -> ResearchRunManifest:
    stamp = _stamp()
    artifact = ResearchArtifactReference(
        artifact_id="artifact_aaaaaaaa",
        name="evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        relative_path="artifacts/evidence__aaaaaaaa.json",
        checksum="a" * 64,
        size_bytes=12,
        created_at=stamp,
        metadata={"producer": "unit-test", "note": "internal"},
    )
    snapshot = ResearchSnapshotReference(
        snapshot_id="snapshot_bbbbbbbb",
        name="summary",
        snapshot_type=ResearchSnapshotType.RESEARCH_SUMMARY,
        relative_path="snapshots/summary__bbbbbbbb.json",
        checksum="b" * 64,
        size_bytes=20,
        created_at=stamp,
        source_artifact_ids=["artifact_aaaaaaaa"],
        metadata={"publisher": "unit-test"},
    )
    return ResearchRunManifest(
        run=ResearchRunMetadata(
            run_id="run_20260728T120000Z_abcd1234",
            run_type=ResearchRunType.FACTOR,
            status=ResearchRunStatus.PUBLISHED,
            created_at=stamp,
            updated_at=stamp,
            published_at=stamp,
            universe="US Liquid 31",
            dataset_version="ds-1",
            feature_version=None,
            model_version=None,
            git_commit="deadbeef",
            generator="test",
            environment="python/3.9",
            notes="demo",
        ),
        artifacts=[artifact],
        snapshots=[snapshot],
        checksums={artifact.artifact_id: artifact.checksum},
        validation=ValidationRecord(ok=True, checks=["ok"]),
        errors=[],
    )


def test_run_summary_and_detail_mapping() -> None:
    manifest = _manifest()
    summary = to_run_summary_dto(manifest)
    assert summary.run_id == manifest.run.run_id
    assert summary.run_type == ResearchRunType.FACTOR
    assert summary.status == ResearchRunStatus.PUBLISHED
    assert summary.artifact_count == 1
    assert summary.snapshot_count == 1
    assert summary.universe == "US Liquid 31"

    detail = to_run_detail_dto(manifest)
    assert detail.generator == "test"
    assert detail.validation.ok is True
    assert detail.artifacts[0].artifact_id == "artifact_aaaaaaaa"
    assert detail.snapshots[0].snapshot_id == "snapshot_bbbbbbbb"
    dumped = detail.model_dump(mode="json")
    assert "relative_path" not in dumped["artifacts"][0]
    assert "relative_path" not in dumped["snapshots"][0]
    assert "metadata" not in dumped["artifacts"][0]
    assert "metadata" not in dumped["snapshots"][0]


def test_artifact_and_snapshot_path_and_metadata_redaction() -> None:
    manifest = _manifest()
    art = to_artifact_reference_dto(manifest.artifacts[0])
    snap = to_snapshot_reference_dto(manifest.snapshots[0])
    art_dump = art.model_dump()
    snap_dump = snap.model_dump()
    assert "relative_path" not in art_dump
    assert "metadata" not in art_dump
    assert "relative_path" not in snap_dump
    assert "metadata" not in snap_dump
    assert snap.source_artifact_ids == ["artifact_aaaaaaaa"]


def test_enum_and_datetime_serialization() -> None:
    summary = to_run_summary_dto(_manifest())
    payload = summary.model_dump(mode="json")
    assert payload["status"] == "PUBLISHED"
    assert payload["run_type"] == "FACTOR"
    # Preserve repository Pydantic convention (+00:00 is acceptable).
    assert "2026-07-28T12:00:00" in payload["created_at"]
    assert payload["created_at"].endswith("+00:00") or payload["created_at"].endswith("Z")


def test_typed_snapshot_content_dto() -> None:
    stamp = _stamp()
    ref = _manifest().snapshots[0]
    content = ResearchSummarySnapshot(
        generated_at=stamp,
        research_title="Title",
        key_findings=[SnapshotFinding(statement="finding")],
        provenance=SnapshotContentProvenance(
            source_artifact_ids=["artifact_aaaaaaaa"],
            builder="test",
        ),
    )
    dto = to_snapshot_content_dto("run_20260728T120000Z_abcd1234", ref, content)
    dumped = dto.model_dump(mode="json")
    assert dumped["run_id"].startswith("run_")
    assert dumped["reference"]["name"] == "summary"
    assert "relative_path" not in dumped["reference"]
    assert dumped["content"]["research_title"] == "Title"
    assert "schema_version" in dumped["content"]

    signal = SignalSnapshot(
        generated_at=stamp,
        signals=[
            SignalRecord(
                symbol="AAPL",
                signal_name="mom",
                direction=SignalDirection.POSITIVE,
            )
        ],
        provenance=SnapshotContentProvenance(
            source_artifact_ids=["artifact_aaaaaaaa"],
            builder="test",
        ),
    )
    signal_ref = ResearchSnapshotReference(
        snapshot_id="snapshot_cccccccc",
        name="signals",
        snapshot_type=ResearchSnapshotType.SIGNAL,
        relative_path="snapshots/signals__cccccccc.json",
        checksum="c" * 64,
        size_bytes=10,
        created_at=stamp,
        source_artifact_ids=["artifact_aaaaaaaa"],
    )
    signal_dto = to_snapshot_content_dto(
        "run_20260728T120000Z_abcd1234", signal_ref, signal
    )
    assert signal_dto.content.signals[0].direction == SignalDirection.POSITIVE
