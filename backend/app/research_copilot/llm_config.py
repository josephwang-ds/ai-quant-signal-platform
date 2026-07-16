"""Resolve Research Copilot LLM provider settings from environment variables.

Exactly one OpenAI-compatible provider is active per deployment.
There is no multi-provider routing or failover.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

AllowedProvider = Literal["openai", "deepseek"]

ALLOWED_PROVIDERS: frozenset[str] = frozenset({"openai", "deepseek"})

PROVIDER_DEFAULT_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com",
}

PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    # Documented DeepSeek Chat Completions compatibility ID. Operators should
    # set COPILOT_MODEL to the account's current official model when available.
    "deepseek": "deepseek-chat",
}

# Both OpenAI and DeepSeek Chat Completions accept response_format=json_object.
PROVIDER_SUPPORTS_JSON_OBJECT: dict[str, bool] = {
    "openai": True,
    "deepseek": True,
}


class LlmConfigurationError(Exception):
    """Invalid or incomplete Copilot LLM configuration."""


@dataclass(frozen=True)
class LlmProviderSettings:
    provider: AllowedProvider
    api_key: str
    base_url: str
    model: str
    supports_response_format_json_object: bool
    chat_completions_url: str


def resolve_llm_provider_settings(
    *,
    environ: dict[str, str] | None = None,
    allow_insecure: bool | None = None,
) -> LlmProviderSettings:
    env = environ if environ is not None else dict(os.environ)
    provider = _resolve_provider(env)
    api_key = _resolve_api_key(env)
    if not api_key:
        raise LlmConfigurationError(
            "Research Copilot is not configured for this deployment."
        )

    base_url = _resolve_base_url(env, provider)
    validated_base = validate_llm_base_url(
        base_url,
        allow_insecure=_should_allow_insecure(env, allow_insecure),
    )
    model = (
        env.get("COPILOT_MODEL", "").strip()
        or PROVIDER_DEFAULT_MODELS[provider]
    )
    if not model:
        raise LlmConfigurationError(
            "Research Copilot model is not configured for this deployment."
        )

    return LlmProviderSettings(
        provider=provider,  # type: ignore[arg-type]
        api_key=api_key,
        base_url=validated_base,
        model=model,
        supports_response_format_json_object=PROVIDER_SUPPORTS_JSON_OBJECT[provider],
        chat_completions_url=build_chat_completions_url(validated_base),
    )


def build_chat_completions_url(base_url: str) -> str:
    """Append /chat/completions once; never duplicate path segments."""
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    return f"{normalized}/chat/completions"


def validate_llm_base_url(base_url: str, *, allow_insecure: bool = False) -> str:
    raw = base_url.strip()
    if not raw:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL is not configured."
        )

    parsed = urlparse(raw)
    if parsed.username or parsed.password:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must not include credentials."
        )
    if parsed.query:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must not include a query string."
        )
    if parsed.fragment:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must not include a URL fragment."
        )
    if not parsed.scheme or not parsed.netloc:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must be an absolute URL."
        )

    host = (parsed.hostname or "").lower()
    is_loopback = host in {"localhost", "127.0.0.1", "::1"}

    if parsed.scheme == "https":
        pass
    elif parsed.scheme == "http" and allow_insecure and is_loopback:
        pass
    else:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must use HTTPS "
            "(http://localhost is allowed only in local development/tests)."
        )

    if is_loopback and not allow_insecure:
        raise LlmConfigurationError(
            "Research Copilot LLM_BASE_URL must not target localhost in production."
        )

    # Rebuild without credentials/query/fragment; preserve path for /v1 etc.
    path = parsed.path.rstrip("/") if parsed.path not in {"", "/"} else ""
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _resolve_provider(env: dict[str, str]) -> AllowedProvider:
    raw = env.get("LLM_PROVIDER", "").strip().lower()
    if not raw:
        # Backward-compatible default when only legacy OpenAI key is present.
        if env.get("LLM_API_KEY", "").strip() or env.get("OPENAI_API_KEY", "").strip():
            return "openai"
        raise LlmConfigurationError(
            "Research Copilot is not configured for this deployment."
        )
    if raw not in ALLOWED_PROVIDERS:
        raise LlmConfigurationError(
            f"Unsupported LLM_PROVIDER '{raw}'. "
            f"Supported: {sorted(ALLOWED_PROVIDERS)}."
        )
    return raw  # type: ignore[return-value]


def _resolve_api_key(env: dict[str, str]) -> str:
    primary = env.get("LLM_API_KEY", "").strip()
    if primary:
        return primary
    # Deprecated fallback — prefer LLM_API_KEY going forward.
    return env.get("OPENAI_API_KEY", "").strip()


def _resolve_base_url(env: dict[str, str], provider: str) -> str:
    explicit = env.get("LLM_BASE_URL", "").strip()
    if explicit:
        return explicit
    # Legacy alias accepted temporarily for OpenAI-compatible deployments.
    legacy = env.get("OPENAI_BASE_URL", "").strip()
    if legacy:
        return legacy
    return PROVIDER_DEFAULT_BASE_URLS[provider]


def _should_allow_insecure(
    env: dict[str, str], override: bool | None
) -> bool:
    if override is not None:
        return override
    if env.get("LLM_ALLOW_INSECURE_BASE_URL", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }:
        return True
    if env.get("PYTEST_CURRENT_TEST"):
        return True
    runtime = (
        env.get("ENVIRONMENT")
        or env.get("APP_ENV")
        or env.get("NODE_ENV")
        or ""
    ).strip().lower()
    if runtime in {"development", "dev", "test", "local"}:
        return True
    if env.get("RENDER", "").strip().lower() in {"true", "1"}:
        return False
    if runtime == "production":
        return False
    # Default local / unset: allow loopback HTTP for adapter unit tests.
    return True
