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

**Where the event window starts** is a decision, not a detail. A close-to-close
series anchors the entry session's return at the *previous* close, which for the
63.2% of 8-Ks accepted outside market hours was printed before the filing
existed. No leakage guard sees this: `causal(acceptance_time <= entry_open)`
passes on every row precisely because the label never touches `entry_open`.

It stays close-to-close anyway. The question is *was this filing material*, and
the overnight gap is part of that reaction rather than contamination of it. The
alternative — `open_anchored_returns`, off by default — asks how much was still
on the table at the open, which is a different and harder question, and
`experiments.anchoring_study` reports both. What the difference is worth is
measured rather than asserted: 27.7% of a material filing's reaction is already
in the opening print, 45.7% for those accepted after the close. See
[LEAKAGE.md](LEAKAGE.md) for the full decomposition.

**Residual standard deviation uses `ddof=2`**, not 1. Alpha and beta were both
estimated on the same window, so two degrees of freedom are already spent. On 120
sessions the correction is under 1%, but it biases the denominator of every
reaction score downward — the direction that quietly moves filings across the
2.0σ threshold.

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
"nothing is material" can look strong while surfacing nothing.

**Average precision is the result.** It is threshold-free, uses the whole
ranking, and imposes no capacity, which is what makes it comparable across
pipeline versions and what makes the leakage ladder legible.

**Daily precision@k is one operational reading of it**, and it is deliberately
demoted here. Earlier versions called it the product metric and quoted `k = 5`
beside average precision as an equal, which promoted a product constraint to a
scientific one: `k` is how many filings someone reads, it was assumed from a
reader's supposed capacity, and nothing in the data derives it. Two corrections
follow.

*It has a ceiling well below 1.* A session holding one material filing caps
precision@5 at 0.2 however good the ranking is, and 37% of eligible sessions
hold none at all. The achievable ceiling on the real sample is 28.3% against a
11.6% floor, so the reading is not "19.4%" but "47% of the gap between them".

*And the whole capacity curve is reported, not one point.* Across `k` from 1 to
20 the lift moves 2.59× to 1.14× on an unchanged model while the span captured
stays near 0.4. The lift is the reading that depends on the assumption; the span
is the one that survives it. Sessions also fall away sharply with `k`, because a
capacity above the day's filing count is reading everything rather than
triaging — the real limit on how far the metric can be pushed.

A pooled top-k over the whole sample is *not* reported as a headline anywhere,
and the reason is worth stating because it is the most flattering number
available: the whole-sample top five is five rows drawn from three years, which
no reader could have acted on, since the queue arrives one morning at a time.

Daily lift uses the expected random precision on the **same eligible sessions**,
not the pooled sample base rate. The report also compares the model with arrival
order and a simple rule that reads Item 2.02 earnings filings first. Those are
credible alternatives to deploying a model and are evaluated on exactly the same
out-of-sample rows.

ROC AUC is reported as a familiar cross-check, not as the headline. It averages
over the whole ranking including the tail nobody reads, and it is blunt about
leaks that concentrate on the positives.

## Uncertainty

A project whose argument is "the flattering number is usually wrong" cannot make
that argument with bare point estimates. A reader cannot tell 1.63× ± 0.05 from
1.63× ± 0.6, and only one of those is a result.

**Resampled by session, not by row.** Filings on the same morning share a market
and a macro tape, so treating 9,721 events as 9,721 independent draws would
understate the interval. Measured, the correction is worth about 4% of the width
— far less than it sounds, because the label is already a market-model residual,
so the common factor that would have driven same-day correlation was subtracted
before the metric saw it. The cluster bootstrap stays regardless: it is correct
whether or not clustering is present, the row bootstrap only if it is absent, and
the safe one costs a rounding error.

**Baselines are paired, not a separate experiment.** Model and baseline see the
same sessions, so sessions are resampled once and every rule is rescored on that
same draw. Bootstrapping two means independently throws the pairing away and
overstates the uncertainty of their difference. The reported column is the share
of draws in which the baseline matched or beat the model — a lift of 1.41× whose
draws favour the baseline one time in eight is a different claim from the same
1.41× at zero.

**Ladder rungs carry no interval, deliberately.** Consecutive rungs are the same
pipeline on overlapping event populations — fixing the entry rule changes which
filings are measurable at all — so a resample of one is not exchangeable with a
resample of the next. A paired bootstrap over them would look rigorous and mean
nothing. What is comparable across rungs is the invariant counts, which is why
those lead the table.

Percentile intervals throughout; BCa would be defensible and is not worth the
machinery at these sample sizes, where the distributions are close to symmetric.

**Where the estimator's constants came from.** Picking them by watching the
out-of-sample metric would be a selection leak spanning the whole project, and
the one class no guard can catch — every individual run is clean and the
contamination lives in which run was kept. Answered with a spread rather than a
promise: perturbing each setting one at a time moves average precision across
0.018, narrower than the 0.062 bootstrap interval on the default, and the
defaults are not the best cell in the grid.

## Does the model family matter

The estimator is deliberately unremarkable, and a good deal rests on that being
true rather than merely convenient, so it is measured against three alternatives
on the same folds and the same events: a regularised linear model, a random
forest, and a stratified dummy that scores at the base rate by construction.

**The comparison is paired**, for the same reason the operational baselines are.
The families saw the same events on the same days, so their difference is
measured within a resample; two overlapping *independent* intervals do not
settle which is better. It matters here — independently, random forest
[0.347, 0.409] and the shipped estimator [0.338, 0.398] overlap almost entirely,
while their paired difference is about three times tighter at
[−0.003, +0.024]. It still straddles zero: **the three real families are not
distinguishable on this sample.**

Family is worth a spread of 0.027 in average precision. The validation scheme is
worth 0.220. That ratio is the argument for where the attention went.

**Every candidate is a Pipeline, and that is a leakage decision.** Two of the
families cannot take a NaN, and the obvious remedy — impute the feature frame
once, before splitting — fits the median partly on the test period and carries it
into training. It is the same shape as a TF-IDF fitted over the whole corpus, and
it is easy to miss because imputation does not feel like fitting. A Pipeline fits
its steps inside each fold, so the leak cannot happen by construction.

**Selecting between families is itself a selection leak**, the kind no per-row
guard can see. So the table above is descriptive only, and a *nested* score
prices the procedure: an inner purged, embargoed split inside each outer training
block chooses the winner, the winner is refit on the full outer training block,
and no test fold ever informs the choice made for it. The number that produces is
what "try these and keep the best" is actually worth. Here it is 0.378 and the
same family wins in every fold, so the selection is stable and its premium over
the descriptive table is zero — which is not the general case, and is why the
per-fold choices are reported alongside the score.

## Reproducibility

Randomness is pinned -- one `random_state` through the model, the permutation
importance and the bootstrap -- so the synthetic path is deterministic. That is
the easy half. The real-data path has three ways to drift, and naming them is
more useful than claiming it does not.

**The dependency floors are `>=`**, which is right for a library and wrong for a
result: two installs a year apart run the same code on different numerics, and
`HistGradientBoostingClassifier` makes no promise of identical splits across
scikit-learn versions. `requirements.lock` pins one resolution known to
reproduce; `make install-locked` installs it, and CI runs the suite against both
the lock and the floors, because those answer different questions -- *can anyone
get these numbers back*, and *does this still work on current libraries*.

**EDGAR grows.** One rebuild from the ingest cache turned 11,702 filings into
11,716. A run is a snapshot of a moving source, not a fixed dataset.

**Vendor prices are adjusted as of the pull date.** A later split rewrites the
whole history retroactively: same rows, same date range, different values. This
does not bias the study -- event and benchmark come from the same adjusted
series and the adjustment is multiplicative -- but it does mean a rerun after a
corporate action will not reproduce the numbers, and the row count will not say
so.

**So each result records what it was computed from.** `manifest.json` carries a
content fingerprint of every input frame plus the interpreter and library
versions behind it. The digest is over canonicalised content -- columns sorted,
rows sorted, floats at fixed precision -- rather than file bytes, because pandas
and pyarrow rewrite their encodings between versions and a fingerprint that
fires on a library upgrade is a false alarm that gets removed. Row counts sit
beside the hashes on purpose: a changed count is the source growing, an
unchanged count with a changed digest is values moving underneath, and those are
different problems.

## What this does not claim

- **No return prediction.** Direction is never modelled, and no strategy return,
  Sharpe ratio or P&L appears anywhere. Reaction *magnitude* is a different and
  more tractable quantity.
- **No claim of tradability**, and this is now a measurement rather than a
  disclaimer. The label is anchored at the previous close, so for a material
  filing accepted after the bell a median **45.7%** of the reaction is already in
  the opening print — gone before any entry rule could act. Scored against an
  open-anchored label the pipeline falls from 0.378 average precision to 0.158.
  The embargo sweep says the rest decays within the session.
- **Daily bars only.** The entry convention — the first *open* at or after the
  decision time — is the most conservative one available at daily resolution.
  Intraday data would allow a tighter and more interesting measurement.
- **Vendor-adjusted prices.** Splits and dividends are adjusted as of today, so
  the price history is not literally what a trader saw. This does not bias the
  study — the event return and its benchmark come from the same adjusted series,
  and the adjustment is multiplicative — but it is a compromise worth naming.
