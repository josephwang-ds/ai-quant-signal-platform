"""Registry/contract → public DTO projection (Phase 4.5).

Metadata on artifact/snapshot references is omitted from public DTOs: existing
validation rejects some domain keys but does not guarantee public-safe values
(paths, secrets, unrestricted producer notes).
"""

from __future__ import annotations

from app.intelligence.schemas import (
    ResearchArtifactReference,
    ResearchRunManifest,
    ResearchSnapshotReference,
    ValidationRecord,
)
from app.intelligence.snapshot_contracts import ResearchSummarySnapshot, SignalSnapshot
from app.intelligence_serving.dto import (
    ArtifactReferenceDTO,
    ResearchRunDetailDTO,
    ResearchRunSummaryDTO,
    SnapshotContentDTO,
    SnapshotReferenceDTO,
    ValidationRecordDTO,
)


def to_artifact_reference_dto(ref: ResearchArtifactReference) -> ArtifactReferenceDTO:
    return ArtifactReferenceDTO(
        artifact_id=ref.artifact_id,
        name=ref.name,
        artifact_type=ref.artifact_type,
        schema_version=ref.schema_version,
        media_type=ref.media_type,
        checksum_algorithm=ref.checksum_algorithm,
        checksum=ref.checksum,
        size_bytes=ref.size_bytes,
        row_count=ref.row_count,
        created_at=ref.created_at,
    )


def to_snapshot_reference_dto(ref: ResearchSnapshotReference) -> SnapshotReferenceDTO:
    return SnapshotReferenceDTO(
        snapshot_id=ref.snapshot_id,
        name=ref.name,
        snapshot_type=ref.snapshot_type,
        schema_version=ref.schema_version,
        media_type=ref.media_type,
        checksum_algorithm=ref.checksum_algorithm,
        checksum=ref.checksum,
        size_bytes=ref.size_bytes,
        created_at=ref.created_at,
        as_of=ref.as_of,
        source_artifact_ids=list(ref.source_artifact_ids),
    )


def to_validation_dto(record: ValidationRecord) -> ValidationRecordDTO:
    return ValidationRecordDTO(ok=record.ok, checks=list(record.checks))


def to_run_summary_dto(manifest: ResearchRunManifest) -> ResearchRunSummaryDTO:
    run = manifest.run
    return ResearchRunSummaryDTO(
        run_id=run.run_id,
        run_type=run.run_type,
        status=run.status,
        created_at=run.created_at,
        updated_at=run.updated_at,
        published_at=run.published_at,
        universe=run.universe,
        dataset_version=run.dataset_version,
        feature_version=run.feature_version,
        model_version=run.model_version,
        git_commit=run.git_commit,
        artifact_count=len(manifest.artifacts),
        snapshot_count=len(manifest.snapshots),
    )


def to_run_detail_dto(manifest: ResearchRunManifest) -> ResearchRunDetailDTO:
    summary = to_run_summary_dto(manifest)
    run = manifest.run
    return ResearchRunDetailDTO(
        **summary.model_dump(),
        generator=run.generator,
        environment=run.environment,
        random_seed=run.random_seed,
        training_window=run.training_window,
        prediction_window=run.prediction_window,
        notes=run.notes,
        validation=to_validation_dto(manifest.validation),
        errors=list(manifest.errors),
        artifacts=[to_artifact_reference_dto(item) for item in manifest.artifacts],
        snapshots=[to_snapshot_reference_dto(item) for item in manifest.snapshots],
    )


def to_snapshot_content_dto(
    run_id: str,
    reference: ResearchSnapshotReference,
    content: ResearchSummarySnapshot | SignalSnapshot,
) -> SnapshotContentDTO:
    return SnapshotContentDTO(
        run_id=run_id,
        reference=to_snapshot_reference_dto(reference),
        content=content,
    )
