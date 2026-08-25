"""Import a small, source-linked financial headline index for bounded retrieval."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

from company_lens.llm.retrieval import ImportedDocument

HEADLINE_FIELDS = frozenset(
    {
        "headline",
        "title",
        "summary",
        "snippet",
        "publisher",
        "source",
        "published_at",
        "fetched_at",
        "url",
        "ticker",
        "tickers",
        "topic",
        "category",
    }
)
MAX_HEADLINES_PER_IMPORT = 5_000


def import_headline_index(path: str | Path) -> list[ImportedDocument]:
    """Read JSON/CSV headline metadata without fetching or copying article bodies."""
    source = Path(path)
    raw = source.read_text(encoding="utf-8")
    if source.suffix.casefold() == ".json":
        payload = json.loads(raw)
        rows = payload.get("headlines", []) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise TypeError("headline JSON must be a list or contain a headlines list")
    elif source.suffix.casefold() == ".csv":
        rows = list(csv.DictReader(StringIO(raw)))
    else:
        raise ValueError("headline index must be .json or .csv")
    if len(rows) > MAX_HEADLINES_PER_IMPORT:
        raise ValueError("headline index exceeds the 5000-row import limit")
    return [_headline_document(row, index) for index, row in enumerate(rows)]


def _headline_document(row: object, index: int) -> ImportedDocument:
    if not isinstance(row, dict):
        raise TypeError(f"headline row {index} must be an object")
    unknown = set(row) - HEADLINE_FIELDS
    if unknown:
        raise ValueError(f"headline row {index} has unsupported fields: {sorted(unknown)}")
    headline = str(row.get("headline") or row.get("title") or "").strip()
    publisher = str(row.get("publisher") or row.get("source") or "").strip()
    published_at = str(row.get("published_at") or "").strip()
    fetched_at = str(row.get("fetched_at") or "").strip() or None
    url = str(row.get("url") or "").strip()
    if not headline or not publisher or not published_at or not _valid_http_url(url):
        raise ValueError(
            f"headline row {index} requires headline, publisher, ISO published_at, and URL"
        )
    _validate_timestamp(published_at, index, "published_at")
    if fetched_at:
        _validate_timestamp(fetched_at, index, "fetched_at")
    summary = str(row.get("summary") or row.get("snippet") or "").strip()
    tickers = _tickers(row.get("tickers") or row.get("ticker"))
    topic = str(row.get("topic") or row.get("category") or "").strip().casefold()
    identity = json.dumps(
        {"headline": headline, "published_at": published_at, "url": url},
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    body = f"Headline: {headline}"
    if summary:
        body += f"\nPublisher summary: {summary}"
    return ImportedDocument(
        document_id=f"headline-{digest}",
        title=headline,
        text=body,
        source_type="company_news" if tickers else "market_news",
        ticker=tickers[0] if len(tickers) == 1 else None,
        tags=tuple(filter(None, (topic, *tickers))),
        source_name=publisher,
        source_url=url,
        published_at=published_at,
        fetched_at=fetched_at,
        tickers=tickers,
        topic=topic or None,
    )


def _tickers(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        values = value.replace(",", " ").split()
    elif isinstance(value, list):
        values = [str(item) for item in value]
    else:
        values = []
    return tuple(sorted({item.strip().upper() for item in values if item.strip()}))


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_timestamp(value: str, index: int, field: str) -> None:
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"headline row {index} has invalid ISO {field}: {value}") from error
