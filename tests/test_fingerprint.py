"""Input fingerprints, and the two ways of computing them that would be useless.

`evidence/real_run` froze the conclusions while the inputs behind them kept
moving: EDGAR grows, and vendor prices are adjusted as of the pull date, so a
split rewrites history without adding a row. A rerun that disagreed could mean
the code changed or the data did, and nothing recorded which.

A fingerprint only helps if it fires on exactly that. These pin down that it
survives the things that should not matter -- row order, a library that writes
parquet differently -- and catches the things that should.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from filing_triage.fingerprint import (
    environment,
    frame_digest,
    frame_fingerprint,
    input_fingerprints,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def panel():
    rng = np.random.default_rng(3)
    return pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "NVDA"] * 8,
        "date": pd.date_range("2024-01-01", periods=24, freq="D"),
        "close": rng.normal(100, 5, 24),
        "volume": rng.integers(1_000, 9_000, 24),
    })


class TestWhatMustNotChangeTheDigest:
    def test_row_order_is_irrelevant(self, panel):
        """The question is 'is this the same data', not 'did it arrive in the
        same order'. A reindex or a differently ordered concat must not fire."""
        assert frame_digest(panel) == frame_digest(panel.sample(frac=1, random_state=9))

    def test_column_order_is_irrelevant(self, panel):
        shuffled = panel[list(reversed(panel.columns))]
        assert frame_digest(panel) == frame_digest(shuffled)

    def test_a_parquet_round_trip_is_stable(self, panel, tmp_path):
        """The reason the digest is over content and not file bytes: pandas and
        pyarrow rewrite their encodings between versions, and a fingerprint that
        fires on a library upgrade is a false alarm that gets it removed."""
        path = tmp_path / "panel.parquet"
        panel.to_parquet(path, index=False)
        assert frame_digest(pd.read_parquet(path)) == frame_digest(panel)

    def test_float_noise_below_the_recorded_precision_is_ignored(self, panel):
        """Daily bars carry far fewer significant digits than a float64, so a
        last-bit difference between platforms is not a data change."""
        jittered = panel.copy()
        jittered["close"] += 1e-12
        assert frame_digest(jittered) == frame_digest(panel)

    def test_an_equivalent_timezone_representation_is_ignored(self):
        utc = pd.DataFrame({"t": pd.to_datetime(["2024-05-01T14:30:00Z"])})
        eastern = pd.DataFrame({"t": utc["t"].dt.tz_convert("America/New_York")})
        assert frame_digest(utc) == frame_digest(eastern)


class TestWhatMustChangeTheDigest:
    def test_a_changed_value_is_caught(self, panel):
        tweaked = panel.copy()
        tweaked.loc[0, "close"] = tweaked.loc[0, "close"] + 0.01
        assert frame_digest(tweaked) != frame_digest(panel)

    def test_an_added_row_is_caught(self, panel):
        """EDGAR grows. One rebuild from cache turned 11,702 filings into
        11,716, and nothing said so."""
        grown = pd.concat([panel, panel.iloc[[0]]], ignore_index=True)
        assert frame_digest(grown) != frame_digest(panel)

    def test_a_dropped_column_is_caught(self, panel):
        assert frame_digest(panel.drop(columns="volume")) != frame_digest(panel)

    def test_a_retroactive_price_adjustment_is_caught(self, panel):
        """The case a row count cannot see: a split re-adjusts every historical
        close, leaving the shape identical and every value different."""
        split = panel.copy()
        split["close"] = split["close"] / 4.0
        assert len(split) == len(panel)
        assert frame_digest(split) != frame_digest(panel)


class TestTheFingerprintIsReadable:
    def test_it_carries_the_shape_beside_the_hash(self, panel):
        """A bare hash says something changed and nothing else. The row count
        beside it usually says what: a changed count is EDGAR growing, an
        unchanged count with a changed digest is values moving underneath."""
        fingerprint = frame_fingerprint(panel)
        assert fingerprint["rows"] == len(panel)
        assert fingerprint["columns"] == sorted(panel.columns)
        assert re.fullmatch(r"[0-9a-f]{64}", fingerprint["sha256"])

    def test_the_price_window_is_recorded(self, panel):
        fingerprints = input_fingerprints(panel, panel, panel)
        assert fingerprints["prices"]["first_session"] == "2024-01-01"
        assert fingerprints["prices"]["last_session"] == "2024-01-24"

    def test_an_empty_frame_does_not_raise(self):
        assert frame_digest(pd.DataFrame()) == frame_digest(pd.DataFrame())


class TestEnvironmentIsRecorded:
    def test_the_libraries_that_can_move_a_number_are_named(self):
        """`>=` floors mean two installs a year apart are different numerics
        running the same code, and HistGradientBoostingClassifier does not
        promise identical splits across scikit-learn versions."""
        packages = environment()["packages"]
        for name in ("pandas", "numpy", "scikit-learn"):
            assert packages[name], f"{name} version was not recorded"

    def test_the_interpreter_is_recorded(self):
        assert re.match(r"^\d+\.\d+\.\d+", environment()["python"])


class TestTheLockfileIsUsable:
    LOCK = ROOT / "requirements.lock"

    def test_it_exists_and_pins_exactly(self):
        lines = [line.strip() for line in self.LOCK.read_text().splitlines()]
        pins = [line for line in lines if line and not line.startswith("#")]
        assert pins, "requirements.lock has no pins"
        loose = [pin for pin in pins if "==" not in pin]
        assert not loose, f"requirements.lock must pin exactly, found {loose}"

    def test_it_pins_every_library_that_can_move_a_number(self):
        text = self.LOCK.read_text().lower()
        for name in ("pandas", "numpy", "scipy", "scikit-learn", "pyarrow"):
            assert f"{name}==" in text, f"{name} is not pinned"

    def test_it_does_not_pin_the_project_itself(self):
        """A lockfile that installs the thing being locked cannot be used to set
        up the environment the thing is then installed into."""
        assert "filing-triage==" not in self.LOCK.read_text()
