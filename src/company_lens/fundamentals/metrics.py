"""Derived fundamental metrics with explicit missing/not-meaningful states."""

from __future__ import annotations

from dataclasses import dataclass

from company_lens.contracts import (
    DerivedMetricObservation,
    DerivedMetricSeries,
    FundamentalObservation,
    FundamentalSeries,
)

FORMULA_VERSION = "company-lens.fundamentals.metrics.v1"


@dataclass(frozen=True)
class _DerivedSpec:
    metric_id: str
    label: str
    definition: str
    unit: str


DERIVED_SPECS: tuple[_DerivedSpec, ...] = (
    _DerivedSpec("gross_margin", "Gross margin", "gross_profit / revenue", "ratio"),
    _DerivedSpec(
        "operating_margin", "Operating margin", "operating_income / revenue", "ratio"
    ),
    _DerivedSpec(
        "free_cash_flow",
        "Free cash flow",
        "operating_cash_flow - abs(capex) for payment-style capex",
        "USD",
    ),
    _DerivedSpec(
        "ocf_to_net_income",
        "Operating cash flow / net income",
        "operating_cash_flow / net income",
        "ratio",
    ),
    _DerivedSpec(
        "fcf_conversion",
        "FCF conversion",
        "free_cash_flow / net income",
        "ratio",
    ),
    _DerivedSpec(
        "gross_profit_to_assets",
        "Gross profit / average assets",
        "gross_profit / average(total_assets_t, total_assets_t-1)",
        "ratio",
    ),
    _DerivedSpec(
        "roa",
        "Return on assets",
        "net_income / average(total_assets_t, total_assets_t-1)",
        "ratio",
    ),
    _DerivedSpec(
        "diluted_share_change",
        "Diluted share change",
        "diluted_shares_t / diluted_shares_t-1 - 1",
        "ratio",
    ),
    _DerivedSpec(
        "revenue_cagr_5y",
        "Revenue 5Y CAGR",
        "compound annual growth of revenue over a 5-year span",
        "ratio",
    ),
    _DerivedSpec(
        "operating_income_cagr_5y",
        "Operating income 5Y CAGR",
        "compound annual growth of operating income over a 5-year span",
        "ratio",
    ),
    _DerivedSpec(
        "fcf_cagr_5y",
        "Free cash flow 5Y CAGR",
        "compound annual growth of free cash flow over a 5-year span",
        "ratio",
    ),
    _DerivedSpec(
        "revenue_per_share",
        "Revenue per diluted share",
        "revenue / diluted_shares",
        "USD/shares",
    ),
    _DerivedSpec(
        "fcf_per_share",
        "Free cash flow per diluted share",
        "free_cash_flow / diluted_shares",
        "USD/shares",
    ),
)


def build_derived_metrics(
    reported_series: tuple[FundamentalSeries, ...] | list[FundamentalSeries],
) -> tuple[DerivedMetricSeries, ...]:
    by_id = {series.metric_id: _index_observations(series) for series in reported_series}
    years = sorted(
        {
            observation.fiscal_year
            for series in reported_series
            for observation in series.observations
        }
    )
    fcf_by_year: dict[int, DerivedMetricObservation] = {}
    built: dict[str, list[DerivedMetricObservation]] = {
        spec.metric_id: [] for spec in DERIVED_SPECS
    }

    for year in years:
        revenue = by_id.get("revenue", {}).get(year)
        gross_profit = by_id.get("gross_profit", {}).get(year)
        operating_income = by_id.get("operating_income", {}).get(year)
        net_income = by_id.get("net_income", {}).get(year)
        ocf = by_id.get("operating_cash_flow", {}).get(year)
        capex = by_id.get("capex", {}).get(year)
        shares = by_id.get("diluted_shares", {}).get(year)
        assets = by_id.get("total_assets", {}).get(year)
        prior_assets = by_id.get("total_assets", {}).get(year - 1)
        prior_shares = by_id.get("diluted_shares", {}).get(year - 1)

        built["gross_margin"].append(
            _ratio_obs(
                "gross_margin",
                year,
                gross_profit,
                revenue,
                numerator_key="gross_profit",
                denominator_key="revenue",
            )
        )
        built["operating_margin"].append(
            _ratio_obs(
                "operating_margin",
                year,
                operating_income,
                revenue,
                numerator_key="operating_income",
                denominator_key="revenue",
            )
        )

        fcf_obs = _free_cash_flow(year, ocf, capex)
        fcf_by_year[year] = fcf_obs
        built["free_cash_flow"].append(fcf_obs)

        built["ocf_to_net_income"].append(
            _ratio_obs(
                "ocf_to_net_income",
                year,
                ocf,
                net_income,
                numerator_key="operating_cash_flow",
                denominator_key="net_income",
            )
        )
        built["fcf_conversion"].append(
            _derived_over_reported(
                "fcf_conversion",
                year,
                fcf_obs,
                net_income,
                denominator_key="net_income",
            )
        )
        built["gross_profit_to_assets"].append(
            _average_assets_ratio(
                "gross_profit_to_assets",
                year,
                gross_profit,
                assets,
                prior_assets,
                numerator_key="gross_profit",
            )
        )
        built["roa"].append(
            _average_assets_ratio(
                "roa",
                year,
                net_income,
                assets,
                prior_assets,
                numerator_key="net_income",
            )
        )
        built["diluted_share_change"].append(
            _share_change(year, shares, prior_shares)
        )
        built["revenue_per_share"].append(
            _ratio_obs(
                "revenue_per_share",
                year,
                revenue,
                shares,
                numerator_key="revenue",
                denominator_key="diluted_shares",
                unit="USD/shares",
            )
        )
        built["fcf_per_share"].append(
            _derived_over_reported(
                "fcf_per_share",
                year,
                fcf_obs,
                shares,
                denominator_key="diluted_shares",
                unit="USD/shares",
            )
        )

    for metric_id, source_id in (
        ("revenue_cagr_5y", "revenue"),
        ("operating_income_cagr_5y", "operating_income"),
    ):
        built[metric_id] = _cagr_series(metric_id, by_id.get(source_id, {}), years)
    built["fcf_cagr_5y"] = _cagr_from_derived("fcf_cagr_5y", fcf_by_year, years)

    return tuple(
        DerivedMetricSeries(
            metric_id=spec.metric_id,
            label=spec.label,
            definition=spec.definition,
            unit=spec.unit,
            observations=tuple(built[spec.metric_id]),
        )
        for spec in DERIVED_SPECS
    )


def _index_observations(
    series: FundamentalSeries,
) -> dict[int, FundamentalObservation]:
    return {observation.fiscal_year: observation for observation in series.observations}


def _period_end(observation: FundamentalObservation | None, year: int) -> str:
    if observation is not None:
        return observation.period_end
    return f"{year}-09-30"


def _citation_id(observation: FundamentalObservation | None) -> str | None:
    return None if observation is None else observation.citation.citation_id


def _same_fiscal_period(
    left: FundamentalObservation | None,
    right: FundamentalObservation | None,
) -> bool:
    if left is None or right is None:
        return True
    return left.period_end == right.period_end and left.fiscal_year == right.fiscal_year


def _ratio_obs(
    metric_id: str,
    year: int,
    numerator: FundamentalObservation | None,
    denominator: FundamentalObservation | None,
    *,
    numerator_key: str,
    denominator_key: str,
    unit: str = "ratio",
) -> DerivedMetricObservation:
    components = {
        numerator_key: _citation_id(numerator),
        denominator_key: _citation_id(denominator),
    }
    period_end = _period_end(numerator or denominator, year)
    if numerator is None or denominator is None or not _same_fiscal_period(
        numerator, denominator
    ):
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="missing_input",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    if denominator_key == "diluted_shares" and _share_basis_noncomparable(denominator):
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
            quality_flags=("share_basis_noncomparable",),
        )
    if denominator.value == 0:
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    return DerivedMetricObservation(
        metric_id=metric_id,
        value=numerator.value / denominator.value,
        unit=unit,
        period_end=period_end,
        fiscal_year=year,
        status="available",
        formula_version=FORMULA_VERSION,
        components=components,
    )


def _free_cash_flow(
    year: int,
    ocf: FundamentalObservation | None,
    capex: FundamentalObservation | None,
) -> DerivedMetricObservation:
    components = {
        "operating_cash_flow": _citation_id(ocf),
        "capex": _citation_id(capex),
    }
    period_end = _period_end(ocf or capex, year)
    if ocf is None or capex is None or not _same_fiscal_period(ocf, capex):
        return DerivedMetricObservation(
            metric_id="free_cash_flow",
            value=None,
            unit="USD",
            period_end=period_end,
            fiscal_year=year,
            status="missing_input",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    # PaymentsToAcquire* are typically positive payment magnitudes in Company Facts.
    value = ocf.value - abs(capex.value)
    return DerivedMetricObservation(
        metric_id="free_cash_flow",
        value=value,
        unit="USD",
        period_end=period_end,
        fiscal_year=year,
        status="available",
        formula_version=FORMULA_VERSION,
        components=components,
    )


def _derived_over_reported(
    metric_id: str,
    year: int,
    derived: DerivedMetricObservation,
    denominator: FundamentalObservation | None,
    *,
    denominator_key: str,
    unit: str = "ratio",
) -> DerivedMetricObservation:
    components = {
        "operating_cash_flow": derived.components.get("operating_cash_flow"),
        "capex": derived.components.get("capex"),
        denominator_key: _citation_id(denominator),
    }
    period_end = derived.period_end if derived.period_end else _period_end(denominator, year)
    period_mismatch = (
        denominator is not None and derived.period_end != denominator.period_end
    )
    if derived.status != "available" or denominator is None or period_mismatch:
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="missing_input",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    if denominator_key == "diluted_shares" and _share_basis_noncomparable(denominator):
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
            quality_flags=("share_basis_noncomparable",),
        )
    if denominator.value == 0:
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit=unit,
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    assert derived.value is not None
    return DerivedMetricObservation(
        metric_id=metric_id,
        value=derived.value / denominator.value,
        unit=unit,
        period_end=period_end,
        fiscal_year=year,
        status="available",
        formula_version=FORMULA_VERSION,
        components=components,
    )


def _average_assets_ratio(
    metric_id: str,
    year: int,
    numerator: FundamentalObservation | None,
    assets: FundamentalObservation | None,
    prior_assets: FundamentalObservation | None,
    *,
    numerator_key: str,
) -> DerivedMetricObservation:
    components = {
        numerator_key: _citation_id(numerator),
        "total_assets": _citation_id(assets),
        "total_assets_prior": _citation_id(prior_assets),
    }
    period_end = _period_end(numerator or assets, year)
    if numerator is None or assets is None or prior_assets is None:
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit="ratio",
            period_end=period_end,
            fiscal_year=year,
            status="missing_input",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    average_assets = (assets.value + prior_assets.value) / 2.0
    if average_assets == 0:
        return DerivedMetricObservation(
            metric_id=metric_id,
            value=None,
            unit="ratio",
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    return DerivedMetricObservation(
        metric_id=metric_id,
        value=numerator.value / average_assets,
        unit="ratio",
        period_end=period_end,
        fiscal_year=year,
        status="available",
        formula_version=FORMULA_VERSION,
        components=components,
    )


def _share_change(
    year: int,
    shares: FundamentalObservation | None,
    prior_shares: FundamentalObservation | None,
) -> DerivedMetricObservation:
    components = {
        "diluted_shares": _citation_id(shares),
        "diluted_shares_prior": _citation_id(prior_shares),
    }
    period_end = _period_end(shares, year)
    if shares is None or prior_shares is None:
        return DerivedMetricObservation(
            metric_id="diluted_share_change",
            value=None,
            unit="ratio",
            period_end=period_end,
            fiscal_year=year,
            status="missing_input",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    if "share_basis_discontinuity" in shares.quality_flags:
        return DerivedMetricObservation(
            metric_id="diluted_share_change",
            value=None,
            unit="ratio",
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
            quality_flags=("share_basis_discontinuity",),
        )
    if prior_shares.value == 0:
        return DerivedMetricObservation(
            metric_id="diluted_share_change",
            value=None,
            unit="ratio",
            period_end=period_end,
            fiscal_year=year,
            status="not_meaningful",
            formula_version=FORMULA_VERSION,
            components=components,
        )
    return DerivedMetricObservation(
        metric_id="diluted_share_change",
        value=(shares.value / prior_shares.value) - 1.0,
        unit="ratio",
        period_end=period_end,
        fiscal_year=year,
        status="available",
        formula_version=FORMULA_VERSION,
        components=components,
    )


def _share_basis_noncomparable(observation: FundamentalObservation) -> bool:
    return "share_basis_noncomparable" in observation.quality_flags


def _cagr_series(
    metric_id: str,
    by_year: dict[int, FundamentalObservation],
    years: list[int],
) -> list[DerivedMetricObservation]:
    observations: list[DerivedMetricObservation] = []
    for year in years:
        start_year = year - 5
        end_obs = by_year.get(year)
        start_obs = by_year.get(start_year)
        components = {
            "start": _citation_id(start_obs),
            "end": _citation_id(end_obs),
        }
        period_end = _period_end(end_obs, year)
        if end_obs is None or start_obs is None:
            observations.append(
                DerivedMetricObservation(
                    metric_id=metric_id,
                    value=None,
                    unit="ratio",
                    period_end=period_end,
                    fiscal_year=year,
                    status="missing_input",
                    formula_version=FORMULA_VERSION,
                    components=components,
                )
            )
            continue
        value = _cagr(start_obs.value, end_obs.value, periods=5)
        if value is None:
            observations.append(
                DerivedMetricObservation(
                    metric_id=metric_id,
                    value=None,
                    unit="ratio",
                    period_end=period_end,
                    fiscal_year=year,
                    status="not_meaningful",
                    formula_version=FORMULA_VERSION,
                    components=components,
                )
            )
        else:
            observations.append(
                DerivedMetricObservation(
                    metric_id=metric_id,
                    value=value,
                    unit="ratio",
                    period_end=period_end,
                    fiscal_year=year,
                    status="available",
                    formula_version=FORMULA_VERSION,
                    components=components,
                )
            )
    return observations


def _cagr_from_derived(
    metric_id: str,
    by_year: dict[int, DerivedMetricObservation],
    years: list[int],
) -> list[DerivedMetricObservation]:
    observations: list[DerivedMetricObservation] = []
    for year in years:
        start = by_year.get(year - 5)
        end = by_year.get(year)
        components = {
            "start_operating_cash_flow": None if start is None else start.components.get(
                "operating_cash_flow"
            ),
            "start_capex": None if start is None else start.components.get("capex"),
            "end_operating_cash_flow": None if end is None else end.components.get(
                "operating_cash_flow"
            ),
            "end_capex": None if end is None else end.components.get("capex"),
        }
        period_end = end.period_end if end is not None else f"{year}-09-30"
        if (
            start is None
            or end is None
            or start.status != "available"
            or end.status != "available"
            or start.value is None
            or end.value is None
        ):
            observations.append(
                DerivedMetricObservation(
                    metric_id=metric_id,
                    value=None,
                    unit="ratio",
                    period_end=period_end,
                    fiscal_year=year,
                    status="missing_input",
                    formula_version=FORMULA_VERSION,
                    components=components,
                )
            )
            continue
        value = _cagr(start.value, end.value, periods=5)
        observations.append(
            DerivedMetricObservation(
                metric_id=metric_id,
                value=value,
                unit="ratio",
                period_end=period_end,
                fiscal_year=year,
                status="available" if value is not None else "not_meaningful",
                formula_version=FORMULA_VERSION,
                components=components,
            )
        )
    return observations


def _cagr(start: float, end: float, *, periods: int) -> float | None:
    if periods <= 0 or start == 0:
        return None
    if start < 0 or end < 0:
        return None
    return (end / start) ** (1.0 / periods) - 1.0
