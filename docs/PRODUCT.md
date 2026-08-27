# Company Lens — Product Definition

> Working title. The product definition is intentionally independent of the final
> brand and repository name.
>
> This document describes the product direction. The narrower portfolio-project
> commitment, feature cuts, and interview story are frozen in [SCOPE.md](SCOPE.md).

## Product promise

Enter a public company and get a clear, source-backed picture of:

- what the company is;
- what it disclosed recently;
- what changed from prior disclosures;
- how the stock has performed historically;
- what risk an investor actually experienced; and
- what remains uncertain.

Deterministic code owns every number. NLP organizes the source material. An LLM
explains cited evidence in plain language. The product does not predict short-term
price direction, produce buy/sell signals, optimize a portfolio, or compete with
institutional research desks.

## One-sentence positioning

**A source-backed company intelligence page that combines SEC filings, historical
performance, risk, NLP, and grounded AI for ordinary investors.**

Suggested homepage copy:

> Understand a public company in 30 seconds: latest disclosures, historical return,
> risk, and an AI explanation with citations. No price prediction. No investment
> recommendation.

Chinese copy:

> 输入一家公司，30 秒看懂最新披露、历史表现与风险画像。所有数字可追溯，AI 只解释，不预测涨跌。

## Audience

Primary audience:

- an ordinary investor who knows a ticker but not how to read an 8-K;
- a job interviewer evaluating data science and AI-product judgment; and
- an analyst who wants a fast first-pass brief before opening the source filing.

The interface assumes financial curiosity, not quant-research expertise. Terms such
as beta, drawdown, abnormal return, and filing item codes must always have a plain
language explanation.

## The user question

The product answers one question:

> What should I understand about this company right now, based on public evidence
> and its historical record?

It does not answer:

> Will the stock go up, and should I buy it?

## Primary user journey

1. Enter a ticker, for example `AAPL`.
2. See an immediately usable cached company snapshot.
3. Read a four-card executive snapshot: latest disclosure, selected historical lens,
   interpretation, and the boundary on what not to conclude.
4. Inspect historical return and risk relative to a benchmark.
5. Open the latest filings, their cited passages, and changes from prior filings.
6. Ask a follow-up question whose answer is restricted to the retrieved evidence.
7. See the source, timestamp, methodology, and limitations behind every output.

## Information architecture

The MVP is one company page, not a collection of research workspaces.

### 1. Company header

- ticker, company name, sector, and short business description;
- current or latest available market price;
- market-data and filing-data timestamps;
- latest filing type and acceptance time; and
- clear source links.

### 2. Thirty-second brief

Four deliberately unequal cards:

- **Latest disclosure** — filing type, event category, acceptance time, observed
  reaction, and the most important supported change;
- **Selected historical lens** — total return and maximum drawdown as the two
  headline numbers for the active period;
- **Read the signal** — a plain-language interpretation of supplied evidence; and
- **Do not over-read it** — missing evidence, ambiguity, or a limitation.

Cards use an asymmetric visual hierarchy rather than giving every metric equal weight.
Externally checkable claims cite filing passages or deterministic metrics.

### 3. Historical investment picture

The user selects an initial amount and start date. The page shows:

- current historical value of the investment;
- cumulative total return;
- CAGR;
- benchmark return and relative return;
- maximum drawdown;
- time to recover from the largest drawdown;
- worst day, month, and year; and
- whether dividends are included in the selected price series.

The main chart answers:

> What happened to $10,000 invested on this date, compared with the benchmark?

This is historical buy-and-hold context, not a strategy backtest or expected return.

### 4. Risk picture

- annualized historical volatility;
- beta and correlation to the benchmark;
- current drawdown from the historical peak;
- maximum historical drawdown;
- frequency of declines greater than a stated threshold;
- filing-reaction distribution; and
- transparent comparisons such as `higher than SPY`, not an unexplained composite
  risk score.

### 5. Filing intelligence

For each filing:

- form, item codes, acceptance time, and source URL;
- plain-language summary;
- key disclosed numbers;
- ranked source passages;
- changes from the prior comparable filing;
- text novelty relative to the issuer's own history;
- historical reaction percentile; and
- explicit uncertainty and extraction warnings.

The existing materiality model becomes a supporting attention-ranking component.
The user-facing output is a historical percentile and explanation, not a trading
signal or an unsupported prediction.

### 6. Ask this company

The assistant answers questions using only the current company snapshot, retrieved
filing passages, deterministic metrics, and approved glossary/methodology content.

Every answer contains:

- a direct answer;
- cited evidence;
- the relevant date range;
- a distinction between observed fact and interpretation; and
- an explicit `not available` result when evidence is missing.

## Product boundaries

### In scope

- US public companies with usable SEC and market data;
- company snapshot and source freshness;
- historical buy-and-hold performance;
- transparent risk metrics;
- SEC filing ingestion and comparison;
- filing materiality and novelty;
- cited LLM summaries and Q&A;
- bilingual English/Chinese explanation; and
- an optional user-entered portfolio snapshot after the single-company product is
  complete.

### Out of scope

- price targets and future-return forecasts;
- buy, sell, hold, promote, or reject labels;
- alpha research and factor discovery;
- strategy backtesting and parameter tuning;
- model tournaments presented as investment evidence;
- paper trading or broker integration;
- automated rebalancing or portfolio optimization;
- autonomous investment agents; and
- a multi-stage research lifecycle UI.

## Quantitative content

Quantitative content must answer ordinary user questions directly.

| User question | Deterministic output |
|---|---|
| What happened to an investment? | Growth of $10,000, total return, CAGR |
| Was it a rough ride? | Volatility, drawdown, recovery time, worst periods |
| Did it beat the market? | Same-period benchmark and relative return |
| Does it move with the market? | Beta and correlation with named benchmark |
| Was this filing unusual? | Issuer-relative novelty and reaction percentile |
| Is the latest filing worth reading first? | Rank, operational baseline, cited drivers |

No metric is shown without its period, benchmark, source, and plain-language meaning.

## NLP responsibilities

NLP owns organization and retrieval, not investment conclusions.

Required capabilities:

1. **Document normalization** — remove markup while preserving headings, tables,
   paragraphs, and stable source anchors.
2. **Section and event classification** — map filing passages to event types such as
   earnings, agreements, management changes, litigation, impairment, and financing.
3. **Key-passage ranking** — surface the passages most relevant to the filing's item
   codes and detected changes.
4. **Novelty detection** — compare with the issuer's prior comparable filings.
5. **Change detection** — identify added, removed, and materially changed statements
   and numbers.
6. **Entity and number extraction** — extract dates, amounts, percentages, names, and
   referenced agreements with source spans.

Sentiment may be reported as a secondary descriptive feature, never as the main
filing interpretation.

## LLM responsibilities

The LLM may:

- turn supplied structured evidence into plain language;
- summarize cited filing passages;
- compare two supplied filings;
- explain financial and SEC terminology;
- answer evidence-grounded follow-up questions; and
- adapt explanation depth and language.

The LLM may not:

- calculate authoritative return or risk metrics;
- invent missing company facts or filing numbers;
- infer a target price or expected return;
- issue an investment recommendation;
- cite a passage that was not supplied; or
- silently convert interpretation into fact.

The response contract is structured:

```json
{
  "what_changed": [],
  "why_it_matters": [],
  "key_numbers": [],
  "risks": [],
  "uncertainties": [],
  "citations": []
}
```

## Trust contract

The interface visually separates three authorities:

1. **Observed source** — SEC text, XBRL facts, and market observations.
2. **Deterministic calculation** — performance, risk, event study, novelty, and rank.
3. **AI interpretation** — cited natural-language explanation.

Every page must show:

- source and timestamp;
- calculation period and benchmark;
- whether the data is real, cached, delayed, or synthetic;
- citations at the claim level;
- unavailable and partial states; and
- limitations close to the claims they qualify.

## LLM and NLP evaluation

The AI layer is a measured component, not a visual feature.

Minimum evaluation set:

- valid structured-output rate;
- citation coverage;
- citation entailment / support rate;
- extracted-number consistency;
- unsupported-claim rate;
- key-event recall on a labeled filing set;
- comparison accuracy for changed/unchanged statements;
- latency; and
- cost per processed filing.

The product must retain a deterministic no-LLM fallback: source passages, extracted
facts, and quantitative metrics remain available when an LLM is unavailable.

## Automation

```text
SEC submissions / XBRL / market data
                 ↓
        normalize and timestamp
                 ↓
 deterministic metrics + NLP extraction
                 ↓
       cited structured LLM explanation
                 ↓
 snapshot cache + company page + Q&A
```

Two refresh paths are required:

- **Scheduled refresh:** poll known issuers, process new filings idempotently, and
  rebuild affected company snapshots.
- **On-demand refresh:** return cached content immediately, then check for a newer
  filing and update the page when processing completes.

Every run records source identifiers, timestamps, code/model version, warnings,
and output hashes. Reprocessing the same accession must not create a duplicate.

## Success criteria

The MVP is successful when a new user can:

1. enter a supported ticker;
2. understand the latest material disclosure without opening the full filing;
3. verify every important claim against a cited source passage;
4. understand historical return and risk relative to a benchmark;
5. distinguish observed data from AI interpretation; and
6. complete the journey without seeing a research protocol, strategy backtest,
   unexplained signal score, or investment recommendation.
