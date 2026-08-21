# data/

    sample/     small committed fixtures
    cache/      raw EDGAR and price downloads (gitignored, safe to delete)
    build/      everything the pipeline derives (gitignored)

## Why there is no committed S&P 500 membership file

A membership file generated today is a fact about today. Checked into git it goes
stale, and a stale universe file is the survivorship bug wearing a helpful face:
it silently deletes the issuers that were dropped after a collapse, which are the
ones whose disclosures moved most.

So it is generated, not committed:

    export EDGAR_USER_AGENT="Your Name you@example.com"
    python scripts/build_universe.py --out data/build/sp500_membership.csv

`make demo` needs none of this -- it builds its own synthetic universe, complete
with issuers that join and leave, so the survivorship guard has something to catch.
