"""Build the compact, immutable evidence map used by the public Q&A function."""

from __future__ import annotations

import json
from typing import Any

from company_lens.llm.grounded import NUMBER_LITERAL, localized_month_number_literals

ASK_EVIDENCE_VERSION = "company-lens.ask-evidence.v1"


def build_ask_evidence(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Reduce one public snapshot to the facts a live model may read."""
    ticker = str(snapshot["ticker"]).upper()
    benchmark = str(snapshot["benchmark"]).upper()
    profile = snapshot.get("profile") or {}
    performance = snapshot["performance"]
    filing = next(iter(snapshot.get("latest_filings") or []), None)
    citations: dict[str, dict[str, str]] = {}

    profile_citation = "source:company-profile"
    citations[profile_citation] = {
        "label": "SEC company record",
        "url": str(profile.get("source_url") or f"/{ticker.lower()}.html"),
        "section": "overview",
    }
    evidence: dict[str, Any] = {
        "schema_version": ASK_EVIDENCE_VERSION,
        "ticker": ticker,
        "as_of": snapshot["as_of"],
        "company": {
            "name": profile.get("display_name") or snapshot.get("company_name") or ticker,
            "category": profile.get("category"),
            "summary": profile.get("summary"),
            "citation": profile_citation,
        },
        "historical_performance": _performance_packet(
            ticker, benchmark, performance, citations
        ),
        "latest_filing": _filing_packet(filing, citations),
        "company_headlines": _headline_packet(snapshot.get("headlines") or [], citations),
        "interpretation_limits": [
            "Use only this evidence map; do not browse or rely on general model knowledge.",
            "Historical returns and filing reactions are observations, not forecasts.",
            "Do not provide a recommendation, price target, or directional prediction.",
            "If the evidence does not answer the question, say so explicitly.",
        ],
    }
    canonical = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    allowed_numbers = sorted(
        {
            *NUMBER_LITERAL.findall(canonical),
            *localized_month_number_literals(evidence),
        }
    )
    return {
        "evidence": evidence,
        "citations": citations,
        "allowed_citations": sorted(citations),
        "allowed_number_literals": allowed_numbers,
    }


def _performance_packet(
    ticker: str,
    benchmark: str,
    performance: dict[str, Any],
    citations: dict[str, dict[str, str]],
) -> dict[str, Any]:
    page = f"/{ticker.lower()}.html#performance"
    metrics = {
        "asset_total_return": (
            "metric:asset.total_return",
            f"{performance['asset']['total_return']:+.1%}",
        ),
        "asset_annualized_return": (
            "metric:asset.cagr",
            f"{performance['asset']['cagr']:+.1%}",
        ),
        "asset_max_drawdown": (
            "metric:asset.max_drawdown",
            f"{performance['asset']['max_drawdown']:.1%}",
        ),
        "benchmark_total_return": (
            "metric:benchmark.total_return",
            f"{performance['benchmark']['total_return']:+.1%}",
        ),
        "relative_total_return": (
            "metric:relative_total_return",
            f"{performance['relative_total_return']:+.1%}",
        ),
        "observations": ("metric:observations", str(performance["observations"])),
    }
    packet: dict[str, Any] = {
        "asset": ticker,
        "benchmark": benchmark,
        "definition": "Adjusted buy-and-hold history over the page's selected period.",
    }
    for name, (citation, value) in metrics.items():
        citations[citation] = {
            "label": name.replace("_", " ").title(),
            "url": page,
            "section": "history",
        }
        packet[name] = {"value": value, "citation": citation}
    return packet


def _filing_packet(
    filing: dict[str, Any] | None,
    citations: dict[str, dict[str, str]],
) -> dict[str, Any] | None:
    if not filing:
        return None
    source_url = str(filing["source_url"])
    source_citation = "source:latest-filing"
    citations[source_citation] = {
        "label": "Latest SEC filing",
        "url": source_url,
        "section": "filing",
    }
    passages = []
    for passage in (filing.get("passages") or [])[:6]:
        citation = str(passage["anchor"])
        citations[citation] = {
            "label": "SEC source passage",
            "url": str(passage.get("source_url") or source_url),
            "section": "filing",
        }
        passages.append(
            {
                "text": passage["text"],
                "citation": citation,
            }
        )
    packet: dict[str, Any] = {
        "accession": filing["accession"],
        "form": filing["form"],
        "accepted_at": filing["accepted_at"],
        "items": filing.get("items") or [],
        "source_citation": source_citation,
        "passages": passages,
    }
    comparison = filing.get("comparison")
    if comparison:
        count_citation = "metric:filing.comparison_counts"
        citations[count_citation] = {
            "label": "Filing wording comparison",
            "url": source_url,
            "section": "filing",
        }
        packet["comparison"] = {
            "prior_accepted_at": comparison.get("prior_accepted_at"),
            "counts": {
                **(comparison.get("counts") or {}),
                "citation": count_citation,
            },
        }
    reaction = filing.get("reaction")
    if reaction:
        reaction_fields = {
            "asset_open_to_close": f"{reaction['asset_open_to_close']:+.1%}",
            "benchmark_open_to_close": f"{reaction['benchmark_open_to_close']:+.1%}",
            "benchmark_adjusted_move": f"{reaction['benchmark_adjusted_move']:+.1%}",
            "prior_sample_size": str(reaction["prior_sample_size"]),
        }
        if reaction.get("magnitude_percentile") is not None:
            reaction_fields["historical_magnitude_percentile"] = (
                f"{reaction['magnitude_percentile']:.0%}"
            )
        packet["reaction"] = {
            "session": reaction["session"],
            "definition": (
                "First eligible session open-to-close issuer return less benchmark "
                "open-to-close return; this does not establish causality."
            ),
        }
        for name, value in reaction_fields.items():
            citation = f"metric:filing.{name}"
            citations[citation] = {
                "label": name.replace("_", " ").title(),
                "url": source_url,
                "section": "filing",
            }
            packet["reaction"][name] = {"value": value, "citation": citation}
    return packet


def _headline_packet(
    headlines: list[dict[str, Any]],
    citations: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    packet = []
    company_rows = [
        headline
        for headline in headlines
        if headline.get("source_type") == "company_news"
    ][:3]
    for headline in company_rows:
        citation = str(headline["citation"])
        citations[citation] = {
            "label": str(headline["publisher"]),
            "url": str(headline["url"]),
            "section": "company_news",
        }
        packet.append(
            {
                "headline": headline["headline"],
                "publisher": headline["publisher"],
                "published_at": headline["published_at"],
                "citation": citation,
            }
        )
    return packet
