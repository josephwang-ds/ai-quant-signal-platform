"""Assemble one cacheable company snapshot from local source artifacts."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from company_lens.contracts import (
    CompanySnapshot,
    EvidenceScopeSummary,
    HeadlineBrief,
)
from company_lens.filings import build_filing_briefs, build_filing_timeline
from company_lens.llm import ImportedDocument, deterministic_explanation, import_headline_index
from company_lens.performance import historical_picture
from company_lens.profiles import company_profile
from company_lens.reactions import build_filing_reactions
from company_lens.universe import (
    SupportedCompany,
    resolve_supported_company,
    supported_companies,
)
from filing_triage.ingest.prices import load_prices

DEFAULT_PERIODS = (1, 3, 5, 10)


def build_snapshot(
    ticker: str,
    *,
    data_dir: str | Path = "data/build",
    benchmark: str = "SPY",
    years: int = 5,
    initial_investment: float = 10_000.0,
    headline_index: str | Path | None = None,
) -> CompanySnapshot:
    """Build a complete, no-network company page read model."""
    return build_snapshots(
        [ticker],
        data_dir=data_dir,
        benchmark=benchmark,
        years=years,
        initial_investment=initial_investment,
        headline_index=headline_index,
    )[0]


def build_snapshots(
    tickers: list[str] | tuple[str, ...] | None = None,
    *,
    data_dir: str | Path = "data/build",
    benchmark: str = "SPY",
    years: int = 5,
    initial_investment: float = 10_000.0,
    headline_index: str | Path | None = None,
) -> list[CompanySnapshot]:
    """Build many snapshots while loading the shared local artifacts only once."""
    root = Path(data_dir)
    universe_path = root / "universe.csv"
    companies = (
        supported_companies(universe_path)
        if tickers is None
        else [resolve_supported_company(ticker, universe_path) for ticker in tickers]
    )
    prices = load_prices(root / "prices.parquet")
    events = pd.read_parquet(root / "events.parquet")
    headline_documents = (
        import_headline_index(headline_index) if headline_index is not None else None
    )
    price_tickers = prices["ticker"].astype(str).str.upper()
    event_tickers = events["ticker"].astype(str).str.upper()
    benchmark_rows = prices[price_tickers == benchmark.upper()]
    price_groups = _group_frames(
        prices[price_tickers != benchmark.upper()],
        prices.loc[price_tickers != benchmark.upper(), "ticker"].astype(str).str.upper(),
    )
    event_groups = _group_frames(events, event_tickers)
    return [
        _assemble_snapshot(
            company,
            root,
            pd.concat([price_groups.get(company.ticker, pd.DataFrame()), benchmark_rows]),
            event_groups.get(company.ticker, events.iloc[0:0]),
            benchmark=benchmark,
            years=years,
            initial_investment=initial_investment,
            headline_documents=headline_documents,
        )
        for company in companies
    ]


def _group_frames(frame: pd.DataFrame, keys: pd.Series) -> dict[str, pd.DataFrame]:
    """Materialize ticker groups without relying on GroupBy's mapping protocol."""
    return {str(ticker): group for ticker, group in frame.groupby(keys, sort=False)}


def _assemble_snapshot(
    company: SupportedCompany,
    root: Path,
    prices: pd.DataFrame,
    events: pd.DataFrame,
    *,
    benchmark: str,
    years: int,
    initial_investment: float,
    headline_documents: list[ImportedDocument] | None,
) -> CompanySnapshot:
    ticker = company.ticker

    requested_periods = tuple(dict.fromkeys((*DEFAULT_PERIODS, years)))
    period_options = {}
    for option_years in requested_periods:
        option_metrics, option_growth = historical_picture(
            prices, ticker, benchmark, option_years, initial_investment
        )
        chart_growth = _downsample_growth(option_growth)
        period_options[f"{option_years}Y"] = {
            "period": {
                "start": chart_growth[0]["date"],
                "end": chart_growth[-1]["date"],
            },
            "performance": option_metrics,
            "growth": chart_growth,
        }

    selected = period_options[f"{years}Y"]
    metrics = selected["performance"]
    growth = selected["growth"]
    reactions = build_filing_reactions(events, prices, ticker, benchmark)
    filings = build_filing_briefs(events, ticker, reactions=reactions)
    filing_timeline = build_filing_timeline(events, ticker, reactions=reactions)
    market_rows = prices[prices["ticker"].str.upper() == ticker]
    company_name, cik = company.official_name, company.cik
    first_market = market_rows.sort_values("date").iloc[0]
    last_market = market_rows.sort_values("date").iloc[-1]
    period = {"start": growth[0]["date"], "end": growth[-1]["date"]}
    warnings = []
    if not filings:
        warnings.append("No 8-K filing was available in the local event dataset.")
    evidence_scope, headlines = _headline_context(headline_documents, ticker)

    provenance = _provenance(root / "provenance.json")
    provenance.update(
        {
            "prices_artifact": "prices.parquet",
            "events_artifact": "events.parquet",
            "generated_at": datetime.now(UTC).isoformat(),
            "calculation": "company_lens.v1.7",
            "filing_reaction": (
                "issuer open-to-close return on the first eligible session after SEC "
                "acceptance, less benchmark open-to-close return; magnitude percentile "
                "uses only earlier measurable issuer filings"
            ),
            "chart_sampling": "deterministic stride; at most 520 points per period",
        }
    )
    explanation = deterministic_explanation(ticker, metrics, filings)
    profile = company_profile(
        ticker,
        company_name,
        cik,
        price_start=pd.Timestamp(first_market["date"]).date().isoformat(),
        price_end=pd.Timestamp(last_market["date"]).date().isoformat(),
        filing_count=len(filings),
    )
    return CompanySnapshot(
        schema_version="1.7",
        ticker=ticker,
        company_name=company_name,
        as_of=period["end"],
        benchmark=benchmark.upper(),
        period=period,
        profile=profile,
        market={
            "latest_adjusted_close": float(last_market["close"]),
            "price_date": pd.Timestamp(last_market["date"]).date().isoformat(),
            "price_field": "vendor-adjusted close",
        },
        performance=metrics,
        growth=growth,
        period_options=period_options,
        latest_filings=filings,
        explanation=explanation,
        provenance=provenance,
        warnings=warnings,
        filing_timeline=filing_timeline,
        evidence_scope=evidence_scope,
        headlines=headlines,
    )


def _provenance(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {"source": "unknown"}


def _headline_context(
    documents: list[ImportedDocument] | None,
    ticker: str,
    *,
    now: datetime | None = None,
) -> tuple[EvidenceScopeSummary | None, list[HeadlineBrief]]:
    if documents is None:
        return None, []
    ticker = ticker.upper()
    matching = [
        document
        for document in documents
        if document.source_type == "market_news"
        or (
            document.source_type == "company_news"
            and (
                document.ticker == ticker
                or ticker in document.tickers
            )
        )
    ]
    ranked = sorted(
        matching,
        key=lambda document: (
            -_timestamp(document.published_at).timestamp(),
            0 if document.source_type == "company_news" else 1,
            document.document_id,
        ),
    )
    selected = ranked[:3]
    headlines = [
        HeadlineBrief(
            headline=document.title,
            publisher=document.source_name,
            published_at=document.published_at or "",
            fetched_at=document.fetched_at,
            url=document.source_url,
            source_type=document.source_type,
            ticker=document.ticker,
            topic=document.topic,
            citation=f"news:{document.document_id}#headline",
        )
        for document in selected
    ]
    fetched_times = [
        _timestamp(document.fetched_at)
        for document in matching
        if document.fetched_at
    ]
    current = now or datetime.now(UTC)
    stale = bool(fetched_times) and max(fetched_times) < current - timedelta(days=2)
    status = "empty" if not matching else "stale" if stale else "available"
    return (
        EvidenceScopeSummary(
            status=status,
            source_types=sorted({document.source_type for document in matching}),
            query=None,
            max_chunks=0,
            selected_chunks=0,
            published_after=None,
            generated_at=current.isoformat(),
        ),
        headlines,
    )


def _timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=UTC)
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _downsample_growth(
    growth: list[dict], max_points: int = 520
) -> list[dict]:
    """Bound chart payload size without changing daily-input metric calculations."""
    if len(growth) <= max_points:
        return growth
    stride = math.ceil((len(growth) - 1) / (max_points - 1))
    sampled = growth[::stride]
    if sampled[-1] != growth[-1]:
        sampled.append(growth[-1])
    return sampled
