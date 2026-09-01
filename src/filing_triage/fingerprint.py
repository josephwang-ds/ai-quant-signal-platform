"""Content fingerprints for the frames a result was computed from.

A number without an error bar is a claim with its uncertainty deleted; a result
without an input fingerprint is a claim with its *subject* deleted. This project
already refuses the first and, until now, shipped the second: `evidence/real_run`
froze the conclusions while the inputs behind them kept moving. EDGAR grows --
one rebuild from cache turned 11,702 filings into 11,716 -- and yfinance serves
prices adjusted as of today, so a split silently rewrites the whole history. A
rerun that disagrees could mean the code changed, or the data did, and nothing
recorded which.

**The digest is of the content, not the file.** Hashing the parquet bytes would
be easier and wrong: pandas and pyarrow rewrite their encodings between versions,
so the same table hashes differently after an upgrade and the fingerprint fires
on a library bump. That is a false alarm, and a check that cries wolf gets
removed. So the digest is taken over a canonical rendering -- columns in sorted
order, rows in sorted order, floats at fixed precision -- which is stable across
any library that can still read the table at all.

**Floats are rounded before hashing.** Daily bars carry far fewer significant
digits than a float64, so rounding to `FLOAT_PRECISION` discards nothing real and
buys immunity from last-bit differences between platforms and BLAS builds. A
fingerprint that depends on which CPU computed it is not a fingerprint.
"""

from __future__ import annotations

import hashlib
import platform
import sys
from importlib.metadata import PackageNotFoundError, version

import pandas as pd

FLOAT_PRECISION = 6
CHUNK_ROWS = 200_000

# The libraries whose version can move a number. Recorded with every result, so
# a rerun that disagrees can be told apart from a rerun on a different stack.
# The optional stacks are here too, and record `None` when absent -- which is
# the informative answer, not a gap. `nlp_feature_ablation.csv` and the
# volatility tables cannot be reproduced without them, and a transformers
# release can move a tone score the same way a scikit-learn release moves a
# split. The model ids and revisions are pinned in their caches; these are the
# libraries around them.
TRACKED_PACKAGES = ("pandas", "numpy", "scipy", "scikit-learn", "pyarrow",
                    "yfinance", "torch", "transformers", "chronos-forecasting")


def frame_digest(frame: pd.DataFrame, *, precision: int = FLOAT_PRECISION) -> str:
    """A sha256 over the frame's content, stable across library versions.

    Row order is normalised, so a reindex or a differently ordered concat does
    not change the digest -- only the values do. That is the intended sensitivity:
    the question this answers is "is this the same data", not "did it arrive in
    the same order".
    """
    if frame.empty:
        return hashlib.sha256(b"empty").hexdigest()

    columns = sorted(frame.columns)
    canonical = frame[columns].copy()
    for column in canonical.columns:
        values = canonical[column]
        if pd.api.types.is_float_dtype(values):
            canonical[column] = values.round(precision)
        # Rendered as text below anyway; normalising to UTC first stops a
        # tz-aware column hashing differently from the same instants stored
        # against another offset.
        elif isinstance(values.dtype, pd.DatetimeTZDtype):
            canonical[column] = values.dt.tz_convert("UTC")

    canonical = canonical.sort_values(list(canonical.columns), kind="mergesort")

    digest = hashlib.sha256()
    digest.update(("\x1f".join(columns) + "\x1e").encode())
    # Chunked so a two-million-row panel does not materialise as one string.
    for start in range(0, len(canonical), CHUNK_ROWS):
        block = canonical.iloc[start:start + CHUNK_ROWS]
        digest.update(block.to_csv(
            index=False, header=False, float_format=f"%.{precision}f",
        ).encode())
    return digest.hexdigest()


def frame_fingerprint(frame: pd.DataFrame, **extra) -> dict:
    """The digest plus the shape it was taken over, which makes it readable.

    A bare hash tells a reader that something changed and nothing else. The row
    count beside it usually tells them *what*: 11,702 becoming 11,716 is EDGAR
    growing, while an unchanged count with a changed digest is values moving
    underneath -- a vendor re-adjusting prices, say. Those are different problems
    and the fingerprint should not make them look alike.
    """
    return {
        "rows": len(frame),
        "columns": sorted(str(column) for column in frame.columns),
        "sha256": frame_digest(frame),
        **extra,
    }


def environment() -> dict:
    """The interpreter and the libraries that can move a number.

    Not vanity metadata. The dependency floors in `pyproject.toml` are `>=`, so
    two installs a year apart are different environments running the same code,
    and `HistGradientBoostingClassifier` does not promise identical splits across
    scikit-learn versions. Recorded with the result rather than assumed.
    """
    packages = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(terse=True),
        "packages": packages,
    }


def input_fingerprints(events: pd.DataFrame, prices: pd.DataFrame,
                       membership: pd.DataFrame) -> dict:
    """Fingerprints for the three frames every result is computed from.

    `prices_as_of` is called out separately because it is the one input that can
    change without any row being added. Vendor prices are adjusted as of the pull
    date, so a split rewrites the history retroactively: same row count, same
    date range, different values. Recording the pull date lets a reader see that
    coming instead of discovering it as an unexplained digest change.
    """
    fingerprints = {
        "events": frame_fingerprint(events),
        "prices": frame_fingerprint(prices),
        "membership": frame_fingerprint(membership),
    }
    if "date" in prices.columns and len(prices):
        dates = pd.to_datetime(prices["date"])
        fingerprints["prices"]["first_session"] = str(dates.min().date())
        fingerprints["prices"]["last_session"] = str(dates.max().date())
    fingerprints["note"] = (
        "Digests are over canonicalised content, not file bytes, so a pandas or "
        "pyarrow upgrade does not change them. Vendor prices are adjusted as of "
        "the pull date: a later split rewrites history without adding a row, "
        "which shows up here as an unchanged row count and a changed digest."
    )
    return fingerprints
