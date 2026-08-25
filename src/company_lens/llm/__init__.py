"""Grounded explanation contracts and provider-independent fallbacks."""

from company_lens.llm.compatible_providers import (
    AnthropicMessagesProvider,
    DeepSeekResponsesProvider,
    GeminiInteractionsProvider,
    QwenChatProvider,
    create_explanation_provider,
)
from company_lens.llm.evaluation import (
    PILOT_THRESHOLDS,
    evaluate_provider_run,
    load_grounded_cases,
    load_provider_run,
)
from company_lens.llm.evidence import PROMPT_VERSION, build_grounded_request
from company_lens.llm.explain import deterministic_explanation
from company_lens.llm.grounded import (
    ExplanationProvider,
    GroundedExplanationRequest,
    ValidationResult,
    explanation_cache_key,
    validate_grounded_explanation,
)
from company_lens.llm.headlines import import_headline_index
from company_lens.llm.openai_provider import OpenAIResponsesProvider
from company_lens.llm.persistence import (
    RetrievalPersistence,
    persist_llm_provenance,
    persist_retrieval,
)
from company_lens.llm.retrieval import (
    ImportedDocument,
    LocalDocumentRetriever,
    RetrievalScope,
    RetrievedChunk,
    extend_request_with_retrieval,
    import_document,
    split_text,
    validate_reader_rules,
)
from company_lens.llm.service import (
    GenerationResult,
    JsonExplanationCache,
    generate_with_fallback,
)

__all__ = [
    "PILOT_THRESHOLDS",
    "PROMPT_VERSION",
    "AnthropicMessagesProvider",
    "DeepSeekResponsesProvider",
    "ExplanationProvider",
    "GeminiInteractionsProvider",
    "GenerationResult",
    "GroundedExplanationRequest",
    "ImportedDocument",
    "JsonExplanationCache",
    "LocalDocumentRetriever",
    "OpenAIResponsesProvider",
    "QwenChatProvider",
    "RetrievalPersistence",
    "RetrievalScope",
    "RetrievedChunk",
    "ValidationResult",
    "build_grounded_request",
    "create_explanation_provider",
    "deterministic_explanation",
    "evaluate_provider_run",
    "explanation_cache_key",
    "extend_request_with_retrieval",
    "generate_with_fallback",
    "import_document",
    "import_headline_index",
    "load_grounded_cases",
    "load_provider_run",
    "persist_llm_provenance",
    "persist_retrieval",
    "split_text",
    "validate_grounded_explanation",
    "validate_reader_rules",
]
