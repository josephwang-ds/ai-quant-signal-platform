"""EDGAR parsing, against fixtures shaped like the real payloads.

The client cannot be exercised against the live SEC from CI, so the parsing layer
is pinned to fixtures that reproduce the shapes EDGAR actually serves -- including
the awkward ones. Every case here is something the real feed does:

  * the submissions index is paginated once an issuer has enough history, and the
    older shards are *flat* -- they are not wrapped in {"filings": {"recent": ...}}
  * `items` is empty for most forms and comma-separated for 8-Ks
  * `reportDate` is an empty string, not null, when a form has no period
  * `acceptanceDateTime` carries a `Z` that does not mean UTC
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import pandas as pd
import pytest

from filing_triage.ingest.edgar import (
    ACCEPTANCE_TZ,
    ITEM_LABELS,
    EdgarClient,
    parse_submissions,
    strip_markup,
)


def _recent(**overrides) -> dict:
    block = {
        "accessionNumber": ["0000320193-24-000100", "0000320193-24-000101",
                            "0000320193-24-000102"],
        "filingDate": ["2024-10-31", "2024-08-01", "2024-05-02"],
        "reportDate": ["2024-09-28", "", "2024-03-30"],
        "acceptanceDateTime": ["2024-10-31T18:03:31.000Z",
                               "2024-08-01T09:00:00.000Z",
                               "2024-05-02T16:30:12.000Z"],
        "form": ["8-K", "10-Q", "8-K"],
        "items": ["2.02,9.01", "", "5.02"],
        "primaryDocument": ["a8k.htm", "aapl-q3.htm", "b8k.htm"],
    }
    block.update(overrides)
    return block


def _payload(recent: dict | None = None, shards: list | None = None) -> dict:
    return {"cik": "320193", "name": "Apple Inc.",
            "filings": {"recent": recent or _recent()},
            "_shards": shards or []}


class TestParsing:
    def test_keeps_only_the_requested_forms(self):
        frame = parse_submissions(_payload(), 320193, forms=("8-K",))
        assert list(frame["form"]) == ["8-K", "8-K"]

    def test_acceptance_time_is_eastern_not_utc(self):
        """The bug this whole project exists to prevent. 18:03 is after the close;
        read as UTC it becomes 14:03, an intraday filing that never happened."""
        frame = parse_submissions(_payload(), 320193)
        first = frame["acceptance_time"].iloc[0]
        assert str(first.tzinfo) == str(ACCEPTANCE_TZ)
        assert (first.hour, first.minute) == (18, 3)

    def test_all_three_timestamps_are_carried(self):
        """The wrong two are kept deliberately, so the leakage study can price them."""
        frame = parse_submissions(_payload(), 320193)
        row = frame.iloc[0]
        assert row["filing_date"] == date(2024, 10, 31)
        assert row["period_of_report"] == date(2024, 9, 28)
        assert row["acceptance_time"].date() == date(2024, 10, 31)

    def test_empty_report_date_becomes_null_not_a_crash(self):
        frame = parse_submissions(_payload(), 320193, forms=("10-Q",))
        assert pd.isna(frame["period_of_report"].iloc[0])

    def test_item_codes_survive_as_written(self):
        frame = parse_submissions(_payload(), 320193)
        assert frame["items"].iloc[0] == "2.02,9.01"
        assert frame["items"].iloc[1] == "5.02"

    def test_every_shipped_item_code_is_labelled(self):
        for code in ["2.02", "5.02", "1.03", "4.02", "9.01"]:
            assert code in ITEM_LABELS


class TestPagination:
    """Issuers with long histories are sharded, and the shards are flat."""

    def test_flat_shards_are_merged(self):
        shard = {
            "accessionNumber": ["0000320193-19-000001"],
            "filingDate": ["2019-02-01"],
            "reportDate": ["2018-12-29"],
            "acceptanceDateTime": ["2019-02-01T17:02:00.000Z"],
            "form": ["8-K"],
            "items": ["2.02"],
            "primaryDocument": ["old8k.htm"],
        }
        frame = parse_submissions(_payload(shards=[shard]), 320193)
        assert len(frame) == 3           # two recent 8-Ks plus one from the shard
        assert "0000320193-19-000001" in set(frame["accession"])

    def test_nested_shards_are_also_accepted(self):
        """Defensive: the same content sometimes arrives wrapped."""
        nested = {"filings": {"recent": {
            "accessionNumber": ["0000320193-18-000001"],
            "filingDate": ["2018-02-01"],
            "reportDate": ["2017-12-30"],
            "acceptanceDateTime": ["2018-02-01T17:02:00.000Z"],
            "form": ["8-K"], "items": ["2.02"], "primaryDocument": ["x.htm"],
        }}}
        frame = parse_submissions(_payload(shards=[nested]), 320193)
        assert "0000320193-18-000001" in set(frame["accession"])


class TestDegenerateInputs:
    def test_issuer_with_no_matching_forms(self):
        frame = parse_submissions(_payload(), 320193, forms=("S-1",))
        assert frame.empty
        assert "acceptance_time" in frame.columns      # schema survives emptiness

    def test_empty_recent_block(self):
        frame = parse_submissions({"filings": {"recent": {}}}, 320193)
        assert frame.empty

    def test_unparseable_acceptance_time_is_dropped_not_guessed(self):
        """A filing we cannot timestamp cannot be used. Dropping it loses a row;
        guessing at it silently corrupts every number downstream."""
        recent = _recent(acceptanceDateTime=["not a timestamp",
                                             "2024-08-01T09:00:00.000Z",
                                             "2024-05-02T16:30:12.000Z"])
        frame = parse_submissions(_payload(recent), 320193)
        assert len(frame) == 1
        assert frame["accession"].iloc[0] == "0000320193-24-000102"

    def test_missing_items_column_entirely(self):
        recent = _recent()
        del recent["items"]
        frame = parse_submissions(_payload(recent), 320193)
        assert (frame["items"] == "").all()


class TestStripMarkup:
    def test_strips_tags_and_entities(self):
        assert strip_markup("<p>Apple &amp; Co. <b>reported</b></p>") == "Apple & Co. reported"

    def test_drops_tables_and_scripts(self):
        html = "<p>keep</p><table><tr><td>99</td></tr></table><script>x()</script>"
        assert strip_markup(html) == "keep"

    def test_collapses_whitespace(self):
        assert strip_markup("a\n\n   b\t\tc") == "a b c"

    @pytest.mark.parametrize("raw", ["", "   ", "<p></p>"])
    def test_empty_documents_do_not_crash(self, raw):
        assert strip_markup(raw) == ""


class TestCacheFreshness:
    def test_mutable_cache_refreshes_when_stale(self, tmp_path, monkeypatch):
        client = EdgarClient(user_agent="Test test@example.com", cache_dir=tmp_path)
        path = tmp_path / "submissions" / "CIK0000320193.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"old")
        os.utime(path, (0, 0))
        monkeypatch.setattr(client, "_get", lambda _: b"new")

        assert client._cached("submissions/CIK0000320193.json", "https://example.test",
                              max_age=timedelta(hours=6)) == b"new"

    def test_immutable_cache_remains_reusable(self, tmp_path, monkeypatch):
        client = EdgarClient(user_agent="Test test@example.com", cache_dir=tmp_path)
        path = tmp_path / "docs" / "accession.txt"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"cached")
        monkeypatch.setattr(client, "_get", lambda _: pytest.fail("network not expected"))

        assert client._cached("docs/accession.txt", "https://example.test") == b"cached"
