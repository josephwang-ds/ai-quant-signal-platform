"""Source-linked financial headline refresh with a bounded last-good cache."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import requests

from company_lens.universe import supported_companies

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"


class NewsProvider(Protocol):
    """Small provider boundary; pages never depend on a vendor response shape."""

    def company_news(self, ticker: str, start: date, end: date) -> list[dict[str, Any]]: ...

    def market_news(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class HeadlineRefreshResult:
    status: str
    checked_at: str
    provider: str
    companies_checked: int
    headline_count: int
    failed_tickers: list[str]
    market_failed: bool
    output_path: str


class FinnhubNewsProvider:
    """Fetch Finnhub headline metadata without downloading article bodies."""

    name = "finnhub"

    def __init__(
        self,
        api_key: str,
        *,
        session: requests.Session | None = None,
        base_url: str = FINNHUB_BASE_URL,
        timeout: float = 20.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("FINNHUB_API_KEY is required for live headline refresh")
        self._api_key = api_key.strip()
        self._session = session or requests.Session()
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def company_news(self, ticker: str, start: date, end: date) -> list[dict[str, Any]]:
        return self._get(
            "/company-news",
            {"symbol": ticker, "from": start.isoformat(), "to": end.isoformat()},
        )

    def market_news(self) -> list[dict[str, Any]]:
        return self._get("/news", {"category": "general", "minId": 0})

    def _get(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        response = self._session.get(
            f"{self._base_url}{path}",
            params=params,
            headers={"X-Finnhub-Token": self._api_key, "Accept": "application/json"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("error") or payload.get("Information") or payload.get("Note")
            raise RuntimeError(str(detail or "Finnhub returned an object instead of a news list"))
        if not isinstance(payload, list):
            raise TypeError("Finnhub news response must be a list")
        return [row for row in payload if isinstance(row, dict)]


def refresh_headlines(
    *,
    provider: NewsProvider,
    output_path: str | Path = "data/build/headlines.json",
    universe_path: str | Path = "data/build/universe.csv",
    tickers: list[str] | tuple[str, ...] | None = None,
    lookback_days: int = 3,
    retention_days: int = 14,
    max_per_ticker: int = 5,
    max_market: int = 20,
    request_delay: float = 1.05,
    now: datetime | None = None,
    sleep: Any = time.sleep,
) -> HeadlineRefreshResult:
    """Refresh legal headline metadata and atomically replace the bounded cache."""
    if lookback_days < 1 or retention_days < lookback_days:
        raise ValueError("retention_days must be at least lookback_days, both positive")
    if max_per_ticker < 1 or max_market < 1 or request_delay < 0:
        raise ValueError("headline limits must be positive and request_delay cannot be negative")

    checked = (now or datetime.now(UTC)).astimezone(UTC)
    universe = supported_companies(universe_path)
    known = {company.ticker for company in universe}
    requested = {value.strip().upper() for value in tickers or () if value.strip()}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(f"unknown local ticker(s): {', '.join(unknown)}")
    symbols = sorted(requested or known)
    if not symbols:
        raise ValueError("headline refresh requires a non-empty local company universe")

    path = Path(output_path)
    previous = _read_cached_rows(path)
    fresh: list[dict[str, Any]] = []
    failed: list[str] = []
    start = checked.date() - timedelta(days=lookback_days)
    end = checked.date()

    for index, ticker in enumerate(symbols):
        try:
            rows = provider.company_news(ticker, start, end)
            fresh.extend(
                row
                for payload in rows
                if (row := _normalize_provider_row(payload, checked, ticker=ticker)) is not None
            )
        except Exception:  # noqa: BLE001 - retain last-good rows for one failed ticker
            failed.append(ticker)
        if request_delay and index < len(symbols) - 1:
            sleep(request_delay)

    market_failed = False
    try:
        fresh.extend(
            row
            for payload in provider.market_news()
            if (row := _normalize_provider_row(payload, checked, ticker=None)) is not None
        )
    except Exception:  # noqa: BLE001 - retain last-good market rows
        market_failed = True

    rows = _bounded_merge(
        previous,
        fresh,
        checked=checked,
        retention_days=retention_days,
        max_per_ticker=max_per_ticker,
        max_market=max_market,
    )
    provider_name = str(getattr(provider, "name", provider.__class__.__name__)).casefold()
    status = "partial" if failed or market_failed else "current"
    result = HeadlineRefreshResult(
        status=status,
        checked_at=checked.isoformat(),
        provider=provider_name,
        companies_checked=len(symbols) - len(failed),
        headline_count=len(rows),
        failed_tickers=failed,
        market_failed=market_failed,
        output_path=str(path),
    )
    _atomic_json(
        path,
        {
            "schema_version": 1,
            "scope": "source-linked headline metadata only; no article bodies or sentiment",
            "refresh": asdict(result),
            "headlines": rows,
        },
    )
    return result


def _normalize_provider_row(
    payload: dict[str, Any], fetched_at: datetime, *, ticker: str | None
) -> dict[str, Any] | None:
    headline = str(payload.get("headline") or "").strip()
    publisher = str(payload.get("source") or "").strip()
    url = str(payload.get("url") or "").strip()
    published_at = _published_at(payload.get("datetime"))
    if not headline or not publisher or not published_at or not url.startswith(("http://", "https://")):
        return None
    summary = " ".join(str(payload.get("summary") or "").split())[:800]
    category = str(payload.get("category") or "").strip().casefold()
    row: dict[str, Any] = {
        "headline": headline,
        "publisher": publisher,
        "published_at": published_at,
        "fetched_at": fetched_at.isoformat(),
        "url": url,
    }
    if summary:
        row["summary"] = summary
    if ticker:
        row["ticker"] = ticker
    if category:
        row["topic"] = category
    return row


def _published_at(value: Any) -> str | None:
    try:
        return datetime.fromtimestamp(int(value), tz=UTC).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _read_cached_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("headlines", []) if isinstance(payload, dict) else payload
        return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _bounded_merge(
    previous: list[dict[str, Any]],
    fresh: list[dict[str, Any]],
    *,
    checked: datetime,
    retention_days: int,
    max_per_ticker: int,
    max_market: int,
) -> list[dict[str, Any]]:
    cutoff = checked - timedelta(days=retention_days)
    unique: dict[str, dict[str, Any]] = {}
    for row in [*previous, *fresh]:
        published = _parse_iso(row.get("published_at"))
        url = str(row.get("url") or "").strip()
        headline = str(row.get("headline") or row.get("title") or "").strip()
        if published is None or published < cutoff or not url or not headline:
            continue
        unique[f"{url}\n{headline}"] = row

    ordered = sorted(
        unique.values(),
        key=lambda row: _parse_iso(row.get("published_at")) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    counts: dict[str, int] = {}
    market_count = 0
    kept: list[dict[str, Any]] = []
    for row in ordered:
        ticker = str(row.get("ticker") or "").strip().upper()
        if ticker:
            if counts.get(ticker, 0) >= max_per_ticker:
                continue
            counts[ticker] = counts.get(ticker, 0) + 1
        else:
            if market_count >= max_market:
                continue
            market_count += 1
        kept.append(row)
    return kept


def _parse_iso(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.part")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
