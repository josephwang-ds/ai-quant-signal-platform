"""Form 4 insider transactions, parsed from the raw XML EDGAR files them as.

A Form 4 reports that an officer, director or large holder bought or sold their
own company's stock. It is a different kind of evidence from an 8-K: structured
rather than prose, about a *person's behaviour* rather than a corporate event,
and -- unlike a press release -- filed after the fact.

**Two timestamps, and the gap between them is the whole point.** An 8-K has one
knowledge time: EDGAR accepted it, so the market could read it. A Form 4 has
two. `transaction_date` is when the insider actually traded; `acceptance_time`
is when anyone else could have known, and the SEC allows two business days
between them. Anchoring an analysis at the transaction date is hindsight of
exactly the kind this project exists to measure -- the market did not know yet --
and it is the natural, obvious thing to do, because the transaction date is the
more precise field and sits right there in the XML.

So both are carried, `acceptance_time` is the only one anything downstream may
use, and the distance between them becomes a new rung on the leakage ladder.

**The styled document is not the document.** `primaryDocument` in the
submissions feed points at `xslF345X06/form4.xml`, an XSL-rendered HTML view for
humans. Stripping that prefix gives the machine-readable XML the filer actually
submitted. Parsing the rendered view would mean scraping a presentation layer
that changes when the SEC restyles it.

**Most Form 4s report no decision at all.** The transaction code says what
happened, and the majority of rows are compensation mechanics: a grant vesting
(`A`), shares withheld to pay tax on that vest (`F`), an option exercised (`M`).
None of those is a choice about the stock's value; they happen on a schedule set
years earlier. Only `P` and `S` -- open-market purchase and sale -- are a person
deciding to buy or sell today. `OPEN_MARKET_CODES` is that filter, and it is the
single most consequential line in this module: an analysis that skips it is
mostly measuring vesting calendars.

**Rule 10b5-1 is disclosed now, and that is new.** A 10b5-1 plan is adopted in
advance and executed automatically, so trades under one are pre-scheduled by
construction. Since 2023 the filer must flag them, and `plan_10b5_1` carries the
flag. The classic way to find pre-scheduled trades -- Cohen, Malloy and Pomorski's
"routine" insiders, inferred from whether someone trades the same month every
year -- was invented when this flag did not exist. Both are kept, so the inferred
label can be checked against the disclosed one on the filings that have both.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import date

import pandas as pd

# Codes where a person chose to buy or sell on the open market. Everything else
# on a Form 4 is machinery: `A` grant, `F` tax withholding, `M` option exercise,
# `G` gift, `C` conversion. See the module docstring.
OPEN_MARKET_CODES = frozenset({"P", "S"})

# What each code means, for the evidence tables. Not exhaustive -- the rare ones
# fall through to the raw letter rather than being renamed into a guess.
TRANSACTION_CODES = {
    "P": "open-market purchase",
    "S": "open-market sale",
    "A": "grant or award",
    "D": "disposition to the issuer",
    "F": "shares withheld for tax",
    "M": "option exercise or conversion",
    "G": "gift",
    "C": "conversion of a derivative",
    "V": "reported early, voluntarily",
}

COLUMNS = (
    "accession", "issuer_cik", "ticker", "owner_cik", "owner_name",
    "is_director", "is_officer", "is_ten_percent_owner", "officer_title",
    "plan_10b5_1", "security", "derivative", "transaction_date",
    "transaction_code", "shares", "price", "acquired", "shares_after",
)


def raw_document(primary_document: str) -> str:
    """The filer's XML, from the submissions feed's pointer to the styled view.

    `xslF345X06/form4.xml` renders for a human; `form4.xml` is what was filed.
    A path with no prefix is already raw and passes through unchanged.
    """
    return primary_document.rsplit("/", 1)[-1]


def _text(node: ET.Element | None, path: str) -> str:
    """The `<value>` inside a field, or the field's own text, or empty.

    Form 4 wraps most scalars in a `<value>` child so a `<footnoteId>` can sit
    beside them. A few fields are bare. Both shapes appear in the same document.
    """
    if node is None:
        return ""
    found = node.find(path)
    if found is None:
        return ""
    value = found.find("value")
    raw = (value.text if value is not None else found.text) or ""
    return raw.strip()


def _number(node: ET.Element | None, path: str) -> float | None:
    raw = _text(node, path)
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _flag(node: ET.Element | None, path: str) -> bool:
    """A boolean that EDGAR writes as `true`, `1`, or an empty element."""
    raw = _text(node, path).lower()
    return raw in {"true", "1", "y", "yes"}


def _day(raw: str) -> date | None:
    if not raw:
        return None
    parsed = pd.to_datetime(raw, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def parse_form4(xml: str, *, accession: str) -> pd.DataFrame:
    """One row per reported transaction, with its filing's context repeated.

    Per transaction rather than per filing because a single Form 4 can report a
    sale and the tax withholding that funded it, and collapsing those into one
    row would average a decision together with its bookkeeping.

    A document that will not parse returns an empty frame rather than raising:
    one malformed filing among a hundred thousand must not stop an ingest, and
    the caller counts what it lost.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return _empty()

    issuer = root.find("issuer")
    issuer_cik = _text(issuer, "issuerCik")
    ticker = _text(issuer, "issuerTradingSymbol").upper()
    plan = _flag(root, "aff10b5One")

    # A Form 4 may be filed jointly. Each owner's relationship is their own, so
    # a joint filing becomes one set of rows per owner rather than one row
    # attributed to whoever happened to be listed first.
    owners = root.findall("reportingOwner") or [None]
    transactions = (
        [(node, False) for node in root.iter("nonDerivativeTransaction")]
        + [(node, True) for node in root.iter("derivativeTransaction")]
    )
    if not transactions:
        return _empty()

    rows = []
    for owner in owners:
        identity = owner.find("reportingOwnerId") if owner is not None else None
        relationship = (owner.find("reportingOwnerRelationship")
                        if owner is not None else None)
        for node, derivative in transactions:
            amounts = node.find("transactionAmounts")
            rows.append({
                "accession": accession,
                "issuer_cik": int(issuer_cik) if issuer_cik.isdigit() else None,
                "ticker": ticker,
                "owner_cik": _text(identity, "rptOwnerCik"),
                "owner_name": _text(identity, "rptOwnerName"),
                "is_director": _flag(relationship, "isDirector"),
                "is_officer": _flag(relationship, "isOfficer"),
                "is_ten_percent_owner": _flag(relationship, "isTenPercentOwner"),
                "officer_title": _text(relationship, "officerTitle"),
                "plan_10b5_1": plan,
                "security": _text(node, "securityTitle"),
                "derivative": derivative,
                # The insider's own date. Never a knowledge time -- see the module
                # docstring -- and carried so the gap can be measured.
                "transaction_date": _day(_text(node, "transactionDate")),
                "transaction_code": _text(node, "transactionCoding/transactionCode"),
                "shares": _number(amounts, "transactionShares"),
                "price": _number(amounts, "transactionPricePerShare"),
                "acquired": _text(amounts, "transactionAcquiredDisposedCode"),
                "shares_after": _number(node.find("postTransactionAmounts"),
                                        "sharesOwnedFollowingTransaction"),
            })
    return pd.DataFrame(rows, columns=list(COLUMNS))


def is_readable(xml: str) -> bool:
    """Whether the document is well-formed XML at all.

    Exists to keep two very different things apart in the ingest's counters. A
    Form 4 that produces no rows is usually not broken: it reported a *holding*
    rather than a transaction, which happens when beneficial ownership changes
    form or a position is restated, and about one filing in two hundred does it.
    A Form 4 that will not parse is a data-quality alarm.

    Counting them together makes the alarm meaningless, and sends whoever reads
    the log looking for a parser bug that is not there.
    """
    try:
        ET.fromstring(xml)
    except ET.ParseError:
        return False
    return True


def _empty() -> pd.DataFrame:
    return pd.DataFrame({name: pd.Series(dtype="object") for name in COLUMNS})


def open_market(transactions: pd.DataFrame) -> pd.DataFrame:
    """Only the rows where somebody decided to buy or sell.

    Applied as its own step, and named, because dropping it silently is how an
    insider-trading study ends up measuring when option grants vest.
    """
    if transactions.empty:
        return transactions
    return transactions[transactions["transaction_code"].isin(OPEN_MARKET_CODES)]


def signed_value(transactions: pd.DataFrame) -> pd.Series:
    """Dollar value of each trade, positive for a purchase and negative for a sale.

    Signed by the acquired/disposed code rather than by the transaction code, so
    a row whose code and direction disagree -- which does happen -- follows the
    field that says what moved.
    """
    value = transactions["shares"].astype(float) * transactions["price"].astype(float)
    return value.where(transactions["acquired"].eq("A"), -value)
