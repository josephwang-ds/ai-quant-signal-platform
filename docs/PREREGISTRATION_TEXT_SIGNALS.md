# Pre-registration — Text Signals, Experiment A

Decisions recorded **before** the corresponding evidence exists. The point of
writing them down is that a choice made after seeing a result is not a design
decision, it is a selection — and Experiment C exists to measure exactly that
failure in an AI agent, so the human track cannot commit it first.

Status: A1 (EDGAR fetcher), A2 (document retrieval, Item 1A extraction) and A3
(year-over-year TF-IDF cosine) implemented. **No return has been measured**, so
no similarity has been compared against an outcome. Nothing below was chosen
from a result, because there are no results yet.

Any row changed later must be changed *here first*, with a dated reason.

---

## Decided

### D1 — Section: Item 1A (Risk Factors)

Alternatives were Item 7 (MD&A) and full document text.

Item 1A is the pre-registered choice for three reasons: it is long enough for
cosine similarity to be stable, it is highly discretionary (management chooses
what to disclose and how to word it, so a change is a decision rather than a
mechanical restatement), and it is copy-forward by convention — which is what
makes a *change* informative in the first place.

Full text was rejected because it is dominated by financial statements whose
year-over-year wording changes mechanically with the numbers, which would swamp
the discretionary signal. Item 7 remains a reasonable secondary section but is
explicitly **not** part of the first pass; adding it later would be a second
hypothesis and must be declared as one.

*Constraint reference: C5 (scope is deliberately narrow — one section).*

### D2 — Similarity: TF-IDF cosine, same company against its own prior filing

Never cross-company. Different industries use different vocabulary, so a
cross-company cosine measures industry membership, not textual change.

*Constraint reference: C5, and A3 in the handoff.*

### D3 — Document timestamp: `acceptanceDateTime`, read as UTC

Not `filingDate`. A submission accepted after 17:30 ET is *dated* the next
business day, so `filingDate` can be a full day later than the moment the
document became public.

The UTC reading was established empirically rather than assumed — the natural
guess (Eastern, since EDGAR is an ET system) is wrong and would shift every
document four to five hours. Evidence: predicting SEC's own published filing
dates from acceptance under both readings, on forms where the 17:30 cutoff
applies strictly, the UTC reading scores 21/21 (Apple) and 18/18 (Microsoft)
against 14/21 and 1/18 for Eastern. Enforced by
`tests/test_edgar_fetcher.py::TestAcceptanceIsUtcNotEastern`.

### D4 — Section-extraction failure is reported, never filled in

When Item 1A cannot be located, or the widest candidate span falls below
`MIN_SECTION_CHARS` (500), extraction returns `text=None` with an
`unavailable_reason`. It never falls back to the whole document, and a
"Not applicable" stub is treated as absent rather than as an empty section.

This matters beyond tidiness: a silently-empty section would compute as a total
year-over-year rewrite — the maximum possible signal — from a filing that
actually said nothing.

### D5 — Tokenization: alphabetic tokens only, minimum length 2

Pattern: `(?u)\b[A-Za-z][A-Za-z]+\b`, lowercased.

Pure numbers are excluded deliberately. Dollar amounts, dates and share counts
change every single year for reasons that have nothing to do with a firm
revising what it discloses; counting them as textual change would manufacture
signal mechanically, and would do so *most* strongly for the firms whose
financials moved most — precisely the wrong correlation to introduce into a
return study.

### D6 — IDF is fit point-in-time, never on the full sample

The vectoriser is fit only on documents whose `information_available_time` is
at or before the computation instant (`select_point_in_time_corpus`). Fitting
IDF across the whole sample would let term rarity measured on not-yet-filed
documents change the weights applied to earlier ones — look-ahead that no
amount of careful return-side lagging would undo.

Enforced by `tests/test_similarity.py::TestPointInTimeCorpus`, which includes a
test showing the leaked and honest corpora produce *different* similarities, so
the guard is demonstrably load-bearing rather than decorative.

### D7 — An undefined similarity is reported, never coerced to zero

If a document shares no vocabulary with the fitted corpus its TF-IDF vector is
all zeros and the cosine is undefined. That returns `unavailable_reason`, not
`0.0`. A zero cosine would claim *maximal* year-over-year change — the
strongest possible signal — from what is actually a vectorisation failure.
Same reasoning as D4.

### D8 — Universe: point-in-time from EDGAR, sample 2015–2025

Membership for year *Y* is "companies that actually filed a 10-K in year *Y*",
read from EDGAR's quarterly `full-index/YYYY/QTRn/form.idx`. That index lists
filings as they happened, including from companies that have since been
acquired, delisted or gone bankrupt.

This is the part that is free and genuinely fixes something: **the text side
carries no selection bias at all.** A universe assembled from today's ticker
list would silently be a list of survivors.

It does *not* fix the return side. Mapping a historical CIK to a tradeable
ticker relies on SEC's current `company_tickers.json`, so a company that no
longer exists has no ticker and drops out. That residual bias is exactly C1,
and rather than restate it as a caveat the pipeline **measures** it: attrition
is reported at each stage of the funnel —

```
10-K filers in year Y            (point-in-time, unbiased)
  → have a current ticker        (drops acquired / delisted / renamed)
  → have usable price history    (drops illiquid and data-gap names)
  → top ~200 by dollar volume    (the traded universe)
```

The gap between the first and last row is the survivorship leak, stated as a
number rather than a footnote. Target width ~200 gives ~40 names per quintile.

Sample period 2015–2025 straddles both structural breaks the study cares
about: publication of *Lazy Prices* (2020) and broad LLM availability (2023+).

### D9 — Holding period: 1 month

Matches the existing monthly rebalance spine in `factor_validation`, so the
text arm and the price baseline are compared on identical timing rather than
on two conventions that would have to be reconciled afterwards.

This sets the HAC bandwidth floor to `max(nw1994, 0)` via
`newey_west_lag(n, holding_periods=1)`. Fixed **now**, before any t-statistic
is computed, because choosing the horizon after seeing the t-statistic is the
most common form of the same p-hacking the lag rule guards against.

### D10 — `PASS_ELIGIBLE_WIDTH` = 20

Below 20 usable names in a cross-section, core checks return `inconclusive`
rather than `pass`. Five quintiles over fewer than 20 names is not a quintile
sort, it is four names per bucket and noise.

### D11 — Falsification criteria, written before the run

The result is a **Fail** for the text channel if any of these holds:

1. incremental signal value has `|t| < 2.0` under the pre-registered HAC lag;
2. net economic value ≤ 0 after trading *and* inference cost;
3. the sign of the effect is opposite to the documented direction (i.e. firms
   that *changed* their filing outperform), which would indicate the pipeline
   is measuring something other than the hypothesised effect.

The result is **Inconclusive** — not a pass — if cross-sectional width falls
below D10, or if extraction attrition leaves fewer than 5 usable years.

Declaring these now is the point. A negative verdict published against this
list is a finding; a negative verdict explained away afterwards is not.

---

## Still open — must be fixed before A4 runs

These bind at A3/A4, when similarity meets returns. They are **not** decided
here, and deciding them from a first result would invalidate the experiment.

| Decision | Notes |
| --- | --- |
| **Backfill polling interval** | Currently defaults to 15 minutes in `edgar_collector`. It is a free parameter that moves `information_available_time`, and therefore results. |

---

## Standing constraints these decisions inherit

- **C1** — modern re-test, not a replication; survivorship bias is a core
  limitation, not a footnote.
- **C2** — no causal claim that LLMs caused any decay; this is a
  structural-break diagnosis.
- **C3** — the measured quantity is **incremental signal value**, not alpha.

See `docs/HANDOFF_TEXT_SIGNALS.md` Part 2 for the full statements and
`docs/KNOWN_LIMITATIONS.md` items 7–11 for the data-quality boundary.
