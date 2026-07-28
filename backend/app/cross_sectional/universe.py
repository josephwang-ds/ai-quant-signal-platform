"""Configurable demonstration universes for cross-sectional datasets.

Membership is an explicit static list. This is not historical index
membership and does not claim to solve survivorship bias.

Domain tickers use canonical forms (e.g. ``BRK-B``). Provider-specific
formatting is applied only inside MarketDataPort adapters.
"""

from __future__ import annotations

from app.cross_sectional.constants import (
    UNIVERSE_ID_LIQUID_31,
    UNIVERSE_ID_LIQUID_50,
)

# Explicit demo membership (31 liquid US equities). Static snapshot only.
# Authoritative configuration — do not duplicate this full list elsewhere.
US_LIQUID_31_V1: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "BRK-B",
    "JPM",
    "V",
    "MA",
    "UNH",
    "XOM",
    "JNJ",
    "PG",
    "COST",
    "HD",
    "ABBV",
    "KO",
    "PEP",
    "MRK",
    "AVGO",
    "CRM",
    "AMD",
    "NFLX",
    "WMT",
    "BAC",
    "ORCL",
    "CVX",
    "ADBE",
    "MU",
)

# Broader static demo universe: all of us_liquid_31_v1 plus 19 names.
# Built from the authoritative 31-tuple — do not re-list the 31 tickers here.
_US_LIQUID_50_EXTRA: tuple[str, ...] = (
    "LLY",
    "QCOM",
    "TXN",
    "AMAT",
    "LRCX",
    "GS",
    "MS",
    "MCD",
    "COP",
    "CAT",
    "GE",
    "RTX",
    "HON",
    "DIS",
    "LIN",
    "NEE",
    "PLTR",
    "TMO",
    "LOW",
)

US_LIQUID_50_V1: tuple[str, ...] = US_LIQUID_31_V1 + _US_LIQUID_50_EXTRA

UNIVERSE_PRESETS: dict[str, tuple[str, ...]] = {
    UNIVERSE_ID_LIQUID_31: US_LIQUID_31_V1,
    UNIVERSE_ID_LIQUID_50: US_LIQUID_50_V1,
}

_STATIC_DISCLOSURE = (
    "Static manually configured demonstration universe — not a point-in-time "
    "S&P 500 or Nasdaq-100 (or any index) membership series.",
    "Historical membership and survivorship bias are not solved; delisted "
    "names are not reconstructed.",
)

UNIVERSE_DISCLOSURES: dict[str, tuple[str, ...]] = {
    UNIVERSE_ID_LIQUID_31: _STATIC_DISCLOSURE,
    UNIVERSE_ID_LIQUID_50: _STATIC_DISCLOSURE
    + (
        "Broader research universe (50 names) extending us_liquid_31_v1; "
        "still a curated static list, not historical index reconstitutions.",
    ),
}


def resolve_universe(
    universe_id: str,
    *,
    symbols_override: list[str] | tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Return an explicit symbol tuple for the requested universe.

    When ``symbols_override`` is provided, it replaces the preset membership
    but ``universe_id`` is still recorded by the caller for provenance.
    Duplicate override tickers are dropped deterministically (first wins).
    """
    if symbols_override is not None:
        cleaned: list[str] = []
        seen: set[str] = set()
        for raw in symbols_override:
            symbol = str(raw or "").strip().upper()
            if not symbol:
                continue
            if symbol in seen:
                continue
            seen.add(symbol)
            cleaned.append(symbol)
        if not cleaned:
            raise ValueError("symbols override must contain at least one ticker.")
        return tuple(cleaned)

    key = str(universe_id or "").strip().lower()
    if key not in UNIVERSE_PRESETS:
        raise ValueError(
            f"Unknown universe '{universe_id}'. Supported: {sorted(UNIVERSE_PRESETS)}"
        )
    return UNIVERSE_PRESETS[key]


def universe_disclosures(universe_id: str) -> tuple[str, ...]:
    key = str(universe_id or "").strip().lower()
    return UNIVERSE_DISCLOSURES.get(key, ())


def configured_universe_version(universe_id: str) -> str:
    """Universe version equals the configured preset id (or override provenance id)."""
    return str(universe_id or "").strip().lower()
