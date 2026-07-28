# Architecture Decision Records

Authoritative numbering is sequential under the `ADR-NNNN` prefix.

| ID | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001.md) | Adopt a Modular Monolith as the Default Runtime | Accepted |
| [ADR-0002](ADR-0002.md) | Organize the Domain Around Bounded Contexts and Aggregates | Accepted |
| [ADR-0003](ADR-0003.md) | Apply Clean Architecture Through Vertical Slices | Accepted |
| [ADR-0004](ADR-0004.md) | Use Events and AI as Governed Workflow Participants | Accepted |
| [ADR-0005](ADR-0005-create-research-vertical-slice.md) | CreateResearch as the first modular-monolith vertical slice | Accepted |
| [ADR-0006](ADR-0006-research-initial-state-draft.md) | Research initial state is Draft | Accepted |
| [ADR-0007](ADR-0007-market-data-router.md) | Route market data by asset class behind MarketDataPort | Accepted |
| [ADR-0008](ADR-0008-factor-validation-engine.md) | Factor Validation engine and Cross-Sectional Factor Study | Accepted |
| [ADR-0009](ADR-0009-deepseek-research-reviewer.md) | DeepSeek as a governed research reviewer | Accepted |
| [ADR-0010](ADR-0010-quant-research-governance-agent.md) | Controlled Quant Research Governance Agent | Accepted |
| [ADR-0011](ADR-0011-cross-sectional-factor-dataset.md) | Cross-Sectional Factor Dataset (Phase 1) | Accepted |
| [ADR-0012](ADR-0012-cross-sectional-factor-research.md) | Cross-Sectional Factor Research (Phase 2) | Accepted |
| [ADR-0013](ADR-0013-cross-sectional-modeling-and-stock-scores.md) | Cross-Sectional Modeling and Stock Scores (Phase 3) | Accepted |

## Numbering rules

1. New decisions receive the next unused integer (`ADR-0007`, …).
2. Do not reuse IDs. Superseded decisions keep their ID and gain a `Superseded by` note.
3. Filenames may include a kebab-case slug after the ID for discoverability.
4. Historical collisions (`0001-create-research-vertical-slice.md`, `0002-research-initial-state-draft.md`) were retired in PR-001; their decisions live as ADR-0005 and ADR-0006.
