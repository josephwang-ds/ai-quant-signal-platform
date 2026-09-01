# Company Lens — DS / DSA Expansion Plan

## 1. Objective

Keep the current **Company Lens + Filing Triage** framework intact and extend it
with a coherent set of data-science capabilities that are easy to demonstrate in
a DS or DSA interview.

The product should answer one additional question:

> **Is this company's latest disclosure unusual relative to its own history, and
> does it deserve attention now?**

The public experience remains a source-backed company page. The extension adds:

1. issuer-relative ranking;
2. calibrated filing-impact prediction;
3. a transparent reading recommendation;
4. financial-NLP features and explanations; and
5. an optional time-series foundation-model experiment for risk forecasting.

The system does **not** rank companies against one another in the UI and does not
produce buy, sell, hold, target-price, or expected-return recommendations.

---

## 1a. Implementation status

Phases 1 and 2 are built and measured. What each one returned:

| Plan section | Where it lives | Outcome |
|---|---|---|
| 5.1 issuer-relative ranking | `src/filing_triage/self_relative.py` | 10,674 of 11,665 filings have enough of their own history; 21.5% base rate |
| 5.2 calibrated prediction | `src/filing_triage/calibration.py` | Three methods compared; **isotonic made it worse**, so raw scores ship at 0.011 ECE |
| 5.3 reading recommendation | `src/filing_triage/recommend.py` | `Read now` 42.2% precision vs 21.5% base rate, on 9.1% of the queue |
| 4.2 self-history visualization | `src/company_lens/web/page.py` | Scatter of this filing against the issuer's own history |
| 5.4 financial NLP | `src/filing_triage/text_model.py` | FinBERT encoded, ablated, and **held out of the shipped model** |
| 5.5 time-series foundation model | `src/filing_triage/volatility.py`, `chronos_model.py` | Chronos-2 measured and **not shipped**; HAR passed the coverage gate and the card uses it |

Three places where the implementation departs from this document, each for a
reason worth recording:

**The transformer features do not ship.** §5.4 asks for the ablation and for an
honest report of what it shows. It showed a paired, session-clustered interval of
[−0.0102, −0.0010] average precision — below zero, not merely indistinguishable
from it. FinBERT predicts the *direction* of sentiment; the target here is the
*magnitude* of a reaction, which is direction-free by construction. Tone is close
to orthogonal to the question, and six near-orthogonal columns make a forest's
splits worse. The module and its cache remain, held beside the shipped feature
matrix rather than inside it, with a test asserting they cannot reach it.

**The foundation model does not ship either, and the card still does.** §5.5
sets the condition -- do not ship unless the intervals are calibrated -- and
Chronos-2 fails it: its 80% band holds 75.5% of outcomes, and on a paired,
session-clustered comparison it loses 0.0014 more pinball loss than a HAR
regression over an interval of [0.0010, 0.0018] that excludes zero. It was given
its best configuration, forecasting log volatility like every baseline. HAR
passes the gate, so the card exists and HAR is behind it. The gate is enforced by
the export, which writes the card file only for a calibrated forecaster and
deletes it otherwise.

**`text_model.py` lives in `filing_triage`, not `company_lens/nlp/`.**
`company_lens` already imports `filing_triage`, so the placement this document
specifies would close that into an import cycle. The features are consumed by the
ranker, which is in `filing_triage`.

**Outcome-derived issuer statistics are not features.** §5.1's point-in-time rule
is necessary but not sufficient: a percentile of *how the issuer usually reacts*
needs the earlier reaction to have finished resolving, which is strictly stronger
than the earlier filing having been accepted. `self_reaction_pct` and
`self_reaction_z` are computed for display and named in `OUTCOME_COLUMNS`, and
`assert_no_outcome_features` raises if either reaches a model.

---

## 2. Preserve the Current Framework

No package or product rewrite is required.

| Existing component | Keep its responsibility | Proposed extension |
|---|---|---|
| `filing_triage` | Point-in-time ingest, labels, features, temporal validation, leakage guards and daily ranking | Add issuer-relative targets, features, calibration and recommendation evaluation |
| `company_lens.performance` | Deterministic historical return and risk calculations | Add optional post-filing realized-volatility targets and forecast presentation |
| `company_lens.filings` | Filing taxonomy, passages, comparable filings, changes, numbers and citations | Add financial-language features and issuer-relative novelty decomposition |
| `company_lens.llm` | Bounded explanation, retrieval, validation and fallback | Explain model evidence; never own scores, predictions or recommendations |
| `company_lens.snapshots` | Versioned company-page payload | Add typed self-benchmark, prediction and recommendation fields |
| `company_lens.web` | Company page and research views | Add one self-history view and compact model-evidence cards |
| `evidence/real_run` | Reproducible quantitative evidence | Add calibration, ablation, recommendation and subgroup artifacts |

The current Filing Triage result remains the cross-sectional research foundation.
The new self-relative layer becomes an additional company-level interpretation,
not a replacement for the existing model.

---

## 3. Product Positioning

### One sentence

> Company Lens compares a company's latest SEC disclosure with its own history,
> estimates whether the reaction may be unusually large, and explains the source
> evidence behind a transparent reading recommendation.

### Thirty-second interview version

> I extended a point-in-time SEC filing pipeline into a company self-benchmarking
> system. For each disclosure, it calculates how unusual the language and event are
> relative to that issuer's prior filings, predicts the calibrated probability of
> an above-normal market reaction, and recommends `Read now`, `Monitor`, or
> `Routine`. The model can learn pooled patterns across issuers, but every user-facing
> score is normalized and explained against that company's own history. NLP extracts
> changes and evidence; deterministic code owns every metric and recommendation.

### User-facing question

> Is what this company disclosed today unusual for this company, and should I read
> it now?

---

## 4. Proposed User Experience

Do not add a separate application. Add one model-evidence section to the current
company page.

### 4.1 Latest-disclosure decision card

Example:

```text
APPLE · LATEST 8-K

Reading priority       READ NOW
Impact probability     64%
AAPL historical rate   20%
Confidence             Medium

Why
• More semantically unusual than 92% of comparable Apple filings
• Contains a large issuer-relative financial change
• Event type has historically produced above-normal reactions for Apple

Evidence
• 3 materially changed passages
• 4 source-linked financial facts
• 38 eligible historical Apple filings
```

Every displayed result must include:

- prediction timestamp;
- eligible history cutoff;
- number of comparable historical filings;
- model and feature version;
- confidence or abstention state;
- source-linked reasons; and
- an explicit statement that reaction magnitude is not price direction.

### 4.2 Self-history visualization

Show the current filing against earlier filings from the same issuer.

```text
Historical reaction magnitude
  ↑
  │                         ● Current filing
  │             ●
  │     ●             ●
  │          ●
  └────────────────────────────────→ Semantic novelty

  Each point is an earlier filing from the same issuer.
```

Recommended interactions:

- filter by comparable event type;
- hover to see acceptance date, filing type and observed reaction;
- highlight the current filing;
- switch between novelty, financial-change magnitude and predicted impact;
- open the cited filing evidence from a historical point.

Do not add peer-company comparison to this view.

### 4.3 Compact model-quality disclosure

The page should expose only a short status:

```text
Model status: calibrated on later, unseen filing periods
Coverage: prediction available / abstained
Last evaluated: YYYY-MM-DD
```

Calibration plots, ablations, leakage studies and subgroup results belong in the
research view, not the company-page hero.

---

## 5. Data-Science Tasks

## 5.1 Issuer-relative ranking

### Question

How unusual is the current disclosure compared with earlier eligible disclosures
from the same issuer?

### Proposed outputs

- semantic-novelty percentile;
- financial-change percentile;
- release-timing rarity;
- event-type rarity;
- historical-reaction percentile;
- combined attention percentile; and
- rank among eligible historical filings.

### Point-in-time rule

For filing `i` accepted at time `t`, every percentile and reference distribution
must use only filings accepted strictly before `t`.

```text
eligible_history(i) = issuer filings with acceptance_time < acceptance_time(i)
```

If history is insufficient, return `insufficient_history`; do not substitute a
cross-sectional percentile without labeling it differently.

### Minimum-history policy

Initial proposal:

| Eligible comparable filings | Output policy |
|---:|---|
| 0–4 | No issuer percentile; display raw evidence only |
| 5–9 | Percentile with `low confidence` |
| 10–19 | Percentile with `medium confidence` |
| 20+ | Standard issuer-relative result |

These cutoffs must be evaluated through a history-depth sensitivity study before
they become final product rules.

---

## 5.2 Filing-impact prediction

### Prediction target

Predict whether the filing produces an unusually large **absolute** abnormal
reaction relative to the issuer's own earlier distribution.

Candidate binary target:

```text
y_i = 1 if |CAR_i| > Q80(previous eligible |CAR| values for issuer i)
```

Alternative targets to evaluate:

- exceed issuer's rolling 80th percentile of absolute CAR;
- exceed a volatility-normalized issuer threshold;
- continuous issuer-relative reaction percentile; or
- ordinal `routine / elevated / exceptional` reaction class.

The binary target is recommended for the first release because it supports clear
probability calibration and recommendation rules.

### Prediction contract

```text
impact_probability: 0.64
issuer_historical_rate: 0.20
calibration_group: "sufficient_history"
confidence: "medium"
prediction_status: "available"
```

The model predicts magnitude, not sign. The UI must never translate the result
into an expected price direction.

### Modeling strategy

Use a pooled model with issuer-relative features rather than fitting one model per
issuer.

```text
All eligible historical issuers
             ↓
Pooled temporal model learns common filing patterns
             ↓
Issuer-relative percentiles and z-scores provide local context
             ↓
Calibration converts scores into usable probabilities
```

This avoids the small-sample failure of fitting a separate model on a few dozen
filings per company while preserving self-relative user outputs.

Candidate estimators:

1. regularized logistic regression as the interpretable baseline;
2. histogram gradient boosting or random forest using the existing pipeline;
3. calibrated tree model as the likely shipped candidate; and
4. an optional text-plus-tabular late-fusion model after the structured baseline
   is validated.

Model choice must remain inside the existing nested temporal selection procedure.

---

## 5.3 Reading recommendation

The recommendation concerns analyst attention, not investment action.

### Allowed states

| State | Meaning |
|---|---|
| `Read now` | High predicted impact with supported issuer-relative evidence |
| `Monitor` | Moderate probability, high uncertainty, or one strong signal without confirmation |
| `Routine` | Similar to the issuer's normal disclosure history |
| `Insufficient history` | The system cannot establish a defensible self-relative baseline |
| `Withheld` | Validation, evidence or freshness checks failed |

### Initial transparent policy

```text
READ NOW
  if calibrated_probability >= 0.60
  and at least one supported issuer-relative feature >= 80th percentile

MONITOR
  if calibrated_probability >= 0.40
  or uncertainty is high

ROUTINE
  otherwise
```

Thresholds are placeholders. Select final thresholds using training/validation
periods only and report their capacity, precision, recall and abstention behavior
on untouched later periods.

### Recommendation evaluation

Report:

- precision and recall for `Read now`;
- number of recommendations per session and per issuer;
- false-positive case review;
- false-negative case review;
- recommendation stability across nearby thresholds;
- coverage after abstention;
- performance by history depth;
- performance by filing event type; and
- temporal drift.

---

## 5.4 Financial NLP

### NLP responsibilities

1. **Event classification** — earnings, management change, financing, litigation,
   acquisition, impairment, governance and other supported event types.
2. **Comparable-document retrieval** — select only strictly earlier comparable
   issuer filings.
3. **Change detection** — identify added, removed and materially changed passages.
4. **Financial fact extraction** — amounts, percentages, dates and named metrics
   with stable source anchors.
5. **Financial-language features** — tone, uncertainty, forward-looking language,
   risk-language change and semantic novelty.
6. **Evidence explanation** — translate supported structured evidence into plain
   language without creating the underlying score.

### Proposed transformer experiment

Add a financial-domain transformer as a feature generator, not as an autonomous
decision maker.

Candidate feature groups:

- sentence/document embeddings;
- positive, negative and neutral financial tone;
- uncertainty-language share;
- forward-looking-statement share;
- embedding distance from prior comparable filing;
- embedding distance from the issuer's historical centroid; and
- tone/change interaction features.

The existing deterministic lexical and hashing features remain the baseline.

### Required ablation

| Experiment | Feature groups |
|---|---|
| Structured baseline | Filing metadata + issuer state |
| Deterministic text | Structured + existing novelty/change features |
| Transformer text | Structured + financial transformer features |
| Combined | All validated structured and text features |

Report whether transformer features improve operational metrics and calibration,
not merely whether they make the project look more current.

---

## 5.5 Optional time-series foundation model

This is a separate risk-forecasting experiment. It must not replace the filing
ranker or become a price-direction feature.

### Recommended task

Forecast the issuer's next 20-session realized-volatility distribution after the
latest filing.

Example output:

```text
Expected 20-session annualized volatility
Median forecast       24%
80% prediction band   18%–34%
Issuer 5Y median      22%
Risk state            Slightly elevated
```

### Candidate model

Use one foundation model only in the shipped experiment:

- preferred: Amazon Chronos-2;
- research challenger: Google TimesFM 2.5; or
- defer the feature if walk-forward interval coverage is unreliable.

### Inputs

- trailing returns and realized volatility;
- relative volume;
- market volatility or SPY volatility;
- filing-event indicator;
- issuer-relative novelty;
- event type; and
- release timing.

### Evaluation

- rolling-origin walk-forward evaluation;
- MAE or RMSFE for realized volatility;
- pinball loss for forecast quantiles;
- empirical coverage of 50% and 80% prediction intervals;
- interval width;
- coverage by volatility regime; and
- comparison with simple rolling-volatility and historical-quantile baselines.

Do not ship the foundation-model card unless its out-of-sample intervals are at
least well calibrated enough to be useful.

---

## 6. Feature Design

### 6.1 Existing feature groups to retain

- SEC item codes;
- form and event type;
- pre-market, intraday, after-market and non-session timing;
- text novelty;
- trailing volatility and relative volume;
- filing cadence and reporting-cycle features;
- issuer state available before the decision point; and
- market context available before the decision point.

### 6.2 New issuer-relative features

For every raw value `x`, evaluate causal transformations such as:

```text
issuer_percentile(x_t | x before t)
issuer_robust_z(x_t | x before t)
distance_from_issuer_median
distance_from_prior_comparable
event_frequency_within_issuer
days_since_same_event_type
```

Prefer robust median/MAD transformations for heavy-tailed financial variables.

### 6.3 New text features

- current-to-prior comparable embedding distance;
- current-to-historical-centroid embedding distance;
- changed-passage count and share;
- novel-number count;
- uncertainty-language change;
- forward-looking-language change;
- tone change rather than tone level alone;
- financial-fact magnitude relative to issuer history; and
- missing/extraction-warning indicators.

### 6.4 Missingness

Missingness may be informative. Preserve explicit missing indicators and evaluate
models that can use missing values natively. Do not convert unavailable evidence
to zero.

---

## 7. Validation and Evidence

Strong DS/DSA positioning depends more on validation than model novelty.

### 7.1 Temporal design

Retain:

- point-in-time acceptance timestamps;
- first eligible decision session;
- purged and embargoed walk-forward validation;
- training-only earliest block;
- strictly earlier comparable filings; and
- leakage guards that fail execution.

Add:

- issuer-history construction audit;
- percentile causality audit;
- calibration-set separation;
- recommendation-threshold selection audit; and
- foundation-model rolling-origin audit.

### 7.2 Baselines

The UI does not compare companies, but the analysis must compare methods.

Required baselines:

- issuer historical base rate;
- random ranking within eligible queue;
- arrival order;
- simple event-type heuristic;
- regularized logistic regression;
- current shipped model; and
- previous production version when a new version is introduced.

### 7.3 Core metrics

#### Ranking

- daily precision@k;
- recall@k;
- NDCG@k;
- achievable ceiling;
- share of achievable span captured; and
- sessions with enough candidates for ranking to matter.

#### Probability prediction

- PR-AUC;
- ROC AUC as a secondary metric;
- Brier score;
- log loss;
- expected calibration error;
- reliability curve; and
- calibration slope/intercept.

#### Recommendation

- precision and recall by state;
- recommendation volume;
- abstention coverage;
- selective risk;
- false-positive and false-negative review; and
- threshold sensitivity.

#### NLP

- event-classification macro F1;
- extraction precision/recall/F1;
- change-detection precision/recall/F1;
- citation accuracy;
- numeric consistency;
- unsupported-claim rate; and
- incremental lift from each text feature group.

#### Time series

- MAE/RMSFE;
- quantile loss;
- interval coverage;
- interval width; and
- regime-specific performance.

### 7.4 Required evidence artifacts

Proposed additions under `evidence/real_run/`:

```text
self_relative_metrics.json
self_relative_fold_metrics.csv
calibration_curve.csv
calibration_metrics.json
recommendation_thresholds.csv
recommendation_confusion.csv
history_depth_sensitivity.csv
event_type_subgroups.csv
self_relative_ablation.csv
nlp_feature_ablation.csv
recommendation_cases.json
tsfm_forecast_metrics.csv          # optional
tsfm_interval_coverage.csv         # optional
```

All published cards and charts must be generated from these artifacts.

---

## 8. DS / DSA Skill Mapping

The project should make each skill visible through a concrete decision or artifact.

| Skill | Project evidence | Interview message |
|---|---|---|
| Business problem framing | Five-document review capacity and `Read now` decision | Chose a metric and output tied to a real workflow |
| KPI design | Precision@k, coverage, calibration and achievable ceiling | Avoided optimizing an abstract score disconnected from use |
| Data acquisition | SEC EDGAR, market prices, filing metadata and text | Built a reproducible multi-source dataset |
| Data quality | Attrition ledger, provenance, missing-state handling | Made missing and excluded observations auditable |
| Point-in-time data | Acceptance timestamps and causal issuer history | Prevented future information from entering features |
| Feature engineering | Issuer percentiles, robust z-scores, cadence, event rarity | Converted raw financial events into defensible signals |
| Statistical thinking | Cluster bootstrap, paired comparisons and uncertainty | Reported uncertainty rather than isolated point estimates |
| Supervised learning | Calibrated classification and ranking | Matched model formulation to the user decision |
| Ranking systems | Daily top-k filing queue | Evaluated the exact capacity-constrained workflow |
| Probability calibration | Brier score and reliability curves | Made probabilities usable for recommendations |
| Recommendation systems | Read/Monitor/Routine with abstention | Converted prediction into a transparent action policy |
| NLP | Classification, change detection, embeddings and extraction | Used text models for measurable tasks, not generic summaries |
| Time-series modeling | Optional volatility quantile forecast | Evaluated a modern foundation model under walk-forward testing |
| Experimentation | Feature/model ablations and threshold sensitivity | Identified what caused improvement |
| Model validation | Purged walk-forward, nested selection and leakage guards | Demonstrated production-grade temporal evaluation judgment |
| Explainability | Evidence-backed reasons and source passages | Explanations trace to model inputs and source data |
| Responsible AI | Withheld states and no buy/sell output | Separated evidence, prediction and interpretation |
| Product analytics | Coverage, usage constraint and recommendation volume | Connected model quality with product behavior |
| Software engineering | Typed contracts, tests, CLI and generated artifacts | Shipped reproducible analysis rather than a one-off notebook |
| Communication | Company page, research view and concise case study | Explained technical work at recruiter and technical depth levels |

---

## 9. Portfolio and Interview Presentation

### 9.1 Recruiter-facing summary

> Built a source-backed company intelligence product that ranks SEC disclosures
> against each issuer's own history, predicts the calibrated probability of an
> unusually large reaction, and converts the result into a transparent reading
> recommendation supported by filing evidence.

### 9.2 DS-focused résumé bullets

- Built a point-in-time self-benchmarking system for SEC filings using issuer-relative
  features, temporal ranking and calibrated impact probabilities.
- Designed a capacity-aware recommendation policy that maps model probability,
  uncertainty and source-backed novelty into `Read now`, `Monitor`, `Routine` or
  abstention states.
- Combined structured filing and market features with financial-NLP change,
  extraction and embedding features; measured incremental value through temporal
  ablation studies.
- Prevented look-ahead bias with causal issuer histories, purged walk-forward
  validation, nested selection and automated leakage guards.

### 9.3 DSA-focused résumé bullets

- Translated an analyst's limited reading capacity into measurable ranking and
  recommendation KPIs, including precision@k, coverage, calibration and achievable
  ceiling.
- Built issuer-relative benchmarks that explain whether a filing is unusual for the
  same company rather than relying on opaque cross-company scores.
- Created auditable evidence artifacts, subgroup diagnostics and threshold-sensitivity
  analysis to support model and product decisions.
- Delivered the analysis through a source-backed company page with clear confidence,
  limitations and evidence links.

### 9.4 Five-minute demo

1. Open AAPL and state the product question.
2. Show the latest disclosure's `Read now / Monitor / Routine` status.
3. Explain the calibrated impact probability and AAPL historical base rate.
4. Show the current filing on the AAPL self-history chart.
5. Open one changed passage and one extracted financial fact.
6. Show one reliability curve or temporal fold result in the research view.
7. End with the boundary: attention prioritization and risk context, not price
   direction or investment advice.

---

## 10. Implementation Plan

## Phase 0 — Freeze contracts and evidence rules

Deliverables:

- written target definition;
- causal history rules;
- minimum-history and abstention policy;
- proposed snapshot fields;
- baseline list;
- evaluation plan; and
- leakage-test plan.

Exit criteria:

- target can be recomputed from committed or reproducible data;
- no current filing contributes to its own historical threshold;
- all user-visible terms have plain-language definitions.

## Phase 1 — Self-relative analytics

Deliverables:

- causal issuer-history builder;
- issuer percentiles and robust z-scores;
- minimum-history states;
- self-history research artifact;
- ranking evaluation; and
- tests for strict historical cutoffs.

Suggested module placement:

```text
src/filing_triage/self_relative.py
src/filing_triage/features.py
src/filing_triage/evaluate.py
tests/test_self_relative.py
```

Exit criteria:

- no future filing enters an issuer baseline;
- percentiles match manually verified examples;
- history-depth sensitivity is reported.

## Phase 2 — Calibrated impact model

Deliverables:

- issuer-relative target;
- pooled temporal model;
- calibration stage fitted without test-fold leakage;
- Brier score and reliability artifacts;
- subgroup diagnostics; and
- prediction contract.

Suggested module placement:

```text
src/filing_triage/calibration.py
src/filing_triage/model.py
src/filing_triage/pipeline.py
src/company_lens/contracts.py
tests/test_calibration.py
```

Exit criteria:

- probability estimates are evaluated on later unseen periods;
- calibration data is separate from final evaluation data;
- performance is reported by issuer-history depth and event type.

## Phase 3 — Recommendation policy

Deliverables:

- typed recommendation states;
- transparent threshold policy;
- recommendation-volume and coverage analysis;
- abstention behavior;
- case-review artifact; and
- snapshot integration.

Suggested module placement:

```text
src/filing_triage/recommend.py
src/company_lens/contracts.py
src/company_lens/snapshots/builder.py
tests/test_recommendation.py
```

Exit criteria:

- no state implies buy, sell or price direction;
- every non-routine state has at least one source-backed reason;
- thresholds are selected without reading the final test period.

## Phase 4 — Financial-NLP experiment

Deliverables:

- frozen labeled evaluation cases;
- transformer feature adapter;
- cached embeddings with model/version hashes;
- deterministic baseline versus transformer ablation;
- latency and failure-mode report; and
- provider-independent fallback.

Suggested module placement:

```text
src/company_lens/nlp/financial_transformer.py
src/company_lens/nlp/evaluation.py
src/filing_triage/features.py
tests/test_financial_transformer.py
```

Exit criteria:

- transformer features show measurable out-of-sample value or remain research-only;
- an unavailable model never blocks deterministic page generation;
- every extracted fact retains a source anchor.

## Phase 5 — Company-page integration

Deliverables:

- latest-disclosure decision card;
- self-history visualization;
- confidence and abstention states;
- concise methodology link;
- responsive and accessibility tests; and
- generated AAPL/MSFT/NVDA examples.

Suggested module placement:

```text
src/company_lens/web/page.py
src/company_lens/contracts.py
tests/test_company_page.py
tests/test_brief_mobile_layout.py
```

Exit criteria:

- recruiter can understand the card without knowing CAR, calibration or embeddings;
- technical reviewer can trace every displayed value to an artifact or source;
- the page remains useful when the prediction or LLM is unavailable.

## Phase 6 — Optional time-series foundation model

Deliverables:

- isolated optional dependency;
- reproducible Chronos-2 experiment;
- rolling-origin evaluation;
- quantile-coverage report;
- deterministic or classical fallback; and
- product card only if evidence supports it.

Suggested module placement:

```text
src/company_lens/performance/forecasting.py
scripts/evaluate_risk_forecast.py
tests/test_risk_forecast.py
```

Exit criteria:

- model weights and inference are optional;
- no live model call is required to render cached pages;
- forecast intervals have acceptable out-of-sample coverage;
- the page labels the output as historical risk forecasting, not expected return.

---

## 11. Scope Controls

### Build

- issuer-relative ranking;
- calibrated unusual-reaction probability;
- reading recommendation with abstention;
- financial-NLP feature ablation;
- one self-history visualization;
- generated evidence and evaluation artifacts; and
- optional volatility forecasting experiment.

### Keep but do not expand now

- existing Company Lens Q&A;
- news and market-context scopes;
- earnings calendar;
- bilingual explanation;
- broad issuer directory; and
- current model-family studies.

### Do not add

- buy/sell/hold recommendations;
- price targets;
- stock-direction forecasts;
- portfolio optimization;
- broker execution;
- reinforcement-learning trading;
- social-media signal ingestion;
- multi-agent investment committees;
- multiple time-series foundation models in the product; or
- an opaque combined score without component evidence.

---

## 12. Decision Gates

Each proposed capability must pass a gate before entering the company page.

| Capability | Ship when | Otherwise |
|---|---|---|
| Self-relative percentile | Causal audit passes and history-depth behavior is stable | Show raw evidence with insufficient-history state |
| Impact probability | Later-period calibration and discrimination are useful | Keep score research-only |
| Recommendation | Thresholds deliver acceptable precision, volume and coverage | Display probability without action label |
| Transformer NLP | Temporal ablation shows incremental value or clear extraction quality | Retain deterministic NLP |
| Foundation-model forecast | Interval coverage and latency are acceptable | Keep as notebook/technical experiment |
| LLM explanation | Citation and numeric validators pass | Use deterministic fallback |

---

## 13. Definition of Done

The DS/DSA extension is complete when:

- the company page answers whether the latest filing is unusual for that company;
- issuer-relative features use only strictly earlier information;
- the impact output is a calibrated probability, not an unbounded model score;
- the recommendation is about reading priority, not investment action;
- insufficient history and failed validation produce explicit abstention;
- structured, deterministic-text and transformer-text feature groups have a temporal
  ablation study;
- performance is reported against operational and statistical baselines;
- calibration, coverage, subgroup and threshold-sensitivity artifacts are committed;
- every displayed reason traces to a deterministic feature or cited filing passage;
- the existing Filing Triage and Company Lens paths continue to work;
- tests, lint and end-to-end page generation pass; and
- the five-minute demo communicates one product question and the DS decisions behind
  it without touring every feature.

---

## 14. Recommended Delivery Order

1. Causal self-relative history and percentiles.
2. Issuer-relative prediction target.
3. Calibrated pooled model.
4. Recommendation and abstention policy.
5. Evaluation artifacts and research view.
6. Company-page decision card and self-history chart.
7. Financial-transformer feature experiment.
8. Optional Chronos-2 volatility experiment.

Do not start with the foundation model. The strongest DS story is the causal target,
operational metric, calibration, recommendation policy and honest evaluation. The
foundation model is valuable only after those foundations are working.
