# Filing Triage

**Which of today's SEC filings deserve a human read?**

Forty 8-Ks land before breakfast and an analyst has time for five. This ranks
them by how hard the market is about to react — *magnitude, not direction*.

Predicting direction is a bet against people with faster data, better models and
more capital. Predicting which disclosures matter is a triage problem, and triage
is answerable.

---

> [!NOTE]
> **The figures below come from a real EDGAR pull**: 11,702 8-K filings from 193
> issuers, 2022 to 2026, with prices from yfinance. Reproduce them with
> `make universe && make ingest && make run` (about 40 minutes).
>
> Two caveats the page states in its own banner, because everything else on it is
> real and these are exactly the ones a reader would assume away. **The universe
> is a survivor sample** — 200 hand-picked large caps that still exist — so
> survivorship bias is *not* controlled on this path; leak 3 is measured on the
> synthetic corpus instead. And the demo run uses a fixed ticker list rather than
> point-in-time index membership, for reasons in [docs/LEAKAGE.md](docs/LEAKAGE.md).

---

## The result

A pipeline written the obvious way reports an **ROC AUC of 0.888** on real SEC
filings. The version that survives its own audit reports **0.768**.

An AUC near 0.9 on public disclosures would be a remarkable finding. It is
instead four bugs, and none of them announced itself — every one produced a
*better* number.

| Stage | Avg precision | ROC AUC | Guards failing |
|---|---|---|---|
| Naive pipeline | 0.518 | **0.888** | 1 |
| + purged, embargoed CV | 0.482 | 0.871 | 1 |
| + trailing windows shifted | 0.263 | 0.791 | 1 |
| + point-in-time universe | 0.263 | 0.791 | 1 |
| + point-in-time entry | 0.345 | **0.768** | **0** |

Two rows deserve their explanation up front, because both look wrong.

**The universe row does not move at all** — 0.262916 before and after, to six
decimals. That is the survivor sample confessing: when every issuer in the file
still exists, switching on a point-in-time membership filter has nothing to
remove. The pipeline is reporting its own blind spot rather than hiding it.

**The entry row moves *up*.** Correcting the entry also corrects the window the
outcome is measured over: with the filing date, a filing accepted after the close
is scored across a session that had not yet heard the news, so the label carries a
day of pure noise. Fixing it sharpens the label as well as removing the impossible
trade. That stage's honest result is not its effect on the score at all — it is
this:

| | Naive entry | Point-in-time entry |
|---|---|---|
| Entries priced before the filing was public | **11,168 of 11,681 (95.6%)** | **0** |
| Median hindsight granted | **10.6 hours** | — |

Only the small pre-market minority of 8-Ks is genuinely tradable at its own
filing date's open. Everything filed during the session or after the close was
being entered at a print that had already happened, by a median of ten and a half
hours. No metric would have told you: the score barely moves.

**What the audited model is worth.** Filings arrive at a median of 9 a session.
Reading the top 5 of each surfaces material news at **1.56×** the rate of reading
5 at random (15.6% against a 10% base rate), measured over the 769 sessions
crowded enough for a ranking to mean anything. Useful. Not a trading strategy, and
not claimed as one.

**How long it lasts.** Holding the model fixed and delaying the decision, the
ranking decays within a session. Whatever is being measured is mostly over by the
next open.

**Where the other filings went.** 11,702 were ingested and 9,729 were scored. The
gap is itemised rather than left as arithmetic for the reader, because an
unexplained drop is indistinguishable from a bug:

| | Filings |
|---|---|
| Scored out of sample | 9,729 |
| Held out by walk-forward as training-only | 1,945 |
| Event window ran past the end of the price data | 15 |
| Missing price bars inside the event window | 7 |
| Entry session had no price bar | 6 |

The large line is the honest cost of the split. Walk-forward tests folds 1..n, so
the earliest block is only ever training data and never receives an out-of-sample
score. Shuffled K-fold scores all 11,681 — by training on the future to do it. A
test asserts this ledger balances.

---

## What this is, and is not

**Is:** a point-in-time event dataset built from EDGAR acceptance timestamps, a
reusable leakage-audit library that fails the build rather than logging, and a
ranker that triages a daily filing queue.

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

Every `make` target picks up `.venv/bin/python` on its own if the virtualenv is
there, so a shell that forgot to activate still runs the right interpreter rather
than failing with a version error about a system Python nobody meant to use.

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
make test            # 123 tests
make audit           # the leakage checks as an exit code
```

### On real filings

The SEC requires an identifying User-Agent with a real name and email:

```bash
export EDGAR_USER_AGENT="Your Name you@example.com"
make universe
make doctor
make ingest
make run
```

`make universe` resolves the 40 tickers in `data/sample/demo_tickers.txt` to CIKs
through the SEC's own mapping. `make doctor` takes about five seconds. `make
ingest` pulls those issuers' 8-Ks from EDGAR and their prices from yfinance,
rate-limited and cached, in a few minutes.

**The demo universe is a survivor sample, and survivorship is not controlled on
this path.** It is a hand-picked list of issuers that still exist, so the
companies whose disclosures preceded a collapse are absent by construction. The
universe file records this in a sidecar, the ingest carries it into the run's
provenance, and the report says so in its banner — because everything else on
that page is real, which makes this exactly the caveat a reader would assume
away. Leak 3 is measured on the synthetic corpus, where membership is generated
with issuers that join and leave. `scripts/build_universe.py` reconstructs true
point-in-time S&P 500 membership from a dated changes table and stays in the
repository for when there is a stable source to point it at — Wikipedia's moved
off the page, and scraping a live page for a load-bearing input is what caused
three separate failures before this.

Prices come from yfinance with Stooq as a fallback. Free price data has no
service level — Stooq was the original single choice and started answering 404
for symbols it serves fine in a browser — so the layer tries sources in order and
reports which one answered.

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
| 1 | `filing_date` (a date) used instead of `acceptanceDateTime` (the knowledge time). ~80% of 8-Ks arrive outside market hours, so the naive entry buys before the news exists. | `guards.causal` asserts the entry open postdates the acceptance time, on every row | Nothing you would notice in the metric — and **11,168 of 11,681 entries (95.6%)** priced before their filing was public, median **10.6 h** of hindsight, reduced to zero |
| 2 | `.rolling(20)` without `.shift(1)`, so a filing's "trailing" volatility contains the event day. Sharpest as relative volume, which unshifted is the reaction's own volume spike. | No guard is possible — one switch, one comment, and a test asserting the leaky config scores *better* | The largest single effect by far: average precision **0.482 → 0.263**, a 46% overstatement |
| 3 | Screening on today's index constituents, which deletes every issuer dropped after a collapse — the ones whose 8-Ks moved most. | `guards.universe_pit` checks membership *as of the event date*; membership stored as intervals, never a list | Nothing on this universe, and that is the finding — see above |
| 4 | `KFold(shuffle=True)` on time-ordered events: trains on the future, and overlapping outcome windows carry test-period returns into training labels. | `PurgedWalkForward` + `guards.purged_split` re-checking the gap every fold | **0.518 → 0.482** average precision, and a smaller sample |

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

## The published site

`web/` is a static site published to GitHub Pages with no build step — what is
committed is what goes live, so there is nothing that can fail to build.

| | |
|---|---|
| `web/showcase.html` | the full write-up: story, method, findings, diagrams |
| `web/index.html` | a short landing page |
| `web/report.html` | the generated report from a run |

`showcase.html` is one self-contained file with no external requests, so it also
embeds directly into Streamlit or a personal site — see
[web/EMBEDDING.md](web/EMBEDDING.md).

```bash
make run     # or make demo
make site    # copies data/build/report.html -> web/report.html
```

Then commit `web/report.html`. Reports carry their own provenance banner, so a
synthetic run published by accident says so on its own face rather than passing
as a real one.

Enable it once under **Settings → Pages → Source: GitHub Actions**. The workflow
runs on any push to `main` that touches `web/`.

## Layout

```
src/filing_triage/
  pit.py           rule-generated NYSE calendar; acceptance time -> tradable session
  guards.py        the leakage checks, and purged/embargoed walk-forward CV
  config.py        one config, four correctness switches
  ingest/          EDGAR client, multi-source prices, interval-based membership
  features.py      features, each computable at decision time
  labels.py        market-model event study on a numpy session grid
  model.py         the ranker
  evaluate.py      ranking metrics
  experiments.py   the leakage study and the embargo sweep
  report.py        self-contained HTML
  synth.py         the offline corpus
tests/             123 tests; test_guards, test_pipeline and
                   test_ingest_integration are the ones that matter
docs/              METHODOLOGY.md, LEAKAGE.md
```

About 3,287 lines under `src/`, plus 1,184 of tests. It is meant to be read
end to end, and a test asserts these figures have not drifted from the code.

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
