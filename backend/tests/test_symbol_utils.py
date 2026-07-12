"""symbol_utils / Stooq 映射单元测试。"""

from app.data_providers.symbol_utils import (
    looks_like_a_share,
    to_akshare_a_share_code,
    to_stooq_symbol,
)


def test_to_stooq_us_symbol() -> None:
    assert to_stooq_symbol("AAPL") == "aapl.us"
    assert to_stooq_symbol("MSFT") == "msft.us"


def test_to_stooq_hk_and_cn() -> None:
    assert to_stooq_symbol("0700.HK") == "0700.hk"
    assert to_stooq_symbol("600519.SS") == "600519.cn"
    assert to_stooq_symbol("000001.SZ") == "000001.cn"


def test_a_share_detection() -> None:
    assert looks_like_a_share("600519.SS") is True
    assert looks_like_a_share("000001.SZ") is True
    assert looks_like_a_share("AAPL") is False
    assert to_akshare_a_share_code("600519.SS") == "600519"
