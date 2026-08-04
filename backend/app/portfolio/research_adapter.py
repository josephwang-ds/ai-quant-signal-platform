"""Phase 4 Intelligence adapter for Portfolio publication (Phase 5.1C)."""

from __future__ import annotations

from typing import Optional, Sequence

from app.intelligence.schemas import ResearchRunStatus
from app.intelligence_serving.errors import (
    IntelligenceServingError,
    InvalidRunIdError,
    ManifestValidationServingError,
    RunNotFoundServingError,
    RunNotPublishedError,
    SnapshotContentInvalidError,
    SnapshotIntegrityServingError,
    SnapshotNotFoundServingError,
)
from app.intelligence_serving.service import IntelligenceService
from app.portfolio.ports import (
    PublishedResearchQueryPort,
    PublishedRunReference,
    PublishedSnapshotReference,
)


class PublishedResearchResolutionError(Exception):
    """Typed failure resolving Published Research evidence for Portfolio admission."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        run_id: Optional[str] = None,
        snapshot_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.run_id = run_id
        self.snapshot_id = snapshot_id


class IntelligencePublishedResearchAdapter:
    """Adapts ``IntelligenceService`` into ``PublishedResearchQueryPort``."""

    def __init__(self, service: IntelligenceService) -> None:
        self._service = service

    def get_published_run(self, run_id: str) -> PublishedRunReference:
        try:
            detail = self._service.get_run(run_id)
        except RunNotFoundServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_FOUND",
                str(exc),
                run_id=run_id,
            ) from exc
        except RunNotPublishedError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_PUBLISHED",
                str(exc),
                run_id=run_id,
            ) from exc
        except InvalidRunIdError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_FOUND",
                str(exc),
                run_id=run_id,
            ) from exc
        except ManifestValidationServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_INTEGRITY_FAILED",
                str(exc),
                run_id=run_id,
            ) from exc
        except IntelligenceServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_INTEGRITY_FAILED",
                str(exc),
                run_id=run_id,
            ) from exc

        if detail.run_id != run_id:
            raise PublishedResearchResolutionError(
                "SOURCE_IDENTITY_MISMATCH",
                "resolved run_id does not match requested source_run_id",
                run_id=run_id,
            )
        if detail.status is not ResearchRunStatus.PUBLISHED:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_PUBLISHED",
                f"research run status is {detail.status.value}, expected PUBLISHED",
                run_id=run_id,
            )
        if detail.published_at is None:
            raise PublishedResearchResolutionError(
                "SOURCE_RUN_NOT_PUBLISHED",
                "published research run is missing published_at",
                run_id=run_id,
            )

        snapshots = [
            PublishedSnapshotReference(
                snapshot_id=item.snapshot_id,
                name=item.name,
                snapshot_type=item.snapshot_type.value,
                schema_version=item.schema_version,
                checksum_algorithm=item.checksum_algorithm,
                checksum=item.checksum,
                size_bytes=item.size_bytes,
                created_at=item.created_at,
                integrity_verified=False,
            )
            for item in detail.snapshots
        ]
        name = detail.notes
        if detail.universe:
            name = detail.universe if name is None else f"{detail.universe}: {name}"

        return PublishedRunReference(
            run_id=detail.run_id,
            publication_status=detail.status.value,
            validation_ok=bool(detail.validation.ok),
            published_at=detail.published_at,
            strategy_or_research_name=name,
            snapshot_references=snapshots,
            source_integrity_status="ok",
            methodology_version=detail.model_version,
            universe=detail.universe,
            notes=detail.notes,
        )

    def list_snapshot_references(
        self,
        run_id: str,
    ) -> Sequence[PublishedSnapshotReference]:
        run = self.get_published_run(run_id)
        return list(run.snapshot_references)

    def verify_snapshot(
        self,
        run_id: str,
        snapshot_id: str,
    ) -> PublishedSnapshotReference:
        # Ensure the run is published before verifying snapshot bytes.
        self.get_published_run(run_id)
        try:
            content = self._service.get_snapshot_content(
                run_id,
                snapshot_id,
                verify=True,
            )
        except SnapshotNotFoundServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_NOT_FOUND",
                str(exc),
                run_id=run_id,
                snapshot_id=snapshot_id,
            ) from exc
        except SnapshotIntegrityServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_INVALID",
                str(exc),
                run_id=run_id,
                snapshot_id=snapshot_id,
            ) from exc
        except SnapshotContentInvalidError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_INVALID",
                str(exc),
                run_id=run_id,
                snapshot_id=snapshot_id,
            ) from exc
        except IntelligenceServingError as exc:
            raise PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_INVALID",
                str(exc),
                run_id=run_id,
                snapshot_id=snapshot_id,
            ) from exc

        reference = content.reference
        if reference.snapshot_id != snapshot_id:
            raise PublishedResearchResolutionError(
                "SOURCE_SNAPSHOT_OWNERSHIP_MISMATCH",
                "resolved snapshot_id does not match requested snapshot",
                run_id=run_id,
                snapshot_id=snapshot_id,
            )
        return PublishedSnapshotReference(
            snapshot_id=reference.snapshot_id,
            name=reference.name,
            snapshot_type=reference.snapshot_type.value,
            schema_version=reference.schema_version,
            checksum_algorithm=reference.checksum_algorithm,
            checksum=reference.checksum,
            size_bytes=reference.size_bytes,
            created_at=reference.created_at,
            integrity_verified=True,
        )


def as_published_research_query_port(
    service: IntelligenceService,
) -> PublishedResearchQueryPort:
    return IntelligencePublishedResearchAdapter(service)
