# Methodology

## The question

Not "will this filing move the stock up or down" — that is a bet against people
with faster data, better models and more capital, and it is not a bet worth
taking. The question here is **which of today's filings deserve a human read**,
which is a ranking problem over *reaction magnitude* and is answerable.

The distinction matters for what counts as success. A direction model is only
useful if it beats the market. A triage model is useful if it beats reading the
filings in the order they arrive.

## Measuring the reaction

A standard market-model event study.

```
estimation window   [entry - 139, entry - 20] sessions (120 observations)
                    regress issuer return on market return
                    -> alpha, beta, residual standard deviation

event window        [entry, entry + 1] sessions
                    abnormal = actual - (alpha + beta * market)
                    CAR = sum over the window

reaction            |CAR| / (residual sd * sqrt(window))
```

Expressed in standard deviations of that issuer's own noise, so a utility and a
biotech land on the same scale.

**The 20-session gap** between the estimation window and the event is not
decoration. Without it the baseline absorbs any pre-announcement drift and shrinks
the abnormality being measured.

**The label** is `reaction >= 2.0` — the absolute abnormal reaction is at least two
issuer-specific residual standard deviations. The cutoff is declared before the
sample is observed. A full-sample percentile would let future test-fold outcomes
help define what "material" means, even if the model never trained on those rows.

## Features

Every feature must be computable by someone standing at `decision_time`.

| Family | Features |
|---|---|
| What kind of news | 8-K item codes (21 one-hot), item count |
| When it landed | pre / open / post / closed, hour, weekday, days since last filing, filings in the trailing year |
| How unusual | cosine distance from the issuer's own previous 8 filings, document length, length vs the issuer's running median |
| Issuer state | 20-session volatility, 5-session mean absolute return, 20-session dollar volume, relative volume — all ending the session *before* entry |

**Novelty uses a `HashingVectorizer`, not TF-IDF.** This is a leakage decision, not
a performance one. TF-IDF must be fitted, and a vectorizer fitted over the whole
corpus carries document frequencies computed from filings that had not been
written yet. Hashing is stateless: the same document maps to the same vector
regardless of what else is in the sample.

## Validation

Purged, embargoed walk-forward, five folds. A training event survives only if its
entire outcome window closed before the test fold opened, plus a five-day embargo.
See [LEAKAGE.md](LEAKAGE.md) §4.

Metrics are ranking metrics. With a rare outcome, accuracy is worthless —
"nothing is material" can look strong while surfacing nothing. The headline is
**average precision**, with
**mean daily precision@5** as the product metric: of the five filings surfaced
each morning, how many actually mattered. Averaging the daily figure is both what
the product does and far more stable than one pooled top-5 over three years.

Daily lift uses the expected random precision on the **same eligible sessions**,
not the pooled sample base rate. The report also compares the model with arrival
order and a simple rule that reads Item 2.02 earnings filings first. Those are
credible alternatives to deploying a model and are evaluated on exactly the same
out-of-sample rows.

ROC AUC is reported as a familiar cross-check, not as the headline. It averages
over the whole ranking including the tail nobody reads, and it is blunt about
leaks that concentrate on the positives.

## What this does not claim

- **No return prediction.** Direction is never modelled, and no strategy return,
  Sharpe ratio or P&L appears anywhere. Reaction *magnitude* is a different and
  more tractable quantity.
- **No claim of tradability.** Ranking which filings the market reacted to is not
  the same as being able to profit from it, and the embargo sweep exists partly to
  show how little is left after any realistic delay.
- **Daily bars only.** The entry convention — the first *open* at or after the
  decision time — is the most conservative one available at daily resolution.
  Intraday data would allow a tighter and more interesting measurement.
- **Vendor-adjusted prices.** Splits and dividends are adjusted as of today, so
  the price history is not literally what a trader saw. This does not bias the
  study — the event return and its benchmark come from the same adjusted series,
  and the adjustment is multiplicative — but it is a compromise worth naming.
