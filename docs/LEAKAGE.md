# Four ways to see the future

Every bug below produces a better number. That is what makes them dangerous: the
failure mode of leakage is not a crash or a warning, it is a result you are
pleased with. None of these were hypothetical — each one was in this pipeline at
some point, and the guard exists because it caught it.

The measured cost of each is in the report (`make demo`) and in
`data/build/leakage_study.csv`.

---

## 1. The timestamp that lies

**The bug.** EDGAR gives you three dates and only one of them is a knowledge time.

| Field | What it is | Safe to key off? |
|---|---|---|
| `period_of_report` | the fiscal period the filing describes | No — months early |
| `filing_date` | the calendar date EDGAR stamped | No — a *date*, no time |
| `acceptanceDateTime` | when EDGAR accepted the submission | **Yes** |

About four out of five 8-Ks are accepted outside market hours. For those, treating
`filing_date` as tradable at that day's open buys the position several hours
before the information existed.

There is a second trap inside the right field. `acceptanceDateTime` is served as
`2024-10-31T18:03:31.000Z` — but the clock is the SEC's, which runs on
America/New_York. Parsing that `Z` as UTC shifts every filing four or five hours
earlier and quietly reclassifies the after-hours population as intraday.

**The guard.** `TradingClock.entry_session` returns the first session whose *open*
is at or after the decision time, and `guards.causal` asserts on every row that
the entry open postdates the acceptance time. `pit.ACCEPTANCE_TZ` names the
timezone assumption instead of burying it in a parse call.

**What it costs to fix.** Almost nothing in the ranking metric — which is the
point. It is not a modelling error, it is a claim to have traded on unpublished
news, and no score will tell you about it. The report counts the impossible
entries directly.

---

## 2. The window that swallows its own event

**The bug.** A trailing statistic computed with `.rolling(n)` and no `.shift(1)`
includes the current row. Joined at the entry session, the "trailing" volatility
of a filing that moved the stock 8% contains that 8% day.

The sharpest case is relative volume — `volume / median_volume_60`. Unshifted, on
the entry session, that is the reaction's own volume spike divided by its
baseline. It is the label with a moustache on. It is also a completely ordinary
feature to want, which is why the bug ships.

Window length decides whether it matters. A 60-session window barely notices one
extra day; a 5-session window is dominated by it.

**The guard.** None, structurally — a rolling window that includes the event day
is indistinguishable from one that does not by inspecting the data. This one is
caught by `PipelineConfig.shift_trailing_features` being a single switch that
every trailing statistic reads, by a code comment where it is read, and by a test
asserting the leaky configuration scores *better*.

**What it costs to fix.** The largest single effect measured here: average
precision falls by roughly 40%. ROC AUC moves about 0.04 — which is why AUC is
not the headline metric on this page.

---

## 3. The index that only contains survivors

**The bug.** Screening on today's S&P 500 constituents deletes every company that
was dropped after a collapse, an acquisition or a delisting. Those are exactly
the issuers whose 8-Ks moved most. A model trained on the survivors learns that
disclosures rarely matter.

**The guard.** Membership is stored as intervals — `ticker, start_date, end_date`
— never as a list, and `guards.universe_pit` asserts that every event's issuer
was in the index *on the event date*. `scripts/build_universe.py` builds the file
from the dated additions-and-removals table, and the file is deliberately not
committed: a membership file generated today is a fact about today, and a stale
one checked into git is this bug wearing a helpful face.

**What it costs to fix.** A few percent of the sample, and a base rate that moves.
The metrics before and after are not comparable, because the bug selected the
sample they were computed on — which is a second, quieter way this one hides.

---

## 4. The split that trains on the future

**The bug.** `KFold(shuffle=True)` on time-ordered events trains on the future.
Worse, because each label spans a multi-day outcome window, a training event whose
window overlaps the test period carries the test period's returns inside its own
label. Shuffling is the obvious default and it is wrong twice over.

**The guard.** `PurgedWalkForward`. Folds run forward in time; a training event
survives only if its entire outcome window closed before the test fold opened,
plus an embargo on top for serial correlation across the boundary.
`guards.purged_split` re-checks the gap on every fold at runtime.

**What it costs to fix.** Average precision falls, and the sample shrinks —
purging discards events it cannot honestly train on. A walk-forward split also
tells you something a shuffled one cannot: whether the ranking still works in the
*latest* fold, or has decayed.

---

## The general shape

Three of the four bugs are invisible in the code and visible only in the metric.
The fourth is invisible in the metric and visible only in the data. That
asymmetry is the argument for checking mechanically rather than carefully:

- a check that can be ignored is a comment, so `LeakageAudit` raises;
- the audit runs on every pipeline execution, not in a notebook someone ran once;
- `python -m filing_triage.cli audit` is a CI job, so a regression fails a build
  rather than a quarterly review;
- the correct configuration is the *default*, because a safe default you have to
  opt into is not a safe default.
