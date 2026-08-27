"""Derived fundamental formulas against explicit observations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from company_lens.contracts import (
    FundamentalCitation,
    FundamentalObservation,
    FundamentalSeries,
)
from company_lens.fundamentals.metrics import FORMULA_VERSION, build_derived_metrics
from company_lens.fundamentals.normalize import normalize_annual_fundamentals

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sec"


def _citation(metric_id: str, year: int, value: float, unit: str = "USD") -> FundamentalCitation:
    return FundamentalCitation(
        citation_id=f"us-gaap:{metric_id}:{year}:accn",
        taxonomy="us-gaap",
        concept=metric_id,
        accession=f"0001-{year}",
        form="10-K",
        source_url=f"https://www.sec.gov/Archives/edgar/data/1/{year}.htm",
        period_start=f"{year - 1}-10-01",
        period_end=f"{year}-09-30",
        filed_date=f"{year}-11-01",
        accepted_at=f"{year}-11-01T18:00:00-04:00",
        fiscal_year=year,
        fiscal_period="FY",
        unit=unit,
    )


def _obs(metric_id: str, year: int, value: float, unit: str = "USD") -> FundamentalObservation:
    citation = _citation(metric_id, year, value, unit)
    return FundamentalObservation(
        metric_id=metric_id,
        value=value,
        unit=unit,
        period_start=citation.period_start,
        period_end=citation.period_end,
        fiscal_year=year,
        knowledge_at=citation.accepted_at or citation.filed_date,
        citation=citation,
    )


def _series(metric_id: str, values: dict[int, float], unit: str = "USD") -> FundamentalSeries:
    return FundamentalSeries(
        metric_id=metric_id,
        label=metric_id,
        definition=metric_id,
        expected_unit=unit,
        observations=tuple(
            _obs(metric_id, year, value, unit) for year, value in sorted(values.items())
        ),
        concept_priority=(metric_id,),
        coverage_status="complete",
    )


def _by_id(series_list, metric_id: str):
    return next(series for series in series_list if series.metric_id == metric_id)


def test_margin_and_fcf_formulas_use_absolute_capex() -> None:
    derived = build_derived_metrics(
        (
            _series("revenue", {2024: 100}),
            _series("gross_profit", {2024: 40}),
            _series("operating_income", {2024: 25}),
            _series("net_income", {2024: 20}),
            _series("operating_cash_flow", {2024: 30}),
            _series("capex", {2024: 8}),
            _series("diluted_shares", {2024: 10}, unit="shares"),
            _series("total_assets", {2023: 80, 2024: 100}),
        )
    )
    gross_margin = _by_id(derived, "gross_margin").observations[-1]
    operating_margin = _by_id(derived, "operating_margin").observations[-1]
    fcf = _by_id(derived, "free_cash_flow").observations[-1]
    conversion = _by_id(derived, "fcf_conversion").observations[-1]
    roa = _by_id(derived, "roa").observations[-1]
    gp_assets = _by_id(derived, "gross_profit_to_assets").observations[-1]
    rev_share = _by_id(derived, "revenue_per_share").observations[-1]
    fcf_share = _by_id(derived, "fcf_per_share").observations[-1]

    assert gross_margin.status == "available"
    assert gross_margin.value == pytest.approx(0.4)
    assert operating_margin.value == pytest.approx(0.25)
    assert fcf.value == pytest.approx(22)
    assert conversion.value == pytest.approx(22 / 20)
    assert roa.value == pytest.approx(20 / 90)
    assert gp_assets.value == pytest.approx(40 / 90)
    assert rev_share.value == pytest.approx(10)
    assert fcf_share.value == pytest.approx(2.2)
    assert gross_margin.formula_version == FORMULA_VERSION
    assert gross_margin.components["revenue"] == "us-gaap:revenue:2024:accn"
    assert fcf.components["capex"] == "us-gaap:capex:2024:accn"


def test_negative_capex_still_subtracts_payment_magnitude() -> None:
    derived = build_derived_metrics(
        (
            _series("operating_cash_flow", {2024: 30}),
            _series("capex", {2024: -8}),
        )
    )
    fcf = _by_id(derived, "free_cash_flow").observations[-1]
    assert fcf.value == pytest.approx(22)


def test_missing_denominator_is_missing_not_zero() -> None:
    derived = build_derived_metrics(
        (
            _series("gross_profit", {2024: 40}),
            _series("operating_cash_flow", {2024: 30}),
            _series("capex", {2024: 8}),
        )
    )
    gross_margin = _by_id(derived, "gross_margin").observations[-1]
    conversion = _by_id(derived, "fcf_conversion").observations[-1]
    assert gross_margin.status == "missing_input"
    assert gross_margin.value is None
    assert conversion.status == "missing_input"
    assert conversion.value is None


def test_zero_denominator_is_not_meaningful() -> None:
    derived = build_derived_metrics(
        (
            _series("revenue", {2024: 0}),
            _series("gross_profit", {2024: 10}),
            _series("net_income", {2024: 0}),
            _series("operating_cash_flow", {2024: 5}),
            _series("diluted_shares", {2023: 0, 2024: 10}, unit="shares"),
        )
    )
    assert _by_id(derived, "gross_margin").observations[-1].status == "not_meaningful"
    assert _by_id(derived, "ocf_to_net_income").observations[-1].status == "not_meaningful"
    assert _by_id(derived, "diluted_share_change").observations[-1].status == "not_meaningful"
    assert _by_id(derived, "gross_margin").observations[-1].value is None


def test_share_change_and_five_year_cagr() -> None:
    revenue = {year: float(100 * (1.1 ** (year - 2016))) for year in range(2016, 2022)}
    derived = build_derived_metrics(
        (
            _series("revenue", revenue),
            _series("operating_income", {year: value * 0.3 for year, value in revenue.items()}),
            _series("operating_cash_flow", {year: value * 0.4 for year, value in revenue.items()}),
            _series("capex", dict.fromkeys(revenue, 10)),
            _series("diluted_shares", {2020: 110, 2021: 100}, unit="shares"),
        )
    )
    share_change = next(
        obs
        for obs in _by_id(derived, "diluted_share_change").observations
        if obs.fiscal_year == 2021
    )
    assert share_change.value == pytest.approx(100 / 110 - 1)
    cagr_2021 = next(
        obs for obs in _by_id(derived, "revenue_cagr_5y").observations if obs.fiscal_year == 2021
    )
    cagr_2018 = next(
        obs for obs in _by_id(derived, "revenue_cagr_5y").observations if obs.fiscal_year == 2018
    )
    assert cagr_2021.status == "available"
    assert cagr_2021.value == pytest.approx((revenue[2021] / revenue[2016]) ** 0.2 - 1)
    assert cagr_2018.status == "missing_input"
    assert cagr_2018.value is None
    fcf_cagr = next(
        obs for obs in _by_id(derived, "fcf_cagr_5y").observations if obs.fiscal_year == 2021
    )
    assert fcf_cagr.status == "available"
    assert fcf_cagr.components["start_operating_cash_flow"]
    assert fcf_cagr.components["end_capex"]


def test_negative_cagr_endpoints_are_not_meaningful() -> None:
    derived = build_derived_metrics(
        (
            _series("revenue", {2016: -10, 2021: 20}),
            _series("operating_cash_flow", {2016: 5, 2021: 8}),
            _series("capex", {2016: 10, 2021: 1}),
        )
    )
    revenue_cagr = next(
        obs for obs in _by_id(derived, "revenue_cagr_5y").observations if obs.fiscal_year == 2021
    )
    fcf_cagr = next(
        obs for obs in _by_id(derived, "fcf_cagr_5y").observations if obs.fiscal_year == 2021
    )
    assert revenue_cagr.status == "not_meaningful"
    # 2016 FCF = 5 - 10 = -5, so CAGR is not meaningful
    assert fcf_cagr.status == "not_meaningful"
    assert fcf_cagr.value is None


def test_aapl_fixture_metrics_carry_citations() -> None:
    facts = json.loads((FIXTURES / "aapl_companyfacts_2016_2025.json").read_text())
    submissions = json.loads((FIXTURES / "aapl_submissions_fundamentals.json").read_text())
    reported = normalize_annual_fundamentals(
        facts, ticker="AAPL", submissions=submissions
    ).reported_series
    derived = build_derived_metrics(reported)
    fy2025 = next(
        obs for obs in _by_id(derived, "gross_margin").observations if obs.fiscal_year == 2025
    )
    revenue = next(series for series in reported if series.metric_id == "revenue")
    fy2025_rev = next(obs for obs in revenue.observations if obs.fiscal_year == 2025)
    assert fy2025.status == "available"
    assert fy2025.components["revenue"] == fy2025_rev.citation.citation_id
    fcf = next(
        obs for obs in _by_id(derived, "free_cash_flow").observations if obs.fiscal_year == 2025
    )
    assert fcf.value == pytest.approx(125_400_000_000 - 10_200_000_000)
