# Project Structure

This guide explains the repository’s current layout, target conventions, and migration boundaries. It is descriptive, not authorization for a bulk move.

## Repository map

```text
ai-quant-signal-platform/
├── .github/
│   ├── ISSUE_TEMPLATE/       # Structured bug, feature, epic, and story intake
│   ├── workflows/ci.yml      # Backend, apps/api, and frontend checks
│   ├── CODEOWNERS            # Review ownership
│   └── PULL_REQUEST_TEMPLATE.md
├── .cursor/rules/            # Versioned AI-assisted engineering rules
├── apps/
│   └── api/                  # Target modular-monolith API; see apps/api/README.md
├── backend/                  # Current deployed FastAPI runtime (legacy path)
├── frontend/                 # Current Next.js workspace application
├── docs/
│   ├── Architecture-Bible/   # Frozen product/domain/runtime architecture
│   ├── adr/                  # Architectural decision records (ADR-0001+)
│   ├── legacy/               # Archived non-authoritative docs
│   ├── risk_knowledge/       # Deterministic risk knowledge documents
│   ├── slices/               # Use-case delivery notes
│   ├── ARCHITECTURE.md       # Legacy snapshot (bannered)
│   ├── PROJECT_BIBLE.md      # Repository constitution and source of truth
│   └── STYLE_GUIDE.md        # Product visual and interaction rules
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── LICENSE
├── CHANGELOG.md
├── DEVELOPMENT_WORKFLOW.md
├── MIGRATION_REPORT.md
├── PROJECT_STRUCTURE.md
├── ROADMAP.md
├── README.md
└── render.yaml               # Current backend deployment descriptor
```

## Community and governance files

GitHub-native project health files live in `.github/`; human-readable policies with repository-wide relevance live at the root so they are easy to discover.

| Path | Ownership |
|---|---|
| `.github/ISSUE_TEMPLATE/` | contributor intake and triage contracts |
| `.github/PULL_REQUEST_TEMPLATE.md` | review evidence and Definition of Done |
| `.github/CODEOWNERS` | automatic reviewer routing; not a substitute for branch protection |
| `CODE_OF_CONDUCT.md` | community behavior, reporting, and enforcement |
| `SECURITY.md` | private vulnerability reporting and coordinated disclosure |
| `CHANGELOG.md` | notable unreleased and released changes |

## Current and target state

Two backend structures coexist intentionally:

- `backend/` is the current application with market-data, backtest, risk, simulation, persistence, and API behavior. Preserve it until an approved cutover.
- `apps/api/` demonstrates the target modular-monolith and vertical-slice structure. It is not yet a complete replacement or the documented production entry point.

The current web application remains in `frontend/`. The frozen Runtime Architecture recommends eventual convergence on `apps/web/`, but that move should happen only as an atomic, tested repository migration. Folder location does not justify changing runtime behavior.

## Target application structure

```text
apps/
├── api/
│   ├── src/
│   │   ├── bootstrap/                 # Composition root
│   │   ├── modules/
│   │   │   ├── research/
│   │   │   ├── validation/
│   │   │   ├── governance/
│   │   │   ├── portfolio/
│   │   │   └── market_intelligence/
│   │   └── shared/                    # Minimal cross-cutting kernel
│   └── tests/
└── web/
    └── src/
        ├── app/                       # Next.js routes and composition
        ├── modules/                   # Domain-oriented UI modules
        └── shared/                    # Reusable UI and platform utilities

packages/                              # Only independently valuable shared packages
tests/                                 # Cross-application acceptance/contract tests
scripts/                               # Repeatable engineering and operational commands
```

Do not create `packages/`, root `tests/`, or `scripts/` merely to match the diagram. Add them when a concrete, owned responsibility exists.

## API module convention

```text
modules/<bounded_context>/
├── domain/
│   ├── entities and aggregates
│   ├── value objects
│   ├── policies
│   ├── events
│   └── repository/port protocols
├── application/
│   ├── commands/<use_case>/
│   ├── queries/<use_case>/
│   └── dto/
├── infrastructure/
│   ├── persistence adapters
│   └── provider adapters
└── presentation/
    └── HTTP/event/job adapters
```

Each use case is a vertical slice. Domain is framework-independent. Application coordinates ports. Infrastructure implements ports. Presentation translates transport concerns. `bootstrap/` is the only place that knows concrete wiring.

### Shared kernel rule

`shared/` is for stable, genuinely cross-context primitives such as correlation identifiers or base error contracts. It is not a home for ambiguous helpers, shared domain entities, or a universal repository. Prefer duplication over premature coupling; promote only after repeated, stable use.

## Web module convention

The current application uses:

```text
frontend/
├── app/                     # Next.js App Router entry points
├── components/
│   ├── features/            # Domain/task-oriented compositions
│   ├── layout/              # Workspace shell and navigation
│   ├── ui/                  # Reusable primitives
│   ├── workspace/           # Workspace-level compositions
│   └── legacy/              # Explicit compatibility surface
├── lib/                     # Client services, formatters, config, i18n
└── types/                   # Stable UI/boundary types
```

Routes should be thin. Feature modules own task composition; `ui/` primitives remain domain-neutral. Business rules and authoritative state transitions do not belong in the browser.

## Documentation convention

| Location | Purpose | Naming |
|---|---|---|
| `docs/Architecture-Bible/` | frozen architecture book | `Chapter-NN-Topic.md` |
| `docs/adr/` | durable architecture decisions | `ADR-NNNN.md` for foundational series |
| `docs/slices/` | implementation-slice notes | `<context>-<use-case>.md` |
| `docs/risk_knowledge/` | governed policy/glossary material | descriptive kebab/snake case until normalized |
| repository root | contributor-facing entry documents | uppercase descriptive names |

Avoid duplicate authorities. A detailed document should link to the Project Bible rather than restating the constitution.

## Naming conventions

### Domain

- Use singular nouns for entities and aggregate roots: `Research`, `Evaluation`, `Portfolio`.
- Use imperative use-case names: `CreateResearch`, `RunValidation`, `PublishStrategy`.
- Use past tense for events: `ResearchCreated`, `ValidationPassed`, `MonitoringAlertRaised`.
- Use explicit state names from the State Machine chapter; do not invent near-synonyms.
- Name ports by capability (`ResearchRepository`, `MarketDataProvider`), not vendor.
- Name adapters by technology plus port (`PostgresResearchRepository`).

### Python

- Files, functions, and variables: `snake_case`.
- Types and exceptions: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Tests: `test_<behavior>_<condition>` where it remains readable.

### TypeScript and React

- Components and exported types: `PascalCase`.
- Functions, hooks, and variables: `camelCase`; hooks begin with `use`.
- Component files: `PascalCase.tsx`; utilities may use the repository’s existing `camelCase.ts` convention.
- Route segments: lowercase kebab-case.
- CSS classes: descriptive kebab-case with a stable component prefix.

### Branches and documents

- Branches: `<type>/<context>-<outcome>` in lowercase kebab-case.
- ADR titles state the decision, not the discussion topic.
- Avoid version suffixes such as `final`, `new`, or `latest`; use history and ADR status.

## Dependency rules

1. Domain imports only language/runtime primitives and domain-owned code.
2. Application imports Domain and inward-owned ports.
3. Infrastructure imports ports it implements; Domain never imports Infrastructure.
4. Presentation invokes Application; it does not call repositories directly.
5. Schedulers and agents invoke Application only.
6. Bounded contexts do not import another context’s internals.
7. Frontend consumes public contracts and never becomes the authority for domain rules.

## Adding a new module

Before creating folders, identify the owning bounded context, aggregate or policy, use case, contract, state/invariant impact, and required ADR. Deliver one complete slice and prove the boundaries. A module with no owned behavior is probably a view, adapter, or premature abstraction.
