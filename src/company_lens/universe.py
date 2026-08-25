"""One supported-company contract shared by every Company Lens entry point."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from company_lens.profiles import DEMO_PROFILES, display_name


class UnsupportedCompanyError(ValueError):
    """The requested company is outside the declared cached-demo universe."""


@dataclass(frozen=True)
class SupportedCompany:
    ticker: str
    display_name: str
    official_name: str
    cik: int | None


def supported_companies(universe_path: str | Path) -> list[SupportedCompany]:
    """Return every issuer declared by the current local universe artifact."""
    path = Path(universe_path)
    universe = pd.read_csv(path) if path.exists() else pd.DataFrame()
    if universe.empty or not {"ticker", "name"}.issubset(universe.columns):
        return []
    companies = []
    for row in universe.sort_values("ticker").drop_duplicates("ticker", keep="last").to_dict(
        "records"
    ):
        ticker = str(row["ticker"]).upper()
        official_name = str(row["name"])
        cik = (
            int(row["cik"])
            if "cik" in row and pd.notna(row["cik"])
            else None
        )
        companies.append(
            SupportedCompany(
                ticker=ticker,
                display_name=display_name(ticker, official_name),
                official_name=official_name,
                cik=cik,
            )
        )
    return companies


def resolve_supported_company(query: str, universe_path: str | Path) -> SupportedCompany:
    """Resolve a cached ticker or company name, or raise one stable user-facing error."""
    raw = query.strip()
    normalized = _normalize(raw)
    companies = supported_companies(universe_path)
    matches = [
        company
        for company in companies
        if normalized
        in {
            _normalize(company.ticker),
            _normalize(company.display_name),
            _normalize(company.official_name),
        }
    ]
    if len(matches) == 1:
        return matches[0]
    featured = ", ".join(DEMO_PROFILES)
    requested = raw or "Empty ticker"
    raise UnsupportedCompanyError(
        f"{requested!r} is not in the current local company universe "
        f"({len(companies)} companies; featured examples: {featured})."
    )


def _normalize(value: str) -> str:
    return "".join(character for character in value.upper() if character.isalnum())
