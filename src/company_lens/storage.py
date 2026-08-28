"""Local-first persistence boundary for retrieval and grounded-LLM provenance."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

Collection = Literal[
    "documents",
    "chunks",
    "headlines",
    "rulesets",
    "retrieval_runs",
    "llm_runs",
]
COLLECTIONS: tuple[Collection, ...] = (
    "documents",
    "chunks",
    "headlines",
    "rulesets",
    "retrieval_runs",
    "llm_runs",
)
IDENTIFIER = re.compile(r"^[^\x00-\x1f\x7f]{1,240}$")
StorageBackend = Literal["local"]
TABLES: dict[Collection, str] = {
    "documents": "documents",
    "chunks": "document_chunks",
    "headlines": "headlines",
    "rulesets": "rulesets",
    "retrieval_runs": "retrieval_runs",
    "llm_runs": "llm_runs",
}
PRIMARY_KEYS: dict[Collection, str] = {
    "documents": "document_id",
    "chunks": "citation",
    "headlines": "headline_id",
    "rulesets": "ruleset_id",
    "retrieval_runs": "run_id",
    "llm_runs": "run_id",
}


@dataclass(frozen=True)
class StoredDocument:
    document_id: str
    source_type: str
    title: str
    content_hash: str
    ticker: str | None = None
    source_url: str | None = None
    storage_key: str | None = None
    published_at: str | None = None
    fetched_at: str | None = None
    owner_id: str | None = None


@dataclass(frozen=True)
class StoredChunk:
    citation: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class StoredHeadline:
    headline_id: str
    headline: str
    publisher: str
    published_at: str
    url: str
    source_type: str
    tickers: tuple[str, ...] = ()
    fetched_at: str | None = None
    topic: str | None = None
    owner_id: str | None = None


@dataclass(frozen=True)
class StoredRuleset:
    ruleset_id: str
    name: str
    rules: tuple[str, ...]
    trust_policy_version: str
    created_at: str
    owner_id: str | None = None


@dataclass(frozen=True)
class StoredRetrievalRun:
    run_id: str
    query: str
    scope: dict[str, Any]
    selected_citations: tuple[str, ...]
    index_version: str
    latency_ms: int
    created_at: str
    owner_id: str | None = None


@dataclass(frozen=True)
class StoredLlmRun:
    run_id: str
    provider: str
    model: str
    prompt_version: str
    evidence_hash: str
    validator_status: str
    usage: dict[str, Any]
    cost: dict[str, Any]
    created_at: str
    owner_id: str | None = None


class EvidenceStorage(Protocol):
    """Backend-neutral writes plus small read methods used by local tooling."""

    def save_document(self, value: StoredDocument) -> None: ...

    def save_chunks(self, values: Iterable[StoredChunk]) -> None: ...

    def save_headline(self, value: StoredHeadline) -> None: ...

    def save_ruleset(self, value: StoredRuleset) -> None: ...

    def save_retrieval_run(self, value: StoredRetrievalRun) -> None: ...

    def save_llm_run(self, value: StoredLlmRun) -> None: ...

    def get(self, collection: Collection, record_id: str) -> dict[str, Any] | None: ...

    def list_records(self, collection: Collection) -> list[dict[str, Any]]: ...


class StorageConfigurationError(ValueError):
    """Safe, actionable storage configuration error."""


class LocalJsonStorage:
    """Atomic JSON persistence used when no database is configured."""

    schema_version = 1

    def __init__(self, root: str | Path = "data/build/company_lens_storage") -> None:
        self.root = Path(root)

    def save_document(self, value: StoredDocument) -> None:
        self._upsert("documents", value.document_id, asdict(value))

    def save_chunks(self, values: Iterable[StoredChunk]) -> None:
        records = [(value.citation, asdict(value)) for value in values]
        self._upsert_many("chunks", records)

    def save_headline(self, value: StoredHeadline) -> None:
        self._upsert("headlines", value.headline_id, asdict(value))

    def save_ruleset(self, value: StoredRuleset) -> None:
        self._upsert("rulesets", value.ruleset_id, asdict(value))

    def save_retrieval_run(self, value: StoredRetrievalRun) -> None:
        self._upsert("retrieval_runs", value.run_id, asdict(value))

    def save_llm_run(self, value: StoredLlmRun) -> None:
        self._upsert("llm_runs", value.run_id, asdict(value))

    def get(self, collection: Collection, record_id: str) -> dict[str, Any] | None:
        _validate_collection(collection)
        _validate_identifier(record_id)
        value = self._read(collection)["records"].get(record_id)
        return dict(value) if value is not None else None

    def list_records(self, collection: Collection) -> list[dict[str, Any]]:
        _validate_collection(collection)
        records = self._read(collection)["records"]
        return [dict(records[key]) for key in sorted(records)]

    def _upsert(
        self,
        collection: Collection,
        record_id: str,
        value: dict[str, Any],
    ) -> None:
        self._upsert_many(collection, [(record_id, value)])

    def _upsert_many(
        self,
        collection: Collection,
        values: Iterable[tuple[str, dict[str, Any]]],
    ) -> None:
        payload = self._read(collection)
        for record_id, value in values:
            _validate_identifier(record_id)
            payload["records"][record_id] = value
        self._write(collection, payload)

    def _read(self, collection: Collection) -> dict[str, Any]:
        path = self.root / f"{collection}.json"
        if not path.exists():
            return {"schema_version": self.schema_version, "records": {}}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != self.schema_version
            or not isinstance(payload.get("records"), dict)
        ):
            raise ValueError(f"unsupported or malformed local storage file: {path.name}")
        return payload

    def _write(self, collection: Collection, payload: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{collection}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)


def create_storage(
    backend: StorageBackend = "local",
    storage_dir: str | Path = "data/build/company_lens_storage",
) -> EvidenceStorage:
    """Create the evidence backend.

    Local JSON is the only one. A PostgREST adapter lived here until
    2026-08-28, alongside a dual-write mode that paired the two; both were
    removed because nothing selected them. They cost four environment
    variables, a SQL migration, a page of operating documentation and a
    credential class that must never reach a browser -- carried, in the end, for
    a code path no run took. The `backend` argument stays so callers and their
    provenance records keep their shape, and it now accepts one value.
    """
    if backend != "local":
        raise StorageConfigurationError(
            f"unsupported storage backend: {backend!r}; only 'local' remains"
        )
    return LocalJsonStorage(storage_dir)


def storage_write_status(storage: EvidenceStorage) -> str:
    """Return the bounded persistence status used in public provenance.

    Always "stored" now: "degraded" existed for the dual-write backend, where a
    local write could succeed while the remote one failed. With one backend a
    write either happens or raises, and there is no partial state to report.
    The function stays because the provenance schema does.
    """
    del storage
    return "stored"


def _json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _validate_collection(collection: str) -> None:
    if collection not in COLLECTIONS:
        raise ValueError(f"unsupported storage collection: {collection}")


def _validate_identifier(value: str) -> None:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError("storage identifiers must be 1-240 printable characters")
