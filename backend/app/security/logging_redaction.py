"""Log hygiene helpers — never emit secrets, DB URLs, or raw prompts."""

from __future__ import annotations

import re
from typing import Any, Mapping

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token|password|secret)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+/=]+"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9]{10,}"),
    re.compile(
        r"(?i)\b(?:postgres|postgresql|mysql|mongodb(?:\+srv)?)://[^\s\"']+"
    ),
    re.compile(r"(?i)\bSUPABASE_DB_URL\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bLLM_API_KEY\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bOPENAI_API_KEY\b\s*[:=]\s*\S+"),
)

_BLOCKED_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "supabase_db_url",
        "database_url",
        "db_url",
        "system_prompt",
        "user_prompt",
        "prompt",
        "raw_prompt",
        "chain_of_thought",
        "reasoning",
        "cot",
        "messages",
    }
)

_SAFE_KEYS = frozenset(
    {
        "run_id",
        "agent_run_id",
        "validation_run_id",
        "endpoint",
        "path",
        "method",
        "duration_ms",
        "latency_ms",
        "status",
        "status_code",
        "provider",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "token_usage",
        "tier",
        "client_ip_hash",
    }
)


def redact_secrets(value: str) -> str:
    """Redact credential-like substrings from a log string."""
    if not value:
        return value
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def safe_log_extra(payload: Mapping[str, Any]) -> dict[str, Any]:
    """
    Filter a structured log payload to safe operational fields.

    Allowed: run ids, endpoint, duration, status, token usage.
    Rejected: API keys, DB URLs, raw prompts, chain-of-thought.
    """
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        normalized = str(key).strip().lower()
        if normalized in _BLOCKED_KEYS:
            continue
        if normalized not in _SAFE_KEYS and not normalized.endswith("_id"):
            continue
        if isinstance(value, str):
            safe[key] = redact_secrets(value)
        elif isinstance(value, (int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = redact_secrets(str(value))
    return safe
