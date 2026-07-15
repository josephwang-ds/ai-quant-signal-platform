"""
Canonical symbol classification and normalization for market-data routing.

Routing is deterministic from explicit symbol structure — no company-name guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from app.research_execution.market_data_port import (
    MarketDataValidationError,
    UnsupportedSymbolError,
)

AssetClass = Literal[
    "us_equity",
    "hk_equity",
    "cn_equity",
    "etf",
    "index",
    "crypto",
    "unknown",
]

PreferredProvider = Literal["yahoo", "akshare"]

# Common ETF tickers routed to Yahoo with asset_class=etf.
KNOWN_ETFS = frozenset(
    {
        "SPY",
        "QQQ",
        "IWM",
        "DIA",
        "VTI",
        "VOO",
        "IVV",
        "EFA",
        "EEM",
        "AGG",
        "GLD",
        "XLF",
        "XLK",
        "XLE",
        "ARKK",
        "VEA",
        "VWO",
        "BND",
        "TLT",
        "HYG",
        "LQD",
        "SCHD",
        "VNQ",
    }
)

CN_EXCHANGE_SUFFIXES = frozenset({"SZ", "SH", "SS", "BJ"})

# Yahoo-style Shanghai suffix (.SS) is accepted; canonical symbol preserves input.
_SUFFIX_TO_EXCHANGE: dict[str, str] = {
    "SZ": "SZ",
    "SH": "SH",
    "SS": "SH",
    "BJ": "BJ",
}

_HK_PATTERN = re.compile(r"^\d{1,5}\.HK$")
_CN_PATTERN = re.compile(r"^(\d{6})\.(SZ|SH|SS|BJ)$")
_CRYPTO_PATTERN = re.compile(r"^[A-Z0-9]+-USD$")
_US_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.\-]{0,14}$")

@dataclass(frozen=True)
class SymbolDescriptor:
    """Normalized symbol metadata used for provider routing."""

    input_symbol: str
    canonical_symbol: str
    provider_symbol: str
    exchange: str | None
    asset_class: AssetClass
    currency: str
    preferred_provider: PreferredProvider


def classify_symbol(input_symbol: str) -> SymbolDescriptor:
    """
    Classify a user symbol into asset class and preferred provider.

    Raises UnsupportedSymbolError for malformed or ambiguous symbols.
    """
    raw = (input_symbol or "").strip()
    if not raw:
        raise UnsupportedSymbolError("Symbol must not be empty.")

    upper = raw.upper()

    cn_match = _CN_PATTERN.match(upper)
    if cn_match:
        code, suffix = cn_match.group(1), cn_match.group(2)
        exchange = _SUFFIX_TO_EXCHANGE[suffix]
        return SymbolDescriptor(
            input_symbol=raw,
            canonical_symbol=upper,
            provider_symbol=code,
            exchange=exchange,
            asset_class="cn_equity",
            currency="CNY",
            preferred_provider="akshare",
        )

    if _HK_PATTERN.match(upper):
        return SymbolDescriptor(
            input_symbol=raw,
            canonical_symbol=upper,
            provider_symbol=upper,
            exchange="HK",
            asset_class="hk_equity",
            currency="HKD",
            preferred_provider="yahoo",
        )

    if _CRYPTO_PATTERN.match(upper):
        return SymbolDescriptor(
            input_symbol=raw,
            canonical_symbol=upper,
            provider_symbol=upper,
            exchange=None,
            asset_class="crypto",
            currency="USD",
            preferred_provider="yahoo",
        )

    if upper.startswith("^"):
        if not re.match(r"^\^[A-Z0-9.\-=]+$", upper):
            raise UnsupportedSymbolError(f"Malformed index symbol '{raw}'.")
        return SymbolDescriptor(
            input_symbol=raw,
            canonical_symbol=upper,
            provider_symbol=upper,
            exchange=None,
            asset_class="index",
            currency="USD",
            preferred_provider="yahoo",
        )

    if upper.isdigit() and len(upper) == 6:
        raise UnsupportedSymbolError(
            f"Ambiguous mainland symbol '{raw}'. "
            "Provide an explicit exchange suffix such as .SZ or .SH."
        )

    ticker = upper.removesuffix(".US") if upper.endswith(".US") else upper
    if not _US_TICKER_PATTERN.match(ticker):
        raise UnsupportedSymbolError(f"Unsupported symbol format '{raw}'.")

    asset_class: AssetClass = "etf" if ticker in KNOWN_ETFS else "us_equity"
    currency = "USD"
    return SymbolDescriptor(
        input_symbol=raw,
        canonical_symbol=upper,
        provider_symbol=upper,
        exchange=None,
        asset_class=asset_class,
        currency=currency,
        preferred_provider="yahoo",
    )


ALLOWED_PROVIDER_OVERRIDES = frozenset({"yahoo", "akshare"})


def resolve_provider(
    descriptor: SymbolDescriptor,
    override: str | None,
) -> PreferredProvider:
    """
    Validate an optional provider override against descriptor capabilities.

    Raises UnsupportedSymbolError when override is invalid or incompatible.
    """
    if not override:
        return descriptor.preferred_provider

    normalized = override.strip().lower()
    if normalized not in ALLOWED_PROVIDER_OVERRIDES:
        raise UnsupportedSymbolError(
            f"Unsupported provider override '{override}'. "
            f"Allowed: {sorted(ALLOWED_PROVIDER_OVERRIDES)}."
        )

    if normalized == "akshare" and descriptor.asset_class != "cn_equity":
        raise UnsupportedSymbolError(
            f"Provider 'akshare' does not support asset_class "
            f"'{descriptor.asset_class}' for '{descriptor.canonical_symbol}'."
        )
    if normalized == "yahoo" and descriptor.asset_class == "cn_equity":
        # Yahoo may expose some A-shares via alternate suffixes, but research
        # routing keeps mainland equities on AkShare unless explicitly overridden
        # for cn_equity is disallowed — akshare is required for cn_equity.
        raise UnsupportedSymbolError(
            f"Provider 'yahoo' is not supported for mainland equity "
            f"'{descriptor.canonical_symbol}'. Use AkShare routing."
        )

    return normalized  # type: ignore[return-value]
