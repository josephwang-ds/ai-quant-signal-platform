"""Phase 4.1 — research run registry foundation tests."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from app.intelligence.errors import (
    IntelligenceStorageError,
    InvalidRunTransitionError,
    ManifestValidationError,
    RunNotFoundError,
)
from app.intelligence.manifest import (
    apply_status,
    build_new_manifest,
    manifest_from_dict,
    manifest_to_dict,
    validate_manifest,
)
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ResearchArtifactReference,
    ResearchArtifactType,
    ResearchRunManifest,
    ResearchRunStatus,
    ResearchRunType,
    ResearchSnapshotReference,
    ResearchSnapshotType,
    generate_run_id,
    is_valid_run_id,
    utc_now,
)
from app.intelligence.storage import (
    ENV_OUTPUT_DIR,
    IntelligenceStorage,
    resolve_output_root,
)

RUN_ID_RE = re.compile(r"^run_\d{8}T\d{6}Z_[0-9a-f]{8}$")


def _artifact(
    *,
    name: str,
    relative_path: str,
    artifact_id: str = "artifact_aaaaaaaa",
) -> ResearchArtifactReference:
    return ResearchArtifactReference(
        artifact_id=artifact_id,
        name=name,
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        relative_path=relative_path,
        checksum="a" * 64,
        size_bytes=1,
        created_at=utc_now(),
    )


def _snapshot(
    *,
    name: str,
    relative_path: str,
    snapshot_id: str = "snapshot_aaaaaaaa",
    source_artifact_ids: list[str] | None = None,
) -> ResearchSnapshotReference:
    return ResearchSnapshotReference(
        snapshot_id=snapshot_id,
        name=name,
        snapshot_type=ResearchSnapshotType.RESEARCH_SUMMARY,
        relative_path=relative_path,
        checksum="b" * 64,
        size_bytes=1,
        created_at=utc_now(),
        source_artifact_ids=source_artifact_ids or [],
    )


@pytest.fixture
def registry(tmp_path: Path) -> ResearchRunRegistry:
    storage = IntelligenceStorage(root=tmp_path / "outputs")
    return ResearchRunRegistry(storage=storage)


def _advance_to_validated(registry: ResearchRunRegistry) -> ResearchRunManifest:
    created = registry.create_run(run_type=ResearchRunType.FACTOR, universe="us_liquid_31_v1")
    registry.update_status(created.run.run_id, ResearchRunStatus.RUNNING)
    return registry.update_status(created.run.run_id, ResearchRunStatus.VALIDATED)


def test_run_id_format() -> None:
    run_id = generate_run_id(when=datetime(2026, 7, 28, 4, 15, 30, tzinfo=timezone.utc))
    assert RUN_ID_RE.fullmatch(run_id)
    assert run_id.startswith("run_20260728T041530Z_")
    assert is_valid_run_id(run_id)
    assert not is_valid_run_id("run_bad")
    assert not is_valid_run_id("../run_20260728T041530Z_abcd1234")
    assert not is_valid_run_id("run_20260728T041530Z_SPY")


def test_run_id_uniqueness() -> None:
    ids = {generate_run_id() for _ in range(200)}
    assert len(ids) == 200


def test_create_run_writes_valid_manifest(registry: ResearchRunRegistry) -> None:
    manifest = registry.create_run(
        run_type=ResearchRunType.MODEL,
        notes="phase-4.1 foundation",
    )
    assert manifest.run.status == ResearchRunStatus.CREATED
    assert manifest.artifacts == []
    assert manifest.snapshots == []
    assert manifest.checksums == {}
    assert manifest.errors == []
    path = registry.storage.manifest_path(manifest.run.run_id)
    assert path.is_file()
    loaded = registry.get_run(manifest.run.run_id)
    assert loaded.run.run_id == manifest.run.run_id
    assert loaded.run.dataset_version is None
    assert loaded.run.feature_version is None
    assert loaded.run.model_version is None


def test_manifest_directory_matches_run_id(registry: ResearchRunRegistry) -> None:
    manifest = registry.create_run(run_type=ResearchRunType.GENERAL)
    run_dir = registry.storage.run_dir(manifest.run.run_id)
    assert run_dir.name == manifest.run.run_id
    assert (run_dir / "manifest.json").is_file()


def test_default_and_env_output_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    default_root = resolve_output_root({})
    assert default_root.name == "outputs"
    assert default_root.parent.name == "backend"

    configured = tmp_path / "intel-out"
    monkeypatch.setenv(ENV_OUTPUT_DIR, str(configured))
    resolved = resolve_output_root()
    assert resolved == configured.resolve()

    storage = IntelligenceStorage(env={ENV_OUTPUT_DIR: str(configured)})
    storage.ensure_root()
    assert (configured / "runs").is_dir()


def test_path_traversal_rejection(registry: ResearchRunRegistry) -> None:
    with pytest.raises(IntelligenceStorageError):
        registry.storage.run_dir("../secret")
    with pytest.raises(IntelligenceStorageError):
        registry.storage.run_dir("run_20260728T041530Z_abcd1234/../../etc")
    with pytest.raises(IntelligenceStorageError):
        registry.get_run("not-a-run-id")


def test_valid_status_transitions(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.TREND)
    running = registry.update_status(created.run.run_id, ResearchRunStatus.RUNNING)
    assert running.run.status == ResearchRunStatus.RUNNING
    validated = registry.update_status(created.run.run_id, ResearchRunStatus.VALIDATED)
    assert validated.run.status == ResearchRunStatus.VALIDATED
    published = registry.publish_run(created.run.run_id)
    assert published.run.status == ResearchRunStatus.PUBLISHED
    archived = registry.archive_run(created.run.run_id)
    assert archived.run.status == ResearchRunStatus.ARCHIVED


def test_invalid_status_transitions(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.TREND)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(created.run.run_id, ResearchRunStatus.PUBLISHED)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(created.run.run_id, ResearchRunStatus.VALIDATED)

    validated = _advance_to_validated(registry)
    published = registry.publish_run(validated.run.run_id)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(published.run.run_id, ResearchRunStatus.RUNNING)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(published.run.run_id, ResearchRunStatus.FAILED)

    archived = registry.archive_run(published.run.run_id)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(archived.run.run_id, ResearchRunStatus.RUNNING)


def test_failed_run_stores_error(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.FACTOR)
    failed = registry.mark_failed(created.run.run_id, "validation rejected")
    assert failed.run.status == ResearchRunStatus.FAILED
    assert "validation rejected" in failed.errors


def test_failed_without_errors_is_rejected(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.FACTOR)
    with pytest.raises(ManifestValidationError):
        registry.mark_failed(created.run.run_id, "   ")
    with pytest.raises(ManifestValidationError):
        registry.update_status(created.run.run_id, ResearchRunStatus.FAILED)


def test_publish_requires_validated(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.MODEL)
    with pytest.raises(InvalidRunTransitionError):
        registry.publish_run(created.run.run_id)
    registry.update_status(created.run.run_id, ResearchRunStatus.RUNNING)
    with pytest.raises(InvalidRunTransitionError):
        registry.publish_run(created.run.run_id)


def test_publish_sets_published_at_and_latest_pointer(registry: ResearchRunRegistry) -> None:
    validated = _advance_to_validated(registry)
    assert validated.run.published_at is None
    published = registry.publish_run(validated.run.run_id)
    assert published.run.published_at is not None
    assert published.run.published_at.tzinfo is not None
    latest_path = registry.storage.latest_path
    assert latest_path.is_file()
    pointer = json.loads(latest_path.read_text(encoding="utf-8"))
    assert set(pointer.keys()) == {
        "schema_version",
        "run_id",
        "manifest_path",
        "published_at",
    }
    assert pointer["run_id"] == published.run.run_id
    assert pointer["manifest_path"] == f"runs/{published.run.run_id}/manifest.json"
    assert "artifacts" not in pointer


def test_latest_updates_only_after_successful_publish(
    registry: ResearchRunRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validated = _advance_to_validated(registry)
    assert not registry.storage.latest_path.exists()

    original = registry.storage.write_json_atomic
    calls: list[Path] = []

    def tracking_write(path: Path, payload: Any) -> None:
        calls.append(path)
        if path == registry.storage.latest_path:
            raise OSError("simulated latest pointer failure")
        original(path, payload)

    monkeypatch.setattr(registry.storage, "write_json_atomic", tracking_write)
    with pytest.raises(OSError):
        registry.publish_run(validated.run.run_id)

    assert registry.storage.latest_path.exists() is False
    # Manifest publish write happened first; pointer update failed afterward.
    assert any(path.name == "manifest.json" for path in calls)
    # Status may already be PUBLISHED on disk because manifest write preceded pointer write.
    # The pointer must still be absent so get_latest_published_run returns None.
    assert registry.get_latest_published_run() is None


def test_get_latest_published_run_returns_correct_run(registry: ResearchRunRegistry) -> None:
    first = _advance_to_validated(registry)
    registry.publish_run(first.run.run_id)
    second = _advance_to_validated(registry)
    registry.publish_run(second.run.run_id)
    latest = registry.get_latest_published_run()
    assert latest is not None
    assert latest.run.run_id == second.run.run_id
    assert latest.run.status == ResearchRunStatus.PUBLISHED


def test_published_manifest_cannot_be_mutated(registry: ResearchRunRegistry) -> None:
    validated = _advance_to_validated(registry)
    published = registry.publish_run(validated.run.run_id)
    with pytest.raises(InvalidRunTransitionError):
        registry.update_status(published.run.run_id, ResearchRunStatus.RUNNING)
    with pytest.raises(InvalidRunTransitionError):
        registry.mark_failed(published.run.run_id, "too late")
    reloaded = registry.get_run(published.run.run_id)
    assert reloaded.run.status == ResearchRunStatus.PUBLISHED
    assert reloaded.run.notes == published.run.notes


def test_published_run_may_be_archived(registry: ResearchRunRegistry) -> None:
    validated = _advance_to_validated(registry)
    published = registry.publish_run(validated.run.run_id)
    archived = registry.archive_run(published.run.run_id)
    assert archived.run.status == ResearchRunStatus.ARCHIVED
    assert archived.run.published_at == published.run.published_at


def test_atomic_write_does_not_leave_destination_after_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = IntelligenceStorage(root=tmp_path / "outputs")
    storage.ensure_root()
    destination = storage.root / "probe.json"

    real_replace = os.replace

    def failing_replace(src: str, dst: str) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(IntelligenceStorageError):
        storage.write_json_atomic(destination, {"ok": True})
    assert not destination.exists()
    leftovers = list(storage.root.glob(".probe.json.*.tmp"))
    assert leftovers == []

    monkeypatch.setattr(os, "replace", real_replace)
    storage.write_json_atomic(destination, {"ok": True})
    assert destination.is_file()


def test_datetimes_are_timezone_aware_utc(registry: ResearchRunRegistry) -> None:
    manifest = registry.create_run(run_type=ResearchRunType.GENERAL)
    assert manifest.run.created_at.tzinfo is not None
    assert manifest.run.updated_at.tzinfo is not None
    assert manifest.run.created_at.utcoffset() == timedelta(0)


def test_serialization_round_trip_preserves_manifest(registry: ResearchRunRegistry) -> None:
    original = registry.create_run(
        run_type=ResearchRunType.FACTOR,
        universe="us_liquid_31_v1",
        random_seed=7,
    )
    payload = manifest_to_dict(original)
    restored = manifest_from_dict(payload)
    assert restored == original


def test_unsafe_artifact_paths_rejected() -> None:
    base = build_new_manifest(run_type=ResearchRunType.GENERAL)
    bad = base.model_copy(
        update={
            "artifacts": [
                _artifact(name="scores", relative_path="../escape.parquet"),
            ]
        }
    )
    with pytest.raises(ManifestValidationError):
        validate_manifest(bad)


def test_duplicate_artifact_and_snapshot_names_rejected() -> None:
    base = build_new_manifest(run_type=ResearchRunType.GENERAL)
    with pytest.raises(ManifestValidationError):
        validate_manifest(
            base.model_copy(
                update={
                    "artifacts": [
                        _artifact(
                            name="a",
                            relative_path="artifacts/a.json",
                            artifact_id="artifact_aaaaaaaa",
                        ),
                        _artifact(
                            name="a",
                            relative_path="artifacts/b.json",
                            artifact_id="artifact_bbbbbbbb",
                        ),
                    ]
                }
            )
        )
    with pytest.raises(ManifestValidationError):
        validate_manifest(
            base.model_copy(
                update={
                    "artifacts": [
                        _artifact(
                            name="src",
                            relative_path="artifacts/src.json",
                            artifact_id="artifact_cccccccc",
                        )
                    ],
                    "snapshots": [
                        _snapshot(
                            name="s",
                            relative_path="snapshots/s.json",
                            snapshot_id="snapshot_aaaaaaaa",
                            source_artifact_ids=["artifact_cccccccc"],
                        ),
                        _snapshot(
                            name="s",
                            relative_path="snapshots/t.json",
                            snapshot_id="snapshot_bbbbbbbb",
                            source_artifact_ids=["artifact_cccccccc"],
                        ),
                    ],
                }
            )
        )


def test_get_missing_run_raises(registry: ResearchRunRegistry) -> None:
    missing = generate_run_id()
    with pytest.raises(RunNotFoundError):
        registry.get_run(missing)


def test_failed_then_archived(registry: ResearchRunRegistry) -> None:
    created = registry.create_run(run_type=ResearchRunType.TREND)
    failed = registry.mark_failed(created.run.run_id, "boom")
    archived = registry.archive_run(failed.run.run_id)
    assert archived.run.status == ResearchRunStatus.ARCHIVED
    assert archived.run.published_at is None


def test_apply_status_sets_published_at_only_on_publish() -> None:
    base = build_new_manifest(run_type=ResearchRunType.MODEL)
    running = apply_status(base, ResearchRunStatus.RUNNING)
    assert running.run.published_at is None
    validated = apply_status(running, ResearchRunStatus.VALIDATED)
    published = apply_status(validated, ResearchRunStatus.PUBLISHED)
    assert published.run.published_at is not None
    assert published.run.published_at.tzinfo is not None


def test_utc_now_is_aware() -> None:
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)
