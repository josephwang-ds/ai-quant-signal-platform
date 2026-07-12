"""AKShare 免费行情（国内较稳；可选依赖）。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from app.data_providers.base import MarketDataRequest, REQUIRED_OHLCV_COLUMNS
from app.data_providers.symbol_utils import (
    looks_like_a_share,
    normalize_symbol,
    to_akshare_a_share_code,
    to_akshare_us_symbol,
)


class AkshareProvider:
    """通过 AKShare 获取 A 股 / 美股日线。"""

    name = "akshare"

    def get_price_history(self, request: MarketDataRequest) -> pd.DataFrame:
        try:
            import akshare as ak
        except ImportError as exc:
            raise ValueError(
                "AKShare is not installed. Add `akshare` to backend requirements."
            ) from exc

        symbol = normalize_symbol(request.symbol)
        start_date = request.start_date or "2022-01-01"
        end_date = request.end_date or datetime.utcnow().strftime("%Y-%m-%d")

        if looks_like_a_share(symbol):
            last_error: Optional[Exception] = None
            df = None
            for _ in range(2):
                try:
                    df = self._fetch_a_share(ak, symbol, start_date, end_date)
                    break
                except Exception as exc:  # noqa: BLE001 — A 股接口偶发断连，重试一次
                    last_error = exc
            if df is None:
                raise ValueError(f"AKShare A-share failed for '{symbol}': {last_error}") from last_error
        else:
            df = self._fetch_us(ak, symbol, start_date, end_date)

        df["symbol"] = symbol
        df["ticker"] = symbol
        df["data_source"] = "akshare"
        if request.market:
            df["market"] = request.market
        if request.adjustment:
            df["adjustment"] = request.adjustment
        return df.reset_index(drop=True)

    def _fetch_a_share(
        self,
        ak,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        code = to_akshare_a_share_code(symbol)
        raw = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust="qfq",
        )
        if raw is None or raw.empty:
            raise ValueError(f"No AKShare A-share data for '{symbol}'.")

        rename_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        df = raw.rename(columns=rename_map)
        return self._finalize(df, symbol)

    def _fetch_us(
        self,
        ak,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        us_symbol = to_akshare_us_symbol(symbol)
        # stock_us_daily 返回全历史，再按日期过滤
        raw = ak.stock_us_daily(symbol=us_symbol, adjust="qfq")
        if raw is None or raw.empty:
            raise ValueError(f"No AKShare US data for '{symbol}'.")

        rename_map = {
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        }
        df = raw.rename(columns=rename_map)
        df = self._finalize(df, symbol)
        df = df[df["date"] >= pd.Timestamp(start_date)]
        df = df[df["date"] <= pd.Timestamp(end_date)]
        if df.empty:
            raise ValueError(
                f"No AKShare US data for '{symbol}' ({start_date} to {end_date})."
            )
        return df

    def _finalize(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        missing = [col for col in REQUIRED_OHLCV_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"Unexpected AKShare format for '{symbol}': missing {missing}."
            )
        out = df[REQUIRED_OHLCV_COLUMNS].copy()
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out = out.dropna(subset=["date", "open", "high", "low", "close"])
        out = out.sort_values("date")
        if out.empty:
            raise ValueError(f"No AKShare price data for '{symbol}'.")
        return out
