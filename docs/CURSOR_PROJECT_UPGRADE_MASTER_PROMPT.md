# Cursor Master Prompt — AI Quant Research Workspace vNext

Copy everything below into Cursor Agent mode from the repository root.

---

You are upgrading the repository `josephwang-ds/ai-quant-signal-platform`.

Your job is to implement the next production-quality iteration of the project, not to create another visual redesign or a collection of placeholders. Work through the phases below in order. Inspect the existing code and tests before editing. Preserve all unrelated user changes in the worktree.

## 0. Product thesis and non-negotiable boundaries

This product is an **evidence-governed quantitative research operating system**:

```text
Research
→ Experiment
→ Validation
→ Robustness
→ Paper Observation
→ Human Decision
```

It is not:

- a broker;
- an OMS;
- a live-trading terminal;
- an autonomous stock-picking agent;
- a place to show fabricated performance, P&L, fills, confidence, or approval.

Maintain these authority boundaries:

1. Deterministic backend services own all financial calculations.
2. Validation rules own pass/fail/inconclusive states.
3. The LLM may explain supplied evidence but may not calculate financial truth.
4. The Governance Agent coordinates registered tools only.
5. Human users own final `Promote / Hold / Reject / Archive` decisions.
6. Missing evidence must remain missing. Never convert unavailable values to zero.

The canonical trend study remains:

- research id: `ma-crossover-spy`
- symbol: `SPY`
- strategy: MA20/MA60 crossover
- benchmark: same-asset Buy & Hold
- start: `2018-01-01`
- transaction cost: `0.001` per unit position change
- one-day signal lag

The canonical factor studies remain:

- US sector ETF universe
- Momentum: 12-1 monthly momentum
- Low Volatility: negative 60-day realized volatility
- monthly rebalance
- one-month forward return
- RankIC and Q1–Q5 evidence

Do not change metric definitions merely to improve displayed results.

## 1. Working rules

Before changing code:

1. Read `README.md`, `docs/PROJECT_STORY.md`, `docs/ARCHITECTURE.md`,
   `docs/RESEARCH_WORKFLOW.md`, `docs/AGENT_GOVERNANCE.md`,
   `docs/AUTHENTICITY.md`, and `docs/KNOWN_LIMITATIONS.md`.
2. Inspect `git status`; preserve all existing modifications.
3. Locate repository-specific instructions such as `AGENTS.md` or Cursor rules.
4. Map current frontend routes, backend routes, stores, and database repositories.
5. Run the existing non-live backend suite and frontend suite before editing.
6. Record the baseline result. Do not “fix” a failing test by weakening it.

Implementation rules:

- Make small cohesive changes.
- Add migrations rather than editing production data manually.
- Keep API schemas strict and versioned.
- Use UTC timestamps.
- Use opaque IDs, idempotency keys, and append-only records where evidence lineage matters.
- Never put provider or LLM secrets in the browser.
- Never silently fall back from a failed real provider to fixtures or demo metrics.
- Do not add a disabled card for future functionality. Either implement it or list it in a compact scope-boundary disclosure.
- Keep the current Apple-inspired Bento visual language, but prioritize information hierarchy, accessibility, and workflow clarity.

After every phase:

- run focused backend tests;
- run focused frontend tests;
- run the complete non-live suites;
- run frontend type-check/build;
- update relevant documentation;
- provide a concise change summary and remaining limitations.

## 2. Target architecture

Move the current modular monolith toward this deployable shape without a big-bang rewrite:

```text
Next.js UI
  ├─ Research workspace
  ├─ Evidence views
  ├─ Governance Agent review
  └─ Human-authored observation and decision forms
          ↓ typed HTTP contracts
FastAPI application
  ├─ Research definition service
  ├─ Execution service
  ├─ Validation service
  ├─ Robustness service
  ├─ Factor validation service
  ├─ Evidence snapshot service
  ├─ Governance Agent service
  └─ Decision / observation service
          ↓ ports
Infrastructure
  ├─ Yahoo / AkShare adapters
  ├─ Postgres repositories
  ├─ optional LLM adapter
  └─ structured logging / telemetry
```

The frontend must never reconstruct authoritative metrics or create a second
conflicting decision policy. Presentation-only projections are allowed when
they directly reflect backend evidence.

## Phase 1 — Durable research and evidence lineage

### Goal

Remove the largest credibility and reliability gap: process-local validation,
Agent, observation, and decision state.

### Required domain records

Create durable schemas/repositories for:

1. `research_definitions`
   - `research_id`
   - `research_type`
   - version
   - question
   - hypothesis
   - null hypothesis
   - mechanism
   - benchmark
   - outcome metrics
   - active success criteria
   - evaluation period
   - symbol or universe
   - run configuration JSON
   - known limitations
   - created/updated timestamps

2. `validation_runs`
   - opaque `validation_run_id`
   - research id and definition version
   - evidence kind
   - status
   - generated timestamp
   - complete normalized result JSON
   - provider provenance
   - code/research-rule version
   - optional request id / correlation id

3. `evidence_snapshots`
   - immutable snapshot id
   - validation run id
   - research id
   - deterministic availability map
   - metric references
   - evidence IDs
   - methodology version IDs
   - generated timestamp
   - content hash

4. `agent_runs`
   - agent run id
   - research id
   - intent
   - graph and prompt versions
   - current status/node
   - normalized trace
   - requested tools and results
   - approval state
   - evidence snapshot id
   - LLM availability/provider/model metadata
   - errors
   - created/updated/completed timestamps

5. `paper_observation_sessions`
   - session id
   - research id
   - evidence snapshot id at start
   - cadence
   - minimum days
   - exit criteria
   - active/completed status
   - timestamps

6. `paper_observation_entries`
   - append-only entry id
   - session id
   - observed timestamp
   - human note
   - optional structured fields only when truly entered by the user

7. `decision_records`
   - append-only decision id
   - research id
   - evidence snapshot id
   - agent run id when applicable
   - deterministic suggestion
   - human decision
   - human rationale
   - override rationale when decision differs from suggestion
   - actor identifier when authentication exists
   - recorded timestamp

### Persistence behavior

- Prefer configured Postgres/Supabase.
- Preserve a clearly labelled local development fallback only if required.
- Production must report whether durable persistence is available.
- Do not pretend that an in-memory fallback is durable.
- Reads must enforce research-id ownership of referenced validation and evidence IDs.
- Evidence snapshots and decisions are immutable. Corrections create a new record.
- Add idempotency support for run creation and decision submission.
- Add repository interfaces so application services do not contain SQL.
- Add migrations and repository tests.

### API work

Add or normalize routes for:

- research definition get/list/create/update-as-new-version;
- validation run get;
- evidence snapshot get/list-for-research;
- Agent run get/resume;
- observation session start/get/add-entry/complete;
- decision create/list;
- persistence capability/status.

Return typed error codes such as:

- `PERSISTENCE_UNAVAILABLE`
- `VALIDATION_RUN_NOT_FOUND`
- `EVIDENCE_RESEARCH_MISMATCH`
- `IDEMPOTENCY_CONFLICT`
- `DECISION_OVERRIDE_RATIONALE_REQUIRED`

### Frontend migration

- Introduce repository adapters for remote persistence.
- Migrate existing browser-local research definitions, observation sessions,
  and decisions once when durable persistence is available.
- Keep local data intact until server persistence confirms success.
- Show a small `Saved to workspace` / `Browser only` provenance label.
- Do not make persistence internals visually dominant.

### Acceptance criteria

- A Render restart does not invalidate a persisted validation run, evidence
  snapshot, Agent run, observation session, or decision.
- A decision always references the exact evidence snapshot reviewed.
- Cross-research ID substitution is rejected.
- Duplicate submission with the same idempotency key is safe.
- Browser-local migration is tested.
- The UI never says “saved” when only an in-memory store accepted the record.

## Phase 2 — Evidence snapshot and reproducibility contract

### Goal

Make every research result reproducible and reviewable as a single immutable
artifact.

### Add to every snapshot

- canonical research id and definition version;
- strategy parameters;
- requested and actual data bounds;
- provider, adapter, provider symbol, adjustment mode, cache state;
- row count;
- data fingerprint/hash;
- calculation engine version;
- rulebook version;
- repository commit SHA when available;
- transaction-cost and risk-free-rate assumptions;
- benchmark definition;
- metric definition version;
- warnings, blockers, unavailable fields;
- generated timestamp.

### Metric registry

Create one backend metric-definition registry for reader-facing metadata:

- metric id;
- label in English and Chinese;
- formula description;
- unit;
- favorable direction, if any;
- valid range, if bounded;
- interpretation;
- caveat.

Cover:

- total return;
- CAGR;
- annualized volatility;
- Sharpe ratio;
- maximum drawdown;
- trade count;
- win rate;
- turnover;
- transaction costs;
- exposure;
- downside capture;
- benchmark deltas;
- OOS deltas;
- parameter sensitivity summaries;
- cost degradation;
- RankIC / ICIR / positive IC ratio;
- quantile returns and Q5−Q1;
- directional accuracy;
- evidence coverage;
- workflow completion.

The frontend should fetch or share this registry rather than maintain
inconsistent tooltip prose across screens.

### Acceptance criteria

- A reviewer can identify exactly which data, parameters, code, and definitions
  produced a displayed number.
- Downloaded JSON contains no `NaN` or infinity.
- Metric tooltips use the same definitions as the calculation engine.
- `coverage` and `workflow completion` explicitly say they are not confidence.

## Phase 3 — Stronger trend robustness evidence

### Goal

Turn current scope boundaries into real engines one at a time, while preserving
the distinction between implemented evidence and roadmap.

Implement in this order:

### 3.1 Walk-forward validation for the canonical trend strategy

- Use chronological folds.
- Support expanding and rolling training/history windows where meaningful.
- Keep MA parameters fixed unless a nested train-only selection protocol is
  explicitly chosen.
- Apply an embargo at label/evaluation boundaries.
- Preserve position and turnover boundary semantics.
- Aggregate only OOS fold rows.
- Report per-fold and aggregate metrics.
- Report fold dispersion for Sharpe, return, drawdown, and exposure.
- Do not cherry-pick the best fold.

### 3.2 Regime analysis

Use deterministic, documented regimes based on information available at each
date. Start with simple ex-post review labels, clearly marked as diagnostic:

- bull/bear using a long moving-average state;
- high/low volatility using a rolling realized-volatility threshold calculated
  without future data.

Report strategy and benchmark metrics by regime, observation counts, and the
regime-definition limitation. Do not claim causal performance.

### 3.3 Bootstrap / Monte Carlo uncertainty

- Prefer block bootstrap over IID bootstrap for daily returns.
- Use a fixed random seed for reproducibility.
- Report distributions and percentile intervals for return, Sharpe, and
  maximum drawdown.
- State that resampling historical returns is not a forecast.
- Do not output a fake “probability of success.”

### 3.4 Liquidity and capacity approximation

Only implement if required volume data is available:

- average daily dollar volume;
- assumed participation rate;
- estimated notional capacity;
- turnover-aware trading notional;
- simple spread/slippage scenario assumptions.

Mark it unavailable when volume or currency metadata is inadequate.

### Acceptance criteria

- Each new engine has a pure calculation module and fixture-based tests.
- No new method appears as completed before successful calculation.
- Robustness UI separates result, method, limitation, and next action.
- The decision policy consumes configured core checks without treating every
  supporting diagnostic as a hard gate.

## Phase 4 — Stronger factor research

### Goal

Advance the factor path from a convincing small-universe demonstration toward
a more research-grade contract.

Implement:

1. configurable but bounded universes;
2. explicit universe version and membership provenance;
3. minimum cross-section checks per date;
4. factor coverage percentage per rebalance;
5. optional winsorization and cross-sectional z-score, fit at each date only;
6. optional sector neutralization only when sector metadata is available;
7. Newey-West or another documented uncertainty estimate for mean IC;
8. top-minus-bottom spread confidence interval;
9. turnover and cost sensitivity;
10. subperiod and rolling RankIC stability;
11. missing-symbol and stale-price diagnostics.

Do not claim that the static sector ETF preset reconstructs historical index
membership. Do not expose the unimplemented Value factor as selectable.

### Acceptance criteria

- Q5 always means strongest expected exposure, including Low Volatility after
  direction normalization.
- Formation information never includes forward return.
- At least five valid names are required for Q1–Q5.
- RankIC remains Spearman cross-sectional correlation.
- Every factor result includes universe and factor-definition provenance.

## Phase 5 — Model comparison reliability

### Goal

Make Compare Models fail softly, remain fair, and explain what is actually
being compared.

### Required changes

- Add a model-capability endpoint returning availability and reason for every
  registry model.
- If LightGBM, XGBoost, statsmodels, SHAP, or an offline artifact is missing,
  mark only that model/method unavailable. Do not fail the whole comparison.
- Keep all successful models and rule baselines on the identical OOS interval.
- Keep chronological split, train-only scaler/preprocessing, and one-row
  embargo.
- Keep walk-forward as the preferred evaluation mode.
- Show fold dispersion, not only aggregate champions.
- Add class-balance and trivial majority-direction baseline.
- Add balanced accuracy and optionally ROC AUC only where probabilities and
  both classes exist; mark unavailable otherwise.
- Keep portfolio metrics as the decision-relevant evidence.
- Keep directional accuracy labelled as a next-day hit rate, not a return
  promise.
- Preserve feature-importance caveats.

### Statistical guardrails

- Random-walk leakage smoke test must remain near chance.
- No randomized KFold.
- Hyperparameter search stays inside training data with `TimeSeriesSplit`.
- Limit search spaces and report tuning metadata.
- Never select a model using final OOS results and then report the same OOS
  result as unbiased.

### Feature interpretation

- Native importance: tree gain/importance or normalized absolute coefficient.
- Permutation importance: held-out diagnostic.
- SHAP: optional, tree-only, unavailable if dependency is absent.
- Signed linear coefficients: separate magnitude and direction.
- Walk-forward stability: preserve per-fold CV and rank variation.
- Add feature correlation/redundancy view if it can be implemented without
  making causal claims.

### Acceptance criteria

- Missing LightGBM no longer returns a 500 for all models.
- Every result declares model paradigm, feature usage, split, preprocessing,
  tuning status, and OOS dates.
- UI supports partial success with explicit unavailable rows.
- “Best” labels are descriptive summaries, not promotion decisions.

## Phase 6 — Governance Agent hardening

### Goal

Make the Agent auditable, durable, bounded, and demonstrably subordinate to
deterministic evidence.

### Preserve

- LangGraph controlled workflow;
- maximum 24 graph nodes;
- maximum 8 planned tool calls;
- registered tools only;
- approvals for expensive and write-sensitive tools;
- at most one interpretation model call per review path;
- strict Pydantic output;
- evidence IDs separate from methodology knowledge IDs;
- no chain-of-thought exposure;
- deterministic decision suggestion;
- human final decision and required override rationale.

### Improve

1. Replace process-local checkpointer/run store with durable persistence.
2. Add idempotent tool execution and resume.
3. Store graph version, prompt versions, model, latency, safety warnings, and
   evidence snapshot id.
4. Add per-tool execution status, duration, and sanitized error code.
5. Verify citations structurally:
   - every evidence claim references an ID present in the current snapshot;
   - every methodology claim references an active rulebook version.
6. Reject numeric claims not present in trusted context.
7. Add prompt-injection tests using research text, news text, and provider notes.
8. Add replay tests: the same stored snapshot and rule version must produce the
   same deterministic readiness and suggestion.
9. Ensure LLM outage leaves definition checks, completeness, tool planning, and
   decision suggestion usable.
10. Add a concise Agent execution timeline to the UI:
    `loaded → inspected → approval → calculated → reviewed → awaiting human`.

### Deterministic suggestion policy

Keep this logic centralized in the backend:

```text
failed validation or failed benchmark → Reject
missing required evidence or incomplete readiness → Hold
complete required evidence and passing benchmark → Promote
otherwise → Hold
```

`Archive` remains a human lifecycle choice, not a performance score.

### Acceptance criteria

- The LLM cannot alter completeness, check statuses, benchmark verdict, or
  deterministic suggestion.
- A decision differing from the suggestion requires an override rationale.
- Agent restart/resume survives backend restart.
- An unrelated evidence snapshot cannot be injected into a run.
- All tool arguments are allow-listed and validated.

## Phase 7 — Paper Observation and Decision UX

### Goal

Remove ambiguity between historical simulation, forward observation, and live
execution.

### Paper Observation

- Rename any remaining “Paper Trading” language in the primary workflow to
  “Paper Observation.”
- The main workspace must not expose fake account equity, fake fills, or
  generated P&L.
- A session contains only:
  - cadence;
  - minimum observation duration;
  - exit/stop criteria;
  - evidence snapshot at start;
  - dated human notes;
  - completion state.
- If the legacy simulated paper-account API remains, move it to a clearly
  labelled legacy/lab route or remove it after checking dependencies.

### Decision

- Present evidence summary first.
- Present deterministic suggestion second.
- Present AI interpretation as optional commentary.
- Present human choice and rationale last.
- Show conflicts and missing evidence explicitly.
- Show the exact evidence snapshot and timestamp being approved.
- Preserve append-only history; never overwrite an old decision silently.

### Acceptance criteria

- Users cannot confuse observation with brokerage.
- No decision exists until a human submits it.
- Refreshing or switching browser preserves server-backed sessions/decisions.

## Phase 8 — Data reliability and provider behavior

### Goal

Make provider behavior explainable and resilient without fake fallback.

Implement:

- provider capability registry;
- symbol/asset-class routing tests;
- per-provider timeout and typed failures;
- bounded retry only for retryable failures;
- cache freshness metadata;
- last-complete-session cutoff;
- data-contract validation before calculations;
- source provenance on every result;
- provider health diagnostics separated from application health;
- Stooq remains non-selectable while browser-verification responses are
  possible;
- CSV/CoinGecko/Tushare/BaoStock remain absent until genuinely implemented.

Add a frontend recovery path that distinguishes:

- backend cold start;
- backend unavailable;
- market-data provider unavailable;
- invalid research request;
- missing optional model dependency;
- LLM unavailable;
- persistence unavailable.

Never show raw stack traces, but retain a safe diagnostic code and correlation id.

## Phase 9 — Deployment, cold start, and observability

### Goal

Make the interview/demo path reliable even when infrastructure is imperfect.

Preserve and test:

- one shared `/health` warm-up promise;
- 180-second bounded warm-up;
- 45-second attempt timeout;
- exponential retry capped at 5 seconds;
- 60-second ready TTL;
- queued requests resuming after readiness;
- manual retry/resume.

Improve:

1. Add `/ready` for dependencies and keep `/health` process-only.
2. Do not block process health on optional DB/LLM/provider status.
3. Add structured JSON logs with:
   - correlation id;
   - route;
   - research id when present;
   - validation/agent run id;
   - provider;
   - duration;
   - outcome/error code.
4. Add lightweight metrics for request latency, provider failures, Agent tool
   failures, and cold-start warm-up duration.
5. Add a production smoke test for:
   - health;
   - canonical SPY execution;
   - validation;
   - evidence retrieval;
   - Agent deterministic path without requiring an LLM call.
6. Keep GitHub keep-warm as an optimization, not correctness.
7. Document that an always-on Render Starter instance is the cleanest option
   when interview reliability matters.

## Phase 10 — UI and design-system refinement

### Goal

Keep the Apple Bento character but make the product feel like a serious
research workspace rather than a landing page.

### Design rules

- Quiet `#f5f5f7` canvas.
- White evidence surfaces.
- One primary blue/cyan gradient only for the current primary action.
- Red only for errors/blockers/destructive actions.
- Green only for verified/pass states.
- Avoid large empty cards and decorative numbers without meaning.
- Use consistent 6px/12px grid rhythm.
- Constrain editorial headline size so Chinese does not wrap awkwardly.
- Keep readable line length.
- Use full-height cards only when their content justifies the space.
- Buttons must meet WCAG contrast, including disabled states.
- Focus ring must remain visible.

### Information architecture

Research Home:

- one concise thesis;
- canonical studies;
- continue recent research;
- one guided-review CTA;
- lifecycle orientation;
- no duplicated CTA.

Research Workspace:

- sticky identity/header;
- `Question / Experiment / Validation / Robustness / Observation / Decision`;
- one clear “what this page answers” sentence;
- one primary next action;
- evidence provenance close to metrics;
- no generic readiness checklist with unexplained yes/no labels.

Metrics:

- show 3–5 decision-relevant headline metrics;
- place full definitions in accessible tooltips/details;
- keep strategy and benchmark aligned;
- show `N/A`, not `0`, for missing metrics.

Responsive:

- test 1440px, 1024px, 768px, and 390px;
- no horizontal overflow;
- tables become usable scroll regions or stacked comparisons;
- maintain touch target sizes.

### Acceptance criteria

- A first-time reviewer can answer within 30 seconds:
  1. What is being researched?
  2. What evidence exists?
  3. What is missing or conflicting?
  4. What should I do next?
- The primary workflow no longer contains placeholder pages.
- Disabled controls remain readable.
- All main routes pass keyboard and basic accessibility checks.

## Phase 11 — Testing and quality gates

Add or strengthen:

### Backend

- pure metric fixture tests;
- property tests for finite JSON metrics and cumulative-return invariants;
- no-look-ahead and boundary tests;
- OOS alignment tests;
- factor direction and formation-date tests;
- persistence/restart tests;
- idempotency tests;
- evidence ownership tests;
- Agent approval, citation, tool allow-list, replay, and step-limit tests;
- optional dependency degradation tests;
- typed provider failure tests.

### Frontend

- authenticity regression tests;
- loading/error/empty/partial-success tests;
- local-to-server migration tests;
- observation and decision history tests;
- metric-definition rendering tests;
- keyboard/accessibility tests;
- responsive smoke tests.

### E2E

Add Playwright coverage for:

1. open Research Home;
2. enter canonical trend study;
3. run/load validation;
4. inspect robustness evidence;
5. open Agent review without an LLM key;
6. approve a deterministic tool call;
7. save an observation note;
8. record a human decision;
9. reload and confirm durable state;
10. simulate cold-start and provider failure states.

### CI

- format/lint;
- type-check;
- frontend unit tests;
- backend non-live tests;
- build;
- migration check;
- E2E against fixtures;
- separate non-blocking or scheduled live-provider smoke test.

Do not make live Yahoo/AkShare availability a required PR test.

## Phase 12 — Documentation and interview readiness

Update:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/AGENT_GOVERNANCE.md`
- `docs/RESEARCH_WORKFLOW.md`
- `docs/AUTHENTICITY.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/ROADMAP.md`
- `docs/DEMO_SCRIPT.md`

Documentation must match the running product. Remove stale claims about:

- features that are still placeholders;
- durability if state is still local/in-memory;
- unsupported data providers;
- live trading;
- models unavailable in deployment.

Add:

- one current architecture diagram;
- one evidence-authority diagram;
- one screenshot of Research Home;
- one screenshot of the Governance Agent;
- metric glossary link;
- reproducible canonical configurations;
- exact local and deployed verification commands.

## Final verification

Before declaring completion:

1. Inspect `git diff` for accidental unrelated changes.
2. Run all non-live backend tests.
3. Run frontend unit tests.
4. Run frontend type-check/build.
5. Run Playwright fixture E2E.
6. Verify no secrets or generated local DB/cache artifacts are staged.
7. Verify every new UI capability has a real backend or local human-authored
   implementation.
8. Verify every unsupported method is labelled as a scope boundary.
9. Verify all displayed numeric results come from a deterministic response.
10. Produce a final report:
    - files changed;
    - migrations;
    - tests and results;
    - deploy configuration changes;
    - known limitations;
    - recommended commit breakdown.

Do not automatically push or deploy unless explicitly instructed.

## Recommended commit sequence

Use cohesive commits such as:

1. `feat(persistence): add durable research evidence repositories`
2. `feat(lineage): add immutable evidence snapshot contract`
3. `feat(robustness): add trend walk-forward evidence`
4. `feat(factor): strengthen factor diagnostics and provenance`
5. `fix(models): degrade optional model dependencies independently`
6. `feat(agent): persist and harden governance agent runs`
7. `feat(workflow): persist observation and decision records`
8. `feat(observability): add readiness and structured diagnostics`
9. `refactor(ui): clarify evidence-first research workspace`
10. `test(e2e): cover governed research lifecycle`
11. `docs: align architecture metrics and demo narrative`

If a phase is too large for one safe iteration, complete the smallest vertical
slice with tests and clearly report what remains. Do not replace unfinished
work with a visual placeholder.
