# Changelog

All notable changes to AI Quant Research Workspace will be documented in this file.

The project intends to follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic versioning once public releases begin. Until then, changes remain under **Unreleased** and are grouped by pull request.

## [Unreleased]

### Added

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
- Continuous integration workflow (`.github/workflows/ci.yml`) for backend tests, `apps/api` tests, and frontend build.
- `apps/api` dependency manifests and runbook (`apps/api/README.md`).
- Cursor project rules with corrected attachment metadata; merged frontend UI/engineering rule.
- Architecture Bible Appendix A (Information Architecture) and legacy documentation archive.
- Read-only migration report covering technical debt, duplicate documentation, compatibility surfaces, and staged improvements.
- Final foundation review checklist in `docs/PR-001-FINAL-REVIEW.md`.

### Changed

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

