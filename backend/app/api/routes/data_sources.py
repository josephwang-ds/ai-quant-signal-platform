"""数据源状态 API。"""

from fastapi import APIRouter

from app.services.market_data_service import AUTO_CHAIN_A_SHARE, AUTO_CHAIN_DEFAULT

router = APIRouter(prefix="/api/data-sources", tags=["data-sources"])


def _akshare_installed() -> bool:
    try:
        import akshare  # noqa: F401

        return True
    except ImportError:
        return False


@router.get("/status")
def get_data_sources_status() -> dict:
    """返回当前与规划中的数据源状态。"""
    akshare_ready = _akshare_installed()
    return {
        "active_provider": "auto",
        "fallback_chain": {
            "default": list(AUTO_CHAIN_DEFAULT),
            "a_share": list(AUTO_CHAIN_A_SHARE),
        },
        "providers": [
            {
                "name": "auto",
                "status": "active",
                "asset_classes": [
                    "US stocks",
                    "ETFs",
                    "HK stocks",
                    "A-shares",
                    "indices (partial)",
                ],
                "note": (
                    "Automatic failover. Order: AKShare → Yahoo → Stooq. "
                    "Prefer AKShare for China network stability."
                ),
            },
            {
                "name": "akshare",
                "status": "active" if akshare_ready else "degraded",
                "asset_classes": [
                    "A-shares",
                    "US stocks",
                ],
                "note": (
                    "Free China-friendly source (primary). Installed."
                    if akshare_ready
                    else "Package not installed on this server — auto path may skip it."
                ),
            },
            {
                "name": "yahoo",
                "status": "active",
                "asset_classes": [
                    "US stocks",
                    "ETFs",
                    "HK stocks",
                    "basic A-share via .SS/.SZ",
                    "crypto via -USD",
                    "indices",
                    "FX",
                    "futures",
                ],
                "note": "Fallback via yfinance. May be unstable in China.",
            },
            {
                "name": "stooq",
                "status": "active",
                "asset_classes": [
                    "US stocks",
                    "ETFs",
                    "HK stocks",
                    "EU stocks (partial)",
                    "indices (partial)",
                ],
                "note": "Free CSV, no API key. May hit bot checks from some networks; used as last fallback.",
            },
            {
                "name": "coingecko",
                "status": "planned",
            },
            {
                "name": "csv",
                "status": "planned",
            },
        ],
    }
