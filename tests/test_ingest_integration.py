"""The real-data path, end to end, with the network replaced.

`triage ingest` is the code that runs against the live SEC, and it is the code
that cannot be exercised in CI. So the transport is swapped for fakes that return
EDGAR-shaped payloads, and everything downstream of them -- the per-issuer loop,
the frame assembly, the parquet round trip, and the pipeline reading what was
written -- runs for real.

This is the seam that a fixture test of `parse_submissions` alone does not cover:
parsing one issuer correctly says nothing about what happens when five hundred of
them are concatenated and handed to the pipeline.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from filing_triage import cli, pipeline
from filing_triage.config import PipelineConfig
from filing_triage.pit import CALENDAR

ISSUERS = [("AAA", 1001), ("BBB", 1002), ("CCC", 1003)]
START, END = date(2022, 1, 3), date(2024, 6, 28)


class FakeEdgarClient:
    """Same surface as EdgarClient, no sockets."""

    calls: list[str] = []

    def __init__(self, *_, **__):
        self.user_agent = "Test test@example.com"

    def check_access(self) -> str:
        return "SEC reachable (fake)"

    def submissions(self, cik: int) -> dict:
        FakeEdgarClient.calls.append(f"submissions:{cik}")
        if cik == 1003:
            raise RuntimeError("SEC returned 404 for CIK0000001003")   # one bad issuer
        sessions = CALENDAR.sessions_between(START, END)[::19]
        return {"filings": {"recent": {
            "accessionNumber": [f"{cik:010d}-24-{i:06d}" for i in range(len(sessions))],
            "filingDate": [d.isoformat() for d in sessions],
            "reportDate": [(d - timedelta(days=20)).isoformat() for d in sessions],
            "acceptanceDateTime": [f"{d.isoformat()}T18:0{i % 6}:00.000Z"
                                   for i, d in enumerate(sessions)],
            "form": ["8-K"] * len(sessions),
            "items": ["2.02,9.01" if i % 3 else "5.02" for i in range(len(sessions))],
            "primaryDocument": ["a8k.htm"] * len(sessions),
        }}}

    def document_text(self, cik: int, accession: str, document: str) -> str:
        return (f"the registrant furnished results for the period. "
                f"reference {accession[-3:]} operating margin commentary")


def fake_fetch_daily(ticker: str, **_) -> pd.DataFrame:
    sessions = CALENDAR.sessions_between(START, END)
    n = len(sessions)
    base = 100.0 + (hash(ticker) % 50)
    close = [base * (1 + 0.0004 * i) for i in range(n)]
    return pd.DataFrame({
        "ticker": ticker, "date": sessions,
        "open": close, "high": [c * 1.01 for c in close],
        "low": [c * 0.99 for c in close], "close": close,
        "volume": [1_000_000.0 + 5000 * (i % 40) for i in range(n)],
    })


@pytest.fixture
def universe_file(tmp_path):
    path = tmp_path / "membership.csv"
    pd.DataFrame([
        {"ticker": t, "cik": c, "name": f"{t} Corp",
         "start_date": "2020-01-01", "end_date": ""}
        for t, c in ISSUERS
    ]).to_csv(path, index=False)
    return path


@pytest.fixture
def ingested(tmp_path, universe_file, monkeypatch):
    monkeypatch.setattr("filing_triage.ingest.edgar.EdgarClient", FakeEdgarClient)
    monkeypatch.setattr("filing_triage.ingest.prices.fetch_daily", fake_fetch_daily)
    monkeypatch.setattr(cli, "BUILD", tmp_path / "build")
    FakeEdgarClient.calls = []
    code = cli.main(["ingest", "--universe", str(universe_file), "--since", "2022-01-01"])
    return code, tmp_path / "build"


class TestIngest:
    def test_completes_despite_a_failing_issuer(self, ingested):
        code, build = ingested
        assert code == 0
        provenance = pd.read_json(build / "provenance.json", typ="series")
        assert provenance["source"] == "edgar"
        assert provenance["issuers"] == 2                # CCC failed
        assert provenance["failed_issuers"] == ["CCC"]

    def test_writes_the_three_frames(self, ingested):
        _, build = ingested
        for name in ("events.parquet", "prices.parquet", "membership.csv"):
            assert (build / name).exists(), name

    def test_events_carry_everything_the_pipeline_needs(self, ingested):
        _, build = ingested
        events = pd.read_parquet(build / "events.parquet")
        for column in ("event_id", "ticker", "cik", "items", "acceptance_time",
                       "filing_date", "period_of_report", "text", "accession"):
            assert column in events.columns, column
        assert events["event_id"].is_unique
        assert str(events["acceptance_time"].dt.tz) == "America/New_York"

    def test_the_benchmark_is_fetched_even_though_it_is_not_a_member(self, ingested):
        """The market model needs SPY. It is not in the index file, so nothing
        in the per-issuer loop would ever ask for it."""
        _, build = ingested
        prices = pd.read_parquet(build / "prices.parquet")
        assert "SPY" in set(prices["ticker"])

    def test_prices_have_no_duplicate_ticker_dates(self, ingested):
        _, build = ingested
        prices = pd.read_parquet(build / "prices.parquet")
        assert not prices.duplicated(["ticker", "date"]).any()


class TestPipelineConsumesIngestedFrames:
    def test_pipeline_runs_on_what_ingest_wrote(self, ingested):
        """The actual seam. Parquet round-trips dtypes, and a tz-aware column that
        survives the write is the difference between this working and the clock
        rejecting every row."""
        _, build = ingested
        events = pd.read_parquet(build / "events.parquet")
        prices = pd.read_parquet(build / "prices.parquet")
        membership = pd.read_csv(build / "membership.csv")

        result = pipeline.run(events, prices, membership, PipelineConfig(),
                              compute_importance=False)
        assert result.audit.passed, result.audit.summary()
        assert result.integrity["impossible_entries"] == 0
