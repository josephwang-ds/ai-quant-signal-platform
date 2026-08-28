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
import math
import sys
from datetime import UTC, datetime, timedelta
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
    demo.add_argument("--force", action="store_true",
                      help="overwrite a real EDGAR build in data/build")

    ingest = sub.add_parser("ingest", help="pull real EDGAR filings and prices")
    ingest.add_argument("--universe", default=str(BUILD / "universe.csv"))
    ingest.add_argument("--since", default="2022-01-01")
    ingest.add_argument("--limit", type=int, default=None,
                        help="stop after this many issuers (for a smoke test)")

    run = sub.add_parser("run", help="run the pipeline over data/build")
    run.add_argument("--out", default=str(BUILD / "report.html"))

    audit = sub.add_parser("audit", help="run the leakage checks; non-zero on failure")
    audit.add_argument("--issuers", type=int, default=80)

    doctor = sub.add_parser("doctor", help="preflight a real ingest")
    doctor.add_argument("--universe", default=str(BUILD / "universe.csv"))

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
        except Exception:                                  # noqa: BLE001
            continue
        served_by = (source, frame)
        break

    if served_by:
        source, frame = served_by
        checks.append(("price source reachable", True,
                       (f"{source}: SPY, {len(frame):,} daily bars to "
                        f"{frame['date'].max()}")))
    else:
        try:
            fetch_daily("SPY", cache_dir=Path("data/cache/prices"))
        except Exception as error:                                  # noqa: BLE001
            checks.append(("price source reachable", False, str(error)))

    universe = Path(args.universe)
    if universe.exists():
        members = load_membership(universe)
        historical = int(members["end_date"].notna().sum())
        quality = _universe_meta(universe)
        if quality.get("survivorship_controlled") is False:
            detail = (f"{len(members):,} issuers, {quality.get('universe_quality')} "
                      "-- survivorship NOT controlled on this path")
        else:
            detail = (f"{len(members):,} intervals, {historical} historical "
                      f"(0 historical would mean a survivorship trap)")
        checks.append(("universe file", True, detail))
    else:
        checks.append(("universe file", False,
                       f"{universe} missing -- run scripts/build_demo_universe.py"))

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
def _guard_real_build(force: bool) -> int | None:
    """Refuse to overwrite a real EDGAR build with a synthetic one.

    `demo` and `ingest` write their frames to the same three files, so running
    the demo after a real pull silently replaces tens of thousands of filings
    with a simulation. Nothing about the result looks wrong afterwards -- the
    pipeline runs, the report renders, the numbers are plausible -- which puts
    this in the same category as the leaks the project is about: a failure that
    produces an answer instead of an error.

    The README hands a reader the sequence that triggers it, `make demo` first
    and `make ingest` later, so this is the expected order of operations rather
    than an unlikely mistake.
    """
    provenance = _read_provenance()
    if provenance.get("source") != "edgar" or force:
        return None
    print(
        f"data/build holds a real EDGAR build "
        f"({provenance.get('filings', '?'):,} filings from "
        f"{provenance.get('issuers', '?')} issuers, written "
        f"{provenance.get('written_at', 'at an unrecorded time')}).\n"
        "\n"
        "The demo writes its synthetic world to the same files and would "
        "replace it.\n"
        "The ingest cache in data/cache can rebuild it, but that is a rerun of "
        "`make ingest`,\n"
        "not an undo.\n"
        "\n"
        "  make ingest            rebuild the real frames from cache\n"
        "  make demo FORCE=1      overwrite anyway (also make quick FORCE=1)\n"
        "  triage demo --force    the same, without make",
        file=sys.stderr,
    )
    return 1


def _demo(args) -> int:
    from filing_triage.synth import generate

    refused = _guard_real_build(args.force)
    if refused is not None:
        return refused

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
    profile = load_issuer_profile()
    return _pipeline_and_report(events, prices, membership, Path(args.out),
                                issuer_profile=profile)


def _universe_meta(universe: Path) -> dict:
    """What the universe file says about its own limitations, if anything."""
    sidecar = universe.with_suffix(".meta.json")
    return json.loads(sidecar.read_text()) if sidecar.exists() else {}


def _write_issuer_profile(client, events: pd.DataFrame) -> None:
    """Static issuer attributes, from submissions already in the cache.

    Written during ingest rather than fetched later because the payload it reads
    is the same one the filings came from -- a second pass would re-request it,
    and could get a different answer, since EDGAR reports these as of today.
    """
    from filing_triage.ingest.edgar import parse_issuer_profile

    rows = []
    for cik in sorted({int(c) for c in events["cik"].unique()}):
        try:
            rows.append(parse_issuer_profile(client.submissions(cik), cik))
        except Exception:      # noqa: BLE001 - one bad issuer must not lose the rest
            continue
    if rows:
        pd.DataFrame(rows).to_csv(BUILD / "issuer_profile.csv", index=False)
        print(f"  issuer profile for {len(rows)} issuers")


def load_issuer_profile() -> pd.DataFrame | None:
    """The profile table, or None when there is not one.

    Absent for a synthetic world, which has no EDGAR behind it, so the features
    built from it degrade to a constant rather than raising -- the demo path must
    keep working without pretending the attributes exist.
    """
    path = BUILD / "issuer_profile.csv"
    return pd.read_csv(path) if path.exists() else None


def _write_provenance(source: str, **fields) -> None:
    """Record where the frames came from, so the report can say so.

    A page of numbers with no provenance on it is one screenshot away from being
    presented as a fact about the market.
    """
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "provenance.json").write_text(json.dumps(
        {"source": source, "written_at": datetime.now(UTC).isoformat(),
         **fields}, indent=2))


def _read_provenance() -> dict:
    path = BUILD / "provenance.json"
    if not path.exists():
        return {"source": "unknown", "note": "no provenance record was written"}
    return json.loads(path.read_text())


def _pipeline_and_report(events, prices, membership, out: Path,
                         quick: bool = False,
                         issuer_profile: pd.DataFrame | None = None) -> int:
    print("running the honest pipeline...", flush=True)
    result = pipeline.run(events, prices, membership, PipelineConfig(),
                          issuer_profile=issuer_profile)
    print(f"  {result.audit.summary()}")
    for name, value in _headline(result.metrics, result.baseline_comparisons):
        print(f"  {name:<34} {value}")

    _print_attrition(result.integrity, len(events))

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
        print(study[["stage", "n_events", "average_precision", "roc_auc",
                     "impossible_entries", "median_hindsight_hours",
                     "checks_failed"]].to_string(index=False))
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
        path = report.render(
            result, study, sweep, out,
            provenance=_read_provenance(),
            capacity=experiments.capacity_profile(result.predictions, result.events),
        )
        print(f"\nreport written to {path}")

    if not result.audit.passed:
        print("\nLEAKAGE CHECKS FAILED", file=sys.stderr)
        return 1
    return 0


def _print_attrition(integrity: dict, ingested: int) -> None:
    """Account for every filing that did not make it to a score.

    Between ingest and scoring the count drops, and a drop nobody explains is
    indistinguishable from a bug. Silent data loss belongs in the same category
    as silent leakage: it moves the answer and nothing says so.
    """
    attrition = integrity.get("attrition") or {}
    dropped_by_universe = integrity.get("events_dropped_by_universe", 0)
    if not attrition and not dropped_by_universe:
        return

    scored = integrity.get("events_scored", 0)
    print(f"\n  of {ingested:,} filings, {scored:,} were scored out of sample")
    if dropped_by_universe:
        print(f"    {dropped_by_universe:>6,}  issuer outside the universe on that date")
    for reason, count in sorted(attrition.items(), key=lambda kv: -kv[1]):
        print(f"    {count:>6,}  {reason}")


def _interval(metrics: dict, key: str, fmt: str = "{:.3f}") -> str:
    """The 95% range beside a point estimate, or nothing if it was not computed.

    Blank rather than a placeholder. The leakage and embargo studies run the
    pipeline a dozen times with the bootstrap switched off, and printing
    `[nan, nan]` on those rows would read as a computation that failed rather
    than one deliberately skipped.
    """
    low, high = metrics.get(f"{key}_ci_low"), metrics.get(f"{key}_ci_high")
    if low is None or high is None:
        return ""
    if not (math.isfinite(low) and math.isfinite(high)):
        return ""
    return f"  [{fmt.format(low)}, {fmt.format(high)}]"


def _suffix(lift: str) -> str:
    """Parenthesise a lift beside a baseline's own precision, or print nothing."""
    return f"  (model {lift})" if lift else ""


def _paired_lift(comparisons: pd.DataFrame, name: str) -> str:
    """The model's lift over one baseline, with its paired interval.

    Paired: model and baseline are rescored on one shared resample of sessions,
    so this is the interval on their *difference*. Bootstrapping the two means
    separately would throw that pairing away and widen the range for no reason.
    """
    if comparisons is None or comparisons.empty:
        return ""
    row = comparisons[comparisons["baseline"] == name]
    if row.empty:
        return ""
    lift, low, high = (float(row.iloc[0]["lift"]), float(row.iloc[0]["lift_ci_low"]),
                       float(row.iloc[0]["lift_ci_high"]))
    if not all(math.isfinite(v) for v in (lift, low, high)):
        return ""
    return f"{lift:.2f}x [{low:.2f}, {high:.2f}]"


def _headline(metrics: dict,
              comparisons: pd.DataFrame | None = None) -> list[tuple[str, str]]:
    if not metrics:
        return []
    rows = [
        ("events scored", f"{metrics['n_events']:,}"),
        ("base rate", f"{metrics['base_rate']:.1%}"),
        ("average precision",
         f"{metrics['average_precision']:.3f}{_interval(metrics, 'average_precision')}"),
        ("ROC AUC", f"{metrics['roc_auc']:.3f}{_interval(metrics, 'roc_auc')}"),
        ("filings per session (median)",
         f"{metrics.get('filings_per_session_median', float('nan')):.0f}"),
    ]
    counted = metrics.get("daily_sessions_at_5", 0)
    if metrics.get("daily_usable_at_5"):
        random_lift = _paired_lift(comparisons, "random")
        ceiling = metrics.get("daily_oracle_precision_at_5", float("nan"))
        span = metrics.get("daily_span_captured_at_5", float("nan"))
        rows += [
            ("daily precision @5", (f"{metrics['daily_precision_at_5']:.1%} "
                                    f"of a {ceiling:.1%} ceiling "
                                    f"({counted} sessions)")),
            # The lift depends on a reading capacity the project assumed rather
            # than derived; the span survives it. Both are printed, span first.
            ("share of achievable span @5", f"{span:.0%}"),
            ("lift vs matched random @5",
             random_lift or f"{metrics['daily_lift_at_5']:.2f}x"),
            ("arrival-order precision @5",
             f"{metrics.get('daily_arrival_precision_at_5', float('nan')):.1%}"
             + _suffix(_paired_lift(comparisons, "arrival"))),
            ("Item 2.02 heuristic precision @5",
             f"{metrics.get('daily_item_202_precision_at_5', float('nan')):.1%}"
             + _suffix(_paired_lift(comparisons, "item_202"))),
        ]
    else:
        rows.append(("daily precision @5",
                     (f"not reported -- only {counted} sessions had more than 5 "
                      f"filings, so the queue metric would be measuring the "
                      f"calendar, not the ranker")))
    return rows


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
                                               frame["primary_document"],
                                               strict=True)
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
    _write_issuer_profile(client, events)
    events.to_parquet(BUILD / "events.parquet", index=False)
    pd.concat(prices, ignore_index=True).to_parquet(BUILD / "prices.parquet", index=False)
    membership.to_csv(BUILD / "membership.csv", index=False)

    _write_provenance("edgar", issuers=len(filings), filings=len(events),
                      failed_issuers=[t for t, _ in failures],
                      unresolved_ciks=len(unresolved),
                      universe=_universe_meta(Path(args.universe)),
                      note="SEC EDGAR submissions + daily bars")

    print(f"\n{len(events):,} filings from {len(filings)} issuers "
          f"({len(failures)} failed) -> {BUILD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
