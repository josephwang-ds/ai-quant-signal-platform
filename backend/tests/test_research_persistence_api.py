"""Tests for optional research lifecycle persistence API/service."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import research_persistence as route
from app.db.repositories.backtest_runs import DatabaseUnavailableError
from app.services.research_lifecycle_service import (
    ResearchLifecycleService,
    map_database_error,
)


def test_map_database_error_redacts_connection_details() -> None:
    status, detail = map_database_error(
        DatabaseUnavailableError("failed postgres://user:secret@host/db")
    )
    assert status == 503
    assert "postgres://" not in detail
    assert "secret" not in detail
    assert "SUPABASE" not in detail.upper()


def test_protocol_version_immutability_and_idempotency(monkeypatch) -> None:
    service = ResearchLifecycleService()
    calls = {"insert": 0}

    monkeypatch.setattr(
        "app.services.research_lifecycle_service.repo.get_protocol_version",
        lambda research_id, version: {
            "id": "pv-1",
            "research_id": research_id,
            "version": version,
            "protocol_hash": "abc",
            "created_at": "2026-01-01T00:00:00Z",
        },
    )

    def boom(**kwargs):
        calls["insert"] += 1
        raise AssertionError("must not insert when version exists")

    monkeypatch.setattr(
        "app.services.research_lifecycle_service.repo.insert_protocol_version",
        boom,
    )
    result = service.publish_protocol_version(
        {
            "research_id": "ma-crossover-spy",
            "version": 1,
            "parameters": {"short_window": 20},
        }
    )
    assert result["idempotent_replay"] is True
    assert result["immutable"] is True
    assert calls["insert"] == 0


def test_validation_run_idempotency_key(monkeypatch) -> None:
    service = ResearchLifecycleService()
    monkeypatch.setattr(
        "app.services.research_lifecycle_service.repo.insert_validation_run",
        lambda row: {
            "id": row["id"],
            "research_id": row["research_id"],
            "status": row["status"],
            "evidence_snapshot_id": None,
            "created_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
            "idempotent_replay": True,
        },
    )
    first = service.save_validation_run(
        {
            "id": "val-1",
            "research_id": "ma-crossover-spy",
            "idempotency_key": "key-1",
            "status": "completed",
        }
    )
    assert first["idempotent_replay"] is True


def test_api_returns_safe_503_when_db_unavailable(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(route.router)
    client = TestClient(app)

    def raise_unavailable(*args, **kwargs):
        raise DatabaseUnavailableError("Database is not configured.")

    monkeypatch.setattr(route._service, "upsert_project", raise_unavailable)
    response = client.put(
        "/api/v1/research/persistence/projects",
        json={
            "id": "demo-1",
            "name": "Demo",
            "question": "Does MA20/MA60 outperform buy-and-hold?",
        },
    )
    assert response.status_code == 503
    body = response.json()
    assert "SUPABASE_DB_URL" not in body["detail"]
    assert "postgres" not in body["detail"].lower()


def test_api_rejects_overlong_rationale(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(route.router)
    client = TestClient(app)
    response = client.post(
        "/api/v1/research/persistence/decision-records",
        json={
            "research_id": "ma-crossover-spy",
            "human_outcome": "hold",
            "rationale": "x" * 4001,
        },
    )
    assert response.status_code == 422


def test_decision_save_and_list(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(route.router)
    client = TestClient(app)
    saved = {
        "id": "dec-1",
        "research_id": "ma-crossover-spy",
        "human_outcome": "hold",
        "created_at": "2026-01-01T00:00:00Z",
    }
    monkeypatch.setattr(route._service, "save_decision", lambda payload: saved)
    monkeypatch.setattr(
        route._service,
        "list_decisions",
        lambda research_id, limit=20: [saved],
    )
    create = client.post(
        "/api/v1/research/persistence/decision-records",
        json={
            "research_id": "ma-crossover-spy",
            "human_outcome": "hold",
            "rationale": "Evidence incomplete; wait for walk-forward.",
        },
    )
    assert create.status_code == 200
    listed = client.get(
        "/api/v1/research/persistence/decision-records",
        params={"research_id": "ma-crossover-spy"},
    )
    assert listed.status_code == 200
    assert listed.json()["items"][0]["human_outcome"] == "hold"
