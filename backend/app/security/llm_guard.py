"""LLM port wrapper: bounded concurrency + configured timeout + safe logging."""

from __future__ import annotations

import logging
from typing import Any

from app.research_copilot.llm_port import ContextItem, LlmPort, LlmResult
from app.security.concurrency import LlmConcurrencyFullError, acquire_llm_slot
from app.security.logging_redaction import safe_log_extra
from app.security.settings import get_demo_protection_settings

logger = logging.getLogger("app.security.llm")


class GuardedLlmAdapter:
    """Decorate an LlmPort with demo concurrency and operational log hygiene."""

    def __init__(self, inner: LlmPort) -> None:
        self._inner = inner
        # Preserve common metadata attributes used by Governance Agent.
        self.model = getattr(inner, "model", None)
        self.provider = getattr(inner, "provider", None)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        context: list[ContextItem],
    ) -> LlmResult:
        # Do not log prompts, context, or chain-of-thought.
        with acquire_llm_slot():
            result = self._inner.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context,
            )

        usage = getattr(result, "token_usage", None) or {}
        logger.info(
            "llm_call_completed",
            extra=safe_log_extra(
                {
                    "provider": getattr(self, "provider", None),
                    "model": result.model,
                    "latency_ms": result.latency_ms,
                    "status": "ok",
                    "prompt_tokens": usage.get("prompt_tokens")
                    if isinstance(usage, dict)
                    else None,
                    "completion_tokens": usage.get("completion_tokens")
                    if isinstance(usage, dict)
                    else None,
                    "total_tokens": usage.get("total_tokens")
                    if isinstance(usage, dict)
                    else None,
                }
            ),
        )
        return result


def wrap_llm_adapter(adapter: LlmPort) -> LlmPort:
    """Apply concurrency guard. Timeout is configured on the HTTP adapter."""
    return GuardedLlmAdapter(adapter)


def apply_llm_timeout(adapter: Any) -> Any:
    """Stamp configured LLM timeout onto adapters that expose timeout_seconds."""
    timeout = get_demo_protection_settings().llm_timeout_seconds
    if hasattr(adapter, "timeout_seconds"):
        adapter.timeout_seconds = timeout
    return adapter


__all__ = [
    "GuardedLlmAdapter",
    "LlmConcurrencyFullError",
    "apply_llm_timeout",
    "wrap_llm_adapter",
]
