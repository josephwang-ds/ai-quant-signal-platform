# Company Lens — Long-term value workbench research

## Decision

Company Lens should evolve from a portfolio demonstration into a personal,
source-backed **long-term company review workbench**. Its job is not to name a buy
or sell. Its job is to reduce the weekly work required to answer:

1. Is this still a high-quality business?
2. Is its growth economically productive and financially durable?
3. Is the balance sheet able to survive a bad period?
4. What expectations appear to be embedded in today's price?
5. What changed since the last review, and does it weaken the thesis?

That is a more useful product boundary than either a news dashboard or a universal
stock score. It supports a decision while keeping assumptions visible and editable.

## What the evidence supports

The research points to a combined **quality + price + change** framework:

- **Price must be connected to future cash flows.** Intrinsic value is a function of
  cash flows, growth, and risk, and a DCF is useful partly because it forces those
  assumptions into the open. A reverse DCF is therefore better suited to this product
  than an unexplained fair-value target: it can show what growth and margin assumptions
  the current price requires without claiming those assumptions will occur.
  [Damodaran valuation foundation](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/background/valintro.htm)
- **Cheap is not sufficient.** Gross profitability has historically carried
  substantial information alongside traditional value measures, while broader quality
  research combines profitability, growth, safety, and payout. The interface should
  therefore show business economics beside valuation rather than rank on P/E alone.
  [Novy-Marx profitability research](https://www.nber.org/papers/w15940),
  [Quality Minus Junk](https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk)
- **Earnings quality matters.** The cash and accrual components of earnings have
  different persistence. Cash conversion and accrual intensity belong beside reported
  earnings growth so an accounting increase is not automatically treated as durable.
  [Sloan accrual research](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2598)
- **Capital allocation changes per-share value.** Retained earnings, acquisitions,
  debt, issuance, dividends, and repurchases must be judged per share and in relation
  to price. A buyback is not automatically positive, and growth that consumes large
  amounts of low-return capital is not automatically valuable.
  [Berkshire 2010 letter](https://berkshirehathaway.com/letters/2010ltr.pdf),
  [Berkshire 2011 letter](https://www.berkshirehathaway.com/letters/2011ltr.pdf)
- **The filing is the primary record.** The SEC describes the 10-K Business, Risk
  Factors, MD&A, audited financial statements, and notes as the core places to
  understand operations, risks, liquidity, trends, and accounting judgments. News is
  secondary context; a material 10-K/10-Q/8-K change should rank above repeated market
  commentary.
  [SEC guide to reading 10-K/10-Q](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/how-read)

Historical empirical relationships are not promises of future return. They justify
which questions the workbench asks; they do not justify a deterministic stock rating.

## Recommended default page

### 1. Long-term brief

The first screen should be a one-minute memo, not a grid of equal cards:

- **Current view:** `Research`, `Watch`, or `Needs review` — a user-owned workflow
  state, never a model-issued buy/sell label.
- **Why it may compound:** two or three evidence-backed strengths.
- **What the price assumes:** a reverse-DCF expectation range or, until that exists,
  valuation ratios compared with the company's own history.
- **What could break the thesis:** the three most material risks or deteriorating
  trends.
- **What changed:** only new facts since the last reviewed filing or saved thesis.

### 2. Business quality and durability

Use annual data by default and trailing-twelve-month data only when definitions are
comparable. Show trends, not isolated point values.

| Question | Core measures | Interpretation guardrail |
|---|---|---|
| Is the business profitable? | gross margin, operating margin, ROA/ROE, gross profit/assets | sector and accounting model affect comparability |
| Does growth create value? | revenue, operating income and FCF CAGR; reinvestment; return on capital | growth without adequate return on capital can destroy value |
| Are earnings cash-backed? | operating cash flow/net income, FCF conversion, accrual ratio | one year can be distorted by working capital |
| Is financing resilient? | net cash/debt, interest coverage, debt maturity context | banks and insurers require a separate model |
| Is per-share ownership improving? | diluted share trend, buybacks, dividends, stock compensation | repurchases only help when price and dilution are considered |

No universal composite score should ship in the first version. Each measure should
show direction, period, source, coverage, and a short explanation. A later score is
acceptable only if every component, weight, sector rule, and missing-data behavior is
visible and tested.

### 3. Valuation as expectations

Use three layers:

1. **Current observable multiples:** FCF yield, earnings yield, EV/operating income,
   and price/book only where economically meaningful.
2. **Own-history range:** current percentile versus the same company's prior five or
   ten years, using point-in-time fundamentals and prices.
3. **Editable reverse DCF:** solve for the growth or margin path required to reconcile
   market price with user-selected discount and terminal assumptions.

The output should say `the current price is consistent with these assumptions`, not
`fair value is $X`. Banks, insurers, REITs, commodity producers, and firms with
negative normalized cash flow need dedicated templates or an honest unsupported state.

### 4. Thesis change feed

Replace a generic news stream with a ranked change feed:

- SEC filing or earnings exhibit change;
- guidance or capital-allocation change;
- material acquisition, divestiture, financing, litigation, or management change;
- company headline that adds a fact not already present in the filing;
- repeated or broad-market commentary collapsed by topic.

Each item needs `what changed`, `why it may matter`, `source`, `published/accepted
time`, and `which thesis assumption it touches`. The LLM may classify and explain
supplied evidence, but deterministic code owns dates, values, comparisons, and source
links.

### 5. Personal thesis journal

The highest personal-use return after fundamentals is a small private journal:

- thesis and expected holding period;
- required evidence before considering an entry;
- key assumptions and invalidation conditions;
- optional valuation scenarios, never an automated recommendation;
- watchlist status and last-reviewed timestamp;
- machine-generated diff between the saved thesis and new evidence.

Supabase is appropriate here because this data is private and user-authored. Public
company facts can remain cacheable build artifacts; private thesis state should not be
embedded in static HTML.

## Data architecture

### Primary sources

- SEC submissions and filing documents for identity, disclosures, and source text.
- SEC Company Facts/XBRL for standardized reported financial facts. The API is free,
  needs no key, updates throughout the day, and exposes annual and quarterly facts.
  Company extensions and fiscal calendars still require normalization and coverage
  warnings. [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- Adjusted daily prices for historical shareholder experience and price-linked
  valuation observations.
- Company-matched headlines as a secondary discovery layer, never the authoritative
  source for reported financial figures.

### New deterministic snapshot contract

Add a versioned `fundamentals` section with:

- standardized annual observations and the exact XBRL concept used;
- filing accession, period start/end, filed date, unit, and fiscal-year/quarter;
- normalized derived metrics with numerator and denominator citations;
- coverage flags for restatements, duplicate contexts, tag substitution, missing
  periods, and sector-template applicability;
- a separate `valuation_context` whose price date matches the latest eligible
  fundamental knowledge date.

Point-in-time discipline matters: a historical valuation series must use the first
public filing date for each fact, not today's restated history as if it had been known
earlier.

## Sector boundary

Start with a **general operating-company template**. Do not pretend one ratio system
works everywhere.

- General operating companies: revenue, margins, cash conversion, capital returns,
  leverage, per-share trends, and FCFF/reverse DCF.
- Banks and insurers: separate capital, credit quality, book-value, and excess-return
  model; do not show industrial net debt/EBITDA or FCFF as if comparable.
- REITs: require FFO/AFFO and property/debt maturity context.
- Commodity businesses: normalize through-cycle prices and margins before valuation.
- Negative-cash-flow or very young companies: emphasize unit economics only when a
  trustworthy source exists; otherwise show the missing analytical boundary.

## Product priorities and ROI

| Priority | Work | Personal usefulness | Cost/risk |
|---|---|---:|---:|
| P0 | Full English/Chinese interface toggle; preserve source text | High | Low |
| P1 | SEC XBRL annual trends and data-quality flags | Very high | Medium |
| P1 | One-minute long-term brief and thesis-change feed | Very high | Medium |
| P1 | Private watchlist/thesis journal | Very high | Medium |
| P2 | Own-history valuation context and editable reverse DCF | High | Medium-high |
| P2 | General-company quality/financial-resilience view | High | Medium |
| P3 | Bank/REIT/commodity-specific templates | High for those holdings | High |
| Avoid | Real-time market-news wall, sentiment score, universal stock score, target price | Low | High trust risk |

The recommended next engineering slice is **AAPL end to end**: ingest five to ten
years of annual SEC facts, calculate a small audited set of quality and per-share
trends, add expectation-based valuation context, and produce a thesis-change brief.
Only after field-level QA should the pipeline expand across the 193-company universe.

## Success measures

Product success should be measured by the personal review workflow, not page views:

- time required to complete a weekly watchlist review;
- percentage of displayed conclusions with a working primary-source path;
- percentage of followed companies with current financials and reviewed thesis state;
- number of new items collapsed as duplicates versus surfaced as thesis-relevant;
- grounded-answer validation pass rate and explicit `not available` rate;
- user corrections to an extracted fact or thesis classification.

The target is a repeatable, auditable decision aid. The site should make research
faster and more disciplined while leaving the investment decision with the user.
