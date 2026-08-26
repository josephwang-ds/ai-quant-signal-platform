from __future__ import annotations

from dataclasses import replace

from company_lens.contracts import (
    Citation,
    CompanySnapshot,
    EvidenceScopeSummary,
    FilingBrief,
    FilingChange,
    FilingComparison,
    FilingEntity,
    FilingReaction,
    FilingTimelinePoint,
    HeadlineBrief,
)
from company_lens.web import render_company_page, render_index, render_unsupported


def _period(total_return: float) -> dict:
    performance = {
        "initial_investment": 10_000.0,
        "ending_value": 10_000 * (1 + total_return),
        "asset": {
            "total_return": total_return,
            "cagr": total_return,
            "annualized_volatility": 0.2,
            "max_drawdown": -0.15,
            "current_drawdown": -0.02,
            "max_drawdown_date": "2024-02-01",
            "recovery_sessions": 30,
            "worst_day": -0.05,
        },
        "benchmark": {
            "total_return": 0.1,
            "cagr": 0.1,
            "annualized_volatility": 0.12,
            "max_drawdown": -0.1,
            "current_drawdown": -0.01,
            "max_drawdown_date": "2024-02-01",
            "recovery_sessions": 20,
            "worst_day": -0.03,
        },
        "relative_total_return": total_return - 0.1,
        "beta": 1.1,
        "correlation": 0.7,
        "observations": 2,
        "dividends": "included when supplied by the adjusted-price vendor",
    }
    return {
        "period": {"start": "2024-01-02", "end": "2024-12-31"},
        "performance": performance,
        "growth": [
            {"date": "2024-01-02", "asset_value": 10_000, "benchmark_value": 10_000},
            {
                "date": "2024-12-31",
                "asset_value": performance["ending_value"],
                "benchmark_value": 11_000,
            },
        ],
    }


def _snapshot() -> CompanySnapshot:
    period_options = {label: _period(value) for label, value in {
        "1Y": 0.2, "3Y": 0.4, "5Y": 0.6, "10Y": 1.0,
    }.items()}
    filing = FilingBrief(
        accession="0000123-24-000001",
        form="8-K",
        accepted_at="2024-12-20T17:00:00-05:00",
        items=[{"code": "2.02", "label": "Results of operations (earnings)"}],
        source_url="https://www.sec.gov/example",
        novelty=0.25,
        key_numbers=[{"value": "$120 million", "citation": "filing#sentence-1"}],
        entities=[
            FilingEntity(
                text="$120 million",
                kind="money",
                normalized_value="1.2e+08",
                unit="USD",
                citation="filing#sentence-1",
                source_start=12,
                source_end=24,
            )
        ],
        passages=[Citation(
            anchor="filing#sentence-1",
            accession="0000123-24-000001",
            source_url="https://www.sec.gov/example",
            text="Revenue was $120 million.",
        )],
        reaction=FilingReaction(
            session="2024-12-23",
            asset_open_to_close=0.032,
            benchmark_open_to_close=0.008,
            benchmark_adjusted_move=0.024,
            magnitude_percentile=0.8,
            prior_sample_size=10,
        ),
    )
    selected = period_options["5Y"]
    return CompanySnapshot(
        schema_version="1.6",
        ticker="ABC",
        company_name="ABC & Partners",
        as_of="2024-12-31",
        benchmark="SPY",
        period=selected["period"],
        profile={
            "display_name": "ABC & Partners",
            "official_name": "ABC & Partners",
            "category": "Test category",
            "summary": "A source-backed test company profile.",
            "cik": "0000000123",
            "source_label": "SEC EDGAR company record",
            "source_url": "https://www.sec.gov/edgar/browse/?CIK=123",
            "method": "test fixture",
            "coverage": {
                "price_start": "2024-01-02",
                "price_end": "2024-12-31",
                "filings_in_snapshot": 1,
            },
        },
        market={
            "latest_adjusted_close": 120.0,
            "price_date": "2024-12-31",
            "price_field": "vendor-adjusted close",
        },
        performance=selected["performance"],
        growth=selected["growth"],
        period_options=period_options,
        latest_filings=[filing],
        explanation={
            "mode": "deterministic_fallback",
            "what_changed": [
                {"text": "Revenue changed.", "citations": [filing.passages[0].anchor]}
            ],
            "why_it_matters": [
                {
                    "text": "Historical context only.",
                    "citations": ["metric:asset.total_return"],
                }
            ],
            "uncertainties": [{"text": "Future return is unknown.", "citations": []}],
        },
        provenance={"source": "edgar", "written_at": "2024-12-21T02:00:00+00:00"},
        filing_timeline=[
            FilingTimelinePoint(
                accession=filing.accession,
                accepted_at=filing.accepted_at,
                item_code="2.02",
                item_label="Results of operations (earnings)",
                source_url=filing.source_url,
                reaction=filing.reaction,
            )
        ],
    )


def test_company_page_is_self_contained_and_source_linked(tmp_path) -> None:
    output = render_company_page(_snapshot(), tmp_path / "abc.html", tickers=("ABC",))
    page = output.read_text()

    assert "ABC &amp; Partners" in page
    assert page.count('class="period-button"') == 4
    assert 'id="period-data"' in page
    assert 'id="citation-filing-sentence-1"' in page
    assert "https://www.sec.gov/example" in page
    assert "Revenue was " in page
    assert "$120 million" in page
    assert "Extracted facts" in page
    assert 'class="entity-mark money"' in page
    assert "normalized 1.2e+08 USD" in page
    assert "SEC cache collected 2024-12-21" in page
    assert "https://cdn" not in page
    assert 'aria-current="page"' in page
    assert "A source-backed test company profile." in page
    assert "CIK 0000000123" in page
    assert "Prices 2024-01-02—2024-12-31" in page
    assert "Find a company" in page
    assert '<span class="current-symbol" aria-current="page">ABC</span>' in page
    assert 'id="correlation"' in page
    assert 'id="worst-day"' in page
    assert "Prior comparison unavailable" in page
    assert "What happened next" in page
    assert "+2.4% vs SPY" in page
    assert "More extreme than 80%" in page
    assert "of 10 earlier measurable filings" in page
    assert "does not claim the filing caused the move" in page
    assert "Recent filing timeline" not in page
    assert "What matters on this page" in page
    assert "Source-backed summary" in page
    assert "Latest SEC disclosure" in page
    assert "Selected historical period" in page
    assert "Ask the evidence" in page
    assert "Every answer is validated" in page
    assert 'id="ask-model"' in page
    assert 'id="ask-question"' in page
    assert "API keys remain server-side" in page
    assert "grounding_validation_failed" not in page
    assert "More risk metrics" in page
    assert page.count('class="metric-card"') == 6
    assert 'href="#brief" data-i18n="nav.overview">Overview</a>' in page
    assert 'href="#ask" data-i18n="nav.ask">Ask AI</a>' in page
    assert 'id="workspace"' in page
    assert page.count('data-workspace-view="') == 4
    assert 'data-view-target="performance"' in page
    assert "activateWorkspace" in page
    assert "workspace-enhanced" in page
    assert 'id="language-toggle"' in page
    assert 'data-i18n="ask.title"' in page
    assert 'data-i18n-placeholder="ask.placeholder"' in page
    assert "company-lens-language" in page
    assert "document.documentElement.lang" in page
    assert '"zh": {' in page
    assert '"ask.title": "向证据提问"' in page
    assert "getElementById('ask-language').value" in page
    assert 'data-status-key="ask.checking_models"' in page
    assert 'data-i18n="ask.checking_models"' not in page
    assert "refreshAskStatus" in page
    assert 'data-freshness-key="filings.sec_collected"' in page
    assert "SEC excerpts remain in the filed language" in page
    assert "The architecture is the trust story" not in page
    assert "How to read this lens" in page
    assert "No cached headline index is configured for this build." not in page
    assert '<div class="scope-meta">' not in page
    assert "retrieval_headlines" not in page
    assert "evidence_scope" not in _snapshot().to_dict()


def test_company_page_renders_at_most_three_safe_source_linked_headlines(tmp_path) -> None:
    scope = EvidenceScopeSummary(
        status="available",
        source_types=["company_news", "market_news"],
        query="earnings & rates",
        max_chunks=6,
        selected_chunks=2,
        published_after="2026-08-01",
        generated_at="2026-08-25T06:00:00+00:00",
    )
    headlines = [
        HeadlineBrief(
            headline="<script>alert('headline')</script>",
            publisher="Publisher <img src=x onerror=alert(1)>",
            published_at="2026-08-25T09:00:00+00:00",
            fetched_at="2026-08-25T09:05:00+00:00",
            url="https://example.com/company?a=1&b=2",
            source_type="company_news",
            ticker="ABC",
            topic="<b>earnings</b>",
            citation="news:headline-one#headline",
        ),
        HeadlineBrief(
            headline="Rates remain unchanged",
            publisher="Market Desk",
            published_at="2026-08-24T09:00:00+00:00",
            fetched_at=None,
            url="https://example.com/market",
            source_type="market_news",
            ticker=None,
            topic="macro",
            citation="news:headline-two#headline",
        ),
        HeadlineBrief(
            headline="Company opens a new facility",
            publisher="Local Wire",
            published_at="2026-08-23T09:00:00+00:00",
            fetched_at="2026-08-23T10:00:00+00:00",
            url="https://example.com/facility",
            source_type="company_news",
            ticker="ABC",
            topic=None,
            citation="news:headline-three#headline",
        ),
        HeadlineBrief(
            headline="Third company headline",
            publisher="Overflow Wire",
            published_at="2026-08-22T09:00:00+00:00",
            fetched_at=None,
            url="https://example.com/fourth",
            source_type="company_news",
            ticker="ABC",
            topic=None,
            citation="news:headline-four#headline",
        ),
        HeadlineBrief(
            headline="This fourth company row must not render",
            publisher="Overflow Wire",
            published_at="2026-08-21T09:00:00+00:00",
            fetched_at=None,
            url="https://example.com/fifth",
            source_type="company_news",
            ticker="ABC",
            topic=None,
            citation="news:headline-five#headline",
        ),
    ]
    snapshot = replace(
        _snapshot(),
        evidence_scope=scope,
        headlines=headlines,
        provenance={
            "api_key": "must-not-render",
            "path": "/Users/example/private/headlines.json",
        },
    )

    page = render_company_page(snapshot, tmp_path / "abc.html").read_text()
    payload = snapshot.to_dict()

    assert page.count('class="headline-card"') == 3
    assert "This fourth company row must not render" not in page
    assert "Rates remain unchanged" not in page
    assert "&lt;script&gt;alert(&#x27;headline&#x27;)&lt;/script&gt;" in page
    assert "Publisher &lt;img src=x onerror=alert(1)&gt;" in page
    assert "&lt;b&gt;earnings&lt;/b&gt;" not in page
    assert "<script>alert('headline')</script>" not in page
    assert "https://example.com/company?a=1&amp;b=2" in page
    assert "Company</span>" not in page
    assert "Market</span>" not in page
    assert "Fetch time unavailable" not in page
    assert "2 of 6 chunks selected" not in page
    assert payload["headlines"][0]["citation"] == "news:headline-one#headline"
    assert payload["headlines"][0]["fetched_at"] == "2026-08-25T09:05:00+00:00"
    assert payload["headlines"][0]["publisher"].startswith("Publisher")
    assert "must-not-render" not in page
    assert "/Users/example/private" not in page


def test_company_page_uses_readable_demo_display_name(tmp_path) -> None:
    snapshot = _snapshot()
    profile = {**snapshot.profile, "display_name": "Microsoft Corporation"}
    snapshot = replace(
        snapshot,
        ticker="MSFT",
        company_name="MICROSOFT CORP",
        profile=profile,
    )

    output = render_company_page(snapshot, tmp_path / "msft.html", tickers=("MSFT",))
    page = output.read_text()

    assert "Microsoft Corporation" in page
    assert "MICROSOFT CORP" not in page


def test_company_page_does_not_repeat_featured_tickers_in_navigation(tmp_path) -> None:
    snapshot = replace(_snapshot(), ticker="AAPL")

    page = render_company_page(
        snapshot,
        tmp_path / "aapl.html",
        tickers=("AAPL", "MSFT", "NVDA"),
    ).read_text()

    assert 'href="msft.html"' not in page
    assert 'href="nvda.html"' not in page
    assert '<span class="current-symbol" aria-current="page">AAPL</span>' in page


def test_index_links_every_cached_company(tmp_path) -> None:
    output = render_index(tmp_path / "index.html", tickers=("AAPL", "MSFT", "NVDA"))
    page = output.read_text()

    assert 'href="aapl.html"' in page
    assert "point-in-time SEC ingestion" in page
    assert "source-bounded LLM explanation layer" in page
    assert 'href="msft.html"' in page
    assert 'href="nvda.html"' in page
    assert 'id="ticker-search"' in page
    assert 'id="company-data"' in page
    assert "Not in the current local {count}-company universe" in page
    assert 'id="index-language-toggle"' in page
    assert 'class="index-topbar"' in page
    assert '<details class="company-directory" id="directory">' in page
    assert 'id="directory-grid"' in page
    assert "const directoryPageSize = 9" in page
    assert '<details class="method-note" id="method">' in page
    assert 'data-index-i18n="method.expand"' in page
    assert 'data-index-i18n="hero.title"' in page
    assert "'hero.title': '理解一家公司。'" in page
    assert "Microsoft Corporation" in page


def test_index_searches_full_universe_but_features_only_three(tmp_path) -> None:
    companies = [
        {"ticker": "AAPL", "name": "Apple Inc."},
        {"ticker": "MSFT", "name": "Microsoft Corporation"},
        {"ticker": "NVDA", "name": "NVIDIA Corporation"},
        {"ticker": "TSLA", "name": "Tesla, Inc."},
    ]

    page = render_index(
        tmp_path / "index.html",
        tickers=tuple(company["ticker"] for company in companies),
        companies=companies,
    ).read_text()

    assert "Search 4 locally available companies" in page
    assert '<option value="TSLA">Tesla, Inc.</option>' in page
    assert page.count('class="company-link"') == 3
    assert "const exactTicker" in page
    assert "const exactName" in page
    assert "exactTicker || exactName" in page
    assert "directoryCompanies.slice(start, start + directoryPageSize)" in page
    assert "setSearchStatus(" in page
    assert "refreshSearchStatus();" in page
    assert "status.textContent = indexTr('search.scope'" not in page


def test_company_page_renders_prior_filing_change_evidence(tmp_path) -> None:
    snapshot = _snapshot()
    filing = snapshot.latest_filings[0]
    prior = Citation(
        anchor="prior#sentence-1",
        accession="prior",
        source_url="https://www.sec.gov/prior",
        text="Revenue was $100 million.",
    )
    comparison = FilingComparison(
        comparable_key="8-K:2.02",
        prior_accession="prior",
        prior_accepted_at="2024-09-20T17:00:00-04:00",
        prior_source_url=prior.source_url,
        changes=[
            FilingChange(
                kind="changed",
                current=filing.passages[0],
                prior=prior,
                similarity=0.9,
            )
        ],
        counts={"changed": 1, "added": 0, "removed": 0},
    )
    filing = replace(filing, comparison=comparison)
    snapshot = replace(snapshot, latest_filings=[filing])

    page = render_company_page(snapshot, tmp_path / "abc.html").read_text()

    assert "What changed vs the last similar filing" in page
    assert "1 changed" in page
    assert "Revenue was $100 million." in page
    assert "90% text match" in page


def test_static_404_preserves_supported_scope(tmp_path) -> None:
    page = render_unsupported(tmp_path / "404.html", company_count=193).read_text()

    assert "not cached yet" in page
    assert "193-company universe" in page
    assert "AAPL, MSFT, NVDA" in page
    assert 'href="index.html"' in page
