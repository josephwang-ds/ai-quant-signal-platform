"""统一行情数据服务入口。"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.data_providers.akshare_provider import AkshareProvider
from app.data_providers.base import MarketDataRequest, REQUIRED_OHLCV_COLUMNS
from app.data_providers.stooq_provider import StooqProvider
from app.data_providers.symbol_utils import looks_like_a_share
from app.data_providers.yahoo_provider import YahooProvider

# 缓存层未来将包装 MarketDataService，而非直接调用提供方。

# auto 回退顺序：国内优先 AKShare，Yahoo / Stooq 垫底
AUTO_CHAIN_DEFAULT = ("akshare", "yahoo", "stooq")
AUTO_CHAIN_A_SHARE = ("akshare", "yahoo", "stooq")


class MarketDataService:
    """按 data_source 路由到具体行情提供方；支持 auto 多源回退。"""

    def __init__(self) -> None:
        self.providers = {
            "yahoo": YahooProvider(),
            "stooq": StooqProvider(),
            "akshare": AkshareProvider(),
        }

    def list_providers(self) -> list[str]:
        return list(self.providers.keys())

    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        market: Optional[str] = None,
        data_source: str = "auto",
        adjustment: Optional[str] = None,
    ) -> pd.DataFrame:
        source = (data_source or "auto").strip().lower()
        if source in {"auto", "fallback"}:
            return self._get_with_fallback(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                market=market,
                adjustment=adjustment,
            )

        return self._get_from_provider(
            source=source,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            market=market,
            adjustment=adjustment,
        )

    def _resolve_auto_chain(self, symbol: str) -> tuple[str, ...]:
        if looks_like_a_share(symbol):
            return AUTO_CHAIN_A_SHARE
        return AUTO_CHAIN_DEFAULT

    def _get_with_fallback(
        self,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        market: Optional[str],
        adjustment: Optional[str],
    ) -> pd.DataFrame:
        errors: list[str] = []
        for source in self._resolve_auto_chain(symbol):
            try:
                return self._get_from_provider(
                    source=source,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    market=market,
                    adjustment=adjustment,
                )
            except Exception as exc:  # noqa: BLE001 — 聚合多源失败原因
                errors.append(f"{source}: {exc}")

        detail = " | ".join(errors) if errors else "no providers available"
        raise ValueError(
            f"All data sources failed for '{symbol}'. Tried: {detail}"
        )

    def _get_from_provider(
        self,
        source: str,
        symbol: str,
        start_date: Optional[str],
        end_date: Optional[str],
        market: Optional[str],
        adjustment: Optional[str],
    ) -> pd.DataFrame:
        provider = self.providers.get(source)
        if provider is None:
            raise ValueError(f"Unsupported data source: {source}")

        request = MarketDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_source=source,
            adjustment=adjustment,
        )
        df = provider.get_price_history(request)

        missing_cols = [col for col in REQUIRED_OHLCV_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Provider '{source}' returned incomplete data: missing {missing_cols}."
            )

        # 统一保证 data_source 列存在
        if "data_source" not in df.columns:
            df = df.copy()
            df["data_source"] = source
        return df


_default_service: Optional[MarketDataService] = None


def get_market_data_service() -> MarketDataService:
    """返回进程内单例 MarketDataService。"""
    global _default_service
    if _default_service is None:
        _default_service = MarketDataService()
    return _default_service
