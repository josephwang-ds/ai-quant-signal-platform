from __future__ import annotations

import json
import math
from datetime import UTC, datetime

import pandas as pd
import pytest

from company_lens.contracts import FilingReaction
from company_lens.filings.intelligence import build_filing_briefs, build_filing_timeline
from company_lens.llm import deterministic_explanation
from company_lens.llm.headlines import import_headline_index
from company_lens.performance import historical_picture
from company_lens.profiles import company_profile
from company_lens.snapshots import build_snapshot
from company_lens.snapshots.builder import (
    DEFAULT_PERIODS,
    _downsample_growth,
    _headline_context,
)
from company_lens.universe import UnsupportedCompanyError, resolve_supported_company


def _prices() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=6)
    return pd.DataFrame(
        [
            {"ticker": ticker, "date": date.date(), "close": close}
            for ticker, closes in {
                "ABC": [100, 110, 99, 120, 108, 130],
                "SPY": [100, 102, 101, 104, 105, 108],
            }.items()
            for date, close in zip(dates, closes, strict=True)
        ]
    )


def test_historical_picture_uses_same_period_and_growth_base() -> None:
    metrics, growth = historical_picture(_prices(), "abc", years=5)

    assert growth[0]["asset_value"] == 10_000
    assert growth[-1]["asset_value"] == 13_000
    assert metrics["asset"]["total_return"] == pytest.approx(0.30)
    assert metrics["benchmark"]["total_return"] == pytest.approx(0.08)
    assert metrics["relative_total_return"] == pytest.approx(0.22)
    assert metrics["asset"]["max_drawdown"] == pytest.approx(-0.10)
    assert metrics["observations"] == 6
    assert math.isfinite(metrics["beta"])


def test_historical_picture_rejects_missing_benchmark() -> None:
    with pytest.raises(ValueError, match="SPY"):
        historical_picture(_prices().query("ticker == 'ABC'"), "ABC")


def test_filing_brief_has_causal_novelty_and_cited_numbers() -> None:
    events = pd.DataFrame(
        [
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000001",
                "primary_document": "first.htm",
                "form": "8-K",
                "items": "2.02,9.01",
                "acceptance_time": pd.Timestamp("2024-01-02 17:00", tz="America/New_York"),
                "text": "Item 2.02 Results of Operations. Revenue was $100 million.",
            },
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000002",
                "primary_document": "second.htm",
                "form": "8-K",
                "items": "2.02,9.01",
                "acceptance_time": pd.Timestamp("2024-04-02 17:00", tz="America/New_York"),
                "text": "Item 2.02 Results of Operations. Revenue was $120 million.",
            },
        ]
    )

    newest, oldest = build_filing_briefs(events, "abc", limit=2)

    assert newest.novelty is not None
    assert oldest.novelty is None
    assert newest.items[0] == {"code": "2.02", "label": "Results of operations (earnings)"}
    assert newest.passages[0].anchor.startswith(newest.accession)
    assert any(number["value"] == "$120 million" for number in newest.key_numbers)
    money = next(entity for entity in newest.entities if entity.text == "$120 million")
    assert money.kind == "money"
    assert money.normalized_value == "1.2e+08"
    assert money.unit == "USD"
    passage = next(value for value in newest.passages if value.anchor == money.citation)
    assert passage.text[money.source_start:money.source_end] == money.text
    assert newest.source_url.endswith("/second.htm")


def test_filing_timeline_is_chronological_and_source_linked() -> None:
    events = pd.DataFrame(
        [
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": f"0000123-24-00000{index}",
                "primary_document": f"filing-{index}.htm",
                "items": "2.02,9.01" if index % 2 else "5.02",
                "acceptance_time": pd.Timestamp(
                    f"2024-0{index}-02 17:00", tz="America/New_York"
                ),
            }
            for index in range(1, 4)
        ]
    )
    reactions = {
        "0000123-24-000003": FilingReaction(
            session="2024-03-04",
            asset_open_to_close=0.02,
            benchmark_open_to_close=0.005,
            benchmark_adjusted_move=0.015,
            magnitude_percentile=0.75,
            prior_sample_size=8,
        )
    }

    timeline = build_filing_timeline(events, "abc", reactions=reactions, limit=2)

    assert [point.accession for point in timeline] == [
        "0000123-24-000002",
        "0000123-24-000003",
    ]
    assert timeline[0].item_label == "Director or principal officer change"
    assert timeline[1].item_label == "Results of operations (earnings)"
    assert timeline[1].source_url.endswith("/filing-3.htm")
    assert timeline[1].reaction == reactions["0000123-24-000003"]


def test_filing_entities_type_percentages_and_dates_with_source_spans() -> None:
    events = pd.DataFrame(
        [
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000003",
                "primary_document": "third.htm",
                "form": "8-K",
                "items": "2.02,9.01",
                "acceptance_time": pd.Timestamp(
                    "2024-07-02 17:00", tz="America/New_York"
                ),
                "text": (
                    "Item 2.02 Results of Operations. On July 2, 2024, revenue grew "
                    "12.5 percent to $1.2 billion."
                ),
            }
        ]
    )

    brief = build_filing_briefs(events, "ABC")[0]
    by_kind = {entity.kind: entity for entity in brief.entities}

    assert by_kind["percentage"].normalized_value == "0.125"
    assert by_kind["date"].normalized_value == "2024-07-02"
    assert by_kind["money"].normalized_value == "1.2e+09"
    for entity in brief.entities:
        passage = next(value for value in brief.passages if value.anchor == entity.citation)
        assert passage.text[entity.source_start:entity.source_end] == entity.text


def test_fallback_separates_observation_from_forecast() -> None:
    metrics, _ = historical_picture(_prices(), "ABC", years=5)
    response = deterministic_explanation("ABC", metrics, [])

    assert response["mode"] == "deterministic_fallback"
    assert "not a forecast" in response["why_it_matters"][0]["text"]
    assert response["why_it_matters"][0]["citations"] == [
        "metric:asset.total_return",
        "metric:asset.max_drawdown",
    ]


def test_default_page_periods_are_declared_and_ordered() -> None:
    assert DEFAULT_PERIODS == (1, 3, 5, 10)


def test_chart_sampling_preserves_endpoints_and_metric_grain() -> None:
    growth = [{"date": str(index), "asset_value": index} for index in range(2_000)]

    sampled = _downsample_growth(growth, max_points=520)

    assert len(sampled) <= 520
    assert sampled[0] == growth[0]
    assert sampled[-1] == growth[-1]


def test_headline_context_caps_rows_and_never_leaks_company_tickers(tmp_path) -> None:
    path = tmp_path / "headlines.json"
    path.write_text(
        json.dumps(
            [
                {
                    "headline": "Apple filing context",
                    "publisher": "Company Wire",
                    "published_at": "2026-08-25T09:00:00+00:00",
                    "fetched_at": "2026-08-25T09:05:00+00:00",
                    "url": "https://example.com/apple",
                    "ticker": "AAPL",
                    "topic": "earnings",
                },
                {
                    "headline": "Apple product context",
                    "publisher": "Company Wire",
                    "published_at": "2026-08-24T09:00:00+00:00",
                    "url": "https://example.com/apple-product",
                    "tickers": ["AAPL", "MSFT"],
                    "topic": "product",
                },
                {
                    "headline": "Rates remain unchanged",
                    "publisher": "Market Desk",
                    "published_at": "2026-08-23T09:00:00+00:00",
                    "fetched_at": "2026-08-23T09:05:00+00:00",
                    "url": "https://example.com/rates",
                    "topic": "macro",
                },
                {
                    "headline": "Broad market volatility",
                    "publisher": "Market Desk",
                    "published_at": "2026-08-22T09:00:00+00:00",
                    "url": "https://example.com/volatility",
                },
                {
                    "headline": "Microsoft company context",
                    "publisher": "Company Wire",
                    "published_at": "2026-08-25T10:00:00+00:00",
                    "url": "https://example.com/microsoft",
                    "ticker": "MSFT",
                },
                {
                    "headline": "Nvidia company context",
                    "publisher": "Company Wire",
                    "published_at": "2026-08-25T11:00:00+00:00",
                    "url": "https://example.com/nvidia",
                    "ticker": "NVDA",
                },
            ]
        ),
        encoding="utf-8",
    )

    scope, headlines = _headline_context(
        import_headline_index(path),
        "AAPL",
        now=datetime(2026, 8, 25, 12, tzinfo=UTC),
    )

    assert scope is not None
    assert scope.status == "available"
    assert scope.source_types == ["company_news", "market_news"]
    assert len(headlines) == 3
    assert {headline.headline for headline in headlines} == {
        "Apple filing context",
        "Apple product context",
        "Rates remain unchanged",
    }
    assert all("Microsoft" not in headline.headline for headline in headlines)
    assert all("Nvidia" not in headline.headline for headline in headlines)
    assert headlines[0].publisher == "Company Wire"
    assert headlines[0].published_at == "2026-08-25T09:00:00+00:00"
    assert headlines[0].fetched_at == "2026-08-25T09:05:00+00:00"
    assert headlines[0].url == "https://example.com/apple"
    assert headlines[0].topic == "earnings"
    assert headlines[0].citation.startswith("news:headline-")


def test_company_profile_separates_curated_summary_from_observed_coverage() -> None:
    profile = company_profile(
        "MSFT",
        "MICROSOFT CORP",
        789019,
        price_start="2020-01-02",
        price_end="2025-12-31",
        filing_count=5,
    )

    assert profile["display_name"] == "Microsoft Corporation"
    assert profile["cik"] == "0000789019"
    assert profile["method"].startswith("curated category")
    assert profile["coverage"]["filings_in_snapshot"] == 5
    assert profile["source_url"].startswith("https://www.sec.gov/")
    generic = company_profile(
        "ABBV",
        "ABBVIE INC.",
        1551152,
        price_start="2020-01-02",
        price_end="2025-12-31",
        filing_count=5,
    )
    assert generic["category"] == "Company evidence profile"
    assert "Historical market context and recent SEC disclosures" in generic["summary"]


def test_filing_comparison_uses_only_prior_same_event_type() -> None:
    events = pd.DataFrame(
        [
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000001",
                "primary_document": "first.htm",
                "form": "8-K",
                "items": "2.02,9.01",
                "acceptance_time": pd.Timestamp("2024-01-02 17:00", tz="America/New_York"),
                "text": (
                    "Item 2.02 Results of Operations. Revenue was $100 million. "
                    "The company recorded an impairment charge."
                ),
            },
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000002",
                "primary_document": "director.htm",
                "form": "8-K",
                "items": "5.02",
                "acceptance_time": pd.Timestamp("2024-02-02 17:00", tz="America/New_York"),
                "text": "Item 5.02. The board appointed a new director.",
            },
            {
                "ticker": "ABC",
                "cik": 123,
                "accession": "0000123-24-000003",
                "primary_document": "latest.htm",
                "form": "8-K",
                "items": "2.02,9.01",
                "acceptance_time": pd.Timestamp("2024-04-02 17:00", tz="America/New_York"),
                "text": (
                    "Item 2.02 Results of Operations. Revenue was $120 million. "
                    "The board declared a quarterly dividend."
                ),
            },
        ]
    )

    latest = build_filing_briefs(events, "ABC", limit=3)[0]

    assert latest.comparison is not None
    assert latest.comparison.comparable_key == "8-K:2.02"
    assert latest.comparison.prior_accession == "0000123-24-000001"
    assert latest.comparison.prior_accepted_at < latest.accepted_at
    assert latest.comparison.counts == {"changed": 1, "added": 1, "removed": 1}
    assert {change.kind for change in latest.comparison.changes} == {
        "changed",
        "added",
        "removed",
    }


def test_supported_company_resolver_has_one_stable_scope_error(tmp_path) -> None:
    universe = tmp_path / "universe.csv"
    pd.DataFrame(
        [
            {"ticker": "AAPL", "cik": 320193, "name": "Apple Inc."},
            {"ticker": "ABBV", "cik": 1551152, "name": "ABBVIE INC."},
        ]
    ).to_csv(universe, index=False)

    assert resolve_supported_company("Apple Inc.", universe).ticker == "AAPL"
    assert resolve_supported_company("ABBV", universe).display_name == "Abbvie Inc."
    with pytest.raises(UnsupportedCompanyError, match=r"2 companies.*AAPL, MSFT, NVDA"):
        resolve_supported_company("TSLA", universe)
    with pytest.raises(UnsupportedCompanyError, match=r"TSLA.*not in the current"):
        build_snapshot("TSLA", data_dir=tmp_path)
