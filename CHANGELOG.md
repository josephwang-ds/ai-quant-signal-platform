# Changelog

All notable changes to AI Quant Research Workspace will be documented in this file.

The project intends to follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic versioning once public releases begin. Until then, changes remain under **Unreleased** and are grouped by pull request.

## [Unreleased]

### Added

#### PR-020 — Wire Research Workspace actions

- Wired `ResearchActionPanel` to existing Notebook, Experiments, Validation,
  Evaluation, and Copilot sections via canonical `?tab=` navigation.
- Run Validation navigates to Validation and reuses the existing
  `useResearchValidation` reload path without a second hook instance;
  Evaluation and Copilot enable only after `validation_run_id` exists.
- Opening Copilot does not submit an LLM request; Export remains honestly
  disabled. Fixed `isResearchWorkspaceSection` to recognize `copilot`.

#### PR-019 — Configurable OpenAI-compatible Copilot providers

- Research Copilot now resolves one OpenAI-compatible Chat Completions
  provider per deployment via `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_BASE_URL`,
  and `COPILOT_MODEL` (OpenAI + DeepSeek allowlist; HTTPS base URL validation;
  no failover).
- `OpenAiCompatibleLlmAdapter` builds `{base}/chat/completions` safely,
  preserves structured JSON response requests, and maps auth/rate-limit/
  malformed provider failures without exposing raw bodies.
- Temporary deprecated fallback: `OPENAI_API_KEY` still works when
  `LLM_API_KEY` is absent.
- Production base-URL hardening: `RENDER` / `ENVIRONMENT|APP_ENV|NODE_ENV=
  production` always require HTTPS and reject localhost; insecure overrides
  cannot relax this.

### Fixed

#### PR-018 — Research Execution request contract and production errors

- Fixed Yahoo adapter rejecting valid SPY requests when yfinance returned the
  current session day with NaN OHLC bars (`Column 'open' must be positive and
  valid.`). Incomplete bars are now dropped before validation.
- Reclassified provider-normalized market-data validation failures from HTTP
  400 to HTTP 502 so the frontend no longer labels Yahoo payload issues as
  invalid user parameters.
- Added `getApiDisplayMessage()` and wired Research Execution errors to show
  safe backend `detail` text instead of only generic category messages.
- Added canonical execution contract regression tests (backend + frontend).

#### PR-017 — Research Workspace production server exception

- Fixed `/research/[researchId]` SSR crash caused by passing
  `onLanguageChange={() => undefined}` from a Server Component Suspense
  fallback into Client `AppShell` (`Event handlers cannot be passed to Client
  Component props`; production digest `440809330`).
- Added honest route `loading.tsx` / `error.tsx` boundaries and regression
  tests. Fallback skeleton no longer wraps AppShell.

### Added

#### PR-016 — Deployed end-to-end verification evidence

- Operator evidence report
  `docs/reviews/DEPLOYED-E2E-VERIFICATION.md` documenting process health,
  asset-class provider status, deployed SPY / Yahoo execution success (after one
  provider flake), AkShare remote-disconnect classification, frontend API host
  + CORS checks, Copilot honest 503 without `OPENAI_API_KEY`, and failure-state
  probes. No deployment secrets or hardcoded app URLs were added.

#### PR-015 — Live market data verification

- `tests/test_market_data_live.py` with `@pytest.mark.live` Yahoo (SPY) and
  AkShare (600519.SH) OHLCV + Research Execution end-to-end smoke cases.
- Shared `live_verification.py` helpers for provenance, JSON safety, and
  fabricated-fallback detection.
- Manual `live-smoke.yml` workflow with `run_yahoo` / `run_akshare` inputs.
- Local scripts: `scripts/live_market_data_check.py` and
  `scripts/verify_deployed_research_api.py`.
- Offline verification tests and `docs/deployment/LIVE_DATA_VERIFICATION.md`.

#### PR-014 — Multi-provider market data routing

- `MarketDataRouter` behind `MarketDataPort` with deterministic asset-class
  routing: Yahoo for US/HK equities, ETFs, indices, and crypto; AkShare for
  mainland A-shares (`*.SZ`, `*.SH`, `*.BJ`).
- `SymbolDescriptor` / `classify_symbol()` value object with explicit exchange
  suffixes; bare six-digit mainland codes are rejected.
- `AkShareMarketDataAdapter` normalizing Chinese OHLCV columns to the canonical
  research schema with `qfq` adjustment recorded in provenance.
- Provider-aware cache keys (`provider|symbol|adjustment|start|end|interval`).
- Extended `DataProvenance` fields: `adapter`, `canonical_symbol`,
  `provider_symbol`, `asset_class`, `exchange`, `adjustment`, `row_count`.
- Updated `GET /api/data-sources/status` with `routing_mode: "asset_class"` and
  honest installed/configured capability flags (no live health probe per request).
- Frontend provenance banner and Data Center updates for routing metadata and
  A-share symbol guidance.
- Offline router/adapter tests, slice doc `docs/slices/multi-provider-market-data.md`,
  and ADR-0007.

#### PR-012 — Evidence-grounded Research Copilot

- `POST /api/v1/research/copilot/query` — backend-owned interpretation layer
  that explains assembled workspace evidence for the canonical MA Crossover
  research. Reads a stored `ValidationResult` by `validation_run_id`, derives
  evaluation governance context, assembles bounded structured context, and
  calls `LlmPort` — never calculates metrics, never triggers Validation, and
  never fabricates answers when the provider is unavailable.
- `ResearchContextAssembler`, lightweight in-memory document retrieval,
  `OpenAiLlmAdapter` (stdlib HTTP; `OPENAI_API_KEY` + `COPILOT_MODEL`),
  `FakeLlmAdapter` for offline CI, server-owned system policy, deterministic
  citations, and post-generation grounding checks (prohibited recommendation
  language, unsupported numeric claims).
- Research Workspace **Research Copilot** tab with sample questions, citations,
  grounding status, limitations disclaimer, awaiting-validation guidance, and
  honest not-configured / provider-unavailable states. The browser never calls
  an LLM provider directly.
- Offline copilot tests, frontend policy tests (no `NEXT_PUBLIC_*API_KEY`, no
  frontend OpenAI SDK), and slice documentation in
  `docs/slices/research-copilot.md`.

#### PR-010 — Research evaluation governance layer

- `POST /api/v1/research/evaluation` summarizing an already-produced
  PR-009 `ValidationResult`, identified by `validation_run_id`. Evaluation
  performs no MA-crossover, OOS, sensitivity, or cost calculations, no
  market-data reads, and — after an architecture fix on this branch — **no
  longer calls `ResearchValidationService.execute` at all**: its
  constructor accepts only a `ValidationResultStore`, so it is structurally
  unable to trigger a new Validation run.
- New `ValidationResultStore` (in-memory MVP; `InMemoryValidationResultStore`
  in `app.research_validation.result_store`). `POST /api/v1/research/validation`
  now saves its result exactly once per run and returns the new
  `validation_run_id` in its response; `POST /api/v1/research/evaluation`
  requires that id, returns `404` if it is unknown and `400` if it belongs
  to a different `research_id`. Saved results are lost on backend restart —
  persistent `ValidationRun` storage remains future work.
- Deterministic `evaluation_status` restricted to `completed`, `incomplete`,
  or `blocked` — no quality, robustness, or investment judgement.
- Evidence coverage as implementation completeness only (implemented vs.
  completed stage counts and percentage — never a confidence score).
- Deterministic blockers reused verbatim from the stored validation stage
  results; fixed, informational limitations and outstanding-evidence lists
  for stress testing, regime analysis, walk-forward validation, Monte Carlo
  simulation, and paper trading.
- Evaluation Workspace tab replaced with an enterprise governance
  dashboard: evaluation status, evidence coverage, evidence summary table,
  completed/incomplete/outstanding evidence, limitations, blockers, and the
  research timeline. No score, confidence, star rating, or buy/sell
  recommendation is rendered anywhere in the view. The frontend reuses the
  `validation_run_id` from the Validation result already loaded by the
  workspace and never silently runs Validation from the Evaluation tab; if
  Validation evidence is not yet available it shows "Run or load
  Validation evidence before Evaluation can be generated."
- Offline evaluation fixture tests (backend aggregation/coverage/blocker
  rules, store-based isolation, spy/failing-dependency proof that
  Evaluation never touches `MarketDataPort` or `ResearchValidationService`;
  frontend loading/success/awaiting-validation/incomplete/blocked/API-
  unavailable states) and slice documentation in
  `docs/slices/research-evaluation.md` and
  `docs/slices/research-validation.md`.

#### PR-009 — Real MA Crossover validation evidence

- `POST /api/v1/research/validation` reusing the PR-008B market-data port,
  provenance, normalized SPY series, and deterministic MA calculations.
- Chronological IS/OOS evidence with pre-OOS warm-up and continuous
  split-boundary position/cost state.
- Bounded MA parameter and transaction-cost sensitivity grids with descriptive
  summaries and no automatic strategy selection.
- Structured data-quality evidence separating fatal checks, non-fatal
  limitations, and provenance information.
- Validation Workspace rendering driven only by backend stage results;
  Evaluation and Research Confidence remain unavailable.
- Offline validation fixture tests and slice documentation in
  `docs/slices/research-validation.md`.

#### PR-008B — Real SPY research execution

- `POST /api/v1/research/execution` on the legacy FastAPI runtime with
  `MarketDataPort`, Yahoo Finance adapter, filesystem cache, and deterministic
  MA20/60 calculations (adjusted close, one-day position lag, tested costs).
- Canonical Research Workspace (`ma-crossover-spy`) connected to backend
  evidence only — provenance banner, calculated overview metrics, baseline
  experiment overlay; Evaluation remains unavailable.
- Offline fixture tests, optional live Yahoo smoke (`pytest -m live`), and
  slice documentation in `docs/slices/research-execution.md`.

#### PR-008A — Authenticity-first research baseline

- Single canonical MA Crossover research project; fictional projects and
  fabricated confidence/validation outcomes removed from the public workspace.

#### PR-001 — Engineering Foundation

- Repository constitution in `docs/PROJECT_BIBLE.md`.
- Foundational architecture decisions for the modular monolith, DDD boundaries, Clean Architecture, vertical slices, event-driven workflows, and governed AI (`ADR-0001`…`ADR-0004`).
- Slice ADRs renumbered to `ADR-0005` and `ADR-0006` with an ADR index.
- Contribution, development-workflow, roadmap, project-structure, style, security, and community conduct guidance.
- GitHub issue forms for bugs, features, epics, and stories.
- Pull request template and CODEOWNERS review routing.
- MIT `LICENSE`.
- Continuous integration workflow (`.github/workflows/ci.yml`) for backend offline tests, `apps/api` tests, frontend tests/typecheck/build, and repository policy checks *(implemented in PR-011C; prior docs claimed this before the workflow existed)*.
- `apps/api` dependency manifests and runbook (`apps/api/README.md`).
- Cursor project rules with corrected attachment metadata; merged frontend UI/engineering rule.
- Architecture Bible Appendix A (Information Architecture) and legacy documentation archive.
- Read-only migration report covering technical debt, duplicate documentation, compatibility surfaces, and staged improvements.
- Final foundation review checklist in `docs/PR-001-FINAL-REVIEW.md`.

### Changed

#### PR-011A — Remove fabricated evidence from adjacent public product previews

- Removed `frontend/lib/mockQuantData.ts` (hardcoded Sharpe 1.12, max
  drawdown -8.6%, hit rate 0.58, a "Strategy Health Score" of 76/100 with
  fabricated pillar scores, simulated "Approved with caution" / "Approved —
  size capped" governance verdicts, and `BUY`/`SELL` signal strings) and the
  two dead-code components it fed that no route rendered
  (`ExecutiveCockpitGrid`, `ExecutiveCockpitSnapshot`).
- Converted six public preview routes — Strategy Health Score
  (`/strategy-health-score`), Return Quality Lens (`/return-quality-lens`),
  Risk Gate Review (`/risk-gate-review`), Scenario Shock Test
  (`/scenario-shock-test`), Decision Ledger (`/decision-ledger`), and
  Decision Room (`/decision-room`) — from fabricated-metric panels to an
  honest `WorkspacePlaceholder` "Planned Capability" state. No score,
  signal, or verdict is shown until real Research Execution / Validation /
  Evaluation evidence exists; none of these modules were previously listed
  in top-level navigation or `WORKSPACE_MODULES`, and remain unlisted.
- Removed the now-dead `BACKEND_TEXT_ZH` translation entries in
  `frontend/lib/i18n.ts` that only existed to translate the fabricated copy
  above, and corrected the `/overview` route's title/description (previously
  "Executive Cockpit" / a "risk governance, return quality, and audit trail"
  description) to "Workspace Overview", matching what that page actually
  renders (the honest `WORKSPACE_MODULES` directory).
- Added `frontend/lib/publicPreviewAuthenticity.test.ts` proving
  `mockQuantData` no longer exists or is imported anywhere reachable from
  public navigation, that none of the six remediated routes render any
  fabricated Sharpe/CAGR/drawdown/health-score/BUY/SELL/Approved value, and
  that each renders the honest placeholder state instead.
- See `docs/data/AUTHENTICITY_POLICY.md` ("PR-011A remediation") and
  `docs/reviews/RC-1-REPOSITORY-AUDIT.md` for the audit finding this
  addresses.

#### PR-011B — Harden production API wiring and backend-unavailable states

- Added shared frontend API configuration (`frontend/lib/apiConfig.ts`):
  `getApiBaseUrl()`, `buildApiUrl()`, `ApiConfigurationError`, and
  `isProductionRuntime()`. Local development may fall back to
  `http://127.0.0.1:8000` when unset; production requires
  `NEXT_PUBLIC_API_BASE_URL` and never silently calls localhost.
- Added shared request transport (`frontend/lib/apiRequest.ts`) with typed
  error categories (`configuration`, `network`, `timeout`,
  `backend_unavailable`, `provider_unavailable`, `invalid_request`,
  `not_found`, `server_error`, `unknown`), safe backend-detail parsing,
  bounded timeouts (60s canonical research POSTs, 5s health/status), and
  `AbortSignal` composition without silent retries.
- Updated canonical research API clients (`researchExecutionApi`,
  `researchValidationApi`, `researchEvaluationApi`) and health/status helpers
  in `frontend/lib/api.ts` to use the shared configuration and transport.
  Research hooks render stable user-facing messages per category and never
  show fabricated fallback evidence.
- Hardened backend CORS parsing (`backend/app/config.py`): explicit origins
  only, trailing-slash normalization, deduplication, and rejection of `*`.
- Added deployment runbook `docs/deployment/PRODUCTION_API_WIRING.md` and
  updated `.env.example`, `README.md`, `backend/README.md`, and
  `docs/ARCHITECTURE.md` with the environment contract, timeout policy,
  health vs provider-status semantics, and troubleshooting guidance.
- Added frontend unit tests (`apiConfig.test.ts`, `apiRequest.test.ts`,
  `researchApiClients.test.ts`, hook failure-state tests) and backend CORS
  contract tests (`tests/test_config_cors.py`).

#### PR-011C — Deterministic CI and offline test gates

- Added `.github/workflows/ci.yml` with required jobs for backend offline
  tests (`pytest -m "not live"`), focused research suites, independent
  `apps/api` tests, frontend tests/typecheck/build, and repository policy
  checks (governance files, no tracked `.env` secrets, public authenticity
  suite).
- Added optional manual `.github/workflows/live-smoke.yml` for live Yahoo
  smoke tests only (`pytest -m live`); non-blocking and not required for PR
  CI.
- Added `backend/tests/conftest.py` to inject deterministic legacy market
  data and block outbound network access in default offline tests.
- Tightened `backend/pytest.ini` and `apps/api/pytest.ini` with
  `--strict-markers`; documented default offline, focused, and live suites in
  `README.md`, `CONTRIBUTING.md`, `backend/README.md`, and
  `apps/api/README.md`.

#### PR-008B review follow-ups

- Enforce same-asset buy-and-hold only (`benchmark` must equal `symbol`; HTTP 400 otherwise).
- Apply Yahoo `timeout_seconds` via `yfinance.download(timeout=…)`.
- Clip open-ended history to completed daily bars using an America/New_York exclusive cutoff.
- Clarify ROADMAP: OOS / sensitivity / stress / regime / full robustness remain pending.

- Reframed the README around AI Quant Research Workspace as a research operating system rather than a trading dashboard.
- Established explicit documentation precedence and a no-big-bang migration policy.
- Marked `docs/ARCHITECTURE.md` and the former `README 2.md` as legacy.
- Resolved ADR ID collisions and Chapter-02 numbering collision without changing decision content.

### Security

- Added a private vulnerability-reporting process, supported-version statement, response targets, coordinated-disclosure guidance, and sensitive-data rules.

## Release process

When the first versioned release is prepared:

1. move relevant entries from **Unreleased** into a dated version section;
2. classify entries as Added, Changed, Deprecated, Removed, Fixed, or Security;
3. link the version to its Git tag and comparison; and
4. ensure migration and security notes are complete before publishing.

