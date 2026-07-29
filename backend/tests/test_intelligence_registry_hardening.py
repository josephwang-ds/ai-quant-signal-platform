"""Phase 4.3.1 — registry concurrency and publish-recovery hardening tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.errors import IntelligenceStorageError, InvalidRunTransitionError
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import (
    ResearchArtifactType,
    ResearchRunStatus,
    ResearchRunType,
)
from app.intelligence.snapshot_contracts import (
    SignalDirection,
    SignalRecord,
    SnapshotFinding,
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


def test_concurrent_artifact_registration_preserves_both(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
) -> None:
    run_id = run_registry.create_run(run_type=ResearchRunType.FACTOR).run.run_id

    def register(name: str) -> str:
        ref = artifacts.register_json_artifact(
            run_id,
            name=name,
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"name": name},
        )
        return ref.artifact_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(register, "concurrent-a"),
            pool.submit(register, "concurrent-b"),
        ]
        ids = [future.result() for future in as_completed(futures)]

    listed = artifacts.list_artifacts(run_id)
    assert len(listed) == 2
    assert {item.name for item in listed} == {"concurrent-a", "concurrent-b"}
    assert {item.artifact_id for item in listed} == set(ids)
    for item in listed:
        assert artifacts.verify_artifact(run_id, item.artifact_id).valid is True
        path = run_registry.storage.resolve_run_relative_path(run_id, item.relative_path)
        assert path.is_file()


def test_concurrent_snapshot_registration_preserves_both(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
    snapshots: ResearchSnapshotRegistry,
) -> None:
    run_id = run_registry.create_run(run_type=ResearchRunType.MODEL).run.run_id
    source = artifacts.register_json_artifact(
        run_id,
        name="signal-src",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={"ok": True},
    )
    prior = snapshots.build_research_summary_snapshot(
        run_id,
        name="prior-summary",
        source_artifact_ids=[source.artifact_id],
        key_findings=[SnapshotFinding(statement="prior")],
    )

    def register(name: str, symbol: str) -> str:
        ref = snapshots.build_signal_snapshot(
            run_id,
            name=name,
            source_artifact_ids=[source.artifact_id],
            signals=[
                SignalRecord(
                    symbol=symbol,
                    signal_name="mom",
                    direction=SignalDirection.POSITIVE,
                )
            ],
        )
        return ref.snapshot_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(register, "snap-a", "AAPL"),
            pool.submit(register, "snap-b", "MSFT"),
        ]
        ids = [future.result() for future in as_completed(futures)]

    listed = snapshots.list_snapshots(run_id)
    assert len(listed) == 3
    assert {item.name for item in listed} == {"prior-summary", "snap-a", "snap-b"}
    assert prior.snapshot_id in {item.snapshot_id for item in listed}
    assert set(ids).issubset({item.snapshot_id for item in listed})
    for item in listed:
        assert snapshots.verify_snapshot(run_id, item.snapshot_id).valid is True


def test_different_runs_do_not_share_one_global_lock(
    run_registry: ResearchRunRegistry,
    artifacts: ResearchArtifactRegistry,
) -> None:
    left = run_registry.create_run(run_type=ResearchRunType.FACTOR).run.run_id
    right = run_registry.create_run(run_type=ResearchRunType.TREND).run.run_id
    assert run_registry.storage.run_lock_path(left) != run_registry.storage.run_lock_path(
        right
    )

    def register(run_id: str, name: str) -> str:
        return artifacts.register_json_artifact(
            run_id,
            name=name,
            artifact_type=ResearchArtifactType.GENERIC_JSON,
            payload={"run": run_id},
        ).artifact_id

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(register, left, "left-art"),
            pool.submit(register, right, "right-art"),
        ]
        results = [future.result() for future in as_completed(futures)]

    assert len(results) == 2
    assert len(artifacts.list_artifacts(left)) == 1
    assert len(artifacts.list_artifacts(right)) == 1


def test_publish_pointer_failure_recovery(
    run_registry: ResearchRunRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = run_registry.create_run(run_type=ResearchRunType.GENERAL).run.run_id
    run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
    run_registry.update_status(run_id, ResearchRunStatus.VALIDATED)

    original = run_registry._write_latest_pointer
    calls = {"n": 0}

    def boom(manifest: Any) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntelligenceStorageError("simulated latest.json failure")
        return original(manifest)

    monkeypatch.setattr(run_registry, "_write_latest_pointer", boom)
    with pytest.raises(IntelligenceStorageError, match="latest.json"):
        run_registry.publish_run(run_id)

    published = run_registry.get_run(run_id)
    assert published.run.status == ResearchRunStatus.PUBLISHED
    published_at = published.run.published_at
    assert published_at is not None
    assert not run_registry.storage.latest_path.is_file()

    repaired = run_registry.publish_run(run_id)
    assert repaired.run.status == ResearchRunStatus.PUBLISHED
    assert repaired.run.published_at == published_at
    assert run_registry.storage.latest_path.is_file()
    latest = run_registry.get_latest_published_run()
    assert latest is not None
    assert latest.run.run_id == run_id
    assert latest.run.published_at == published_at


def test_repeated_publish_is_idempotent(run_registry: ResearchRunRegistry) -> None:
    run_id = run_registry.create_run(run_type=ResearchRunType.FACTOR).run.run_id
    run_registry.update_status(run_id, ResearchRunStatus.RUNNING)
    run_registry.update_status(run_id, ResearchRunStatus.VALIDATED)
    first = run_registry.publish_run(run_id)
    second = run_registry.publish_run(run_id)
    assert second.run.status == ResearchRunStatus.PUBLISHED
    assert second.run.published_at == first.run.published_at
    assert second.model_dump(mode="json") == first.model_dump(mode="json")
    assert run_registry.get_latest_published_run().run.run_id == run_id


def test_publish_rejects_non_validated_and_non_published(
    run_registry: ResearchRunRegistry,
) -> None:
    created = run_registry.create_run(run_type=ResearchRunType.TREND).run.run_id
    with pytest.raises(InvalidRunTransitionError):
        run_registry.publish_run(created)

    failed = run_registry.create_run(run_type=ResearchRunType.GENERAL)
    run_registry.mark_failed(failed.run.run_id, "nope")
    with pytest.raises(InvalidRunTransitionError):
        run_registry.publish_run(failed.run.run_id)


def test_create_run_cleans_up_when_manifest_write_fails(
    run_registry: ResearchRunRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = run_registry._write_manifest

    def boom(manifest: Any) -> None:
        raise IntelligenceStorageError("simulated create manifest failure")

    monkeypatch.setattr(run_registry, "_write_manifest", boom)
    with pytest.raises(IntelligenceStorageError, match="simulated create"):
        run_registry.create_run(run_type=ResearchRunType.FACTOR)

    monkeypatch.setattr(run_registry, "_write_manifest", original)
    assert run_registry.list_runs() == []
    runs_dir = run_registry.storage.runs_dir
    if runs_dir.is_dir():
        leftovers = [p for p in runs_dir.iterdir() if p.is_dir()]
        assert leftovers == []
