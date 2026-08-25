# Company Lens / Filing Triage

> The repository is being expanded into **Company Lens**: a source-backed company
> overview for ordinary investors. The original Filing Triage pipeline remains the
> point-in-time event and data-quality foundation; it is not being replaced by a
> generic research agent. See [the frozen portfolio scope](docs/SCOPE.md),
> [product definition](docs/PRODUCT.md), [architecture](docs/ARCHITECTURE.md), and
> [roadmap](docs/ROADMAP.md), [grounded LLM strategy](docs/LLM.md), and
> [deployment guide](docs/DEPLOYMENT.md).

Live Company Lens: <https://company-lens-demo.vercel.app>

The first vertical slice is runnable against the existing local real-data build:

```bash
make company        # -> one AAPL JSON snapshot + self-contained HTML page
make company-featured # -> quick AAPL/MSFT/NVDA showcase build
make company-pages  # -> all 193 locally available company pages + index
make refresh-filings # -> check SEC heads, append unseen 8-Ks, rebuild pages
make refresh-all    # -> locked SEC + market refresh for scheduled operation
make vercel-bundle  # -> public 41.6 MB HTML-only prebuilt frontend
make vercel-deploy  # -> publish that bundle to Vercel production
make nlp-eval       # -> labeled prior-filing change-detection metrics
```

It produces a versioned company snapshot containing a growth-of-$10,000 series,
same-period SPY comparison, return, CAGR, volatility, beta, correlation, drawdown,
worst day, a bounded business profile, latest 8-Ks, SEC source links, deterministic
passage ranking, causal novelty, prior-comparable-filing changes, typed cited entities
with source spans, retrospective benchmark-adjusted filing reactions compared only
with earlier issuer filings, and a no-LLM explanation fallback. An optional local
JSON/CSV headline index can add an Evidence Scope section with at most three
source-linked company or market headlines; normal builds use the honest
not-configured state and make no live-news request. Opt-in grounded retrieval runs
persist their documents, selected chunks, safe reader rules, and run provenance to
local versioned JSON by default; no database is required. A backend worker can
explicitly select the optional PostgREST adapter without changing the snapshot:

```bash
company-lens AAPL --llm --storage-backend local
company-lens AAPL --llm --storage-backend dual  # requires backend-only Supabase env vars
```

Use `SUPABASE_SECRET_KEY` for the current `sb_secret_...` backend key;
`SUPABASE_SERVICE_ROLE_KEY` remains a legacy JWT fallback. Neither may enter
frontend/browser configuration or a public build, and publishable keys are rejected.
The versioned migration and current Secret-key path have completed a controlled live
PostgREST write/read/cleanup smoke test. The repository still defaults to local storage
and contains no Supabase project identifier or credential.
The entry searches all 193 companies in the current local evidence universe while
keeping AAPL/MSFT/NVDA as featured examples. It states when a company is genuinely
outside that universe. It makes no forecast or recommendation.

---

## Filing Triage foundation

**Which of today's SEC filings deserve a human read?**

At each market open, an analyst faces the 8-Ks accepted since the prior queue and
has time for five. This ranks them by the magnitude of the abnormal reaction after
that decision point — *magnitude, not direction*.

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
> The small committed package in [`evidence/real_run`](evidence/real_run) contains
> the metrics, fold results, OOS importance, audit, leakage ladder, and provenance
> behind the claims below; it contains no raw filing text or price history.

---

## The result

A pipeline written the obvious way reports an **average precision of 0.603** and
**ROC AUC of 0.842** on real SEC filings. The version that survives its own audit
reports **0.366** and **0.740** respectively.

That gap is not model improvement. It is four common pipeline bugs, none of which
announced itself — every one produced a result the author would have preferred.

| Stage | Avg precision | ROC AUC | Guards failing |
|---|---|---|---|
| Naive pipeline | **0.603** | **0.842** | 1 |
| + purged, embargoed CV | 0.596 | 0.839 | 1 |
| + trailing windows shifted | 0.425 | 0.774 | 1 |
| + point-in-time universe | 0.425 | 0.774 | 1 |
| + point-in-time entry | **0.366** | **0.740** | **0** |

Two rows deserve their explanation up front, because both look wrong.

**The universe row does not move at all** — 0.425033 before and after, to six
decimals. That is the survivor sample confessing: when every issuer in the file
still exists, switching on a point-in-time membership filter has nothing to
remove. The pipeline is reporting its own blind spot rather than hiding it.

**The entry row also changes the measured population.** The filing-date rule uses
that date's opening print even when acceptance came hours later. In this sample it
creates 11,168 impossible entries—95.4% of measurable filings—with a median 10.6
hours of hindsight. The corrected rule places every filing in the first market-open
queue after its acceptance time and reduces that count to zero. Because it also
changes the outcome window and class balance, its metric movement is not a clean
estimate of one leak's cost; the zero impossible-entry count is the invariant.

The real sample has 63.5% of acceptances outside regular market hours. The larger
95.4% impossible-entry share under the naive rule also includes intraday filings:
that day's opening print still predates a filing accepted at 10 a.m.

**What the audited model is worth.** Filings arrive at a median of 9 a session.
Reading the model's top five surfaces material post-queue reactions at **18.6%**
precision over the 769 sessions crowded enough for ranking to matter. On those
same sessions, expected random selection scores **11.7%**, arrival order **9.4%**,
and a simple “Item 2.02 earnings first” rule **13.6%**. The model is therefore
1.59×, 1.98×, and 1.38× better respectively. Useful triage, not a trading strategy.

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
make test            # 217 tests
make audit           # the leakage checks as an exit code
make llm-eval        # frozen English/Chinese grounded-output scorecard
make llm-eval-openai-dry-run  # inspect 20-case paid benchmark scope; sends nothing
```

### On real filings

The SEC requires an identifying User-Agent with a real name and email:

```bash
export EDGAR_USER_AGENT="Your Name you@example.com"
make universe
make doctor
make ingest
make run
make refresh-filings
```

`make universe` resolves the 200 tickers in `data/sample/demo_tickers.txt` to CIKs
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
Submission heads are refreshed on a six-hour TTL; historical shards and accession
documents remain immutable caches. `make refresh-filings` performs a forced incremental
check, appends only unseen accessions, records the SEC check time, and rebuilds the
static Company Lens pages.

No pipeline code changes between the two paths — only where the frames come from.

---

## The four leaks

Every one of these produces a *better* number. That is what makes them dangerous:
the failure mode of leakage is not a crash, it is a result you are pleased with.
Full write-up in [docs/LEAKAGE.md](docs/LEAKAGE.md).

| # | The bug | How it is caught | What fixing it costs |
|---|---|---|---|
| 1 | `filing_date` (a date) used instead of the accepted timestamp, so the naive entry uses an opening print before the filing was accepted. | `guards.causal` asserts the entry open postdates the acceptance time, on every row | 11,168 impossible entries (95.4%) reduced to zero |
| 2 | `.rolling(20)` without `.shift(1)`, so a filing's "trailing" volatility contains the event day. Sharpest as relative volume, which unshifted is the reaction's own volume spike. | No guard is possible — one switch, one comment, and a test asserting the leaky config scores *better* | Average precision **0.596 → 0.425**, a 29% reduction |
| 3 | Screening on today's index constituents, which deletes every issuer dropped after a collapse — the ones whose 8-Ks moved most. | `guards.universe_pit` checks membership *as of the event date*; membership stored as intervals, never a list | Nothing on this universe, and that is the finding — see above |
| 4 | `KFold(shuffle=True)` on time-ordered events: trains on the future, and overlapping outcome windows carry test-period returns into training labels. | `PurgedWalkForward` + `guards.purged_split` re-checking the gap every fold | **0.603 → 0.596** average precision, and a smaller sample |

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
`[entry−139, entry−20]` sessions, measure abnormal return over `[entry, entry+1]`,
and express it as `|CAR| / residual sd`. A filing is labelled material when the
absolute reaction is at least **2.0 issuer-specific residual standard deviations**,
a cutoff fixed before the sample is observed. The 20-session gap stops
pre-announcement drift from contaminating the baseline.

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
Accuracy would be meaningless for a rare outcome. Daily lift uses the expected
random result on the same eligible sessions and is shown beside arrival order and
an Item 2.02-first heuristic.

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
src/company_lens/
  contracts.py     versioned company, filing, and citation read models
  performance/     historical return, benchmark, drawdown, beta, correlation
  filings/         causal novelty, item taxonomy, passage and number extraction
  llm/             evidence packets, provider adapter, guards, cache and fallback
  snapshots/       one cacheable company-page payload
  cli.py            no-network snapshot entry point
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
tests/             217 tests; test_guards, test_pipeline and
                   test_ingest_integration are the ones that matter
docs/              METHODOLOGY.md, LEAKAGE.md
```

About 8,756 lines under `src/`, plus 3,578 of tests. It is meant to be read
end to end, and a test asserts these figures have not drifted from the code.

---

## Caveats

- Daily bars. The entry rule — first *open* at or after the decision time — is the
  most conservative convention available at that resolution. Intraday data would
  allow a tighter measurement.
- Vendor-adjusted prices are not literally what a trader saw. Multiplicative and
  applied to both the issuer and its benchmark, so it does not bias the study, but
  it is a compromise worth naming.
- Headline figures on this README come from the real-data provenance described at
  the top. `make demo` produces a separately and visibly labelled synthetic report
  so the leakage mechanisms remain reproducible without credentials.
- EDGAR's accepted timestamp is the official knowledge-time field available here;
  it is not a measured timestamp of first public dissemination. The project uses it
  conservatively and does not claim sub-minute tradability.
- The real-data path runs end to end in the test suite with the network faked
  (`tests/test_ingest_integration.py`): EDGAR-shaped payloads through the
  per-issuer loop, the parquet round trip, and into the pipeline. Only the
  transport itself — rate limiting, backoff, resumability — has not been
  exercised against the live SEC.

## License

MIT — see [LICENSE](LICENSE).
