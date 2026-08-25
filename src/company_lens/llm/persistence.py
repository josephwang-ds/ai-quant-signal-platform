"""Persist bounded retrieval and LLM provenance through the storage protocol."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from company_lens.llm.grounded import GroundedExplanationRequest
from company_lens.llm.retrieval import (
    ImportedDocument,
    RetrievalScope,
    RetrievedChunk,
)
from company_lens.llm.service import GenerationResult
from company_lens.storage import (
    EvidenceStorage,
    StoredChunk,
    StoredDocument,
    StoredHeadline,
    StoredLlmRun,
    StoredRetrievalRun,
    StoredRuleset,
)

READER_TRUST_POLICY_VERSION = "reader-policy-v1"


@dataclass(frozen=True)
class RetrievalPersistence:
    run_id: str
    ruleset_id: str | None
    index_version: str


def persist_retrieval(
    storage: EvidenceStorage,
    *,
    documents: list[ImportedDocument],
    chunks: list[RetrievedChunk],
    query: str,
    scope: RetrievalScope,
    reader_rules: tuple[str, ...] = (),
    latency_ms: int = 0,
    created_at: str | None = None,
) -> RetrievalPersistence:
    """Persist selected evidence and scope without storing local source paths."""
    timestamp = created_at or datetime.now(UTC).isoformat()
    for document in documents:
        storage.save_document(_stored_document(document))
        if document.source_type in {"company_news", "market_news"}:
            storage.save_headline(_stored_headline(document))
    storage.save_chunks(_stored_chunks(chunks))

    ruleset_id = None
    if reader_rules:
        ruleset_id = _stable_id(
            "ruleset",
            {
                "rules": reader_rules,
                "trust_policy_version": READER_TRUST_POLICY_VERSION,
            },
        )
        storage.save_ruleset(
            StoredRuleset(
                ruleset_id=ruleset_id,
                name="CLI reader rules",
                rules=reader_rules,
                trust_policy_version=READER_TRUST_POLICY_VERSION,
                created_at=timestamp,
            )
        )

    index_version = _stable_id(
        "index",
        sorted(document.document_id for document in documents),
    )
    run_id = _stable_id(
        "retrieval",
        {
            "created_at": timestamp,
            "query": query,
            "scope": scope.to_dict(),
            "selected_citations": [chunk.citation for chunk in chunks],
            "index_version": index_version,
        },
    )
    storage.save_retrieval_run(
        StoredRetrievalRun(
            run_id=run_id,
            query=query,
            scope=scope.to_dict(),
            selected_citations=tuple(chunk.citation for chunk in chunks),
            index_version=index_version,
            latency_ms=max(0, latency_ms),
            created_at=timestamp,
        )
    )
    return RetrievalPersistence(
        run_id=run_id,
        ruleset_id=ruleset_id,
        index_version=index_version,
    )


def persist_llm_provenance(
    storage: EvidenceStorage,
    *,
    request: GroundedExplanationRequest,
    result: GenerationResult,
    created_at: str | None = None,
) -> str:
    """Persist generation provenance, never provider secrets or raw errors."""
    timestamp = created_at or datetime.now(UTC).isoformat()
    evidence_hash = hashlib.sha256(
        json.dumps(
            request.evidence,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    run_id = _stable_id(
        "llm",
        {
            "created_at": timestamp,
            "cache_key": result.cache_key,
            "evidence_hash": evidence_hash,
        },
    )
    status = (
        "deterministic_fallback"
        if result.fallback_reason
        else "cache_hit"
        if result.cache_hit
        else "validated"
    )
    storage.save_llm_run(
        StoredLlmRun(
            run_id=run_id,
            provider=result.provider,
            model=result.model,
            prompt_version=request.prompt_version,
            evidence_hash=evidence_hash,
            validator_status=status,
            usage={},
            cost={},
            created_at=timestamp,
        )
    )
    return run_id


def _stored_document(document: ImportedDocument) -> StoredDocument:
    return StoredDocument(
        document_id=document.document_id,
        source_type=document.source_type,
        title=document.title,
        content_hash=(
            "sha256:" + hashlib.sha256(document.text.encode("utf-8")).hexdigest()
        ),
        ticker=document.ticker,
        source_url=document.source_url or None,
        published_at=document.published_at,
        fetched_at=document.fetched_at,
    )


def _stored_headline(document: ImportedDocument) -> StoredHeadline:
    if not document.published_at or not document.source_url:
        raise ValueError("headline documents require published_at and source_url")
    return StoredHeadline(
        headline_id=document.document_id,
        headline=document.title,
        publisher=document.source_name,
        published_at=document.published_at,
        fetched_at=document.fetched_at,
        url=document.source_url,
        source_type=document.source_type,
        tickers=document.tickers,
        topic=document.topic,
    )


def _stored_chunks(chunks: list[RetrievedChunk]) -> list[StoredChunk]:
    return [
        StoredChunk(
            citation=chunk.citation,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            metadata={
                "title": chunk.title,
                "source_type": chunk.source_type,
                "source_name": chunk.source_name,
                "source_url": chunk.source_url,
                "published_at": chunk.published_at,
                "fetched_at": chunk.fetched_at,
                "score": round(chunk.score, 4),
                "ticker": chunk.ticker,
                "tags": list(chunk.tags),
            },
        )
        for chunk in chunks
    ]


def _stable_id(prefix: str, value: object) -> str:
    digest = hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:20]
    return f"{prefix}-{digest}"
