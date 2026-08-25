from __future__ import annotations

from typing import Any

import pytest
import requests

from company_lens.storage import (
    DualWriteStorage,
    LocalJsonStorage,
    StorageConfigurationError,
    StoredChunk,
    StoredDocument,
    StoredHeadline,
    StoredLlmRun,
    StoredRetrievalRun,
    StoredRuleset,
    SupabaseStorage,
    SupabaseStorageError,
    create_storage,
)

KEY = "sb_secret_test-secret"
LEGACY_JWT = "eyJhbGciOiJIUzI1NiJ9.legacy-service-role.signature"
PUBLISHABLE_KEY = "sb_publishable_test-key"
URL = "https://example.supabase.co"


class FakeResponse:
    def __init__(self, status_code: int = 201, payload: Any = None) -> None:
        self.status_code = status_code
        self.payload = payload
        self.text = f"Authorization: Bearer {KEY}; private document body"

    def json(self) -> Any:
        return self.payload


class FakeSession:
    def __init__(
        self,
        responses: list[FakeResponse] | None = None,
        failure: Exception | None = None,
    ) -> None:
        self.responses = list(responses or [])
        self.failure = failure
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        if self.failure is not None:
            raise self.failure
        return self.responses.pop(0) if self.responses else FakeResponse()


def _records() -> tuple[
    StoredDocument,
    tuple[StoredChunk, ...],
    StoredHeadline,
    StoredRuleset,
    StoredRetrievalRun,
    StoredLlmRun,
]:
    document = StoredDocument(
        document_id="doc-one",
        source_type="uploaded",
        title="Private note",
        content_hash="sha256:abc",
        ticker="AAPL",
        owner_id="00000000-0000-0000-0000-000000000001",
    )
    chunks = (
        StoredChunk(
            citation="document:doc-one#chunk-0",
            document_id=document.document_id,
            chunk_index=0,
            text="Private document body.",
            metadata={"tags": ("earnings", "risk")},
        ),
        StoredChunk(
            citation="document:doc-one#chunk-1",
            document_id=document.document_id,
            chunk_index=1,
            text="Second chunk.",
            metadata={},
        ),
    )
    headline = StoredHeadline(
        headline_id="headline-one",
        headline="Company update",
        publisher="Example Wire",
        published_at="2026-08-25T09:00:00+00:00",
        url="https://example.com/update",
        source_type="company_news",
        tickers=("AAPL", "MSFT"),
    )
    ruleset = StoredRuleset(
        ruleset_id="rules-one",
        name="Plain language",
        rules=("Explain legal terms.", "Do not forecast."),
        trust_policy_version="v1",
        created_at="2026-08-25T09:00:00+00:00",
    )
    retrieval = StoredRetrievalRun(
        run_id="retrieval-one",
        query="material changes",
        scope={"ticker": "AAPL"},
        selected_citations=(chunks[0].citation, chunks[1].citation),
        index_version="index-v1",
        latency_ms=8,
        created_at="2026-08-25T09:01:00+00:00",
    )
    llm = StoredLlmRun(
        run_id="llm-one",
        provider="fallback",
        model="deterministic",
        prompt_version="v2",
        evidence_hash="sha256:def",
        validator_status="passed",
        usage={},
        cost={},
        created_at="2026-08-25T09:02:00+00:00",
    )
    return document, chunks, headline, ruleset, retrieval, llm


def test_supabase_maps_every_record_batches_chunks_and_uses_primary_keys() -> None:
    session = FakeSession()
    storage = SupabaseStorage(URL, KEY, session=session, timeout=4.5)
    document, chunks, headline, ruleset, retrieval, llm = _records()

    storage.save_document(document)
    storage.save_chunks(chunks)
    storage.save_headline(headline)
    storage.save_ruleset(ruleset)
    storage.save_retrieval_run(retrieval)
    storage.save_llm_run(llm)

    assert [call["url"].rsplit("/", 1)[-1] for call in session.calls] == [
        "documents",
        "document_chunks",
        "headlines",
        "rulesets",
        "retrieval_runs",
        "llm_runs",
    ]
    assert [call["params"]["on_conflict"] for call in session.calls] == [
        "document_id",
        "citation",
        "headline_id",
        "ruleset_id",
        "run_id",
        "run_id",
    ]
    assert all(call["method"] == "POST" for call in session.calls)
    assert all(call["timeout"] == 4.5 for call in session.calls)
    assert len(session.calls[1]["json"]) == 2
    assert session.calls[2]["json"]["tickers"] == ["AAPL", "MSFT"]
    assert session.calls[3]["json"]["rules"] == ["Explain legal terms.", "Do not forecast."]
    assert session.calls[4]["json"]["selected_citations"] == [
        "document:doc-one#chunk-0",
        "document:doc-one#chunk-1",
    ]
    assert session.calls[1]["json"][0]["metadata"]["tags"] == ["earnings", "risk"]


def test_current_secret_key_sends_only_apikey_header() -> None:
    session = FakeSession()
    storage = SupabaseStorage(URL, KEY, session=session)

    storage.save_document(_records()[0])

    headers = session.calls[0]["headers"]
    assert headers["apikey"] == KEY
    assert "Authorization" not in headers


def test_legacy_service_role_jwt_sends_apikey_and_bearer_headers() -> None:
    session = FakeSession()
    storage = SupabaseStorage(URL, LEGACY_JWT, session=session)

    storage.save_document(_records()[0])

    headers = session.calls[0]["headers"]
    assert headers["apikey"] == LEGACY_JWT
    assert headers["Authorization"] == f"Bearer {LEGACY_JWT}"


def test_supabase_get_and_list_are_bounded_and_deterministic() -> None:
    session = FakeSession(
        [
            FakeResponse(200, [{"document_id": "doc-one", "title": "One"}]),
            FakeResponse(200, []),
            FakeResponse(
                200,
                [
                    {"headline_id": "headline-z"},
                    {"headline_id": "headline-a"},
                ],
            ),
        ]
    )
    storage = SupabaseStorage(URL, KEY, session=session)

    assert storage.get("documents", "doc-one") == {
        "document_id": "doc-one",
        "title": "One",
    }
    assert storage.get("documents", "missing") is None
    assert [row["headline_id"] for row in storage.list_records("headlines")] == [
        "headline-a",
        "headline-z",
    ]
    assert session.calls[0]["params"] == {
        "select": "*",
        "document_id": "eq.doc-one",
        "limit": "1",
    }
    assert session.calls[2]["params"]["order"] == "headline_id.asc"


@pytest.mark.parametrize("status_code", [401, 403, 500])
def test_supabase_http_errors_are_actionable_and_secret_free(status_code: int) -> None:
    session = FakeSession([FakeResponse(status_code)])
    storage = SupabaseStorage(URL, KEY, session=session)

    with pytest.raises(SupabaseStorageError) as error:
        storage.save_document(_records()[0])

    message = str(error.value)
    assert str(status_code) in message
    assert KEY not in message
    assert "Authorization" not in message
    assert "private document body" not in message


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (requests.Timeout(f"Authorization: Bearer {KEY}"), "timed out"),
        (requests.ConnectionError("private document body"), "could not connect"),
    ],
)
def test_supabase_transport_errors_are_actionable_and_secret_free(
    failure: Exception,
    expected: str,
) -> None:
    storage = SupabaseStorage(URL, KEY, session=FakeSession(failure=failure))

    with pytest.raises(SupabaseStorageError) as error:
        storage.save_document(_records()[0])

    message = str(error.value)
    assert expected in message
    assert KEY not in message
    assert "Authorization" not in message
    assert "private document body" not in message


def test_storage_factory_defaults_local_without_reading_supabase_env(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "not-a-url")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", KEY)

    storage = create_storage(storage_dir=tmp_path / "storage")

    assert isinstance(storage, LocalJsonStorage)


def test_secret_key_environment_takes_precedence_over_legacy(
    tmp_path,
    monkeypatch,
) -> None:
    session = FakeSession()
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_SECRET_KEY", KEY)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", LEGACY_JWT)

    storage = create_storage("supabase", tmp_path / "storage", session=session)
    storage.save_document(_records()[0])

    headers = session.calls[0]["headers"]
    assert headers["apikey"] == KEY
    assert "Authorization" not in headers


def test_explicit_key_takes_precedence_over_both_environment_keys(
    tmp_path,
    monkeypatch,
) -> None:
    session = FakeSession()
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.setenv("SUPABASE_SECRET_KEY", KEY)
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "legacy-environment-key")

    storage = create_storage(
        "supabase",
        tmp_path / "storage",
        supabase_key=LEGACY_JWT,
        session=session,
    )
    storage.save_document(_records()[0])

    headers = session.calls[0]["headers"]
    assert headers["apikey"] == LEGACY_JWT
    assert headers["Authorization"] == f"Bearer {LEGACY_JWT}"


@pytest.mark.parametrize("source", ["explicit", "environment"])
def test_publishable_key_is_rejected_for_backend_storage(
    source: str,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", URL)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    explicit = PUBLISHABLE_KEY if source == "explicit" else None
    if source == "environment":
        monkeypatch.setenv("SUPABASE_SECRET_KEY", PUBLISHABLE_KEY)
    else:
        monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)

    with pytest.raises(StorageConfigurationError) as error:
        create_storage(
            "supabase",
            tmp_path / "storage",
            supabase_key=explicit,
            session=FakeSession(),
        )

    message = str(error.value)
    assert "publishable" in message
    assert PUBLISHABLE_KEY not in message
    assert "Authorization" not in message


@pytest.mark.parametrize("backend", ["supabase", "dual"])
def test_remote_storage_modes_fail_fast_when_configuration_is_missing(
    backend: str,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

    with pytest.raises(StorageConfigurationError) as error:
        create_storage(backend, tmp_path / "storage")

    message = str(error.value)
    assert "SUPABASE_URL" in message
    assert "SUPABASE_SECRET_KEY" in message
    assert "SUPABASE_SERVICE_ROLE_KEY" in message
    assert KEY not in message


def test_dual_write_keeps_all_local_records_after_remote_failure(tmp_path) -> None:
    local = LocalJsonStorage(tmp_path / "storage")
    remote = SupabaseStorage(
        URL,
        KEY,
        session=FakeSession(failure=requests.ConnectionError("offline")),
    )
    storage = DualWriteStorage(local, remote)
    document, chunks, headline, ruleset, retrieval, llm = _records()

    storage.save_document(document)
    storage.save_chunks(chunks)
    storage.save_headline(headline)
    storage.save_ruleset(ruleset)
    storage.save_retrieval_run(retrieval)
    storage.save_llm_run(llm)

    assert storage.remote_failed is True
    assert local.get("documents", document.document_id) is not None
    assert len(local.list_records("chunks")) == 2
    assert local.get("headlines", headline.headline_id) is not None
    assert local.get("rulesets", ruleset.ruleset_id) is not None
    assert local.get("retrieval_runs", retrieval.run_id) is not None
    assert local.get("llm_runs", llm.run_id) is not None
