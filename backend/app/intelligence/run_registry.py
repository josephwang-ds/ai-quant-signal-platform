"""Filesystem-backed research run registry (Phase 4.1)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.intelligence.errors import (
    IntelligenceStorageError,
    InvalidRunTransitionError,
    ManifestValidationError,
    RunAlreadyExistsError,
    RunNotFoundError,
)
from app.intelligence.manifest import (
    apply_status,
    assert_transition_allowed,
    build_new_manifest,
    manifest_from_dict,
    manifest_to_dict,
    validate_manifest,
)
from app.intelligence.schemas import (
    LATEST_POINTER_SCHEMA_VERSION,
    LatestRunPointer,
    ResearchRunManifest,
    ResearchRunStatus,
    ResearchRunType,
    utc_now,
)
from app.intelligence.storage import IntelligenceStorage


class ResearchRunRegistry:
    """Register completed research runs and store immutable run manifests."""

    def __init__(self, storage: IntelligenceStorage | None = None) -> None:
        self._storage = storage or IntelligenceStorage()

    @property
    def storage(self) -> IntelligenceStorage:
        return self._storage

    def create_run(
        self,
        *,
        run_type: ResearchRunType,
        dataset_version: str | None = None,
        feature_version: str | None = None,
        model_version: str | None = None,
        git_commit: str | None = None,
        environment: str | None = None,
        random_seed: int | None = None,
        training_window: str | None = None,
        prediction_window: str | None = None,
        universe: str | None = None,
        notes: str | None = None,
        now: datetime | None = None,
    ) -> ResearchRunManifest:
        """Create a run directory and write the initial CREATED manifest."""
        manifest = build_new_manifest(
            run_type=run_type,
            status=ResearchRunStatus.CREATED,
            dataset_version=dataset_version,
            feature_version=feature_version,
            model_version=model_version,
            git_commit=git_commit,
            environment=environment,
            random_seed=random_seed,
            training_window=training_window,
            prediction_window=prediction_window,
            universe=universe,
            notes=notes,
            now=now,
        )
        run_id = manifest.run.run_id
        if self._storage.run_exists(run_id):
            raise RunAlreadyExistsError(f"run already exists: {run_id}")
        self._storage.create_run_directory(run_id)
        self._write_manifest(manifest)
        return manifest

    def get_run(self, run_id: str) -> ResearchRunManifest:
        path = self._storage.manifest_path(run_id)
        if not path.is_file():
            raise RunNotFoundError(f"research run not found: {run_id}")
        payload = self._storage.read_json(path)
        if not isinstance(payload, dict):
            raise IntelligenceStorageError(f"corrupt manifest for run: {run_id}")
        return validate_manifest(
            manifest_from_dict(payload),
            expected_run_id=run_id,
        )

    def list_runs(
        self,
        *,
        status: ResearchRunStatus | None = None,
        run_type: ResearchRunType | None = None,
    ) -> list[ResearchRunManifest]:
        manifests: list[ResearchRunManifest] = []
        for run_id in self._storage.list_run_ids():
            try:
                manifest = self.get_run(run_id)
            except (RunNotFoundError, ManifestValidationError, IntelligenceStorageError):
                continue
            if status is not None and manifest.run.status != status:
                continue
            if run_type is not None and manifest.run.run_type != run_type:
                continue
            manifests.append(manifest)
        manifests.sort(key=lambda item: item.run.created_at)
        return manifests

    def update_status(
        self,
        run_id: str,
        status: ResearchRunStatus,
        *,
        error: str | None = None,
        now: datetime | None = None,
    ) -> ResearchRunManifest:
        current = self.get_run(run_id)
        if current.run.status == ResearchRunStatus.PUBLISHED and status != ResearchRunStatus.ARCHIVED:
            raise InvalidRunTransitionError(
                "published manifests are immutable except transition to ARCHIVED"
            )
        if current.run.status == ResearchRunStatus.ARCHIVED:
            raise InvalidRunTransitionError("ARCHIVED runs cannot transition further")
        updated = apply_status(current, status, error=error, now=now)
        self._write_manifest(updated)
        return updated

    def mark_failed(self, run_id: str, error: str) -> ResearchRunManifest:
        if not error or not str(error).strip():
            raise ManifestValidationError("FAILED runs must contain at least one error")
        return self.update_status(
            run_id,
            ResearchRunStatus.FAILED,
            error=str(error).strip(),
        )

    def publish_run(self, run_id: str, *, now: datetime | None = None) -> ResearchRunManifest:
        current = self.get_run(run_id)
        if current.run.status != ResearchRunStatus.VALIDATED:
            raise InvalidRunTransitionError(
                f"publish requires VALIDATED status; found {current.run.status.value}"
            )
        assert_transition_allowed(current.run.status, ResearchRunStatus.PUBLISHED)
        stamp = now or utc_now()
        published = apply_status(current, ResearchRunStatus.PUBLISHED, now=stamp)
        # Persist the immutable published manifest first; only then update the pointer.
        self._write_manifest(published)
        pointer = LatestRunPointer(
            schema_version=LATEST_POINTER_SCHEMA_VERSION,
            run_id=run_id,
            manifest_path=self._storage.relative_manifest_path(run_id),
            published_at=published.run.published_at or stamp,
        )
        self._storage.write_json_atomic(
            self._storage.latest_path,
            pointer.model_dump(mode="json"),
        )
        return published

    def get_latest_published_run(self) -> ResearchRunManifest | None:
        latest_path = self._storage.latest_path
        if not latest_path.is_file():
            return None
        try:
            payload = self._storage.read_json(latest_path)
        except (RunNotFoundError, IntelligenceStorageError):
            return None
        if not isinstance(payload, dict):
            raise IntelligenceStorageError("latest.json is corrupt")
        try:
            pointer = LatestRunPointer.model_validate(payload)
        except Exception as exc:
            raise IntelligenceStorageError("latest.json pointer is invalid") from exc

        try:
            manifest = self.get_run(pointer.run_id)
        except RunNotFoundError as exc:
            raise IntelligenceStorageError(
                f"latest.json points to missing run: {pointer.run_id}"
            ) from exc

        if manifest.run.status not in {
            ResearchRunStatus.PUBLISHED,
            ResearchRunStatus.ARCHIVED,
        }:
            raise IntelligenceStorageError(
                f"latest.json points to non-published run: {pointer.run_id}"
            )
        if manifest.run.status == ResearchRunStatus.ARCHIVED and manifest.run.published_at is None:
            raise IntelligenceStorageError(
                f"latest.json points to archived non-published run: {pointer.run_id}"
            )
        return manifest

    def archive_run(self, run_id: str, *, now: datetime | None = None) -> ResearchRunManifest:
        return self.update_status(run_id, ResearchRunStatus.ARCHIVED, now=now)

    def _write_manifest(self, manifest: ResearchRunManifest) -> None:
        validate_manifest(manifest, expected_run_id=manifest.run.run_id)
        path = self._storage.manifest_path(manifest.run.run_id)
        self._storage.write_json_atomic(path, manifest_to_dict(manifest))
