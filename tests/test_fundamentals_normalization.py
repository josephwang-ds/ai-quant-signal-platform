"""Annual Company Facts normalization against the reduced AAPL fixture."""

from __future__ import annotations

import json
from pathlib import Path

from company_lens.fundamentals import build_fundamentals_section, normalize_annual_fundamentals
from company_lens.fundamentals.normalize import fiscal_year_from_period_end

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sec"


def _facts() -> dict:
    return json.loads((FIXTURES / "aapl_companyfacts_2016_2025.json").read_text())


def _submissions() -> dict:
    return json.loads((FIXTURES / "aapl_submissions_fundamentals.json").read_text())


def test_normalizes_ten_annual_periods_in_fiscal_year_order() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions(), requested_years=10
    )
    years = [period["fiscal_year"] for period in result.annual_periods]
    assert years == list(range(2016, 2026))
    revenue = next(series for series in result.reported_series if series.metric_id == "revenue")
    assert [obs.fiscal_year for obs in revenue.observations] == years
    assert revenue.coverage_status == "complete"
    assert all(
        obs.fiscal_year == fiscal_year_from_period_end(obs.period_end)
        for obs in revenue.observations
    )


def test_latest_restated_keeps_later_10k_and_preserves_as_reported() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    revenue = next(series for series in result.reported_series if series.metric_id == "revenue")
    as_reported = next(
        series for series in result.as_reported_series if series.metric_id == "revenue"
    )
    fy2018 = next(obs for obs in revenue.observations if obs.fiscal_year == 2018)
    first_known = next(obs for obs in as_reported.observations if obs.fiscal_year == 2018)
    assert fy2018.value == 266_000_000_000
    assert first_known.value == 265_595_000_000
    assert "restated_value" in fy2018.quality_flags
    assert fy2018.citation.accession == "0000320193-19-000010"
    assert first_known.citation.accession == "0000320193-18-000145"
    restated = [
        row
        for row in result.coverage["restated_value"]
        if row["metric_id"] == "revenue" and row["fiscal_year"] == 2018
    ]
    assert restated[0]["later_value"] == 266_000_000_000
    assert restated[0]["original_value"] == 265_595_000_000


def test_concept_priority_flags_tag_substitution_on_older_alias() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    revenue = next(series for series in result.reported_series if series.metric_id == "revenue")
    fy2016 = next(obs for obs in revenue.observations if obs.fiscal_year == 2016)
    fy2017 = next(obs for obs in revenue.observations if obs.fiscal_year == 2017)
    assert fy2016.citation.concept == "Revenues"
    assert "tag_substitution" in fy2016.quality_flags
    assert fy2017.citation.concept == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert "tag_substitution" not in fy2017.quality_flags


def test_duplicate_context_and_unit_duration_flags() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    ocf = next(
        series
        for series in result.reported_series
        if series.metric_id == "operating_cash_flow"
    )
    fy2020 = next(obs for obs in ocf.observations if obs.fiscal_year == 2020)
    assert "duplicate_context" in fy2020.quality_flags
    assert any(row["metric_id"] == "gross_profit" for row in result.coverage["unexpected_unit"])
    assert any(row["metric_id"] == "net_income" for row in result.coverage["duration_outlier"])


def test_submissions_join_builds_primary_document_url() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    revenue = next(series for series in result.reported_series if series.metric_id == "revenue")
    fy2025 = next(obs for obs in revenue.observations if obs.fiscal_year == 2025)
    assert fy2025.citation.source_url.endswith("/aapl-20250927x10k.htm")
    assert fy2025.citation.accepted_at is not None
    assert "acceptance_unresolved" not in fy2025.quality_flags
    assert fy2025.knowledge_at == fy2025.citation.accepted_at


def test_missing_submissions_uses_filed_date_and_viewer_url() -> None:
    result = normalize_annual_fundamentals(_facts(), ticker="aapl")
    revenue = next(series for series in result.reported_series if series.metric_id == "revenue")
    fy2025 = next(obs for obs in revenue.observations if obs.fiscal_year == 2025)
    assert "acceptance_unresolved" in fy2025.quality_flags
    assert fy2025.knowledge_at == fy2025.citation.filed_date
    assert "cgi-bin/viewer" in fy2025.citation.source_url
    assert fy2025.citation.source_url.endswith("xbrl_type=v")


def test_instant_facts_have_no_duration_start() -> None:
    result = normalize_annual_fundamentals(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    assets = next(
        series for series in result.reported_series if series.metric_id == "total_assets"
    )
    assert all(obs.period_start is None for obs in assets.observations)
    shares = next(
        series for series in result.reported_series if series.metric_id == "diluted_shares"
    )
    assert shares.expected_unit == "shares"
    assert all(obs.unit == "shares" for obs in shares.observations)


def test_builder_marks_available_and_is_deterministic() -> None:
    first = build_fundamentals_section(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    second = build_fundamentals_section(
        _facts(), ticker="AAPL", submissions=_submissions()
    )
    assert first.status == "available"
    assert first.schema_version == "company-lens.fundamentals.v1"
    assert first.template == "general_operating_company"
    assert first.series_basis == "latest_restated"
    assert first.as_reported_series
    assert [period["fiscal_year"] for period in first.annual_periods] == list(range(2016, 2026))
    assert [series.metric_id for series in first.reported_series] == [
        series.metric_id for series in second.reported_series
    ]
    revenue = next(series for series in first.reported_series if series.metric_id == "revenue")
    assert [obs.value for obs in revenue.observations] == [
        obs.value
        for obs in next(
            series for series in second.reported_series if series.metric_id == "revenue"
        ).observations
    ]
