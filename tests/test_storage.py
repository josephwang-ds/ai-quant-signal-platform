from __future__ import annotations

import pytest

from company_lens.llm.grounded import GroundedExplanationRequest
from company_lens.llm.persistence import persist_llm_provenance, persist_retrieval
from company_lens.llm.retrieval import ImportedDocument, RetrievalScope, RetrievedChunk
from company_lens.llm.service import GenerationResult
from company_lens.storage import (
    LocalJsonStorage,
    StoredChunk,
    StoredDocument,
    StoredHeadline,
    StoredLlmRun,
    StoredRetrievalRun,
    StoredRuleset,
)


def test_local_json_storage_persists_each_boundary_record(tmp_path) -> None:
    storage = LocalJsonStorage(tmp_path / "storage")
    storage.save_document(
        StoredDocument(
            document_id="doc-one",
            source_type="uploaded",
            title="Local note",
            content_hash="sha256:abc",
            ticker="AAPL",
            owner_id="local-user",
        )
    )
    storage.save_chunks(
        [
            StoredChunk(
                citation="document:doc-one#chunk-0",
                document_id="doc-one",
                chunk_index=0,
                text="Untrusted evidence text.",
                metadata={"source": "local"},
            )
        ]
    )
    storage.save_headline(
        StoredHeadline(
            headline_id="headline-one",
            headline="Company update",
            publisher="Example Wire",
            published_at="2026-08-25T09:00:00+00:00",
            url="https://example.com/update",
            source_type="company_news",
            tickers=("AAPL",),
        )
    )
    storage.save_ruleset(
        StoredRuleset(
            ruleset_id="rules-one",
            name="Plain language",
            rules=("Explain legal terms.",),
            trust_policy_version="v1",
            created_at="2026-08-25T09:00:00+00:00",
            owner_id="local-user",
        )
    )
    storage.save_retrieval_run(
        StoredRetrievalRun(
            run_id="retrieval-one",
            query="management changes",
            scope={"ticker": "AAPL", "max_chunks": 3},
            selected_citations=("document:doc-one#chunk-0",),
            index_version="local-v1",
            latency_ms=4,
            created_at="2026-08-25T09:00:00+00:00",
            owner_id="local-user",
        )
    )
    storage.save_llm_run(
        StoredLlmRun(
            run_id="llm-one",
            provider="fallback",
            model="deterministic",
            prompt_version="v2",
            evidence_hash="sha256:def",
            validator_status="passed",
            usage={},
            cost={},
            created_at="2026-08-25T09:00:00+00:00",
            owner_id="local-user",
        )
    )

    assert storage.get("documents", "doc-one")["ticker"] == "AAPL"
    assert storage.get("chunks", "document:doc-one#chunk-0")["chunk_index"] == 0
    assert storage.get("headlines", "headline-one")["tickers"] == ["AAPL"]
    assert storage.get("rulesets", "rules-one")["trust_policy_version"] == "v1"
    assert storage.get("retrieval_runs", "retrieval-one")["latency_ms"] == 4
    assert storage.get("llm_runs", "llm-one")["validator_status"] == "passed"
    assert not list((tmp_path / "storage").glob("*.tmp"))


def test_local_json_storage_rejects_control_characters_in_ids(tmp_path) -> None:
    storage = LocalJsonStorage(tmp_path / "storage")

    with pytest.raises(ValueError, match="printable"):
        storage.save_document(
            StoredDocument(
                document_id="bad\nid",
                source_type="uploaded",
                title="Bad ID",
                content_hash="sha256:abc",
            )
        )


def test_retrieval_and_fallback_provenance_persist_end_to_end_without_cloud(
    tmp_path,
) -> None:
    storage = LocalJsonStorage(tmp_path / "storage")
    documents = [
        ImportedDocument(
            document_id="doc-note",
            title="Local note",
            text="Revenue was $45 million.",
            ticker="AAPL",
            source_name="note.md",
        ),
        ImportedDocument(
            document_id="headline-one",
            title="Apple updates reporting",
            text="Headline: Apple updates reporting",
            source_type="company_news",
            ticker="AAPL",
            tags=("earnings", "AAPL"),
            source_name="Example Wire",
            source_url="https://example.com/apple",
            published_at="2026-08-25T09:00:00+00:00",
            fetched_at="2026-08-25T09:05:00+00:00",
            tickers=("AAPL",),
            topic="earnings",
        ),
    ]
    chunks = [
        RetrievedChunk(
            citation="document:doc-note#chunk-0",
            document_id="doc-note",
            title="Local note",
            text="Revenue was $45 million.",
            source_type="uploaded",
            source_name="note.md",
            source_url="",
            published_at=None,
            fetched_at=None,
            score=0.9,
            chunk_index=0,
            ticker="AAPL",
            tags=(),
        )
    ]
    scope = RetrievalScope(ticker="AAPL", max_chunks=3, min_relevance=0)
    persisted = persist_retrieval(
        storage,
        documents=documents,
        chunks=chunks,
        query="revenue reporting",
        scope=scope,
        reader_rules=("Explain legal terms plainly.",),
        latency_ms=7,
        created_at="2026-08-25T09:10:00+00:00",
    )
    request = GroundedExplanationRequest(
        ticker="AAPL",
        accession="0001",
        prompt_version="v2",
        language="English",
        depth="beginner",
        evidence={"retrieval": {"citations": [chunks[0].citation]}},
        allowed_citations=frozenset({chunks[0].citation}),
        allowed_number_literals=frozenset({"$45"}),
    )
    llm_run_id = persist_llm_provenance(
        storage,
        request=request,
        result=GenerationResult(
            explanation={"mode": "deterministic_fallback"},
            provider="openai",
            model="test-model",
            cache_key="cache-one",
            cache_hit=False,
            fallback_reason="Authorization: Bearer must-not-persist",
        ),
        created_at="2026-08-25T09:11:00+00:00",
    )

    assert len(storage.list_records("documents")) == 2
    assert storage.get("headlines", "headline-one")["publisher"] == "Example Wire"
    assert storage.get("chunks", chunks[0].citation)["metadata"]["score"] == 0.9
    assert storage.get("rulesets", persisted.ruleset_id)["rules"] == [
        "Explain legal terms plainly."
    ]
    assert storage.get("retrieval_runs", persisted.run_id)["latency_ms"] == 7
    assert (
        storage.get("llm_runs", llm_run_id)["validator_status"]
        == "deterministic_fallback"
    )
    stored_text = "".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / "storage").glob("*.json")
    )
    assert "must-not-persist" not in stored_text
    assert "/Users/" not in stored_text


def test_only_the_local_backend_exists() -> None:
    """A PostgREST adapter and a dual-write mode lived here until 2026-08-28.

    They were removed rather than kept, and the code worked -- it had passed a
    controlled live write/read/cleanup test. What it never had was a caller.
    It was carrying four environment variables, a SQL migration, a page of
    operating documentation and a credential class that must never reach a
    browser, all for a path no run took. This asserts they stay gone: an
    unselected backend with a security surface is not free.
    """
    from company_lens.storage import StorageConfigurationError, create_storage

    for removed in ("supabase", "dual"):
        with pytest.raises(StorageConfigurationError, match="only 'local' remains"):
            create_storage(removed)


