"""Public-demo request protection: limits, rate limiting, LLM concurrency, log hygiene."""

from app.security.concurrency import (
    LlmConcurrencyFullError,
    acquire_llm_slot,
    get_llm_semaphore,
    reset_llm_concurrency_for_tests,
)
from app.security.limits import (
    MAX_CONVERSATION_TURN_LENGTH,
    MAX_NOTES_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_QUESTION_LENGTH,
    MAX_RATIONALE_LENGTH,
    MAX_SYMBOL_LIST_LENGTH,
)
from app.security.logging_redaction import redact_secrets, safe_log_extra
from app.security.rate_limit import (
    RateLimitExceeded,
    check_rate_limit,
    classify_endpoint,
    reset_rate_limiter_for_tests,
)
from app.security.settings import (
    DemoProtectionSettings,
    clear_demo_protection_settings_cache,
    get_demo_protection_settings,
)

__all__ = [
    "DemoProtectionSettings",
    "LlmConcurrencyFullError",
    "MAX_CONVERSATION_TURN_LENGTH",
    "MAX_NOTES_LENGTH",
    "MAX_PROMPT_LENGTH",
    "MAX_QUESTION_LENGTH",
    "MAX_RATIONALE_LENGTH",
    "MAX_SYMBOL_LIST_LENGTH",
    "RateLimitExceeded",
    "acquire_llm_slot",
    "check_rate_limit",
    "classify_endpoint",
    "clear_demo_protection_settings_cache",
    "get_demo_protection_settings",
    "get_llm_semaphore",
    "redact_secrets",
    "reset_llm_concurrency_for_tests",
    "reset_rate_limiter_for_tests",
    "safe_log_extra",
]
