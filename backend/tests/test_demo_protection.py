"""Public-demo security and cost-protection tests."""

from __future__ import annotations

import threading

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.research_agent.schemas import AgentResumeRequest
from app.research_copilot.schemas import ResearchCopilotRequest
from app.schemas import SaveBacktestRunRequest
from app.security.client_ip import resolve_client_ip
from app.security.concurrency import (
    LlmConcurrencyFullError,
    acquire_llm_slot,
    reset_llm_concurrency_for_tests,
)
from app.security.limits import MAX_NOTES_LENGTH, MAX_PROMPT_LENGTH, MAX_QUESTION_LENGTH
from app.security.logging_redaction import redact_secrets, safe_log_extra
from app.security.rate_limit import classify_endpoint, reset_rate_limiter_for_tests
from app.security.settings import clear_demo_protection_settings_cache


@pytest.fixture(autouse=True)
def _reset_protection(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("AGENT_RATE_LIMIT", "1000")
    monkeypatch.setenv("EXPENSIVE_RATE_LIMIT", "1000")
    monkeypatch.setenv("WRITE_RATE_LIMIT", "1000")
    monkeypatch.setenv("READ_RATE_LIMIT", "1000")
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "2")
    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()
    reset_llm_concurrency_for_tests()
    yield
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()
    reset_llm_concurrency_for_tests()


def test_overlong_prompt_rejected() -> None:
    with pytest.raises(ValidationError) as exc:
        ResearchCopilotRequest(
            validation_run_id="validation-demo",
            question="x" * (MAX_QUESTION_LENGTH + 1),
        )
    assert "question" in str(exc.value).lower()

    client = TestClient(app)
    response = client.post(
        "/api/v1/research/reviewer/review-hypothesis",
        json={
            "research_type": "trend_following",
            "research_question": "q" * (MAX_PROMPT_LENGTH + 1),
            "hypothesis": "h",
            "null_hypothesis": "n",
            "benchmark": "SPY buy-and-hold",
            "success_criteria": [],
            "available_validation_methods": ["oos"],
        },
    )
    assert response.status_code == 422
    body = response.text.lower()
    assert "research_question" in body or "string_too_long" in body
    assert "sk-" not in body
    assert "supabase" not in body


def test_overlong_notes_rejected() -> None:
    with pytest.raises(ValidationError):
        SaveBacktestRunRequest(
            ticker="AAPL",
            strategy="ma_crossover",
            strategy_config={"strategy": "ma_crossover"},
            start_date="2022-01-01",
            metrics={"total_return": 0.1},
            notes="n" * (MAX_NOTES_LENGTH + 1),
        )

    with pytest.raises(ValidationError) as exc:
        AgentResumeRequest(
            action="record_decision",
            payload={"decision": "Hold", "rationale": "r" * (MAX_NOTES_LENGTH + 1)},
        )
    assert "rationale" in str(exc.value).lower()

    client = TestClient(app)
    response = client.post(
        "/api/experiments/backtest-runs",
        json={
            "ticker": "AAPL",
            "strategy": "ma_crossover",
            "strategy_config": {"strategy": "ma_crossover"},
            "start_date": "2022-01-01",
            "metrics": {"total_return": 0.1},
            "notes": "n" * (MAX_NOTES_LENGTH + 1),
        },
    )
    assert response.status_code == 422
    assert "SUPABASE_DB_URL" not in response.text


def test_rate_limit_returns_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_RATE_LIMIT", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()

    client = TestClient(app)
    first = client.post(
        "/api/v1/research/copilot/query",
        json={
            "validation_run_id": "missing",
            "question": "Why is evaluation incomplete?",
        },
    )
    # First request may be 4xx from business rules, but must not be 429.
    assert first.status_code != 429

    second = client.post(
        "/api/v1/research/copilot/query",
        json={
            "validation_run_id": "missing",
            "question": "Why is evaluation incomplete?",
        },
    )
    assert second.status_code == 429
    detail = second.json()["detail"]
    assert "try again" in detail.lower()
    assert "InMemoryRateLimiter" not in detail
    assert "semaphore" not in detail.lower()
    assert "retry-after" in second.headers
    assert "SUPABASE_DB_URL" not in second.text
    assert "sk-" not in second.text


def test_health_uses_looser_read_tier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENT_RATE_LIMIT", "1")
    monkeypatch.setenv("READ_RATE_LIMIT", "5")
    clear_demo_protection_settings_cache()
    reset_rate_limiter_for_tests()

    client = TestClient(app)
    # Exhaust LLM tier with one agent/copilot-class call classification sanity.
    assert classify_endpoint("GET", "/health") == "read"
    assert classify_endpoint("POST", "/api/v1/research/copilot/query") == "llm"
    assert classify_endpoint("POST", "/api/experiments/backtest-runs") == "write"

    for _ in range(5):
        assert client.get("/health").status_code == 200
    limited = client.get("/health")
    assert limited.status_code == 429


def test_concurrency_full_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "1")
    clear_demo_protection_settings_cache()
    reset_llm_concurrency_for_tests()

    held = threading.Event()
    release = threading.Event()

    def hold_slot() -> None:
        with acquire_llm_slot():
            held.set()
            release.wait(timeout=2.0)

    worker = threading.Thread(target=hold_slot, daemon=True)
    worker.start()
    assert held.wait(timeout=1.0)

    with pytest.raises(LlmConcurrencyFullError) as exc:
        with acquire_llm_slot():
            pass
    assert exc.value.status_code == 503
    assert "try again" in exc.value.message.lower()
    assert "queue" not in exc.value.message.lower()

    release.set()
    worker.join(timeout=2.0)


def test_log_redaction_helper() -> None:
    raw = (
        "LLM_API_KEY=sk-abcdefghijklmnopqrstuvwxyz "
        "Bearer tok_secret_value "
        "postgres://user:pass@host/db "
        "SUPABASE_DB_URL=postgresql://x:y@z/db"
    )
    redacted = redact_secrets(raw)
    assert "sk-abcdefghijklmnopqrstuvwxyz" not in redacted
    assert "tok_secret_value" not in redacted
    assert "postgres://user:pass@host/db" not in redacted
    assert "postgresql://x:y@z/db" not in redacted
    assert "[REDACTED]" in redacted

    safe = safe_log_extra(
        {
            "run_id": "agent-123",
            "endpoint": "/api/v1/research/copilot/query",
            "duration_ms": 12,
            "status_code": 200,
            "prompt_tokens": 10,
            "system_prompt": "SECRET PROMPT TEXT",
            "user_prompt": "secret question",
            "api_key": "sk-should-not-appear",
            "chain_of_thought": "hidden reasoning",
        }
    )
    assert safe["run_id"] == "agent-123"
    assert safe["endpoint"] == "/api/v1/research/copilot/query"
    assert safe["prompt_tokens"] == 10
    assert "system_prompt" not in safe
    assert "user_prompt" not in safe
    assert "api_key" not in safe
    assert "chain_of_thought" not in safe


def test_response_contains_no_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://user:secret@host/db")
    monkeypatch.setenv("LLM_API_KEY", "sk-test-secret-key-value")
    clear_demo_protection_settings_cache()

    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert "sk-test-secret-key-value" not in health.text
    assert "postgresql://user:secret@host/db" not in health.text
    assert "SUPABASE_DB_URL" not in health.text

    db_status = client.get("/api/database/status")
    blob = db_status.text
    assert "sk-test-secret-key-value" not in blob
    assert "postgresql://user:secret@host/db" not in blob
    assert "user:secret@" not in blob


def test_trusted_proxy_ip_handling() -> None:
    # Untrusted peer: ignore spoofed X-Forwarded-For.
    assert (
        resolve_client_ip(
            peer_ip="203.0.113.10",
            x_forwarded_for="198.51.100.1, 203.0.113.10",
            x_real_ip="198.51.100.1",
            trusted_proxy_ips=[],
        )
        == "203.0.113.10"
    )

    # Trusted peer: walk XFF from the right, skip trusted hops.
    assert (
        resolve_client_ip(
            peer_ip="10.0.0.2",
            x_forwarded_for="198.51.100.7, 10.0.0.1, 10.0.0.2",
            x_real_ip=None,
            trusted_proxy_ips={"10.0.0.1", "10.0.0.2"},
        )
        == "198.51.100.7"
    )


def test_body_too_large_returns_413(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_REQUEST_BODY_BYTES", "2048")
    clear_demo_protection_settings_cache()

    client = TestClient(app)
    response = client.post(
        "/api/v1/research/copilot/query",
        content=b"x" * 4096,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()
