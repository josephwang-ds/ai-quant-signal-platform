#!/usr/bin/env python3
"""The insider-trading study, exported as evidence rather than as a claim.

    python scripts/export_insider_evidence.py

Three things are measured, and the first is the one this project exists to do.

**A new rung on the leakage ladder.** A Form 4 carries two dates. The insider
traded on one; the market could not know until the other, up to two business
days later. Anchoring the event study at the transaction date is the natural
thing to do -- it is the more precise field, it sits right there in the XML -- and
it is hindsight. Both anchors are run through the same pipeline and the
difference is reported, exactly as the 8-K ladder reports what each of its four
shortcuts is worth.

**Whether the classic classification survives contact with disclosure.** Cohen,
Malloy and Pomorski inferred which insiders trade on a schedule from whether
they trade the same month year after year. Since 2023 filers must state it.
Scoring the inference against the statement is a check on a well-known method
against ground truth that did not exist when it was published.

**Which filings deserve a read.** The same question the 8-K ranker asks, on a
different source: reaction *magnitude*, never direction. Insider buying is the
half of this literature with documented predictive power and it is directional,
so the honest thing is to say that plainly and not model it here -- the project's
standing claim is that direction is never modelled, and one unmeasured effect is
not a reason to break it.

**The survivorship caveat is louder here than anywhere else in the project.**
The universe is companies listed today. Small companies fail often, and the
insiders most conspicuously absent are the ones who bought shortly before a
collapse. Every result below is therefore biased in favour of insider buying,
and the size of that bias is unknown.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from filing_triage.config import PipelineConfig
from filing_triage.fingerprint import environment, frame_fingerprint
from filing_triage.ingest.ownership import open_market, signed_value
from filing_triage.ingest.prices import fetch_daily, to_returns
from filing_triage.insiders import (
    causal_routine,
    classification_agreement,
    gap_profile,
    to_events,
)
from filing_triage.labels import build_labels
from filing_triage.pit import TradingClock, naive_entry_session_from_filing_date

MARKET = "SPY"

# The SEC's deadline is two business days. Ten calendar days covers that plus a
# holiday weekend and is the line between "filed on time" and "filed late".
#
# The tail matters in a way that is worth stating, because it runs against
# intuition: a filing whose transaction is twenty years old -- and a handful are --
# puts the naive anchor's entry in an unrelated decade, which is noise rather
# than hindsight. Noise pulls that arm toward the mean and makes the leak look
# *smaller*. So the headline keeps every filing, and this cap is reported beside
# it as the version where the naive anchor is doing what it is accused of.
ON_TIME_DAYS = 10

# The two ways to anchor the study. `acceptance` is the only honest one; the
# other is here to be measured, not to be used.
ANCHORS = ("transaction_date", "acceptance_time")


def price_panel(tickers, *, market: str = MARKET) -> pd.DataFrame:
    """Daily bars for the universe plus the benchmark, from cache.

    Reads through `fetch_daily`, which returns a cached parquet when it has one,
    so this touches the network only for a ticker the screen never fetched.
    """
    frames, missing = [], []
    for ticker in [*sorted(set(tickers)), market]:
        try:
            bars = fetch_daily(ticker)
        except Exception:                       # noqa: BLE001 - a dead ticker must
            missing.append(ticker)              # not stop the study
            continue
        if bars.empty:
            missing.append(ticker)
            continue
        frames.append(bars)
    if missing:
        print(f"  no price history for {len(missing)} tickers "
              f"({', '.join(missing[:6])}{', ...' if len(missing) > 6 else ''})")
    return pd.concat(frames, ignore_index=True)


def anchored_events(events: pd.DataFrame, anchor: str,
                    clock: TradingClock) -> pd.DataFrame:
    """Entry sessions under one anchoring rule.

    `acceptance_time` runs through the same clock the 8-K path uses: the first
    session whose open is at or after the moment EDGAR made the filing public.
    `transaction_date` uses the naive rule -- tradable at its own open -- which
    is what an analysis reaching for the more precise field would do.
    """
    out = events.copy()
    if anchor == "acceptance_time":
        out = out[out["acceptance_time"].notna()]
        out["entry_session"] = out["acceptance_time"].map(clock.entry_session)
    else:
        traded = pd.to_datetime(out["first_transaction_date"], errors="coerce")
        # Dropped before the calendar lookup, not after: the session rule raises
        # on a missing date rather than returning nothing, and one Form 4 with an
        # unparseable date must not abort an export over a hundred thousand of
        # them.
        out = out[traded.notna()]
        out["entry_session"] = traded[traded.notna()].dt.date.map(
            naive_entry_session_from_filing_date)
    return out.dropna(subset=["entry_session"])


def ladder(events: pd.DataFrame, returns: pd.DataFrame,
           config: PipelineConfig) -> tuple[pd.DataFrame, dict]:
    """What anchoring at the transaction date is worth, on the same filings.

    Both rules are scored on the filings that survive *both*, so the comparison
    cannot be won by one rule keeping events the other drops.
    """
    clock = TradingClock()
    labelled = {}
    for anchor in ANCHORS:
        frame = anchored_events(events, anchor, clock)
        labels = build_labels(frame, returns, config)
        labelled[anchor] = labels.set_index("event_id")

    shared = labelled[ANCHORS[0]].index
    for table in labelled.values():
        shared = shared.intersection(table.index)

    rows = []
    for anchor, table in labelled.items():
        block = table.loc[shared]
        reaction = block["reaction"].abs()
        rows.append({
            "anchor": anchor,
            "honest": anchor == "acceptance_time",
            "filings": len(block),
            "median_abs_reaction": float(reaction.median()),
            "mean_abs_reaction": float(reaction.mean()),
            "material_share": float((reaction >= config.reaction_threshold).mean()),
        })
    table = pd.DataFrame(rows)
    naive, honest = table.iloc[0], table.iloc[1]
    summary = {
        "shared_filings": len(shared),
        # The number the ladder exists to produce: how much apparent reaction a
        # transaction-date anchor manufactures out of days the market had not
        # yet seen the filing.
        "inflation_in_material_share": float(naive["material_share"]
                                             - honest["material_share"]),
        "inflation_in_median_reaction": float(naive["median_abs_reaction"]
                                              - honest["median_abs_reaction"]),
    }
    return table, summary


def reaction_by_kind(events: pd.DataFrame, labels: pd.DataFrame,
                     config: PipelineConfig, minimum: int = 40) -> pd.DataFrame:
    """Reaction magnitude by what the filing actually reported.

    Split by direction, by whether the insider trades on a schedule, and by
    whether a plan was disclosed -- the three cuts the literature says should
    matter. Groups below `minimum` filings are dropped rather than shown: a rate
    computed on nine filings is noise wearing a percentage sign.
    """
    joined = events.set_index("event_id").join(
        labels.set_index("event_id")[["reaction"]], how="inner")
    joined["abs_reaction"] = joined["reaction"].abs()

    cuts = {
        "direction": joined["direction"],
        "behaviour": joined["behaviour"],
        "disclosed plan": np.where(joined["any_plan_10b5_1"], "under a plan",
                                   "not under a plan"),
        "role": np.where(joined["any_officer"], "officer",
                         np.where(joined["any_director"], "director", "other")),
    }
    rows = []
    for name, series in cuts.items():
        for value, group in joined.groupby(pd.Series(series, index=joined.index),
                                           sort=False):
            if len(group) < minimum:
                continue
            rows.append({
                "cut": name,
                "group": str(value),
                "filings": len(group),
                "median_abs_reaction": float(group["abs_reaction"].median()),
                "material_share": float(
                    (group["abs_reaction"] >= config.reaction_threshold).mean()),
                "median_value_usd": float(group["net_value"].abs().median()),
            })
    return pd.DataFrame(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=Path("data/build"))
    parser.add_argument("--out", type=Path, default=Path("evidence/real_run"))
    parser.add_argument("--universe", type=Path,
                        default=Path("data/build/universe_insiders.csv"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    config = PipelineConfig()

    transactions = pd.read_parquet(args.build / "insider_transactions.parquet")
    print(f"  {len(transactions):,} transactions")

    trades = open_market(transactions).copy()
    trades["behaviour"] = causal_routine(trades)
    trades["value"] = signed_value(trades)
    print(f"  {len(trades):,} open-market purchases and sales "
          f"({len(trades) / len(transactions):.1%} of rows)")

    events = to_events(transactions)
    print(f"  {len(events):,} filings with something decided in them")

    returns = to_returns(price_panel(events["ticker"].unique()))
    ladder_table, ladder_summary = ladder(events, returns, config)
    ladder_table.to_csv(args.out / "insider_disclosure_ladder.csv", index=False)

    on_time = events[events["disclosure_gap_days"] <= ON_TIME_DAYS]
    sensitivity, on_time_summary = ladder(on_time, returns, config)
    sensitivity.insert(0, "sample", f"filed within {ON_TIME_DAYS} days")
    sensitivity.to_csv(args.out / "insider_ladder_sensitivity.csv", index=False)
    ladder_summary["late_filings_excluded"] = len(events) - len(on_time)
    ladder_summary["on_time_inflation_in_material_share"] = on_time_summary[
        "inflation_in_material_share"]

    honest = anchored_events(events, "acceptance_time", TradingClock())
    labels = build_labels(honest, returns, config)
    reaction_by_kind(events, labels, config).to_csv(
        args.out / "insider_reaction_by_kind.csv", index=False)
    gap_profile(events).to_csv(args.out / "insider_gap_profile.csv", index=False)
    agreement = classification_agreement(trades)
    if not agreement.empty:
        agreement.to_csv(args.out / "insider_behaviour_agreement.csv", index=False)

    universe_meta = {}
    meta_path = args.universe.with_suffix(".meta.json")
    if meta_path.exists():
        universe_meta = json.loads(meta_path.read_text())

    buys = trades["transaction_code"].eq("P").sum()
    payload = {
        "schema_version": "insiders.v1",
        "exported_at": datetime.now(UTC).isoformat(),
        "source": "SEC Form 4 ownership filings",
        "sample": {
            "issuers": int(events["ticker"].nunique()),
            "transactions": len(transactions),
            "open_market_trades": len(trades),
            "purchases": int(buys),
            "sales": int(trades["transaction_code"].eq("S").sum()),
            "purchase_share": float(buys / len(trades)) if len(trades) else float("nan"),
            "filings_with_a_decision": len(events),
            "first_filing": str(pd.to_datetime(events["acceptance_time"]).min().date()),
            "last_filing": str(pd.to_datetime(events["acceptance_time"]).max().date()),
        },
        "behaviour_counts": events["behaviour"].value_counts().to_dict(),
        "disclosure_ladder": ladder_summary,
        "boundary": (
            "Reaction magnitude, never direction. Insider buying is the half of "
            "this literature with documented predictive power and it is "
            "directional; it is named here and not modelled."
        ),
        "survivorship": (
            "NOT controlled, and the bias favours insider buying: the universe is "
            "companies listed today, small companies fail often, and insiders who "
            "bought shortly before a collapse are the observations most likely to "
            "be missing."
        ),
        "universe": universe_meta,
        "inputs": {"transactions": frame_fingerprint(transactions)},
        "environment": environment(),
    }
    (args.out / "insider_metrics.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n")

    print(f"\ninsider evidence written to {args.out}")
    print(ladder_table.round(4).to_string(index=False))
    print(f"  purchases {buys:,} of {len(trades):,} open-market trades "
          f"({payload['sample']['purchase_share']:.1%})")
    print(f"  behaviour: {payload['behaviour_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
