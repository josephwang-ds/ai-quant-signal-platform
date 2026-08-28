# Company Lens — Portfolio Scope and Story

This document freezes the portfolio-project scope. [PRODUCT.md](PRODUCT.md) describes
the longer product vision; this file defines what must actually be finished and
demonstrated.

## Scope decision

Build one excellent **source-backed company page**, plus a compact methodology view.
Do not build a general investment platform.

The page answers three ordinary-user questions in a fixed visual order:

1. **What happened historically?** — a $10,000 investment and risk picture versus
   SPY over the same period.
2. **What did the company disclose?** — the latest filing, what changed from the
   prior comparable filing, and the passages and numbers that support it.
3. **What can I trust?** — clear separation between source facts, deterministic
   calculations, and AI interpretation, with dates, citations, and limitations.

Everything in the MVP must strengthen one of these three answers.

The default page is also the interview story: the first screen is an executive signal,
the historical chart explains experience, filing cards prove the source, and the final
architecture cards expose the data engineering, quant/NLP, and grounded-LLM boundaries.

## The strongest way to describe it

### One sentence

> I built a source-backed company intelligence page that combines SEC filings,
> transparent historical risk/return, document NLP, and a citation-checked LLM brief
> for ordinary investors—without predicting stock prices.

### Thirty-second version

> Financial sites show charts, and generic AI tools summarize documents, but they
> rarely show where an answer came from or whether a number was calculated correctly.
> Company Lens takes a ticker and produces one evidence-backed view: what a $10,000
> investment actually experienced, what the latest SEC filing changed, and a plain-
> language explanation linked to the source. Code owns the numbers, NLP retrieves and
> compares the filing evidence, and the LLM may only explain supplied evidence.

### Ninety-second interview version

> I deliberately moved away from trying to look like an institutional trading
> platform. The user is an ordinary investor who wants to understand a company, not
> receive a price target. The difficult part is making three data types agree: SEC
> knowledge timestamps, adjusted market history, and unstructured filing text.
>
> The quantitative layer computes same-period return, drawdown, volatility, beta,
> and benchmark comparison. The filing layer preserves source anchors, detects changes
> against earlier comparable filings, extracts cited numbers, and measures novelty
> without looking at future documents. A bounded LLM turns that evidence into `what
> changed`, `why it matters`, and `what remains uncertain`; it does not calculate
> metrics or issue investment advice.
>
> The underlying Filing Triage work demonstrates the deeper data-science judgment:
> point-in-time event construction, market-reaction measurement, purged walk-forward
> validation, realistic baselines, and leakage tests that fail the build. The product
> page stays simple, while the methodology view proves the result is not a polished
> wrapper around unreliable analysis.

## MVP: must ship

### 1. One company-page experience

- ticker input from a declared supported universe;
- company name, latest available adjusted close, and freshness;
- a five-year default with selectable one-, three-, five-, and ten-year periods;
- growth of $10,000 against SPY;
- total return, CAGR, relative return, volatility, beta, correlation, maximum and
  current drawdown, worst day, and recovery duration;
- plain-language definitions next to unfamiliar metrics;
- explicit historical-context and no-investment-advice language.

The portfolio demo should pre-cache at least `AAPL`, `MSFT`, and `NVDA`. Supporting
more tickers through the same contract is useful, but is not a separate feature.

### 2. One high-quality filing workflow

- latest 8-K metadata and direct SEC link;
- retrieval of the primary document and referenced earnings exhibit when present;
- stable paragraph or table anchors;
- comparison with the prior filing of the same event type;
- added, removed, and changed passages;
- extracted amounts, percentages, and dates with source anchors;
- three ranked passages and an issuer-relative novelty measure;
- honest partial states when an exhibit, table, or comparable filing is unavailable.

The MVP does not need broad support for every SEC form. A reliable earnings 8-K path
is more compelling than shallow support for 8-K, 10-Q, 10-K, proxy statements, and
earnings calls simultaneously.

### 3. One bounded AI brief

- structured `what changed`, `why it matters`, `key numbers`, and `uncertainties`;
- claim-level citations restricted to supplied filing anchors and metric IDs;
- automatic rejection or marking of uncited claims;
- numeric-consistency validation against deterministic metrics and cited text;
- a deterministic fallback that keeps the page useful without a model key;
- one explanation depth and one language for the MVP.

Free-form `Ask this company`, bilingual output, model comparison, and multi-agent
research are not required to demonstrate grounded LLM engineering.

### 4. One credible DS/methodology view

- data lineage from EDGAR/market source to snapshot;
- knowledge time versus filing date, with one concrete leakage example;
- event-reaction definition and a consistent ex-ante target;
- purged walk-forward validation diagram;
- model top-five precision compared with arrival order and a simple Item 2.02
  heuristic on the same eligible sessions;
- out-of-sample feature importance;
- sample period, universe limitation, attrition, and real-versus-synthetic labels;
- a downloadable or committed evidence artifact behind every published figure.

The materiality model is supporting evidence for prioritizing filings. It is not the
homepage promise and must not appear as a return forecast or a buy/sell signal.

### 5. Minimal automation

- one idempotent refresh workflow keyed by SEC accession;
- cached-first company snapshots;
- visible `current`, `stale`, `partial`, and `failed` states;
- retryable per-company failure without stopping the full run;
- provenance containing source times, code/prompt version, and output hash.

A manual or scheduled daily job is sufficient. Streaming data and trading-grade
latency are outside the user problem.

## Stretch, only after the MVP is polished

- bounded Q&A over the current company evidence;
- controllable RAG through bounded document import and safe reader rules, with
  LangChain limited to an optional loading/splitting adapter;
- bounded source-linked company and market headline context, capped at three rows
  and designed for a daily cached index rather than a live feed;
- Chinese/English explanation toggle;
- 10-Q and 10-K comparison;
- XBRL trend cards for a small set of standardized financial facts;
- a watchlist of recent filing changes; and
- a user-entered historical portfolio picture.

Stretch work must not delay source anchors, filing comparison, evaluation, or the
single company page. Evidence persists to local JSON when dynamic
uploads or retrieval history require persistence; it is not an MVP user feature.

## Explicitly out of scope

- price direction, price targets, or expected-return forecasts;
- buy/sell/hold recommendations;
- factor discovery, alpha research, strategy optimization, or model tournaments;
- technical-indicator dashboards that do not answer a user question;
- portfolio optimization or automated rebalancing;
- broker connections, paper trading, or order execution;
- sentiment as the main filing conclusion or as a headline trading signal;
- general web research agents or autonomous investment agents;
- social feeds, infinite news streams, and live-news infrastructure; and
- real-time market infrastructure.

## Why each component is easy or hard to explain

| Component | Story value | Explanation difficulty | Decision |
|---|---:|---:|---|
| Growth of $10,000 vs SPY | Very high | Very low | Hero chart |
| Drawdown and recovery | High | Low | Keep; translates risk into experience |
| Beta, correlation, volatility | Medium | Medium | Keep as secondary cards with definitions |
| Filing `what changed` with citations | Very high | Low | Core differentiator |
| Filing numbers linked to passages | Very high | Low | Core trust proof |
| Point-in-time timestamps/leakage | Very high in interviews | Medium | Methodology story, not homepage jargon |
| Purged walk-forward validation | High for DS roles | High for ordinary users | Methods drawer only |
| Operational top-five baselines | High | Medium | Keep; compares with a real reading workflow |
| Novelty score | Medium | Medium | Supporting feature, never a magic score |
| Historical reaction percentile | Medium | Medium | Supporting context with a clear retrospective label |
| Generic chatbot | Low | Low | Defer; common and weakly differentiated |
| Sentiment gauge | Low | Low | Exclude; easy to show but hard to defend |
| Portfolio optimizer | Low for this story | High | Exclude; changes the product promise |
| Autonomous agent | Low | High | Exclude; adds spectacle, not evidence |

## What the project demonstrates

### Data science

- causal feature and label construction;
- point-in-time joins and knowledge-time reasoning;
- event-study normalization;
- temporal validation, purging, realistic baselines, and leakage tests;
- interpretable historical risk/return calculations; and
- evaluation design tied to a human reading constraint.

### NLP

- document normalization with stable anchors;
- event/section classification using SEC structure and text;
- comparable-document retrieval;
- change and novelty detection without future-document leakage;
- passage ranking and typed entity/number extraction; and
- a labeled evaluation set with extraction and comparison metrics.

### LLM engineering

- evidence assembly and bounded context;
- typed structured output;
- claim-level citation validation;
- numeric-consistency and unsupported-claim checks;
- prompt/model/evidence versioned caching;
- deterministic degradation when the provider is unavailable; and
- quality, latency, and cost evaluation.

### Product judgment

- a clear non-institutional user and problem;
- quantitative depth without pretending historical data predicts the future;
- explicit tradeoffs and honest missing states; and
- AI used only where language understanding improves the experience.

## Demo script

The live demo should take five minutes:

1. Enter `AAPL` and explain the one-sentence promise and three-step evidence flow.
2. Read the executive cards from latest disclosure to historical lens to guardrail.
3. Change the period once and show that the headline return/drawdown cards and the
   $10,000 chart share the same state.
4. Open the latest earnings 8-K and show one changed statement and cited number.
5. Show the rules-based fallback or bounded AI mode without changing the underlying
   evidence cards.
6. Use the architecture cards to explain data engineering, quant/NLP, and the LLM
   boundary; then show one methodology leakage example plus the realistic
   baselines.
7. End with the limitation: historical context and disclosure understanding, not a
   forecast or recommendation.

Avoid touring every metric or architecture folder. The audience should remember the
user problem, the evidence chain, and one example of DS judgment.

## Definition of done

The portfolio version is complete when:

- a reviewer can understand the product in one sentence;
- the AAPL/MSFT/NVDA pages work from cached evidence in under three seconds;
- every displayed number has a period, benchmark, and source definition;
- every filing claim and extracted number opens its supporting passage;
- the same filing is compared only with an earlier comparable filing;
- the LLM brief passes schema, citation, and numeric checks or falls back visibly;
- the methodology uses corrected targets, features, and operational baselines;
- all published figures trace to committed evidence artifacts;
- tests, lint, and one end-to-end smoke test pass; and
- the README, screenshots, and five-minute demo tell the same story.
