# Reference Architecture Mapping

> **Status:** Verified study notes · **Date:** 2026-07-28  
> **Authority:** Conceptual guidance only — does not change frozen Architecture Bible decisions  
> **Local clones:** `…/demos/references/` (sibling of `ai-quant-signal-platform`, not a submodule)

## Scope

These five repositories are **read-only architectural references**. They are:

- cloned **outside** `ai-quant-signal-platform`;
- **not** Git submodules;
- **not** application dependencies;
- **not** installed into the project virtualenv for this review;
- **not** vendored into the application tree.

No large source blocks are copied into this document or into application modules. Ideas are reimplemented in the project’s modular-monolith style when adopted.

Verified local availability (shallow clones, 2026-07-28):

| Repository | Local path | Branch | Commit |
|---|---|---|---|
| microsoft/qlib | `demos/references/qlib` | `main` | `79633dd9506ea689e5400dea0197717b5b3d74b7` |
| stefan-jansen/machine-learning-for-trading | `demos/references/machine-learning-for-trading` | `main` | `d1ec72aff04f9c0969dc97b3fd1888d1fca03cd0` |
| AI4Finance-Foundation/FinRL-Trading | `demos/references/finrl-trading` | `master` | `e65d6f0483ead7d2ef4a5fc940cdf960392a25c1` |
| HKUDS/Vibe-Trading | `demos/references/vibe-trading` | `main` | `715ea33b664a0eb55e413cbdef950e0bbb1ee7f3` |
| TauricResearch/TradingAgents | `demos/references/trading-agents` | `main` | `a33fd4c0f134485a43553a2c23a63cb14adbd88f` |

---

## Qlib

### Files reviewed

| Path (relative to `references/qlib/`) | Role |
|---|---|
| `LICENSE` | MIT |
| `qlib/data/dataset/handler.py` | `DataHandlerLP` — learn vs infer processor chains (`DK_L` / `DK_I`) |
| `qlib/data/dataset/__init__.py` | `DatasetH.prepare(segments, …)` |
| `qlib/contrib/data/handler.py` | `Alpha158` / `Alpha360` concrete handlers |
| `qlib/model/base.py` | `Model.fit(dataset)` / `predict(dataset, segment)` |
| `qlib/contrib/model/xgboost.py` | Example fit/predict → score `Series` |
| `qlib/backtest/signal.py` | `Signal` / `ModelSignal` / `create_signal_from` |
| `qlib/contrib/strategy/signal_strategy.py` | `TopkDropoutStrategy` |
| `qlib/backtest/backtest.py`, `qlib/backtest/__init__.py` | `backtest_loop` public wiring |
| `qlib/workflow/recorder.py` | Experiment recorder |
| `qlib/workflow/record_temp.py` | `SignalRecord` → `SigAnaRecord` → `PortAnaRecord` |
| `qlib/workflow/task/gen.py` | `RollingGen` expanding/sliding segments |
| `qlib/contrib/rolling/base.py` | Offline rolling runner |

### Patterns worth borrowing

- Dataset / handler / model separation with explicit segments.
- Learn-vs-infer preprocessing split (`DataHandlerLP`).
- Prediction as a **score artifact** (indexed date×instrument), not a live model call.
- Rank/IC analysis of scores before portfolio simulation (`SigAnaRecord`).
- Top-K as a **strategy boundary** consuming scores (Phase 4), not as Phase 3 truth.
- Rolling / expanding segment generation (`RollingGen`) as a walk-forward analogue.

### Patterns not to borrow

- Full MLflow-coupled experiment OS and stringy `init_instance_by_config` DI.
- Alpha158/360 / CN market defaults as product semantics.
- Nested exchange / order-level backtest as the research spine.
- Online rolling / RL stacks.
- Prediction-as-trading-authority without Validation/Governance gates.

### Mapping to this project

| Qlib concept | Our mapping |
|---|---|
| Handler + DatasetH | `cross_sectional/` panel + future train-only preprocessors |
| Model.fit/predict + score | `cross_sectional/modeling/` (Phase 3) |
| SigAnaRecord | Extend Phase 2 RankIC on **predictions** |
| TopkDropoutStrategy | Future portfolio Top-K (Phase 4) |
| PortAnaRecord / backtest_loop | Future `portfolio_backtest/` (Phase 5) |
| Recorder | Reproducibility manifests + evidence snapshots (existing) |

---

## Machine Learning for Trading

### Files reviewed

| Path (relative to `references/machine-learning-for-trading/`) | Role |
|---|---|
| `LICENSE` | MIT |
| `utils/cv_splits.py` | Calendar-aware walk-forward + purge/embargo via `WalkForwardCV` |
| `utils/modeling.py` | `WalkForwardConfig`; train-only `fit_transform` / `transform` per fold |
| `utils/README.md` | Declares `utils/` as shared importable code |
| `06_strategy_definition/02_cv_foundations.py` | Purge vs embargo; anti-shuffled-KFold teaching |
| `07_defining_the_learning_task/02_preprocessing_pipeline.py` | Pedagogical train-only preprocessor |
| `07_defining_the_learning_task/05_signal_evaluation.py` | Factor IC; pooled vs cross-sectional RankIC |
| `07_defining_the_learning_task/06_ic_inference.py` | IC inference caveats |
| `11_ml_pipeline/04_nested_cv_hpo.py` | Nested WF + per-fold scaler + CS Spearman IC |
| `11_ml_pipeline/08_ml_backtest_intro.py` | Case-study WF + train-only scale + CS IC series |
| `case_studies/utils/registry/metrics.py` | Fold CS Spearman IC of preds vs forward returns |
| `tests/test_leakage_detectors.py` | AST leakage detectors for chapter scripts |

### Patterns worth borrowing

- Chronological / walk-forward splits with label-horizon embargo.
- Train-only preprocessing fitted inside each fold.
- Cross-sectional RankIC of **predictions vs continuous forward returns** (not binary labels).
- Explicit anti-patterns: shuffled KFold, pooled IC as primary ranking metric, full-sample scaling.
- Leakage tests as Validation gates (ideas), not their AST allowlists.

### Patterns not to borrow

- Live broker / paper trading path (`25_live_trading/`).
- RL execution chapters as product surface.
- Notebook-local WF that diverges from a single setup contract.
- External `ml4t.*` library as a runtime dependency.
- Autonomous research-operator agents that mutate strategy state.

### Mapping to this project

| ML4T concept | Our mapping |
|---|---|
| `setup.yaml` / WalkForwardConfig | Phase 3 training protocol + reproducibility fields |
| Train-only preprocess | Phase 3 preprocessor fit on train window only |
| CS IC of predictions | Phase 3 model evaluation (extends Phase 2 RankIC engines) |
| Leakage tests | Phase 3 Validation tests |
| Portfolio chapters | Phase 4–5 evaluation metrics only |

---

## FinRL-Trading

### Files reviewed

| Path (relative to `references/finrl-trading/`) | Role |
|---|---|
| `LICENSE` | Apache-2.0 |
| `examples/weight_allocation_guide.md` | Weight-centric contract narrative |
| `src/strategies/base_strategy.py` | `generate_weights` → `StrategyResult` |
| `src/strategies/ml_strategy.py` | Equal / min-variance allocation |
| `src/strategies/AdaptiveRotationConf_v1.2.2.yaml` | Caps, cash_floor, group budgets |
| `src/strategies/adaptive_rotation/portfolio_builder.py` | Constraint application + audit metadata |
| `src/strategies/adaptive_rotation/risk_manager.py` | Post-signal risk overlay |
| `src/strategies/adaptive_rotation/walk_forward.py` | PIT walk-forward slicing |
| `src/backtest/backtest_engine.py` | Weight schedule → metrics |

### Patterns worth borrowing

- Score → weights interface with explicit metadata.
- Deterministic concentration / cash / group caps (Phase 4).
- Risk overlay as a separate step after scores (governance-owned rules).
- Backtest consumes weights, not model objects.

### Patterns not to borrow

- DRL / gym environments.
- Live Alpaca / broker execution.
- Stop-loss as substitute for research governance.
- Random position culling.

### Mapping to this project

| FinRL concept | Our mapping |
|---|---|
| `generate_weights` | Phase 4 portfolio construction from Phase 3 scores |
| Constraint YAML | Phase 4 deterministic constraint policies |
| `BacktestEngine` | Phase 5 portfolio backtest ports |
| RL / trading | **Out of scope** |

Phase 3 relevance: **low–medium** (score contract only; no RL).

---

## Vibe-Trading

### Files reviewed

| Path (relative to `references/vibe-trading/`) | Role |
|---|---|
| `LICENSE` | MIT |
| `agent/backtest/run_card.py` | `write_run_card` — hashes, schema_version, artifacts |
| `agent/backtest/validation.py` | Statistical validation package (adjacent) |
| `frontend/src/pages/RunDetail.tsx` | Evidence panes (metrics / validation / run card / code) |
| `frontend/src/pages/Compare.tsx` | Multi-run compare UX |
| `frontend/src/components/chat/RunCompleteCard.tsx` | Run completion surface |
| `agent/src/hypotheses/` | Hypothesis registry (lifecycle reference) |
| `agent/src/swarm/grounding.py` | Inject approved market facts before LLM |

### Patterns worth borrowing

- Run-card style reproducibility: config/strategy hashes, artifact checksums, warnings.
- Separation of definition / execution / results / review in UX.
- Grounding: LLM consumes approved facts only.

### Patterns not to borrow

- Chat-as-system-of-record.
- Broker / live mandate path.
- Auto strategy codegen as quantitative truth.
- Bundled alpha-zoo / skill sprawl as architecture.

### Mapping to this project

| Vibe concept | Our mapping |
|---|---|
| Run card | Extend reproducibility manifests + research_run_id artifacts |
| RunDetail tabs | Existing Research Workspace tabs evolution (not redesign now) |
| Grounding | Agent Runtime / later interpretation (not Phase 3 scoring) |

---

## TradingAgents

### Files reviewed

| Path (relative to `references/trading-agents/`) | Role |
|---|---|
| `LICENSE` | Apache-2.0 |
| `tradingagents/agents/schemas.py` | Structured analyst / PM schemas |
| `tradingagents/agents/utils/structured.py` | Structured output helpers |
| `tradingagents/agents/utils/market_data_validation_tools.py` | `get_verified_market_snapshot` |
| `tradingagents/agents/analysts/market_analyst.py` | Tool-bounded market analyst |
| `tradingagents/graph/analyst_execution.py` | `AnalystNodeSpec` role plan |
| `tradingagents/graph/trading_graph.py` | Graph wiring (incl. verified snapshot tools) |
| `tradingagents/dataflows/interface.py` | Vendor-routed data ports |
| `tradingagents/reporting.py` | Sectioned report tree |

### Patterns worth borrowing

- Bounded analyst roles with isolated tool surfaces.
- Deterministic verification snapshot as numeric SoT candidate.
- Structured interpretive schemas that **label interpretation**, not invent metrics.

### Patterns not to borrow

- Trader / PM as decision authority.
- Bull/Bear debate as Validation substitute.
- LLM-authored prices, stops, scores as truth.
- Memory of past LLM decisions driving the next trade.

### Mapping to this project

| TradingAgents concept | Our mapping |
|---|---|
| Bounded analysts | Later Market Intelligence interpretation layer |
| Verified snapshot | Align with `MarketDataPort` provenance |
| PM / Trader autonomy | **Forbidden** |

Phase 3 relevance: **low** (interpretation later; must not compute scores).

---

## Final Decision Matrix

| Capability | Primary Reference | Secondary Reference | Our Implementation Decision |
|---|---|---|---|
| Factor panel | Qlib | ML for Trading | Reimplement within `cross_sectional/` (Phase 1 done) |
| RankIC / quintiles | ML for Trading | Qlib | Deterministic research service (Phase 2 done) |
| Time-aware model validation | ML for Trading | Qlib | Phase 3 done — `modeling/splits.py` expanding WF + purge |
| Train-only preprocessing | ML for Trading | Qlib `DataHandlerLP` | Phase 3 done — `modeling/preprocessing.py` |
| Ridge / LightGBM baselines | Qlib model port | ML for Trading Ch11/12 | Phase 3 done — `modeling/ridge.py`, `lightgbm_model.py` |
| Stock-score contract | Qlib Signal | — | Phase 3 done — `modeling/prediction.py` |
| Prediction RankIC | ML for Trading | Qlib SigAna | Phase 3 done — `modeling/evaluation.py` + narrow `rank_ic._spearman` |
| Top-K portfolio | Qlib | FinRL-Trading | Phase 4 |
| Portfolio constraints | FinRL-Trading | Qlib | Phase 4 |
| Portfolio backtest | FinRL / Qlib | ML4T Ch16 | Phase 5 |
| Research lifecycle / run cards | Vibe-Trading | Qlib recorder | Existing workspace + manifests |
| LLM research analysts | TradingAgents | Vibe grounding | Later bounded interpretation only |

---

## Phase 3 relevance review

Concrete recommendations for **model training and scoring only**. Each pattern was verified in local source files.

### 1. Chronological train / validation / test splitting

1. **Source:** Machine Learning for Trading  
2. **Path:** `utils/cv_splits.py` (`generate_cv_splits`), `utils/modeling.py` (`WalkForwardConfig`)  
3. **Does:** Builds calendar-aware folds with train before validation.  
4. **Useful:** Prevents random shuffle leakage on panels.  
5. **Adapt:** Reimplement inside our Validation/Research ports; do not depend on `ml4t.diagnostic`.  
6. **Do not copy:** External library classes or notebook ad-hoc split helpers.

### 2. Walk-forward / expanding-window evaluation

1. **Source:** Qlib + ML4T  
2. **Path:** `qlib/workflow/task/gen.py` (`RollingGen`); ML4T `06_strategy_definition/02_cv_foundations.py`  
3. **Does:** Rolls or expands train windows; holds out later test segments.  
4. **Useful:** Matches OOS honesty already used in Trend study.  
5. **Adapt:** Small pure Python splitter over our long panel dates; expanding window first.  
6. **Do not copy:** Qlib online `RollingStrategy` or MLflow task graph.

### 3. Embargo / purge between train and test

1. **Source:** ML4T  
2. **Path:** `utils/cv_splits.py` (purge helpers); `06_strategy_definition/02_cv_foundations.py`  
3. **Does:** Gaps train labels from validation by ≥ label horizon.  
4. **Useful:** Forward labels (`forward_return_5d/20d`) overlap risk.  
5. **Adapt:** Configurable embargo days = label horizon (5 or 20).  
6. **Do not copy:** CPCV complexity for the first Phase 3 slice.

### 4. Train-only preprocessing

1. **Source:** Qlib + ML4T  
2. **Path:** `qlib/data/dataset/handler.py` (`DataHandlerLP`); ML4T `utils/modeling.py` fold `fit_transform`/`transform`  
3. **Does:** Fits winsorize/z-score on train; applies to val/test.  
4. **Useful:** Phase 1 already deferred full-panel normalize.  
5. **Adapt:** Simple CS rank/z-score fitted per train date-set only.  
6. **Do not copy:** Full Alpha handler processor graphs.

### 5. Ridge baseline + LightGBM

1. **Source:** Qlib model port pattern; existing repo `backend/app/models/` is **single-name** — do not reuse as CS ranking  
2. **Path:** `qlib/model/base.py`; optional glance `qlib/contrib/model/xgboost.py`  
3. **Does:** `fit(dataset)` / `predict` → scores.  
4. **Useful:** Clear baseline vs non-linear comparison.  
5. **Adapt:** New Phase 3 trainers on long panel; sklearn Ridge + LightGBM regressor/ranker as chosen by tests.  
6. **Do not copy:** Entire `contrib/model/pytorch_*` zoo or single-name `model_comparison` path.

### 6. Cross-sectional prediction / daily stock-score contract

1. **Source:** Qlib  
2. **Path:** `qlib/backtest/signal.py`; `qlib/workflow/record_temp.py` (`SignalRecord`)  
3. **Does:** Materializes scores as date×instrument artifacts with metadata.  
4. **Useful:** Separates training from later Top-K.  
5. **Adapt:** Fields: `date`, `symbol`, `raw_prediction`, `percentile_score`, `model_rank`, `model_name`, `model_version`, `training_cutoff`, `feature_version`, `score_as_of`. No fake confidence.  
6. **Do not copy:** `ModelSignal` live predict-in-backtest coupling for Phase 3 API.

### 7. RankIC evaluation of predictions

1. **Source:** ML4T + our Phase 2  
2. **Path:** ML4T `case_studies/utils/registry/metrics.py`; our `cross_sectional/research/rank_ic.py`  
3. **Does:** Per-date Spearman(pred, forward return).  
4. **Useful:** Same metric family as factor research; comparable evidence.  
5. **Adapt:** Call Phase 2 RankIC engines with `factor=raw_prediction`.  
6. **Do not copy:** Pooled IC or IC vs binary labels.

### 8. Model / feature version metadata + training cutoff + reproducibility

1. **Source:** Vibe-Trading run cards + our manifests  
2. **Path:** `vibe-trading/agent/backtest/run_card.py`; our `research_reproducibility`  
3. **Does:** Hashes config/strategy; records schema version and warnings.  
4. **Useful:** Interview-friendly audit trail.  
5. **Adapt:** Extend reproducibility manifest with model_version, feature_version, training_cutoff, seed.  
6. **Do not copy:** Vibe chat/agent memory as research truth.

### 9. No random shuffle / no future leakage

1. **Source:** ML4T teaching + tests  
2. **Path:** `06_strategy_definition/02_cv_foundations.py`; `tests/test_leakage_detectors.py`  
3. **Does:** Documents and guards anti-patterns.  
4. **Useful:** Aligns with authenticity policy.  
5. **Adapt:** Pytest fixtures asserting date order, embargo, mutate-future-price leakage tests.  
6. **Do not copy:** Their AST detector allowlists.

---

## License review

| Repository | License (verified from `LICENSE`) | Use in this project | Code copied into app? | Attribution if incorporated |
|---|---|---|---|---|
| Qlib | MIT (Microsoft) | Conceptual reference only | **No** | Retain MIT notice if any code were later incorporated (none today) |
| Machine Learning for Trading | MIT (Stefan Jansen) | Conceptual reference only | **No** | Same |
| FinRL-Trading | Apache-2.0 | Conceptual reference only | **No** | Apache NOTICE if later incorporated (none today) |
| Vibe-Trading | MIT | Conceptual reference only | **No** | Same |
| TradingAgents | Apache-2.0 | Conceptual reference only | **No** | Same |

**Verified statement:** No source code from these five repositories has been copied into `ai-quant-signal-platform` application modules. Architectural concepts are reimplemented independently for Phases 1–3. Prior study notes live only under `demos/references/ARCHITECTURAL_COMPARISON.md` (outside the main repo).

---

## Main repository cleanliness

Verified 2026-07-28:

- No `references/` directory inside `ai-quant-signal-platform`.
- `git ls-files` contains **no** qlib / finrl / vibe-trading / tradingagents / ML4T paths.
- Only one `.git` under the main project (the project itself).
- No `import qlib` / `from finrl` / `tradingagents` / `ml4t.` in `backend/` or `frontend/`.
- Reference clones remain at `demos/references/` (sibling). No dependency packages added for this review.
- `.gitignore` entry for sibling `references/` is unnecessary (path is outside the Git root). Documented here so clones are not later dragged inside the tree.

---

## Phase 3 implementation mapping (implemented)

Package: `backend/app/cross_sectional/modeling/`  
API: `POST /api/v1/research/cross-sectional/models`  
ADR: `docs/adr/ADR-0013-cross-sectional-modeling-and-stock-scores.md`

| Adopted concept | Reference repo | Exact relative path inspected | Adaptation in this project | Deliberately not copied |
|---|---|---|---|---|
| Dataset / model / score separation | Qlib | `qlib/model/base.py`, `qlib/backtest/signal.py` | Modeling service consumes Phase 1 panel; emits score table; no strategy | `ModelSignal`, backtest loop, Alpha158 |
| Expanding / rolling segments | Qlib | `qlib/workflow/task/gen.py` (`RollingGen`) | `splits.build_expanding_walk_forward_folds` | Online rolling / MLflow task graph |
| Learn-vs-infer preprocess | Qlib | `qlib/data/dataset/handler.py` (`DataHandlerLP`) | `TrainOnlyPreprocessor` fit on train / purged refit only | Full processor graphs; CS z-score auto |
| Walk-forward + purge | ML for Trading | `utils/cv_splits.py`, `06_strategy_definition/02_cv_foundations.py` | Trading-row purge `i_max = start_idx - H - 1` | CPCV; their AST detectors |
| Train-only scale | ML for Trading | `utils/modeling.py` | Ridge StandardScaler train-only | Notebook pipelines |
| Prediction CS IC | ML for Trading | `case_studies/utils/registry/metrics.py` | `evaluation.py` + Phase 2 `_spearman` / `summarize_rank_ic` | Pooled IC |
| Run / artifact identity | Vibe-Trading | `agent/backtest/run_card.py` | `fit_id`, fold metadata, `ValidationResultStore` summary | Chat memory as truth |
| Score→weights boundary | FinRL-Trading | (deferred) | Documented as Phase 4 only | RL, portfolio actions |
| Agent interpretation | TradingAgents | (deferred) | Agents must not train/score/approve | Multi-agent debate as scorer |

### Rejected for Phase 3

- FinRL RL / portfolio construction
- TradingAgents LLM as model authority
- Qlib TopkDropoutStrategy (Phase 4)
- Random KFold / Optuna / AutoML / XGBoost substitute

```text
backend/app/cross_sectional/
  (Phase 1 dataset modules)
  research/                   # Phase 2 — preserved
  modeling/                   # Phase 3 — implemented
    constants.py
    eligibility.py
    splits.py
    preprocessing.py
    ridge.py
    lightgbm_model.py
    prediction.py
    evaluation.py
    comparison.py
    metadata.py
    schemas.py
    service.py
backend/app/api/routes/cross_sectional_models.py
```

Preserve: Phase 1 panel, Phase 2 factor research, Trend study, ADR-0008 factor validation, authenticity rules (LLM never scores).
Do **not** begin Phase 4 in this package.
