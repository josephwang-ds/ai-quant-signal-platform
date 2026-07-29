"""Phase 4.5 — FastAPI intelligence query route tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import intelligence as intelligence_route
from app.intelligence.schemas import ResearchArtifactType, ResearchRunStatus, ResearchRunType
from app.intelligence.snapshot_builders import (
    RESEARCH_SUMMARY_EVIDENCE_VERSION,
    SIGNAL_EVIDENCE_VERSION,
    ResearchSummarySnapshotBuilder,
    SignalSnapshotBuilder,
)
from app.intelligence.snapshot_contracts import SignalDirection
from app.intelligence.storage import IntelligenceStorage
from app.intelligence_serving.deps import build_intelligence_service, get_intelligence_service
from app.intelligence_serving.service import IntelligenceService


@pytest.fixture
def storage(tmp_path: Path) -> IntelligenceStorage:
    return IntelligenceStorage(root=tmp_path / "outputs")


@pytest.fixture
def service(storage: IntelligenceStorage) -> IntelligenceService:
    return build_intelligence_service(storage)


@pytest.fixture
def client(service: IntelligenceService) -> TestClient:
    app = FastAPI()
    app.include_router(intelligence_route.router)
    app.dependency_overrides[get_intelligence_service] = lambda: service
    return TestClient(app)


def _publish(service: IntelligenceService) -> str:
    runs = service._runs
    artifacts = service._artifacts
    snapshots = service._snapshots
    run_id = runs.create_run(run_type=ResearchRunType.FACTOR, universe="US Liquid 31").run.run_id
    summary_art = artifacts.register_json_artifact(
        run_id,
        name="summary-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={
            "schema_version": RESEARCH_SUMMARY_EVIDENCE_VERSION,
            "research_title": "API summary",
            "key_findings": [{"statement": "ok"}],
            "limitations": [],
        },
    )
    signal_art = artifacts.register_json_artifact(
        run_id,
        name="signal-evidence",
        artifact_type=ResearchArtifactType.GENERIC_JSON,
        payload={
            "schema_version": SIGNAL_EVIDENCE_VERSION,
            "signals": [
                {
                    "symbol": "MSFT",
                    "signal_name": "mom",
                    "direction": SignalDirection.NEGATIVE.value,
                    "evidence_artifact_ids": [],
                    "metadata": {},
                }
            ],
        },
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


def test_six_endpoints_success(client: TestClient, service: IntelligenceService) -> None:
    run_id = _publish(service)

    listed = client.get("/api/v1/intelligence/runs")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1

    latest = client.get("/api/v1/intelligence/runs/latest")
    assert latest.status_code == 200
    assert latest.json()["run_id"] == run_id
    assert "relative_path" not in json_art(latest.json()["artifacts"][0])

    detail = client.get(f"/api/v1/intelligence/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "PUBLISHED"

    arts = client.get(f"/api/v1/intelligence/runs/{run_id}/artifacts")
    assert arts.status_code == 200
    body = arts.json()
    assert body["count"] == 2
    assert "relative_path" not in body["items"][0]
    assert "metadata" not in body["items"][0]
    # No raw evidence payload
    assert "schema_version" not in body["items"][0] or body["items"][0]["schema_version"].startswith(
        "research-artifact"
    )
    assert "key_findings" not in str(body)

    snaps = client.get(f"/api/v1/intelligence/runs/{run_id}/snapshots")
    assert snaps.status_code == 200
    assert snaps.json()["count"] == 2

    content = client.get(
        f"/api/v1/intelligence/runs/{run_id}/snapshots/research-summary"
    )
    assert content.status_code == 200
    payload = content.json()
    assert payload["content"]["research_title"] == "API summary"
    assert "relative_path" not in payload["reference"]


def json_art(item: dict[str, Any]) -> dict[str, Any]:
    return item


def test_latest_static_route_not_swallowed_by_run_id(
    client: TestClient,
    service: IntelligenceService,
) -> None:
    _publish(service)
    response = client.get("/api/v1/intelligence/runs/latest")
    assert response.status_code == 200
    assert response.json()["run_id"].startswith("run_")
    # Dynamic handler would treat "latest" as run_id → 400 invalid
    bad = client.get("/api/v1/intelligence/runs/not-a-valid-run-id")
    assert bad.status_code == 400
    assert bad.json()["detail"]["error_code"] == "INVALID_RUN_ID"


def test_error_codes(
    client: TestClient,
    service: IntelligenceService,
    storage: IntelligenceStorage,
) -> None:
    missing_latest = client.get("/api/v1/intelligence/runs/latest")
    assert missing_latest.status_code == 404
    assert missing_latest.json()["detail"]["error_code"] == "LATEST_NOT_FOUND"

    missing_run = client.get(
        "/api/v1/intelligence/runs/run_20260728T000000Z_deadbeef"
    )
    assert missing_run.status_code == 404
    assert missing_run.json()["detail"]["error_code"] == "RUN_NOT_FOUND"

    created = service._runs.create_run(run_type=ResearchRunType.GENERAL).run.run_id
    unpublished = client.get(f"/api/v1/intelligence/runs/{created}")
    assert unpublished.status_code == 403
    assert unpublished.json()["detail"]["error_code"] == "RUN_NOT_PUBLISHED"

    run_id = _publish(service)
    bad_type = client.get(
        f"/api/v1/intelligence/runs/{run_id}/snapshots",
        params={"snapshot_type": "portfolio"},
    )
    assert bad_type.status_code == 400
    assert bad_type.json()["detail"]["error_code"] == "INVALID_SNAPSHOT_TYPE"

    missing_snap = client.get(
        f"/api/v1/intelligence/runs/{run_id}/snapshots/nope"
    )
    assert missing_snap.status_code == 404
    assert missing_snap.json()["detail"]["error_code"] == "SNAPSHOT_NOT_FOUND"

    ref = service._snapshots.get_snapshot(run_id, "research-summary")
    path = storage.resolve_run_relative_path(run_id, ref.relative_path)
    path.write_bytes(path.read_bytes() + b"x")
    integrity = client.get(
        f"/api/v1/intelligence/runs/{run_id}/snapshots/{ref.snapshot_id}",
        params={"verify": "true"},
    )
    assert integrity.status_code == 409
    assert integrity.json()["detail"]["error_code"] == "SNAPSHOT_INTEGRITY_FAILED"

    path.write_text('{"not": "a snapshot"}', encoding="utf-8")
    invalid = client.get(
        f"/api/v1/intelligence/runs/{run_id}/snapshots/{ref.snapshot_id}",
        params={"verify": "false"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["error_code"] == "SNAPSHOT_CONTENT_INVALID"


def test_no_unpublished_bypass_and_no_write_routes(
    client: TestClient,
    service: IntelligenceService,
) -> None:
    created = service._runs.create_run(run_type=ResearchRunType.MODEL).run.run_id
    bypass = client.get(
        f"/api/v1/intelligence/runs/{created}",
        params={"include_unpublished": "true"},
    )
    assert bypass.status_code == 403

    # Router is GET-only for these resources.
    assert client.post("/api/v1/intelligence/runs").status_code == 405
    assert client.delete(f"/api/v1/intelligence/runs/{created}").status_code == 405
    assert client.put(f"/api/v1/intelligence/runs/{created}").status_code == 405

    routes = {route.path for route in intelligence_route.router.routes}
    assert "/api/v1/intelligence/runs" in routes
    assert not any("publish" in path for path in routes)
    assert not any("register" in path for path in routes)


def test_status_filter_rejects_non_published(
    client: TestClient,
    service: IntelligenceService,
) -> None:
    _publish(service)
    response = client.get(
        "/api/v1/intelligence/runs",
        params={"status": "CREATED"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "INVALID_QUERY"
