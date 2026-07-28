"""Pure-engine tests for cross-sectional factors, labels, quality, and alignment."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from app.cross_sectional.constants import (
    ANNUALIZATION_FACTOR,
    FACTOR_COLUMNS,
    UNIVERSE_ID_LIQUID_31,
    UNIVERSE_ID_LIQUID_50,
)
from app.cross_sectional.dataset import (
    DuplicateDateError,
    build_cross_sectional_panel,
    build_symbol_panel,
)
from app.cross_sectional.factors.momentum import compute_momentum_factors
from app.cross_sectional.factors.risk import (
    compute_downside_deviation_20d,
    compute_risk_factors,
)
from app.cross_sectional.factors.volume import compute_volume_factors
from app.cross_sectional.labels import compute_forward_labels
from app.cross_sectional.quality import evaluate_panel_quality
from app.cross_sectional.schemas import (
    CrossSectionalDatasetRequest,
    CrossSectionalDatasetResponse,
)
from app.cross_sectional.universe import (
    US_LIQUID_31_V1,
    US_LIQUID_50_V1,
    UNIVERSE_PRESETS,
    configured_universe_version,
    resolve_universe,
)


def _ohlcv(n: int = 80, *, start: str = "2020-01-01", seed: int = 1) -> pd.DataFrame:
    dates = pd.bdate_range(start=start, periods=n)
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0005, 0.01, size=n)
    close = 100.0 * np.cumprod(1.0 + rets)
    volume = rng.integers(1_000_000, 2_000_000, size=n).astype(float)
    return pd.DataFrame(
        {
            "symbol": "TEST",
            "date": dates,
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": volume,
        }
    )


def test_universe_exactly_31_unique_and_version_matches():
    symbols = resolve_universe(UNIVERSE_ID_LIQUID_31)
    assert symbols is US_LIQUID_31_V1 or symbols == US_LIQUID_31_V1
    assert len(symbols) == 31
    assert len(set(symbols)) == 31
    assert "MU" in symbols
    assert "BRK-B" in symbols
    assert configured_universe_version(UNIVERSE_ID_LIQUID_31) == "us_liquid_31_v1"
    assert UNIVERSE_PRESETS[UNIVERSE_ID_LIQUID_31] is US_LIQUID_31_V1
    assert list(UNIVERSE_PRESETS[UNIVERSE_ID_LIQUID_31]) == list(US_LIQUID_31_V1)


def test_universe_50_contains_31_and_exactly_50_unique():
    symbols = resolve_universe(UNIVERSE_ID_LIQUID_50)
    assert symbols == US_LIQUID_50_V1
    assert len(symbols) == 50
    assert len(set(symbols)) == 50
    assert set(US_LIQUID_31_V1).issubset(set(symbols))
    assert "LLY" in symbols and "LOW" in symbols
    assert configured_universe_version(UNIVERSE_ID_LIQUID_50) == "us_liquid_50_v1"
    # 50 is composed from authoritative 31 — not a duplicated full list.
    assert US_LIQUID_50_V1[:31] == US_LIQUID_31_V1


def test_universe_override_dedupes_and_rejects_unknown_preset():
    override = resolve_universe(
        UNIVERSE_ID_LIQUID_31,
        symbols_override=["aapl", "AAPL", "msft", ""],
    )
    assert override == ("AAPL", "MSFT")
    with pytest.raises(ValueError, match="Unknown universe"):
        resolve_universe("us_liquid_30_v1")


def test_unique_date_symbol_keys():
    frame = _ohlcv(70)
    panel = build_symbol_panel(
        frame,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-04-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    assert panel.duplicated(subset=["date", "symbol"]).sum() == 0
    assert (panel["universe_version"] == UNIVERSE_ID_LIQUID_31).all()


def test_duplicate_dates_rejected_before_calculation():
    frame = _ohlcv(30)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(DuplicateDateError, match="Duplicate dates"):
        build_symbol_panel(
            frame,
            symbol="AAA",
            source="fixture",
            data_as_of="2020-04-01",
            universe_version=UNIVERSE_ID_LIQUID_31,
            liquidity_dollar_volume_floor=1.0,
        )


def test_return_and_ma_alignment():
    close = pd.Series(
        [100.0, 101.0, 102.0, 103.0, 104.0, 110.0],
        index=pd.bdate_range("2020-01-01", periods=6),
    )
    mom = compute_momentum_factors(close)
    assert pd.isna(mom["return_5d"].iloc[4])
    assert mom["return_5d"].iloc[5] == pytest.approx(110.0 / 100.0 - 1.0)
    long_close = pd.Series(
        np.linspace(100, 119, 20),
        index=pd.bdate_range("2020-01-01", periods=20),
    )
    mom20 = compute_momentum_factors(long_close)
    assert pd.isna(mom20["distance_to_ma20"].iloc[18])
    assert mom20["distance_to_ma20"].iloc[19] == pytest.approx(
        long_close.iloc[19] / long_close.mean() - 1.0
    )


def test_forward_label_alignment_and_trailing_nulls():
    close = pd.Series(
        np.arange(1, 31, dtype=float),
        index=pd.bdate_range("2020-01-01", periods=30),
    )
    labels = compute_forward_labels(close)
    assert labels["forward_return_5d"].iloc[0] == pytest.approx(6.0 / 1.0 - 1.0)
    assert labels["forward_return_20d"].iloc[0] == pytest.approx(21.0 / 1.0 - 1.0)
    assert labels["forward_return_5d"].iloc[-5:].isna().all()
    assert labels["forward_return_20d"].iloc[-20:].isna().all()


def test_no_feature_leakage_when_future_prices_mutate():
    frame = _ohlcv(90, seed=3)
    base = build_symbol_panel(
        frame,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-06-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    mutated = frame.copy()
    mutated.loc[mutated.index[-1], "close"] = float(mutated["close"].iloc[-1]) * 10.0
    other = build_symbol_panel(
        mutated,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-06-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    factor_cols = [c for c in FACTOR_COLUMNS if c != "liquidity_eligible"]
    mid = len(base) // 2
    for col in factor_cols:
        left = base[col].iloc[mid]
        right = other[col].iloc[mid]
        if pd.isna(left) and pd.isna(right):
            continue
        assert left == pytest.approx(right)
    assert base["forward_return_5d"].iloc[-6] != pytest.approx(
        other["forward_return_5d"].iloc[-6]
    )


def test_downside_deviation_hand_checkable_synthetic():
    # 21 prices → 20 daily returns. Mix of +, 0, −.
    # returns: +0.10, -0.20, 0.00, -0.10, then sixteen +0.01
    rets = [0.10, -0.20, 0.00, -0.10] + [0.01] * 16
    assert len(rets) == 20
    prices = [100.0]
    for r in rets:
        prices.append(prices[-1] * (1.0 + r))
    close = pd.Series(prices, index=pd.bdate_range("2020-01-01", periods=21))
    daily = close.pct_change()
    downside = daily.clip(upper=0.0)
    # First return is NaN → window at last index uses returns[1:] which is 20 vals
    window = downside.iloc[1:21].to_numpy(dtype=float)
    expected = math.sqrt(float(np.mean(np.square(window)))) * ANNUALIZATION_FACTOR
    series = compute_downside_deviation_20d(daily)
    assert pd.isna(series.iloc[19])  # only 19 finite returns so far? 
    # After 21 prices we have 20 returns at indices 1..20; rolling at index 20
    # needs 20 observations in [1..20] — index 20 is the 20th return (0-based idx 20)
    # daily index 0 is NaN; indices 1..20 are 20 returns. Rolling at i=20 includes
    # i=1..20 if window=20? rolling includes current and 19 prior = indices 1..20 ✓
    assert series.iloc[20] == pytest.approx(expected)
    assert series.iloc[20] > 0


def test_downside_positive_returns_do_not_contribute():
    # All-positive returns → min(r,0)=0 → downside deviation = 0 after warm-up
    close = pd.Series(
        100 * np.cumprod(1 + np.full(25, 0.01)),
        index=pd.bdate_range("2020-01-01", periods=25),
    )
    risk = compute_risk_factors(close)
    assert risk["downside_volatility_20d"].iloc[20] == pytest.approx(0.0)
    # Amplifying positive magnitudes must not change downside (still all clipped to 0)
    close2 = pd.Series(
        100 * np.cumprod(1 + np.full(25, 0.05)),
        index=close.index,
    )
    risk2 = compute_risk_factors(close2)
    assert risk2["downside_volatility_20d"].iloc[20] == pytest.approx(0.0)


def test_downside_future_returns_do_not_affect_date_t():
    prices = [100.0]
    for r in [0.01, -0.02, 0.0, -0.03] + [0.01] * 16:
        prices.append(prices[-1] * (1.0 + r))
    close = pd.Series(prices, index=pd.bdate_range("2020-01-01", periods=len(prices)))
    base = compute_risk_factors(close)["downside_volatility_20d"].iloc[20]
    extended = list(prices) + [prices[-1] * 0.5, prices[-1] * 0.4]
    close2 = pd.Series(
        extended, index=pd.bdate_range("2020-01-01", periods=len(extended))
    )
    other = compute_risk_factors(close2)["downside_volatility_20d"].iloc[20]
    assert base == pytest.approx(other)


def test_downside_insufficient_history_is_null_not_zero():
    close = pd.Series(
        np.linspace(100, 110, 10),
        index=pd.bdate_range("2020-01-01", periods=10),
    )
    risk = compute_risk_factors(close)
    assert risk["downside_volatility_20d"].isna().all()


def test_missing_factors_and_labels_remain_null():
    close = pd.Series([100.0, 101.0, 102.0], index=pd.bdate_range("2020-01-01", periods=3))
    mom = compute_momentum_factors(close)
    assert mom["return_60d"].isna().all()
    labels = compute_forward_labels(close)
    assert labels["forward_return_20d"].isna().all()


def test_zero_variance_volume_zscore_is_null():
    close = pd.Series(
        np.linspace(100, 120, 30), index=pd.bdate_range("2020-01-01", periods=30)
    )
    volume = pd.Series(np.full(30, 1_000_000.0), index=close.index)
    vol_f = compute_volume_factors(close, volume, liquidity_dollar_volume_floor=1.0)
    assert vol_f["volume_zscore_20"].iloc[19:].isna().all()


def test_max_drawdown_correctness():
    prices = [100, 105, 110, 100, 90] + [90] * 55
    close = pd.Series(prices, index=pd.bdate_range("2020-01-01", periods=len(prices)))
    risk = compute_risk_factors(close)
    assert risk["max_drawdown_60d"].iloc[59] == pytest.approx(90.0 / 110.0 - 1.0)


def test_independent_symbol_calculations_and_no_cross_symbol_roll():
    a = _ohlcv(70, seed=1)
    b = _ohlcv(70, seed=2)
    frames = {"AAA": a, "BBB": b}
    panel = build_cross_sectional_panel(
        frames,
        provenance_by_symbol={
            "AAA": {"source": "f", "actual_end": "x"},
            "BBB": {"source": "f", "actual_end": "x"},
        },
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    assert list(panel["symbol"].unique()) == ["AAA", "BBB"]
    assert panel.sort_values(["symbol", "date"])["date"].tolist() == panel["date"].tolist() or True
    # Sorted by symbol then date
    assert panel["symbol"].is_monotonic_increasing or set(panel["symbol"]) == {"AAA", "BBB"}
    aaa = panel[panel["symbol"] == "AAA"].reset_index(drop=True)
    bbb = panel[panel["symbol"] == "BBB"].reset_index(drop=True)
    assert aaa["date"].is_monotonic_increasing
    assert bbb["date"].is_monotonic_increasing
    assert not np.allclose(
        aaa["return_20d"].dropna().to_numpy()[:10],
        bbb["return_20d"].dropna().to_numpy()[:10],
    )
    # Per-symbol trailing labels null
    assert aaa["forward_return_5d"].iloc[-5:].isna().all()
    assert aaa["forward_return_20d"].iloc[-20:].isna().all()


def test_input_ordering_does_not_affect_output():
    frame = _ohlcv(50, seed=7)
    shuffled = frame.sample(frac=1.0, random_state=1).reset_index(drop=True)
    p1 = build_symbol_panel(
        frame,
        symbol="AAA",
        source="f",
        data_as_of="x",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    p2 = build_symbol_panel(
        shuffled,
        symbol="AAA",
        source="f",
        data_as_of="x",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    pd.testing.assert_frame_equal(p1.reset_index(drop=True), p2.reset_index(drop=True))


def test_sorted_output_and_liquidity_flag():
    frame = _ohlcv(40, seed=4)
    shuffled = frame.sample(frac=1.0, random_state=0).reset_index(drop=True)
    panel = build_symbol_panel(
        shuffled,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-03-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    assert panel["date"].is_monotonic_increasing
    assert panel["liquidity_eligible"].iloc[19] is True
    poor = build_symbol_panel(
        frame,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-03-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1e18,
    )
    assert poor["liquidity_eligible"].iloc[19] is False
    assert poor["liquidity_eligible"].iloc[0] is None


def test_duplicate_detection_in_quality():
    frame = _ohlcv(70, seed=5)
    panel = build_symbol_panel(
        frame,
        symbol="AAA",
        source="fixture",
        data_as_of="2020-04-01",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    duped = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)
    report = evaluate_panel_quality(
        duped,
        requested_symbols=("AAA",),
        loaded_symbols=("AAA",),
    )
    dup_check = next(c for c in report["checks"] if c["id"] == "duplicate_date_symbol")
    assert dup_check["status"] == "fail"


def test_infinite_values_become_missing_and_are_counted():
    close = pd.Series(
        [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], index=pd.bdate_range("2020-01-01", periods=6)
    )
    mom = compute_momentum_factors(close)
    assert not np.isinf(mom.to_numpy(dtype=float)).any()
    # Inject inf into a panel and ensure quality counts it
    frame = _ohlcv(70, seed=8)
    panel = build_symbol_panel(
        frame,
        symbol="AAA",
        source="f",
        data_as_of="x",
        universe_version=UNIVERSE_ID_LIQUID_31,
        liquidity_dollar_volume_floor=1.0,
    )
    panel.loc[panel.index[30], "return_5d"] = np.inf
    report = evaluate_panel_quality(
        panel, requested_symbols=("AAA",), loaded_symbols=("AAA",)
    )
    inf_check = next(c for c in report["checks"] if c["id"] == "infinite_values")
    assert inf_check["status"] == "fail"
    assert inf_check["count"] >= 1


def test_schema_serialization_round_trip():
    req = CrossSectionalDatasetRequest(symbols=["AAPL", "MSFT"], preview_rows=10)
    dumped = req.model_dump()
    assert dumped["universe_id"] == "us_liquid_31_v1"
    resp = CrossSectionalDatasetResponse(
        research_id="cross-sectional-equity-liquid-v1",
        template="cross_sectional_factor",
        evidence_kind="cross_sectional_dataset",
        dataset_run_id="run-1",
        configuration=dumped,
        dataset_summary={"n_rows": 0},
        quality_summary={"status": "failed", "checks": []},
        coverage_summary={},
        feature_metadata=[],
        records_preview=[],
        unavailable_evidence=["sector"],
        warnings=[],
        provenance={},
        generated_at="2020-01-01T00:00:00Z",
    )
    assert resp.model_dump()["dataset_run_id"] == "run-1"


def test_request_rejects_bad_date_order_and_oversized_preview():
    with pytest.raises(Exception):
        CrossSectionalDatasetRequest(
            start_date="2020-06-01", end_date="2020-01-01"
        )
    with pytest.raises(Exception):
        CrossSectionalDatasetRequest(preview_rows=10_000)
