from __future__ import annotations

from company_lens.web.ask import ASK_EVIDENCE_VERSION, build_ask_evidence


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
            {
                "headline": "Rates are unchanged",
                "publisher": "Market Wire",
                "published_at": "2026-08-24T09:00:00+00:00",
                "url": "https://example.com/market",
                "source_type": "market_news",
                "citation": "news:market#headline",
            },
        ],
    }


def test_ask_evidence_is_compact_company_specific_and_citation_bounded() -> None:
    packet = build_ask_evidence(_snapshot())

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
