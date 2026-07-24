"""Factor validation application service — builds panels, runs pure engines."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from app.factor_validation.factors import (
    COMING_SOON_FACTORS,
    align_factor_and_forward,
    build_factor_panel,
    build_monthly_forward_returns,
    build_price_panel,
    resolve_universe,
)
from app.factor_validation.quantile_portfolios import compute_quantile_portfolios
from app.factor_validation.rank_ic import (
    compute_rank_ic_series,
    rolling_ic,
    summarize_ic,
)
from app.research_execution.market_data_port import (
    MarketDataError,
    MarketDataPort,
    utc_now_iso,
)
from app.research_validation.result_store import (
    InMemoryValidationResultStore,
    ValidationResultStore,
)

RESEARCH_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-_]{1,63}$")
CANONICAL_FACTOR_RESEARCH_ID = "cross-sectional-factor-sector-etfs"


class FactorValidationError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _finite_nonneg(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise FactorValidationError(f"{name} must be a number.") from exc
    if not math.isfinite(number) or number < 0:
        raise FactorValidationError(f"{name} must be a finite non-negative number.")
    return number


def _holding_months(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise FactorValidationError("holding_period_months must be an integer.") from exc
    if isinstance(value, bool) or float(value) != number or number < 1 or number > 12:
        raise FactorValidationError("holding_period_months must be an integer from 1 to 12.")
    return number


def _series_from_ic(ic: pd.Series) -> list[dict[str, Any]]:
    return [{"date": str(idx), "value": float(val)} for idx, val in ic.items()]


class FactorValidationService:
    def __init__(
        self,
        market_data: MarketDataPort,
        result_store: ValidationResultStore | None = None,
    ) -> None:
        self._market_data = market_data
        self._result_store = result_store or InMemoryValidationResultStore()

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        research_id = str(payload.get("research_id") or CANONICAL_FACTOR_RESEARCH_ID).strip()
        if not RESEARCH_ID_PATTERN.match(research_id):
            raise FactorValidationError(
                "research_id must be 2–64 chars of lowercase letters, digits, -, _."
            )

        factor_id = str(payload.get("factor_id") or "momentum").strip().lower()
        if factor_id in COMING_SOON_FACTORS:
            raise FactorValidationError(
                f"Factor '{factor_id}' is Coming Soon.",
                status_code=400,
            )

        universe_id = str(payload.get("universe_id") or "us_sector_etfs").strip().lower()
        try:
            symbols = resolve_universe(universe_id)
        except ValueError as exc:
            raise FactorValidationError(str(exc)) from exc

        rebalance = str(payload.get("rebalance_frequency") or "monthly").strip().lower()
        if rebalance != "monthly":
            raise FactorValidationError("Only monthly rebalance_frequency is supported in v1.")

        holding = _holding_months(payload.get("holding_period_months", 1))
        cost_rate = _finite_nonneg(payload.get("transaction_cost", 0.001), "transaction_cost")
        start_date = str(payload.get("start_date") or "2018-01-01").strip()
        end_date = payload.get("end_date")
        end_date_str = str(end_date).strip() if end_date else None

        warnings: list[str] = []
        price_map: dict[str, pd.Series] = {}
        symbol_provenance: list[dict[str, Any]] = []

        for symbol in symbols:
            try:
                series = self._market_data.get_daily_ohlcv(
                    symbol, start_date, end_date_str
                )
            except MarketDataError as exc:
                warnings.append(f"{symbol}: {exc}")
                continue
            close = self._extract_close(series, symbol)
            if close is None or close.empty:
                warnings.append(f"{symbol}: empty close series")
                continue
            price_map[symbol] = close
            prov = getattr(series, "provenance", None)
            symbol_provenance.append(
                {
                    "symbol": symbol,
                    "provider": getattr(prov, "provider", None) if prov else None,
                    "rows": int(len(close)),
                }
            )

        if len(price_map) < 5:
            raise FactorValidationError(
                "Fewer than 5 symbols with usable prices; cannot run quantile validation.",
                status_code=422,
            )

        price_panel = build_price_panel(price_map)
        try:
            factor = build_factor_panel(factor_id, price_panel)
        except ValueError as exc:
            raise FactorValidationError(str(exc)) from exc

        forward = build_monthly_forward_returns(
            price_panel, holding_period_months=holding
        )
        factor_aligned, forward_aligned = align_factor_and_forward(factor, forward)
        if factor_aligned.empty:
            raise FactorValidationError(
                "No overlapping month-end periods with enough names for factor validation.",
                status_code=422,
            )

        # Use period labels as YYYY-MM for stable JSON
        factor_aligned = factor_aligned.copy()
        forward_aligned = forward_aligned.copy()
        factor_aligned.index = pd.Index(
            [idx.strftime("%Y-%m") if hasattr(idx, "strftime") else str(idx) for idx in factor_aligned.index]
        )
        forward_aligned.index = factor_aligned.index

        rank_ic = compute_rank_ic_series(factor_aligned, forward_aligned)
        ic_summary = summarize_ic(rank_ic)
        rolled = rolling_ic(rank_ic)
        quantiles = compute_quantile_portfolios(
            factor_aligned, forward_aligned, cost_rate=cost_rate
        )

        if ic_summary["n_periods"] == 0:
            warnings.append("RankIC series empty after cross-section filters.")
        if quantiles["n_rebalances"] == 0:
            warnings.append("No quantile rebalances produced.")

        generated_at = utc_now_iso()
        result: dict[str, Any] = {
            "research_id": research_id,
            "template": "cross_sectional_factor",
            "universe_id": universe_id,
            "factor_id": factor_id,
            "rebalance_frequency": rebalance,
            "holding_period_months": holding,
            "ic": {
                "series": _series_from_ic(rank_ic),
                "rolling_series": _series_from_ic(rolled),
                "summary": ic_summary,
            },
            "quantiles": {
                "period_returns": quantiles["period_returns"],
                "cumulative_returns": quantiles["cumulative_returns"],
                "turnover": quantiles["turnover"],
                "transaction_cost": quantiles["transaction_cost"],
                "n_rebalances": quantiles["n_rebalances"],
            },
            "long_short": quantiles["long_short"],
            "warnings": warnings,
            "provenance": {
                "universe_symbols": list(symbols),
                "symbols_used": sorted(price_map.keys()),
                "symbol_series": symbol_provenance,
                "start_date": start_date,
                "end_date": end_date_str,
                "n_factor_periods": int(len(factor_aligned)),
            },
            "generated_at": generated_at,
            # Shape marker so Copilot / Evaluation can detect factor evidence
            "evidence_kind": "factor_validation",
            "validation_status": "completed" if quantiles["n_rebalances"] > 0 else "incomplete",
        }

        validation_run_id = self._result_store.save(result)
        result["validation_run_id"] = validation_run_id
        return result

    @staticmethod
    def _extract_close(series: Any, symbol: str) -> pd.Series | None:
        frame = getattr(series, "frame", None)
        if not isinstance(frame, pd.DataFrame) or frame.empty:
            return None
        work = frame.copy()
        if "date" in work.columns:
            work["date"] = pd.to_datetime(work["date"])
            work = work.set_index("date").sort_index()
        for col in ("close", "Close", "adj_close", "Adj Close"):
            if col in work.columns:
                out = work[col].astype(float)
                out.name = symbol
                return out
        # Do not guess an arbitrary numeric column — that can invent prices.
        return None
