"""
Shared helpers for live market-data and research-execution verification.

Used by live smoke tests and manual verification scripts. Offline-safe helpers
do not perform network I/O.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, is_dataclass
from typing import Any

import pandas as pd

from app.research_execution.market_data_port import DataProvenance, NormalizedMarketSeries

PROVENANCE_FIELDS = (
    "provider",
    "adapter",
    "requested_symbol",
    "canonical_symbol",
    "provider_symbol",
    "asset_class",
    "exchange",
    "currency",
    "adjustment",
    "interval",
    "actual_start",
    "actual_end",
    "row_count",
    "cache_hit",
    "cache_stale",
)

FABRICATED_FALLBACK_MARKERS = (
    "deterministic local fixture",
    "fabricated",
    "fake data",
    "invented fallback",
    "offline-fixture",
)

# Conservative bounded ranges — completed calendar years, no current-session bar.
YAHOO_LIVE_START = "2023-01-01"
YAHOO_LIVE_END = "2024-12-31"
AKSHARE_LIVE_START = "2023-01-01"
AKSHARE_LIVE_END = "2024-12-31"
# Longer window for MA20/60 execution smoke on A-shares.
AKSHARE_EXECUTION_START = "2020-01-01"
AKSHARE_EXECUTION_END = "2024-12-31"

MIN_OHLCV_ROWS = 100


class LiveVerificationError(Exception):
    """Verification failure with a stable error category for scripts."""

    def __init__(self, message: str, *, category: str = "verification_failed") -> None:
        super().__init__(message)
        self.category = category
        self.message = message


def provenance_as_dict(provenance: DataProvenance | dict[str, Any]) -> dict[str, Any]:
    if isinstance(provenance, dict):
        return provenance
    return asdict(provenance)


def validate_json_safe(value: Any, *, path: str = "$") -> list[str]:
    """Return human-readable JSON-safety violations (NaN/Infinity/non-serializable)."""
    errors: list[str] = []

    if value is None or isinstance(value, (str, bool, int)):
        return errors

    if isinstance(value, float):
        if not math.isfinite(value):
            errors.append(f"{path}: non-finite float")
        return errors

    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(validate_json_safe(item, path=f"{path}.{key}"))
        return errors

    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            errors.extend(validate_json_safe(item, path=f"{path}[{index}]"))
        return errors

    if is_dataclass(value):
        return validate_json_safe(asdict(value), path=path)

    errors.append(f"{path}: unsupported JSON type {type(value).__name__}")
    return errors


def assert_json_safe(value: Any, *, path: str = "$") -> None:
    errors = validate_json_safe(value, path=path)
    if errors:
        raise LiveVerificationError(
            "; ".join(errors),
            category="invalid_response",
        )


def validate_provenance_contract(
    provenance: DataProvenance | dict[str, Any],
    *,
    expected_provider: str | None = None,
    expected_asset_class: str | None = None,
    expected_canonical_symbol: str | None = None,
    expected_exchange: str | None = None,
    expected_adjustment: str | None = None,
    require_fresh_live_fetch: bool = False,
) -> list[str]:
    """Return provenance validation errors (empty list means OK)."""
    prov = provenance_as_dict(provenance)
    errors: list[str] = []

    for field in PROVENANCE_FIELDS:
        if field not in prov:
            errors.append(f"provenance missing field '{field}'")

    if expected_provider and prov.get("provider") != expected_provider:
        errors.append(
            f"expected provider '{expected_provider}', got '{prov.get('provider')}'"
        )
    if expected_asset_class and prov.get("asset_class") != expected_asset_class:
        errors.append(
            f"expected asset_class '{expected_asset_class}', "
            f"got '{prov.get('asset_class')}'"
        )
    if expected_canonical_symbol and prov.get("canonical_symbol") != expected_canonical_symbol:
        errors.append(
            f"expected canonical_symbol '{expected_canonical_symbol}', "
            f"got '{prov.get('canonical_symbol')}'"
        )
    if expected_exchange is not None and prov.get("exchange") != expected_exchange:
        errors.append(
            f"expected exchange '{expected_exchange}', got '{prov.get('exchange')}'"
        )
    if expected_adjustment and prov.get("adjustment") != expected_adjustment:
        errors.append(
            f"expected adjustment '{expected_adjustment}', got '{prov.get('adjustment')}'"
        )

    if require_fresh_live_fetch:
        if prov.get("cache_hit"):
            errors.append("expected cache_hit=false on fresh live fetch")
        if prov.get("cache_stale"):
            errors.append("expected cache_stale=false on successful live fetch")

    if not prov.get("actual_start") or not prov.get("actual_end"):
        errors.append("actual_start/actual_end must be populated")

    row_count = prov.get("row_count")
    if not isinstance(row_count, int) or row_count <= 0:
        errors.append("row_count must be a positive integer")

    return errors


def assert_provenance_contract(
    provenance: DataProvenance | dict[str, Any],
    **kwargs: Any,
) -> None:
    errors = validate_provenance_contract(provenance, **kwargs)
    if errors:
        raise LiveVerificationError(
            "; ".join(errors),
            category="provenance_invalid",
        )


def validate_ohlcv_frame(frame: pd.DataFrame, *, min_rows: int = MIN_OHLCV_ROWS) -> list[str]:
    errors: list[str] = []
    if frame is None or frame.empty:
        return ["OHLCV frame is empty"]

    if len(frame) < min_rows:
        errors.append(f"expected at least {min_rows} rows, got {len(frame)}")

    dates = pd.to_datetime(frame["date"], errors="coerce")
    if dates.isna().any():
        errors.append("one or more dates could not be parsed")
    if dates.duplicated().any():
        errors.append("duplicate dates detected")
    if not dates.is_monotonic_increasing:
        errors.append("dates are not ascending")

    for col in ("open", "high", "low", "close", "volume"):
        series = pd.to_numeric(frame[col], errors="coerce")
        if series.isna().any():
            errors.append(f"column '{col}' contains NaN")
        if col != "volume" and (series <= 0).any():
            errors.append(f"column '{col}' must be positive")

    for col in ("open", "high", "low", "close", "volume"):
        values = frame[col].tolist()
        for value in values:
            if isinstance(value, float) and not math.isfinite(value):
                errors.append(f"column '{col}' contains non-finite value")
                break

    return errors


def assert_ohlcv_frame(frame: pd.DataFrame, *, min_rows: int = MIN_OHLCV_ROWS) -> None:
    errors = validate_ohlcv_frame(frame, min_rows=min_rows)
    if errors:
        raise LiveVerificationError(
            "; ".join(errors),
            category="invalid_provider_response",
        )


def validate_no_fabricated_fallback(warnings: list[str]) -> list[str]:
    lowered = [warning.lower() for warning in warnings]
    hits = [
        warning
        for warning in warnings
        if any(marker in warning.lower() for marker in FABRICATED_FALLBACK_MARKERS)
    ]
    if hits:
        return [f"fabricated fallback warning detected: {hits[0]}"]
    return []


def assert_no_fabricated_fallback(warnings: list[str]) -> None:
    errors = validate_no_fabricated_fallback(warnings)
    if errors:
        raise LiveVerificationError(
            errors[0],
            category="fabricated_fallback",
        )


def series_to_check_payload(series: NormalizedMarketSeries) -> dict[str, Any]:
    prov = provenance_as_dict(series.provenance)
    return {
        "ok": True,
        "symbol": prov.get("canonical_symbol") or series.symbol,
        "provider": prov.get("provider"),
        "row_count": prov.get("row_count", len(series.frame)),
        "actual_start": prov.get("actual_start"),
        "actual_end": prov.get("actual_end"),
        "cache_hit": prov.get("cache_hit", False),
        "cache_stale": prov.get("cache_stale", False),
        "warnings": list(series.warnings),
        "asset_class": prov.get("asset_class"),
        "exchange": prov.get("exchange"),
        "adjustment": prov.get("adjustment"),
    }


def execution_to_check_payload(result: dict[str, Any]) -> dict[str, Any]:
    provenance = provenance_as_dict(result["provenance"])
    return {
        "ok": True,
        "symbol": provenance.get("canonical_symbol") or provenance.get("symbol"),
        "provider": provenance.get("provider"),
        "row_count": provenance.get("row_count"),
        "actual_start": provenance.get("actual_start"),
        "actual_end": provenance.get("actual_end"),
        "cache_hit": provenance.get("cache_hit", False),
        "cache_stale": provenance.get("cache_stale", False),
        "warnings": list(result.get("warnings", [])),
        "observation_count": result.get("metrics", {}).get("observation_count"),
        "asset_class": provenance.get("asset_class"),
        "exchange": provenance.get("exchange"),
        "adjustment": provenance.get("adjustment"),
    }


def dumps_check_payload(payload: dict[str, Any]) -> str:
    assert_json_safe(payload)
    return json.dumps(payload, indent=2, sort_keys=True)
