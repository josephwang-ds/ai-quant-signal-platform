# AI Quant Research Workspace — Roadmap

> **Planning horizon:** capability-based, not date-based · **Last reviewed:** 2026-07-14

This roadmap describes intended product and engineering outcomes. It is not a promise of dates, and planned capabilities must not be presented as implemented. Architecture remains governed by the [Project Bible](docs/PROJECT_BIBLE.md) and accepted ADRs.

## North star

Deliver a production-quality research operating system in which a Strategy can move through a complete, auditable lifecycle—from hypothesis to evidence, decision, monitoring, and retirement—without turning the product into an execution platform.

## Milestone map

```mermaid
flowchart LR
  M0["M0 · Foundation"] --> M1["M1 · Domain Core"] --> M2["M2 · Research Workspace"]
  M2 --> M3["M3 · Validation & Governance"] --> M4["M4 · Portfolio & Monitoring"]
  M4 --> M5["M5 · Governed AI"] --> M6["M6 · Production Readiness"]
```

| Milestone | Outcome | Exit evidence |
|---|---|---|
| M0 · Engineering foundation | Contributors share architecture, workflow, standards, and quality gates | Project Bible, ADR index, contributor guidance, community health files, LICENSE, CI workflow, migration inventory |
| M1 · Domain core | Frozen domain and state machines exist as framework-independent behavior | aggregate tests, transition policies, domain events, boundary checks |
| M2 · Research workspace | Researchers manage Strategy-linked hypotheses, experiments, evidence, and notebooks | one persistent research journey with provenance and reproducibility |
| M3 · Validation & governance | Quantitative eligibility and review decisions are deterministic and auditable | validation runs, evaluations, risk reviews, guardrails, decision ledger |
| M4 · Portfolio & monitoring | Validated strategies can be reviewed in portfolio and simulation contexts | health, exposure, monitoring alerts, review/reopen loop |
| M5 · Governed AI | Agents assist research without gaining domain authority | agent audit trail, evidence-linked reports, human review, failure controls |
| M6 · Production readiness | The platform can be operated securely and predictably | SLOs, observability, recovery drills, security review, release process |

### PR-001 foundation baseline (completed engineering foundation)

PR-001 delivers the mergeable engineering-foundation baseline for M0:

- Project Bible, Architecture Bible chapter authority, and ADR numbering (`ADR-0001`…`ADR-0006`)
- Contribution, development-workflow, roadmap, project-structure, and style guidance
- GitHub issue forms, pull request template, CODEOWNERS, Security policy, and Code of Conduct
- MIT `LICENSE`
- Cursor rules with working frontmatter attachment
- `apps/api` runbook and dependency manifests for the reference modular API
- Minimal CI workflow (`.github/workflows/ci.yml`) for backend tests, `apps/api` tests, and frontend build

Still deferred beyond PR-001: release automation, Dependabot policy, branch-protection configuration in GitHub settings, formatting/lint matrix expansion, and dependency-boundary enforcement tests.

## Epic roadmap

### Epic A — Engineering system

- [x] Establish a minimal CI workflow for backend tests, `apps/api` tests, and frontend build.
- [ ] Expand formatting, linting, type-checking, and documentation checks in CI.
- [ ] Add dependency-boundary tests for bounded contexts and Clean Architecture.
- [x] Document local commands and dependency manifests for `apps/api`.
- [ ] Define release, versioning, and Dependabot policies.
- [x] Publish security reporting and Code of Conduct.
- [ ] Track migration from `backend/` and `frontend/` without big-bang rewrites (ongoing).

### Epic B — Strategy and lifecycle foundation

- Define stable Strategy identity and ownership across bounded contexts.
- Encode canonical state machines and transition authorization.
- Publish idempotent domain events with correlation and causation metadata.
- Preserve immutable lifecycle history and decision provenance.

### Epic C — Research context

- Hypothesis definition and falsification criteria.
- Experiment protocol, approval, execution, and outcome capture.
- [x] Authentic historical backtest *(PR-008B: SPY MA20/60 via `POST /api/v1/research/execution`)*.
- [x] Same-asset buy-and-hold benchmark comparison *(PR-008B; independent benchmark series deferred)*.
- [x] Chronological out-of-sample (OOS) evidence *(PR-009; no optimization or robustness verdict)*.
- [x] Bounded parameter and transaction-cost sensitivity evidence *(PR-009; descriptive only)*.
- [ ] Stress testing.
- [ ] Regime analysis.
- [ ] Full robustness evaluation.
- Research synthesis, review, close, and reopen workflows.
- Notebook records linked to Strategy and Evidence, not isolated documents.
- [x] Authenticity-first canonical MA Crossover research baseline *(PR-008A)*.

### Epic D — Validation context

- [x] Deterministic validation evidence for the canonical MA Crossover research *(PR-009: historical, benchmark, OOS, sensitivity, costs, and data quality)*.
- [ ] Versioned, persisted ValidationRun lifecycle and final Pass / Fail / Inconclusive policy.
- Evaluation policies for performance, robustness, leakage, and data confidence.
- Reproducible benchmarks and comparable metric definitions.
- Expiration and re-validation rules when evidence or market assumptions change.

### Epic E — Governance context

- Risk Review and Review assignment lifecycles.
- Deterministic guardrails and blocking conditions.
- Decision drafting, approval, rejection, execution record, and supersession.
- Evidence-complete audit trails with human accountability.

### Epic F — Market Intelligence

- MarketDataset provenance, freshness, coverage, adjustment, and quality metadata.
- Provider abstraction with observable failover and confidence impact.
- Dataset versioning and reproducible retrieval references.
- Market events that trigger monitoring or research review.

### Epic G — Portfolio and simulation

- Portfolio membership constrained by Strategy eligibility.
- Exposure, concentration, correlation, and risk-budget review.
- Paper simulation with explicit assumptions and no broker connectivity.
- Strategy Health Score and monitoring signals with explainable components.

### Epic H — Agent runtime

- Research, Review, Market, and Portfolio agent roles.
- Event consumption, repository reads, and Application-only mutations.
- Model/prompt versioning, evidence citations, cost and latency telemetry.
- Human review, timeout, retry, idempotency, and provider fallback.

### Epic I — Platform operations

- Authentication, authorization, tenant and workspace boundaries.
- Structured logs, traces, metrics, alerting, and audit retention.
- Postgres backup/restore and object-storage lifecycle policy.
- Threat modeling, dependency scanning, secret management, and incident response.
- Capacity, resilience, and disaster-recovery testing.

## Development phases

### Phase 0 — Inventory and stabilize

Document current behavior, protect the legacy runtime, add quality gates, and classify migration candidates. No architectural cutover occurs implicitly.

### Phase 1 — Prove the reference slice

Use Research/CreateResearch as a reference slice, close its packaging and automation gaps, and validate dependency direction before cloning the pattern.

### Phase 2 — Build the lifecycle spine

Implement domain state machines and event contracts in thin, end-to-end slices. Establish Strategy identity before broad UI expansion.

### Phase 3 — Complete research and validation

Prioritize evidence capture, experiment reproducibility, evaluation, and review over additional indicator widgets.

### Phase 4 — Add governance and portfolio views

Connect deterministic gates and decisions to monitoring, simulation, and portfolio review.

### Phase 5 — Introduce governed AI

Add agents only after evidence, application ports, audit, and authorization boundaries are available.

### Phase 6 — Harden and scale

Use measured bottlenecks and operational evidence to guide caching, queues, workload isolation, and any deployment extraction.

## Future modules

| Module | Purpose | Prerequisite |
|---|---|---|
| Strategy Registry | authoritative Strategy identity and lifecycle history | domain core |
| Research Notebook | linked rationale, observations, and reproducibility record | Evidence model |
| Validation Center | ValidationRun and Evaluation governance | validation policies |
| Decision Ledger | immutable review and decision history | Governance context |
| Monitoring Center | alerts, health, and research reopen loop | Strategy lifecycle |
| Simulation Center | explicit paper assumptions and outcomes | validated Strategy eligibility |
| Portfolio Review | portfolio-level risk and Strategy contribution | Portfolio aggregate |
| Agent Operations | governed agent runs, provenance, and review | Application ports and audit |

## Explicit non-goals

- live order execution or broker integration;
- autonomous trading decisions;
- LLM-generated quantitative validation;
- microservices before a measured operational need;
- feature growth that bypasses Strategy, evidence, or governance.

## Roadmap governance

Review the roadmap at each milestone boundary. A proposal may change sequencing, but any change to product constitution, bounded contexts, aggregate ownership, state machines, or dependency rules requires an ADR and Architecture Bible review.
