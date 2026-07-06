"""数据源状态 API。"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/data-sources", tags=["data-sources"])

_DATA_SOURCES_STATUS = {
    "active_provider": "yahoo",
    "providers": [
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
            "note": "Used for research/demo data. Not trading-grade.",
        },
        {
            "name": "akshare",
            "status": "planned",
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


@router.get("/status")
def get_data_sources_status() -> dict:
    """返回当前与规划中的数据源状态。"""
    return _DATA_SOURCES_STATUS
