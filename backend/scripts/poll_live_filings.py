#!/usr/bin/env python3
"""Record 10-K filings as they arrive, with *measured* receipt times.

This is the only part of the pipeline whose value cannot be manufactured later.
Everything else in the corpus is backfilled: receipt time is reconstructed from
publish time plus an assumed polling interval, and every such record is honestly
labelled ``SIMULATED``. That labelling is correct, but it is still an
assumption.

A collector that is actually running when a filing appears *measures* receipt,
and its records are ``OBSERVED``. No amount of later backfilling can produce
that — the observation either happened or it did not. So the sample this script
accumulates is small at first and grows linearly with wall-clock time, which is
exactly why it is worth starting before it is needed rather than when it is.

Cheap by design: one index request per run. Run it a few times a day from cron
or launchd.

    */30 9-18 * * 1-5  cd /path/to/backend && .venv/bin/python \\
        scripts/poll_live_filings.py --name "Your Name" --email you@example.com

Records append to ``outputs/text_corpus/observed/YYYY-MM.jsonl``. Re-running is
safe: an accession already recorded is never rewritten, so the first observed
receipt time stands rather than being overwritten by a later poll.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.text_signals.edgar_fetcher import (  # noqa: E402
    RateLimiter,
    SecUserAgent,
    _default_http_get,
    parse_acceptance_datetime,
)
from app.text_signals.timestamps import IngestSource  # noqa: E402

ET = ZoneInfo("America/New_York")
DEFAULT_ROOT = _BACKEND_ROOT / "outputs" / "text_corpus"

#: EDGAR's rolling "recent filings" feed, filtered to 10-K.
RECENT_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K"
    "&dateb=&owner=include&count=100&action=getcompany&output=atom"
)
#: The daily index is more reliable than the Atom feed for whole-market sweeps.
DAILY_INDEX_URL = (
    "https://www.sec.gov/Archives/edgar/daily-index/{year}/QTR{quarter}/"
    "form.{yyyymmdd}.idx"
)


def _log(msg: str) -> None:
    print(f"[{datetime.now(ET):%Y-%m-%d %H:%M:%S %Z}] {msg}", flush=True)


def poll_once(root: Path, user_agent: SecUserAgent, *, day: datetime | None = None) -> int:
    """One sweep of the daily index. Returns the number of new records."""
    from app.text_signals.filing_universe import parse_form_index

    now = datetime.now(ET)
    target = day or now
    url = DAILY_INDEX_URL.format(
        year=target.year,
        quarter=(target.month - 1) // 3 + 1,
        yyyymmdd=target.strftime("%Y%m%d"),
    )

    headers = {
        "User-Agent": user_agent.header,
        "Accept-Encoding": "gzip, deflate",
    }
    RateLimiter().acquire()
    try:
        body = _default_http_get(url, headers)
    except Exception as exc:
        # Weekends, holidays and not-yet-published days have no index. That is
        # an expected outcome, not a failure worth alarming about.
        _log(f"no daily index for {target:%Y-%m-%d} ({exc})")
        return 0

    # Receipt is measured *here*, immediately after the bytes arrive.
    received_at = datetime.now(timezone.utc).astimezone(ET)
    entries = parse_form_index(body.decode("utf-8", "replace"))

    out_dir = root / "observed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{target:%Y-%m}.jsonl"

    seen: set[str] = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            if line.strip():
                seen.add(json.loads(line)["accession_number"])

    added = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for entry in entries:
            if entry.accession_number in seen:
                continue  # first observation wins; never overwrite
            fh.write(
                json.dumps(
                    {
                        "accession_number": entry.accession_number,
                        "cik": entry.cik,
                        "company": entry.company_name,
                        "form_type": entry.form_type,
                        "filing_date": entry.filing_date,
                        "ingest_time": received_at.isoformat(),
                        "ingest_time_source": IngestSource.OBSERVED.value,
                        "source": "edgar:daily-index",
                    }
                )
                + "\n"
            )
            added += 1
    _log(
        f"{target:%Y-%m-%d}: {len(entries)} 10-K in index, {added} new OBSERVED "
        f"records -> {out_path.name}"
    )
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True)
    ap.add_argument("--email", required=True)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument(
        "--backfill-days",
        type=int,
        default=0,
        help="Also sweep this many prior days. Those records are still OBSERVED "
        "only in the sense that this collector read them now; prefer 0 for a "
        "genuine live sample.",
    )
    args = ap.parse_args()

    root = Path(args.root)
    ua = SecUserAgent(args.name, args.email)

    total = poll_once(root, ua)
    for back in range(1, args.backfill_days + 1):
        total += poll_once(root, ua, day=datetime.now(ET) - timedelta(days=back))
    _log(f"total new records: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
