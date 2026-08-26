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
        f'<small>Open company lens →</small></a>'
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
<body><main><p class="eyebrow">SOURCE-BACKED COMPANY INTELLIGENCE</p>
<h1>Understand the company.<br><em>Keep the evidence.</em></h1>
<p class="lede">Historical return and risk, recent SEC disclosures, and a bounded
AI explanation with citations. No price prediction. No investment recommendation.</p>
<form id="company-search" class="company-search">
<label for="ticker-search">Search {len(companies)} locally available companies</label>
<div class="search-row"><input id="ticker-search" name="ticker" list="supported-companies"
placeholder="Try AAPL or Apple" autocomplete="off" spellcheck="false" required>
<datalist id="supported-companies">{options}</datalist>
<button type="submit">Open lens</button></div>
<p id="search-status" class="search-status" aria-live="polite">Type an exact ticker or
company name from the current local universe.</p></form>
    <p class="featured-label">Featured examples</p><div class="companies">{links}</div>
    <section class="method-note" id="method"><p class="eyebrow">HOW TO READ A LENS</p>
    <h2>Company first. Evidence second.</h2>
    <p>Every page follows one order: historical picture, latest SEC disclosure, then
    company-specific context. Broad market headlines and implementation details stay off
    the company page so they cannot be mistaken for company evidence.</p>
    <ol><li><span>01</span><strong>History</strong><small>Price and risk versus SPY</small></li>
    <li><span>02</span><strong>Disclosure</strong><small>What the latest 8-K actually says</small></li>
    <li><span>03</span><strong>Boundary</strong><small>Citations, limitations, no forecast</small></li></ol>
    <p class="method-tech"><strong>Under the hood:</strong> point-in-time SEC ingestion,
    return and risk calculations, deterministic NLP change filtering, and an optional
    source-bounded LLM explanation layer.</p></section>
    <p class="foot">Cached real-data demonstration ·
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
    context_nav = '<a href="#context">Company news</a>' if evidence_context else ""
    latest_filing_date = (
        snapshot.latest_filings[0].accepted_at[:10] if snapshot.latest_filings else "Unavailable"
    )
    refresh = snapshot.provenance.get("filing_refresh") or {}
    source_checked_at = refresh.get("checked_at") or snapshot.provenance.get("written_at")
    source_check_label = (
        f"SEC checked {str(source_checked_at)[:10]}"
        if refresh.get("checked_at")
        else f"SEC cache collected {str(source_checked_at)[:10]}"
        if source_checked_at
        else "SEC cache time unavailable"
    )
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
    <a href="index.html" class="company-search-link">Find a company</a>
    <span class="current-symbol" aria-current="page">{html.escape(snapshot.ticker)}</span>
  </nav>
  <nav class="section-nav" aria-label="Page storyline">
        <a href="#brief">Overview</a><a href="#ask">Ask AI</a><a href="#performance">History</a>
        <a href="#filings">Filings</a>{context_nav}
  </nav>
  <span class="trust-label">Evidence, not prediction</span>
</header>

<main>
  {survivor_warning}
  <section class="company-hero">
    <div>
      <p class="eyebrow">COMPANY OVERVIEW · REAL CACHED DATA</p>
      <div class="company-title"><h1>{html.escape(company_name)}</h1>
      <span>{html.escape(snapshot.ticker)}</span></div>
      <p class="profile-category">{html.escape(str(snapshot.profile.get('category', 'Public company')))}</p>
      <p class="hero-copy">{html.escape(str(snapshot.profile.get('summary', 'Business profile unavailable.')))}</p>
      {_profile_meta(snapshot.profile)}
        </div>
    <div class="market-observation">
      <span>Latest adjusted close</span>
      <strong>{_money(snapshot.market['latest_adjusted_close'])}</strong>
      <small>Observed {html.escape(snapshot.market['price_date'])}</small>
    </div>
  </section>

  <section class="brief-section" id="brief" aria-labelledby="brief-title">
    <div class="section-heading">
          <div><p class="eyebrow">AT A GLANCE</p>
          <h2 id="brief-title">What matters on this page</h2></div>
      <span class="mode-badge">{_mode_label(snapshot.explanation.get('mode'))}</span>
    </div>
        <p class="brief-intro">The latest disclosure and one historical reference point.
        Details remain below when you want to verify them.</p>
        <div class="brief-grid">{brief}</div>
      </section>

  {_ask_section(snapshot)}

  <section class="performance-section" id="performance" aria-labelledby="performance-title">
    <div class="section-heading performance-heading">
      <div><p class="eyebrow">HISTORICAL INVESTMENT PICTURE</p>
      <h2 id="performance-title">What happened to $10,000?</h2></div>
      <div class="period-control" aria-label="Historical period">{period_buttons}</div>
    </div>
    <p class="section-intro">Adjusted buy-and-hold history versus {html.escape(snapshot.benchmark)}
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
        <span>Ending value</span><strong id="ending-value"></strong>
        <small id="relative-copy"></small>
        <div class="mini-comparison"><span>{html.escape(snapshot.benchmark)} ending value</span>
        <b id="benchmark-ending"></b></div>
      </aside>
    </div>
        <details class="diagnostics-disclosure"><summary>More risk metrics</summary>
        <div class="metric-grid">
          {_metric("Annualized return", "cagr", "Compound annual growth rate; historical, not forecast.")}
      {_metric("Annualized volatility", "volatility", "Standard deviation of daily returns, annualized.")}
      {_metric(f"Beta vs {snapshot.benchmark}", "beta", "Sensitivity to benchmark daily returns; 1.0 moves roughly with the benchmark.")}
      {_metric(f"Correlation vs {snapshot.benchmark}", "correlation", "How closely daily returns moved together; ranges from -1 to +1.")}
      {_metric("Current drawdown", "current-drawdown", "Distance below the highest adjusted value in the period.")}
      {_metric("Worst day", "worst-day", "Largest single-session adjusted-price decline in the selected period.")}
        </div></details>
        <div class="risk-note" id="risk-note"></div>
  </section>

  <section class="filings-section" id="filings" aria-labelledby="filings-title">
    <div class="section-heading">
      <div><p class="eyebrow">FILING INTELLIGENCE</p><h2 id="filings-title">Recent 8-K disclosures</h2></div>
      <div class="freshness-group"><span class="freshness">Latest filing accepted {html.escape(latest_filing_date)}</span>
      <span class="freshness">{html.escape(source_check_label)}</span></div>
    </div>
        <p class="section-intro">The newest filing opens first. Read what arrived, what the
        next eligible session did, and whether the wording changed in a substantive way.</p>
        <div class="filing-list">{filings}</div>
  </section>

  {evidence_context}

    </main>

    <footer><div><strong>Company Lens</strong><span>Understand the evidence before forming a view.</span>
    <a href="index.html#method">How to read this lens</a></div>
<div class="footer-meta"><span>Snapshot v{html.escape(snapshot.schema_version)}</span>
<span>Market through {html.escape(snapshot.as_of)}</span><span>SEC + adjusted daily prices</span></div></footer>

<script type="application/json" id="period-data">{payload}</script>
<script>{_script(default_period, snapshot.ticker, snapshot.benchmark)}</script>
</body></html>"""


def _ask_section(snapshot: CompanySnapshot) -> str:
    ticker = html.escape(snapshot.ticker)
    return f"""<section class="ask-section" id="ask" aria-labelledby="ask-title">
    <div class="section-heading"><div><p class="eyebrow">CONTROLLED LLM Q&amp;A</p>
    <h2 id="ask-title">Ask the evidence</h2></div>
    <span class="ask-validation">Every answer is validated</span></div>
    <p class="section-intro">Choose a model and ask about {ticker}. The model receives only
    this page's cached SEC passages, calculated history, filing reaction, and matched company
    headlines. Unsupported citations, invented numbers, advice, and forecasts are withheld.</p>
    <div class="ask-layout">
      <form class="ask-form" id="ask-form">
        <div class="ask-controls">
          <label>Model<select id="ask-model" name="provider" disabled>
          <option>Loading live models…</option></select></label>
          <label>Answer language<select id="ask-language" name="language">
          <option value="English">English</option><option value="Chinese">中文</option>
          </select></label>
        </div>
        <label class="ask-question">Question
        <textarea id="ask-question" maxlength="280" rows="3"
        placeholder="What does the latest 8-K tell me?" required></textarea></label>
        <div class="ask-suggestions" aria-label="Suggested questions">
          <button type="button" data-question="What does the latest 8-K tell me?">Latest 8-K</button>
          <button type="button" data-question="How did {ticker} perform versus its benchmark?">Vs benchmark</button>
          <button type="button" data-question="What are the limits of this evidence?">Evidence limits</button>
        </div>
        <div class="ask-submit-row"><button id="ask-submit" type="submit" disabled>Ask model</button>
        <span id="ask-status" aria-live="polite">Checking available models…</span></div>
      </form>
      <div class="ask-result" id="ask-result" aria-live="polite">
        <p class="ask-result-kicker">HOW CONTROL STAYS VISIBLE</p>
        <ol><li><span>1</span>Question is matched to a frozen {ticker} evidence packet.</li>
        <li><span>2</span>The selected provider returns structured claims and citation IDs.</li>
        <li><span>3</span>A server-side validator rejects unsupported citations, numbers,
        advice, or forecasts before anything appears here.</li></ol>
      </div>
    </div>
    <p class="ask-boundary"><strong>Scope:</strong> explanation, not recommendation ·
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
    return f"""<section class="context-section" id="context" aria-labelledby="context-title">
    <div class="section-heading"><div><p class="eyebrow">COMPANY-SPECIFIC CONTEXT</p>
    <h2 id="context-title">Recent company coverage</h2></div>
    <span class="context-status {html.escape(scope.status)}">{html.escape(status_label)}</span></div>
    <p class="section-intro">Only headlines matched to this ticker appear here. They add
    context but are not used to calculate returns or filing reactions.</p>
    <p class="context-freshness">Refreshed {html.escape(freshness)}</p>
    <div class="headline-list">{cards}</div>
    </section>"""


def _headline_card(headline: HeadlineBrief) -> str:
    return (
        f'<article class="headline-card" data-citation="{html.escape(headline.citation)}">'
        f'<div class="headline-meta"><span>{html.escape(headline.publisher)}</span>'
        f"<span>{html.escape(_pretty_context_time(headline.published_at))}</span></div>"
        f"<h3>{html.escape(headline.headline)}</h3>"
        f'<a href="{html.escape(headline.url)}" target="_blank" '
        'rel="noopener noreferrer">Read source ↗</a></article>'
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
            'rel="noreferrer">Open SEC filing ↗</a>'
        )
    else:
        filing_title = "No local filing"
        filing_meta = '<span>Evidence unavailable</span>'
        source_link = ""
    return f"""
    <article class="brief-card brief-lead observed">
      <div class="brief-card-heading"><span>Latest SEC disclosure</span>{source_link}</div>
      <h3>{html.escape(filing_title)}</h3>
      <p>{html.escape(str(changed.get('text', 'Not available.')))}</p>
      <div class="brief-meta">{filing_meta}</div><div class="claim-links">{changed_links}</div>
    </article>
    <article class="brief-card brief-numbers calculated">
      <span>Selected historical period</span>
      <div class="brief-metrics">
        <div><strong id="total-return"></strong><small>Total return</small></div>
        <div><strong id="max-drawdown"></strong><small>Maximum drawdown</small></div>
      </div>
      <p><span id="brief-period-label"></span> of adjusted daily prices versus
      {html.escape(snapshot.benchmark)}. Context, not a forecast.</p>
      <a href="#performance">Explore the full history ↓</a>
    </article>
    <p class="brief-boundary"><strong>Boundary:</strong>
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
    entities = entities or '<span class="missing">No cited entity in the primary document</span>'
    passages = "".join(_passage(passage, filing.entities) for passage in filing.passages)
    if not passages:
        passages = '<p class="missing">No passage passed the deterministic relevance threshold.</p>'
    expanded = " open" if index == 0 else ""
    return f"""<details class="filing-card"{expanded}>
      <summary><div><span class="filing-form">{html.escape(filing.form)}</span>
      <strong>{html.escape(filing.items[0]['label'] if filing.items else 'Corporate update')}</strong>
      <small>Accepted {html.escape(_pretty_date(filing.accepted_at))}</small></div>
      <div class="filing-summary-meta"><span>{html.escape(reaction)}</span>
      <span>View evidence</span><i>⌄</i></div></summary>
      <div class="filing-body"><div class="filing-items">{item_chips}</div>
      {_reaction_block(filing, benchmark)}
      {_comparison_block(filing)}
      <details class="source-details"><summary>Source passages and extracted facts</summary>
      <div class="filing-columns"><div><h3>Extracted facts</h3><div class="number-list">{entities}</div>
      <h3>Relevant passages</h3><div class="passages">{passages}</div></div>
      <aside><span>Source record</span><code>{html.escape(filing.accession)}</code>
      <a href="{html.escape(filing.source_url)}" target="_blank" rel="noreferrer">Open SEC filing ↗</a>
      <p>Passages come from the cached primary filing document.</p></aside></div></details></div>
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
            '<div class="reaction-empty"><strong>Market reaction not yet measurable</strong>'
            '<span>The required company and benchmark bars are not both present for the '
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
    <div class="reaction-heading"><div><span>What happened next</span>
    <strong>{html.escape(session)} · first eligible session</strong></div>
    <small>Observed, not attributed</small></div>
    <div class="reaction-grid">
    <div><span>Company move</span><strong>{html.escape(asset_move)}</strong>
    <small>open to close</small></div>
    <div><span>After subtracting {html.escape(benchmark)}</span><strong>{html.escape(relative_move)}</strong>
    <small>{html.escape(asset_move)} less {html.escape(benchmark_move)}</small></div>
    <div><span>Compared with past filings</span><strong>{html.escape(history_value)}</strong>
    <small>{html.escape(history_note)}</small></div></div>
    <p>This is the first session whose opening followed SEC acceptance. It shows what
    happened next; it does not claim the filing caused the move.</p></section>"""


def _comparison_block(filing: FilingBrief) -> str:
    comparison = filing.comparison
    if comparison is None:
        return (
            '<div class="comparison-empty"><strong>Prior comparison unavailable</strong>'
            '<span>No earlier filing with the same form and primary event type exists in '
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
            '<div class="comparison-clear"><strong>No substantive wording change detected</strong>'
            '<span>Date and fiscal-quarter roll-forwards are treated as routine updates. '
            "Referenced exhibits may still contain detail outside the cached primary document.</span></div>"
        )
    return f"""<section class="comparison-panel" aria-label="Prior comparable filing changes">
    <div class="comparison-heading"><div><span>What changed vs the last similar filing</span>
    <strong>{html.escape(_pretty_date(comparison.prior_accepted_at))}</strong></div>
    <a href="{html.escape(comparison.prior_source_url)}" target="_blank" rel="noreferrer">
    Prior filing ↗</a></div><div class="change-counts">{count_chips}</div>
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
        return '<a href="#performance" class="metric-citation">Calculated metric</a>'
    return f'<a href="#{_dom_id(value)}" class="source-citation">Source passage</a>'


def _metric(label: str, element_id: str, definition: str) -> str:
    return (
        f'<article class="metric-card"><span>{html.escape(label)} '
        f'<i title="{html.escape(definition)}">?</i></span><strong id="{element_id}"></strong>'
        f'<small>{html.escape(definition)}</small></article>'
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
    return f"""
const periods = JSON.parse(document.getElementById('period-data').textContent);
const ticker = {json.dumps(ticker)};
const benchmark = {json.dumps(benchmark)};
const svg = document.getElementById('growth-chart');
const assetPath = document.getElementById('asset-path');
const benchmarkPath = document.getElementById('benchmark-path');
const hoverLine = document.getElementById('hover-line');
const assetPoint = document.getElementById('asset-point');
const benchmarkPoint = document.getElementById('benchmark-point');
const tooltip = document.getElementById('chart-tooltip');
let currentGrowth = [];
let chartScale = null;

const money = value => new Intl.NumberFormat('en-US', {{style:'currency',currency:'USD',maximumFractionDigits:0}}).format(value);
const pct = value => new Intl.NumberFormat('en-US', {{style:'percent',maximumFractionDigits:1,signDisplay:'exceptZero'}}).format(value);
const plainPct = value => new Intl.NumberFormat('en-US', {{style:'percent',maximumFractionDigits:1}}).format(value);
const decimal = value => value == null ? 'Not available' : value.toFixed(2);

function setPeriod(label) {{
  const view = periods[label];
  const p = view.performance;
  document.querySelectorAll('.period-button').forEach(button => {{
    const active = button.dataset.period === label;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  }});
  document.getElementById('ending-value').textContent = money(p.ending_value);
  document.getElementById('benchmark-ending').textContent = money(p.initial_investment * (1 + p.benchmark.total_return));
  document.getElementById('relative-copy').textContent = `${{pct(p.relative_total_return)}} vs ${{benchmark}} over this period`;
  document.getElementById('brief-period-label').textContent = label;
  document.getElementById('total-return').textContent = pct(p.asset.total_return);
  document.getElementById('cagr').textContent = pct(p.asset.cagr);
  document.getElementById('max-drawdown').textContent = plainPct(p.asset.max_drawdown);
  document.getElementById('volatility').textContent = plainPct(p.asset.annualized_volatility);
  document.getElementById('beta').textContent = decimal(p.beta);
  document.getElementById('correlation').textContent = decimal(p.correlation);
  document.getElementById('current-drawdown').textContent = plainPct(p.asset.current_drawdown);
  document.getElementById('worst-day').textContent = plainPct(p.asset.worst_day);
  const recovery = p.asset.recovery_sessions == null ? 'not recovered within the selected period' : `recovered after ${{p.asset.recovery_sessions}} trading sessions`;
  document.getElementById('risk-note').innerHTML = `<strong>Experienced risk</strong><span>The largest decline was ${{plainPct(p.asset.max_drawdown)}} versus ${{plainPct(p.benchmark.max_drawdown)}} for ${{benchmark}}, reaching its trough on ${{p.asset.max_drawdown_date}}; it ${{recovery}}.</span>`;
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
}}

async function loadAskModels() {{
  try {{
    const response = await fetch('/api/ask', {{headers: {{Accept: 'application/json'}}}});
    if (!response.ok) throw new Error('Live model service is unavailable.');
    const payload = await response.json();
    askModel.replaceChildren();
    payload.models.forEach(model => {{
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = `${{model.provider}} · ${{model.model}}`;
      askModel.append(option);
    }});
    if (!payload.models.length) throw new Error('No live model is configured.');
    askModel.disabled = false;
    askSubmit.disabled = false;
    setAskStatus(`${{payload.models.length}} validated model${{payload.models.length === 1 ? '' : 's'}} available`, 'ready');
  }} catch (error) {{
    askModel.innerHTML = '<option>Live models unavailable</option>';
    setAskStatus('The page data remains available; live Q&A is currently offline.', 'error');
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
  askResult.textContent = 'Reading the bounded evidence packet…';
  setAskStatus('Waiting for the selected model…');
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
    if (!response.ok) throw new Error(payload.message || 'The answer could not be generated.');
    renderAskAnswer(payload);
    setAskStatus(`${{payload.meta.model}} · ${{payload.meta.latency_ms}} ms · validator passed`, 'ready');
  }} catch (error) {{
    askResult.className = 'ask-result error';
    askResult.textContent = error.message || 'The selected model is unavailable.';
    setAskStatus('No unvalidated answer was shown.', 'error');
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
  label.textContent = 'VALIDATED ANSWER';
  const model = document.createElement('small');
  model.textContent = `${{payload.meta.provider}} · evidence through ${{payload.meta.evidence_as_of}}`;
  heading.append(label, model);
  askResult.append(heading);
  payload.answer.forEach(claim => askResult.append(renderAskClaim(claim)));
  const details = document.createElement('details');
  details.className = 'ask-limitations';
  const summary = document.createElement('summary');
  summary.textContent = 'What this answer cannot establish';
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

loadAskModels();
"""


def _index_script() -> str:
    return """
const companies = JSON.parse(document.getElementById('company-data').textContent);
const form = document.getElementById('company-search');
const input = document.getElementById('ticker-search');
const status = document.getElementById('search-status');
const normalize = value => value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
const scopeCopy = `${companies.length} companies are available from the current local evidence set.`;

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
  status.classList.add('error');
  status.textContent = partialMatches.length
    ? 'More than one local company matched. Enter the exact ticker.'
    : `Not in the current local ${companies.length}-company universe.`;
});

input.addEventListener('input', () => {
  status.classList.remove('error');
  status.textContent = scopeCopy;
});
"""


def _css() -> str:
    return """
:root{--paper:#f4f3ef;--panel:#fff;--ink:#12202b;--muted:#65727b;--line:#d9dedf;--blue:#2864dc;--blue-soft:#edf3ff;--green:#14765d;--green-soft:#eaf6f0;--amber:#a96418;--amber-soft:#fff5e8;--navy:#0d2538;--shadow:0 18px 50px rgba(24,42,53,.08)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:16px;line-height:1.55}.topbar{height:70px;padding:0 max(28px,calc((100vw - 1240px)/2));display:flex;align-items:center;border-bottom:1px solid var(--line);background:rgba(244,243,239,.94);position:sticky;top:0;z-index:20;backdrop-filter:blur(16px)}.brand{display:flex;align-items:center;gap:10px;color:var(--navy);font-weight:760;text-decoration:none;letter-spacing:-.02em}.brand-mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:var(--navy);color:white;font-size:11px;letter-spacing:.04em}.topbar nav{display:flex;align-items:center;margin-left:55px;gap:8px}.company-search-link{padding:7px 10px;border-radius:8px;color:var(--muted);font-size:12px;font-weight:700;text-decoration:none}.company-search-link:hover{background:var(--panel);color:var(--ink)}.current-symbol{padding:5px 8px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink);font-size:11px;font-weight:800;letter-spacing:.06em}.trust-label{margin-left:auto;color:var(--green);font-size:12px;font-weight:750;text-transform:uppercase;letter-spacing:.08em}main{max-width:1240px;margin:auto;padding:30px 28px 90px}.scope-warning{padding:11px 15px;border:1px solid #ead2ad;border-radius:10px;background:var(--amber-soft);display:flex;gap:15px;font-size:12px;color:#775020}.scope-warning strong{text-transform:uppercase;letter-spacing:.08em}.company-hero{display:flex;justify-content:space-between;align-items:end;padding:65px 0 48px}.eyebrow{margin:0 0 10px;color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.13em}.company-title{display:flex;align-items:center;gap:16px}.company-title h1{margin:0;font-family:Georgia,"Times New Roman",serif;font-size:clamp(40px,5vw,68px);font-weight:500;line-height:1.05;letter-spacing:-.045em}.company-title>span{padding:7px 10px;background:var(--navy);border-radius:8px;color:#fff;font-size:13px;font-weight:800;letter-spacing:.06em}.hero-copy{max-width:650px;margin:17px 0 0;color:var(--muted);font-size:18px}.market-observation{min-width:220px;padding-left:25px;border-left:1px solid var(--line);display:flex;flex-direction:column;align-items:flex-end}.market-observation span,.ending-card>span{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.market-observation strong{font-family:Georgia,serif;font-size:38px;font-weight:500}.market-observation small{color:var(--muted)}section{margin-bottom:28px;padding:38px;border:1px solid var(--line);border-radius:20px;background:var(--panel);box-shadow:0 1px 0 rgba(255,255,255,.6)}.section-heading{display:flex;align-items:start;justify-content:space-between;gap:24px}.section-heading h2,.trust-section h2{margin:0;font-family:Georgia,serif;font-size:34px;font-weight:500;letter-spacing:-.025em}.mode-badge,.freshness{padding:7px 10px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}.brief-section{background:var(--navy);color:#fff;border-color:var(--navy);box-shadow:var(--shadow)}.brief-section .eyebrow{color:#78a7ff}.brief-section .mode-badge{border-color:#365166;color:#aebfca}.brief-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin-top:28px;background:#365166;border:1px solid #365166;border-radius:14px;overflow:hidden}.brief-card{min-height:190px;padding:25px;background:#122d41}.brief-card>span{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.1em}.brief-card.observed>span{color:#80aaff}.brief-card.calculated>span{color:#5fd0aa}.brief-card.interpreted>span{color:#e9b66d}.brief-card p{font-family:Georgia,serif;font-size:20px;line-height:1.45}.claim-links{display:flex;gap:8px}.claim-links a{font-size:11px;color:#d9e6ee;text-decoration:none;border-bottom:1px solid #6e8290}.authority-row{display:flex;gap:25px;margin-top:22px;color:#aebfca;font-size:11px}.authority-row span{display:flex;align-items:center;gap:7px}.dot{width:7px;height:7px;border-radius:50%}.dot.observed{background:#80aaff}.dot.calculated{background:#5fd0aa}.dot.interpreted{background:#e9b66d}.performance-section{padding-bottom:30px}.performance-heading{align-items:center}.period-control{display:flex;padding:4px;background:var(--paper);border-radius:10px}.period-button{border:0;background:transparent;padding:7px 13px;border-radius:7px;color:var(--muted);font-weight:750;cursor:pointer}.period-button:hover{color:var(--ink)}.period-button.active{background:var(--panel);color:var(--blue);box-shadow:0 2px 8px rgba(20,40,55,.08)}.section-intro{max-width:730px;margin:10px 0 28px;color:var(--muted)}.performance-layout{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:18px}.chart-panel{position:relative;border:1px solid var(--line);border-radius:14px;padding:18px;background:#fbfcfc}.chart-legend{height:25px;display:flex;align-items:center;gap:18px;color:var(--muted);font-size:11px}.chart-legend span:last-child{margin-left:auto}.line{display:inline-block;width:18px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}.line.asset{background:var(--blue)}.line.benchmark{background:#8a969e}#growth-chart{display:block;width:100%;overflow:visible}#growth-chart path{fill:none;stroke-linecap:round;stroke-linejoin:round}#asset-path{stroke:var(--blue);stroke-width:3}#benchmark-path{stroke:#99a4ab;stroke-width:2}#chart-grid line{stroke:#e6eaeb;stroke-width:1}#chart-labels text{font-size:10px;fill:#7c888f}#hover-line{stroke:#91a0a8;stroke-dasharray:3 3;opacity:0;pointer-events:none}#asset-point{fill:var(--blue);stroke:white;stroke-width:2;opacity:0}#benchmark-point{fill:#89969e;stroke:white;stroke-width:2;opacity:0}.chart-hit{fill:transparent;cursor:crosshair}.chart-tooltip{position:absolute;top:72px;transform:translateX(-50%);display:none;min-width:155px;padding:10px 12px;background:var(--navy);color:#fff;border-radius:9px;box-shadow:var(--shadow);pointer-events:none;font-size:11px}.chart-tooltip.visible{display:flex;flex-direction:column}.chart-tooltip b{margin-bottom:4px}.ending-card{padding:24px;background:var(--blue-soft);border-radius:14px;display:flex;flex-direction:column}.ending-card>strong{margin:8px 0 2px;font-family:Georgia,serif;font-size:34px;font-weight:500;color:#173f91}.ending-card>small{color:#4d6d9f}.mini-comparison{margin-top:auto;padding-top:18px;border-top:1px solid #cfdbf3;display:flex;flex-direction:column;color:#4d6d9f;font-size:11px}.mini-comparison b{font-size:17px;color:#173f91}.metric-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:18px}.metric-card{padding:16px;border:1px solid var(--line);border-radius:12px}.metric-card>span{display:flex;justify-content:space-between;min-height:36px;color:var(--muted);font-size:11px;font-weight:700}.metric-card i{display:grid;place-items:center;width:17px;height:17px;border:1px solid var(--line);border-radius:50%;font-style:normal}.metric-card strong{display:block;font-family:Georgia,serif;font-size:25px;font-weight:500}.metric-card small{display:none}.risk-note{display:flex;gap:20px;margin-top:18px;padding:15px 18px;border-left:3px solid var(--amber);background:var(--amber-soft);color:#664b2e;font-size:13px}.risk-note strong{min-width:130px}.filing-list{display:flex;flex-direction:column;gap:10px}.filing-card{border:1px solid var(--line);border-radius:14px;overflow:hidden}.filing-card summary{list-style:none;padding:18px 20px;display:flex;align-items:center;justify-content:space-between;cursor:pointer}.filing-card summary::-webkit-details-marker{display:none}.filing-card summary>div:first-child{display:grid;grid-template-columns:auto 1fr;gap:2px 11px;align-items:center}.filing-card summary strong{font-size:15px}.filing-card summary small{grid-column:2;color:var(--muted)}.filing-form{grid-row:1/3;padding:7px 9px;background:var(--green-soft);color:var(--green);border-radius:8px;font-weight:800}.filing-summary-meta{display:flex;align-items:center;gap:18px;color:var(--muted);font-size:12px}.filing-summary-meta i{font-size:18px;transition:transform .2s}.filing-card[open] .filing-summary-meta i{transform:rotate(180deg)}.filing-body{padding:0 20px 22px;border-top:1px solid var(--line);background:#fbfcfc}.filing-items{display:flex;flex-wrap:wrap;gap:7px;padding:16px 0}.item-chip,.number-chip{padding:5px 8px;border-radius:7px;background:var(--paper);color:var(--muted);font-size:11px;text-decoration:none}.number-chip{background:var(--blue-soft);color:#2855a7;font-weight:750}.filing-columns{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:30px}.filing-columns h3{margin:16px 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em}.number-list{display:flex;flex-wrap:wrap;gap:6px}.passages{display:flex;flex-direction:column;gap:8px}blockquote{margin:0;padding:14px 16px;border-left:2px solid #9db8ed;background:#fff}blockquote p{margin:0 0 7px;font-family:Georgia,serif;font-size:15px}blockquote a,.filing-columns aside a{color:var(--blue);font-size:10px;text-decoration:none}.filing-columns aside{padding:16px;border-radius:10px;background:var(--paper);display:flex;flex-direction:column;align-items:start;gap:8px;font-size:11px;color:var(--muted)}.filing-columns aside>span{text-transform:uppercase;letter-spacing:.08em}.filing-columns aside code{word-break:break-all;color:var(--ink)}.missing,.empty{color:var(--muted);font-size:12px;font-style:italic}.trust-section{background:#e9ece9}.trust-section>.eyebrow{color:var(--green)}.trust-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:28px}.trust-grid article{padding:20px;background:rgba(255,255,255,.6);border-radius:12px}.trust-grid article>span{font-family:Georgia,serif;color:var(--green);font-size:24px}.trust-grid h3{margin:8px 0 4px}.trust-grid p{margin:0;color:var(--muted);font-size:13px}footer{max-width:1240px;margin:auto;padding:28px;display:flex;justify-content:space-between;border-top:1px solid var(--line);color:var(--muted);font-size:12px}footer>div:first-child{display:flex;flex-direction:column}.footer-meta{display:flex;gap:20px}
.freshness-group{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:6px}.entity-chip{display:inline-flex;align-items:center;gap:6px}.entity-chip small{padding-right:6px;border-right:1px solid #b9c9e8;color:#60749a;font-size:8px;text-transform:uppercase;letter-spacing:.05em}.entity-mark{padding:1px 3px;border-radius:3px;background:#e8efff;color:inherit}.entity-mark.percentage{background:#e7f5ee}.entity-mark.date{background:#fff0da}.reaction-panel{margin:0 0 14px;padding:18px;border:1px solid #cfe0d8;border-radius:12px;background:#f3f8f5}.reaction-heading{display:flex;justify-content:space-between;gap:20px}.reaction-heading>div{display:flex;flex-direction:column}.reaction-heading span{color:var(--green);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.reaction-heading strong{font-size:13px}.reaction-heading>small{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}.reaction-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:13px}.reaction-grid>div{padding:12px;border:1px solid #dbe8e1;border-radius:9px;background:#fff;display:flex;flex-direction:column}.reaction-grid span{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.07em}.reaction-grid strong{margin:3px 0;font-family:Georgia,serif;font-size:19px;font-weight:500}.reaction-grid small,.reaction-panel>p{color:var(--muted);font-size:10px}.reaction-panel>p{margin:12px 0 0}.reaction-empty{display:flex;flex-direction:column;margin:0 0 14px;padding:13px 15px;border:1px dashed #cfe0d8;border-radius:10px;color:var(--muted);font-size:11px}.reaction-empty strong{color:var(--ink)}.comparison-panel{margin:0 0 22px;padding:18px;border:1px solid #cddbed;border-radius:12px;background:#f5f8fd}.comparison-heading{display:flex;justify-content:space-between;gap:20px}.comparison-heading>div{display:flex;flex-direction:column}.comparison-heading span{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em}.comparison-heading strong{font-size:13px}.comparison-heading a,.change-quote a{color:var(--blue);font-size:10px;text-decoration:none}.change-counts{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}.change-count{padding:4px 7px;border-radius:999px;font-size:10px;font-weight:750}.change-count.changed{background:#fff1d8;color:#825616}.change-count.added{background:var(--green-soft);color:var(--green)}.change-count.removed{background:#f8e9e7;color:#98473e}.change-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:12px}.change-card{padding:12px;border:1px solid var(--line);border-radius:9px;background:#fff}.change-card header{display:flex;justify-content:space-between;gap:10px}.change-card header>strong{font-size:11px;text-transform:uppercase;letter-spacing:.07em}.similarity{color:var(--muted);font-size:10px}.change-quote{margin-top:9px;padding-left:9px;border-left:2px solid #b9c8df}.change-quote>span{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.08em}.change-quote p{margin:2px 0 5px;font-family:Georgia,serif;font-size:13px;line-height:1.4}.comparison-empty{display:flex;flex-direction:column;margin:0 0 22px;padding:13px 15px;border:1px dashed var(--line);border-radius:10px;color:var(--muted);font-size:11px}.comparison-empty strong{color:var(--ink)}.profile-category{margin:18px 0 0;color:var(--blue);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.09em}.hero-copy{margin-top:6px}.profile-meta{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:14px;color:var(--muted);font-size:11px}.profile-meta a{color:var(--blue);text-decoration:none;border-bottom:1px solid #aac0eb}.metric-grid{grid-template-columns:repeat(4,1fr)}
.timeline-panel{margin:0 0 20px;padding:18px;border:1px solid var(--line);border-radius:12px;background:#fbfcfc}.timeline-heading{display:flex;justify-content:space-between;gap:20px}.timeline-heading>div{display:flex;flex-direction:column}.timeline-heading span{color:var(--blue);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.timeline-heading strong{font-size:13px}.timeline-heading>small{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em}.timeline-track{position:relative;display:grid;grid-auto-flow:column;grid-auto-columns:minmax(155px,1fr);gap:8px;margin-top:16px;padding-top:14px;overflow-x:auto;scrollbar-width:thin}.timeline-track:before{content:"";position:absolute;top:20px;left:12px;right:12px;height:1px;background:var(--line)}.timeline-event{position:relative;min-height:145px;padding:20px 12px 12px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);text-decoration:none;display:flex;flex-direction:column}.timeline-event>i{position:absolute;top:-10px;left:14px;width:13px;height:13px;border:3px solid #fff;border-radius:50%;background:#8d989f;box-shadow:0 0 0 1px var(--line)}.timeline-event.positive>i{background:var(--green)}.timeline-event.negative>i{background:#a74e43}.timeline-event>span,.timeline-event>small{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.05em}.timeline-event>strong{margin:5px 0 2px;font-size:11px;line-height:1.35}.timeline-event>b{margin-top:auto;font-size:12px}.timeline-event>em{color:var(--muted);font-size:9px;font-style:normal}.timeline-panel>p{margin:11px 0 0;color:var(--muted);font-size:10px}
.topbar .section-nav{margin-left:auto;gap:3px}.section-nav a{padding:7px 9px;border-radius:7px;color:var(--muted);font-size:11px;font-weight:750;text-decoration:none}.section-nav a:hover{background:var(--panel);color:var(--blue)}.trust-label{margin-left:22px}.company-hero{padding:46px 0 34px}.evidence-flow{display:flex;align-items:center;gap:9px;margin-top:18px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}.evidence-flow span{padding:5px 8px;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.62)}.evidence-flow i{color:var(--blue);font-style:normal}.brief-section{background:linear-gradient(135deg,#0d2436 0%,#132f43 100%)}.brief-intro{max-width:680px;margin:9px 0 0;color:#aebfca;font-size:13px}.brief-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:10px;margin-top:26px;background:transparent;border:0;border-radius:0;overflow:visible}.brief-card{min-height:0;padding:24px;border:1px solid #365166;border-radius:13px;background:rgba(16,43,62,.82)}.brief-lead{grid-column:span 7;background:linear-gradient(145deg,#173a55,#122d41)}.brief-numbers{grid-column:span 5;background:#102f38}.brief-reading,.brief-limit{grid-column:span 6}.brief-limit{background:#302c2a;border-color:#5b4a3b}.brief-card>span,.brief-card-heading>span{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.11em}.brief-card.observed>span,.brief-card.observed .brief-card-heading>span{color:#80aaff}.brief-card.calculated>span{color:#5fd0aa}.brief-card.interpreted>span{color:#b7c9ff}.brief-card.guardrail>span{color:#e9b66d}.brief-card-heading{display:flex;justify-content:space-between;gap:18px}.brief-card-heading>a,.brief-numbers>a{color:#d9e6ee;font-size:10px;text-decoration:none;border-bottom:1px solid #6e8290}.brief-card h3{max-width:540px;margin:18px 0 7px;font-family:Georgia,serif;font-size:26px;font-weight:500;line-height:1.15}.brief-card p{margin:11px 0;font-family:Georgia,serif;font-size:17px;line-height:1.48}.brief-lead>p{font-size:19px}.brief-meta{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 8px}.brief-meta span{padding:5px 7px;border:1px solid #466177;border-radius:6px;color:#bacad4;font-size:9px}.brief-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:19px 0 14px}.brief-metrics>div{padding:14px;border:1px solid #28514e;border-radius:10px;background:rgba(9,33,37,.55)}.brief-metrics strong{display:block;font-family:Georgia,serif;font-size:31px;font-weight:500;color:#77ddb8}.brief-metrics small{color:#9bb9ae;font-size:9px;text-transform:uppercase;letter-spacing:.06em}.brief-numbers p{color:#b8c9c4;font-family:inherit;font-size:11px}.claim-links{flex-wrap:wrap}.authority-row{align-items:center}.authority-row span b{color:#fff;font-size:9px}.authority-row>em{color:#627786;font-style:normal}.diagnostic-heading{display:flex;justify-content:space-between;align-items:end;margin-top:22px;padding-top:17px;border-top:1px solid var(--line)}.diagnostic-heading span{font-size:12px;font-weight:800}.diagnostic-heading small{color:var(--muted);font-size:10px}.metric-grid{grid-template-columns:repeat(3,1fr);margin-top:10px}.metric-card{background:#fbfcfc;transition:border-color .18s,transform .18s}.metric-card:hover{border-color:#b9c9d8;transform:translateY(-1px)}.trust-grid article>b{display:block;margin-top:7px;color:var(--green);font-size:8px;letter-spacing:.1em}#brief,#performance,#filings,#context,#method{scroll-margin-top:90px}.section-nav a:focus-visible,.brief-card a:focus-visible,.headline-card a:focus-visible{outline:3px solid #80aaff;outline-offset:3px}
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
"""


def _index_css() -> str:
    return """
:root{--ink:#102537;--muted:#667681;--blue:#2864dc;--paper:#f3f2ed}*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--paper);color:var(--ink);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{width:min(920px,calc(100% - 40px));padding:80px 0}.eyebrow{color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.14em}h1{margin:22px 0;font:500 clamp(48px,8vw,86px)/.98 Georgia,serif;letter-spacing:-.05em}h1 em{color:var(--blue);font-weight:500}.lede{max-width:660px;color:var(--muted);font-size:19px}.companies{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:55px}.company-link{padding:25px;border:1px solid #d7dcdd;border-radius:14px;background:#fff;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;transition:transform .2s,box-shadow .2s}.company-link:hover{transform:translateY(-3px);box-shadow:0 16px 40px rgba(20,38,52,.1)}.company-link span{font:500 30px Georgia,serif}.company-link small{margin-top:25px;color:var(--blue)}.foot{margin-top:30px;color:var(--muted);font-size:11px}@media(max-width:650px){main{padding:50px 0}.companies{grid-template-columns:1fr}.company-link{padding:18px}.company-link small{margin-top:8px}}
.company-search{max-width:660px;margin-top:34px}.company-search label{display:block;margin-bottom:8px;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}.search-row{display:grid;grid-template-columns:1fr auto;gap:8px}.search-row input{min-width:0;padding:15px 17px;border:1px solid #d7dcdd;border-radius:7px;background:#fff;color:var(--ink);font:inherit;outline:none}.search-row input:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(40,100,220,.12)}.search-row button{padding:0 20px;border:0;border-radius:7px;background:var(--ink);color:#fff;font-weight:750;cursor:pointer}.search-status{margin:7px 2px 0;color:var(--muted);font-size:11px}.search-status.error{color:#a4432d}.featured-label{margin:30px 0 -25px;color:var(--muted);font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.1em}.companies{margin-top:35px}.company-link{padding:22px;border-radius:5px}.company-link strong{margin-top:3px;color:var(--muted);font-size:12px}.company-link small{margin-top:21px}.return-link{display:inline-block;margin-top:24px;color:var(--blue);font-weight:750;text-decoration:none}.method-note{margin-top:80px;padding:54px 0 0;border-top:1px solid #d7dcdd}.method-note h2{margin:8px 0 10px;font:500 38px/1.1 Georgia,serif;letter-spacing:-.025em}.method-note>p:not(.eyebrow){max-width:720px;color:var(--muted);font-size:16px}.method-note ol{margin:30px 0 0;padding:0;border-top:1px solid #d7dcdd;list-style:none}.method-note li{display:grid;grid-template-columns:44px 130px 1fr;gap:16px;padding:16px 0;border-bottom:1px solid #d7dcdd}.method-note li span{color:var(--blue);font-weight:800}.method-note li small{color:var(--muted)}.method-tech{padding-top:18px;font-size:13px!important}.method-tech strong{color:var(--ink)}body{display:block;font-family:"Avenir Next","Segoe UI",sans-serif}main{width:min(1040px,calc(100% - 40px))}@media(max-width:650px){.search-row{grid-template-columns:1fr}.search-row button{padding:14px}.method-note{margin-top:55px;padding-top:36px}.method-note li{grid-template-columns:36px 1fr}.method-note li small{grid-column:2}}
"""
