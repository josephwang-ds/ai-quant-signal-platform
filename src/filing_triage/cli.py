"""Command line entry points.

    triage doctor    check that a real ingest would work, in seconds not hours
    triage demo      generate a world, run the pipeline, write the report
    triage ingest    pull real filings and prices from EDGAR and Stooq
    triage run       run the pipeline over whatever is in data/
    triage audit     run the leakage checks and exit non-zero on a failure

`audit` is the one worth wiring into CI: it is the whole point of the project
expressed as an exit code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path

import pandas as pd

from filing_triage import experiments, pipeline, report
from filing_triage.config import PipelineConfig
from filing_triage.guards import LeakageError

DATA = Path("data")
BUILD = DATA / "build"
SAMPLE = DATA / "sample"

SWEEP = [timedelta(0), timedelta(minutes=30), timedelta(hours=6),
         timedelta(days=1), timedelta(days=5)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="triage", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="synthetic world -> pipeline -> report")
    demo.add_argument("--issuers", type=int, default=300)
    demo.add_argument("--seed", type=int, default=20240719)
    demo.add_argument("--out", default=str(BUILD / "report.html"))
    demo.add_argument("--quick", action="store_true",
                      help="skip the leakage study and the embargo sweep")

    ingest = sub.add_parser("ingest", help="pull real EDGAR filings and prices")
    ingest.add_argument("--universe", default=str(SAMPLE / "sp500_membership.csv"))
    ingest.add_argument("--since", default="2022-01-01")
    ingest.add_argument("--limit", type=int, default=None,
                        help="stop after this many issuers (for a smoke test)")

    run = sub.add_parser("run", help="run the pipeline over data/build")
    run.add_argument("--out", default=str(BUILD / "report.html"))

    audit = sub.add_parser("audit", help="run the leakage checks; non-zero on failure")
    audit.add_argument("--issuers", type=int, default=80)

    doctor = sub.add_parser("doctor", help="preflight a real ingest")
    doctor.add_argument("--universe", default=str(BUILD / "sp500_membership.csv"))

    args = parser.parse_args(argv)
    return {"demo": _demo, "ingest": _ingest, "run": _run, "audit": _audit,
            "doctor": _doctor}[args.command](args)


def _doctor(args) -> int:
    """Everything a real pull needs, checked in a few seconds.

    An S&P 500 ingest is tens of thousands of requests over an hour or more.
    Discovering a rejected User-Agent at minute fifty is a waste of an afternoon
    and of the SEC's patience, so all of it is checked up front.
    """
    from filing_triage.ingest.edgar import EdgarClient
    from filing_triage.ingest.prices import fetch_daily
    from filing_triage.ingest.universe import load_membership

    checks: list[tuple[str, bool, str]] = []

    try:
        client = EdgarClient()
        checks.append(("EDGAR_USER_AGENT", True, client.user_agent))
    except ValueError as error:
        checks.append(("EDGAR_USER_AGENT", False, str(error).splitlines()[0]))
        client = None

    if client is not None:
        try:
            checks.append(("SEC reachable", True, client.check_access()))
        except Exception as error:                                  # noqa: BLE001
            checks.append(("SEC reachable", False, str(error).splitlines()[0]))

    from filing_triage.ingest.prices import DEFAULT_SOURCES

    served_by = None
    for source in DEFAULT_SOURCES:
        try:
            frame = fetch_daily("SPY", cache_dir=Path("data/cache/prices"),
                                sources=(source,))
        except Exception:                                           # noqa: BLE001
            continue
        served_by = (source, frame)
        break

    if served_by:
        source, frame = served_by
        checks.append(("price source reachable", True,
                       f"{source}: SPY, {len(frame):,} daily bars to "
                       f"{frame['date'].max()}"))
    else:
        try:
            fetch_daily("SPY", cache_dir=Path("data/cache/prices"))
        except Exception as error:                                  # noqa: BLE001
            checks.append(("price source reachable", False, str(error)))

    universe = Path(args.universe)
    if universe.exists():
        members = load_membership(universe)
        historical = members["end_date"].notna().sum()
        checks.append(("universe file", True,
                       f"{len(members):,} intervals, {historical} historical "
                       f"(a file with 0 historical members is a survivorship trap)"))
    else:
        checks.append(("universe file", False,
                       f"{universe} missing -- run scripts/build_universe.py"))

    width = max(len(name) for name, _, _ in checks)
    for name, ok, detail in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name:<{width}}  {detail}")

    failed = [name for name, ok, _ in checks if not ok]
    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nready -- `make ingest` will work")
    return 0


# --------------------------------------------------------------------------- #
def _demo(args) -> int:
    from filing_triage.synth import generate

    print(f"generating a synthetic world ({args.issuers} issuers)...", flush=True)
    world = generate(n_issuers=args.issuers, seed=args.seed)
    print(f"  {len(world.events):,} filings, {len(world.prices):,} price rows")

    BUILD.mkdir(parents=True, exist_ok=True)
    world.events.to_parquet(BUILD / "events.parquet", index=False)
    world.prices.to_parquet(BUILD / "prices.parquet", index=False)
    world.membership.to_csv(BUILD / "membership.csv", index=False)
    _write_provenance("synthetic", issuers=args.issuers, filings=len(world.events),
                      note=f"generated by filing_triage.synth, seed {args.seed}")

    return _pipeline_and_report(world.events, world.prices, world.membership,
                                Path(args.out), quick=args.quick)


def _run(args) -> int:
    """Read what ingest or demo wrote -- through the loaders, which enforce the
    frames' contracts. Reading the CSV straight leaves the date columns as
    strings, and the failure surfaces much later as a dtype error deep in a join.
    """
    from filing_triage.ingest.prices import load_prices
    from filing_triage.ingest.universe import load_membership

    events = pd.read_parquet(BUILD / "events.parquet")
    prices = load_prices(BUILD / "prices.parquet")
    membership = load_membership(BUILD / "membership.csv")
    return _pipeline_and_report(events, prices, membership, Path(args.out))


def _write_provenance(source: str, **fields) -> None:
    """Record where the frames came from, so the report can say so.

    A page of numbers with no provenance on it is one screenshot away from being
    presented as a fact about the market.
    """
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "provenance.json").write_text(json.dumps(
        {"source": source, "written_at": datetime.now(timezone.utc).isoformat(),
         **fields}, indent=2))


def _read_provenance() -> dict:
    path = BUILD / "provenance.json"
    if not path.exists():
        return {"source": "unknown", "note": "no provenance record was written"}
    return json.loads(path.read_text())


def _pipeline_and_report(events, prices, membership, out: Path,
                         quick: bool = False) -> int:
    print("running the honest pipeline...", flush=True)
    result = pipeline.run(events, prices, membership, PipelineConfig())
    print(f"  {result.audit.summary()}")
    for name, value in _headline(result.metrics):
        print(f"  {name:<34} {value}")

    if quick:
        study = pd.DataFrame(columns=["stage", "note", "n_events", "base_rate",
                                      "average_precision", "roc_auc",
                                      "daily_precision_at_5", "daily_lift_at_5",
                                      "impossible_entries", "impossible_share",
                                      "median_hindsight_hours", "checks_failed"])
        sweep = pd.DataFrame()
    else:
        print("running the leakage study (5 configurations)...", flush=True)
        study = experiments.run_leakage_study(events, prices, membership)
        print(study[["stage", "average_precision", "roc_auc", "checks_failed"]]
              .to_string(index=False))
        print("sweeping the embargo...", flush=True)
        sweep = experiments.embargo_sweep(events, prices, membership, SWEEP)

    BUILD.mkdir(parents=True, exist_ok=True)
    result.queue.to_csv(BUILD / "queue.csv", index=False)
    result.audit.to_frame().to_csv(BUILD / "audit.csv", index=False)
    if not study.empty:
        study.to_csv(BUILD / "leakage_study.csv", index=False)

    if study.empty:
        print("\nreport needs the leakage study; rerun without --quick")
    else:
        path = report.render(result, study, sweep, out,
                             provenance=_read_provenance())
        print(f"\nreport written to {path}")

    if not result.audit.passed:
        print("\nLEAKAGE CHECKS FAILED", file=sys.stderr)
        return 1
    return 0


def _headline(metrics: dict) -> list[tuple[str, str]]:
    if not metrics:
        return []
    return [
        ("events scored", f"{metrics['n_events']:,}"),
        ("base rate", f"{metrics['base_rate']:.1%}"),
        ("average precision", f"{metrics['average_precision']:.3f}"),
        ("ROC AUC", f"{metrics['roc_auc']:.3f}"),
        ("daily precision @5", f"{metrics['daily_precision_at_5']:.1%}"),
        ("daily lift @5", f"{metrics['daily_lift_at_5']:.2f}x"),
    ]


def _audit(args) -> int:
    """The CI gate. Builds a world, runs the honest pipeline, fails on any leak."""
    from filing_triage.synth import generate

    world = generate(n_issuers=args.issuers, seed=5)
    result = pipeline.run(world.events, world.prices, world.membership,
                          PipelineConfig(), compute_importance=False)
    print(result.audit.to_frame().to_string(index=False))
    print(f"\n{result.audit.summary()}")
    try:
        result.audit.raise_if_failed()
    except LeakageError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1
    if result.integrity["impossible_entries"]:
        print(f"\n{result.integrity['impossible_entries']} entries precede their "
              "filing", file=sys.stderr)
        return 1
    return 0


def _ingest(args) -> int:
    """Pull the real thing. Needs network access and EDGAR_USER_AGENT."""
    from filing_triage.ingest.edgar import EdgarClient, parse_submissions
    from filing_triage.ingest.prices import fetch_daily
    from filing_triage.ingest.universe import load_membership

    membership = load_membership(args.universe)
    if args.limit:
        membership = membership.head(args.limit)

    client = EdgarClient()
    print(f"  {client.check_access()}", flush=True)
    since = pd.Timestamp(args.since).date()

    unresolved = membership[membership["cik"].isna()]
    if len(unresolved):
        print(f"  skipping {len(unresolved)} interval(s) with no CIK "
              f"({', '.join(sorted(set(unresolved['ticker']))[:8])}"
              f"{', ...' if len(set(unresolved['ticker'])) > 8 else ''}) -- "
              f"their filings cannot be fetched", flush=True)
    membership = membership[membership["cik"].notna()]

    filings, prices, failures = [], [], []
    for row in membership.drop_duplicates("cik").itertuples():
        try:
            frame = parse_submissions(client.submissions(row.cik), row.cik)
            frame = frame[frame["filing_date"] >= since]
            frame["ticker"] = row.ticker
            frame["text"] = [
                client.document_text(row.cik, accession, document)
                for accession, document in zip(frame["accession"],
                                               frame["primary_document"])
            ]
            filings.append(frame)
            prices.append(fetch_daily(row.ticker))
            print(f"  {row.ticker:<6} {len(frame):>4} filings", flush=True)
        except Exception as error:            # noqa: BLE001 - one bad issuer must
            failures.append((row.ticker, str(error)))   # not abort a long pull
            print(f"  {row.ticker:<6} FAILED: {error}", flush=True)

    if not filings:
        print("nothing ingested", file=sys.stderr)
        return 1

    prices.append(fetch_daily("SPY"))
    events = pd.concat(filings, ignore_index=True)
    events["event_id"] = events["accession"]

    BUILD.mkdir(parents=True, exist_ok=True)
    events.to_parquet(BUILD / "events.parquet", index=False)
    pd.concat(prices, ignore_index=True).to_parquet(BUILD / "prices.parquet", index=False)
    membership.to_csv(BUILD / "membership.csv", index=False)

    _write_provenance("edgar", issuers=len(filings), filings=len(events),
                      failed_issuers=[t for t, _ in failures],
                      unresolved_ciks=int(len(unresolved)),
                      note="SEC EDGAR submissions + daily bars")

    print(f"\n{len(events):,} filings from {len(filings)} issuers "
          f"({len(failures)} failed) -> {BUILD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
