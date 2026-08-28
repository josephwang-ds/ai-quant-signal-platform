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

**63.2%** of 8-Ks in the real sample are accepted outside regular market hours.
For those, treating `filing_date` as tradable at that day's open buys the
position hours before the information existed. (The synthetic corpus is
generated at 80%, deliberately harsher than reality; the two figures are
sometimes confused because an earlier version of this page quoted the generator's
setting as though it were a measurement.)

Under the naive rule the real sample carries **11,224 impossible entries**, 95.8%
of measurable filings, at a median of 10.6 hours of hindsight. That is larger
than the after-hours share because it also catches intraday filings: the opening
print still predates a document accepted at 10 a.m. The corrected rule reduces
the count to zero, and that zero — not a metric movement — is the auditable
result.

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

**Where this project does and does not control it.** On the synthetic corpus,
fully: membership is generated with issuers that join and leave, the guard has
something to catch, and the cost of the bug is measured. On the real-data demo,
**not at all**. That path draws its universe from a hand-picked list of large caps
that still exist today, because the point-in-time source it used to reconstruct
S&P 500 membership — Wikipedia's dated additions-and-removals table — moved off
the page, and scraping a live page for a load-bearing input had already caused
three separate failures.

So the demo's universe is a survivor sample and the guard passes trivially. That
is worth stating plainly, because everything else on that page is real and a
reader would reasonably assume this was too. The universe file records the
limitation in a sidecar, the ingest carries it into the run's provenance, and the
report puts it in the banner. Restoring it needs a stable point-in-time
membership source; `build_universe.py`, which reconstructs one from a dated
changes table, stays in the repository for when there is one to point it at.

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

## The one that looks like a fifth leak, and is not

Everything above is a bug. This one is a measurement decision that wears a bug's
clothes, and it is on this page because a reader who has understood the four
above will find it and ask.

**The observation.** The label is a market-model event study measured
close-to-close, so the entry session's return is anchored at the *previous*
close. For the 63.2% of filings accepted outside market hours, that price was
printed before the filing existed. The measured reaction therefore contains the
overnight gap in which the news was priced, while `pit_entry` maintains that
entry happens at the open.

**No guard catches it, and cannot.** `guards.causal` asserts
`acceptance_time <= entry_open` and passes on every row — precisely because the
label never touches `entry_open`. The check is looking at the entry rule; the
staleness is in the outcome window. A guard cannot notice a quantity it was not
pointed at.

**Why it is not a bug anyway.** The label answers *was this filing material*, and
the standard event-study convention answers that close-to-close. The overnight
gap is part of the reaction, not contamination of it. Switching to an open
anchor does not remove hindsight; it changes the question to *how much of the
reaction was still on the table at the open*, which is different and harder. So
`open_anchored_returns` exists, is **off by default**, does not participate in
`is_honest`, and is not a rung on the ladder.

**What it is worth, measured rather than asserted.** `experiments.anchoring_study`
scores the same pipeline both ways and `reaction_capture_profile` takes the ratio
filing by filing:

| Filings | Median share of the reaction already in the opening print |
|---|---|
| all | 6.4% |
| not material | 3.1% |
| **material (≥ 2.0σ)** | **27.7%** |
| material, accepted after the close | **45.7%** |

Across all 8-Ks the gap barely matters, because most filings move nothing and a
ratio of two small numbers is noise. Restrict to the ones that cleared the
materiality cutoff and it jumps; restrict to those accepted after the close and
nearly half the move is gone before the bell — concentrated exactly where the
ranker is trying to look. Scored against an open-anchored label the pipeline
falls from 0.397 average precision to 0.155. That is the question getting harder,
not the ranker failing, and the two rows are only meaningful read together.

This is why "useful triage, not a trading strategy" is a number in this
repository rather than a disclaimer.

**The fifth leak no guard can see.** There is one more, and it has no measurement
at the row level because it does not live in a row: choosing the estimator's
constants by watching the out-of-sample metric would contaminate the whole
project, and every individual run would still be clean. The contamination lives
in *which run was kept*. The answer is a spread rather than a promise —
`experiments.hyperparameter_sensitivity` perturbs each setting in turn and moves
average precision across a range of 0.008, narrower than the 0.064 bootstrap
interval on the default configuration, and the defaults are not the best cell in
the grid.

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
