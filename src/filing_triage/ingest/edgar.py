"""SEC EDGAR client.

Pulls the submissions index for each issuer and the primary document text for
each 8-K. Everything is cached to disk keyed by accession number, so a rerun
costs nothing and the expensive part happens once.

Two things this client is careful about:

1. `acceptanceDateTime` is Eastern Time, despite the `Z`.
   EDGAR serves values like "2024-10-31T18:03:31.000Z". The suffix says UTC; the
   clock is the SEC's, which runs on America/New_York. Parsing it as UTC shifts
   every filing four or five hours earlier, which silently converts the large
   after-hours population into "arrived during the session" -- and hands the
   model a same-day entry it never had. `ACCEPTANCE_TZ` makes the assumption
   explicit and overridable rather than buried in a parse call.

2. The SEC asks for a descriptive User-Agent and at most 10 requests/second.
   Both are enforced here. Set EDGAR_USER_AGENT to your own name and email.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"

# See docstring. Override only if you have verified otherwise against live data.
ACCEPTANCE_TZ = ZoneInfo(os.environ.get("EDGAR_ACCEPTANCE_TZ", "America/New_York"))

MAX_REQUESTS_PER_SECOND = 8      # SEC's ceiling is 10; leave headroom.


@dataclass
class EdgarClient:
    user_agent: str = os.environ.get("EDGAR_USER_AGENT", "")
    cache_dir: Path = Path("data/cache/edgar")
    timeout: int = 30

    def __post_init__(self) -> None:
        if not self.user_agent:
            raise ValueError(
                "SEC requires an identifying User-Agent. Set EDGAR_USER_AGENT, e.g.\n"
                '  export EDGAR_USER_AGENT="Jane Doe jane@example.com"'
            )
        self.cache_dir = Path(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
        })
        self._last_request = 0.0

    # -- transport --------------------------------------------------------- #
    def _get(self, url: str) -> bytes:
        wait = (1.0 / MAX_REQUESTS_PER_SECOND) - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        response = self._session.get(url, timeout=self.timeout)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return response.content

    def _cached(self, key: str, url: str) -> bytes:
        path = self.cache_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            return path.read_bytes()
        payload = self._get(url)
        path.write_bytes(payload)
        return payload

    # -- endpoints --------------------------------------------------------- #
    def ticker_map(self) -> pd.DataFrame:
        """ticker -> CIK, straight from the SEC's own mapping."""
        raw = json.loads(self._cached("company_tickers.json", SEC_TICKERS_URL))
        return pd.DataFrame([
            {"ticker": v["ticker"].upper(), "cik": int(v["cik_str"]), "name": v["title"]}
            for v in raw.values()
        ])

    def submissions(self, cik: int) -> dict:
        """Full submission history, following the SEC's pagination shards."""
        head = json.loads(self._cached(
            f"submissions/CIK{cik:010d}.json", SEC_SUBMISSIONS_URL.format(cik=cik)))
        shards = []
        for extra in head.get("filings", {}).get("files", []):
            url = f"https://data.sec.gov/submissions/{extra['name']}"
            shards.append(json.loads(self._cached(f"submissions/{extra['name']}", url)))
        head["_shards"] = shards
        return head

    def document_text(self, cik: int, accession: str, document: str) -> str:
        """Primary document, tags stripped. Enough for a bag-of-words novelty score."""
        key = f"docs/{accession.replace('-', '')}.txt"
        path = self.cache_dir / key
        if path.exists():
            return path.read_text(errors="ignore")
        raw = self._get(SEC_ARCHIVE_URL.format(
            cik=cik, accession=accession.replace("-", ""), document=document))
        text = strip_markup(raw.decode("utf-8", errors="ignore"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return text


def strip_markup(html: str) -> str:
    """Crude but adequate: EDGAR primary documents are HTML or plain text."""
    import re
    text = re.sub(r"(?is)<(script|style|table)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&#160;", " "))
    return re.sub(r"\s+", " ", text).strip()


def parse_submissions(payload: dict, cik: int, forms: tuple[str, ...] = ("8-K",)) -> pd.DataFrame:
    """Flatten a submissions payload into one row per filing.

    Keeps all three timestamps side by side on purpose. `acceptance_time` is the
    one anything downstream is allowed to use; the other two are carried so the
    leakage experiment can show what using them instead costs.
    """
    blocks = [payload["filings"]["recent"]] + [
        s["filings"]["recent"] if "filings" in s else s
        for s in payload.get("_shards", [])
    ]
    frames = [pd.DataFrame(b) for b in blocks if b]
    if not frames:
        return _empty_filings()
    df = pd.concat(frames, ignore_index=True)
    df = df[df["form"].isin(forms)].copy()
    if df.empty:
        return _empty_filings()

    out = pd.DataFrame({
        "cik": cik,
        "accession": df["accessionNumber"],
        "form": df["form"],
        "items": df.get("items", pd.Series("", index=df.index)).fillna(""),
        "primary_document": df["primaryDocument"],
        # THE knowledge time. Localised, never converted from UTC. See module docstring.
        "acceptance_time": pd.to_datetime(
            df["acceptanceDateTime"].str.replace("Z", "", regex=False),
            errors="coerce",
        ).dt.tz_localize(ACCEPTANCE_TZ, ambiguous=True, nonexistent="shift_forward"),
        # Carried for the leakage experiment only. Not inputs.
        "filing_date": pd.to_datetime(df["filingDate"], errors="coerce").dt.date,
        "period_of_report": pd.to_datetime(df.get("reportDate"), errors="coerce").dt.date,
    })
    return out.dropna(subset=["acceptance_time"]).reset_index(drop=True)


def _empty_filings() -> pd.DataFrame:
    return pd.DataFrame({
        "cik": pd.Series(dtype="int64"),
        "accession": pd.Series(dtype="object"),
        "form": pd.Series(dtype="object"),
        "items": pd.Series(dtype="object"),
        "primary_document": pd.Series(dtype="object"),
        "acceptance_time": pd.Series(dtype="datetime64[ns, America/New_York]"),
        "filing_date": pd.Series(dtype="object"),
        "period_of_report": pd.Series(dtype="object"),
    })


# 8-K item taxonomy. The item code is the single most informative structured
# field on a filing: it is assigned by the registrant, available the instant the
# filing lands, and tells you what kind of news this is before reading a word.
ITEM_LABELS = {
    "1.01": "Material agreement entered",
    "1.02": "Material agreement terminated",
    "1.03": "Bankruptcy or receivership",
    "2.01": "Asset acquisition or disposition",
    "2.02": "Results of operations (earnings)",
    "2.03": "Direct financial obligation created",
    "2.04": "Triggering event accelerating an obligation",
    "2.05": "Costs from exit or disposal",
    "2.06": "Material impairment",
    "3.01": "Delisting or listing-rule failure",
    "3.02": "Unregistered equity sale",
    "3.03": "Material modification to security holder rights",
    "4.01": "Auditor changed",
    "4.02": "Prior financial statements not reliable",
    "5.01": "Change in control",
    "5.02": "Director or principal officer change",
    "5.03": "Fiscal year or bylaw amendment",
    "5.07": "Shareholder vote results",
    "7.01": "Regulation FD disclosure",
    "8.01": "Other events",
    "9.01": "Financial statements and exhibits",
}
