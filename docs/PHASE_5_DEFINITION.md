# Phase 5 — Portfolio Intelligence
## Definition and Architecture

> **Status:** Planning — Implementation not started.  
> **Authority:** This document records the accepted Phase 5 definition. It supersedes the informal planning notes in the prior conversation.

---

## Phase Name

```text
Phase 5 — Portfolio Intelligence
```

---

## Product Positioning

Phase 5 is an **evidence-grounded portfolio research layer** that combines eligible published research outputs into a governed portfolio context.

Phase 5 is **not**:
- a portfolio optimizer
- an execution platform
- an investment recommendation system
- an autonomous allocation system

Phase 5 **complete planned scope** includes (not all in first slice):
- Portfolio provenance
- Portfolio membership
- Candidate and strategy selection
- Analytical weights
- Deterministic constraints
- Aggregate exposure
- Portfolio risk evidence
- Portfolio backtest evidence
- Portfolio health and review
- Published Portfolio Intelligence

---

## Relationship to Prior Phases

```text
Phase 1  Data Foundation           ✅ Done
Phase 2  Factor Research           ✅ Done
Phase 3  Modeling                  ✅ Done
Phase 4  Intelligence Publishing   ✅ Done — RC Complete

Phase 5  Portfolio Intelligence    🟡 Planning
  │
  ├── consumes:  Phase 4.5 read-only intelligence query API
  │              Phase 4.6 Published Workspace (run_* identities)
  ├── extends:   Research Library navigation context
  └── adds:      Portfolio bounded context (research-only)
```

Architecture Bible reference: Chapter 2 §3.20 Portfolio, §3.19 Health Score; Chapter 4 Portfolio bounded context.

---

## Canonical Routes

Existing Phase 4 routes are **unchanged**:

```text
/                           Research Library           (unchanged)
/platform                   Platform Overview          (unchanged)
/research/run_xxx           Published Workspace        (unchanged)
/engine/research/xxx        Active Workspace           (unchanged)
```

Phase 5 adds:

```text
/portfolio                  Portfolio Intelligence Library
/portfolio/[portfolioId]    Published Portfolio Workspace
```

No Active Portfolio Workspace in the initial release.

---

## Domain Boundary

Phase 5 is bounded strictly to the **Portfolio & Knowledge** context (Architecture Bible Chapter 2).

### Initial domain objects

| Object | Role |
| --- | --- |
| `Portfolio` | Aggregate root — mandate, membership, constraints, Benchmark reference |
| `PortfolioMember` | Reference to a published run via `source_run_id` + selected snapshot refs |
| `PortfolioMandate` | Scope, universe, objectives, and constraints of the portfolio |
| `PortfolioConstraintSet` | Versioned, deterministic constraint rules (Guardrails at portfolio level) |
| `PortfolioWeightSnapshot` | Analytical weight record — not live allocation, not execution authority |
| `PortfolioExposureSnapshot` | Aggregate factor/sector/instrument exposure from member evidence |
| `PortfolioRiskSnapshot` | Portfolio-level risk evidence from backtest or scenario methods |
| `PortfolioReviewSnapshot` | Portfolio health and review state — deferred until methodology accepted |

### PortfolioMember — MVP provenance seam

For the initial Phase 5 release, a `PortfolioMember` references published research runs via immutable `run_id` values:

```text
PortfolioMember {
  source_run_id: string          # references a PUBLISHED run_*
  selected_snapshot_ids: string[]  # snapshot references used for evidence
}
```

This is an **MVP provenance seam**. `run_id` is not a permanent Strategy identity. A future Strategy Registry may provide a long-lived identity above multiple research runs; it is not part of Phase 5.

Portfolio must **never copy or mutate** ResearchRun evidence.

### What Portfolio must never do

- Own or mutate Strategy identity or research truth
- Produce a live order, position, or trade instruction
- Claim allocation as executed
- Override individual Strategy validation
- Bypass Strategy governance
- Reference unpublished or failed research runs

---

## Analytical Weights

Phase 5 first supports:

| Weight type | Phase |
| --- | --- |
| Equal analytical weight | Phase 5.1 |
| Operator-specified analytical weight (from manifest) | Phase 5.1 |
| Optimization-derived weights | Not implemented |
| AI-generated weights | Not implemented |

Weights represent **analytical research output**, not live allocation or execution intent. The term `PortfolioWeightSnapshot` is used; `AllocationIntent` is not a primary term.

---

## Portfolio Snapshot Type Boundary

Research and Portfolio are separate bounded contexts. Snapshot type enums remain separate:

```text
ResearchSnapshotType (Phase 4 — unchanged):
  research_summary
  signal

PortfolioSnapshotType (Phase 5 — new, separate):
  portfolio_summary
  portfolio_membership
  portfolio_weights
  portfolio_exposure
  portfolio_constraints
  portfolio_risk
  portfolio_review
  portfolio_backtest
```

Only implement snapshot types in the slice that owns them. Do not add placeholder types or empty frontend tabs.

---

## Hard Gate (Frontend)

```text
Portfolio Detail
  ↓ success only
Portfolio Membership (referenced run_ids)
  ↓ success only
Referenced Published Run validation (via Phase 4.5 API)
  ↓
Portfolio Snapshot References
  ↓ lazy, per active tab
Portfolio Snapshot Content
```

Failure boundaries:
- Missing Portfolio → hard-gate failure
- Invalid/missing member run references → portfolio-level integrity failure
- Unavailable exposure/risk evidence → view-local evidence state
- One failed optional snapshot → must not erase valid Portfolio metadata
- No frontend demo fallback may invent members, weights, exposures, or Health Scores

---

## Publishing Lifecycle

```text
DRAFT     → under construction, not queryable via public API
PUBLISHED → immutable, served via read-only query layer
```

Only `PUBLISHED` portfolios are served. Published versions are immutable.

### Initial publishing workflow (operator-seeded)

```text
Operator-defined Portfolio Manifest
  ↓
Validate published run references
  ↓
Register Portfolio
  ↓
Build deterministic portfolio snapshots
  ↓
Publish immutable Portfolio version
  ↓
Serve through read-only API
  ↓
Render Published Portfolio Workspace
```

No frontend create/edit/delete workflow in Phase 5 RC. Internal application services handle creation and publication.

---

## Portfolio Health Score

Do **not** define Portfolio Health Score as a weighted average of Strategy Health Scores by default.

Keep `PortfolioReviewSnapshot` out of the first implementation slice until its deterministic methodology is explicitly accepted in a future ADR or review.

---

## Invariants Preserved from Phase 4

| Invariant | Phase 5 behaviour |
| --- | --- |
| Strategy is the governance unit | Portfolio references; never owns |
| Quant before AI | Health Score calculated deterministically; AI may explain only |
| Deterministic Guardrails | Portfolio constraints evaluated deterministically |
| No execution | Weights are analytical intent; no order API |
| Evidence before conclusion | Portfolio health references Strategy validation evidence |
| Validation authority per run | `ResearchRunDetail.validation.ok` remains canonical |
| Published Workspace read-only | Phase 5 adds no write capability to `/research/run_*` |
| No Buy/Sell language | Portfolio weight is analytical research output, not an order |
| Integrity recorded | Portfolio artifacts follow same evidence safety rules |
| No frontend demo fallback | No auto-synthesis of demo portfolio data |

---

## Delivery Plan

### Phase 5.0 — Definition and Architecture ✅ Complete
- Canonical definition (`docs/PHASE_5_DEFINITION.md`)
- Three ADRs (0015–0017)
- Roadmap status update
- Vertical slice plan (`docs/slices/portfolio-intelligence.md`)

### Phase 5.1A — Portfolio Domain and Contracts ✅ Complete
- Typed Portfolio contracts and enums in `backend/app/portfolio/`
- Deterministic `validate_portfolio_manifest`
- Domain/contract tests
- **No registry, API, frontend, or calculations**

### Phase 5.1B — Registry and Filesystem ✅ Complete
- Filesystem repository (`FilesystemPortfolioRepository`)
- Checksums, locks, atomic writes
- Idempotent publication persistence
- Repository tests
- **No API; no frontend; no calculations; no source-run orchestration**

### Phase 5.1C — Publication Pipeline ✅ Complete
- Source-run existence validation via Phase 4 `IntelligenceService` adapter
- Publish application service + operator seed workflow
- Provenance, dry-run, idempotency, post-write integrity verification
- **No API; no frontend; no snapshot builders**

### Phase 5.1 — Portfolio Registry Foundation ✅ Complete
Published Research → Verified Portfolio Membership → Published Portfolio Registry

### Phase 5.2 — Portfolio Snapshot Contracts and Builders ⛔ Not Started
- `PortfolioSummarySnapshot`
- `PortfolioMembershipSnapshot`
- `PortfolioWeightSnapshot` (equal + operator-specified)
- `PortfolioExposureSnapshot`
- `PortfolioConstraintSnapshot`
- `PortfolioRiskSnapshot`
- Deterministic builders from supported source evidence
- Explicit unavailable and unsupported states
- **No optimization; no AI-generated weights; no API; no frontend**

### Phase 5.3 — Portfolio Intelligence Query Layer
Read-only endpoints only:
```text
GET /api/v1/portfolios
GET /api/v1/portfolios/latest
GET /api/v1/portfolios/{portfolio_id}
GET /api/v1/portfolios/{portfolio_id}/snapshots
GET /api/v1/portfolios/{portfolio_id}/snapshots/{snapshot_id}
```
**No write API.**

### Phase 5.4 — Portfolio Intelligence Frontend
- **5.4A** — transport layer, type contracts, IA, error mapping
- **5.4B** — Portfolio Intelligence Library at `/portfolio`
- **5.4C** — Published Portfolio Workspace at `/portfolio/[portfolioId]`

Initial workspace tabs:
```text
Overview
Membership
Exposure
Constraints
Risk
```
Health tab added only when deterministic portfolio-level methodology is accepted.

### Phase 5.5 — Portfolio Backtest Evidence
Evidence generation slice:
- Chronological portfolio formation
- Monthly or quarterly rebalance with turnover and costs
- Benchmark alignment
- CAGR, volatility, Sharpe ratio, maximum drawdown, tracking error, information ratio
- **Evidence generation, not optimization**

### Phase 5.6 — Portfolio Review and Health
Delivered only after methodology is agreed:
- Deterministic Portfolio Health Score or review state
- Component evidence, blockers, limitations
- Review snapshot
- AI explanation over supplied evidence only

### Phase 5 RC — Hardening and Release Closure
- Concurrency and recovery audit
- Frontend failure states
- Accessibility and responsive review
- Seed workflow with `--dry-run`
- Tests, documentation, release record
- Non-blocking follow-ups

---

## Open Questions

| Question | Decision |
| --- | --- |
| Analytical weight precision | Equal + operator-specified only; no optimization |
| Guardrails | Deterministic, versioned in backend policy configuration; no silent relaxation |
| Portfolio Health | Not defined in Phase 5.1–5.4; deferred to Phase 5.6 after methodology accepted |
| Publishing lifecycle | DRAFT / PUBLISHED; only PUBLISHED served publicly; published is immutable |
| Cross-strategy exposure | Only aggregate compatible dimensions; incompatible/unavailable must be explicit, not coerced to zero |
| Seed tooling | Operator seed command with `--dry-run` and idempotent execution, analogous to Phase 4 |

---

## ADRs Required

| ADR | Title | Status |
| --- | --- | --- |
| [ADR-0015](adr/ADR-0015-portfolio-bounded-context.md) | Portfolio Bounded Context and Authority Boundaries | Draft |
| [ADR-0016](adr/ADR-0016-portfolio-snapshot-contracts.md) | Portfolio Snapshot Contracts and Provenance | Draft |
| [ADR-0017](adr/ADR-0017-portfolio-registry-and-publishing.md) | Portfolio Registry and Publishing Lifecycle | Draft |

---

## Documentation Immutability

The following documents are **not modified** by Phase 5 planning:

- `docs/releases/PHASE_4_RC.md` — immutable historical release record
- `docs/INTELLIGENCE_PUBLISHING.md` — Phase 4 document

Phase 5 has its own documentation:
- `docs/PHASE_5_DEFINITION.md` (this document)
- `docs/slices/portfolio-intelligence.md`
- `docs/adr/ADR-0015`, `ADR-0016`, `ADR-0017`

---

*Phase 5.0 documentation complete. Phase 5.1A–5.1C (Portfolio Registry Foundation)
complete. Phase 5.2 snapshot builders have not started.*
