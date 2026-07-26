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
from app.factor_validation.benchmark import build_factor_benchmark
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
from app.research_reproducibility import build_reproducibility_manifest, hash_ohlcv_frame
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
        min_mean_rank_ic = float(payload.get("min_mean_rank_ic", 0.0))
        min_positive_ic_ratio = float(payload.get("min_positive_ic_ratio", 0.5))
        min_net_long_short_return = float(
            payload.get("min_net_long_short_return", 0.0)
        )
        min_q5_excess_return = float(payload.get("min_q5_excess_return", 0.0))
        max_mean_turnover = _finite_nonneg(
            payload.get("max_mean_turnover", 2.0), "max_mean_turnover"
        )
        min_observations = int(payload.get("min_observations", 24))
        min_icir = float(payload.get("min_icir", 0.0))
        if not 0 <= min_positive_ic_ratio <= 1:
            raise FactorValidationError(
                "min_positive_ic_ratio must be between 0 and 1."
            )
        if min_observations < 1:
            raise FactorValidationError("min_observations must be >= 1.")
        start_date = str(payload.get("start_date") or "2018-01-01").strip()
        end_date = payload.get("end_date")
        end_date_str = str(end_date).strip() if end_date else None

        warnings: list[str] = []
        price_map: dict[str, pd.Series] = {}
        symbol_provenance: list[dict[str, Any]] = []
        hash_frames: list[pd.DataFrame] = []
        retrieval_timestamps: list[str] = []
        adjustments: list[str] = []
        providers: list[str] = []

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
            frame = getattr(series, "frame", None)
            if isinstance(frame, pd.DataFrame) and not frame.empty:
                piece = frame.copy()
                if "symbol" not in piece.columns:
                    piece["symbol"] = symbol
                hash_frames.append(piece)
            if prov is not None:
                retrieved = getattr(prov, "retrieved_at", None)
                if retrieved:
                    retrieval_timestamps.append(str(retrieved))
                adjustment = getattr(prov, "adjustment", None)
                if adjustment:
                    adjustments.append(str(adjustment))
                provider = getattr(prov, "provider", None)
                if provider:
                    providers.append(str(provider))

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
        generated_at = utc_now_iso()
        benchmark = build_factor_benchmark(
            factor_id=factor_id,
            forward_returns=forward_aligned,
            rank_ic=rank_ic,
            ic_summary=ic_summary,
            quantiles=quantiles,
            min_mean_rank_ic=min_mean_rank_ic,
            min_positive_ic_ratio=min_positive_ic_ratio,
            min_net_long_short_return=min_net_long_short_return,
            min_q5_excess_return=min_q5_excess_return,
            max_mean_turnover=max_mean_turnover,
            min_observations=min_observations,
            min_icir=min_icir,
            evidence_timestamp=generated_at,
        )

        if ic_summary["n_periods"] == 0:
            warnings.append("RankIC series empty after cross-section filters.")
        if quantiles["n_rebalances"] == 0:
            warnings.append("No quantile rebalances produced.")

        combined_frame = (
            pd.concat(hash_frames, ignore_index=True) if hash_frames else None
        )
        actual_start = None
        actual_end = None
        if combined_frame is not None and "date" in combined_frame.columns:
            dates = pd.to_datetime(combined_frame["date"], errors="coerce").dropna()
            if not dates.empty:
                actual_start = dates.min().date().isoformat()
                actual_end = dates.max().date().isoformat()
        unique_providers = sorted(set(providers))
        unique_adjustments = sorted(set(adjustments))
        reproducibility_manifest = build_reproducibility_manifest(
            data_source=unique_providers[0] if len(unique_providers) == 1 else (
                unique_providers or None
            ),
            symbol=None,
            universe={
                "universe_id": universe_id,
                "symbols": sorted(price_map.keys()),
            },
            requested_start_date=start_date,
            requested_end_date=end_date_str,
            actual_start_date=actual_start,
            actual_end_date=actual_end,
            retrieval_timestamp=sorted(retrieval_timestamps)[0]
            if retrieval_timestamps
            else None,
            row_count=int(len(combined_frame)) if combined_frame is not None else 0,
            adjustment_mode=unique_adjustments[0]
            if len(unique_adjustments) == 1
            else (unique_adjustments or None),
            protocol={
                "research_id": research_id,
                "template": "cross_sectional_factor",
                "universe_id": universe_id,
                "factor_id": factor_id,
                "rebalance_frequency": rebalance,
                "holding_period_months": holding,
                "transaction_cost": cost_rate,
            },
            data_hash=hash_ohlcv_frame(combined_frame),
            created_at=generated_at,
        )
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
            "benchmark": benchmark,
            "warnings": warnings,
            "provenance": {
                "universe_symbols": list(symbols),
                "symbols_used": sorted(price_map.keys()),
                "symbol_series": symbol_provenance,
                "start_date": start_date,
                "end_date": end_date_str,
                "n_factor_periods": int(len(factor_aligned)),
            },
            "reproducibility_manifest": reproducibility_manifest,
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
