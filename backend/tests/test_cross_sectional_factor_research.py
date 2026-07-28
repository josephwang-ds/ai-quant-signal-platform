"""Pure-engine tests for Phase 2 cross-sectional factor research."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.cross_sectional.research.correlation import (
    compute_factor_correlations,
    summarize_correlations,
)
from app.cross_sectional.research.eligibility import eligible_mask, slice_eligible
from app.cross_sectional.research.quantiles import (
    assign_quantiles,
    compute_daily_quantiles,
    summarize_quantiles,
)
from app.cross_sectional.research.rank_ic import (
    compute_daily_rank_ic,
    summarize_rank_ic,
)
from app.cross_sectional.research.stability import summarize_stability
from app.cross_sectional.research.turnover import (
    compute_factor_turnover,
    summarize_turnover,
)


def _panel_from_day(
    date: str,
    rows: list[tuple[str, float, float]],
    *,
    factor: str = "f",
    label: str = "forward_return_5d",
    liquidity: bool | None = True,
) -> pd.DataFrame:
    records = []
    for sym, fval, lval in rows:
        records.append(
            {
                "date": pd.Timestamp(date),
                "symbol": sym,
                "f": fval,
                "g": -fval,
                factor: fval,
                label: lval,
                "forward_return_20d": lval * 2,
                "liquidity_eligible": liquidity,
            }
        )
    return pd.DataFrame(records)


def test_eligibility_missing_factor_only_affects_that_factor():
    day = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02")] * 3,
            "symbol": ["A", "B", "C"],
            "return_5d": [1.0, np.nan, 3.0],
            "return_20d": [1.0, 2.0, 3.0],
            "forward_return_5d": [0.1, 0.2, 0.3],
            "liquidity_eligible": [True, True, True],
        }
    )
    mask5, reasons5 = eligible_mask(
        day, factor="return_5d", label="forward_return_5d", apply_liquidity_filter=False
    )
    mask20, _ = eligible_mask(
        day, factor="return_20d", label="forward_return_5d", apply_liquidity_filter=False
    )
    assert int(mask5.sum()) == 2
    assert reasons5["missing_factor"] == 1
    assert int(mask20.sum()) == 3


def test_eligibility_liquidity_and_min_cross_section_unavailable():
    rows = [(s, float(i), float(i) / 10) for i, s in enumerate(list("ABCDEFGHIJ"))]
    panel = _panel_from_day("2020-01-02", rows, liquidity=False)
    eligible, meta = slice_eligible(
        panel,
        date_value=pd.Timestamp("2020-01-02"),
        factor="f",
        label="forward_return_5d",
        apply_liquidity_filter=True,
    )
    assert meta["eligible_count"] == 0
    daily = compute_daily_rank_ic(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    # Without liquidity filter, enough names → available
    assert daily[0]["status"] == "available"
    thin = compute_daily_rank_ic(
        panel.head(3),
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    assert thin[0]["status"] == "unavailable"
    assert thin[0]["rank_ic"] is None
    assert thin[0]["unavailable_reason"] == "below_minimum_cross_section"


def test_rank_ic_perfect_positive_and_negative():
    rows = [(s, float(i), float(i)) for i, s in enumerate(list("ABCDEFGHIJ"), start=1)]
    panel = _panel_from_day("2020-01-02", rows)
    daily = compute_daily_rank_ic(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    assert daily[0]["rank_ic"] == pytest.approx(1.0)
    neg_rows = [(s, float(i), -float(i)) for i, s in enumerate(list("ABCDEFGHIJ"), start=1)]
    panel_neg = _panel_from_day("2020-01-02", neg_rows)
    daily_neg = compute_daily_rank_ic(
        panel_neg,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    assert daily_neg[0]["rank_ic"] == pytest.approx(-1.0)


def test_rank_ic_constant_and_zero_std_icir_null():
    rows = [(s, 1.0, float(i)) for i, s in enumerate(list("ABCDEFGHIJ"))]
    panel = _panel_from_day("2020-01-02", rows)
    daily = compute_daily_rank_ic(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    assert daily[0]["status"] == "unavailable"
    assert daily[0]["unavailable_reason"] == "constant_factor"

    # Two identical IC days → std 0 → null ICIR
    perfect = [
        {"status": "available", "rank_ic": 0.5},
        {"status": "available", "rank_ic": 0.5},
    ]
    summary = summarize_rank_ic(perfect)
    assert summary["mean_rank_ic"] == pytest.approx(0.5)
    assert summary["icir"] is None


def test_rank_ic_not_pooled_across_dates():
    # Date1 perfect positive, date2 perfect negative — mean near 0, not pooled +1
    p1 = _panel_from_day(
        "2020-01-02",
        [(s, float(i), float(i)) for i, s in enumerate(list("ABCDEFGHIJ"), start=1)],
    )
    p2 = _panel_from_day(
        "2020-01-03",
        [(s, float(i), -float(i)) for i, s in enumerate(list("ABCDEFGHIJ"), start=1)],
    )
    panel = pd.concat([p1, p2], ignore_index=True)
    daily = compute_daily_rank_ic(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        minimum_cross_section_size=5,
        apply_liquidity_filter=False,
    )
    assert daily[0]["rank_ic"] == pytest.approx(1.0)
    assert daily[1]["rank_ic"] == pytest.approx(-1.0)
    summary = summarize_rank_ic(daily)
    assert summary["mean_rank_ic"] == pytest.approx(0.0)


def test_quantiles_q1_low_q5_high_and_spread():
    symbols = [f"S{i}" for i in range(10)]
    values = list(range(10))
    buckets = assign_quantiles(symbols, values, quantile_count=5)
    assert buckets["Q1"] == ["S0", "S1"]
    assert buckets["Q5"] == ["S8", "S9"]
    assert len({s for members in buckets.values() for s in members}) == 10

    rows = [(s, float(i), float(i) / 10.0) for i, s in enumerate(symbols)]
    panel = _panel_from_day("2020-01-02", rows)
    q_rows, spreads = compute_daily_quantiles(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        quantile_count=5,
        minimum_cross_section_size=10,
        minimum_quantile_size=2,
        apply_liquidity_filter=False,
    )
    assert spreads[0]["status"] == "available"
    # Q5 mean forward = (8+9)/20 = 0.85; Q1 = (0+1)/20 = 0.05; spread 0.8
    assert spreads[0]["top_minus_bottom"] == pytest.approx(0.8)
    neg_panel = _panel_from_day(
        "2020-01-02",
        [(s, float(i), -float(i) / 10.0) for i, s in enumerate(symbols)],
    )
    _, neg_spreads = compute_daily_quantiles(
        neg_panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        quantile_count=5,
        minimum_cross_section_size=10,
        minimum_quantile_size=2,
        apply_liquidity_filter=False,
    )
    assert neg_spreads[0]["top_minus_bottom"] < 0


def test_quantile_too_small_unavailable_and_monotonicity():
    panel = _panel_from_day(
        "2020-01-02",
        [(s, float(i), float(i)) for i, s in enumerate(list("ABCD"))],
    )
    _, spreads = compute_daily_quantiles(
        panel,
        factor="f",
        label="forward_return_5d",
        horizon=5,
        quantile_count=5,
        minimum_cross_section_size=10,
        minimum_quantile_size=2,
        apply_liquidity_filter=False,
    )
    assert spreads[0]["status"] == "unavailable"
    assert spreads[0]["top_minus_bottom"] is None

    # Monotonic increasing quantile means → Spearman ~ 1
    q_rows = [
        {
            "quantile": f"Q{i}",
            "mean_forward_return": float(i),
            "status": "available",
        }
        for i in range(1, 6)
    ]
    summary = summarize_quantiles(q_rows, [], quantile_count=5)
    assert summary["monotonicity_spearman"] == pytest.approx(1.0)


def test_turnover_identical_reversed_and_insufficient_overlap():
    symbols = [f"S{i}" for i in range(10)]
    d1 = _panel_from_day(
        "2020-01-02",
        [(s, float(i), 0.1) for i, s in enumerate(symbols)],
    )
    d2_same = _panel_from_day(
        "2020-01-03",
        [(s, float(i), 0.1) for i, s in enumerate(symbols)],
    )
    d2_rev = _panel_from_day(
        "2020-01-03",
        [(s, float(9 - i), 0.1) for i, s in enumerate(symbols)],
    )
    same = compute_factor_turnover(
        pd.concat([d1, d2_same], ignore_index=True),
        factor="f",
        label="forward_return_5d",
        apply_liquidity_filter=False,
        minimum_overlap=5,
    )
    assert same[0]["turnover"] == pytest.approx(0.0)
    rev = compute_factor_turnover(
        pd.concat([d1, d2_rev], ignore_index=True),
        factor="f",
        label="forward_return_5d",
        apply_liquidity_filter=False,
        minimum_overlap=5,
    )
    assert rev[0]["turnover"] == pytest.approx(2.0)

    d2_partial = _panel_from_day(
        "2020-01-03",
        [(s, float(i), 0.1) for i, s in enumerate(symbols[:3])],
    )
    partial = compute_factor_turnover(
        pd.concat([d1, d2_partial], ignore_index=True),
        factor="f",
        label="forward_return_5d",
        apply_liquidity_filter=False,
        minimum_overlap=5,
    )
    assert partial[0]["status"] == "unavailable"
    assert partial[0]["turnover"] is None


def test_correlation_identical_inverse_and_warning():
    symbols = [f"S{i}" for i in range(10)]
    panel = _panel_from_day(
        "2020-01-02",
        [(s, float(i), 0.1) for i, s in enumerate(symbols)],
    )
    panel["g"] = -panel["f"]
    daily = compute_factor_correlations(
        panel,
        factors=["f", "g"],
        minimum_pairwise_size=5,
        apply_liquidity_filter=False,
    )
    assert daily[0]["correlation"] == pytest.approx(-1.0)
    panel2 = panel.copy()
    panel2["h"] = panel2["f"]
    daily2 = compute_factor_correlations(
        panel2,
        factors=["f", "h"],
        minimum_pairwise_size=5,
        apply_liquidity_filter=False,
    )
    assert daily2[0]["correlation"] == pytest.approx(1.0)
    summary = summarize_correlations(daily2, warning_threshold=0.5)
    assert summary["pairs"][0]["factor_a"] == "f"
    assert summary["pairs"][0]["factor_b"] == "h"
    assert len(summary["redundancy_warnings"]) == 1
    # No mirrored duplicate
    assert all(p["factor_a"] < p["factor_b"] for p in summary["pairs"])


def test_stability_calendar_year_and_thin_period():
    daily_ic = [
        {"date": "2020-01-02", "status": "available", "rank_ic": 0.2},
        {"date": "2020-06-01", "status": "available", "rank_ic": 0.4},
        {"date": "2021-01-02", "status": "available", "rank_ic": -0.3},
    ]
    spreads = [
        {"date": "2020-01-02", "status": "available", "top_minus_bottom": 0.01},
        {"date": "2020-06-01", "status": "available", "top_minus_bottom": 0.02},
        {"date": "2021-01-02", "status": "available", "top_minus_bottom": -0.01},
    ]
    stab = summarize_stability(daily_ic, spreads, minimum_period_dates=2)
    years = {p["period"]: p for p in stab["periods"]}
    assert years["2020"]["status"] == "available"
    assert years["2020"]["mean_rank_ic"] == pytest.approx(0.3)
    assert years["2021"]["status"] == "unavailable"
    assert stab["best_period_mean_ic"] == pytest.approx(0.3)
    assert stab["periods_positive"] == 1
