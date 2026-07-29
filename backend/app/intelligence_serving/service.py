"""Read-only IntelligenceService (Phase 4.5).

Composes registry reads and publication visibility. Never builds snapshots,
mutates manifests, or touches builders.
"""

from __future__ import annotations

from typing import Optional

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.errors import (
    IntelligenceStorageError,
    InvalidSnapshotError,
    ManifestValidationError,
    RunNotFoundError,
    SnapshotIntegrityError,
    SnapshotNotFoundError,
)
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ResearchRunManifest,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotType,
    is_valid_run_id,
)
from app.intelligence.snapshot_registry import ResearchSnapshotRegistry
from app.intelligence_serving.dto import (
    ArtifactListDTO,
    ResearchRunDetailDTO,
    RunListDTO,
    SnapshotContentDTO,
    SnapshotListDTO,
)
from app.intelligence_serving.errors import (
    IntelligenceStorageServingError,
    InvalidIntelligenceQueryError,
    InvalidRunIdError,
    InvalidSnapshotTypeError,
    LatestPointerInvalidError,
    LatestPublishedRunNotFoundError,
    ManifestValidationServingError,
    RunNotFoundServingError,
    RunNotPublishedError,
    SnapshotContentInvalidError,
    SnapshotIntegrityServingError,
    SnapshotNotFoundServingError,
)
from app.intelligence_serving.mappers import (
    to_artifact_reference_dto,
    to_run_detail_dto,
    to_run_summary_dto,
    to_snapshot_content_dto,
    to_snapshot_reference_dto,
)

# Phase 4.5 consumer visibility: only currently PUBLISHED runs.
# ARCHIVED is terminal and not documented as publicly readable — excluded.
_CONSUMER_VISIBLE = frozenset({ResearchRunStatus.PUBLISHED})


class IntelligenceService:
    """Read-only query façade over intelligence registries."""

    def __init__(
        self,
        run_registry: ResearchRunRegistry,
        artifact_registry: ResearchArtifactRegistry,
        snapshot_registry: ResearchSnapshotRegistry,
    ) -> None:
        self._runs = run_registry
        self._artifacts = artifact_registry
        self._snapshots = snapshot_registry

    @staticmethod
    def is_consumer_visible(manifest: ResearchRunManifest) -> bool:
        return manifest.run.status in _CONSUMER_VISIBLE

    def list_runs(
        self,
        *,
        status: Optional[ResearchRunStatus] = None,
        run_type: Optional[ResearchRunType] = None,
    ) -> RunListDTO:
        if status is not None and status not in _CONSUMER_VISIBLE:
            raise InvalidIntelligenceQueryError(
                "status filter must be a consumer-visible status "
                f"(allowed: {[s.value for s in _CONSUMER_VISIBLE]})"
            )
        try:
            manifests = self._runs.list_runs(
                status=ResearchRunStatus.PUBLISHED,
                run_type=run_type,
            )
        except IntelligenceStorageError as exc:
            raise IntelligenceStorageServingError(str(exc)) from exc
        except ManifestValidationError as exc:
            raise ManifestValidationServingError(str(exc)) from exc

        items = [to_run_summary_dto(item) for item in manifests]
        return RunListDTO(items=items, count=len(items))

    def get_latest_run(self) -> ResearchRunDetailDTO:
        try:
            manifest = self._runs.get_latest_published_run()
        except IntelligenceStorageError as exc:
            message = str(exc)
            if "latest.json" in message.lower() or "points to" in message.lower():
                raise LatestPointerInvalidError(message) from exc
            raise IntelligenceStorageServingError(message) from exc
        except ManifestValidationError as exc:
            raise ManifestValidationServingError(str(exc)) from exc

        if manifest is None:
            raise LatestPublishedRunNotFoundError("no latest published research run")
        if not self.is_consumer_visible(manifest):
            raise LatestPointerInvalidError(
                f"latest.json points to non-consumer-visible run "
                f"{manifest.run.run_id} with status {manifest.run.status.value}"
            )
        return to_run_detail_dto(manifest)

    def get_run(self, run_id: str) -> ResearchRunDetailDTO:
        manifest = self._require_visible_run(run_id)
        return to_run_detail_dto(manifest)

    def list_artifacts(self, run_id: str) -> ArtifactListDTO:
        self._require_visible_run(run_id)
        try:
            refs = self._artifacts.list_artifacts(run_id)
        except RunNotFoundError as exc:
            raise RunNotFoundServingError(str(exc), run_id=run_id) from exc
        except IntelligenceStorageError as exc:
            raise IntelligenceStorageServingError(str(exc), run_id=run_id) from exc
        items = [to_artifact_reference_dto(item) for item in refs]
        return ArtifactListDTO(run_id=run_id, items=items, count=len(items))

    def list_snapshots(
        self,
        run_id: str,
        *,
        snapshot_type: Optional[ResearchSnapshotType] = None,
    ) -> SnapshotListDTO:
        self._require_visible_run(run_id)
        try:
            refs = self._snapshots.list_snapshots(run_id)
        except RunNotFoundError as exc:
            raise RunNotFoundServingError(str(exc), run_id=run_id) from exc
        except IntelligenceStorageError as exc:
            raise IntelligenceStorageServingError(str(exc), run_id=run_id) from exc

        if snapshot_type is not None:
            refs = [item for item in refs if item.snapshot_type == snapshot_type]
        items = [to_snapshot_reference_dto(item) for item in refs]
        return SnapshotListDTO(run_id=run_id, items=items, count=len(items))

    def get_snapshot_content(
        self,
        run_id: str,
        snapshot_name_or_id: str,
        *,
        verify: bool = False,
    ) -> SnapshotContentDTO:
        self._require_visible_run(run_id)
        try:
            reference = self._snapshots.get_snapshot(run_id, snapshot_name_or_id)
            content = self._snapshots.read_snapshot(
                run_id,
                snapshot_name_or_id,
                verify=verify,
            )
        except SnapshotNotFoundError as exc:
            raise SnapshotNotFoundServingError(
                str(exc),
                run_id=run_id,
                resource_id=snapshot_name_or_id,
            ) from exc
        except SnapshotIntegrityError as exc:
            raise SnapshotIntegrityServingError(
                str(exc),
                run_id=run_id,
                resource_id=snapshot_name_or_id,
            ) from exc
        except InvalidSnapshotError as exc:
            raise SnapshotContentInvalidError(
                str(exc),
                run_id=run_id,
                resource_id=snapshot_name_or_id,
            ) from exc
        except RunNotFoundError as exc:
            raise RunNotFoundServingError(str(exc), run_id=run_id) from exc
        except IntelligenceStorageError as exc:
            raise IntelligenceStorageServingError(str(exc), run_id=run_id) from exc
        except ManifestValidationError as exc:
            raise ManifestValidationServingError(str(exc), run_id=run_id) from exc

        return to_snapshot_content_dto(run_id, reference, content)

    def _require_visible_run(self, run_id: str) -> ResearchRunManifest:
        if not is_valid_run_id(run_id):
            raise InvalidRunIdError(f"invalid run_id: {run_id!r}", run_id=run_id)
        try:
            manifest = self._runs.get_run(run_id)
        except RunNotFoundError as exc:
            raise RunNotFoundServingError(str(exc), run_id=run_id) from exc
        except IntelligenceStorageError as exc:
            # Storage may raise for invalid ids that slip past; keep typed.
            raise IntelligenceStorageServingError(str(exc), run_id=run_id) from exc
        except ManifestValidationError as exc:
            raise ManifestValidationServingError(str(exc), run_id=run_id) from exc

        if not self.is_consumer_visible(manifest):
            raise RunNotPublishedError(
                f"research run is not published for consumer access: {run_id}",
                run_id=run_id,
            )
        return manifest


def parse_snapshot_type(raw: Optional[str]) -> Optional[ResearchSnapshotType]:
    """Parse optional snapshot_type query against the real enum."""
    if raw is None or raw == "":
        return None
    try:
        return ResearchSnapshotType(raw)
    except ValueError as exc:
        raise InvalidSnapshotTypeError(
            f"invalid snapshot_type: {raw!r}; "
            f"allowed={[item.value for item in ResearchSnapshotType]}"
        ) from exc
