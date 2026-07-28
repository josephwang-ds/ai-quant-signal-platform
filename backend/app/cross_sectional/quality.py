"""Deterministic quality and coverage checks for factor panels."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.constants import (
    FACTOR_COLUMNS,
    LABEL_COLUMNS,
    MIN_HISTORY_DAYS,
)


def _check(
    check_id: str,
    status: str,
    *,
    detail: str,
    category: str = "data",
    count: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": check_id,
        "status": status,
        "category": category,
        "detail": detail,
    }
    if count is not None:
        payload["count"] = int(count)
    return payload


def _finite_mask(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return values.notna() & np.isfinite(values.to_numpy(dtype=float, copy=False))


def evaluate_panel_quality(
    panel: pd.DataFrame,
    *,
    requested_symbols: tuple[str, ...],
    loaded_symbols: tuple[str, ...],
    provider_failures: list[dict[str, str]] | None = None,
    min_history_days: int = MIN_HISTORY_DAYS,
) -> dict[str, Any]:
    """
    Build quality + coverage summaries.

    Distinguishes expected warm-up / future-label nulls from hard failures.
    Never converts missing values to zero.
    """
    failures = list(provider_failures or [])
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    if panel is None or panel.empty:
        checks.append(
            _check(
                "empty_dataset",
                "fail",
                detail="No rows available after market-data load and factor build.",
                category="provider",
                count=0,
            )
        )
        return {
            "status": "failed",
            "checks": checks,
            "coverage": {
                "universe_coverage": 0.0,
                "n_requested_symbols": len(requested_symbols),
                "n_loaded_symbols": 0,
                "n_rows": 0,
                "n_dates": 0,
                "symbol_coverage": [],
                "date_coverage": {
                    "min_symbols_per_date": 0,
                    "median_symbols_per_date": 0,
                    "max_symbols_per_date": 0,
                },
            },
            "provider_failures": failures,
            "warnings": warnings,
        }

    # --- duplicate keys ---
    dup_count = int(panel.duplicated(subset=["date", "symbol"]).sum())
    checks.append(
        _check(
            "duplicate_date_symbol",
            "fail" if dup_count else "pass",
            detail=(
                f"Found {dup_count} duplicate date-symbol rows."
                if dup_count
                else "All date-symbol keys are unique."
            ),
            count=dup_count,
        )
    )

    # --- missing symbols (provider) ---
    loaded_set = {s.upper() for s in loaded_symbols}
    missing_symbols = [s for s in requested_symbols if s.upper() not in loaded_set]
    checks.append(
        _check(
            "missing_symbols",
            "fail" if missing_symbols else "pass",
            detail=(
                f"Provider failed or returned no rows for: {', '.join(missing_symbols)}."
                if missing_symbols
                else "All requested symbols loaded at least one row."
            ),
            category="provider",
            count=len(missing_symbols),
        )
    )

    # --- invalid prices ---
    price_cols = [c for c in ("open", "high", "low", "close") if c in panel.columns]
    invalid_price = 0
    for col in price_cols:
        series = pd.to_numeric(panel[col], errors="coerce")
        bad = (~np.isfinite(series.to_numpy(dtype=float, copy=False))) | (
            series.to_numpy(dtype=float, copy=False) <= 0
        )
        invalid_price += int(np.asarray(bad).sum())
    checks.append(
        _check(
            "invalid_prices",
            "fail" if invalid_price else "pass",
            detail=(
                f"{invalid_price} invalid or non-positive price observations."
                if invalid_price
                else "All present prices are finite and positive."
            ),
            count=invalid_price,
        )
    )

    # --- volume ---
    neg_vol = 0
    zero_vol = 0
    if "volume" in panel.columns:
        vol = pd.to_numeric(panel["volume"], errors="coerce")
        neg_vol = int((vol < 0).sum())
        zero_vol = int((vol == 0).sum())
    checks.append(
        _check(
            "negative_volume",
            "fail" if neg_vol else "pass",
            detail=(
                f"{neg_vol} rows have negative volume."
                if neg_vol
                else "No negative volume rows."
            ),
            count=neg_vol,
        )
    )
    checks.append(
        _check(
            "zero_volume",
            "fail" if zero_vol else "pass",
            detail=(
                f"{zero_vol} rows have zero volume."
                if zero_vol
                else "No zero volume rows."
            ),
            count=zero_vol,
        )
    )

    # --- infinite values across factors/labels ---
    numeric_cols = [
        c
        for c in list(FACTOR_COLUMNS) + list(LABEL_COLUMNS) + price_cols + ["volume"]
        if c in panel.columns and c != "liquidity_eligible"
    ]
    inf_count = 0
    for col in numeric_cols:
        values = pd.to_numeric(panel[col], errors="coerce")
        arr = values.to_numpy(dtype=float, copy=False)
        inf_count += int(np.isinf(arr).sum())
    checks.append(
        _check(
            "infinite_values",
            "fail" if inf_count else "pass",
            detail=(
                f"{inf_count} infinite values remain in the panel."
                if inf_count
                else "No infinite values in numeric panel columns."
            ),
            count=inf_count,
        )
    )

    # --- insufficient history (per symbol) ---
    rows_per_symbol = panel.groupby("symbol", sort=False).size()
    short_symbols = [
        str(sym)
        for sym, n in rows_per_symbol.items()
        if int(n) < int(min_history_days)
    ]
    checks.append(
        _check(
            "insufficient_history",
            "fail" if short_symbols else "pass",
            detail=(
                f"Symbols below min_history_days={min_history_days}: "
                f"{', '.join(short_symbols)}."
                if short_symbols
                else f"All loaded symbols have at least {min_history_days} rows."
            ),
            count=len(short_symbols),
        )
    )

    # --- factor / label missingness with expected warm-up / future windows ---
    factor_missing_unexpected = 0
    label_missing_unexpected = 0
    warmup_nulls = 0
    future_label_nulls = 0

    for symbol, group in panel.groupby("symbol", sort=False):
        g = group.sort_values("date").reset_index(drop=True)
        n = len(g)
        # Expected warm-up: first 60 rows may lack full 60d windows.
        warmup_mask = pd.Series([i < 60 for i in range(n)])
        # Expected future-label nulls: last 5 / 20 rows.
        future5 = pd.Series([i >= n - 5 for i in range(n)])
        future20 = pd.Series([i >= n - 20 for i in range(n)])

        for col in FACTOR_COLUMNS:
            if col not in g.columns or col == "liquidity_eligible":
                continue
            missing = ~_finite_mask(g[col])
            warmup_nulls += int((missing & warmup_mask).sum())
            factor_missing_unexpected += int((missing & ~warmup_mask).sum())

        if "liquidity_eligible" in g.columns:
            # Boolean/NA: treat NA outside warm-up as unexpected for eligibility.
            missing = g["liquidity_eligible"].isna()
            warmup_nulls += int((missing & warmup_mask).sum())
            factor_missing_unexpected += int((missing & ~warmup_mask).sum())

        if "forward_return_5d" in g.columns:
            missing = ~_finite_mask(g["forward_return_5d"])
            future_label_nulls += int((missing & future5).sum())
            label_missing_unexpected += int((missing & ~future5).sum())
        if "forward_return_20d" in g.columns:
            missing = ~_finite_mask(g["forward_return_20d"])
            future_label_nulls += int((missing & future20).sum())
            label_missing_unexpected += int((missing & ~future20).sum())

    checks.append(
        _check(
            "missing_factors",
            "fail" if factor_missing_unexpected else "pass",
            detail=(
                f"{factor_missing_unexpected} unexpected factor nulls outside warm-up; "
                f"{warmup_nulls} expected warm-up nulls."
                if factor_missing_unexpected
                else (
                    f"No unexpected factor nulls outside warm-up "
                    f"({warmup_nulls} expected warm-up nulls)."
                )
            ),
            category="calculation",
            count=factor_missing_unexpected,
        )
    )
    checks.append(
        _check(
            "missing_labels",
            "fail" if label_missing_unexpected else "pass",
            detail=(
                f"{label_missing_unexpected} unexpected label nulls outside "
                f"trailing forward windows; {future_label_nulls} expected future-label nulls."
                if label_missing_unexpected
                else (
                    f"No unexpected label nulls "
                    f"({future_label_nulls} expected future-label nulls)."
                )
            ),
            category="calculation",
            count=label_missing_unexpected,
        )
    )

    if failures:
        checks.append(
            _check(
                "provider_failures",
                "fail",
                detail=f"{len(failures)} symbol-level provider failure(s).",
                category="provider",
                count=len(failures),
            )
        )
    else:
        checks.append(
            _check(
                "provider_failures",
                "pass",
                detail="No provider failures recorded.",
                category="provider",
                count=0,
            )
        )

    # Coverage
    n_requested = len(requested_symbols)
    n_loaded = len(loaded_set)
    universe_coverage = (
        float(n_loaded) / float(n_requested) if n_requested else 0.0
    )
    dates = pd.to_datetime(panel["date"])
    symbols_per_date = panel.assign(date=dates).groupby("date")["symbol"].nunique()
    symbol_coverage = []
    for symbol, group in panel.groupby("symbol", sort=True):
        factor_finite = 0
        factor_total = 0
        for col in FACTOR_COLUMNS:
            if col not in group.columns or col == "liquidity_eligible":
                continue
            factor_total += len(group)
            factor_finite += int(_finite_mask(group[col]).sum())
        missing_rate = (
            1.0 - (factor_finite / factor_total) if factor_total else 1.0
        )
        symbol_coverage.append(
            {
                "symbol": str(symbol),
                "n_rows": int(len(group)),
                "missing_factor_rate": round(float(missing_rate), 6),
            }
        )

    coverage = {
        "universe_coverage": round(universe_coverage, 6),
        "n_requested_symbols": n_requested,
        "n_loaded_symbols": n_loaded,
        "n_rows": int(len(panel)),
        "n_dates": int(panel["date"].nunique()),
        "date_start": str(pd.to_datetime(panel["date"]).min().date()),
        "date_end": str(pd.to_datetime(panel["date"]).max().date()),
        "symbol_coverage": symbol_coverage,
        "date_coverage": {
            "min_symbols_per_date": int(symbols_per_date.min()) if len(symbols_per_date) else 0,
            "median_symbols_per_date": (
                float(symbols_per_date.median()) if len(symbols_per_date) else 0.0
            ),
            "max_symbols_per_date": int(symbols_per_date.max()) if len(symbols_per_date) else 0,
        },
    }

    hard_fail_ids = {
        "empty_dataset",
        "duplicate_date_symbol",
        "invalid_prices",
        "negative_volume",
        "infinite_values",
    }
    failed_hard = any(
        c["status"] == "fail" and c["id"] in hard_fail_ids for c in checks
    )
    failed_any = any(c["status"] == "fail" for c in checks)
    if failed_hard or (panel.empty):
        status = "failed"
    elif failed_any:
        status = "incomplete"
    else:
        status = "completed"

    if missing_symbols:
        warnings.append(
            "One or more requested symbols were unavailable from the market-data port."
        )

    return {
        "status": status,
        "checks": checks,
        "coverage": coverage,
        "provider_failures": failures,
        "warnings": warnings,
        "null_accounting": {
            "expected_warmup_factor_nulls": int(warmup_nulls),
            "expected_future_label_nulls": int(future_label_nulls),
            "unexpected_factor_nulls": int(factor_missing_unexpected),
            "unexpected_label_nulls": int(label_missing_unexpected),
        },
    }
