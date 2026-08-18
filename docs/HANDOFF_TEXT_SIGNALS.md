# Handoff — Text Signals track

Written for an agent picking this up with no memory of the design conversation.
Read all of Part 1 before writing code; the constraints in Part 2 are the
output of a review that rejected several earlier proposals, and re-proposing
them wastes a cycle.

Repo state at handoff:

```
branch   feat/text-signals-spine
62966d7  refactor(inference): compute Newey-West on numpy, drop statsmodels
3757285  feat(text-signals): timestamp discipline, ingest provenance, HAC inference
8ce9a1f  (main) Merge pull request #30

working tree: 3 unrelated frontend files modified (globals.css,
              PublishedRunCard.tsx, SideNav.tsx) — not part of this track,
              leave them alone
env:          backend/.venv exists; statsmodels installed but NOT required
test:         cd backend && python3 -m pytest tests/test_text_signals_timestamps.py \
                tests/test_edgar_collector.py tests/test_factor_validation_inference.py -q
              expected: 81 passed
```

---

# Part 1 — What this track is

## 1.1 The repositioning

This repo used to present as "a quantitative research platform." On that
framing it competes with QuantConnect, Zipline, and ten thousand GitHub
backtesters, using free daily OHLCV and textbook signals (MA crossover,
12-1 momentum, low-vol) over a universe of 11–31 names. There is no available
win on that axis, and no amount of engineering changes that, because the
constraint is the data and the subject matter.

The track repositions on two moves:

1. **The signal channel becomes text, not price.** SEC filings, not moving
   averages.
2. **The target quantity becomes incremental information value, not excess
   return.**

## 1.2 The quantity being measured

```
raw return
  − benchmark return                             → excess return
  − exposure to known factors (mkt/size/mom/vol)  → residual return
  − trading cost                                  → net residual
  − everything predictable from price history alone
                                                  → INCREMENTAL SIGNAL VALUE
```

Formally: run a price-only baseline model, run price+text, and the
**incremental out-of-sample skill** — with a HAC significance test and both
trading *and* inference cost charged — is the quantity of interest.

This converts an unanswerable question ("does this beat the market?") into an
answerable one ("does this text channel add information over price?"), because
both arms span the same periods and bear the same trading assumptions, so cost
cancels in the contrast.

## 1.3 The three experiments

```
A  Does a documented filing-change effect still exist?   → the substrate
B  Is a more expensive extraction model worth its cost?  → the signature
C  Does preregistration reduce an AI's selective         → the headline
   reporting?
```

**A — Filing-change effect, modern sample.** *Lazy Prices* (Cohen, Malloy,
Nguyen, Journal of Finance 2020, NBER w25084): firms that change the language
of their 10-K/10-Q underperform firms that don't. Mechanism: filings are
copy-forward documents, so a change is costly and reluctant, and bad news gets
buried in legal filings rather than announced. Market is slow because nobody
diffs 200-page documents. Original sample ends 2014.

**B — Inference-cost frontier.** How much of A's signal does each extraction
tier capture, and at what cost? The interesting output is not "which tier
wins" but **the AUM above which an expensive tier pays for itself**, because
inference cost is fixed while capital is the denominator.

**C — Governed agent ablation.** Two arms of the same agent proposing
hypotheses over A/B's factor space. Arm 1 must preregister before the
deterministic engine runs. Arm 2 may see results before finalising claims —
i.e. how people actually use AI today. Score both on a held-out final period.
This is why the repo's existing governance layer exists: it finally has an
adversary. Published literature (arXiv 2509.08713) demonstrated that AI
research agents select on test data; the mitigations those papers recommend
are what this repo already implements.

---

# Part 2 — Hard constraints

These came out of a critical review. Each rejects an earlier proposal that was
wrong. Do not re-litigate them without new information.

### C1 — There is no free strict replication of 1995–2014

*Lazy Prices* used CRSP, Compustat and I/B/E/S, not only EDGAR. **Text is
free; survivorship-safe return replication is not.** The hard parts are
historical CIK↔PERMNO mapping, delisting returns, historical market caps and
the CRSP/Compustat link table.

- Without WRDS/CRSP: call it a **modern re-test**, never a replication
- Target the modern sample and state **survivorship bias as a core
  limitation**, not a footnote
- `docs/KNOWN_LIMITATIONS.md` already covers this (items 7–11) — link to it
  from any evidence package rather than restating

### C2 — Never claim LLMs caused any decay

Even if the effect weakens post-2023, confounds include: 2020 publication,
vendor productisation of filing-change signals, quant capital entry, regime
and macro shifts, and changes in disclosure practice.

- Correct framing: *"Did the filing-change effect persist after publication
  and during the LLM era?"*
- This is a structural-break / decay diagnosis, **not causal identification**

### C3 — Do not call it "alpha"

Alpha is the intercept of a portfolio return regressed on a stated risk model.
What this track measures is **Incremental Signal Value**. Portfolio alpha, if
wanted, is computed separately and afterwards.

Units must match before subtracting. Inference cost arrives in currency,
returns arrive in basis points:

```
Net economic value (bps)
  = gross excess return (bps)
  − trading cost (bps)
  − inference cost / capital × 10,000
```

Already implemented as `net_economic_value_bps()` and `breakeven_capital()`.
Report per-$1M-AUM-per-month so the number is legible.

### C4 — Experiment C arms must be matched

Same model, same prompt context, same hypothesis budget, same compute budget,
same seed, same factor space. **The only difference is preregistration and
test-set visibility.**

Metrics to report:

| Metric | Meaning |
|---|---|
| Claimed discovery rate | Share of hypotheses the agent asserted succeeded |
| Hidden-period survival rate | Share of claimed successes holding on the final hidden period |
| Selective-reporting rate | Share of runs executed but not disclosed |
| Test-peek violations | Times test evidence was touched before final validation |
| Protocol deviations | Changes to benchmark / metric / universe / holding period mid-run |

Do not pre-write example numbers into docs or prompts; it anchors the result.

### C5 — Scope is deliberately narrow

Phase A: **10-K only** (10-Q later), **one section** (Risk Factors or full
text, pick one and pre-register it), **TF-IDF cosine only**, **modern sample
only**. Phase B: three tiers only (TF-IDF, local embedding, small API LLM);
frontier model is an optional fourth *after* the first three run end to end.
Phase C: 10–20 hypothesis budget.

### C6 — Correctness gates replacing the lost replication window

C1 removed the built-in correctness check. Two replacements, neither needing
paid data. **Build these before trusting any result:**

1. **Planted-signal test** — inject an artificial signal of known strength
   into the pipeline and assert it is recovered at the right magnitude. Tests
   the pipeline, not the market. Belongs in CI.
2. **Text-side benchmark** — the paper reports distributional properties of
   filing similarity (mean levels, year-over-year trend). Checking against
   those needs **no return data at all**, so it validates the text pipeline
   before a single line of return code exists.

### C7 — Explicit non-goals

- ❌ No Coze / Dify / n8n. LangGraph is already the orchestrator; a third
  layer is tool-brand novelty with zero research content.
- ❌ No LLM stock-picking agent. Unfalsifiable and maximally crowded.
- ❌ No scraped-news sentiment. Timestamp integrity is unprovable — the exact
  failure mode EDGAR was chosen to avoid.
- ❌ Do not touch the legacy engine in `backend/app/main.py` in this track.
  It is a separate (real) problem: ~800 of its 914 lines are a second
  backtest engine duplicating the v1 research spine, with exactly one
  frontend consumer (`frontend/lib/api.ts`) and 8 of 69 test files. Worth
  deleting — later, not here.

---

# Part 3 — What already exists

Three modules, 81 tests, **no existing repo file modified**.

## 3.1 `backend/app/text_signals/timestamps.py`

The failure mode of nearly all text-alpha research is treating a document as
usable at a bar it could not have been acted on. This module makes the
instants explicit and separates the ones routinely conflated.

```
event_time                  when the underlying thing happened
publish_time                when the document became public
ingest_time                 when this pipeline actually received it
information_available_time   = max(publish_time + buffer, ingest_time)   [derived]
execution_time               = next session open at/after available      [derived]
```

Invariants the tests enforce — **do not weaken these**:

- **Derived instants cannot be supplied.** `information_available_time` and
  `execution_time` are `init=False`; passing them to the constructor is a
  `TypeError`. Populate via `TextRecord.resolve(calendar)`.
- **`ingest_time` participates.** A filing the pipeline had not yet received
  was not available to it, however public it was.
- **Calendars fail closed.** `WeekdayCalendar` is test-only
  (`approved_for_research=False`) and `resolve()` rejects it by default.
  `StaticHolidayCalendar` raises `CalendarCoverageError` outside its verified
  date range rather than extrapolating.
- **Availability ≠ execution.** `assert_no_lookahead()` tests availability
  against the *signal computation* instant. Equality is admissible — the
  information exists at that moment. Execution timing is a separate
  constraint carried by `execution_time`.

`IngestSource` is a **required field with no default** — every record declares
whether receipt was `OBSERVED` by a running collector or `SIMULATED` from
publish time plus an assumed polling interval. `assert_ingest_integrity()`
rejects any `OBSERVED` claim whose receipt time falls after the research
period, because such a record was necessarily backfilled. *A false OBSERVED is
worse than an honest SIMULATED: it invites more trust, not less.*

Reported metrics for evidence packages: `publish_to_execution_gap`,
`gap_summary()` (median / p95 / max, plus `ingest_bound_share` and
`simulated_ingest_share`).

## 3.2 `backend/app/text_signals/edgar_collector.py`

Two modes that must never be confused.

```python
collector.poll(since)                 # → OBSERVED. Run on a schedule from today.
collector.backfill(since, until)      # → SIMULATED. Assembles the historical study.
```

Network access is **injected** (`FilingFetcher = Callable[[datetime, datetime],
Iterable[RawFiling]]`), so both paths are tested against fixtures. `RawFiling`
documents why `acceptance_datetime` — not `filing_date` — is authoritative: a
submission accepted after 17:30 ET is *dated* the next business day while the
document became visible at acceptance. Using `filing_date` silently shifts a
document by up to a day.

`provenance_report()` gives the observed/simulated split. A fully simulated
study is not disqualified, it is *described* — the number belongs beside the
result.

## 3.3 `backend/app/factor_validation/inference.py`

The repo previously had **zero inferential statistics**: a mean RankIC of 0.03
could earn a `pass` whether it came from 600 periods or six.

- `newey_west_lag(n, holding_periods)` — bandwidth
  `max(floor(4·(n/100)^(2/9)), holding_periods − 1)`. The holding floor
  handles overlap the design *creates*: with h-period forward returns sampled
  every period, consecutive observations share h−1 periods by construction.
  **`holding_periods` must be pre-registered. Tuning the lag until t > 2 is
  p-hacking with extra steps.**
- `newey_west_mean_tstat(series, holding_periods=, lags=)` — pure numpy, no
  statsmodels. For a constant-only regression the HAC sandwich collapses to
  `Var(mean) = (1/n)·[γ(0) + 2·Σⱼ(1 − j/(L+1))·γ(j)]`. Verified identical to
  statsmodels HAC (`use_correction=False`) to 1.4e-14 across n ∈ {50, 137,
  400, 1000} and φ ∈ {0, 0.3, 0.7, −0.4}; the cross-check ships as a test
  guarded by `importorskip`.
- `incremental_signal_value(enriched, baseline, holding_periods=)` — the
  central statistic. *A positive mean with |t| < 2 is not a finding. It is a
  shrug.*
- `lag_sensitivity()` — shows bandwidth dependence. **Not for choosing a lag.**
- `net_economic_value_bps()`, `breakeven_capital()` — see C3.

Unavailable results carry an `unavailable_reason` and **never substitute
zero**, matching the repo's existing anti-fabrication contract (`502` "no
fabricated series", `503` "no fake answer").

---

# Part 4 — Phase A work

In order. Each step should land with tests.

### A1 — Real EDGAR fetcher

Implement `FilingFetcher` against SEC EDGAR. Requirements:

- Declared `User-Agent` header (`Name email`) or SEC refuses requests
- Respect SEC rate limits; cache by accession number so the corpus is
  genuinely reproducible (unlike yfinance prices, which are restated)
- Source `acceptance_datetime` from the submissions JSON or the filing
  header — **not** `filing_date`
- Keep it behind the existing injected-callable boundary so fixture tests
  still run offline

### A2 — Document retrieval and section extraction

10-K text, then one section. Item 1A (Risk Factors) is the recommended
pre-registered choice: long, discretionary, and rarely read closely. Handle
the messy reality of EDGAR HTML — the extractor needs its own tests with real
saved fixtures.

### A3 — Year-over-year similarity

TF-IDF cosine, **same company against its own prior filing**. Never
cross-company: different industries have different vocabulary, so a
cross-company cosine measures industry, not change.

### A4 — Wire into the existing validation spine

Feed the similarity signal through `factor_validation` so it produces the same
evidence-package shape as existing factors, now carrying `ic_tstat`,
`lag_rule`, `holding_periods`, cross-section width, and the gap/provenance
summaries.

### A5 — The two correctness gates from C6

Planted-signal recovery and the text-side distributional benchmark. **These
land before any result is trusted or published.**

### A6 — Start the live collector

A scheduled `poll()` writing `OBSERVED` records. Cheap, and its value grows
linearly with time: by the time Phase A finishes it will hold months of
genuinely observed receipt timestamps — a short but real sample that no amount
of backfilling can reconstruct.

---

# Part 5 — Open decisions

Not yet made. Pre-register each before running, don't decide them from results.

| Decision | Notes |
|---|---|
| Universe and size | Must clear a cross-section width gate; 31 names is too thin for quintiles (~6 per bucket) |
| Holding period | Sets the HAC lag floor. 1 / 5 / 21 days? |
| Section | Item 1A vs Item 7 vs full text — pick one |
| Backfill polling interval | Currently defaults to 15 min; it is a free parameter that moves results |
| `PASS_ELIGIBLE_WIDTH` | Proposed 20 — the cross-section width below which core checks return `inconclusive` rather than `pass` |
| Falsification criteria | Written before the run: e.g. "incremental t < 2, or net economic value ≤ 0 after inference cost → Fail" |

---

# Part 6 — Known environment quirks

- **Never run git through the Cowork device bridge.** The mount refuses
  `unlink`, so every git write leaves undeletable `.git/*.lock` files and
  `tmp_obj_*` objects. Symptom: `cannot lock ref 'HEAD'`. Recovery:
  `rm -f .git/HEAD.lock .git/index.lock .git/objects/maintenance.lock` and
  `find .git/objects -name "tmp_obj_*" -delete`. Run git in a normal terminal.
- **The shell is zsh.** An unmatched glob aborts the whole command (bash
  passes it through), and `#` is not a comment in interactive zsh. Write
  literal filenames or use `find`.
- **macOS duplicate files.** ~100 `xxx 2.py` / `page 2.tsx` copies were
  removed after verifying byte-identity with their originals. If they
  reappear, classify before deleting: identical → safe; **differing → the
  copy may hold unsaved work**; no original → probably a real filename.
- `backend/pytest.ini` references `statsmodels` in a warning filter, so pytest
  fails to start without it installed even though `inference.py` no longer
  needs it.

---

# Part 7 — The sentence this track exists to be able to say

> I re-tested a documented filing-change effect on a modern sample, priced the
> extraction of it across model tiers net of inference cost, and then measured
> whether preregistration stops an AI research agent from selectively
> reporting its own results.

If the honest verdict on any of the three is negative — **publish that one
first.** The verdict framework is this repo's only real differentiator, and
the only way to show it is not decorative is to let it publicly reject
something.
