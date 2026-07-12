"""跨数据源的标的代码规范化。"""

from __future__ import annotations


def normalize_symbol(symbol: str) -> str:
    """统一为大写、去空格。"""
    return symbol.upper().strip()


def looks_like_a_share(symbol: str) -> bool:
    """是否像 A 股代码（Yahoo 风格 .SS/.SZ，或 6 位数字）。"""
    s = normalize_symbol(symbol)
    if s.endswith(".SS") or s.endswith(".SZ"):
        return True
    bare = s.split(".")[0]
    return bare.isdigit() and len(bare) == 6


def to_stooq_symbol(symbol: str) -> str:
    """
    将常用 Yahoo 代码映射为 Stooq 代码。

    例：AAPL → aapl.us，0700.HK → 0700.hk，600519.SS → 600519.cn
    """
    s = normalize_symbol(symbol).replace("_", "-")

    if s.endswith(".US"):
        return f"{s[:-3].lower()}.us"
    if s.endswith(".HK"):
        return f"{s[:-3].lower()}.hk"
    if s.endswith(".SS") or s.endswith(".SZ"):
        return f"{s.split('.')[0].lower()}.cn"
    if s.startswith("^"):
        index_map = {
            "^GSPC": "^spx",
            "^IXIC": "^ndq",
            "^DJI": "^dji",
            "^HSI": "^hsi",
            "^N225": "^nkx",
            "^FTSE": "^ukx",
        }
        return index_map.get(s, s.lower())
    if s.endswith("-USD"):
        base = s.replace("-USD", "").lower()
        return f"{base}.v"
    if s.endswith("=X"):
        # EURUSD=X → eurusd
        return s.replace("=X", "").lower()
    if s.endswith("=F"):
        # 期货在 Stooq 覆盖不稳定，仍尝试小写
        return s.lower()

    # 裸美股代码默认 .us
    if "." not in s and s.isalpha():
        return f"{s.lower()}.us"

    return s.lower()


def to_akshare_a_share_code(symbol: str) -> str:
    """Yahoo/通用 A 股代码 → AKShare 6 位代码。"""
    s = normalize_symbol(symbol)
    return s.split(".")[0]


def to_akshare_us_symbol(symbol: str) -> str:
    """Yahoo 美股代码 → AKShare US 代码。"""
    s = normalize_symbol(symbol)
    if s.endswith(".US"):
        return s[:-3]
    return s
