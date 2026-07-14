# Changelog

All notable changes to AI Quant Research Workspace will be documented in this file.

The project intends to follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic versioning once public releases begin. Until then, changes remain under **Unreleased** and are grouped by pull request.

## [Unreleased]

### Added

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

