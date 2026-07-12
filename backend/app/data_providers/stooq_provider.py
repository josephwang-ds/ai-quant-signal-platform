"""Stooq 免费日线行情（CSV，无需 API Key）。"""

from __future__ import annotations

from datetime import datetime
from io import StringIO
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

from app.data_providers.base import MarketDataRequest, REQUIRED_OHLCV_COLUMNS
from app.data_providers.symbol_utils import normalize_symbol, to_stooq_symbol

STOOQ_CSV_URL = "https://stooq.com/q/d/l/?s={symbol}&i=d"
USER_AGENT = "ai-quant-signal-platform/1.0 (+research-demo)"


class StooqProvider:
    """通过 Stooq 公开 CSV 拉取日线 OHLCV。"""

    name = "stooq"

    def get_price_history(self, request: MarketDataRequest) -> pd.DataFrame:
        symbol = normalize_symbol(request.symbol)
        stooq_symbol = to_stooq_symbol(symbol)
        start_date = request.start_date or "2022-01-01"
        end_date = request.end_date

        url = STOOQ_CSV_URL.format(symbol=stooq_symbol)
        csv_text = self._download_csv(url)
        if not csv_text or "Date" not in csv_text.splitlines()[0]:
            raise ValueError(
                f"No Stooq price data for '{symbol}' (mapped as '{stooq_symbol}')."
            )

        df = pd.read_csv(StringIO(csv_text))
        if df.empty:
            raise ValueError(
                f"No Stooq price data for '{symbol}' (mapped as '{stooq_symbol}')."
            )

        rename_map = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        df = df.rename(columns=rename_map)
        missing = [col for col in REQUIRED_OHLCV_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(
                f"Unexpected Stooq format for '{symbol}': missing {missing}."
            )

        df = df[REQUIRED_OHLCV_COLUMNS].copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date", "open", "high", "low", "close"])
        df = df.sort_values("date")

        start_ts = pd.Timestamp(start_date)
        df = df[df["date"] >= start_ts]
        if end_date:
            df = df[df["date"] <= pd.Timestamp(end_date)]

        if df.empty:
            range_label = f"{start_date} to {end_date}" if end_date else f"since {start_date}"
            raise ValueError(
                f"No Stooq price data for '{symbol}' ({range_label})."
            )

        df["symbol"] = symbol
        df["ticker"] = symbol
        df["data_source"] = "stooq"
        if request.market:
            df["market"] = request.market
        if request.adjustment:
            df["adjustment"] = request.adjustment

        return df.reset_index(drop=True)

    def _download_csv(self, url: str) -> str:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ValueError(f"Stooq download failed: {exc}") from exc

        # Stooq 偶尔返回 No data 文本
        text = raw.decode("utf-8", errors="replace").strip()
        if not text or text.lower().startswith("no data"):
            return ""
        # Stooq 有时返回浏览器校验页，视为失败以触发回退
        if "<html" in text.lower() or "verify your browser" in text.lower():
            raise ValueError("Stooq returned a browser verification page")
        return text
