# Filing Triage

**Which of today's SEC filings deserve a human read?**

Forty 8-Ks land before breakfast and an analyst has time for five. This ranks
them by how hard the market is about to react — *magnitude, not direction*.

Predicting direction is a bet against people with faster data, better models and
more capital. Predicting which disclosures matter is a triage problem, and triage
is answerable.

---

> [!IMPORTANT]
> **The figures below come from a synthetic corpus, not from SEC EDGAR.**
>
> They demonstrate the *mechanism* — that these four bugs inflate these metrics —
> and the size of each effect is a property of the simulator, not a measurement of
> the market. The simulator was built with the reaction landing on the first open
> after acceptance, so a pipeline that gets the timing right will of course find
> it; what that shows is that the plumbing works, not that the hypothesis holds.
>
> `make ingest` replaces every frame with real EDGAR filings and real prices, with
> no change to any pipeline code. Numbers from a real pull are the ones worth
> quoting. Until then, treat this page as a demonstration of method.

---

## The result

The first version of this pipeline reported an average precision of **0.391**.
The version that survives its own audit reports **0.274** — the first number was
a **43% overstatement**, and every point of the difference was a bug.

Nothing about the features or the model changed between them. The only thing that
changed was whether the pipeline was allowed to see things it could not have known.

| Stage | Avg precision | ROC AUC | Guards failing |
|---|---|---|---|
| Naive pipeline | 0.391 | 0.819 | 2 |
| + purged, embargoed CV | 0.355 | 0.800 | 2 |
| + trailing windows shifted | 0.286 | 0.775 | 2 |
| + point-in-time universe | 0.302 | 0.774 | 1 |
| + point-in-time entry | **0.274** | **0.758** | **0** |

The fourth row goes *up*, and that is not noise being reported as a finding:
restoring the issuers a present-day index screen had deleted changes the sample
the metric is computed on. A number produced by a pipeline with a bug in it is not
comparable to one produced without — which is a second, quieter way this class of
error hides.

**What the audited model is worth.** Reading the top 5 of each session's filings
surfaces material news at **2.0×** the rate of reading 5 at random (19.9% vs a
10% base rate). Useful. Not a trading strategy, and not claimed as one.

**How long it lasts.** Holding the model fixed and delaying the decision, average
precision goes 0.274 → 0.274 (30 min) → 0.261 (6 h) → 0.206 (1 day) → 0.106
(5 days). Whatever is being measured is mostly over within a session.

---

## What this is, and is not

**Is:** a point-in-time event dataset built from EDGAR acceptance timestamps, a
reusable leakage-audit library, and a ranker that triages a daily filing queue.

**Is not:** a return predictor. Direction is never modelled. No strategy return,
Sharpe ratio, or P&L appears anywhere in this repository, because a project that
claims to beat institutional desks on public filings is claiming something untrue.

---

## Quickstart

No API key, no vendor account, no network:

Python 3.11 or newer. On macOS check this first — the interpreter that ships
with the Xcode command line tools is 3.9, and a venv built from it inherits both
that and a pip too old to install this project at all:

```bash
python3 --version
```

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
make install
make demo                          # ~4 min -> data/build/report.html
```

`make install` upgrades pip before installing: pip older than 21.3 cannot do an
editable install of a pyproject-only project, and the failure it prints blames a
missing `setup.py`, which sends you looking for the wrong problem.

A virtualenv is not ceremony here: on macOS with Homebrew Python, a bare
`pip install` fails outright with `externally-managed-environment`. If you would
rather not use one, every target takes an explicit interpreter —
`make demo PYTHON=/path/to/python3`.

Every report says at the top which of the two it is; a synthetic run is labelled
as one, and cannot be mistaken for a real pull at a glance.

`make demo` generates a synthetic corpus with the properties the project is about
— filings on the real NYSE calendar, 80% of them outside market hours, an index
that gains and loses members — then runs the pipeline, the leakage study and the
embargo sweep, and writes a self-contained HTML report.

```bash
make quick           # smaller, no leakage study, ~30s
make test            # 99 tests
make audit           # the leakage checks as an exit code
```

### On real filings

The SEC requires an identifying User-Agent with a real name and email:

```bash
export EDGAR_USER_AGENT="Your Name you@example.com"
python3 scripts/build_universe.py --out data/build/sp500_membership.csv
make doctor
make ingest
make run
```

`make doctor` takes about five seconds. `make ingest` pulls the S&P 500 from
EDGAR and Stooq, rate-limited and cached, and takes roughly an hour.

Run `doctor` first. A full pull is tens of thousands of requests over an hour or
more, and finding out at minute fifty that the SEC rejected the User-Agent wastes
an afternoon and some of the SEC's patience. It checks the User-Agent, that the
SEC and the price source answer, and that the universe file actually contains
historical members — a membership file with zero of them is the survivorship trap
already sprung.

The ingest is cached per accession number and resumable: interrupt it and rerun,
and it picks up where it stopped. One issuer failing does not abort the run.

No pipeline code changes between the two paths — only where the frames come from.

---

## The four leaks

Every one of these produces a *better* number. That is what makes them dangerous:
the failure mode of leakage is not a crash, it is a result you are pleased with.
Full write-up in [docs/LEAKAGE.md](docs/LEAKAGE.md).

| # | The bug | How it is caught | What fixing it costs |
|---|---|---|---|
| 1 | `filing_date` (a date) used instead of `acceptanceDateTime` (the knowledge time). ~80% of 8-Ks arrive outside market hours, so the naive entry buys before the news exists. | `guards.causal` asserts the entry open postdates the acceptance time, on every row | Almost nothing in the metric — and **8,208 impossible entries** (75% of the sample), median **8.1 hours** of hindsight each |
| 2 | `.rolling(20)` without `.shift(1)`, so a filing's "trailing" volatility contains the event day. Sharpest as relative volume, which unshifted is the reaction's own volume spike. | No guard is possible — one switch, one comment, and a test asserting the leaky config scores *better* | The largest single effect: **−0.07 average precision** |
| 3 | Screening on today's index constituents, which deletes every issuer dropped after a collapse — the ones whose 8-Ks moved most. | `guards.universe_pit` checks membership *as of the event date*; membership stored as intervals, never a list | A few % of the sample, and a base rate that moves |
| 4 | `KFold(shuffle=True)` on time-ordered events: trains on the future, and overlapping outcome windows carry test-period returns into training labels. | `PurgedWalkForward` + `guards.purged_split` re-checking the gap every fold | **−0.04 average precision**, and a smaller sample |

There is a second trap inside bug 1. EDGAR serves acceptance times as
`2024-10-31T18:03:31.000Z` — but the clock is the SEC's, which runs on
America/New_York. Parsing that `Z` as UTC shifts every filing five hours earlier
and silently reclassifies the after-hours population as intraday.

### Guards that raise, not warn

A check that can be ignored is a comment. So:

- `LeakageAudit` raises `LeakageError`; it does not log.
- The audit runs on **every** pipeline execution, not in a notebook someone ran once.
- `python -m filing_triage.cli audit` is a CI job — a regression fails a build.
- The correct configuration is the **default**. A safe default you have to opt into
  is not a safe default.

---

## How it works

**Label.** Market-model event study. Regress the issuer on the market over
`[entry−140, entry−20]` sessions, measure abnormal return over `[entry, entry+1]`,
express it as `|CAR| / residual sd`. A filing is "worth reading" if that lands in
the top decile. The 20-session gap stops pre-announcement drift from contaminating
the baseline.

**Features.** Only what a reader had at `decision_time`: 8-K item codes; release
timing (pre / open / post / closed); text novelty against the issuer's own previous
filings; trailing volatility, relative volume and filing cadence through the
session *before* entry.

Novelty uses a `HashingVectorizer` rather than TF-IDF, and that is a leakage
decision rather than a performance one — TF-IDF must be fitted, and a vectorizer
fitted over the whole corpus carries document frequencies from filings that had
not been written yet. Hashing is stateless.

**Validation.** Purged, embargoed walk-forward. Metrics are ranking metrics:
average precision leads, with mean daily precision@5 as the product metric.
Accuracy would be meaningless — "nothing is material" scores 90%.

Details in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## Layout

```
src/filing_triage/
  pit.py           rule-generated NYSE calendar; acceptance time -> tradable session
  guards.py        the leakage checks, and purged/embargoed walk-forward CV
  config.py        one config, four correctness switches
  ingest/          EDGAR client, Stooq prices, interval-based index membership
  features.py      features, each computable at decision time
  labels.py        market-model event study on a numpy session grid
  model.py         the ranker
  evaluate.py      ranking metrics
  experiments.py   the leakage study and the embargo sweep
  report.py        self-contained HTML
  synth.py         the offline corpus
tests/             99 tests; test_guards, test_pipeline and
                   test_ingest_integration are the ones that matter
docs/              METHODOLOGY.md, LEAKAGE.md
```

About 2,750 lines under `src/`, plus 430 of tests. It is meant to be read end to end.

---

## Caveats

- Daily bars. The entry rule — first *open* at or after the decision time — is the
  most conservative convention available at that resolution. Intraday data would
  allow a tighter measurement.
- Vendor-adjusted prices are not literally what a trader saw. Multiplicative and
  applied to both the issuer and its benchmark, so it does not bias the study, but
  it is a compromise worth naming.
- Figures on this page come from the synthetic corpus, so that the repository runs
  end to end with no credentials — see the note at the top. They are illustrative
  of the *mechanism*; run `make ingest` for numbers about the actual market.
- The real-data path runs end to end in the test suite with the network faked
  (`tests/test_ingest_integration.py`): EDGAR-shaped payloads through the
  per-issuer loop, the parquet round trip, and into the pipeline. Only the
  transport itself — rate limiting, backoff, resumability — has not been
  exercised against the live SEC.

## License

MIT — see [LICENSE](LICENSE).
