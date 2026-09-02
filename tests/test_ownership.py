"""Form 4 parsing, and the two mistakes that would quietly ruin the study.

The first is anchoring on the transaction date. It is the more precise field, it
sits in the XML next to everything else, and using it means analysing a trade
the market did not know about yet -- the same bug this project measures on 8-Ks,
in a new place.

The second is forgetting that most rows on a Form 4 are not decisions. A vesting
grant, the shares withheld to pay tax on it, an option exercise: all reported on
the same form as an open-market purchase, all far more numerous, and none of
them a person deciding anything about the price.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from filing_triage.ingest.ownership import (
    OPEN_MARKET_CODES,
    open_market,
    parse_form4,
    raw_document,
    signed_value,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sec" / "form4_plan_sale.xml"


def _document(**parts) -> str:
    """A minimal Form 4 with one non-derivative transaction."""
    defaults = {
        "period": "2024-03-01", "plan": "false", "owner_cik": "0000000001",
        "owner_name": "Doe Jane", "relationship": "<isOfficer>true</isOfficer>",
        "date": "2024-03-01", "code": "P", "shares": "100", "price": "10.5",
        "acquired": "A", "after": "1100",
    }
    p = {**defaults, **parts}
    return f"""<?xml version="1.0"?>
<ownershipDocument>
  <documentType>4</documentType>
  <periodOfReport>{p['period']}</periodOfReport>
  <issuer><issuerCik>0000320193</issuerCik>
    <issuerTradingSymbol>aapl</issuerTradingSymbol></issuer>
  <reportingOwner>
    <reportingOwnerId><rptOwnerCik>{p['owner_cik']}</rptOwnerCik>
      <rptOwnerName>{p['owner_name']}</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship>{p['relationship']}</reportingOwnerRelationship>
  </reportingOwner>
  <aff10b5One>{p['plan']}</aff10b5One>
  <nonDerivativeTable><nonDerivativeTransaction>
    <securityTitle><value>Common Stock</value></securityTitle>
    <transactionDate><value>{p['date']}</value></transactionDate>
    <transactionCoding><transactionCode>{p['code']}</transactionCode></transactionCoding>
    <transactionAmounts>
      <transactionShares><value>{p['shares']}</value></transactionShares>
      <transactionPricePerShare><value>{p['price']}</value></transactionPricePerShare>
      <transactionAcquiredDisposedCode><value>{p['acquired']}</value>
      </transactionAcquiredDisposedCode>
    </transactionAmounts>
    <postTransactionAmounts><sharesOwnedFollowingTransaction><value>{p['after']}</value>
    </sharesOwnedFollowingTransaction></postTransactionAmounts>
  </nonDerivativeTransaction></nonDerivativeTable>
</ownershipDocument>"""


class TestTheFilerSXmlIsWhatGetsParsed:
    def test_the_styled_prefix_is_stripped(self):
        """`primaryDocument` points at an XSL rendering for humans. Scraping it
        would mean depending on a presentation layer the SEC restyles."""
        assert raw_document("xslF345X06/form4.xml") == "form4.xml"
        assert raw_document("xslF345X03/doc4.xml") == "doc4.xml"

    def test_an_already_raw_path_passes_through(self):
        assert raw_document("form4.xml") == "form4.xml"

    def test_a_real_filing_parses(self):
        frame = parse_form4(FIXTURE.read_text(), accession="0001140361-26-034741")
        assert len(frame) == 1
        row = frame.iloc[0]
        assert row["ticker"] == "AAPL"
        assert row["owner_name"] == "Newstead Jennifer"
        assert row["transaction_code"] == "S"
        assert row["shares"] == pytest.approx(1439)
        assert row["price"] == pytest.approx(310.95)
        assert bool(row["is_officer"])

    def test_the_disclosed_plan_flag_is_read(self):
        """Since 2023 a filer must say whether the trade ran under a pre-adopted
        10b5-1 plan. That is the difference between a decision and a calendar."""
        assert parse_form4(FIXTURE.read_text(), accession="a").iloc[0]["plan_10b5_1"]
        assert not parse_form4(_document(plan="false"), accession="a").iloc[0]["plan_10b5_1"]


class TestTheTransactionDateIsNotAKnowledgeTime:
    def test_it_is_kept_separate_and_never_renamed(self):
        """Carried under its own name so nothing downstream can mistake it for
        the time the market learned of the trade."""
        frame = parse_form4(_document(date="2024-03-01"), accession="a")
        assert frame.iloc[0]["transaction_date"] == pd.Timestamp("2024-03-01").date()
        assert "acceptance_time" not in frame.columns

    def test_the_per_transaction_date_wins_over_the_filing_period(self):
        """A filing reporting several days of trades has one `periodOfReport`
        and a date per transaction. The transaction's own date is the finer
        fact, and the one the gap must be measured from."""
        frame = parse_form4(_document(period="2024-03-05", date="2024-03-01"),
                            accession="a")
        assert frame.iloc[0]["transaction_date"] == pd.Timestamp("2024-03-01").date()


class TestMostRowsAreNotDecisions:
    @pytest.mark.parametrize("code", ["A", "F", "M", "G", "C", "D"])
    def test_compensation_machinery_is_filtered_out(self, code):
        """A vest, the tax withheld on it, an exercise, a gift. Reported on the
        same form and far more numerous than actual trades."""
        assert open_market(parse_form4(_document(code=code), accession="a")).empty

    @pytest.mark.parametrize("code", sorted(OPEN_MARKET_CODES))
    def test_open_market_trades_are_kept(self, code):
        assert len(open_market(parse_form4(_document(code=code), accession="a"))) == 1

    def test_an_empty_frame_survives_the_filter(self):
        assert open_market(parse_form4("<bad", accession="a")).empty


class TestOneRowPerTransaction:
    def test_a_sale_and_its_tax_withholding_stay_separate(self):
        """Collapsing them would average a decision together with its
        bookkeeping."""
        xml = _document().replace(
            "</nonDerivativeTable>",
            """<nonDerivativeTransaction>
    <transactionDate><value>2024-03-01</value></transactionDate>
    <transactionCoding><transactionCode>F</transactionCode></transactionCoding>
    <transactionAmounts><transactionShares><value>40</value></transactionShares>
    </transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>""")
        frame = parse_form4(xml, accession="a")
        assert len(frame) == 2
        assert set(frame["transaction_code"]) == {"P", "F"}
        assert len(open_market(frame)) == 1

    def test_a_derivative_transaction_is_flagged_not_dropped(self):
        xml = _document().replace(
            "</nonDerivativeTable>",
            "</nonDerivativeTable><derivativeTable><derivativeTransaction>"
            "<transactionDate><value>2024-03-01</value></transactionDate>"
            "<transactionCoding><transactionCode>M</transactionCode></transactionCoding>"
            "</derivativeTransaction></derivativeTable>")
        frame = parse_form4(xml, accession="a")
        assert list(frame["derivative"]) == [False, True]

    def test_a_joint_filing_gives_each_owner_their_own_rows(self):
        """Relationships differ between co-filers, so attributing the trade to
        whoever was listed first would mislabel the other."""
        xml = _document().replace(
            "</reportingOwner>",
            """</reportingOwner><reportingOwner>
    <reportingOwnerId><rptOwnerCik>0000000002</rptOwnerCik>
      <rptOwnerName>Roe Richard</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><isDirector>true</isDirector></reportingOwnerRelationship>
  </reportingOwner>""")
        frame = parse_form4(xml, accession="a")
        assert len(frame) == 2
        assert set(frame["owner_name"]) == {"Doe Jane", "Roe Richard"}
        assert list(frame["is_director"]) == [False, True]


class TestBadInputDoesNotStopAnIngest:
    def test_malformed_xml_returns_an_empty_frame(self):
        """One broken filing among a hundred thousand must not abort the pull."""
        frame = parse_form4("<ownershipDocument><unclosed>", accession="a")
        assert frame.empty
        assert list(frame.columns)

    def test_a_filing_with_no_transactions_is_empty(self):
        xml = _document()[:_document().index("<nonDerivativeTable>")] + "</ownershipDocument>"
        assert parse_form4(xml, accession="a").empty

    def test_a_missing_price_is_none_rather_than_zero(self):
        """Zero would read as a gift at no cost rather than as an unreported
        price, and would drag any average value toward nothing."""
        xml = _document().replace("<value>10.5</value>", "<value></value>")
        assert parse_form4(xml, accession="a").iloc[0]["price"] is None


class TestValueFollowsWhatMoved:
    def test_a_purchase_is_positive_and_a_sale_negative(self):
        buy = parse_form4(_document(code="P", acquired="A"), accession="a")
        sell = parse_form4(_document(code="S", acquired="D"), accession="a")
        assert signed_value(buy).iloc[0] == pytest.approx(1050.0)
        assert signed_value(sell).iloc[0] == pytest.approx(-1050.0)

    def test_the_sign_follows_the_acquired_field_not_the_code(self):
        """The two disagree occasionally; the field that says what moved wins."""
        odd = parse_form4(_document(code="P", acquired="D"), accession="a")
        assert signed_value(odd).iloc[0] < 0
