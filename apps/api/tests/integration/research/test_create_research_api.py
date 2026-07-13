"""CreateResearch HTTP 集成测试。"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from bootstrap.create_app import create_app
from modules.research.infrastructure.repositories.in_memory_research_repository import (
    InMemoryResearchRepository,
)


def _client() -> tuple[TestClient, InMemoryResearchRepository]:
    repository = InMemoryResearchRepository()
    app = create_app(research_repository=repository)
    return TestClient(app), repository


def test_post_create_research_returns_201_and_persists() -> None:
    client, repository = _client()
    strategy_id = str(uuid4())

    response = client.post(
        "/api/research",
        json={
            "strategy_id": strategy_id,
            "title": "Intraday liquidity research",
            "objective": "Map spread regimes around openings.",
            "owner": "research-owner",
            "notes": None,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["state"] == "Draft"
    assert body["strategy_id"] == strategy_id
    assert body["title"] == "Intraday liquidity research"
    assert body["version"] == 1
    assert repository.get_by_id(__import__("uuid").UUID(body["id"])) is not None


def test_post_create_research_rejects_invalid_payload() -> None:
    client, _ = _client()

    response = client.post(
        "/api/research",
        json={
            "strategy_id": str(uuid4()),
            "title": "",
            "objective": "objective",
            "owner": "owner",
        },
    )

    assert response.status_code == 422


def test_post_create_research_rejects_unknown_fields() -> None:
    client, _ = _client()

    response = client.post(
        "/api/research",
        json={
            "strategy_id": str(uuid4()),
            "title": "title",
            "objective": "objective",
            "owner": "owner",
            "extra_field": "not-allowed",
        },
    )

    assert response.status_code == 422
