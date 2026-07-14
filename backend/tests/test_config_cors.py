"""Deployment configuration and process-liveness contract tests."""

import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_LOCAL_ORIGINS, get_allowed_origins
from app.main import app


def test_allowed_origins_defaults_to_local_development(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

    assert get_allowed_origins() == DEFAULT_LOCAL_ORIGINS


def test_allowed_origins_parses_normalizes_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        " https://workspace.vercel.app/, http://localhost:3000, "
        "https://workspace.vercel.app///, ,",
    )

    assert get_allowed_origins() == [
        "https://workspace.vercel.app",
        "http://localhost:3000",
    ]


def test_allowed_origins_rejects_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://workspace.vercel.app,*")

    with pytest.raises(ValueError, match="explicit origins"):
        get_allowed_origins()


def test_cors_allows_configured_local_origin_without_credentials() -> None:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_does_not_allow_unconfigured_origin() -> None:
    client = TestClient(app)
    response = client.options(
        "/health",
        headers={
            "Origin": "https://unconfigured.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_health_is_exact_process_liveness_contract() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-quant-signal-backend",
    }
