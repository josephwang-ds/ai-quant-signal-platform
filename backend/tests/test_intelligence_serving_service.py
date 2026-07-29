"""Phase 4.5 — IntelligenceService read-only behaviour tests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.intelligence.artifact_registry import ResearchArtifactRegistry
from app.intelligence.run_registry import ResearchRunRegistry
from app.intelligence.schemas import ResearchArtifactType, ResearchRunStatus, ResearchRunType
from app.intelligence.snapshot_builders import (
    RESEARCH_SUMMARY_EVIDENCE_VERSION,
    SIGNAL_EVIDENCE_VERSION,
    ResearchSummarySnapshotBuilder,
    SignalSnapshotBuilder,
)
from app.intelligence.snapshot_contracts import SignalDirection
from app.intelligence.snapshot_registry import ResearchSnapshotRegistry
from app.intelligence.storage import IntelligenceStorage
from app.intelligence_serving.deps import build_intelligence_service
from app.intelligence_serving.errors import (
    LatestPublishedRunNotFoundError,
    RunNotPublishedError,
    SnapshotContentInvalidError,
    SnapshotIntegrityServingError,
    SnapshotNotFoundServingError,
)
from app.intelligence_serving.service import IntelligenceService


@pytest.fixture
def storage(tmp_path: Path) -> IntelligenceStorage:
    return IntelligenceStorage(root=tmp_path / "outputs")


@pytest.fixture
def registries(storage: IntelligenceStorage) -> dict[str, Any]:
    runs = ResearchRunRegistry(storage=storage)
    artifacts = ResearchArtifactRegistry(runs)
    snapshots = ResearchSnapshotRegistry(runs, artifact_registry=artifacts)
    return {"runs": runs, "artifacts": artifacts, "snapshots": snapshots}


@pytest.fixture
def service(registries: dict[str, Any]) -> IntelligenceService:
    return IntelligenceService(
        registries["runs"],
        registries["artifacts"],
        registries["snapshots"],
    )


def _summary_payload() -> dict:
    return {
        "schema_version": RESEARCH_SUMMARY_EVIDENCE_VERSION,
        "research_title": "Published summary",
        "validation_status": "passed",
        "key_findings": [{"statement": "IC positive"}],
        "limitations": [{"statement": "Demo only"}],
    }


def _signal_payload() -> dict:
    return {
        "schema_version": SIGNAL_EVIDENCE_VERSION,
        "signals": [
            {
                "symbol": "AAPL",
                "signal_name": "mom",
                "direction": SignalDirection.POSITIVE.value,
                "evidence_artifact_ids": [],
                "metadata": {},
            }
        ],
    }


def _publish_with_snapshots(registries: dict[str, Any]) -> str:
    runs: ResearchRunRegistry = registries["runs"]
    artifacts: ResearchArtifactRegistry = registries["artifacts"]
    snapshots: ResearchSnapshotRegistry = registries["snapshots"]
    run_id = runs.create_run(
        run_type=ResearchRunType.FACTOR,
        universe="US Liquid 31",
    ).run.run_id
    summary_art = artifacts.register_json_artifact(
        run_id,
        name="summary-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_summary_payload(),
    )
    signal_art = artifacts.register_json_artifact(
        run_id,
        name="signal-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload=_signal_payload(),
    )
    ResearchSummarySnapshotBuilder(artifacts, snapshots).build_and_register(
        run_id,
        name="research-summary",
        source_artifact_ids=[summary_art.artifact_id],
    )
    SignalSnapshotBuilder(artifacts, snapshots).build_and_register(
        run_id,
        name="signal-board",
        source_artifact_ids=[signal_art.artifact_id],
    )
    runs.update_status(run_id, ResearchRunStatus.RUNNING)
    runs.update_status(run_id, ResearchRunStatus.VALIDATED)
    runs.publish_run(run_id)
    return run_id


def test_list_and_get_published_run(service: IntelligenceService, registries: dict[str, Any]) -> None:
    run_id = _publish_with_snapshots(registries)
    listed = service.list_runs()
    assert listed.count == 1
    assert listed.items[0].run_id == run_id
    assert listed.items[0].status == ResearchRunStatus.PUBLISHED
    detail = service.get_run(run_id)
    assert detail.artifact_count == 2
    assert detail.snapshot_count == 2
    latest = service.get_latest_run()
    assert latest.run_id == run_id


def test_unpublished_run_rejected(
    service: IntelligenceService,
    registries: dict[str, Any],
) -> None:
    run_id = registries["runs"].create_run(run_type=ResearchRunType.TREND).run.run_id
    with pytest.raises(RunNotPublishedError):
        service.get_run(run_id)
    assert service.list_runs().count == 0


def test_latest_missing(service: IntelligenceService) -> None:
    with pytest.raises(LatestPublishedRunNotFoundError):
        service.get_latest_run()


def test_artifact_and_snapshot_lists(
    service: IntelligenceService,
    registries: dict[str, Any],
) -> None:
    from app.intelligence.schemas import ResearchSnapshotType

    run_id = _publish_with_snapshots(registries)
    arts = service.list_artifacts(run_id)
    assert arts.count == 2
    assert all("relative_path" not in item.model_dump() for item in arts.items)
    snaps = service.list_snapshots(run_id)
    assert snaps.count == 2
    filtered = service.list_snapshots(run_id, snapshot_type=ResearchSnapshotType.SIGNAL)
    assert filtered.count == 1
    assert filtered.items[0].name == "signal-board"


def test_snapshot_content_by_name_and_id(
    service: IntelligenceService,
    registries: dict[str, Any],
) -> None:
    run_id = _publish_with_snapshots(registries)
    by_name = service.get_snapshot_content(run_id, "research-summary")
    assert by_name.content.research_title == "Published summary"  # type: ignore[union-attr]
    snap_id = by_name.reference.snapshot_id
    by_id = service.get_snapshot_content(run_id, snap_id, verify=True)
    assert by_id.reference.snapshot_id == snap_id

    signal = service.get_snapshot_content(run_id, "signal-board")
    assert signal.reference.snapshot_type.value == "signal"
    assert signal.content.signals[0].symbol == "AAPL"  # type: ignore[union-attr]


def test_verify_tamper_and_malformed_content(
    service: IntelligenceService,
    registries: dict[str, Any],
) -> None:
    run_id = _publish_with_snapshots(registries)
    ref = registries["snapshots"].get_snapshot(run_id, "research-summary")
    path = registries["runs"].storage.resolve_run_relative_path(run_id, ref.relative_path)
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises(SnapshotIntegrityServingError):
        service.get_snapshot_content(run_id, ref.snapshot_id, verify=True)

    path.write_text('{"schema_version": "broken"}', encoding="utf-8")
    with pytest.raises(SnapshotContentInvalidError):
        service.get_snapshot_content(run_id, ref.snapshot_id, verify=False)


def test_missing_snapshot(service: IntelligenceService, registries: dict[str, Any]) -> None:
    run_id = _publish_with_snapshots(registries)
    with pytest.raises(SnapshotNotFoundServingError):
        service.get_snapshot_content(run_id, "missing")


def test_reads_do_not_mutate_manifest_or_latest_or_create_files(
    service: IntelligenceService,
    registries: dict[str, Any],
    storage: IntelligenceStorage,
) -> None:
    run_id = _publish_with_snapshots(registries)
    manifest_path = storage.manifest_path(run_id)
    latest_path = storage.latest_path
    before_manifest = manifest_path.read_bytes()
    before_latest = latest_path.read_bytes()
    before_files = {
        str(p.relative_to(storage.root))
        for p in storage.root.rglob("*")
        if p.is_file()
    }

    service.list_runs()
    service.get_run(run_id)
    service.get_latest_run()
    service.list_artifacts(run_id)
    service.list_snapshots(run_id)
    service.get_snapshot_content(run_id, "research-summary", verify=True)

    assert manifest_path.read_bytes() == before_manifest
    assert latest_path.read_bytes() == before_latest
    after_files = {
        str(p.relative_to(storage.root))
        for p in storage.root.rglob("*")
        if p.is_file()
    }
    assert after_files == before_files


def test_service_does_not_invoke_builders(
    service: IntelligenceService,
    registries: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_id = _publish_with_snapshots(registries)

    def boom(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("builder must not be called from IntelligenceService")

    monkeypatch.setattr(
        "app.intelligence.snapshot_builders.ResearchSummarySnapshotBuilder.build",
        boom,
    )
    monkeypatch.setattr(
        "app.intelligence.snapshot_builders.SignalSnapshotBuilder.build_and_register",
        boom,
    )
    service.get_snapshot_content(run_id, "research-summary")


def test_build_intelligence_service_helper(storage: IntelligenceStorage) -> None:
    svc = build_intelligence_service(storage)
    assert isinstance(svc, IntelligenceService)
    with pytest.raises(LatestPublishedRunNotFoundError):
        svc.get_latest_run()
