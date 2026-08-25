"""Local-first persistence boundary for retrieval and grounded-LLM provenance."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Protocol

import requests

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
StorageBackend = Literal["local", "supabase", "dual"]
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


class SupabaseStorageError(OSError):
    """Safe remote-storage error that never includes request secrets or bodies."""


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


class SupabaseStorage:
    """Opt-in PostgREST adapter for the reviewed Supabase evidence schema."""

    def __init__(
        self,
        url: str,
        service_role_key: str,
        *,
        session: requests.Session | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not url:
            raise StorageConfigurationError("missing SUPABASE_URL")
        if not service_role_key:
            raise StorageConfigurationError("missing SUPABASE_SERVICE_ROLE_KEY")
        if not url.startswith(("https://", "http://")):
            raise StorageConfigurationError("SUPABASE_URL must use http or https")
        if timeout <= 0:
            raise ValueError("Supabase storage timeout must be positive")
        self.base_url = f"{url.rstrip('/')}/rest/v1"
        self._service_role_key = service_role_key
        self._session = session or requests.Session()
        self.timeout = timeout

    def save_document(self, value: StoredDocument) -> None:
        self._upsert("documents", asdict(value))

    def save_chunks(self, values: Iterable[StoredChunk]) -> None:
        payload = [asdict(value) for value in values]
        if payload:
            self._upsert("chunks", payload)

    def save_headline(self, value: StoredHeadline) -> None:
        self._upsert("headlines", asdict(value))

    def save_ruleset(self, value: StoredRuleset) -> None:
        self._upsert("rulesets", asdict(value))

    def save_retrieval_run(self, value: StoredRetrievalRun) -> None:
        self._upsert("retrieval_runs", asdict(value))

    def save_llm_run(self, value: StoredLlmRun) -> None:
        self._upsert("llm_runs", asdict(value))

    def get(self, collection: Collection, record_id: str) -> dict[str, Any] | None:
        _validate_collection(collection)
        _validate_identifier(record_id)
        primary_key = PRIMARY_KEYS[collection]
        payload = self._request(
            "GET",
            collection,
            params={
                "select": "*",
                primary_key: f"eq.{record_id}",
                "limit": "1",
            },
        )
        records = _record_list(payload)
        return records[0] if records else None

    def list_records(self, collection: Collection) -> list[dict[str, Any]]:
        _validate_collection(collection)
        primary_key = PRIMARY_KEYS[collection]
        payload = self._request(
            "GET",
            collection,
            params={"select": "*", "order": f"{primary_key}.asc"},
        )
        records = _record_list(payload)
        return sorted(records, key=lambda record: str(record.get(primary_key, "")))

    def _upsert(
        self,
        collection: Collection,
        payload: dict[str, Any] | list[dict[str, Any]],
    ) -> None:
        self._request(
            "POST",
            collection,
            params={"on_conflict": PRIMARY_KEYS[collection]},
            payload=_json_value(payload),
            upsert=True,
        )

    def _request(
        self,
        method: str,
        collection: Collection,
        *,
        params: dict[str, str],
        payload: Any = None,
        upsert: bool = False,
    ) -> Any:
        table = TABLES[collection]
        headers = {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
            "Content-Type": "application/json",
        }
        if upsert:
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
        try:
            response = self._session.request(
                method,
                f"{self.base_url}/{table}",
                params=params,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.Timeout:
            raise SupabaseStorageError(
                f"Supabase storage timed out while accessing {table}; retry later"
            ) from None
        except requests.ConnectionError:
            raise SupabaseStorageError(
                f"Supabase storage could not connect while accessing {table}; "
                "verify SUPABASE_URL and network access"
            ) from None
        except requests.RequestException:
            raise SupabaseStorageError(
                f"Supabase storage request failed while accessing {table}"
            ) from None

        if not 200 <= response.status_code < 300:
            if response.status_code in {401, 403}:
                detail = "authentication was rejected; verify backend credentials"
            elif response.status_code >= 500:
                detail = "the remote service failed; retry later"
            else:
                detail = "verify the migration and request configuration"
            raise SupabaseStorageError(
                f"Supabase storage returned HTTP {response.status_code} for {table}; {detail}"
            )
        if upsert or response.status_code == 204:
            return None
        try:
            return response.json()
        except (requests.JSONDecodeError, ValueError):
            raise SupabaseStorageError(
                f"Supabase storage returned invalid JSON for {table}"
            ) from None


class DualWriteStorage:
    """Write locally first, then best-effort remote without transaction claims."""

    def __init__(self, local: EvidenceStorage, remote: EvidenceStorage) -> None:
        self.local = local
        self.remote = remote
        self.remote_failed = False

    def save_document(self, value: StoredDocument) -> None:
        self._write("save_document", value)

    def save_chunks(self, values: Iterable[StoredChunk]) -> None:
        records = tuple(values)
        self.local.save_chunks(records)
        self._write_remote("save_chunks", records)

    def save_headline(self, value: StoredHeadline) -> None:
        self._write("save_headline", value)

    def save_ruleset(self, value: StoredRuleset) -> None:
        self._write("save_ruleset", value)

    def save_retrieval_run(self, value: StoredRetrievalRun) -> None:
        self._write("save_retrieval_run", value)

    def save_llm_run(self, value: StoredLlmRun) -> None:
        self._write("save_llm_run", value)

    def get(self, collection: Collection, record_id: str) -> dict[str, Any] | None:
        return self.local.get(collection, record_id)

    def list_records(self, collection: Collection) -> list[dict[str, Any]]:
        return self.local.list_records(collection)

    def _write(self, method: str, value: Any) -> None:
        getattr(self.local, method)(value)
        self._write_remote(method, value)

    def _write_remote(self, method: str, value: Any) -> None:
        if self.remote_failed:
            return
        try:
            getattr(self.remote, method)(value)
        except (OSError, TypeError, ValueError):
            self.remote_failed = True


def create_storage(
    backend: StorageBackend = "local",
    storage_dir: str | Path = "data/build/company_lens_storage",
    supabase_url: str | None = None,
    supabase_key: str | None = None,
    *,
    session: requests.Session | None = None,
    timeout: float = 10.0,
) -> EvidenceStorage:
    """Create a backend without consulting Supabase configuration for local mode."""
    if backend == "local":
        return LocalJsonStorage(storage_dir)
    if backend not in {"supabase", "dual"}:
        raise StorageConfigurationError(f"unsupported storage backend: {backend}")

    url = supabase_url or os.environ.get("SUPABASE_URL")
    key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", url),
            ("SUPABASE_SERVICE_ROLE_KEY", key),
        )
        if not value
    ]
    if missing:
        names = ", ".join(missing)
        raise StorageConfigurationError(f"missing required storage configuration: {names}")
    remote = SupabaseStorage(
        url,
        key,
        session=session,
        timeout=timeout,
    )
    if backend == "supabase":
        return remote
    return DualWriteStorage(LocalJsonStorage(storage_dir), remote)


def storage_write_status(storage: EvidenceStorage) -> str:
    """Return the bounded persistence status used in public provenance."""
    if isinstance(storage, DualWriteStorage) and storage.remote_failed:
        return "degraded"
    return "stored"


def _record_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or any(not isinstance(record, dict) for record in payload):
        raise SupabaseStorageError("Supabase storage returned an unexpected response shape")
    return [dict(record) for record in payload]


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
