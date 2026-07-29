"""Phase 4.2 — research artifact registry tests."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.intelligence.artifact_registry import (
    ResearchArtifactRegistry,
    serialize_artifact_json,
)
from app.intelligence.errors import (
    ArtifactAlreadyExistsError,
    ArtifactNotFoundError,
    IntelligenceStorageError,
    InvalidRunTransitionError,
)
from app.intelligence.manifest import manifest_from_dict, manifest_to_dict
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ResearchArtifactType,
    ResearchRunStatus,
    ResearchRunType,
    generate_artifact_id,
    is_valid_artifact_id,
)
from app.intelligence.storage import IntelligenceStorage, calculate_sha256


@pytest.fixture
def run_registry(tmp_path: Path) -> ResearchRunRegistry:
    return ResearchRunRegistry(storage=IntelligenceStorage(root=tmp_path / "outputs"))


@pytest.fixture
def artifacts(run_registry: ResearchRunRegistry) -> ResearchArtifactRegistry:
    return ResearchArtifactRegistry(run_registry)


@pytest.fixture
def created_run(run_registry: ResearchRunRegistry) -> str:
    return run_registry.create_run(run_type=ResearchRunType.FACTOR).run.run_id


def test_artifact_id_format() -> None:
    artifact_id = generate_artifact_id()
    assert is_valid_artifact_id(artifact_id)
    assert artifact_id.startswith("artifact_")
    assert not is_valid_artifact_id("artifact_SPY")
    assert not is_valid_artifact_id("run_20260728T041530Z_abcd1234")


def test_artifact_id_uniqueness() -> None:
    ids = {generate_artifact_id() for _ in range(200)}
    assert len(ids) == 200


def test_register_json_artifact_writes_under_run_artifacts(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="factor-metrics",
        artifact_type=ResearchArtifactType.FACTOR_METRICS,
        payload={"mean_ic": 0.02, "horizon": 5},
    )
    assert ref.name == "factor-metrics"
    assert ref.artifact_type == ResearchArtifactType.FACTOR_METRICS
    assert ref.relative_path.startswith("artifacts/")
    assert not Path(ref.relative_path).is_absolute()
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    assert path.is_file()
    assert path.parent.name == "artifacts"
    assert created_run in str(path)


def test_deterministic_json_serialization_and_checksum(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    payload = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    left = serialize_artifact_json(payload)
    right = serialize_artifact_json({"nested": {"y": 8, "z": 9}, "a": 1, "b": 2})
    assert left == right
    ref = artifacts.register_json_artifact(
        created_run,
        name="stable-json",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=payload,
    )
    expected = hashlib.sha256(left).hexdigest()
    assert ref.checksum == expected
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    assert calculate_sha256(path) == expected
    assert ref.size_bytes == len(left)
    assert path.stat().st_size == ref.size_bytes


def test_list_payload_row_count_and_unknown_null(
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> None:
    listed = artifacts.register_json_artifact(
        created_run,
        name="rows",
        artifact_type=ResearchArtifactType.PREDICTION_TABLE,
        payload=[{"symbol": "AAPL"}, {"symbol": "MSFT"}],
    )
    assert listed.row_count == 2

    mapping = artifacts.register_json_artifact(
        created_run,
        name="summary",
        artifact_type=ResearchArtifactType.MODEL_EVALUATION,
        payload={"ok": True},
    )
    assert mapping.row_count is None


def test_register_file_artifact_copies_without_source_mutation(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    tmp_path: Path,
) -> None:
    source = tmp_path / "external" / "metrics.json"
    source.parent.mkdir(parents=True)
    original = b'{"ok": true}\n'
    source.write_bytes(original)
    before_mtime = source.stat().st_mtime_ns

    ref = artifacts.register_file_artifact(
        created_run,
        name="copied-metrics",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        source_path=source,
        row_count=1,
    )
    assert source.read_bytes() == original
    assert source.stat().st_mtime_ns == before_mtime
    assert ref.row_count == 1
    assert str(source) not in json.dumps(manifest_to_dict(run_registry.get_run(created_run)))
    assert "external" not in ref.relative_path
    dest = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    assert dest.read_bytes() == original


def test_path_traversal_name_rejected(
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> None:
    with pytest.raises(Exception):
        artifacts.register_json_artifact(
            created_run,
            name="../escape",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"x": 1},
        )


def test_duplicate_name_and_destination_rejected(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    first = artifacts.register_json_artifact(
        created_run,
        name="once",
        artifact_type=ResearchArtifactType.FACTOR_REPORT,
        payload={"v": 1},
    )
    with pytest.raises(ArtifactAlreadyExistsError):
        artifacts.register_json_artifact(
            created_run,
            name="once",
            artifact_type=ResearchArtifactType.FACTOR_REPORT,
            payload={"v": 2},
        )
    dest = run_registry.storage.resolve_run_relative_path(created_run, first.relative_path)
    with pytest.raises(IntelligenceStorageError):
        run_registry.storage.write_bytes_atomic(dest, b"overwrite", overwrite=False)


def test_status_gates_for_registration(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
) -> None:
    created = run_registry.create_run(run_type=ResearchRunType.MODEL)
    run_id = created.run.run_id
    artifacts.register_json_artifact(
        run_id,
        name="created-ok",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"s": "CREATED"},
    )
    run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
    artifacts.register_json_artifact(
        run_id,
        name="running-ok",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"s": "RUNNING"},
    )
    run_registry.update_status(run_id, ResearchRunStatus.VALIDATED)
    artifacts.register_json_artifact(
        run_id,
        name="validated-ok",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"s": "VALIDATED"},
    )
    run_registry.publish_run(run_id)
    with pytest.raises(InvalidRunTransitionError):
        artifacts.register_json_artifact(
            run_id,
            name="published-no",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"s": "PUBLISHED"},
        )

    failed = run_registry.create_run(run_type=ResearchRunType.TREND)
    run_registry.mark_failed(failed.run.run_id, "nope")
    with pytest.raises(InvalidRunTransitionError):
        artifacts.register_json_artifact(
            failed.run.run_id,
            name="failed-no",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"s": "FAILED"},
        )

    archived = run_registry.create_run(run_type=ResearchRunType.GENERAL)
    run_registry.mark_failed(archived.run.run_id, "x")
    run_registry.archive_run(archived.run.run_id)
    with pytest.raises(InvalidRunTransitionError):
        artifacts.register_json_artifact(
            archived.run.run_id,
            name="archived-no",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"s": "ARCHIVED"},
        )


def test_get_artifact_by_name_and_id(
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="lookup",
        artifact_type=ResearchArtifactType.VALIDATION_REPORT,
        payload={"ok": True},
    )
    assert artifacts.get_artifact(created_run, "lookup").artifact_id == ref.artifact_id
    assert artifacts.get_artifact(created_run, ref.artifact_id).name == "lookup"
    assert len(artifacts.list_artifacts(created_run)) == 1
    with pytest.raises(ArtifactNotFoundError):
        artifacts.get_artifact(created_run, "missing")


def test_verify_artifact_success_and_tamper_detection(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="verify-me",
        artifact_type=ResearchArtifactType.DATA_VALIDATION_REPORT,
        payload={"rows": 3},
    )
    ok = artifacts.verify_artifact(created_run, ref.artifact_id)
    assert ok.valid is True
    assert ok.checksum_matches is True
    assert ok.size_matches is True
    assert ok.errors == []

    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    bad = artifacts.verify_artifact(created_run, "verify-me")
    assert bad.valid is False
    assert bad.checksum_matches is False
    # verification is read-only: manifest checksum unchanged
    stored = artifacts.get_artifact(created_run, "verify-me")
    assert stored.checksum == ref.checksum
    path.write_bytes(original)


def test_verify_missing_file(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    ref = artifacts.register_json_artifact(
        created_run,
        name="will-delete",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"x": 1},
    )
    path = run_registry.storage.resolve_run_relative_path(created_run, ref.relative_path)
    path.unlink()
    result = artifacts.verify_artifact(created_run, ref.name)
    assert result.exists is False
    assert result.valid is False
    assert "missing" in " ".join(result.errors).lower()


def test_manifest_update_failure_rolls_back_new_artifact(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = artifacts.register_json_artifact(
        created_run,
        name="keep-me",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"keep": True},
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
        artifacts.register_json_artifact(
            created_run,
            name="rollback-me",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"rollback": True},
        )

    monkeypatch.setattr(run_registry, "_write_manifest", original)
    remaining = artifacts.list_artifacts(created_run)
    assert [item.name for item in remaining] == ["keep-me"]
    assert first_path.is_file()
    artifacts_dir = run_registry.storage.artifacts_dir(created_run)
    leftovers = [p for p in artifacts_dir.iterdir() if p.is_file() and "rollback" in p.name]
    assert leftovers == []


def test_serialization_round_trip_preserves_artifact_metadata(
    artifacts: ResearchArtifactRegistry,
    run_registry: ResearchRunRegistry,
    created_run: str,
) -> None:
    artifacts.register_json_artifact(
        created_run,
        name="round-trip",
        artifact_type=ResearchArtifactType.FEATURE_IMPORTANCE,
        payload={"feature": "mom_20", "weight": 0.1},
        metadata={"source": "unit-test"},
    )
    original = run_registry.get_run(created_run)
    restored = manifest_from_dict(manifest_to_dict(original))
    assert restored.artifacts[0].artifact_id == original.artifacts[0].artifact_id
    assert restored.artifacts[0].checksum == original.artifacts[0].checksum
    assert restored.checksums[restored.artifacts[0].artifact_id] == restored.artifacts[0].checksum
    assert restored.artifacts[0].metadata == {"source": "unit-test"}


def test_artifact_reference_rejects_domain_or_run_metadata_keys(
    artifacts: ResearchArtifactRegistry,
    created_run: str,
) -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        artifacts.register_json_artifact(
            created_run,
            name="bad-meta",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"opaque": True},
            metadata={"sharpe": 1.2},
        )
    with pytest.raises(ValidationError):
        artifacts.register_json_artifact(
            created_run,
            name="bad-run-meta",
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"opaque": True},
            metadata={"run_id": created_run},
        )


def test_datetime_json_is_stable() -> None:
    stamp = datetime(2026, 7, 28, 4, 15, 30, tzinfo=timezone.utc)
    encoded = serialize_artifact_json({"created_at": stamp})
    assert b"2026-07-28T04:15:30Z" in encoded
