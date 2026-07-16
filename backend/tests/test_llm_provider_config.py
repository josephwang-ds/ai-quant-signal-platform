"""Offline tests for OpenAI-compatible Copilot LLM configuration and adapter."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from app.research_copilot.llm_config import (
    LlmConfigurationError,
    build_chat_completions_url,
    resolve_llm_provider_settings,
    validate_llm_base_url,
)
from app.research_copilot.llm_port import ContextItem
from app.research_copilot.openai_adapter import (
    OpenAiCompatibleLlmAdapter,
    ProviderAuthenticationError,
    ProviderMalformedResponseError,
    ProviderUnavailableError,
)
from app.research_copilot.service import ResearchCopilotError, resolve_llm_adapter


def test_openai_default_base_url() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
        },
        allow_insecure=False,
    )
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.chat_completions_url == (
        "https://api.openai.com/v1/chat/completions"
    )
    assert settings.model == "gpt-4o-mini"
    assert settings.supports_response_format_json_object is True


def test_deepseek_default_base_url() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "deepseek",
            "LLM_API_KEY": "sk-deepseek",
        },
        allow_insecure=False,
    )
    assert settings.base_url == "https://api.deepseek.com"
    assert settings.chat_completions_url == (
        "https://api.deepseek.com/chat/completions"
    )
    assert settings.model == "deepseek-chat"


def test_explicit_base_url_and_trailing_slash_normalization() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
            "LLM_BASE_URL": "https://api.openai.com/v1/",
            "COPILOT_MODEL": "gpt-4o-mini",
        },
        allow_insecure=False,
    )
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.chat_completions_url == (
        "https://api.openai.com/v1/chat/completions"
    )
    assert "/v1/v1/" not in settings.chat_completions_url


def test_build_chat_completions_url_does_not_duplicate_path() -> None:
    assert (
        build_chat_completions_url("https://api.deepseek.com/chat/completions")
        == "https://api.deepseek.com/chat/completions"
    )
    assert (
        build_chat_completions_url("https://api.openai.com/v1/chat/completions/")
        == "https://api.openai.com/v1/chat/completions"
    )


def test_legacy_openai_api_key_fallback() -> None:
    settings = resolve_llm_provider_settings(
        environ={"OPENAI_API_KEY": "sk-legacy"},
        allow_insecure=False,
    )
    assert settings.provider == "openai"
    assert settings.api_key == "sk-legacy"


def test_llm_api_key_takes_precedence_over_legacy() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "deepseek",
            "LLM_API_KEY": "sk-primary",
            "OPENAI_API_KEY": "sk-legacy",
            "COPILOT_MODEL": "deepseek-chat",
        },
        allow_insecure=False,
    )
    assert settings.api_key == "sk-primary"
    assert settings.provider == "deepseek"


def test_unknown_provider_rejected() -> None:
    with pytest.raises(LlmConfigurationError, match="Unsupported LLM_PROVIDER"):
        resolve_llm_provider_settings(
            environ={
                "LLM_PROVIDER": "anthropic",
                "LLM_API_KEY": "sk-test",
            }
        )


def test_missing_key_returns_503_via_resolve_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with pytest.raises(ResearchCopilotError) as exc:
        resolve_llm_adapter()
    assert exc.value.status_code == 503


def test_invalid_and_non_https_base_url_rejected() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS"):
        validate_llm_base_url("http://api.openai.com/v1", allow_insecure=False)
    with pytest.raises(LlmConfigurationError, match="absolute URL"):
        validate_llm_base_url("not-a-url", allow_insecure=False)


def test_credentials_query_and_fragment_rejected() -> None:
    with pytest.raises(LlmConfigurationError, match="credentials"):
        validate_llm_base_url(
            "https://user:pass@api.openai.com/v1", allow_insecure=False
        )
    with pytest.raises(LlmConfigurationError, match="query string"):
        validate_llm_base_url(
            "https://api.openai.com/v1?x=1", allow_insecure=False
        )
    with pytest.raises(LlmConfigurationError, match="fragment"):
        validate_llm_base_url(
            "https://api.openai.com/v1#frag", allow_insecure=False
        )


def test_localhost_rejected_in_production_mode() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS|localhost"):
        validate_llm_base_url("http://127.0.0.1:4010/v1", allow_insecure=False)


def test_production_ignores_llm_allow_insecure_env_on_render() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS|localhost"):
        resolve_llm_provider_settings(
            environ={
                "RENDER": "true",
                "LLM_ALLOW_INSECURE_BASE_URL": "true",
                "LLM_PROVIDER": "openai",
                "LLM_API_KEY": "sk-test",
                "LLM_BASE_URL": "http://127.0.0.1:4010/v1",
            },
            allow_insecure=None,
        )


def test_production_ignores_explicit_allow_insecure_override() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS|localhost"):
        resolve_llm_provider_settings(
            environ={
                "ENVIRONMENT": "production",
                "LLM_PROVIDER": "openai",
                "LLM_API_KEY": "sk-test",
                "LLM_BASE_URL": "http://localhost:4010/v1",
            },
            allow_insecure=True,
        )


def test_app_env_production_rejects_http_localhost() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS|localhost"):
        resolve_llm_provider_settings(
            environ={
                "APP_ENV": "production",
                "LLM_PROVIDER": "openai",
                "LLM_API_KEY": "sk-test",
                "LLM_BASE_URL": "http://127.0.0.1:4010/v1",
            }
        )


def test_development_allows_http_localhost() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "ENVIRONMENT": "development",
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
            "LLM_BASE_URL": "http://127.0.0.1:4010/v1",
        }
    )
    assert settings.base_url == "http://127.0.0.1:4010/v1"
    assert settings.chat_completions_url == (
        "http://127.0.0.1:4010/v1/chat/completions"
    )


def test_pytest_allows_http_localhost() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "PYTEST_CURRENT_TEST": "test_pytest_allows_http_localhost",
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
            "LLM_BASE_URL": "http://localhost:4010/v1",
        }
    )
    assert settings.base_url == "http://localhost:4010/v1"


def test_development_rejects_remote_http_host() -> None:
    with pytest.raises(LlmConfigurationError, match="HTTPS"):
        resolve_llm_provider_settings(
            environ={
                "ENVIRONMENT": "development",
                "LLM_ALLOW_INSECURE_BASE_URL": "true",
                "LLM_PROVIDER": "openai",
                "LLM_API_KEY": "sk-test",
                "LLM_BASE_URL": "http://api.example.com/v1",
            },
            allow_insecure=True,
        )


def test_production_accepts_https_deepseek_url() -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "ENVIRONMENT": "production",
            "LLM_PROVIDER": "deepseek",
            "LLM_API_KEY": "sk-deepseek",
            "LLM_BASE_URL": "https://api.deepseek.com",
            "COPILOT_MODEL": "deepseek-chat",
        },
        allow_insecure=True,
    )
    assert settings.base_url == "https://api.deepseek.com"
    assert settings.chat_completions_url == (
        "https://api.deepseek.com/chat/completions"
    )


def test_adapter_uses_bearer_auth_model_and_json_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "deepseek",
            "LLM_API_KEY": "sk-deepseek",
            "COPILOT_MODEL": "deepseek-chat",
        },
        allow_insecure=False,
    )
    adapter = OpenAiCompatibleLlmAdapter(settings=settings, timeout_seconds=12.0)
    captured: dict = {}

    class _FakeResponse:
        def read(self) -> bytes:
            return json.dumps(
                {
                    "model": "deepseek-chat",
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "answer": "Evaluation is incomplete.",
                                        "citation_ids": ["evaluation:status"],
                                    }
                                )
                            },
                            "finish_reason": "stop",
                        }
                    ],
                }
            ).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse()

    monkeypatch.setattr(
        "app.research_copilot.openai_adapter.urllib.request.urlopen",
        fake_urlopen,
    )

    result = adapter.generate(
        system_prompt="Return ONLY valid JSON.",
        user_prompt="Why is evaluation incomplete?",
        context=[
            ContextItem(
                citation_id="evaluation:status",
                source_type="evaluation",
                source_id="status",
                label="Evaluation status",
                content="status=incomplete",
            )
        ],
    )

    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["authorization"] == "Bearer sk-deepseek"
    assert captured["timeout"] == 12.0
    assert captured["body"]["model"] == "deepseek-chat"
    assert captured["body"]["response_format"] == {"type": "json_object"}
    assert result.model == "deepseek-chat"
    parsed = json.loads(result.text)
    assert parsed["citation_ids"] == ["evaluation:status"]


def test_adapter_maps_auth_and_malformed_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
        },
        allow_insecure=False,
    )
    adapter = OpenAiCompatibleLlmAdapter(settings=settings)

    def auth_fail(_request, timeout=None):
        raise HTTPError(
            "https://api.openai.com/v1/chat/completions",
            401,
            "Unauthorized",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )

    monkeypatch.setattr(
        "app.research_copilot.openai_adapter.urllib.request.urlopen",
        auth_fail,
    )
    with pytest.raises(ProviderAuthenticationError):
        adapter.generate(
            system_prompt="x",
            user_prompt="y",
            context=[],
        )

    class _BadJson:
        def read(self) -> bytes:
            return b"not-json"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "app.research_copilot.openai_adapter.urllib.request.urlopen",
        lambda *_a, **_k: _BadJson(),
    )
    with pytest.raises(ProviderMalformedResponseError):
        adapter.generate(system_prompt="x", user_prompt="y", context=[])


def test_adapter_maps_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = resolve_llm_provider_settings(
        environ={
            "LLM_PROVIDER": "openai",
            "LLM_API_KEY": "sk-test",
        },
        allow_insecure=False,
    )
    adapter = OpenAiCompatibleLlmAdapter(settings=settings)

    def rate_limited(_request, timeout=None):
        raise HTTPError(
            "https://api.openai.com/v1/chat/completions",
            429,
            "Too Many Requests",
            hdrs=None,  # type: ignore[arg-type]
            fp=None,
        )

    monkeypatch.setattr(
        "app.research_copilot.openai_adapter.urllib.request.urlopen",
        rate_limited,
    )
    with pytest.raises(ProviderUnavailableError, match="rate limited"):
        adapter.generate(system_prompt="x", user_prompt="y", context=[])


def test_frontend_does_not_call_providers_or_ship_llm_keys() -> None:
    frontend_root = Path(__file__).resolve().parents[2] / "frontend"
    env_example = (frontend_root / ".env.example").read_text(encoding="utf-8")
    assert "NEXT_PUBLIC_LLM" not in env_example
    assert "NEXT_PUBLIC_OPENAI" not in env_example
    assert "NEXT_PUBLIC_DEEPSEEK" not in env_example

    source_files = [
        path
        for path in frontend_root.rglob("*")
        if path.is_file()
        and path.suffix in {".ts", ".tsx"}
        and "node_modules" not in path.parts
        and ".next" not in path.parts
    ]
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in source_files
    )
    assert "api.deepseek.com" not in combined
    assert "api.openai.com" not in combined
    assert "LLM_API_KEY" not in combined
    assert 'from "openai"' not in combined
    assert "from 'openai'" not in combined
    assert "NEXT_PUBLIC_OPENAI_API_KEY" not in combined
    assert "NEXT_PUBLIC_LLM_API_KEY" not in combined
