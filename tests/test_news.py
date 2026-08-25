from __future__ import annotations

import json
from datetime import UTC, date, datetime

from company_lens.news import FinnhubNewsProvider, refresh_headlines


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> list[dict[str, object]]:
        return [{"headline": "Test"}]


class _Session:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> _Response:
        self.calls.append((url, kwargs))
        return _Response()


def test_finnhub_key_is_sent_in_header_not_query() -> None:
    session = _Session()
    provider = FinnhubNewsProvider("secret-value", session=session)  # type: ignore[arg-type]

    provider.company_news("AAPL", date(2026, 8, 22), date(2026, 8, 25))

    url, kwargs = session.calls[0]
    assert url.endswith("/company-news")
    assert kwargs["headers"] == {
        "X-Finnhub-Token": "secret-value",
        "Accept": "application/json",
    }
    assert kwargs["params"] == {
        "symbol": "AAPL",
        "from": "2026-08-22",
        "to": "2026-08-25",
    }
    assert "secret-value" not in url


class _Provider:
    name = "fixture"

    def company_news(self, ticker: str, start: date, end: date) -> list[dict[str, object]]:
        if ticker == "MSFT":
            raise RuntimeError("temporary upstream failure")
        return [
            {
                "category": "company news",
                "datetime": 1787648400,
                "headline": f"{ticker} current company headline",
                "source": "Example Wire",
                "summary": "Source supplied summary.",
                "url": f"https://example.com/{ticker.lower()}",
            }
        ]

    def market_news(self) -> list[dict[str, object]]:
        return [
            {
                "category": "general",
                "datetime": 1787644800,
                "headline": "Current market headline",
                "source": "Market Wire",
                "url": "https://example.com/market",
            }
        ]


def test_refresh_is_bounded_exact_ticker_and_preserves_last_good(tmp_path) -> None:
    universe = tmp_path / "universe.csv"
    universe.write_text("ticker,cik,name\nAAPL,320193,Apple Inc.\nMSFT,789019,Microsoft Corp.\n")
    output = tmp_path / "headlines.json"
    output.write_text(
        json.dumps(
            {
                "headlines": [
                    {
                        "headline": "MSFT last good headline",
                        "publisher": "Cached Wire",
                        "published_at": "2026-08-24T09:00:00+00:00",
                        "fetched_at": "2026-08-24T10:00:00+00:00",
                        "url": "https://example.com/msft-old",
                        "ticker": "MSFT",
                    },
                    {
                        "headline": "Expired headline",
                        "publisher": "Old Wire",
                        "published_at": "2026-07-01T09:00:00+00:00",
                        "url": "https://example.com/expired",
                        "ticker": "AAPL",
                    },
                ]
            }
        )
    )

    result = refresh_headlines(
        provider=_Provider(),
        output_path=output,
        universe_path=universe,
        request_delay=0,
        now=datetime(2026, 8, 25, 12, tzinfo=UTC),
    )

    payload = json.loads(output.read_text())
    rows = payload["headlines"]
    assert result.status == "partial"
    assert result.failed_tickers == ["MSFT"]
    assert result.market_failed is False
    assert payload["scope"].endswith("no article bodies or sentiment")
    assert {row["headline"] for row in rows} == {
        "AAPL current company headline",
        "MSFT last good headline",
        "Current market headline",
    }
    assert next(row for row in rows if row["ticker"] == "AAPL")["ticker"] == "AAPL"
    assert all("sentiment" not in row for row in rows)
    assert all("secret" not in json.dumps(row) for row in rows)
