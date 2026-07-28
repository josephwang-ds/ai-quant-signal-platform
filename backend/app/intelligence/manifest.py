"""Build and validate research-run manifests.

Reuses repository git/runtime resolution from ``research_reproducibility``
without replacing its evidence-artifact manifest contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.intelligence.errors import ManifestValidationError
from app.intelligence.schemas import (
    MANIFEST_SCHEMA_VERSION,
    ResearchArtifactReference,
    ResearchRunManifest,
    ResearchRunMetadata,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
    ValidationRecord,
    generate_run_id,
    is_valid_artifact_id,
    utc_now,
)
from app.research_reproducibility import UNAVAILABLE, resolve_git_commit_sha, resolve_runtime_version

GENERATOR_ID = "intelligence-run-registry/phase-4.1"

ALLOWED_TRANSITIONS: dict[ResearchRunStatus, frozenset[ResearchRunStatus]] = {
    ResearchRunStatus.CREATED: frozenset(
        {ResearchRunStatus.RUNNING, ResearchRunStatus.FAILED}
    ),
    ResearchRunStatus.RUNNING: frozenset(
        {ResearchRunStatus.VALIDATED, ResearchRunStatus.FAILED}
    ),
    ResearchRunStatus.VALIDATED: frozenset(
        {ResearchRunStatus.PUBLISHED, ResearchRunStatus.FAILED}
    ),
    ResearchRunStatus.PUBLISHED: frozenset({ResearchRunStatus.ARCHIVED}),
    ResearchRunStatus.FAILED: frozenset({ResearchRunStatus.ARCHIVED}),
    ResearchRunStatus.ARCHIVED: frozenset(),
}


def _optional_git_commit(explicit: str | None = None) -> str | None:
    if explicit is not None:
        value = explicit.strip()
        if not value or value.lower() in {"unknown", "unavailable", "none"}:
            return None
        return value
    resolved = resolve_git_commit_sha()
    if not resolved or resolved == UNAVAILABLE or resolved.lower() in {"unknown", "none"}:
        return None
    return resolved


def _is_unsafe_relative_path(path: str) -> bool:
    if not path or path.strip() != path:
        return True
    candidate = Path(path)
    if candidate.is_absolute():
        return True
    if ".." in candidate.parts:
        return True
    if path.startswith(("/", "\\")):
        return True
    return False


def assert_transition_allowed(
    current: ResearchRunStatus,
    target: ResearchRunStatus,
) -> None:
    from app.intelligence.errors import InvalidRunTransitionError

    if current == target:
        raise InvalidRunTransitionError(
            f"status is already {current.value}; no-op transitions are rejected"
        )
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise InvalidRunTransitionError(
            f"invalid research-run transition: {current.value} -> {target.value}"
        )


def validate_manifest(
    manifest: ResearchRunManifest,
    *,
    expected_run_id: str | None = None,
) -> ResearchRunManifest:
    """Validate registry-level consistency. Raises ManifestValidationError."""
    run = manifest.run
    errors: list[str] = []

    if expected_run_id is not None and run.run_id != expected_run_id:
        errors.append(
            f"run_id mismatch: manifest has {run.run_id!r}, directory expects {expected_run_id!r}"
        )

    if run.created_at.tzinfo is None or run.updated_at.tzinfo is None:
        errors.append("created_at and updated_at must be timezone-aware")
    elif run.created_at.astimezone(timezone.utc) > run.updated_at.astimezone(timezone.utc):
        errors.append("created_at must not be after updated_at")

    if run.published_at is not None and run.status not in {
        ResearchRunStatus.PUBLISHED,
        ResearchRunStatus.ARCHIVED,
    }:
        errors.append("published_at must be null unless status is PUBLISHED or ARCHIVED")

    if run.status == ResearchRunStatus.PUBLISHED and run.published_at is None:
        errors.append("PUBLISHED runs require published_at")

    if run.status == ResearchRunStatus.ARCHIVED and run.published_at is None:
        # Archived from FAILED never published — published_at may stay null.
        pass

    if run.status == ResearchRunStatus.FAILED and not manifest.errors:
        errors.append("FAILED runs must contain at least one error")

    artifact_names: set[str] = set()
    artifact_ids: set[str] = set()
    for artifact in manifest.artifacts:
        if artifact.name in artifact_names:
            errors.append(f"duplicate artifact name: {artifact.name!r}")
        artifact_names.add(artifact.name)
        if artifact.artifact_id in artifact_ids:
            errors.append(f"duplicate artifact_id: {artifact.artifact_id!r}")
        artifact_ids.add(artifact.artifact_id)
        if _is_unsafe_relative_path(artifact.relative_path):
            errors.append(f"unsafe artifact relative_path: {artifact.relative_path!r}")
        elif not artifact.relative_path.startswith("artifacts/"):
            errors.append(
                f"artifact relative_path must live under artifacts/: {artifact.relative_path!r}"
            )
        expected = manifest.checksums.get(artifact.artifact_id)
        if expected is not None and expected != artifact.checksum:
            errors.append(
                f"checksums map disagrees with artifact {artifact.artifact_id!r}"
            )

    # Top-level checksums keys must refer to registered artifact ids only.
    for key in manifest.checksums:
        if key not in artifact_ids:
            errors.append(f"orphan checksums entry for unknown artifact_id: {key!r}")

    snapshot_names: set[str] = set()
    snapshot_ids: set[str] = set()
    for snapshot in manifest.snapshots:
        if snapshot.name in snapshot_names:
            errors.append(f"duplicate snapshot name: {snapshot.name!r}")
        snapshot_names.add(snapshot.name)
        if snapshot.snapshot_id in snapshot_ids:
            errors.append(f"duplicate snapshot_id: {snapshot.snapshot_id!r}")
        snapshot_ids.add(snapshot.snapshot_id)
        if _is_unsafe_relative_path(snapshot.relative_path):
            errors.append(f"unsafe snapshot relative_path: {snapshot.relative_path!r}")
        elif not snapshot.relative_path.startswith("snapshots/"):
            errors.append(
                f"snapshot relative_path must live under snapshots/: {snapshot.relative_path!r}"
            )
        for source_id in snapshot.source_artifact_ids:
            if not is_valid_artifact_id(source_id):
                errors.append(f"invalid snapshot source artifact_id: {source_id!r}")
            elif source_id not in artifact_ids:
                errors.append(
                    f"snapshot {snapshot.snapshot_id!r} references unknown artifact {source_id!r}"
                )

    if errors:
        raise ManifestValidationError("; ".join(errors))
    return manifest


def build_new_manifest(
    *,
    run_type: ResearchRunType,
    run_id: str | None = None,
    status: ResearchRunStatus = ResearchRunStatus.CREATED,
    dataset_version: str | None = None,
    feature_version: str | None = None,
    model_version: str | None = None,
    git_commit: str | None = None,
    generator: str | None = GENERATOR_ID,
    environment: str | None = None,
    random_seed: int | None = None,
    training_window: str | None = None,
    prediction_window: str | None = None,
    universe: str | None = None,
    notes: str | None = None,
    artifacts: list[ResearchArtifactReference] | None = None,
    snapshots: list[ResearchSnapshotReference] | None = None,
    checksums: dict[str, str] | None = None,
    validation: ValidationRecord | None = None,
    errors: list[str] | None = None,
    now: datetime | None = None,
) -> ResearchRunManifest:
    """Create an initial typed manifest. Unknown versions stay ``None``."""
    stamp = now or utc_now()
    resolved_id = run_id or generate_run_id(when=stamp)
    resolved_env = environment if environment is not None else resolve_runtime_version()
    metadata = ResearchRunMetadata(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_id=resolved_id,
        run_type=run_type,
        status=status,
        created_at=stamp,
        updated_at=stamp,
        published_at=None,
        dataset_version=dataset_version,
        feature_version=feature_version,
        model_version=model_version,
        git_commit=_optional_git_commit(git_commit),
        generator=generator,
        environment=resolved_env,
        random_seed=random_seed,
        training_window=training_window,
        prediction_window=prediction_window,
        universe=universe,
        notes=notes,
    )
    manifest = ResearchRunManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run=metadata,
        artifacts=list(artifacts or []),
        snapshots=list(snapshots or []),
        checksums=dict(checksums or {}),
        validation=validation
        or ValidationRecord(
            ok=True,
            checks=["registry_manifest_created"],
            details={"phase": "4.1"},
        ),
        errors=list(errors or []),
    )
    return validate_manifest(manifest, expected_run_id=resolved_id)


def apply_status(
    manifest: ResearchRunManifest,
    status: ResearchRunStatus,
    *,
    error: str | None = None,
    now: datetime | None = None,
) -> ResearchRunManifest:
    """Return a new manifest with a validated status transition."""
    assert_transition_allowed(manifest.run.status, status)
    stamp = now or utc_now()
    errors = list(manifest.errors)
    if error:
        errors.append(error)
    if status == ResearchRunStatus.FAILED and not errors:
        raise ManifestValidationError("FAILED runs must contain at least one error")

    published_at = manifest.run.published_at
    if status == ResearchRunStatus.PUBLISHED:
        published_at = stamp
    elif status not in {ResearchRunStatus.PUBLISHED, ResearchRunStatus.ARCHIVED}:
        published_at = None

    # ARCHIVED from FAILED keeps published_at as None; from PUBLISHED keeps it.
    if status == ResearchRunStatus.ARCHIVED:
        published_at = manifest.run.published_at

    updated_run = manifest.run.model_copy(
        update={
            "status": status,
            "updated_at": stamp,
            "published_at": published_at,
        }
    )
    updated = manifest.model_copy(update={"run": updated_run, "errors": errors})
    return validate_manifest(updated, expected_run_id=manifest.run.run_id)


def sync_artifact_checksums(manifest: ResearchRunManifest) -> ResearchRunManifest:
    """Keep top-level checksums keyed by artifact_id in sync with artifact refs."""
    mapping = {
        artifact.artifact_id: artifact.checksum for artifact in manifest.artifacts
    }
    return manifest.model_copy(update={"checksums": mapping})


def manifest_to_dict(manifest: ResearchRunManifest) -> dict[str, Any]:
    """Serialize with JSON-compatible UTC datetimes."""
    return manifest.model_dump(mode="json")


def manifest_from_dict(payload: dict[str, Any]) -> ResearchRunManifest:
    manifest = ResearchRunManifest.model_validate(payload)
    return validate_manifest(manifest, expected_run_id=manifest.run.run_id)
