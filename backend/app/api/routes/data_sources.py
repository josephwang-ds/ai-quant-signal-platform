"""Research market-data provider status API."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/data-sources", tags=["data-sources"])


def _akshare_installed() -> bool:
    try:
        import akshare  # noqa: F401

        return True
    except ImportError:
        return False


def _yahoo_installed() -> bool:
    try:
        import yfinance  # noqa: F401

        return True
    except ImportError:
        return False


@router.get("/status")
def get_data_sources_status() -> dict:
    """
    Return honest research routing capabilities.

    Installed/configured does not imply live connectivity was verified.
    """
    akshare_ready = _akshare_installed()
    yahoo_ready = _yahoo_installed()
    return {
        "routing_mode": "asset_class",
        "providers": [
            {
                "name": "yahoo",
                "installed": yahoo_ready,
                "configured": yahoo_ready,
                "supported_assets": [
                    "us_equity",
                    "hk_equity",
                    "etf",
                    "index",
                    "crypto",
                ],
                "live_health_checked": False,
            },
            {
                "name": "akshare",
                "installed": akshare_ready,
                "configured": akshare_ready,
                "supported_assets": ["cn_equity"],
                "live_health_checked": False,
            },
        ],
        "symbol_examples": [
            "SPY",
            "AAPL",
            "0700.HK",
            "000001.SZ",
            "600519.SH",
            "BTC-USD",
        ],
        "notes": [
            "Research execution routes symbols by asset class behind MarketDataPort.",
            "No automatic cross-provider failover in this release.",
            "Installed status does not mean a live provider health check was run.",
        ],
    }
