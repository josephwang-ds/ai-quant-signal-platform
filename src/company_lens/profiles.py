"""Small, explicit profile registry for the declared cached-demo universe."""

from __future__ import annotations

from typing import Any

DEMO_PROFILES = {
    "AAPL": {
        "display_name": "Apple Inc.",
        "category": "Consumer technology",
        "summary": (
            "A consumer technology company spanning devices, software, and services."
        ),
    },
    "MSFT": {
        "display_name": "Microsoft Corporation",
        "category": "Software & cloud",
        "summary": (
            "A technology company spanning productivity software, cloud infrastructure, "
            "operating systems, and gaming."
        ),
    },
    "NVDA": {
        "display_name": "NVIDIA Corporation",
        "category": "Semiconductors & computing",
        "summary": (
            "A semiconductor and computing-platform company focused on accelerated "
            "computing."
        ),
    },
}


def display_name(ticker: str, official_name: str) -> str:
    """Prefer curated names, otherwise make all-caps SEC names readable."""
    configured = DEMO_PROFILES.get(ticker.upper())
    if configured:
        return configured["display_name"]
    if official_name.isupper():
        return official_name.title().replace("&Amp;", "&")
    return official_name


def company_profile(
    ticker: str,
    official_name: str,
    cik: int | None,
    *,
    price_start: str,
    price_end: str,
    filing_count: int,
) -> dict[str, Any]:
    """Return a bounded profile plus observable local evidence coverage."""
    ticker = ticker.upper()
    configured = DEMO_PROFILES.get(ticker, {})
    readable_name = display_name(ticker, official_name)
    padded_cik = f"{cik:010d}" if cik is not None else None
    source_url = (
        f"https://www.sec.gov/edgar/browse/?CIK={cik}&owner=exclude"
        if cik is not None
        else None
    )
    return {
        "display_name": readable_name,
        "official_name": official_name,
        "category": configured.get("category", "Company evidence profile"),
        "summary": configured.get(
            "summary",
            "Historical market context and recent SEC disclosures for "
            f"{readable_name.rstrip('.')}. This view uses the current local evidence "
            "snapshot.",
        ),
        "cik": padded_cik,
        "source_label": "SEC EDGAR company record" if source_url else None,
        "source_url": source_url,
        "method": (
            "curated category for featured examples; otherwise evidence-profile copy; "
            "issuer identity linked to SEC"
        ),
        "coverage": {
            "price_start": price_start,
            "price_end": price_end,
            "filings_in_snapshot": filing_count,
        },
    }
