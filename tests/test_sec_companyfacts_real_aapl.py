"""Golden checks against an unmodified slice of the real SEC AAPL CompanyFacts payload."""

from __future__ import annotations

import json
from pathlib import Path

from company_lens.fundamentals import build_fundamentals_section
from company_lens.fundamentals.normalize import fiscal_year_from_period_end

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sec"


def test_real_aapl_companyfacts_slice_golden_revenue_and_aligned_derived() -> None:
    facts = json.loads((FIXTURES / "aapl_companyfacts_real_slice.json").read_text())
    # Fixture must remain an unmodified concept slice of the live SEC payload.
    raw_revenue = facts["facts"]["us-gaap"][
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    ]["units"]["USD"]
    assert any(
        row.get("end") == "2025-09-27" and row.get("val") == 416_161_000_000
        for row in raw_revenue
    )

    section = build_fundamentals_section(facts, ticker="AAPL", requested_years=10)
    assert section.status == "available"
    assert section.series_basis == "latest_restated"

    revenue = next(series for series in section.reported_series if series.metric_id == "revenue")
    fy2025 = next(obs for obs in revenue.observations if obs.fiscal_year == 2025)
    assert fy2025.value == 416_161_000_000
    assert fy2025.period_end == "2025-09-27"
    assert fy2025.fiscal_year == fiscal_year_from_period_end(fy2025.period_end)
    assert fy2025.citation.document_fy == 2025
    assert fy2025.citation.document_fp == "FY"

    for series in section.reported_series:
        for observation in series.observations:
            assert observation.fiscal_year == fiscal_year_from_period_end(
                observation.period_end
            )
            if observation.citation.document_fy is not None:
                # Document fy may disagree with the economic period (comparatives).
                assert observation.citation.fiscal_year == observation.fiscal_year

    shares = next(
        series for series in section.reported_series if series.metric_id == "diluted_shares"
    )
    as_reported_shares = next(
        series
        for series in section.as_reported_series
        if series.metric_id == "diluted_shares"
    )
    restated_2019 = next(obs for obs in shares.observations if obs.fiscal_year == 2019)
    first_2019 = next(
        obs for obs in as_reported_shares.observations if obs.fiscal_year == 2019
    )
    restated_2020 = next(obs for obs in shares.observations if obs.fiscal_year == 2020)
    assert first_2019.value == 4_648_913_000
    assert restated_2019.value == 18_595_651_000
    assert restated_2020.value == 17_528_214_000
    assert "share_basis_noncomparable" in next(
        obs for obs in shares.observations if obs.fiscal_year == 2017
    ).quality_flags
    assert "share_basis_discontinuity" in next(
        obs for obs in shares.observations if obs.fiscal_year == 2018
    ).quality_flags
    share_change = next(
        series
        for series in section.derived_series
        if series.metric_id == "diluted_share_change"
    )
    change_2020 = next(obs for obs in share_change.observations if obs.fiscal_year == 2020)
    change_2018 = next(obs for obs in share_change.observations if obs.fiscal_year == 2018)
    assert change_2018.status == "not_meaningful"
    assert change_2018.value is None
    assert "share_basis_discontinuity" in change_2018.quality_flags
    assert change_2020.status == "available"
    assert change_2020.value is not None
    assert abs(change_2020.value) < 0.2

    fcf_per_share = next(
        series for series in section.derived_series if series.metric_id == "fcf_per_share"
    )
    assert next(
        obs for obs in fcf_per_share.observations if obs.fiscal_year == 2017
    ).status == "not_meaningful"
    assert next(
        obs for obs in fcf_per_share.observations if obs.fiscal_year == 2018
    ).status == "available"

    revenue_as_reported = next(
        series for series in section.as_reported_series if series.metric_id == "revenue"
    )
    first_known_2017 = next(
        obs for obs in revenue_as_reported.observations if obs.fiscal_year == 2017
    )
    assert first_known_2017.citation.concept == "SalesRevenueNet"
    assert first_known_2017.citation.filed_date == "2017-11-03"

    gross_margin = next(
        series for series in section.derived_series if series.metric_id == "gross_margin"
    )
    free_cash_flow = next(
        series for series in section.derived_series if series.metric_id == "free_cash_flow"
    )
    gm_2025 = next(obs for obs in gross_margin.observations if obs.fiscal_year == 2025)
    fcf_2025 = next(obs for obs in free_cash_flow.observations if obs.fiscal_year == 2025)
    share_change_2025 = next(
        obs for obs in share_change.observations if obs.fiscal_year == 2025
    )
    assert gm_2025.status == "available"
    assert fcf_2025.status == "available"
    assert share_change_2025.status == "available"
    assert gm_2025.period_end == fy2025.period_end == "2025-09-27"
    assert fcf_2025.period_end == fy2025.period_end
    assert share_change_2025.period_end == fy2025.period_end
    assert gm_2025.fiscal_year == fcf_2025.fiscal_year == share_change_2025.fiscal_year == 2025
