"""Small, explicit profile registry for the declared cached-demo universe."""

from __future__ import annotations

from typing import Any

DEMO_PROFILES = {
    "AAPL": {
        "display_name": "Apple Inc.",
        "category": "Consumer technology",
        "category_zh": "消费科技",
        "summary": (
            "A consumer technology company spanning devices, software, and services."
        ),
        "summary_zh": "一家覆盖硬件、软件与服务的消费科技公司。",
    },
    "MSFT": {
        "display_name": "Microsoft Corporation",
        "category": "Software & cloud",
        "category_zh": "软件与云",
        "summary": (
            "A technology company spanning productivity software, cloud infrastructure, "
            "operating systems, and gaming."
        ),
        "summary_zh": "一家覆盖生产力软件、云基础设施、操作系统与游戏的科技公司。",
    },
    "NVDA": {
        "display_name": "NVIDIA Corporation",
        "category": "Semiconductors & computing",
        "category_zh": "半导体与计算",
        "summary": (
            "A semiconductor and computing-platform company focused on accelerated "
            "computing."
        ),
        "summary_zh": "一家专注加速计算的半导体与计算平台公司。",
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
    default_summary = (
        "Historical market context and recent SEC disclosures for "
        f"{readable_name.rstrip('.')}. This view uses the current local evidence "
        "snapshot."
    )
    default_summary_zh = (
        f"{readable_name.rstrip('.')} 的历史市场背景与近期 SEC 披露。"
        "本视图使用当前本地证据快照。"
    )
    return {
        "display_name": readable_name,
        "official_name": official_name,
        "category": configured.get("category", "Company evidence profile"),
        "category_zh": configured.get("category_zh", "公司证据档案"),
        "summary": configured.get("summary", default_summary),
        "summary_zh": configured.get("summary_zh", default_summary_zh),
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
