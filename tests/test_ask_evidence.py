from __future__ import annotations

from company_lens.web.ask import (
    ASK_EVIDENCE_VERSION,
    SCOPE_SECTIONS,
    build_ask_evidence,
    evidence_scopes,
)


def _scope(snapshot: dict, name: str = "all") -> dict:
    """One scope's packet, in the shape the Q&A function consumes."""
    return build_ask_evidence(snapshot)["scopes"][name]


def _snapshot() -> dict:
    return {
        "ticker": "ABC",
        "company_name": "ABC Corp.",
        "as_of": "2026-08-25",
        "benchmark": "SPY",
        "profile": {
            "display_name": "ABC Corp.",
            "category": "Test company",
            "summary": "A bounded profile.",
            "source_url": "https://www.sec.gov/abc",
        },
        "performance": {
            "asset": {
                "total_return": 0.25,
                "cagr": 0.12,
                "max_drawdown": -0.20,
            },
            "benchmark": {"total_return": 0.10},
            "relative_total_return": 0.15,
            "observations": 250,
        },
        "growth": [{"date": "2026-08-25", "asset_value": 12_500}],
        "latest_filings": [
            {
                "accession": "0001",
                "form": "8-K",
                "accepted_at": "2026-08-20T16:30:00-04:00",
                "items": [{"code": "2.02", "label": "Results"}],
                "source_url": "https://www.sec.gov/filing",
                "passages": [
                    {
                        "anchor": "filing#sentence-1",
                        "text": "Revenue was $120 million.",
                        "source_url": "https://www.sec.gov/filing#sentence-1",
                    }
                ],
                "comparison": {
                    "prior_accepted_at": "2026-05-20T16:30:00-04:00",
                    "counts": {"changed": 1, "added": 0, "removed": 0},
                },
                "reaction": {
                    "session": "2026-08-21",
                    "asset_open_to_close": 0.03,
                    "benchmark_open_to_close": 0.01,
                    "benchmark_adjusted_move": 0.02,
                    "magnitude_percentile": 0.8,
                    "prior_sample_size": 10,
                },
            }
        ],
        "headlines": [
            {
                "headline": "ABC launches a product",
                "publisher": "Company Wire",
                "published_at": "2026-08-24T10:00:00+00:00",
                "url": "https://example.com/company",
                "source_type": "company_news",
                "citation": "news:abc#headline",
            },
        ],
        "market_headlines": [
            {
                "headline": "Rates are unchanged at 4.25%",
                "publisher": "Market Wire",
                "published_at": "2026-08-24T09:00:00+00:00",
                "url": "https://example.com/market",
                "source_type": "market_news",
                "citation": "news:market#headline",
            },
        ],
    }


def test_ask_evidence_is_compact_company_specific_and_citation_bounded() -> None:
    packet = _scope(_snapshot(), "company")

    assert packet["evidence"]["schema_version"] == ASK_EVIDENCE_VERSION
    assert "growth" not in packet["evidence"]
    assert packet["evidence"]["company_headlines"] == [
        {
            "headline": "ABC launches a product",
            "publisher": "Company Wire",
            "published_at": "2026-08-24T10:00:00+00:00",
            "citation": "news:abc#headline",
        }
    ]
    assert "news:market#headline" not in packet["allowed_citations"]
    assert "filing#sentence-1" in packet["allowed_citations"]
    assert "metric:asset.total_return" in packet["allowed_citations"]
    assert "$120" in packet["allowed_number_literals"]
    assert set(packet["allowed_citations"]) == set(packet["citations"])


def test_ask_evidence_keeps_api_keys_and_local_paths_out() -> None:
    snapshot = _snapshot()
    snapshot["provenance"] = {
        "api_key": "secret",
        "path": "/Users/example/private/file.json",
    }

    packet = build_ask_evidence(snapshot)
    rendered = str(packet)

    assert "secret" not in rendered
    assert "/Users/example" not in rendered


def test_ask_evidence_includes_bounded_fundamentals_when_available() -> None:
    snapshot = _snapshot()
    snapshot["fundamentals"] = {
        "status": "available",
        "series_basis": "latest_restated",
        "requested_years": 10,
        "knowledge_at": "2025-10-31T18:00:00-04:00",
        "warnings": ["Coverage note"],
        "reported_series": [
            {
                "metric_id": "revenue",
                "label": "Revenue",
                "definition": "Top-line revenue",
                "expected_unit": "USD",
                "coverage_status": "complete",
                "observations": [
                    {
                        "fiscal_year": 2024,
                        "period_end": "2024-09-28",
                        "value": 391_035_000_000,
                        "unit": "USD",
                        "status": "available",
                        "quality_flags": ["share_basis_noncomparable"],
                        "citation": {
                            "citation_id": "sec:revenue:2024",
                            "source_url": "https://www.sec.gov/2024-10k",
                        },
                    },
                    {
                        "fiscal_year": 2025,
                        "period_end": "2025-09-27",
                        "value": 416_161_000_000,
                        "unit": "USD",
                        "status": "available",
                        "quality_flags": [],
                        "citation": {
                            "citation_id": "sec:revenue:2025",
                            "source_url": "https://www.sec.gov/2025-10k",
                        },
                    },
                ],
            }
        ],
        "derived_series": [
            {
                "metric_id": "gross_margin",
                "label": "Gross margin",
                "definition": "gross_profit / revenue",
                "unit": "ratio",
                "observations": [
                    {
                        "fiscal_year": 2025,
                        "period_end": "2025-09-27",
                        "value": 0.46,
                        "unit": "ratio",
                        "status": "available",
                        "formula_version": "formula.v1",
                        "components": {"revenue": "sec:revenue:2025"},
                    }
                ],
            }
        ],
    }
    packet = _scope(snapshot, "core")
    fundamentals = packet["evidence"]["fundamentals"]
    assert fundamentals["series_basis"] == "latest_restated"
    assert fundamentals["annual_trends"]
    revenue = next(
        series for series in fundamentals["annual_trends"] if series["metric_id"] == "revenue"
    )
    assert [item["fiscal_year"] for item in revenue["observations"]] == [2025]
    assert revenue["observations"][0]["display_value"] == "$416.2B"
    assert "metric:fundamentals.revenue.2025" in packet["allowed_citations"]
    assert packet["citations"]["metric:fundamentals.revenue.2025"]["url"] == (
        "https://www.sec.gov/2025-10k"
    )
    assert packet["citations"]["metric:fundamentals.gross_margin.2025"]["url"] == (
        "https://www.sec.gov/2025-10k"
    )
    gross_margin = next(
        series
        for series in fundamentals["annual_trends"]
        if series["metric_id"] == "gross_margin"
    )
    assert gross_margin["observations"][0]["display_value"] == "46.0%"
    assert gross_margin["observations"][0]["source_citations"] == ["sec:revenue:2025"]
    assert gross_margin["observations"][0]["formula_version"] == "formula.v1"
    assert "sec:revenue:2025" in packet["allowed_citations"]
    assert packet["citations"]["sec:revenue:2025"]["url"] == (
        "https://www.sec.gov/2025-10k"
    )
    assert revenue["coverage_status"] == "partial"
    assert "416161000000" in packet["allowed_number_literals"] or "416,161,000,000" in str(
        packet
    )
    assert "$416.2B" in packet["allowed_number_literals"]
    assert "46.0%" in packet["allowed_number_literals"]


def test_every_scope_is_offered_with_a_bilingual_label() -> None:
    offered = evidence_scopes()
    assert [scope["id"] for scope in offered] == list(SCOPE_SECTIONS)
    for scope in offered:
        assert scope["label"] and scope["label_zh"]
        assert scope["description"] and scope["description_zh"]


def test_scopes_carry_exactly_the_sections_they_promise() -> None:
    scopes = build_ask_evidence(_snapshot())["scopes"]

    assert "company_headlines" not in scopes["core"]["evidence"]
    assert "market_headlines" not in scopes["core"]["evidence"]
    assert "company_headlines" in scopes["company"]["evidence"]
    assert "market_headlines" not in scopes["company"]["evidence"]
    assert "market_headlines" in scopes["market"]["evidence"]
    assert "company_headlines" not in scopes["market"]["evidence"]
    assert "company_headlines" in scopes["all"]["evidence"]
    assert "market_headlines" in scopes["all"]["evidence"]

    # Core survives in every scope: the point of the selector is what gets
    # added, never what gets taken away from the source-backed foundation.
    for scope in scopes.values():
        assert scope["evidence"]["latest_filing"]["accession"] == "0001"
        assert scope["evidence"]["historical_performance"]["asset"] == "ABC"


def test_a_narrow_scope_cannot_validate_a_wider_scopes_evidence() -> None:
    """The property the whole mechanism exists for.

    The validator accepts a claim only if its citations and numbers appear in
    the allow-lists. Those lists are built per scope from the sections that
    scope actually contains, so a model answering in `core` cannot cite a
    headline it was never shown, even though the headline exists in the build.
    """
    scopes = build_ask_evidence(_snapshot())["scopes"]

    assert "news:market#headline" in scopes["market"]["allowed_citations"]
    assert "news:market#headline" not in scopes["core"]["allowed_citations"]
    assert "news:market#headline" not in scopes["company"]["allowed_citations"]

    assert "news:abc#headline" in scopes["company"]["allowed_citations"]
    assert "news:abc#headline" not in scopes["core"]["allowed_citations"]
    assert "news:abc#headline" not in scopes["market"]["allowed_citations"]

    # A number reachable only through the market headline is allowed only where
    # that headline was actually sent.
    assert "4.25%" in scopes["market"]["allowed_number_literals"]
    assert "4.25%" in scopes["all"]["allowed_number_literals"]
    assert "4.25%" not in scopes["core"]["allowed_number_literals"]
    assert "4.25%" not in scopes["company"]["allowed_number_literals"]


def test_core_allow_lists_are_a_subset_of_every_wider_scope() -> None:
    scopes = build_ask_evidence(_snapshot())["scopes"]
    core = set(scopes["core"]["allowed_citations"])
    for name in ("company", "market", "all"):
        assert core <= set(scopes[name]["allowed_citations"])


def test_a_narrowed_scope_tells_the_model_it_is_narrowed() -> None:
    scopes = build_ask_evidence(_snapshot())["scopes"]
    for name in ("core", "company", "market"):
        limits = " ".join(scopes[name]["evidence"]["interpretation_limits"])
        assert "narrowed evidence scope" in limits
    assert "narrowed evidence scope" not in " ".join(
        scopes["all"]["evidence"]["interpretation_limits"])


def test_market_headlines_carry_a_do_not_attribute_limit() -> None:
    limits = " ".join(
        build_ask_evidence(_snapshot())["scopes"]["market"]
        ["evidence"]["interpretation_limits"])
    assert "not this company" in limits


def test_an_empty_optional_section_still_declares_itself() -> None:
    """Silence invites the model to fall back on memory.

    A scope with no headlines available must still say so, rather than omitting
    the key and leaving the absence indistinguishable from an oversight.
    """
    snapshot = _snapshot()
    snapshot["headlines"] = []
    snapshot["market_headlines"] = []
    scopes = build_ask_evidence(snapshot)["scopes"]

    assert scopes["company"]["evidence"]["company_headlines"] == []
    limits = " ".join(scopes["company"]["evidence"]["interpretation_limits"])
    assert "No company headlines are available" in limits
