# Full-width punctuation is intentional in the user-facing Chinese interface copy.
# ruff: noqa: RUF001
"""A self-contained Company Lens page backed only by the snapshot contract."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from company_lens.contracts import (
    Citation,
    CompanySnapshot,
    EvidenceScopeSummary,
    FilingBrief,
    FilingChange,
    FilingEntity,
    FilingTimelinePoint,
    HeadlineBrief,
)
from company_lens.profiles import DEMO_PROFILES

DEFAULT_TICKERS = ("AAPL", "MSFT", "NVDA")


def render_company_page(
    snapshot: CompanySnapshot,
    output: str | Path,
    *,
    tickers: tuple[str, ...] = DEFAULT_TICKERS,
) -> Path:
    """Write one offline-capable HTML page from a versioned snapshot."""
    del tickers  # retained for callers built against the pre-v1.4 renderer
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_document(snapshot), encoding="utf-8")
    return output


def render_index(
    output: str | Path,
    tickers: tuple[str, ...] = DEFAULT_TICKERS,
    *,
    companies: list[dict[str, str]] | None = None,
    featured_tickers: tuple[str, ...] = DEFAULT_TICKERS,
) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    companies = companies or [
        {
            "ticker": ticker,
            "name": DEMO_PROFILES.get(ticker, {}).get("display_name", ticker),
        }
        for ticker in tickers
    ]
    featured = [
        company for company in companies if company["ticker"] in featured_tickers
    ] or companies[:3]
    links = "".join(
        f'<a class="company-link" href="{html.escape(company["ticker"].lower())}.html">'
        f'<span>{html.escape(company["ticker"])}</span>'
        f'<strong>{html.escape(company["name"])}</strong>'
        f'<small data-index-i18n="card.open">Open company lens →</small></a>'
        for company in featured
    )
    options = "".join(
        f'<option value="{html.escape(company["ticker"])}">'
        f'{html.escape(company["name"])}</option>'
        for company in companies
    )
    search_payload = json.dumps(companies, ensure_ascii=False).replace("</", "<\\/")
    output.write_text(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Company Lens</title><style>{_index_css()}</style></head>
<body><main><header class="index-topbar"><a class="index-brand" href="index.html">
<span>CL</span><strong>Company Lens</strong></a><div>
<small data-index-i18n="nav.scope">{len(companies)}-company evidence universe</small>
<button class="index-language-toggle" id="index-language-toggle" type="button"
aria-label="切换为中文" aria-pressed="false">中文</button></div></header>
<div class="index-hero">
<p class="eyebrow" data-index-i18n="hero.eyebrow">SOURCE-BACKED COMPANY INTELLIGENCE</p>
<h1><span data-index-i18n="hero.title">Understand the company.</span><br><em data-index-i18n="hero.emphasis">Keep the evidence.</em></h1>
<p class="lede" data-index-i18n="hero.lede">Historical return and risk, recent SEC disclosures, and a bounded
AI explanation with citations. No price prediction. No investment recommendation.</p>
<form id="company-search" class="company-search">
<label for="ticker-search" data-index-i18n="search.label">Search {len(companies)} locally available companies</label>
<div class="search-row"><input id="ticker-search" name="ticker" list="supported-companies"
placeholder="Try AAPL or Apple" data-index-i18n-placeholder="search.placeholder"
autocomplete="off" spellcheck="false" required>
<datalist id="supported-companies">{options}</datalist>
<button type="submit" data-index-i18n="search.submit">Open lens</button></div>
<p id="search-status" class="search-status" aria-live="polite"
data-status-key="search.hint">Type an exact ticker or
company name from the current local universe.</p></form></div>
    <p class="featured-label" data-index-i18n="featured">Featured examples</p><div class="companies">{links}</div>
    <details class="company-directory" id="directory"><summary><div>
    <p class="eyebrow" data-index-i18n="directory.eyebrow">LOCAL DIRECTORY</p>
    <h2 data-index-i18n="directory.title">Browse without a long page</h2></div>
    <span data-index-i18n="directory.expand">Open paginated directory</span></summary>
    <div class="directory-body"><div class="directory-toolbar">
    <p id="directory-status" aria-live="polite"></p><div>
    <button id="directory-previous" type="button" data-index-i18n="directory.previous">Previous</button>
    <button id="directory-next" type="button" data-index-i18n="directory.next">Next</button>
    </div></div><div class="directory-grid" id="directory-grid"></div></div></details>
    <details class="method-note" id="method"><summary><div>
    <p class="eyebrow" data-index-i18n="method.eyebrow">HOW TO READ A LENS</p>
    <h2 data-index-i18n="method.title">Company first. Evidence second.</h2></div>
    <span data-index-i18n="method.expand">Open the 3-step guide</span></summary><div class="method-body">
    <p data-index-i18n="method.intro">Every page follows one order: historical picture, latest SEC disclosure, then
    company-specific context. Broad market headlines and implementation details stay off
    the company page so they cannot be mistaken for company evidence.</p>
    <ol><li><span>01</span><strong data-index-i18n="method.history">History</strong><small data-index-i18n="method.history_copy">Price and risk versus SPY</small></li>
    <li><span>02</span><strong data-index-i18n="method.disclosure">Disclosure</strong><small data-index-i18n="method.disclosure_copy">What the latest 8-K actually says</small></li>
    <li><span>03</span><strong data-index-i18n="method.boundary">Boundary</strong><small data-index-i18n="method.boundary_copy">Citations, limitations, no forecast</small></li></ol>
    <p class="method-tech" data-index-i18n="method.tech"><strong>Under the hood:</strong> point-in-time SEC ingestion,
    return and risk calculations, deterministic NLP change filtering, and an optional
    source-bounded LLM explanation layer.</p></div></details>
    <p class="foot" data-index-i18n="footer">Cached real-data demonstration ·
SEC EDGAR + vendor-adjusted daily prices</p></main>
<script type="application/json" id="company-data">{search_payload}</script>
<script>{_index_script()}</script></body></html>""",
        encoding="utf-8",
    )
    return output


def render_unsupported(
    output: str | Path,
    *,
    company_count: int,
    featured_tickers: tuple[str, ...] = DEFAULT_TICKERS,
) -> Path:
    """Write a friendly static-host 404 page that preserves the scope boundary."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    featured = ", ".join(featured_tickers)
    output.write_text(
        f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Company not cached · Company Lens</title><style>{_index_css()}</style></head>
<body><main><p class="eyebrow">CACHED DEMO BOUNDARY</p>
<h1>This company is<br><em>not cached yet.</em></h1>
<p class="lede">This ticker is not in the current local {company_count}-company universe.
Featured examples are {html.escape(featured)}. The page will not fabricate a profile
or silently fetch a different evidence set.</p>
<p><a class="return-link" href="index.html">← Return to supported companies</a></p>
</main></body></html>""",
        encoding="utf-8",
    )
    return output


def _document(snapshot: CompanySnapshot) -> str:
    company_name = snapshot.profile.get("display_name") or snapshot.company_name
    payload = json.dumps(snapshot.period_options, ensure_ascii=False).replace("</", "<\\/")
    default_period = _default_period(snapshot)
    filings = "".join(
        _filing_card(filing, index, snapshot.benchmark)
        for index, filing in enumerate(snapshot.latest_filings)
    ) or '<p class="empty">No local 8-K filings are available for this company.</p>'
    period_buttons = "".join(
        f'<button class="period-button" data-period="{label}" type="button">{label}</button>'
        for label in snapshot.period_options
    )
    brief = _brief(snapshot)
    evidence_context = _evidence_context(snapshot.evidence_scope, snapshot.headlines)
    context_nav = (
        '<a href="#context" data-i18n="nav.company_news">Company news</a>'
        if evidence_context
        else ""
    )
    latest_filing_date = (
        snapshot.latest_filings[0].accepted_at[:10] if snapshot.latest_filings else "Unavailable"
    )
    refresh = snapshot.provenance.get("filing_refresh") or {}
    source_checked_at = refresh.get("checked_at") or snapshot.provenance.get("written_at")
    if refresh.get("checked_at"):
        source_check_key = "filings.sec_checked"
        source_check_prefix = "SEC checked"
    elif source_checked_at:
        source_check_key = "filings.sec_collected"
        source_check_prefix = "SEC cache collected"
    else:
        source_check_key = "filings.sec_unavailable"
        source_check_prefix = "SEC cache time unavailable"
    source_check_date = str(source_checked_at)[:10] if source_checked_at else ""
    survivor_warning = ""
    universe = snapshot.provenance.get("universe") or {}
    if universe.get("survivorship_controlled") is False:
        survivor_warning = (
            '<div class="scope-warning"><strong>Universe limitation</strong>'
            '<span>This cached demo uses a survivor convenience sample, not a '
            'point-in-time index universe.</span></div>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Source-backed company intelligence for {html.escape(company_name)}">
<title>{html.escape(snapshot.ticker)} · Company Lens</title>
<style>{_css()}</style>
</head>
<body>
<header class="topbar">
  <a class="brand" href="index.html"><span class="brand-mark">CL</span><span>Company Lens</span></a>
  <nav class="company-nav" aria-label="Company navigation">
    <a href="index.html" class="company-search-link" data-i18n="nav.find">Find a company</a>
    <span class="current-symbol" aria-current="page">{html.escape(snapshot.ticker)}</span>
  </nav>
  <nav class="section-nav" aria-label="Page storyline">
        <a href="#brief" data-i18n="nav.overview">Overview</a>
        <a href="#performance" data-i18n="nav.history">History</a>
        <a href="#filings" data-i18n="nav.filings">Filings</a>
        <a href="#ask" data-i18n="nav.ask">Ask AI</a>{context_nav}
  </nav>
  <span class="trust-label" data-i18n="nav.trust">Evidence, not prediction</span>
  <button class="language-toggle" id="language-toggle" type="button"
  aria-label="切换为中文" aria-pressed="false">中文</button>
</header>

<main>
  {survivor_warning}
  <section class="company-hero">
    <div>
      <p class="eyebrow" data-i18n="hero.eyebrow">COMPANY OVERVIEW · REAL CACHED DATA</p>
      <div class="company-title"><h1>{html.escape(company_name)}</h1>
      <span>{html.escape(snapshot.ticker)}</span></div>
      <p class="profile-category">{html.escape(str(snapshot.profile.get('category', 'Public company')))}</p>
      <p class="hero-copy">{html.escape(str(snapshot.profile.get('summary', 'Business profile unavailable.')))}</p>
      {_profile_meta(snapshot.profile)}
        </div>
    <div class="market-observation">
      <span data-i18n="hero.latest_close">Latest adjusted close</span>
      <strong>{_money(snapshot.market['latest_adjusted_close'])}</strong>
      <small><span data-i18n="hero.observed">Observed</span> {html.escape(snapshot.market['price_date'])}</small>
    </div>
  </section>

  <nav class="workspace-switcher" id="workspace" aria-label="Company research views">
    <div><p class="eyebrow" data-i18n="workspace.eyebrow">RESEARCH WORKSPACE</p>
    <strong data-i18n="workspace.title">Choose one view at a time</strong></div>
    <div class="workspace-links">
      <a href="#brief" data-view-target="brief"><span>01</span><b data-i18n="nav.overview">Overview</b></a>
      <a href="#performance" data-view-target="performance"><span>02</span><b data-i18n="nav.history">History</b></a>
      <a href="#filings" data-view-target="filings"><span>03</span><b data-i18n="nav.filings">Filings</b></a>
      <a href="#ask" data-view-target="ask"><span>04</span><b data-i18n="nav.ask">Ask AI</b></a>
      {'<a href="#context" data-view-target="context"><span>05</span><b data-i18n="nav.company_news">Company news</b></a>' if evidence_context else ''}
    </div>
  </nav>

  <section class="brief-section" id="brief" data-workspace-view="brief" aria-labelledby="brief-title">
    <div class="section-heading">
          <div><p class="eyebrow" data-i18n="brief.eyebrow">AT A GLANCE</p>
          <h2 id="brief-title" data-i18n="brief.title">What matters on this page</h2></div>
      <span class="mode-badge" data-explanation-mode="{html.escape(str(snapshot.explanation.get('mode') or 'unavailable'))}">{_mode_label(snapshot.explanation.get('mode'))}</span>
    </div>
        <p class="brief-intro" data-i18n="brief.intro">The latest disclosure and one historical reference point.
        Details remain below when you want to verify them.</p>
        <div class="brief-grid">{brief}</div>
      </section>

  {_ask_section(snapshot)}

  <section class="performance-section" id="performance" data-workspace-view="performance" aria-labelledby="performance-title">
    <div class="section-heading performance-heading">
      <div><p class="eyebrow" data-i18n="performance.eyebrow">HISTORICAL INVESTMENT PICTURE</p>
      <h2 id="performance-title" data-i18n="performance.title">What happened to $10,000?</h2></div>
      <div class="period-control" aria-label="Historical period">{period_buttons}</div>
    </div>
    <p class="section-intro" data-i18n="performance.intro">Adjusted buy-and-hold history versus {html.escape(snapshot.benchmark)}
    over the exact same dates. Historical context, not expected return.</p>
    <div class="performance-layout">
      <div class="chart-panel">
        <div class="chart-legend">
          <span><i class="line asset"></i>{html.escape(snapshot.ticker)}</span>
          <span><i class="line benchmark"></i>{html.escape(snapshot.benchmark)}</span>
          <span id="chart-range"></span>
        </div>
        <svg id="growth-chart" viewBox="0 0 920 360" role="img"
             aria-label="Growth of ten thousand dollars compared with benchmark">
          <g id="chart-grid"></g><path id="benchmark-path"></path><path id="asset-path"></path>
          <g id="chart-labels"></g><line id="hover-line" x1="0" x2="0" y1="24" y2="314"></line>
          <circle id="asset-point" r="5"></circle><circle id="benchmark-point" r="5"></circle>
          <rect class="chart-hit" x="58" y="20" width="838" height="296"></rect>
        </svg>
        <div id="chart-tooltip" class="chart-tooltip" aria-live="polite"></div>
      </div>
      <aside class="ending-card">
        <span data-i18n="performance.ending_value">Ending value</span><strong id="ending-value"></strong>
        <small id="relative-copy"></small>
        <div class="mini-comparison"><span id="benchmark-ending-label">{html.escape(snapshot.benchmark)} ending value</span>
        <b id="benchmark-ending"></b></div>
      </aside>
    </div>
        <details class="diagnostics-disclosure"><summary data-i18n="performance.more_risk">More risk metrics</summary>
        <div class="metric-grid">
          {_metric("Annualized return", "cagr", "Compound annual growth rate; historical, not forecast.", "metric.return")}
      {_metric("Annualized volatility", "volatility", "Standard deviation of daily returns, annualized.", "metric.volatility")}
      {_metric(f"Beta vs {snapshot.benchmark}", "beta", "Sensitivity to benchmark daily returns; 1.0 moves roughly with the benchmark.", "metric.beta")}
      {_metric(f"Correlation vs {snapshot.benchmark}", "correlation", "How closely daily returns moved together; ranges from -1 to +1.", "metric.correlation")}
      {_metric("Current drawdown", "current-drawdown", "Distance below the highest adjusted value in the period.", "metric.current_drawdown")}
      {_metric("Worst day", "worst-day", "Largest single-session adjusted-price decline in the selected period.", "metric.worst_day")}
        </div></details>
        <div class="risk-note" id="risk-note"></div>
  </section>

  <section class="filings-section" id="filings" data-workspace-view="filings" aria-labelledby="filings-title">
    <div class="section-heading">
      <div><p class="eyebrow" data-i18n="filings.eyebrow">FILING INTELLIGENCE</p>
      <h2 id="filings-title" data-i18n="filings.title">Recent 8-K disclosures</h2></div>
      <div class="freshness-group"><span class="freshness"
      data-freshness-key="filings.latest_accepted"
      data-freshness-date="{html.escape(latest_filing_date)}">Latest filing accepted {html.escape(latest_filing_date)}</span>
      <span class="freshness" data-freshness-key="{source_check_key}"
      data-freshness-date="{html.escape(source_check_date)}">{source_check_prefix}{' ' if source_check_date else ''}{html.escape(source_check_date)}</span></div>
    </div>
        <p class="section-intro" data-i18n="filings.intro">The newest filing opens first. Read what arrived, what the
        next eligible session did, and whether the wording changed in a substantive way.</p>
        <div class="filing-list">{filings}</div>
  </section>

  {evidence_context}

    </main>

    <footer><div><strong>Company Lens</strong><span data-i18n="footer.tagline">Understand the evidence before forming a view.</span>
    <a href="index.html#method" data-i18n="footer.how">How to read this lens</a></div>
<div class="footer-meta"><span>Snapshot v{html.escape(snapshot.schema_version)}</span>
<span>Market through {html.escape(snapshot.as_of)}</span><span>SEC + adjusted daily prices</span></div></footer>

<script type="application/json" id="period-data">{payload}</script>
<script>{_script(default_period, snapshot.ticker, snapshot.benchmark)}</script>
</body></html>"""


def _ask_section(snapshot: CompanySnapshot) -> str:
    ticker = html.escape(snapshot.ticker)
    return f"""<section class="ask-section" id="ask" data-workspace-view="ask"
    aria-labelledby="ask-title">
    <div class="section-heading"><div><p class="eyebrow" data-i18n="ask.eyebrow">CONTROLLED LLM Q&amp;A</p>
    <h2 id="ask-title" data-i18n="ask.title">Ask the evidence</h2></div>
    <span class="ask-validation" data-i18n="ask.validated">Every answer is validated</span></div>
    <p class="section-intro" data-i18n="ask.intro">Choose a model and ask about {ticker}. The model receives only
    this page's cached SEC passages, calculated history, filing reaction, and matched company
    headlines. Unsupported citations, invented numbers, advice, and forecasts are withheld.</p>
    <div class="ask-layout">
      <form class="ask-form" id="ask-form">
        <div class="ask-controls">
          <label><span data-i18n="ask.model">Model</span><select id="ask-model" name="provider" disabled>
          <option data-i18n="ask.loading_models">Loading live models…</option></select></label>
          <label><span data-i18n="ask.answer_language">Answer language</span><select id="ask-language" name="language">
          <option value="English">English</option><option value="Chinese">中文</option>
          </select></label>
        </div>
        <label class="ask-question"><span data-i18n="ask.question">Question</span>
        <textarea id="ask-question" maxlength="280" rows="3"
        placeholder="What does the latest 8-K tell me?"
        data-i18n-placeholder="ask.placeholder" required></textarea></label>
        <div class="ask-suggestions" aria-label="Suggested questions">
          <button type="button" data-i18n="ask.latest_8k"
          data-question-en="What does the latest 8-K tell me?"
          data-question-zh="最新一份 8-K 披露了什么？">Latest 8-K</button>
          <button type="button" data-i18n="ask.vs_benchmark"
          data-question-en="How did {ticker} perform versus its benchmark?"
          data-question-zh="{ticker} 与基准相比表现如何？">Vs benchmark</button>
          <button type="button" data-i18n="ask.evidence_limits"
          data-question-en="What are the limits of this evidence?"
          data-question-zh="目前这些证据有哪些局限？">Evidence limits</button>
        </div>
        <div class="ask-submit-row"><button id="ask-submit" type="submit" disabled
        data-i18n="ask.submit">Ask model</button>
        <span id="ask-status" aria-live="polite"
        data-status-key="ask.checking_models">Checking available models…</span></div>
      </form>
      <div class="ask-result" id="ask-result" aria-live="polite">
        <p class="ask-result-kicker" data-i18n="ask.control_title">HOW CONTROL STAYS VISIBLE</p>
        <ol><li><span>1</span><span data-i18n="ask.control_1">Question is matched to a frozen {ticker} evidence packet.</span></li>
        <li><span>2</span><span data-i18n="ask.control_2">The selected provider returns structured claims and citation IDs.</span></li>
        <li><span>3</span><span data-i18n="ask.control_3">A server-side validator rejects unsupported citations, numbers,
        advice, or forecasts before anything appears here.</span></li></ol>
      </div>
    </div>
    <p class="ask-boundary" data-i18n="ask.boundary"><strong>Scope:</strong> explanation, not recommendation ·
    maximum 280 characters · public-demo rate limit · API keys remain server-side</p>
    </section>"""


def _evidence_context(
    scope: EvidenceScopeSummary | None,
    headlines: list[HeadlineBrief],
) -> str:
    company_headlines = [
        headline for headline in headlines if headline.source_type == "company_news"
    ][:3]
    if scope is None or not company_headlines:
        return ""

    cards = "".join(_headline_card(headline) for headline in company_headlines)
    status_label = {
        "available": "Available",
        "empty": "Empty",
        "stale": "Stale cache",
        "not_configured": "Not configured",
    }[scope.status]
    freshness = _pretty_context_time(scope.generated_at) if scope.generated_at else "Unknown"
    return f"""<section class="context-section" id="context" data-workspace-view="context"
    aria-labelledby="context-title">
    <div class="section-heading"><div><p class="eyebrow" data-i18n="context.eyebrow">COMPANY-SPECIFIC CONTEXT</p>
    <h2 id="context-title" data-i18n="context.title">Recent company coverage</h2></div>
    <span class="context-status {html.escape(scope.status)}"
    data-i18n="context.status_{html.escape(scope.status)}">{html.escape(status_label)}</span></div>
    <p class="section-intro" data-i18n="context.intro">Only headlines matched to this ticker appear here. They add
    context but are not used to calculate returns or filing reactions.</p>
    <p class="context-freshness"><span data-i18n="context.refreshed">Refreshed</span> {html.escape(freshness)}</p>
    <div class="headline-list">{cards}</div>
    </section>"""


def _headline_card(headline: HeadlineBrief) -> str:
    return (
        f'<article class="headline-card" data-citation="{html.escape(headline.citation)}">'
        f'<div class="headline-meta"><span>{html.escape(headline.publisher)}</span>'
        f"<span>{html.escape(_pretty_context_time(headline.published_at))}</span></div>"
        f"<h3>{html.escape(headline.headline)}</h3>"
        f'<a href="{html.escape(headline.url)}" target="_blank" '
        'rel="noopener noreferrer" data-i18n="context.read_source">Read source ↗</a></article>'
    )


def _pretty_context_time(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%b %d, %Y · %H:%M %Z").rstrip(" ·")


def _profile_meta(profile: dict[str, Any]) -> str:
    coverage = profile.get("coverage") or {}
    price_start = html.escape(str(coverage.get("price_start", "Unavailable")))
    price_end = html.escape(str(coverage.get("price_end", "Unavailable")))
    filing_count = html.escape(str(coverage.get("filings_in_snapshot", 0)))
    source_url = profile.get("source_url")
    source_label = profile.get("source_label")
    source = ""
    if source_url and source_label:
        source = (
            f'<a href="{html.escape(str(source_url))}" target="_blank" rel="noreferrer">'
            f'{html.escape(str(source_label))} ↗</a>'
        )
    cik = profile.get("cik")
    cik_label = f"CIK {html.escape(str(cik))}" if cik else "CIK unavailable"
    return (
        '<div class="profile-meta">'
        f"<span>{cik_label}</span>{source}"
        f"<span>Prices {price_start}—{price_end}</span>"
        f"<span>{filing_count} recent filings in snapshot</span>"
        "</div>"
    )


def _brief(snapshot: CompanySnapshot) -> str:
    latest = snapshot.latest_filings[0] if snapshot.latest_filings else None
    changed = _first_claim(snapshot.explanation, "what_changed")
    uncertainty = _first_claim(snapshot.explanation, "uncertainties")
    changed_links = "".join(
        _citation_link(value) for value in changed.get("citations", [])
    )
    if latest:
        filing_title_key = ""
        filing_title = latest.items[0]["label"] if latest.items else "Corporate update"
        filing_meta = (
            f'<span>{html.escape(latest.form)}</span>'
            f'<span>{html.escape(_pretty_date(latest.accepted_at))}</span>'
        )
        if latest.reaction:
            filing_meta += (
                f'<span>{_signed_percent(latest.reaction.benchmark_adjusted_move)} '
                f'vs {html.escape(snapshot.benchmark)}</span>'
            )
        source_link = (
            f'<a href="{html.escape(latest.source_url)}" target="_blank" '
            'rel="noreferrer" data-i18n="filing.open_sec">Open SEC filing ↗</a>'
        )
    else:
        filing_title_key = ' data-i18n="filing.no_local_filing"'
        filing_title = "No local filing"
        filing_meta = '<span data-i18n="filing.evidence_unavailable">Evidence unavailable</span>'
        source_link = ""
    return f"""
    <article class="brief-card brief-lead observed">
      <div class="brief-card-heading"><span data-i18n="brief.latest_disclosure">Latest SEC disclosure</span>{source_link}</div>
      <h3{filing_title_key}>{html.escape(filing_title)}</h3>
      <p>{html.escape(str(changed.get('text', 'Not available.')))}</p>
      <div class="brief-meta">{filing_meta}</div><div class="claim-links">{changed_links}</div>
    </article>
    <article class="brief-card brief-numbers calculated">
      <span data-i18n="brief.selected_period">Selected historical period</span>
      <div class="brief-metrics">
        <div><strong id="total-return"></strong><small data-i18n="brief.total_return">Total return</small></div>
        <div><strong id="max-drawdown"></strong><small data-i18n="brief.max_drawdown">Maximum drawdown</small></div>
      </div>
      <p><span id="brief-period-label"></span> <span data-i18n="brief.period_context">of adjusted daily prices versus
      {html.escape(snapshot.benchmark)}. Context, not a forecast.</span></p>
      <a href="#performance" data-view-target="performance"
      data-i18n="brief.explore_history">Explore the full history ↓</a>
    </article>
    <p class="brief-boundary"><strong data-i18n="brief.boundary">Boundary:</strong>
    {html.escape(str(uncertainty.get('text', 'Not available.')))}</p>"""


def _first_claim(explanation: dict, section: str) -> dict:
    claims = explanation.get(section, [])
    return claims[0] if claims else {"text": "Not available.", "citations": []}


def _mode_label(mode: Any) -> str:
    if mode == "grounded_llm":
        return "Source-bounded AI"
    if mode == "deterministic_fallback":
        return "Source-backed summary"
    return html.escape(str(mode or "Explanation unavailable"))


def _filing_card(filing: FilingBrief, index: int, benchmark: str) -> str:
    item_chips = "".join(
        f'<span class="item-chip" title="{html.escape(item["label"])}">'
        f'{html.escape(item["code"])} · {html.escape(item["label"])}</span>'
        for item in filing.items
    )
    reaction = (
        "Reaction not yet measurable"
        if filing.reaction is None
        else f"{_signed_percent(filing.reaction.benchmark_adjusted_move)} vs {benchmark}"
    )
    entities = "".join(_entity_chip(entity) for entity in filing.entities)
    if not entities:
        entities = "".join(
            f'<a class="number-chip" href="#{_dom_id(number["citation"])}">'
            f'{html.escape(number["value"])}</a>' for number in filing.key_numbers
        )
    entities = entities or (
        '<span class="missing" data-i18n="filing.no_entities">'
        "No cited entity in the primary document</span>"
    )
    passages = "".join(_passage(passage, filing.entities) for passage in filing.passages)
    if not passages:
        passages = (
            '<p class="missing" data-i18n="filing.no_passages">'
            "No passage passed the deterministic relevance threshold.</p>"
        )
    expanded = " open" if index == 0 else ""
    return f"""<details class="filing-card"{expanded}>
      <summary><div><span class="filing-form">{html.escape(filing.form)}</span>
      <strong>{html.escape(filing.items[0]['label'] if filing.items else 'Corporate update')}</strong>
      <small><span data-i18n="filing.accepted">Accepted</span> {html.escape(_pretty_date(filing.accepted_at))}</small></div>
      <div class="filing-summary-meta"><span>{html.escape(reaction)}</span>
      <span data-i18n="filing.view_evidence">View evidence</span><i>⌄</i></div></summary>
      <div class="filing-body"><div class="filing-items">{item_chips}</div>
      {_reaction_block(filing, benchmark)}
      {_comparison_block(filing)}
      <details class="source-details"><summary data-i18n="filing.source_facts">Source passages and extracted facts</summary>
      <div class="filing-columns"><div><h3 data-i18n="filing.extracted_facts">Extracted facts</h3><div class="number-list">{entities}</div>
      <h3 data-i18n="filing.relevant_passages">Relevant passages</h3><div class="passages">{passages}</div></div>
      <aside><span data-i18n="filing.source_record">Source record</span><code>{html.escape(filing.accession)}</code>
      <a href="{html.escape(filing.source_url)}" target="_blank" rel="noreferrer" data-i18n="filing.open_sec">Open SEC filing ↗</a>
      <p data-i18n="filing.source_note">SEC excerpts remain in the filed language so citations can be verified exactly.</p></aside></div></details></div>
      </details>"""


def _filing_timeline(points: list[FilingTimelinePoint], benchmark: str) -> str:
    if not points:
        return ""
    events = []
    for point in points:
        if point.reaction is None:
            direction = "unavailable"
            move = "Reaction unavailable"
            context = "Required session bars are not both cached"
        else:
            value = point.reaction.benchmark_adjusted_move
            direction = "positive" if value > 0 else "negative" if value < 0 else "flat"
            move = f"{_signed_percent(value)} vs {benchmark}"
            context = (
                f"{point.reaction.magnitude_percentile:.0%} of earlier filings were smaller"
                if point.reaction.magnitude_percentile is not None
                else f"{point.reaction.prior_sample_size} earlier measurable filings"
            )
        accepted = datetime.fromisoformat(point.accepted_at).strftime("%b %d, %Y")
        events.append(
            f'<a class="timeline-event {direction}" href="{html.escape(point.source_url)}" '
            f'target="_blank" rel="noreferrer"><span>{html.escape(accepted)}</span>'
            f'<i aria-hidden="true"></i><strong>{html.escape(point.item_label)}</strong>'
            f'<small>Item {html.escape(point.item_code)}</small><b>{html.escape(move)}</b>'
            f'<em>{html.escape(context)}</em></a>'
        )
    return f"""<section class="timeline-panel" aria-label="Recent filing timeline">
    <div class="timeline-heading"><div><span>Recent filing timeline</span>
    <strong>What arrived, and how the next eligible session moved</strong></div>
    <small>Oldest → newest · latest {len(points)}</small></div>
    <div class="timeline-track">{''.join(events)}</div>
    <p>Relative moves are open-to-close company returns less {html.escape(benchmark)};
    they are historical context, not event forecasts.</p></section>"""


def _reaction_block(filing: FilingBrief, benchmark: str) -> str:
    reaction = filing.reaction
    if reaction is None:
        return (
            '<div class="reaction-empty"><strong data-i18n="reaction.unavailable">'
            'Market reaction not yet measurable</strong><span data-i18n="reaction.missing_bars">'
            "The required company and benchmark bars are not both present for the "
            "first eligible session.</span></div>"
        )
    if reaction.magnitude_percentile is None:
        history_value = "Building history"
        history_note = (
            f"{reaction.prior_sample_size} earlier measurable filing"
            f"{'s' if reaction.prior_sample_size != 1 else ''}; shown after 5"
        )
    else:
        history_value = f"More extreme than {reaction.magnitude_percentile:.0%}"
        history_note = f"of {reaction.prior_sample_size} earlier measurable filings"
    asset_move = _signed_percent(reaction.asset_open_to_close)
    benchmark_move = _signed_percent(reaction.benchmark_open_to_close)
    relative_move = _signed_percent(reaction.benchmark_adjusted_move)
    session = datetime.fromisoformat(reaction.session).strftime("%b %d, %Y")
    return f"""<section class="reaction-panel" aria-label="Observed filing market reaction">
    <div class="reaction-heading"><div><span data-i18n="reaction.title">What happened next</span>
    <strong>{html.escape(session)} · first eligible session</strong></div>
    <small data-i18n="reaction.observed">Observed, not attributed</small></div>
    <div class="reaction-grid">
    <div><span data-i18n="reaction.company_move">Company move</span><strong>{html.escape(asset_move)}</strong>
    <small data-i18n="reaction.open_close">open to close</small></div>
    <div><span data-i18n="reaction.after_benchmark">After subtracting {html.escape(benchmark)}</span><strong>{html.escape(relative_move)}</strong>
    <small>{html.escape(asset_move)} less {html.escape(benchmark_move)}</small></div>
    <div><span data-i18n="reaction.compared">Compared with past filings</span><strong>{html.escape(history_value)}</strong>
    <small>{html.escape(history_note)}</small></div></div>
    <p data-i18n="reaction.boundary">This is the first session whose opening followed SEC acceptance. It shows what
    happened next; it does not claim the filing caused the move.</p></section>"""


def _comparison_block(filing: FilingBrief) -> str:
    comparison = filing.comparison
    if comparison is None:
        return (
            '<div class="comparison-empty"><strong data-i18n="comparison.unavailable">'
            'Prior comparison unavailable</strong><span data-i18n="comparison.no_prior">'
            "No earlier filing with the same form and primary event type exists in "
            "the local issuer history.</span></div>"
        )
    counts = comparison.counts
    substantive_count = sum(counts.get(kind, 0) for kind in ("changed", "added", "removed"))
    count_chips = "" if not substantive_count else "".join(
        f'<span class="change-count {kind}">{counts.get(kind, 0)} {kind}</span>'
        for kind in ("changed", "added", "removed")
        if counts.get(kind, 0)
    )
    selected = _representative_changes(comparison.changes)
    if selected:
        changes = "".join(_change_card(change) for change in selected)
    else:
        changes = (
            '<div class="comparison-clear"><strong data-i18n="comparison.no_change">'
            'No substantive wording change detected</strong>'
            '<span data-i18n="comparison.no_change_note">'
            "Date and fiscal-quarter roll-forwards are treated as routine updates. "
            "Referenced exhibits may still contain detail outside the cached primary document.</span>"
            "</div>"
        )
    return f"""<section class="comparison-panel" aria-label="Prior comparable filing changes">
    <div class="comparison-heading"><div><span data-i18n="comparison.title">What changed vs the last similar filing</span>
    <strong>{html.escape(_pretty_date(comparison.prior_accepted_at))}</strong></div>
    <a href="{html.escape(comparison.prior_source_url)}" target="_blank" rel="noreferrer">
    <span data-i18n="comparison.prior">Prior filing ↗</span></a></div><div class="change-counts">{count_chips}</div>
    <div class="change-list">{changes}</div></section>"""


def _representative_changes(
    changes: list[FilingChange], limit: int = 4
) -> list[FilingChange]:
    selected = []
    for kind in ("changed", "added", "removed"):
        match = next((change for change in changes if change.kind == kind), None)
        if match is not None:
            selected.append(match)
    selected.extend(change for change in changes if change not in selected)
    return selected[:limit]


def _change_card(change: FilingChange) -> str:
    current = _change_quote("Current", change.current) if change.current else ""
    prior = _change_quote("Prior", change.prior) if change.prior else ""
    similarity = (
        f'<span class="similarity">{change.similarity:.0%} text match</span>'
        if change.similarity is not None
        else ""
    )
    return (
        f'<article class="change-card {html.escape(change.kind)}">'
        f'<header><strong>{html.escape(change.kind.title())}</strong>{similarity}</header>'
        f"{current}{prior}</article>"
    )


def _change_quote(label: str, citation: Citation) -> str:
    return (
        f'<div class="change-quote"><span>{html.escape(label)}</span>'
        f'<p>{html.escape(citation.text)}</p>'
        f'<a href="{html.escape(citation.source_url)}" target="_blank" rel="noreferrer">'
        f'{html.escape(citation.anchor)} ↗</a></div>'
    )


def _entity_chip(entity: FilingEntity) -> str:
    label = entity.kind.replace("_", " ")
    title = f"{label}; normalized {entity.normalized_value} {entity.unit}"
    return (
        f'<a class="number-chip entity-chip" href="#{_dom_id(entity.citation)}" '
        f'title="{html.escape(title)}"><small>{html.escape(label)}</small>'
        f'{html.escape(entity.text)}</a>'
    )


def _passage(citation: Citation, entities: list[FilingEntity] | None = None) -> str:
    cited = sorted(
        (entity for entity in entities or [] if entity.citation == citation.anchor),
        key=lambda entity: entity.source_start,
    )
    text = _highlight_entities(citation.text, cited)
    return (
        f'<blockquote id="{_dom_id(citation.anchor)}"><p>{text}</p>'
        f'<a href="{html.escape(citation.source_url)}" target="_blank" rel="noreferrer">'
        f'{html.escape(citation.anchor)} ↗</a></blockquote>'
    )


def _highlight_entities(text: str, entities: list[FilingEntity]) -> str:
    rendered = []
    position = 0
    for entity in entities:
        if (
            entity.source_start < position
            or text[entity.source_start:entity.source_end] != entity.text
        ):
            continue
        rendered.append(html.escape(text[position:entity.source_start]))
        rendered.append(
            f'<mark class="entity-mark {html.escape(entity.kind)}" '
            f'title="{html.escape(entity.kind.replace("_", " "))}">'
            f'{html.escape(entity.text)}</mark>'
        )
        position = entity.source_end
    rendered.append(html.escape(text[position:]))
    return "".join(rendered)


def _citation_link(value: str) -> str:
    if value.startswith("metric:"):
        return (
            '<a href="#performance" class="metric-citation" '
            'data-i18n="citation.metric">Calculated metric</a>'
        )
    return (
        f'<a href="#{_dom_id(value)}" class="source-citation" '
        'data-i18n="citation.source">Source passage</a>'
    )


def _metric(label: str, element_id: str, definition: str, translation_key: str) -> str:
    return (
        f'<article class="metric-card"><span><span data-i18n="{translation_key}">'
        f'{html.escape(label)}</span><i title="{html.escape(definition)}" '
        f'data-i18n-title="{translation_key}.definition">?</i></span>'
        f'<strong id="{element_id}"></strong><small data-i18n="{translation_key}.definition">'
        f'{html.escape(definition)}</small></article>'
    )


def _default_period(snapshot: CompanySnapshot) -> str:
    years = round((datetime.fromisoformat(snapshot.period["end"]) -
                   datetime.fromisoformat(snapshot.period["start"])).days / 365.25)
    candidate = f"{years}Y"
    return candidate if candidate in snapshot.period_options else next(iter(snapshot.period_options))


def _pretty_date(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%b %d, %Y · %H:%M ET")


def _dom_id(value: str) -> str:
    return "citation-" + re.sub(r"[^a-zA-Z0-9_-]+", "-", value)


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _signed_percent(value: float) -> str:
    return f"{value:+.1%}" if value else "0.0%"


def _script(default_period: str, ticker: str, benchmark: str) -> str:
    translations = json.dumps(
        {
            "en": {
                "nav.find": "Find a company",
                "nav.overview": "Overview",
                "nav.ask": "Ask AI",
                "nav.history": "History",
                "nav.filings": "Filings",
                "nav.company_news": "Company news",
                "nav.trust": "Evidence, not prediction",
                "workspace.eyebrow": "RESEARCH WORKSPACE",
                "workspace.title": "Choose one view at a time",
                "hero.eyebrow": "COMPANY OVERVIEW · REAL CACHED DATA",
                "hero.latest_close": "Latest adjusted close",
                "hero.observed": "Observed",
                "brief.eyebrow": "AT A GLANCE",
                "brief.title": "What matters on this page",
                "brief.intro": (
                    "The latest disclosure and one historical reference point. "
                    "Details remain below when you want to verify them."
                ),
                "brief.latest_disclosure": "Latest SEC disclosure",
                "brief.selected_period": "Selected historical period",
                "brief.total_return": "Total return",
                "brief.max_drawdown": "Maximum drawdown",
                "brief.period_context": (
                    "of adjusted daily prices versus {benchmark}. Context, not a forecast."
                ),
                "brief.explore_history": "Explore the full history ↓",
                "brief.boundary": "Boundary:",
                "mode.grounded": "Source-bounded AI",
                "mode.fallback": "Source-backed summary",
                "mode.unavailable": "Explanation unavailable",
                "ask.eyebrow": "CONTROLLED LLM Q&A",
                "ask.title": "Ask the evidence",
                "ask.validated": "Every answer is validated",
                "ask.intro": (
                    "Choose a model and ask about {ticker}. The model receives only "
                    "this page's cached SEC passages, calculated history, filing reaction, "
                    "and matched company headlines. Unsupported citations, invented "
                    "numbers, advice, and forecasts are withheld."
                ),
                "ask.model": "Model",
                "ask.loading_models": "Loading live models…",
                "ask.answer_language": "Answer language",
                "ask.question": "Question",
                "ask.placeholder": "What does the latest 8-K tell me?",
                "ask.latest_8k": "Latest 8-K",
                "ask.vs_benchmark": "Vs benchmark",
                "ask.evidence_limits": "Evidence limits",
                "ask.submit": "Ask model",
                "ask.checking_models": "Checking available models…",
                "ask.control_title": "HOW CONTROL STAYS VISIBLE",
                "ask.control_1": "Question is matched to a frozen {ticker} evidence packet.",
                "ask.control_2": (
                    "The selected provider returns structured claims and citation IDs."
                ),
                "ask.control_3": (
                    "A server-side validator rejects unsupported citations, numbers, "
                    "advice, or forecasts before anything appears here."
                ),
                "ask.boundary": (
                    "Scope: explanation, not recommendation · maximum 280 characters · "
                    "public-demo rate limit · API keys remain server-side"
                ),
                "performance.eyebrow": "HISTORICAL INVESTMENT PICTURE",
                "performance.title": "What happened to $10,000?",
                "performance.intro": (
                    "Adjusted buy-and-hold history versus {benchmark} over the exact same "
                    "dates. Historical context, not expected return."
                ),
                "performance.ending_value": "Ending value",
                "performance.more_risk": "More risk metrics",
                "metric.return": "Annualized return",
                "metric.return.definition": "Compound annual growth rate; historical, not forecast.",
                "metric.volatility": "Annualized volatility",
                "metric.volatility.definition": "Standard deviation of daily returns, annualized.",
                "metric.beta": "Beta vs {benchmark}",
                "metric.beta.definition": (
                    "Sensitivity to benchmark daily returns; 1.0 moves roughly with the benchmark."
                ),
                "metric.correlation": "Correlation vs {benchmark}",
                "metric.correlation.definition": (
                    "How closely daily returns moved together; ranges from -1 to +1."
                ),
                "metric.current_drawdown": "Current drawdown",
                "metric.current_drawdown.definition": (
                    "Distance below the highest adjusted value in the period."
                ),
                "metric.worst_day": "Worst day",
                "metric.worst_day.definition": (
                    "Largest single-session adjusted-price decline in the selected period."
                ),
                "filings.eyebrow": "FILING INTELLIGENCE",
                "filings.title": "Recent 8-K disclosures",
                "filings.latest_accepted": "Latest filing accepted",
                "filings.sec_checked": "SEC checked",
                "filings.sec_collected": "SEC cache collected",
                "filings.sec_unavailable": "SEC cache time unavailable",
                "filings.intro": (
                    "The newest filing opens first. Read what arrived, what the next eligible "
                    "session did, and whether the wording changed in a substantive way."
                ),
                "filing.accepted": "Accepted",
                "filing.view_evidence": "View evidence",
                "filing.source_facts": "Source passages and extracted facts",
                "filing.extracted_facts": "Extracted facts",
                "filing.relevant_passages": "Relevant passages",
                "filing.no_local_filing": "No local filing",
                "filing.evidence_unavailable": "Evidence unavailable",
                "filing.no_entities": "No cited entity in the primary document",
                "filing.no_passages": (
                    "No passage passed the deterministic relevance threshold."
                ),
                "filing.source_record": "Source record",
                "filing.open_sec": "Open SEC filing ↗",
                "filing.source_note": (
                    "SEC excerpts remain in the filed language so citations can be verified exactly."
                ),
                "reaction.title": "What happened next",
                "reaction.observed": "Observed, not attributed",
                "reaction.company_move": "Company move",
                "reaction.open_close": "open to close",
                "reaction.after_benchmark": "After subtracting {benchmark}",
                "reaction.compared": "Compared with past filings",
                "reaction.unavailable": "Market reaction not yet measurable",
                "reaction.missing_bars": (
                    "The required company and benchmark bars are not both present for "
                    "the first eligible session."
                ),
                "reaction.boundary": (
                    "This is the first session whose opening followed SEC acceptance. It shows "
                    "what happened next; it does not claim the filing caused the move."
                ),
                "comparison.title": "What changed vs the last similar filing",
                "comparison.prior": "Prior filing ↗",
                "comparison.unavailable": "Prior comparison unavailable",
                "comparison.no_prior": (
                    "No earlier filing with the same form and primary event type exists "
                    "in the local issuer history."
                ),
                "comparison.no_change": "No substantive wording change detected",
                "comparison.no_change_note": (
                    "Date and fiscal-quarter roll-forwards are treated as routine updates. "
                    "Referenced exhibits may still contain detail outside the cached "
                    "primary document."
                ),
                "context.eyebrow": "COMPANY-SPECIFIC CONTEXT",
                "context.title": "Recent company coverage",
                "context.intro": (
                    "Only headlines matched to this ticker appear here. They add context but are "
                    "not used to calculate returns or filing reactions."
                ),
                "context.refreshed": "Refreshed",
                "context.read_source": "Read source ↗",
                "context.status_available": "Available",
                "context.status_empty": "Empty",
                "context.status_stale": "Stale cache",
                "context.status_not_configured": "Not configured",
                "citation.metric": "Calculated metric",
                "citation.source": "Source passage",
                "footer.tagline": "Understand the evidence before forming a view.",
                "footer.how": "How to read this lens",
                "performance.relative": "{value} vs {benchmark} over this period",
                "performance.benchmark_ending": "{benchmark} ending value",
                "performance.not_available": "Not available",
                "performance.not_recovered": "not recovered within the selected period",
                "performance.recovered": "recovered after {sessions} trading sessions",
                "performance.risk_title": "Experienced risk",
                "performance.risk_copy": (
                    "The largest decline was {asset} versus {benchmark_drawdown} for "
                    "{benchmark}, reaching its trough on {date}; it {recovery}."
                ),
                "ask.models_ready": "{count} validated model{suffix} available",
                "ask.models_unavailable": "Live models unavailable",
                "ask.offline": (
                    "The page data remains available; live Q&A is currently offline."
                ),
                "ask.reading": "Reading the bounded evidence packet…",
                "ask.waiting": "Waiting for the selected model…",
                "ask.answer_failed": "The answer could not be generated.",
                "ask.selected_unavailable": "The selected model is unavailable.",
                "ask.withheld": "No unvalidated answer was shown.",
                "ask.validated_answer": "VALIDATED ANSWER",
                "ask.evidence_through": "evidence through {date}",
                "ask.limitations": "What this answer cannot establish",
            },
            "zh": {
                "nav.find": "查找公司",
                "nav.overview": "概览",
                "nav.ask": "问 AI",
                "nav.history": "历史表现",
                "nav.filings": "公司披露",
                "nav.company_news": "公司新闻",
                "nav.trust": "基于证据，不做预测",
                "workspace.eyebrow": "公司研究工作台",
                "workspace.title": "每次聚焦一个研究视图",
                "hero.eyebrow": "公司概览 · 真实缓存数据",
                "hero.latest_close": "最新复权收盘价",
                "hero.observed": "观测日期",
                "brief.eyebrow": "一分钟概览",
                "brief.title": "这页最值得关注的内容",
                "brief.intro": "先看最新披露和一个历史参照；需要核验时，再展开下方证据。",
                "brief.latest_disclosure": "最新 SEC 披露",
                "brief.selected_period": "所选历史期间",
                "brief.total_return": "累计回报",
                "brief.max_drawdown": "最大回撤",
                "brief.period_context": "的复权日线数据，对比 {benchmark}。仅作历史背景，不代表预测。",
                "brief.explore_history": "查看完整历史 ↓",
                "brief.boundary": "证据边界：",
                "mode.grounded": "来源受限的 AI",
                "mode.fallback": "基于来源的摘要",
                "mode.unavailable": "暂无解释",
                "ask.eyebrow": "受控的 LLM 问答",
                "ask.title": "向证据提问",
                "ask.validated": "每个答案都经过校验",
                "ask.intro": (
                    "选择模型并询问 {ticker}。模型只能读取本页缓存的 SEC 原文、计算得到的"
                    "历史表现、披露后的市场反应和匹配到的公司新闻。无法支持的引用、虚构数字、"
                    "投资建议和价格预测不会显示。"
                ),
                "ask.model": "模型",
                "ask.loading_models": "正在读取可用模型…",
                "ask.answer_language": "回答语言",
                "ask.question": "问题",
                "ask.placeholder": "最新一份 8-K 披露了什么？",
                "ask.latest_8k": "最新 8-K",
                "ask.vs_benchmark": "对比基准",
                "ask.evidence_limits": "证据边界",
                "ask.submit": "询问模型",
                "ask.checking_models": "正在检查可用模型…",
                "ask.control_title": "如何让回答保持可控",
                "ask.control_1": "问题只会匹配到冻结的 {ticker} 证据包。",
                "ask.control_2": "所选模型必须返回结构化结论和引用编号。",
                "ask.control_3": "服务端会拦截无来源引用、额外数字、投资建议和价格预测。",
                "ask.boundary": (
                    "范围：解释而非推荐 · 问题最多 280 字符 · 公开演示限流 · API 密钥只在服务端"
                ),
                "performance.eyebrow": "长期历史表现",
                "performance.title": "投入 10,000 美元后发生了什么？",
                "performance.intro": (
                    "按完全相同日期比较复权持有 {benchmark} 的历史结果；这是历史背景，不是"
                    "预期回报。"
                ),
                "performance.ending_value": "期末价值",
                "performance.more_risk": "展开更多风险指标",
                "metric.return": "年化回报",
                "metric.return.definition": "复合年增长率；仅为历史结果，不是预测。",
                "metric.volatility": "年化波动率",
                "metric.volatility.definition": "日收益率标准差按年化处理。",
                "metric.beta": "相对 {benchmark} 的 Beta",
                "metric.beta.definition": "对基准日收益变化的敏感度；1.0 大致表示与基准同步。",
                "metric.correlation": "相对 {benchmark} 的相关性",
                "metric.correlation.definition": "日收益共同变化的程度，范围从 -1 到 +1。",
                "metric.current_drawdown": "当前回撤",
                "metric.current_drawdown.definition": "当前复权价值低于所选期间最高点的幅度。",
                "metric.worst_day": "最差单日",
                "metric.worst_day.definition": "所选期间内最大的单日复权价格跌幅。",
                "filings.eyebrow": "公司披露解读",
                "filings.title": "近期 8-K 披露",
                "filings.latest_accepted": "最新披露接收日期",
                "filings.sec_checked": "SEC 检查日期",
                "filings.sec_collected": "SEC 缓存采集日期",
                "filings.sec_unavailable": "SEC 缓存时间不可用",
                "filings.intro": "最新披露默认展开：查看公司说了什么、下一可交易日如何变化，以及措辞是否有实质改变。",
                "filing.accepted": "SEC 接收时间",
                "filing.view_evidence": "查看证据",
                "filing.source_facts": "来源段落与提取事实",
                "filing.extracted_facts": "提取到的事实",
                "filing.relevant_passages": "相关原文",
                "filing.no_local_filing": "暂无本地披露",
                "filing.evidence_unavailable": "证据暂不可用",
                "filing.no_entities": "主文档中没有带引用的实体",
                "filing.no_passages": "没有段落达到确定性相关度阈值。",
                "filing.source_record": "来源记录",
                "filing.open_sec": "打开 SEC 原文 ↗",
                "filing.source_note": "SEC 原文保持申报语言，便于逐字核验引用。",
                "reaction.title": "披露后发生了什么",
                "reaction.observed": "仅为观测，不作归因",
                "reaction.company_move": "公司股价变化",
                "reaction.open_close": "开盘到收盘",
                "reaction.after_benchmark": "扣除 {benchmark} 后",
                "reaction.compared": "与历史披露相比",
                "reaction.unavailable": "市场反应暂不可测量",
                "reaction.missing_bars": "首个符合规则的交易日缺少公司或基准行情数据。",
                "reaction.boundary": (
                    "这是 SEC 接收披露后第一个符合规则的交易日。它描述随后发生的情况，"
                    "并不声称股价变化由该披露造成。"
                ),
                "comparison.title": "与上一份同类披露相比的变化",
                "comparison.prior": "上一份披露 ↗",
                "comparison.unavailable": "暂无上一份同类披露可比较",
                "comparison.no_prior": "本地公司历史中没有相同表单和主要事件类型的更早披露。",
                "comparison.no_change": "未发现实质性措辞变化",
                "comparison.no_change_note": (
                    "日期和财季顺延会被视为常规更新；引用的附件仍可能包含缓存主文档之外的细节。"
                ),
                "context.eyebrow": "公司相关信息",
                "context.title": "近期公司报道",
                "context.intro": "这里只显示与当前股票明确匹配的标题；它们提供背景，但不参与回报或披露反应计算。",
                "context.refreshed": "更新时间",
                "context.read_source": "阅读来源 ↗",
                "context.status_available": "可用",
                "context.status_empty": "暂无内容",
                "context.status_stale": "缓存已过期",
                "context.status_not_configured": "未配置",
                "citation.metric": "计算指标",
                "citation.source": "来源段落",
                "footer.tagline": "先理解证据，再形成自己的判断。",
                "footer.how": "如何阅读 Company Lens",
                "performance.relative": "本期相对 {benchmark}：{value}",
                "performance.benchmark_ending": "{benchmark} 期末价值",
                "performance.not_available": "暂无数据",
                "performance.not_recovered": "在所选期间内尚未收复",
                "performance.recovered": "在 {sessions} 个交易日后收复",
                "performance.risk_title": "实际经历的风险",
                "performance.risk_copy": (
                    "最大跌幅为 {asset}，同期 {benchmark} 为 {benchmark_drawdown}；最低点出现在 "
                    "{date}，此后{recovery}。"
                ),
                "ask.models_ready": "已有 {count} 个通过校验的模型可用",
                "ask.models_unavailable": "实时模型暂不可用",
                "ask.offline": "页面证据仍可查看；实时问答目前离线。",
                "ask.reading": "正在读取受限证据包…",
                "ask.waiting": "正在等待所选模型…",
                "ask.answer_failed": "暂时无法生成答案。",
                "ask.selected_unavailable": "所选模型暂不可用。",
                "ask.withheld": "未展示任何未经校验的答案。",
                "ask.validated_answer": "已验证答案",
                "ask.evidence_through": "证据截至 {date}",
                "ask.limitations": "这个答案无法证明什么",
            },
        },
        ensure_ascii=False,
    )
    return f"""
const periods = JSON.parse(document.getElementById('period-data').textContent);
const ticker = {json.dumps(ticker)};
const benchmark = {json.dumps(benchmark)};
const translations = {translations};
const svg = document.getElementById('growth-chart');
const assetPath = document.getElementById('asset-path');
const benchmarkPath = document.getElementById('benchmark-path');
const hoverLine = document.getElementById('hover-line');
const assetPoint = document.getElementById('asset-point');
const benchmarkPoint = document.getElementById('benchmark-point');
const tooltip = document.getElementById('chart-tooltip');
let currentGrowth = [];
let chartScale = null;
let currentPeriod = {json.dumps(default_period)};
let uiLanguage = 'en';

function tr(key, values={{}}) {{
  const template = (translations[uiLanguage] || translations.en)[key] || translations.en[key] || key;
  return Object.entries(values).reduce(
    (copy, [name, value]) => copy.replaceAll(`{{${{name}}}}`, String(value)),
    template,
  );
}}

function storedLanguage() {{
  try {{ return window.localStorage.getItem('company-lens-language'); }} catch (error) {{ return null; }}
}}

function applyLanguage(language, persist=true) {{
  uiLanguage = language === 'zh' ? 'zh' : 'en';
  document.documentElement.lang = uiLanguage === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-i18n]').forEach(element => {{
    element.textContent = tr(element.dataset.i18n, {{ticker, benchmark}});
  }});
  document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {{
    element.placeholder = tr(element.dataset.i18nPlaceholder, {{ticker, benchmark}});
  }});
  document.querySelectorAll('[data-i18n-title]').forEach(element => {{
    element.title = tr(element.dataset.i18nTitle, {{ticker, benchmark}});
  }});
  document.querySelectorAll('[data-freshness-key]').forEach(element => {{
    const date = element.dataset.freshnessDate;
    element.textContent = `${{tr(element.dataset.freshnessKey)}}${{date ? ` ${{date}}` : ''}}`;
  }});
  const modeBadge = document.querySelector('[data-explanation-mode]');
  const modeKey = modeBadge.dataset.explanationMode === 'grounded_llm'
    ? 'mode.grounded'
    : modeBadge.dataset.explanationMode === 'deterministic_fallback'
      ? 'mode.fallback'
      : 'mode.unavailable';
  modeBadge.textContent = tr(modeKey);
  document.querySelectorAll('[data-question-en]').forEach(button => {{
    const raw = uiLanguage === 'zh' ? button.dataset.questionZh : button.dataset.questionEn;
    button.dataset.question = raw.replaceAll('{{ticker}}', ticker);
  }});
  const toggle = document.getElementById('language-toggle');
  toggle.textContent = uiLanguage === 'zh' ? 'EN' : '中文';
  toggle.setAttribute('aria-label', uiLanguage === 'zh' ? 'Switch to English' : '切换为中文');
  toggle.setAttribute('aria-pressed', String(uiLanguage === 'zh'));
  document.getElementById('ask-language').value = uiLanguage === 'zh' ? 'Chinese' : 'English';
  document.getElementById('benchmark-ending-label').textContent = tr(
    'performance.benchmark_ending', {{benchmark}},
  );
  refreshAskStatus();
  if (askModel.dataset.state === 'unavailable' && askModel.options.length) {{
    askModel.options[0].textContent = tr('ask.models_unavailable');
  }}
  if (persist) {{
    try {{ window.localStorage.setItem('company-lens-language', uiLanguage); }} catch (error) {{}}
  }}
  setPeriod(currentPeriod);
}}

const money = value => new Intl.NumberFormat('en-US', {{style:'currency',currency:'USD',maximumFractionDigits:0}}).format(value);
const pct = value => new Intl.NumberFormat('en-US', {{style:'percent',maximumFractionDigits:1,signDisplay:'exceptZero'}}).format(value);
const plainPct = value => new Intl.NumberFormat('en-US', {{style:'percent',maximumFractionDigits:1}}).format(value);
const decimal = value => value == null ? tr('performance.not_available') : value.toFixed(2);

function setPeriod(label) {{
  currentPeriod = label;
  const view = periods[label];
  const p = view.performance;
  document.querySelectorAll('.period-button').forEach(button => {{
    const active = button.dataset.period === label;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  }});
  document.getElementById('ending-value').textContent = money(p.ending_value);
  document.getElementById('benchmark-ending').textContent = money(p.initial_investment * (1 + p.benchmark.total_return));
  document.getElementById('relative-copy').textContent = tr('performance.relative', {{
    value: pct(p.relative_total_return), benchmark,
  }});
  document.getElementById('brief-period-label').textContent = label;
  document.getElementById('total-return').textContent = pct(p.asset.total_return);
  document.getElementById('cagr').textContent = pct(p.asset.cagr);
  document.getElementById('max-drawdown').textContent = plainPct(p.asset.max_drawdown);
  document.getElementById('volatility').textContent = plainPct(p.asset.annualized_volatility);
  document.getElementById('beta').textContent = decimal(p.beta);
  document.getElementById('correlation').textContent = decimal(p.correlation);
  document.getElementById('current-drawdown').textContent = plainPct(p.asset.current_drawdown);
  document.getElementById('worst-day').textContent = plainPct(p.asset.worst_day);
  const recovery = p.asset.recovery_sessions == null
    ? tr('performance.not_recovered')
    : tr('performance.recovered', {{sessions: p.asset.recovery_sessions}});
  const riskNote = document.getElementById('risk-note');
  riskNote.replaceChildren();
  const riskTitle = document.createElement('strong');
  riskTitle.textContent = tr('performance.risk_title');
  const riskCopy = document.createElement('span');
  riskCopy.textContent = tr('performance.risk_copy', {{
    asset: plainPct(p.asset.max_drawdown),
    benchmark_drawdown: plainPct(p.benchmark.max_drawdown),
    benchmark,
    date: p.asset.max_drawdown_date,
    recovery,
  }});
  riskNote.append(riskTitle, riskCopy);
  document.getElementById('chart-range').textContent = `${{view.period.start}} — ${{view.period.end}}`;
  drawChart(view.growth);
}}

function drawChart(growth) {{
  currentGrowth = growth;
  const left=58, right=896, top=22, bottom=316;
  const values = growth.flatMap(row => [row.asset_value,row.benchmark_value]);
  let min = Math.min(...values), max = Math.max(...values);
  const pad = Math.max((max-min)*0.12, 500); min=Math.max(0,min-pad); max+=pad;
  const x = index => left + (index / Math.max(growth.length-1,1)) * (right-left);
  const y = value => bottom - ((value-min)/(max-min))*(bottom-top);
  const path = key => growth.map((row,index) => `${{index?'L':'M'}}${{x(index).toFixed(1)}},${{y(row[key]).toFixed(1)}}`).join(' ');
  assetPath.setAttribute('d', path('asset_value'));
  benchmarkPath.setAttribute('d', path('benchmark_value'));
  const grid = [], labels=[];
  for(let i=0;i<5;i++){{ const value=min+(max-min)*i/4, yy=y(value); grid.push(`<line x1="${{left}}" x2="${{right}}" y1="${{yy}}" y2="${{yy}}"></line>`); labels.push(`<text x="${{left-10}}" y="${{yy+4}}" text-anchor="end">${{money(value)}}</text>`); }}
  labels.push(`<text x="${{left}}" y="344">${{growth[0].date}}</text><text x="${{right}}" y="344" text-anchor="end">${{growth[growth.length-1].date}}</text>`);
  document.getElementById('chart-grid').innerHTML=grid.join('');
  document.getElementById('chart-labels').innerHTML=labels.join('');
  chartScale={{left,right,top,bottom,x,y}};
  hideTooltip();
}}

function hideTooltip() {{ tooltip.classList.remove('visible'); hoverLine.style.opacity=0; assetPoint.style.opacity=0; benchmarkPoint.style.opacity=0; }}
svg.addEventListener('pointermove', event => {{
  if(!chartScale || !currentGrowth.length) return;
  const rect=svg.getBoundingClientRect(), svgX=(event.clientX-rect.left)*920/rect.width;
  const ratio=Math.max(0,Math.min(1,(svgX-chartScale.left)/(chartScale.right-chartScale.left)));
  const index=Math.round(ratio*(currentGrowth.length-1)), row=currentGrowth[index], xx=chartScale.x(index);
  hoverLine.setAttribute('x1',xx); hoverLine.setAttribute('x2',xx); hoverLine.style.opacity=1;
  assetPoint.setAttribute('cx',xx); assetPoint.setAttribute('cy',chartScale.y(row.asset_value)); assetPoint.style.opacity=1;
  benchmarkPoint.setAttribute('cx',xx); benchmarkPoint.setAttribute('cy',chartScale.y(row.benchmark_value)); benchmarkPoint.style.opacity=1;
  tooltip.innerHTML=`<b>${{row.date}}</b><span>${{ticker}} ${{money(row.asset_value)}}</span><span>${{benchmark}} ${{money(row.benchmark_value)}}</span>`;
  tooltip.style.left=`${{Math.min(Math.max(event.clientX-rect.left,90),rect.width-90)}}px`; tooltip.classList.add('visible');
}});
svg.addEventListener('pointerleave', hideTooltip);
document.querySelectorAll('.period-button').forEach(button => button.addEventListener('click',()=>setPeriod(button.dataset.period)));
setPeriod({json.dumps(default_period)});

const askForm = document.getElementById('ask-form');
const askModel = document.getElementById('ask-model');
const askLanguage = document.getElementById('ask-language');
const askQuestion = document.getElementById('ask-question');
const askSubmit = document.getElementById('ask-submit');
const askStatus = document.getElementById('ask-status');
const askResult = document.getElementById('ask-result');

function setAskStatus(message, state='') {{
  askStatus.textContent = message;
  askStatus.className = state;
  askStatus.dataset.statusKey = '';
  askStatus.dataset.statusValues = '';
}}

function setTranslatedAskStatus(key, values={{}}, state='') {{
  askStatus.dataset.statusKey = key;
  askStatus.dataset.statusValues = JSON.stringify(values);
  askStatus.textContent = tr(key, values);
  askStatus.className = state;
}}

function refreshAskStatus() {{
  const key = askStatus.dataset.statusKey;
  if (!key) return;
  let values = {{}};
  try {{ values = JSON.parse(askStatus.dataset.statusValues || '{{}}'); }} catch (error) {{}}
  askStatus.textContent = tr(key, values);
}}

async function loadAskModels() {{
  try {{
    const response = await fetch('/api/ask', {{headers: {{Accept: 'application/json'}}}});
    if (!response.ok) throw new Error(tr('ask.offline'));
    const payload = await response.json();
    askModel.replaceChildren();
    payload.models.forEach(model => {{
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = `${{model.provider}} · ${{model.model}}`;
      askModel.append(option);
    }});
    if (!payload.models.length) throw new Error(tr('ask.offline'));
    askModel.dataset.state = 'ready';
    askModel.disabled = false;
    askSubmit.disabled = false;
    setTranslatedAskStatus('ask.models_ready', {{
      count: payload.models.length,
      suffix: payload.models.length === 1 ? '' : 's',
    }}, 'ready');
  }} catch (error) {{
    askModel.replaceChildren();
    const option = document.createElement('option');
    option.textContent = tr('ask.models_unavailable');
    askModel.append(option);
    askModel.dataset.state = 'unavailable';
    setTranslatedAskStatus('ask.offline', {{}}, 'error');
  }}
}}

document.querySelectorAll('[data-question]').forEach(button => {{
  button.addEventListener('click', () => {{
    askQuestion.value = button.dataset.question;
    askQuestion.focus();
  }});
}});

askForm.addEventListener('submit', async event => {{
  event.preventDefault();
  const question = askQuestion.value.trim();
  if (!question || askModel.disabled) return;
  askSubmit.disabled = true;
  askResult.className = 'ask-result loading';
  askResult.textContent = tr('ask.reading');
  setTranslatedAskStatus('ask.waiting');
  try {{
    const response = await fetch('/api/ask', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json', Accept: 'application/json'}},
      body: JSON.stringify({{
        ticker,
        provider: askModel.value,
        language: askLanguage.value,
        depth: 'beginner',
        question,
      }}),
    }});
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || tr('ask.answer_failed'));
    renderAskAnswer(payload);
    setAskStatus(`${{payload.meta.model}} · ${{payload.meta.latency_ms}} ms · validator passed`, 'ready');
  }} catch (error) {{
    askResult.className = 'ask-result error';
    askResult.textContent = error.message || tr('ask.selected_unavailable');
    setTranslatedAskStatus('ask.withheld', {{}}, 'error');
  }} finally {{
    askSubmit.disabled = askModel.disabled;
  }}
}});

function renderAskAnswer(payload) {{
  askResult.replaceChildren();
  askResult.className = 'ask-result answered';
  const heading = document.createElement('div');
  heading.className = 'ask-answer-heading';
  const label = document.createElement('span');
  label.textContent = tr('ask.validated_answer');
  const model = document.createElement('small');
  model.textContent = `${{payload.meta.provider}} · ${{tr('ask.evidence_through', {{date: payload.meta.evidence_as_of}})}}`;
  heading.append(label, model);
  askResult.append(heading);
  payload.answer.forEach(claim => askResult.append(renderAskClaim(claim)));
  const details = document.createElement('details');
  details.className = 'ask-limitations';
  const summary = document.createElement('summary');
  summary.textContent = tr('ask.limitations');
  details.append(summary);
  payload.boundaries.forEach(claim => details.append(renderAskClaim(claim)));
  askResult.append(details);
}}

function renderAskClaim(claim) {{
  const article = document.createElement('article');
  const copy = document.createElement('p');
  copy.textContent = claim.text;
  article.append(copy);
  if (claim.citations.length) {{
    const links = document.createElement('div');
    links.className = 'ask-citations';
    claim.citations.forEach(citation => {{
      const link = document.createElement('a');
      link.href = safeAskHref(citation.url);
      link.textContent = citation.label;
      if (link.href.startsWith('http')) {{
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
      }}
      links.append(link);
    }});
    article.append(links);
  }}
  return article;
}}

function safeAskHref(value) {{
  try {{
    const url = new URL(value, window.location.origin);
    if (url.protocol === 'https:' || (url.protocol === 'http:' && url.origin === window.location.origin)) {{
      return url.href;
    }}
  }} catch (error) {{}}
  return '#ask';
}}

const workspaceViews = Array.from(document.querySelectorAll('[data-workspace-view]'));
const workspaceLinks = Array.from(
  document.querySelectorAll('[data-view-target], .section-nav a[href^="#"]'),
);
const workspaceTarget = link => link.dataset.viewTarget || link.getAttribute('href').slice(1);

function activateWorkspace(view, updateHash=false, scroll=false) {{
  const target = workspaceViews.find(panel => panel.dataset.workspaceView === view);
  if (!target) return false;
  document.documentElement.classList.add('workspace-enhanced');
  workspaceViews.forEach(panel => {{
    const active = panel === target;
    panel.classList.toggle('workspace-active', active);
    panel.toggleAttribute('hidden', !active);
  }});
  workspaceLinks.forEach(link => {{
    const active = workspaceTarget(link) === view;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }});
  if (updateHash) history.pushState(null, '', `#${{view}}`);
  if (scroll) document.getElementById('workspace').scrollIntoView({{block: 'start'}});
  return true;
}}

workspaceLinks.forEach(link => link.addEventListener('click', event => {{
  event.preventDefault();
  activateWorkspace(workspaceTarget(link), true, true);
}}));
window.addEventListener('hashchange', () => {{
  const view = window.location.hash.slice(1);
  if (view) activateWorkspace(view);
}});
const requestedView = window.location.hash.slice(1);
activateWorkspace(requestedView || 'brief');

document.getElementById('language-toggle').addEventListener('click', () => {{
  applyLanguage(uiLanguage === 'en' ? 'zh' : 'en');
}});

applyLanguage(storedLanguage() === 'zh' ? 'zh' : 'en', false);
loadAskModels();
"""


def _index_script() -> str:
    return """
const companies = JSON.parse(document.getElementById('company-data').textContent);
const form = document.getElementById('company-search');
const input = document.getElementById('ticker-search');
const status = document.getElementById('search-status');
const directoryGrid = document.getElementById('directory-grid');
const directoryStatus = document.getElementById('directory-status');
const directoryPrevious = document.getElementById('directory-previous');
const directoryNext = document.getElementById('directory-next');
const directoryCompanies = [...companies].sort((left, right) => left.ticker.localeCompare(right.ticker));
const directoryPageSize = 9;
let directoryPage = 0;
const normalize = value => value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
const indexTranslations = {
  en: {
    'nav.scope': '{count}-company evidence universe',
    'hero.eyebrow': 'SOURCE-BACKED COMPANY INTELLIGENCE',
    'hero.title': 'Understand the company.',
    'hero.emphasis': 'Keep the evidence.',
    'hero.lede': 'Historical return and risk, recent SEC disclosures, and a bounded AI explanation with citations. No price prediction. No investment recommendation.',
    'search.label': 'Search {count} locally available companies',
    'search.placeholder': 'Try AAPL or Apple',
    'search.submit': 'Open lens',
    'search.hint': 'Type an exact ticker or company name from the current local universe.',
    'search.scope': '{count} companies are available from the current local evidence set.',
    'search.multiple': 'More than one local company matched. Enter the exact ticker.',
    'search.missing': 'Not in the current local {count}-company universe.',
    'featured': 'Featured examples',
    'card.open': 'Open company lens →',
    'directory.eyebrow': 'LOCAL DIRECTORY',
    'directory.title': 'Browse without a long page',
    'directory.expand': 'Open paginated directory',
    'directory.previous': 'Previous',
    'directory.next': 'Next',
    'directory.page': 'Page {page} of {pages} · {count} cached companies',
    'method.eyebrow': 'HOW TO READ A LENS',
    'method.title': 'Company first. Evidence second.',
    'method.expand': 'Open the 3-step guide',
    'method.intro': 'Every page follows one order: historical picture, latest SEC disclosure, then company-specific context. Broad market headlines and implementation details stay off the company page so they cannot be mistaken for company evidence.',
    'method.history': 'History',
    'method.history_copy': 'Price and risk versus SPY',
    'method.disclosure': 'Disclosure',
    'method.disclosure_copy': 'What the latest 8-K actually says',
    'method.boundary': 'Boundary',
    'method.boundary_copy': 'Citations, limitations, no forecast',
    'method.tech': 'Under the hood: point-in-time SEC ingestion, return and risk calculations, deterministic NLP change filtering, and an optional source-bounded LLM explanation layer.',
    'footer': 'Cached real-data demonstration · SEC EDGAR + vendor-adjusted daily prices',
  },
  zh: {
    'nav.scope': '覆盖 {count} 家公司的证据范围',
    'hero.eyebrow': '基于来源的公司研究',
    'hero.title': '理解一家公司。',
    'hero.emphasis': '保留每条证据。',
    'hero.lede': '集中查看历史回报与风险、近期 SEC 披露，以及带引用的受控 AI 解释。不预测股价，不提供投资建议。',
    'search.label': '搜索本地已有的 {count} 家公司',
    'search.placeholder': '输入 AAPL 或 Apple',
    'search.submit': '打开公司页',
    'search.hint': '请输入当前本地范围内的准确股票代码或公司名称。',
    'search.scope': '当前本地证据集包含 {count} 家公司。',
    'search.multiple': '匹配到多家公司，请输入准确股票代码。',
    'search.missing': '不在当前本地 {count} 家公司的范围内。',
    'featured': '示例公司',
    'card.open': '打开 Company Lens →',
    'directory.eyebrow': '本地公司目录',
    'directory.title': '分页浏览，避免拉成长页',
    'directory.expand': '打开分页公司目录',
    'directory.previous': '上一页',
    'directory.next': '下一页',
    'directory.page': '第 {page} / {pages} 页 · 共 {count} 家缓存公司',
    'method.eyebrow': '如何阅读公司页',
    'method.title': '先看公司，再核验证据。',
    'method.expand': '展开三步阅读指南',
    'method.intro': '每个公司页按同一顺序呈现：长期历史表现、最新 SEC 披露、公司相关信息。宽泛市场新闻和实现细节不会混入公司证据。',
    'method.history': '历史表现',
    'method.history_copy': '价格与风险对比 SPY',
    'method.disclosure': '公司披露',
    'method.disclosure_copy': '最新 8-K 实际说了什么',
    'method.boundary': '证据边界',
    'method.boundary_copy': '引用、局限与不预测原则',
    'method.tech': '技术基础：时点正确的 SEC 数据摄取、回报与风险计算、确定性 NLP 变化过滤，以及可选的来源受限 LLM 解释层。',
    'footer': '真实缓存数据演示 · SEC EDGAR + 供应商复权日线价格',
  },
};
let indexLanguage = 'en';
const indexTr = (key, values={}) => Object.entries(values).reduce(
  (copy, [name, value]) => copy.replaceAll(`{${name}}`, String(value)),
  indexTranslations[indexLanguage][key] || indexTranslations.en[key] || key,
);

function setSearchStatus(key, values={}, error=false) {
  status.dataset.statusKey = key;
  status.dataset.statusValues = JSON.stringify(values);
  status.classList.toggle('error', error);
  refreshSearchStatus();
}

function refreshSearchStatus() {
  let values = {};
  try { values = JSON.parse(status.dataset.statusValues || '{}'); } catch (error) {}
  status.textContent = indexTr(
    status.dataset.statusKey || 'search.scope',
    {count: companies.length, ...values},
  );
}

function renderDirectory() {
  const pages = Math.max(1, Math.ceil(directoryCompanies.length / directoryPageSize));
  directoryPage = Math.min(Math.max(directoryPage, 0), pages - 1);
  const start = directoryPage * directoryPageSize;
  directoryGrid.replaceChildren();
  directoryCompanies.slice(start, start + directoryPageSize).forEach(company => {
    const link = document.createElement('a');
    link.className = 'directory-link';
    link.href = `${encodeURIComponent(company.ticker.toLowerCase())}.html`;
    const tickerLabel = document.createElement('strong');
    tickerLabel.textContent = company.ticker;
    const name = document.createElement('span');
    name.textContent = company.name;
    const action = document.createElement('small');
    action.textContent = indexTr('card.open');
    link.append(tickerLabel, name, action);
    directoryGrid.append(link);
  });
  directoryStatus.textContent = indexTr('directory.page', {
    page: directoryPage + 1,
    pages,
    count: directoryCompanies.length,
  });
  directoryPrevious.disabled = directoryPage === 0;
  directoryNext.disabled = directoryPage >= pages - 1;
}

function applyIndexLanguage(language, persist=true) {
  indexLanguage = language === 'zh' ? 'zh' : 'en';
  document.documentElement.lang = indexLanguage === 'zh' ? 'zh-CN' : 'en';
  document.querySelectorAll('[data-index-i18n]').forEach(element => {
    element.textContent = indexTr(element.dataset.indexI18n, {count: companies.length});
  });
  document.querySelectorAll('[data-index-i18n-placeholder]').forEach(element => {
    element.placeholder = indexTr(element.dataset.indexI18nPlaceholder, {count: companies.length});
  });
  const toggle = document.getElementById('index-language-toggle');
  toggle.textContent = indexLanguage === 'zh' ? 'EN' : '中文';
  toggle.setAttribute('aria-label', indexLanguage === 'zh' ? 'Switch to English' : '切换为中文');
  toggle.setAttribute('aria-pressed', String(indexLanguage === 'zh'));
  refreshSearchStatus();
  renderDirectory();
  if (persist) {
    try { localStorage.setItem('company-lens-language', indexLanguage); } catch (error) {}
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const query = normalize(input.value);
  const exactTicker = companies.find(company => normalize(company.ticker) === query);
  const exactName = companies.find(company => normalize(company.name) === query);
  const partialMatches = companies.filter(company => normalize(company.name).includes(query));
  const match = exactTicker || exactName || (partialMatches.length === 1 ? partialMatches[0] : null);
  if (match) {
    window.location.href = `${match.ticker.toLowerCase()}.html`;
    return;
  }
  setSearchStatus(
    partialMatches.length ? 'search.multiple' : 'search.missing',
    {count: companies.length},
    true,
  );
});

input.addEventListener('input', () => {
  setSearchStatus('search.scope', {count: companies.length});
});

directoryPrevious.addEventListener('click', () => {
  directoryPage -= 1;
  renderDirectory();
});
directoryNext.addEventListener('click', () => {
  directoryPage += 1;
  renderDirectory();
});

document.getElementById('index-language-toggle').addEventListener('click', () => {
  applyIndexLanguage(indexLanguage === 'en' ? 'zh' : 'en');
});
let savedIndexLanguage = null;
try { savedIndexLanguage = localStorage.getItem('company-lens-language'); } catch (error) {}
applyIndexLanguage(savedIndexLanguage === 'zh' ? 'zh' : 'en', false);
"""


def _css() -> str:
    return """
:root{--paper:#f4f3ef;--panel:#fff;--ink:#12202b;--muted:#65727b;--line:#d9dedf;--blue:#2864dc;--blue-soft:#edf3ff;--green:#14765d;--green-soft:#eaf6f0;--amber:#a96418;--amber-soft:#fff5e8;--navy:#0d2538;--shadow:0 18px 50px rgba(24,42,53,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16px;line-height:1.55}.topbar{height:70px;padding:0 max(28px,calc((100vw - 1240px)/2));display:flex;align-items:center;border-bottom:1px solid var(--line);background:rgba(244,243,239,.94);position:sticky;top:0;z-index:20;backdrop-filter:blur(16px)}.brand{display:flex;align-items:center;gap:10px;color:var(--navy);font-weight:760;text-decoration:none;letter-spacing:-.02em}.brand-mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--navy);color:white;font-size:11px;letter-spacing:.04em}.topbar nav{display:flex;align-items:center;margin-left:55px;gap:8px}.company-search-link{padding:7px 10px;border-radius:8px;color:var(--muted);font-size:12px;font-weight:700;text-decoration:none}.company-search-link:hover{background:var(--panel);color:var(--ink)}.current-symbol{padding:5px 8px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink);font-size:11px;font-weight:800;letter-spacing:.06em}.trust-label{margin-left:auto;color:var(--green);font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.08em}.language-toggle{margin-left:14px;padding:6px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--ink);font:750 11px/1.2 "Avenir Next","Segoe UI",sans-serif;cursor:pointer}.language-toggle:hover{border-color:#aebbc0;color:var(--blue)}.language-toggle:focus-visible{outline:3px solid rgba(40,100,220,.18);outline-offset:2px}main{max-width:1240px;margin:auto;padding:30px 28px 90px}.scope-warning{padding:11px 15px;border:1px solid #ead2ad;border-radius:10px;background:var(--amber-soft);display:flex;gap:15px;font-size:12px;color:#775020}.scope-warning strong{text-transform:uppercase;letter-spacing:.08em}.company-hero{display:flex;justify-content:space-between;align-items:end;padding:65px 0 48px}.eyebrow{margin:0 0 10px;color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.13em}.company-title{display:flex;align-items:center;gap:16px}.company-title h1{margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(40px,5vw,68px);font-weight:500;line-height:1.05;letter-spacing:-.045em}.company-title>span{padding:7px 10px;background:var(--navy);border-radius:8px;color:#fff;font-size:13px;font-weight:800;letter-spacing:.06em}.hero-copy{max-width:650px;margin:17px 0 0;color:var(--muted);font-size:18px}.market-observation{min-width:220px;padding-left:25px;border-left:1px solid var(--line);display:flex;flex-direction:column;align-items:flex-end}.market-observation span,.ending-card>span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.market-observation strong{font-family:Georgia,serif;font-size:38px;font-weight:500}.market-observation small{color:var(--muted)}section{margin-bottom:28px;padding:38px;border:1px solid var(--line);border-radius:20px;background:var(--panel);box-shadow:0 1px 0 rgba(255,255,255,.6)}.section-heading{display:flex;align-items:start;justify-content:space-between;gap:24px}.section-heading h2,.trust-section h2{margin:0;font-family:Georgia,serif;font-size:34px;font-weight:500;letter-spacing:-.025em}.mode-badge,.freshness{padding:7px 10px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}.brief-section{background:var(--navy);color:#fff;border-color:var(--navy);box-shadow:var(--shadow)}.brief-section .eyebrow{color:#78a7ff}.brief-section .mode-badge{border-color:#365166;color:#aebfca}.brief-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin-top:28px;background:#365166;border:1px solid #365166;border-radius:14px;overflow:hidden}.brief-card{min-height:190px;padding:25px;background:#122d41}.brief-card>span{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.1em}.brief-card.observed>span{color:#80aaff}.brief-card.calculated>span{color:#5fd0aa}.brief-card.interpreted>span{color:#e9b66d}.brief-card p{font-family:Georgia,serif;font-size:20px;line-height:1.45}.claim-links{display:flex;gap:8px}.claim-links a{font-size:11px;color:#d9e6ee;text-decoration:none;border-bottom:1px solid #6e8290}.authority-row{display:flex;gap:25px;margin-top:22px;color:#aebfca;font-size:11px}.authority-row span{display:flex;align-items:center;gap:7px}.dot{width:7px;height:7px;border-radius:50%}.dot.observed{background:#80aaff}.dot.calculated{background:#5fd0aa}.dot.interpreted{background:#e9b66d}.performance-section{padding-bottom:30px}.performance-heading{align-items:center}.period-control{display:flex;padding:4px;background:var(--paper);border-radius:10px}.period-button{border:0;background:transparent;padding:7px 13px;border-radius:7px;color:var(--muted);font-weight:750;cursor:pointer}.period-button:hover{color:var(--ink)}.period-button.active{background:var(--panel);color:var(--blue);box-shadow:0 2px 8px rgba(20,40,55,.08)}.section-intro{max-width:730px;margin:10px 0 28px;color:var(--muted)}.performance-layout{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:18px}.chart-panel{position:relative;border:1px solid var(--line);border-radius:14px;padding:18px;background:#fbfcfc}.chart-legend{height:25px;display:flex;align-items:center;gap:18px;color:var(--muted);font-size:11px}.chart-legend span:last-child{margin-left:auto}.line{display:inline-block;width:18px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}.line.asset{background:var(--blue)}.line.benchmark{background:#8a969e}#growth-chart{display:block;width:100%;overflow:visible}#growth-chart path{fill:none;stroke-linecap:round;stroke-linejoin:round}#asset-path{stroke:var(--blue);stroke-width:3}#benchmark-path{stroke:#99a4ab;stroke-width:2}#chart-grid line{stroke:#e6eaeb;stroke-width:1}#chart-labels text{font-size:10px;fill:#7c888f}#hover-line{stroke:#91a0a8;stroke-dasharray:3 3;opacity:0;pointer-events:none}#asset-point{fill:var(--blue);stroke:white;stroke-width:2;opacity:0}#benchmark-point{fill:#89969e;stroke:white;stroke-width:2;opacity:0}.chart-hit{fill:transparent;cursor:crosshair}.chart-tooltip{position:absolute;top:72px;transform:translateX(-50%);display:none;min-width:155px;padding:10px 12px;background:var(--navy);color:#fff;border-radius:9px;box-shadow:var(--shadow);pointer-events:none;font-size:11px}.chart-tooltip.visible{display:flex;flex-direction:column}.chart-tooltip b{margin-bottom:4px}.ending-card{padding:24px;background:var(--blue-soft);border-radius:14px;display:flex;flex-direction:column}.ending-card>strong{margin:8px 0 2px;font-family:Georgia,serif;font-size:34px;font-weight:500;color:#173f91}.ending-card>small{color:#4d6d9f}.mini-comparison{margin-top:auto;padding-top:18px;border-top:1px solid #cfdbf3;display:flex;flex-direction:column;color:#4d6d9f;font-size:11px}.mini-comparison b{font-size:17px;color:#173f91}.metric-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:18px}.metric-card{padding:16px;border:1px solid var(--line);border-radius:12px}.metric-card>span{display:flex;justify-content:space-between;min-height:36px;color:var(--muted);font-size:11px;font-weight:700}.metric-card i{display:grid;place-items:center;width:17px;height:17px;border:1px solid var(--line);border-radius:50%;font-style:normal}.metric-card strong{display:block;font-family:Georgia,serif;font-size:25px;font-weight:500}.metric-card small{display:none}.risk-note{display:flex;gap:20px;margin-top:18px;padding:15px 18px;border-left:3px solid var(--amber);background:var(--amber-soft);color:#664b2e;font-size:13px}.risk-note strong{min-width:130px}.filing-list{display:flex;flex-direction:column;gap:10px}.filing-card{border:1px solid var(--line);border-radius:14px;overflow:hidden}.filing-card summary{list-style:none;padding:18px 20px;display:flex;align-items:center;justify-content:space-between;cursor:pointer}.filing-card summary::-webkit-details-marker{display:none}.filing-card summary>div:first-child{display:grid;grid-template-columns:auto 1fr;gap:2px 11px;align-items:center}.filing-card summary strong{font-size:15px}.filing-card summary small{grid-column:2;color:var(--muted)}.filing-form{grid-row:1/3;padding:7px 9px;background:var(--green-soft);color:var(--green);border-radius:8px;font-weight:800}.filing-summary-meta{display:flex;align-items:center;gap:18px;color:var(--muted);font-size:12px}.filing-summary-meta i{font-size:18px;transition:transform .2s}.filing-card[open] .filing-summary-meta i{transform:rotate(180deg)}.filing-body{padding:0 20px 22px;border-top:1px solid var(--line);background:#fbfcfc}.filing-items{display:flex;flex-wrap:wrap;gap:7px;padding:16px 0}.item-chip,.number-chip{padding:5px 8px;border-radius:7px;background:var(--paper);color:var(--muted);font-size:11px;text-decoration:none}.number-chip{background:var(--blue-soft);color:#2855a7;font-weight:750}.filing-columns{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:30px}.filing-columns h3{margin:16px 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em}.number-list{display:flex;flex-wrap:wrap;gap:6px}.passages{display:flex;flex-direction:column;gap:8px}blockquote{margin:0;padding:14px 16px;border-left:2px solid #9db8ed;background:#fff}blockquote p{margin:0 0 7px;font-family:Georgia,serif;font-size:15px}blockquote a,.filing-columns aside a{color:var(--blue);font-size:10px;text-decoration:none}.filing-columns aside{padding:16px;border-radius:10px;background:var(--paper);display:flex;flex-direction:column;align-items:start;gap:8px;font-size:11px;color:var(--muted)}.filing-columns aside>span{text-transform:uppercase;letter-spacing:.08em}.filing-columns aside code{word-break:break-all;color:var(--ink)}.missing,.empty{color:var(--muted);font-size:12px;font-style:italic}.trust-section{background:#e9ece9}.trust-section>.eyebrow{color:var(--green)}.trust-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:28px}.trust-grid article{padding:20px;background:rgba(255,255,255,.6);border-radius:12px}.trust-grid article>span{font-family:Georgia,serif;color:var(--green);font-size:24px}.trust-grid h3{margin:8px 0 4px}.trust-grid p{margin:0;color:var(--muted);font-size:13px}footer{max-width:1240px;margin:auto;padding:28px;display:flex;justify-content:space-between;border-top:1px solid var(--line);color:var(--muted);font-size:12px}footer>div:first-child{display:flex;flex-direction:column}.footer-meta{display:flex;gap:20px}
.freshness-group{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px}.entity-chip{display:inline-flex;align-items:center;gap:6px}.entity-chip small{padding-right:6px;border-right:1px solid #b9c9e8;color:#60749a;font-size:8px;text-transform:uppercase;letter-spacing:.05em}.entity-mark{padding:1px 3px;border-radius:3px;background:#e8efff;color:inherit}.entity-mark.percentage{background:#e7f5ee}.entity-mark.date{background:#fff0da}.reaction-panel{margin:0 0 14px;padding:18px;border:1px solid #cfe0d8;border-radius:12px;background:#f3f8f5}.reaction-heading{display:flex;justify-content:space-between;gap:20px}.reaction-heading>div{display:flex;flex-direction:column}.reaction-heading span{color:var(--green);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.reaction-heading strong{font-size:13px}.reaction-heading>small{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}.reaction-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:13px}.reaction-grid>div{padding:12px;border:1px solid #dbe8e1;border-radius:9px;background:#fff;display:flex;flex-direction:column}.reaction-grid span{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.07em}.reaction-grid strong{margin:3px 0;font-family:Georgia,serif;font-size:19px;font-weight:500}.reaction-grid small,.reaction-panel>p{color:var(--muted);font-size:10px}.reaction-panel>p{margin:12px 0 0}.reaction-empty{display:flex;flex-direction:column;margin:0 0 14px;padding:13px 15px;border:1px dashed #cfe0d8;border-radius:10px;color:var(--muted);font-size:11px}.reaction-empty strong{color:var(--ink)}.comparison-panel{margin:0 0 22px;padding:18px;border:1px solid #cddbed;border-radius:12px;background:#f5f8fd}.comparison-heading{display:flex;justify-content:space-between;gap:20px}.comparison-heading>div{display:flex;flex-direction:column}.comparison-heading span{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}.comparison-heading strong{font-size:13px}.comparison-heading a,.change-quote a{color:var(--blue);font-size:10px;text-decoration:none}.change-counts{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}.change-count{padding:4px 7px;border-radius:999px;font-size:10px;font-weight:750}.change-count.changed{background:#fff1d8;color:#825616}.change-count.added{background:var(--green-soft);color:var(--green)}.change-count.removed{background:#f8e9e7;color:#98473e}.change-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}.change-card{padding:12px;border:1px solid var(--line);border-radius:9px;background:#fff}.change-card header{display:flex;justify-content:space-between;gap:10px}.change-card header>strong{font-size:11px;text-transform:uppercase;letter-spacing:.07em}.similarity{color:var(--muted);font-size:10px}.change-quote{margin-top:9px;padding-left:9px;border-left:2px solid #b9c8df}.change-quote>span{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.08em}.change-quote p{margin:2px 0 5px;font-family:Georgia,serif;font-size:13px;line-height:1.4}.comparison-empty{display:flex;flex-direction:column;margin:0 0 22px;padding:13px 15px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);font-size:11px}.comparison-empty strong{color:var(--ink)}.profile-category{margin:18px 0 0;color:var(--blue);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.09em}.hero-copy{margin-top:6px}.profile-meta{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:14px;color:var(--muted);font-size:11px}.profile-meta a{color:var(--blue);text-decoration:none;border-bottom:1px solid #aac0eb}.metric-grid{grid-template-columns:repeat(4,1fr)}
.timeline-panel{margin:0 0 20px;padding:18px;border:1px solid var(--line);border-radius:12px;background:#fbfcfc}.timeline-heading{display:flex;justify-content:space-between;gap:20px}.timeline-heading>div{display:flex;flex-direction:column}.timeline-heading span{color:var(--blue);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.timeline-heading strong{font-size:13px}.timeline-heading>small{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em}.timeline-track{position:relative;display:grid;grid-auto-flow:column;grid-auto-columns:minmax(155px,1fr);gap:8px;margin-top:16px;padding-top:14px;overflow-x:auto;scrollbar-width:thin}.timeline-track:before{content:"";position:absolute;top:20px;left:12px;right:12px;height:1px;background:var(--line)}.timeline-event{position:relative;min-height:145px;padding:20px 12px 12px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);text-decoration:none;display:flex;flex-direction:column}.timeline-event>i{position:absolute;top:-10px;left:14px;width:13px;height:13px;border:3px solid #fff;border-radius:50%;background:#8d989f;box-shadow:0 0 0 1px var(--line)}.timeline-event.positive>i{background:var(--green)}.timeline-event.negative>i{background:#a74e43}.timeline-event>span,.timeline-event>small{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.05em}.timeline-event>strong{margin:5px 0 2px;font-size:11px;line-height:1.35}.timeline-event>b{margin-top:auto;font-size:12px}.timeline-event>em{color:var(--muted);font-size:9px;font-style:normal}.timeline-panel>p{margin:11px 0 0;color:var(--muted);font-size:10px}
.topbar .section-nav{margin-left:auto;gap:3px}.section-nav a{padding:7px 9px;border-radius:7px;color:var(--muted);font-size:11px;font-weight:750;text-decoration:none}.section-nav a:hover{background:var(--panel);color:var(--blue)}.trust-label{margin-left:22px}.company-hero{padding:46px 0 34px}.evidence-flow{display:flex;align-items:center;gap:9px;margin-top:18px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.evidence-flow span{padding:5px 8px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.62)}.evidence-flow i{color:var(--blue);font-style:normal}.brief-section{background:linear-gradient(135deg,#0d2436 0%,#132f43 100%)}.brief-intro{max-width:680px;margin:9px 0 0;color:#aebfca;font-size:13px}.brief-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:10px;margin-top:26px;background:transparent;border:0;border-radius:0;overflow:visible}.brief-card{min-height:0;padding:24px;border:1px solid #365166;border-radius:13px;background:rgba(16,43,62,.82)}.brief-lead{grid-column:span 7;background:linear-gradient(145deg,#173a55,#122d41)}.brief-numbers{grid-column:span 5;background:#102f38}.brief-reading,.brief-limit{grid-column:span 6}.brief-limit{background:#302c2a;border-color:#5b4a3b}.brief-card>span,.brief-card-heading>span{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.11em}.brief-card.observed>span,.brief-card.observed .brief-card-heading>span{color:#80aaff}.brief-card.calculated>span{color:#5fd0aa}.brief-card.interpreted>span{color:#b7c9ff}.brief-card.guardrail>span{color:#e9b66d}.brief-card-heading{display:flex;justify-content:space-between;gap:18px}.brief-card-heading>a,.brief-numbers>a{color:#d9e6ee;font-size:10px;text-decoration:none;border-bottom:1px solid #6e8290}.brief-card h3{max-width:540px;margin:18px 0 7px;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.15}.brief-card p{margin:11px 0;font-family:Georgia,serif;font-size:17px;line-height:1.48}.brief-lead>p{font-size:19px}.brief-meta{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 8px}.brief-meta span{padding:5px 7px;border:1px solid #466177;border-radius:6px;color:#bacad4;font-size:9px}.brief-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:19px 0 14px}.brief-metrics>div{padding:14px;border:1px solid #28514e;border-radius:10px;background:rgba(9,33,37,.55)}.brief-metrics strong{display:block;font-family:Georgia,serif;font-size:31px;font-weight:500;color:#77ddb8}.brief-metrics small{color:#9bb9ae;font-size:9px;text-transform:uppercase;letter-spacing:.06em}.brief-numbers p{color:#b8c9c4;font-family:inherit;font-size:11px}.claim-links{flex-wrap:wrap}.authority-row{align-items:center}.authority-row span b{color:#fff;font-size:9px}.authority-row>em{color:#627786;font-style:normal}.diagnostic-heading{display:flex;justify-content:space-between;align-items:end;margin-top:22px;padding-top:17px;border-top:1px solid var(--line)}.diagnostic-heading span{font-size:12px;font-weight:800}.diagnostic-heading small{color:var(--muted);font-size:10px}.metric-grid{grid-template-columns:repeat(3,1fr);margin-top:10px}.metric-card{background:#fbfcfc;transition:border-color .18s,transform .18s}.metric-card:hover{border-color:#b9c9d8;transform:translateY(-1px)}.trust-grid article>b{display:block;margin-top:7px;color:var(--green);font-size:8px;letter-spacing:.1em}#brief,#performance,#filings,#context,#method{scroll-margin-top:90px}.section-nav a:focus-visible,.brief-card a:focus-visible,.headline-card a:focus-visible{outline:3px solid #80aaff;outline-offset:3px}
.workspace-switcher{position:sticky;top:70px;z-index:14;display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:28px;margin:0 0 28px;padding:12px 14px;border:1px solid var(--line);background:rgba(244,243,239,.96);backdrop-filter:blur(14px);box-shadow:0 10px 30px rgba(24,42,53,.06)}.workspace-switcher p{margin:0}.workspace-switcher>div:first-child{min-width:170px}.workspace-switcher>div:first-child strong{font:500 17px/1.2 Georgia,serif}.workspace-links{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(108px,1fr);gap:5px;overflow-x:auto}.workspace-links a{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:8px;padding:10px 11px;border:1px solid transparent;color:var(--muted);text-decoration:none}.workspace-links a span{color:#97a3aa;font-size:9px;font-weight:800}.workspace-links a b{font-size:11px}.workspace-links a:hover{border-color:var(--line);background:var(--panel);color:var(--blue)}.workspace-links a.active{border-color:var(--navy);background:var(--navy);color:#fff}.workspace-links a.active span{color:#87afff}.section-nav a.active{background:var(--panel);color:var(--blue)}[data-workspace-view][hidden]{display:none!important}#workspace{scroll-margin-top:82px}
.context-section{background:#f9faf8}.context-status{padding:7px 10px;border:1px solid var(--line);border-radius:999px;color:var(--green);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.context-status.stale{color:var(--amber);border-color:#e5c89e;background:var(--amber-soft)}.headline-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.headline-card{padding:17px;border:1px solid var(--line);border-radius:12px;background:#fff;display:flex;flex-direction:column;align-items:flex-start}.headline-card h3{margin:13px 0 11px;font:500 18px/1.35 Georgia,serif}.headline-meta{display:flex;flex-direction:column;color:var(--muted);font-size:10px}.headline-card>a{margin-top:auto;padding-top:15px;color:var(--blue);font-size:10px;font-weight:750;text-decoration:none}
@media(max-width:900px){.trust-label{display:none}.company-hero{align-items:start}.brief-grid,.trust-grid{grid-template-columns:1fr}.brief-card{min-height:auto}.performance-layout{grid-template-columns:1fr}.ending-card{min-height:190px}.metric-grid{grid-template-columns:repeat(3,1fr)}.filing-columns{grid-template-columns:1fr}.authority-row{flex-wrap:wrap}.section-nav{display:none}.brief-lead,.brief-numbers,.brief-reading,.brief-limit{grid-column:1}.brief-grid{gap:8px}.brief-metrics strong{font-size:28px}.headline-list{grid-template-columns:1fr}}
@media(max-width:620px){.topbar{padding:0 16px}.topbar nav{margin-left:auto}.company-search-link{padding:6px}.trust-label{display:none}.brand>span:last-child{display:none}main{padding:18px 14px 60px}.scope-warning{flex-direction:column;gap:2px}.company-hero{padding:42px 0 30px;flex-direction:column;gap:25px}.market-observation{align-items:start;border-left:0;padding-left:0}.company-title{align-items:start}.company-title h1{font-size:42px}section{padding:24px 18px}.section-heading{flex-direction:column}.performance-heading{align-items:start}.metric-grid{grid-template-columns:repeat(2,1fr)}.period-control{width:100%}.period-button{flex:1}.risk-note{flex-direction:column;gap:4px}.filing-card summary strong{max-width:190px}.filing-summary-meta>span{display:none}.footer-meta{display:none}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important}}
@media(max-width:620px){.profile-meta{flex-direction:column;align-items:flex-start;gap:3px}.timeline-heading,.reaction-heading,.comparison-heading{flex-direction:column;gap:6px}.reaction-grid,.change-list{grid-template-columns:1fr}.timeline-track{grid-auto-columns:minmax(145px,72vw)}.topbar .section-nav,.company-search-link{display:none}.topbar .company-nav{margin-left:auto}.company-hero{padding:24px 0 18px;gap:13px}.hero-copy{font-size:15px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.profile-meta>span{display:none}.profile-meta{margin-top:8px}.evidence-flow{display:none}.market-observation{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:12px;background:var(--panel);align-items:flex-start}.market-observation strong{font-size:29px}.brief-card{padding:19px}.brief-card h3{font-size:22px}.brief-card p,.brief-lead>p{font-size:16px}.brief-card-heading{flex-direction:column;gap:5px}.brief-metrics{grid-template-columns:1fr 1fr}.authority-row{gap:8px}.authority-row>em{display:none}.diagnostic-heading{align-items:start;flex-direction:column;gap:2px}.metric-grid{grid-template-columns:1fr 1fr}.metric-card{padding:13px}.trust-grid{gap:8px}}
body{font-family:"Avenir Next","Segoe UI",sans-serif}.company-hero{border:0;border-radius:0;background:transparent;box-shadow:none;margin-bottom:0}.brief-section{border-radius:8px}.brief-grid{grid-template-columns:repeat(12,minmax(0,1fr));gap:0;border-top:1px solid #365166;border-bottom:1px solid #365166}.brief-card{border:0;border-radius:0;background:transparent}.brief-lead{border-right:1px solid #365166}.brief-metrics>div{padding:10px 0;border:0;border-radius:0;background:transparent}.brief-metrics>div+div{padding-left:18px;border-left:1px solid #28514e}.brief-boundary{grid-column:1/-1;margin:0;padding:17px 24px;color:#aebfca;font-size:12px}.brief-boundary strong{color:#e9b66d}.performance-section,.filings-section,.context-section{padding:58px 0;border:0;border-top:1px solid var(--line);border-radius:0;background:transparent;box-shadow:none}.diagnostics-disclosure{margin-top:20px;border-top:1px solid var(--line)}.diagnostics-disclosure>summary,.source-details>summary{padding:14px 0;color:var(--blue);font-size:12px;font-weight:750;cursor:pointer}.metric-card{border-radius:3px;background:rgba(255,255,255,.55)}.filing-card{border-radius:4px;background:#fff}.filing-card summary{min-height:76px}.reaction-panel,.comparison-panel{border-width:0 0 0 3px;border-radius:0}.reaction-grid>div{border:0;border-left:1px solid #dbe8e1;border-radius:0;background:transparent}.reaction-grid>div:first-child{border-left:0}.comparison-clear{display:flex;flex-direction:column;margin-top:14px;color:var(--muted);font-size:12px}.comparison-clear strong{margin-bottom:3px;color:var(--ink)}.source-details{margin-top:8px;border-top:1px solid var(--line)}.filing-columns aside{border-radius:3px}.context-freshness{margin:-14px 0 20px;color:var(--muted);font-size:10px}.headline-list{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0;border-top:1px solid var(--line)}.headline-card{padding:20px 22px;border:0;border-right:1px solid var(--line);border-radius:0;background:transparent}.headline-card:last-child{border-right:0}.headline-card h3{margin:10px 0 14px}.headline-meta{display:flex;flex-direction:row;flex-wrap:wrap;gap:5px 12px}.headline-meta span:first-child{color:var(--ink);font-weight:750}.headline-card>a{padding-top:2px}footer a{margin-top:5px;color:var(--blue);text-decoration:none}#brief,#ask,#performance,#filings,#context{scroll-margin-top:90px}
.ask-section{padding:58px 0;border:0;border-top:1px solid var(--line);border-radius:0;background:transparent;box-shadow:none}.ask-validation{padding:7px 10px;border:1px solid #b9d8ca;border-radius:999px;color:var(--green);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.ask-layout{display:grid;grid-template-columns:minmax(0,5fr) minmax(320px,4fr);border:1px solid var(--line);background:var(--panel)}.ask-form{padding:28px;border-right:1px solid var(--line)}.ask-controls{display:grid;grid-template-columns:1fr 150px;gap:12px}.ask-form label{display:flex;flex-direction:column;gap:7px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.ask-form select,.ask-form textarea{width:100%;border:1px solid var(--line);border-radius:4px;background:#fff;color:var(--ink);font:500 14px/1.5 "Avenir Next","Segoe UI",sans-serif}.ask-form select{height:43px;padding:0 11px}.ask-form textarea{resize:vertical;min-height:90px;padding:12px}.ask-form select:focus,.ask-form textarea:focus{outline:3px solid rgba(40,100,220,.14);border-color:var(--blue)}.ask-question{margin-top:17px}.ask-suggestions{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}.ask-suggestions button{padding:6px 9px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--blue);font-size:10px;cursor:pointer}.ask-suggestions button:hover{background:var(--blue-soft)}.ask-submit-row{display:flex;align-items:center;gap:13px;margin-top:20px}.ask-submit-row>button{min-width:120px;padding:11px 16px;border:0;border-radius:4px;background:var(--navy);color:#fff;font-weight:800;cursor:pointer}.ask-submit-row>button:disabled{opacity:.45;cursor:not-allowed}.ask-submit-row>span{color:var(--muted);font-size:10px}.ask-submit-row>span.ready{color:var(--green)}.ask-submit-row>span.error{color:#98473e}.ask-result{min-height:330px;padding:28px;background:#f8faf8;color:var(--muted);font-size:13px}.ask-result-kicker,.ask-answer-heading>span{margin:0;color:var(--green);font-size:10px;font-weight:850;letter-spacing:.1em}.ask-result>ol{margin:18px 0 0;padding:0;list-style:none}.ask-result>ol li{display:grid;grid-template-columns:25px 1fr;gap:10px;padding:12px 0;border-top:1px solid var(--line)}.ask-result>ol li span{color:var(--green);font-weight:850}.ask-result.loading{display:grid;place-items:center}.ask-result.error{display:grid;place-items:center;color:#98473e}.ask-answer-heading{display:flex;justify-content:space-between;gap:15px;padding-bottom:12px;border-bottom:1px solid var(--line)}.ask-answer-heading small{color:var(--muted)}.ask-result article{padding:15px 0;border-bottom:1px solid var(--line)}.ask-result article p{margin:0;color:var(--ink);font:500 17px/1.45 Georgia,serif}.ask-citations{display:flex;flex-wrap:wrap;gap:7px;margin-top:9px}.ask-citations a{color:var(--blue);font-size:10px;text-decoration:none;border-bottom:1px solid #aec2e9}.ask-limitations{margin-top:15px}.ask-limitations>summary{color:var(--amber);font-size:11px;font-weight:800;cursor:pointer}.ask-limitations article p{font:inherit;color:var(--muted)}.ask-boundary{margin:14px 0 0;color:var(--muted);font-size:10px}.ask-boundary strong{color:var(--ink)}
@media(max-width:900px){.brief-lead{border-right:0;border-bottom:1px solid #365166}.headline-card{border-right:0;border-bottom:1px solid var(--line)}}
@media(max-width:900px){.ask-layout{grid-template-columns:1fr}.ask-form{border-right:0;border-bottom:1px solid var(--line)}}
@media(max-width:620px){.ask-section,.performance-section,.filings-section,.context-section{padding:40px 0}.ask-controls{grid-template-columns:1fr}.ask-form,.ask-result{padding:20px}.ask-submit-row{align-items:flex-start;flex-direction:column}.brief-section{border-radius:4px}.reaction-grid>div{padding-left:0;border-left:0;border-top:1px solid #dbe8e1}.reaction-grid>div:first-child{border-top:0}.filing-summary-meta span:first-child{display:block}.filing-summary-meta span:nth-child(2){display:none}}
@media(max-width:760px){.workspace-switcher{top:70px;display:block;margin-left:-14px;margin-right:-14px;padding:10px 14px;border-left:0;border-right:0}.workspace-switcher>div:first-child{display:none}.workspace-links{grid-auto-columns:minmax(95px,1fr)}.workspace-links a{padding:9px}.workspace-links a span{display:none}}
"""


def _index_css() -> str:
    return """
:root{--ink:#102537;--muted:#667681;--blue:#2864dc;--paper:#f3f2ed}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--paper);color:var(--ink);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{width:min(920px,calc(100% - 40px));padding:80px 0}.eyebrow{color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.14em}h1{margin:22px 0;font:500 clamp(48px,8vw,86px)/.98 Georgia,serif;letter-spacing:-.05em}h1 em{color:var(--blue);font-weight:500}.lede{max-width:660px;color:var(--muted);font-size:19px}.companies{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:55px}.company-link{padding:25px;border:1px solid #d7dcdd;border-radius:14px;background:#fff;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;transition:transform .2s,box-shadow .2s}.company-link:hover{transform:translateY(-3px);box-shadow:0 16px 40px rgba(20,38,52,.1)}.company-link span{font:500 30px Georgia,serif}.company-link small{margin-top:25px;color:var(--blue)}.foot{margin-top:30px;color:var(--muted);font-size:11px}@media(max-width:650px){main{padding:50px 0}.companies{grid-template-columns:1fr}.company-link{padding:18px}.company-link small{margin-top:8px}}
.company-search{max-width:660px;margin-top:34px}.company-search label{display:block;margin-bottom:8px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.search-row{display:grid;grid-template-columns:1fr auto;gap:8px}.search-row input{min-width:0;padding:15px 17px;border:1px solid #d7dcdd;border-radius:7px;background:#fff;color:var(--ink);font:inherit;outline:none}.search-row input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(40,100,220,.12)}.search-row button{padding:0 20px;border:0;border-radius:7px;background:var(--ink);color:#fff;font-weight:750;cursor:pointer}.search-status{margin:7px 2px 0;color:var(--muted);font-size:11px}.search-status.error{color:#a4432d}.featured-label{margin:30px 0 -25px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.1em}.companies{margin-top:35px}.company-link{padding:22px;border-radius:5px}.company-link strong{margin-top:3px;color:var(--muted);font-size:12px}.company-link small{margin-top:21px}.return-link{display:inline-block;margin-top:24px;color:var(--blue);font-weight:750;text-decoration:none}.method-note{margin-top:80px;padding:54px 0 0;border-top:1px solid #d7dcdd}.method-note h2{margin:8px 0 10px;font:500 38px/1.1 Georgia,serif;letter-spacing:-.025em}.method-note>p:not(.eyebrow){max-width:720px;color:var(--muted);font-size:16px}.method-note ol{margin:30px 0 0;padding:0;border-top:1px solid #d7dcdd;list-style:none}.method-note li{display:grid;grid-template-columns:44px 130px 1fr;gap:16px;padding:16px 0;border-bottom:1px solid #d7dcdd}.method-note li span{color:var(--blue);font-weight:800}.method-note li small{color:var(--muted)}.method-tech{padding-top:18px;font-size:13px!important}.method-tech strong{color:var(--ink)}body{display:block;font-family:"Avenir Next","Segoe UI",sans-serif}main{width:min(1040px,calc(100% - 40px))}@media(max-width:650px){.search-row{grid-template-columns:1fr}.search-row button{padding:14px}.method-note{margin-top:55px;padding-top:36px}.method-note li{grid-template-columns:36px 1fr}.method-note li small{grid-column:2}}
.index-language-toggle{float:right;margin-top:-34px;padding:7px 12px;border:1px solid #d7dcdd;border-radius:999px;background:#fff;color:var(--ink);font:750 11px/1.2 "Avenir Next","Segoe UI",sans-serif;cursor:pointer}.index-language-toggle:hover{border-color:#aebbc0;color:var(--blue)}.index-language-toggle:focus-visible{outline:3px solid rgba(40,100,220,.16);outline-offset:2px}
.index-topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:70px;padding-bottom:16px;border-bottom:1px solid #d7dcdd}.index-brand{display:flex;align-items:center;gap:10px;color:var(--ink);text-decoration:none}.index-brand>span{display:grid;place-items:center;width:32px;height:32px;border-radius:8px;background:var(--ink);color:#fff;font-size:10px;font-weight:850}.index-brand strong{font-size:13px}.index-topbar>div{display:flex;align-items:center;gap:14px}.index-topbar small{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}.index-language-toggle{float:none;margin:0}.index-hero{max-width:790px}.method-note{margin-top:56px;padding:0;border:1px solid #d7dcdd;background:rgba(255,255,255,.45)}.method-note>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:24px 26px;cursor:pointer}.method-note>summary::-webkit-details-marker{display:none}.method-note>summary .eyebrow{margin:0 0 5px}.method-note>summary h2{margin:0;font-size:28px}.method-note>summary>span{color:var(--blue);font-size:11px;font-weight:800}.method-note[open]>summary{border-bottom:1px solid #d7dcdd}.method-body{padding:24px 26px 28px}.method-body>p{max-width:720px;color:var(--muted);font-size:14px}.method-body ol{margin-top:22px}@media(max-width:650px){.index-topbar{margin-bottom:44px}.index-topbar small{display:none}.method-note>summary{align-items:flex-start;padding:20px;flex-direction:column;gap:8px}.method-note>summary h2{font-size:24px}.method-body{padding:20px}}
.company-directory{margin-top:56px;border:1px solid #d7dcdd;background:#fff}.company-directory>summary{list-style:none;display:flex;align-items:center;justify-content:space-between;gap:24px;padding:24px 26px;cursor:pointer}.company-directory>summary::-webkit-details-marker{display:none}.company-directory>summary .eyebrow{margin:0 0 5px}.company-directory>summary h2{margin:0;font:500 28px/1.1 Georgia,serif}.company-directory>summary>span{color:var(--blue);font-size:11px;font-weight:800}.company-directory[open]>summary{border-bottom:1px solid #d7dcdd}.directory-body{padding:22px 26px 26px}.directory-toolbar{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:16px}.directory-toolbar p{margin:0;color:var(--muted);font-size:11px}.directory-toolbar>div{display:flex;gap:6px}.directory-toolbar button{padding:7px 10px;border:1px solid #d7dcdd;background:#fff;color:var(--ink);font-size:10px;font-weight:750;cursor:pointer}.directory-toolbar button:disabled{opacity:.35;cursor:not-allowed}.directory-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border-top:1px solid #d7dcdd;border-left:1px solid #d7dcdd}.directory-link{min-width:0;padding:15px;border-right:1px solid #d7dcdd;border-bottom:1px solid #d7dcdd;color:var(--ink);text-decoration:none;display:grid;grid-template-columns:auto minmax(0,1fr);gap:2px 10px}.directory-link strong{font:500 18px Georgia,serif}.directory-link span{overflow:hidden;color:var(--muted);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.directory-link small{grid-column:1/-1;margin-top:8px;color:var(--blue);font-size:9px}.directory-link:hover{background:#f7f9ff}@media(max-width:650px){.company-directory{margin-top:38px}.company-directory>summary{align-items:flex-start;padding:20px;flex-direction:column;gap:8px}.company-directory>summary h2{font-size:24px}.directory-body{padding:18px}.directory-toolbar{align-items:flex-start;flex-direction:column}.directory-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.directory-link{display:flex;flex-direction:column;gap:2px}.directory-link small{margin-top:6px}}
"""
