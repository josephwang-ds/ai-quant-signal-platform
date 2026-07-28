"""Build and serve the cross-sectional date × symbol factor panel.

Rolling factor and label calculations run **per symbol** after sorting by
date. Shifts and rolling windows never cross symbol boundaries because each
symbol is processed in isolation before concatenation.
"""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from app.cross_sectional.constants import (
    DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
    DEFAULT_PREVIEW_ROWS,
    DOWNSIDE_VOL_MIN_PERIODS,
    FACTOR_COLUMNS,
    FACTOR_VERSION,
    LABEL_COLUMNS,
    MAX_PREVIEW_ROWS,
    MAX_REQUEST_SYMBOLS,
    METADATA_COLUMNS,
    MIN_HISTORY_DAYS,
    MOMENTUM_FACTORS,
    PANEL_SORT_COLUMNS,
    RISK_FACTORS,
    UNIVERSE_ID_LIQUID_31,
    VOLUME_FACTORS,
)
from app.cross_sectional.factors import compute_all_factors
from app.cross_sectional.labels import compute_forward_labels
from app.cross_sectional.quality import evaluate_panel_quality
from app.cross_sectional.universe import (
    configured_universe_version,
    resolve_universe,
    universe_disclosures,
)
from app.research_execution.market_data_port import (
    MarketDataError,
    MarketDataPort,
    utc_now_iso,
)
from app.research_reproducibility import build_reproducibility_manifest
from app.research_validation.result_store import (
    InMemoryValidationResultStore,
    ValidationResultStore,
)

RESEARCH_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-_]{1,63}$")
EVIDENCE_KIND = "cross_sectional_dataset"
TEMPLATE_ID = "cross_sectional_factor"


class CrossSectionalDatasetError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DuplicateDateError(ValueError):
    """Raised when a single-symbol OHLCV frame has duplicate dates."""


def _finite_nonneg(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CrossSectionalDatasetError(f"{name} must be a number.") from exc
    if not math.isfinite(number) or number < 0:
        raise CrossSectionalDatasetError(f"{name} must be a finite non-negative number.")
    return number


def _parse_iso_date(value: str, *, field_name: str) -> date:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise CrossSectionalDatasetError(
            f"{field_name} must be an ISO date (YYYY-MM-DD)."
        ) from exc


def _as_jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return str(value.date())
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value


def build_symbol_panel(
    frame: pd.DataFrame,
    *,
    symbol: str,
    source: str,
    data_as_of: str,
    universe_version: str,
    liquidity_dollar_volume_floor: float,
) -> pd.DataFrame:
    """
    Build one symbol's long panel rows from normalized OHLCV.

    Sorts by date before rolling calculations. Does not forward-fill prices.
    Duplicate dates are rejected before any factor/label calculation.
    """
    if frame is None or frame.empty:
        return pd.DataFrame()

    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"])
    if work["date"].duplicated().any():
        raise DuplicateDateError(
            f"Duplicate dates detected for symbol {symbol.upper().strip()} "
            "before factor calculation."
        )
    work = work.sort_values("date").reset_index(drop=True)

    close = pd.to_numeric(work["close"], errors="coerce")
    volume = pd.to_numeric(work["volume"], errors="coerce")
    # Factors never receive forward labels — labels computed separately.
    factors = compute_all_factors(
        close,
        volume,
        liquidity_dollar_volume_floor=liquidity_dollar_volume_floor,
    )
    labels = compute_forward_labels(close)

    out = pd.DataFrame(
        {
            "date": work["date"],
            "symbol": symbol.upper().strip(),
            "open": pd.to_numeric(work["open"], errors="coerce"),
            "high": pd.to_numeric(work["high"], errors="coerce"),
            "low": pd.to_numeric(work["low"], errors="coerce"),
            "close": close,
            "volume": volume,
            "source": source,
            "data_as_of": data_as_of,
            "factor_version": FACTOR_VERSION,
            "universe_version": universe_version,
        }
    )
    out = pd.concat(
        [out, factors.reset_index(drop=True), labels.reset_index(drop=True)],
        axis=1,
    )
    return out.replace([np.inf, -np.inf], np.nan)


def build_cross_sectional_panel(
    frames_by_symbol: dict[str, pd.DataFrame],
    *,
    provenance_by_symbol: dict[str, dict[str, Any]],
    universe_version: str,
    liquidity_dollar_volume_floor: float,
    calculation_failures: list[dict[str, str]] | None = None,
) -> pd.DataFrame:
    """
    Build per-symbol panels in isolation, then concatenate and sort.

    Rolling windows and shifts cannot cross symbol boundaries because each
    symbol is calculated independently before the final sort by (symbol, date).
    """
    failures = calculation_failures if calculation_failures is not None else []
    pieces: list[pd.DataFrame] = []
    for symbol, frame in frames_by_symbol.items():
        meta = provenance_by_symbol.get(symbol, {})
        try:
            piece = build_symbol_panel(
                frame,
                symbol=symbol,
                source=str(meta.get("source") or meta.get("provider") or "unknown"),
                data_as_of=str(meta.get("actual_end") or meta.get("retrieved_at") or ""),
                universe_version=universe_version,
                liquidity_dollar_volume_floor=liquidity_dollar_volume_floor,
            )
        except DuplicateDateError as exc:
            failures.append(
                {
                    "symbol": symbol,
                    "error": str(exc),
                    "category": "calculation",
                }
            )
            continue
        if not piece.empty:
            pieces.append(piece)
    if not pieces:
        return pd.DataFrame()
    panel = pd.concat(pieces, ignore_index=True)
    return panel.sort_values(list(PANEL_SORT_COLUMNS)).reset_index(drop=True)


def feature_metadata() -> list[dict[str, Any]]:
    meta: list[dict[str, Any]] = []
    for name in MOMENTUM_FACTORS:
        meta.append(
            {
                "name": name,
                "family": "momentum",
                "uses_future": False,
                "description": "Trailing price momentum / distance-to-MA factor.",
            }
        )
    for name in RISK_FACTORS:
        description = (
            "Annualized downside deviation: "
            f"sqrt(mean(min(r,0)^2)) * sqrt(252) over {DOWNSIDE_VOL_MIN_PERIODS} "
            "observations (field name retained for API stability)."
            if name == "downside_volatility_20d"
            else "Trailing risk / drawdown factor (annualized vols)."
        )
        meta.append(
            {
                "name": name,
                "family": "risk",
                "uses_future": False,
                "description": description,
            }
        )
    for name in VOLUME_FACTORS:
        meta.append(
            {
                "name": name,
                "family": "volume",
                "uses_future": False,
                "description": "Volume / liquidity factor.",
            }
        )
    for name in LABEL_COLUMNS:
        horizon = 5 if name.endswith("5d") else 20
        meta.append(
            {
                "name": name,
                "family": "label",
                "uses_future": True,
                "label_horizon": horizon,
                "description": f"Forward {horizon}-day return label (not a feature).",
            }
        )
    return meta


class CrossSectionalDatasetService:
    """Orchestrates MarketDataPort → factor panel → quality report.

    Does not mutate Trend Following or Factor Validation research state.
    Only appends a summary artifact to ValidationResultStore under a new
    ``dataset_run_id``.
    """

    def __init__(
        self,
        market_data: MarketDataPort,
        result_store: ValidationResultStore | None = None,
    ) -> None:
        self._market_data = market_data
        self._result_store = result_store or InMemoryValidationResultStore()

    def load_panel(self, payload: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
        """
        Build the full date×symbol panel for internal research use.

        Not exposed over HTTP. Phase 2 research reuses this instead of
        recalculating factors. Does not write to the result store.
        """
        universe_id = str(
            payload.get("universe_id") or UNIVERSE_ID_LIQUID_31
        ).strip().lower()
        symbols_override = payload.get("symbols")
        if symbols_override is not None and len(symbols_override) > MAX_REQUEST_SYMBOLS:
            raise CrossSectionalDatasetError(
                f"symbols must contain at most {MAX_REQUEST_SYMBOLS} tickers."
            )
        try:
            symbols = resolve_universe(
                universe_id,
                symbols_override=symbols_override,
            )
        except ValueError as exc:
            raise CrossSectionalDatasetError(str(exc)) from exc

        if len(symbols) > MAX_REQUEST_SYMBOLS:
            raise CrossSectionalDatasetError(
                f"Resolved universe exceeds {MAX_REQUEST_SYMBOLS} symbols."
            )

        start_date = str(payload.get("start_date") or "2019-01-01").strip()
        end_date_raw = payload.get("end_date")
        end_date = str(end_date_raw).strip() if end_date_raw else None
        start_parsed = _parse_iso_date(start_date, field_name="start_date")
        if end_date:
            end_parsed = _parse_iso_date(end_date, field_name="end_date")
            if start_parsed >= end_parsed:
                raise CrossSectionalDatasetError(
                    "start_date must be earlier than end_date."
                )

        universe_version = configured_universe_version(universe_id)
        min_history_days = int(payload.get("min_history_days", MIN_HISTORY_DAYS))
        if min_history_days < 20 or min_history_days > 252:
            raise CrossSectionalDatasetError(
                "min_history_days must be between 20 and 252."
            )
        liquidity_floor = _finite_nonneg(
            payload.get(
                "liquidity_dollar_volume_floor",
                DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
            ),
            "liquidity_dollar_volume_floor",
        )

        frames: dict[str, pd.DataFrame] = {}
        provenance_by_symbol: dict[str, dict[str, Any]] = {}
        provider_failures: list[dict[str, str]] = []
        calculation_failures: list[dict[str, str]] = []
        warnings: list[str] = list(universe_disclosures(universe_id))

        for symbol in symbols:
            try:
                series = self._market_data.get_daily_ohlcv(symbol, start_date, end_date)
            except MarketDataError as exc:
                provider_failures.append(
                    {"symbol": symbol, "error": str(exc), "category": "provider"}
                )
                continue
            except Exception as exc:  # noqa: BLE001
                provider_failures.append(
                    {
                        "symbol": symbol,
                        "error": f"Unexpected market-data failure: {exc}",
                        "category": "provider",
                    }
                )
                continue

            frame = series.frame
            if frame is None or frame.empty:
                provider_failures.append(
                    {
                        "symbol": symbol,
                        "error": "Empty OHLCV frame.",
                        "category": "provider",
                    }
                )
                continue

            frames[series.symbol] = frame
            provenance_by_symbol[series.symbol] = {
                "provider": series.provenance.provider,
                "source": series.provenance.source,
                "retrieved_at": series.provenance.retrieved_at,
                "actual_start": series.provenance.actual_start,
                "actual_end": series.provenance.actual_end,
                "adjustment": series.provenance.adjustment,
                "row_count": int(len(frame)),
            }
            warnings.extend(series.warnings)

        panel = build_cross_sectional_panel(
            frames,
            provenance_by_symbol=provenance_by_symbol,
            universe_version=universe_version,
            liquidity_dollar_volume_floor=liquidity_floor,
            calculation_failures=calculation_failures,
        )
        failed_calc_symbols = {f["symbol"] for f in calculation_failures}
        loaded_symbols = tuple(
            sorted(s for s in frames.keys() if s not in failed_calc_symbols)
        )
        quality = evaluate_panel_quality(
            panel,
            requested_symbols=symbols,
            loaded_symbols=loaded_symbols,
            provider_failures=provider_failures + calculation_failures,
            min_history_days=min_history_days,
        )
        warnings.extend(quality.get("warnings") or [])
        seen_warn: set[str] = set()
        unique_warnings: list[str] = []
        for item in warnings:
            text = str(item).strip()
            if text and text not in seen_warn:
                seen_warn.add(text)
                unique_warnings.append(text)

        unavailable: list[str] = ["sector"]
        if provider_failures or calculation_failures:
            unavailable.append("full_universe_ohlcv")

        providers = sorted(
            {
                str(meta.get("provider"))
                for sym, meta in provenance_by_symbol.items()
                if sym in loaded_symbols and meta.get("provider")
            }
        )
        meta = {
            "symbols": list(symbols),
            "loaded_symbols": list(loaded_symbols),
            "universe_id": universe_id,
            "universe_version": universe_version,
            "start_date": start_date,
            "end_date": end_date,
            "warnings": unique_warnings,
            "unavailable_evidence": unavailable,
            "quality_status": quality["status"],
            "quality": quality,
            "dataset_summary": {
                "n_rows": int(len(panel)),
                "n_dates": int(panel["date"].nunique()) if not panel.empty else 0,
                "n_symbols": int(panel["symbol"].nunique()) if not panel.empty else 0,
                "date_start": quality["coverage"].get("date_start"),
                "date_end": quality["coverage"].get("date_end"),
                "factors": list(FACTOR_COLUMNS),
                "labels": list(LABEL_COLUMNS),
                "factor_version": FACTOR_VERSION,
                "universe_version": universe_version,
                "grain": "date_symbol",
                "sorted_by": list(PANEL_SORT_COLUMNS),
            },
            "provenance": {
                "requested_symbols": list(symbols),
                "loaded_symbols": list(loaded_symbols),
                "provider_failures": provider_failures,
                "calculation_failures": calculation_failures,
                "providers": providers,
                "adjustment": "auto",
                "disclosures": list(universe_disclosures(universe_id)),
            },
        }
        return panel, meta

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(
            payload.get("research_id") or "cross-sectional-equity-liquid-v1"
        ).strip()
        if not RESEARCH_ID_PATTERN.match(research_id):
            raise CrossSectionalDatasetError(
                "research_id must be 2–64 chars of lowercase letters, digits, -, _."
            )

        preview_rows = int(payload.get("preview_rows", DEFAULT_PREVIEW_ROWS))
        if preview_rows < 0 or preview_rows > MAX_PREVIEW_ROWS:
            raise CrossSectionalDatasetError(
                f"preview_rows must be between 0 and {MAX_PREVIEW_ROWS}."
            )

        panel, meta = self.load_panel(payload)
        quality = meta["quality"]
        universe_id = meta["universe_id"]
        universe_version = meta["universe_version"]
        symbols = meta["symbols"]
        loaded_symbols = meta["loaded_symbols"]
        start_date = meta["start_date"]
        end_date = meta["end_date"]
        unique_warnings = list(meta["warnings"])
        unavailable = list(meta["unavailable_evidence"])

        preview: list[dict[str, Any]] = []
        if not panel.empty and preview_rows > 0:
            preview_frame = panel.head(preview_rows)
            preview_cols = [
                c
                for c in list(METADATA_COLUMNS)
                + ["open", "high", "low", "close", "volume"]
                + list(FACTOR_COLUMNS)
                + list(LABEL_COLUMNS)
                if c in preview_frame.columns
            ]
            for row in preview_frame.loc[:, preview_cols].to_dict(orient="records"):
                preview.append({k: _as_jsonable(v) for k, v in row.items()})

        benchmark = str(payload.get("benchmark") or "SPY").strip().upper() or "SPY"
        liquidity_floor = _finite_nonneg(
            payload.get(
                "liquidity_dollar_volume_floor",
                DEFAULT_LIQUIDITY_DOLLAR_VOLUME_FLOOR,
            ),
            "liquidity_dollar_volume_floor",
        )
        min_history_days = int(payload.get("min_history_days", MIN_HISTORY_DAYS))

        configuration = {
            "research_id": research_id,
            "universe_id": universe_id,
            "symbols": list(symbols),
            "benchmark": benchmark,
            "start_date": start_date,
            "end_date": end_date,
            "min_history_days": min_history_days,
            "liquidity_dollar_volume_floor": liquidity_floor,
            "preview_rows": preview_rows,
            "factor_version": FACTOR_VERSION,
            "universe_version": universe_version,
            "label_horizons": [5, 20],
        }

        provenance = {
            **meta["provenance"],
            "benchmark": benchmark,
        }

        generated_at = utc_now_iso()
        result = {
            "research_id": research_id,
            "template": TEMPLATE_ID,
            "evidence_kind": EVIDENCE_KIND,
            "configuration": configuration,
            "dataset_summary": meta["dataset_summary"],
            "quality_summary": {
                "status": quality["status"],
                "checks": quality["checks"],
                "null_accounting": quality.get("null_accounting", {}),
            },
            "coverage_summary": quality["coverage"],
            "feature_metadata": feature_metadata(),
            "records_preview": preview,
            "unavailable_evidence": unavailable,
            "warnings": unique_warnings,
            "provenance": provenance,
            "generated_at": generated_at,
            "validation_status": quality["status"],
        }
        providers = meta["provenance"].get("providers") or []
        result["reproducibility_manifest"] = build_reproducibility_manifest(
            data_source=providers[0] if len(providers) == 1 else (providers or None),
            symbol=None,
            universe={"universe_id": universe_id, "symbols": list(loaded_symbols)},
            requested_start_date=start_date,
            requested_end_date=end_date,
            actual_start_date=meta["dataset_summary"].get("date_start"),
            actual_end_date=meta["dataset_summary"].get("date_end"),
            row_count=meta["dataset_summary"].get("n_rows"),
            adjustment_mode="auto",
            protocol={
                "research_id": research_id,
                "evidence_kind": EVIDENCE_KIND,
                "universe_id": universe_id,
                "universe_version": universe_version,
                "factor_version": FACTOR_VERSION,
                "start_date": start_date,
                "end_date": end_date,
                "liquidity_dollar_volume_floor": liquidity_floor,
            },
            frame=panel if not panel.empty else None,
            created_at=generated_at,
        )

        dataset_run_id = self._result_store.save(result)
        result["dataset_run_id"] = dataset_run_id
        return result
