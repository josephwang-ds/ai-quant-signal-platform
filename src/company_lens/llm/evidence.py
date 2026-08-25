"""Build the small, deterministic evidence packet supplied to an LLM."""

from __future__ import annotations

import json

from company_lens.contracts import Citation, FilingBrief
from company_lens.llm.grounded import (
    NUMBER_LITERAL,
    GroundedExplanationRequest,
    localized_month_number_literals,
)

PROMPT_VERSION = "company-lens-grounded-v2"


def build_grounded_request(
    ticker: str,
    performance: dict,
    filings: list[FilingBrief],
    *,
    language: str = "English",
    depth: str = "beginner",
    prompt_version: str = PROMPT_VERSION,
) -> GroundedExplanationRequest:
    """Freeze the facts, citations, and number literals a provider may use."""
    if not filings:
        raise ValueError("a grounded explanation requires at least one filing")

    filing = filings[0]
    citations: set[str] = set()
    filing_packet = {
        "accession": filing.accession,
        "form": filing.form,
        "accepted_at": filing.accepted_at,
        "items": filing.items,
        "source_url": filing.source_url,
        "passages": [
            _citation_packet(passage, citations) for passage in filing.passages
        ],
        "comparison": _comparison_packet(filing, citations),
        "reaction": _reaction_packet(filing, citations),
    }
    evidence = {
        "schema_version": "company-lens.evidence.v1",
        "company": {"ticker": ticker.upper()},
        "latest_filing": filing_packet,
        "historical_performance": _performance_packet(performance, citations),
        "interpretation_limits": [
            "Use only the supplied evidence and citation IDs.",
            "Historical returns and filing reactions are context, not forecasts.",
            "Do not provide an investment recommendation or price target.",
        ],
    }
    canonical = json.dumps(evidence, sort_keys=True, ensure_ascii=False)
    number_literals = frozenset(
        {*NUMBER_LITERAL.findall(canonical), *localized_month_number_literals(evidence)}
    )
    return GroundedExplanationRequest(
        ticker=ticker.upper(),
        accession=filing.accession,
        prompt_version=prompt_version,
        language=language,
        depth=depth,
        evidence=evidence,
        allowed_citations=frozenset(citations),
        allowed_number_literals=number_literals,
    )


def _citation_packet(citation: Citation, allowed: set[str]) -> dict:
    allowed.add(citation.anchor)
    return {
        "citation": citation.anchor,
        "text": citation.text,
        "source_url": citation.source_url,
    }


def _comparison_packet(filing: FilingBrief, allowed: set[str]) -> dict | None:
    comparison = filing.comparison
    if comparison is None:
        return None
    count_citation = "metric:filing.comparison_counts"
    allowed.add(count_citation)
    changes = []
    for change in comparison.changes:
        changes.append(
            {
                "kind": change.kind,
                "current": (
                    _citation_packet(change.current, allowed) if change.current else None
                ),
                "prior": _citation_packet(change.prior, allowed) if change.prior else None,
                "similarity": (
                    f"{change.similarity:.1%}" if change.similarity is not None else None
                ),
            }
        )
    return {
        "comparable_key": comparison.comparable_key,
        "prior_accession": comparison.prior_accession,
        "prior_accepted_at": comparison.prior_accepted_at,
        "counts": {"citation": count_citation, **comparison.counts},
        "changes": changes,
    }


def _reaction_packet(filing: FilingBrief, allowed: set[str]) -> dict | None:
    reaction = filing.reaction
    if reaction is None:
        return None
    fields = {
        "asset_open_to_close": _metric(
            "metric:filing.asset_open_to_close",
            f"{reaction.asset_open_to_close:+.1%}",
            allowed,
        ),
        "benchmark_open_to_close": _metric(
            "metric:filing.benchmark_open_to_close",
            f"{reaction.benchmark_open_to_close:+.1%}",
            allowed,
        ),
        "benchmark_adjusted_move": _metric(
            "metric:filing.benchmark_adjusted_move",
            f"{reaction.benchmark_adjusted_move:+.1%}",
            allowed,
        ),
        "prior_sample_size": _metric(
            "metric:filing.prior_sample_size", str(reaction.prior_sample_size), allowed
        ),
    }
    if reaction.magnitude_percentile is not None:
        fields["historical_magnitude_percentile"] = _metric(
            "metric:filing.magnitude_percentile",
            f"{reaction.magnitude_percentile:.0%}",
            allowed,
        )
    return {
        "session": reaction.session,
        "definition": (
            "First eligible session open-to-close issuer return less benchmark "
            "open-to-close return; percentile uses only earlier issuer filings."
        ),
        **fields,
    }


def _performance_packet(performance: dict, allowed: set[str]) -> list[dict]:
    asset = performance["asset"]
    benchmark = performance["benchmark"]
    return [
        _metric("metric:asset.total_return", f"{asset['total_return']:+.1%}", allowed),
        _metric("metric:asset.cagr", f"{asset['cagr']:+.1%}", allowed),
        _metric("metric:asset.max_drawdown", f"{asset['max_drawdown']:.1%}", allowed),
        _metric(
            "metric:benchmark.total_return",
            f"{benchmark['total_return']:+.1%}",
            allowed,
        ),
        _metric(
            "metric:relative_total_return",
            f"{performance['relative_total_return']:+.1%}",
            allowed,
        ),
        _metric("metric:observations", str(performance["observations"]), allowed),
    ]


def _metric(citation: str, value: str, allowed: set[str]) -> dict:
    allowed.add(citation)
    return {"citation": citation, "value": value}
