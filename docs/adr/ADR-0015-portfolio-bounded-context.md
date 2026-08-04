# ADR-0015 — Portfolio Bounded Context and Authority Boundaries

| Field | Value |
| --- | --- |
| **ID** | ADR-0015 |
| **Status** | Draft |
| **Phase** | Phase 5 — Portfolio Intelligence |
| **Deciders** | Architecture owners |
| **Date** | 2026-07-29 |

---

## Context

Phase 5 introduces a Portfolio Intelligence layer. The Architecture Bible (Chapter 2 §3.20) defines Portfolio as a governed allocation context in which multiple Strategies interact through exposures, constraints, diversification, and shared capital intent.

Before implementation begins, the authority boundaries of this bounded context must be explicit. The most important risks are:

1. Portfolio reaching into Research or Validation internals and creating hidden coupling.
2. Portfolio acquiring execution authority it is not designed to have.
3. AI output silently becoming an allocation recommendation or decision authority.
4. Portfolio overwriting or reinterpreting individual Strategy validation records.

---

## Decision

### 1. Portfolio aggregate boundary

The `Portfolio` aggregate root owns:
- mandate (scope, universe, objectives)
- membership list (`PortfolioMember` references)
- constraint set (`PortfolioConstraintSet`)
- benchmark reference
- lifecycle state (DRAFT / PUBLISHED)
- snapshot references

The `Portfolio` aggregate does **not** own:
- Strategy or ResearchRun identity
- Research evidence
- Validation results
- Governance decisions at the Strategy level

### 2. Portfolio membership references

A `PortfolioMember` references a published research run by its immutable `run_id`:

```text
PortfolioMember {
  source_run_id: string          # must be a PUBLISHED run_*
  selected_snapshot_ids: string[]  # snapshot references used for evidence
}
```

This is an MVP provenance seam. `run_id` is not a permanent cross-version Strategy identity. A future Strategy Registry may provide a long-lived identity above multiple runs; it is out of Phase 5 scope.

Portfolio **never copies or mutates** ResearchRun evidence. All research evidence is read from the Phase 4.5 read-only intelligence API.

### 3. Analytical weights versus execution

Portfolio weights in Phase 5 are **analytical research outputs**, not live allocation instructions or execution authority.

- Supported: equal analytical weight; operator-specified weight from manifest.
- Not supported: optimization-derived weights; AI-generated weights.
- The product must never imply that a `PortfolioWeightSnapshot` constitutes an order, position, or recommendation to trade.

### 4. Deterministic Guardrails

Portfolio-level constraints (`PortfolioConstraintSet`) are:
- deterministic and version-controlled in backend policy configuration
- evaluated with a verifiable, reproducible result
- never silently relaxed or overridden by AI output or UI state

AI may explain a constraint result. It cannot alter it.

### 5. No Strategy ownership

Portfolio references Strategies by identity. It cannot:
- override a Strategy's lifecycle state
- modify a Strategy's validation record
- publish a Strategy on behalf of the research pipeline
- authorize a Strategy lifecycle transition

### 6. No execution authority

Phase 5 has no broker connectivity, order management, or live position system. The word "execution" must not appear in portfolio UI copy as a product action.

### 7. AI explanatory-only boundary

AI in Phase 5 may:
- explain portfolio evidence already produced deterministically
- summarize constraint results with evidence citations
- draft portfolio review notes for human review

AI in Phase 5 must not:
- generate weights or allocations
- override constraint results
- become the Decision Authority for any portfolio lifecycle transition
- produce findings without tracing them to evidence

---

## Consequences

- Research and Portfolio remain separate bounded contexts with no shared mutable state.
- Portfolio frontend reads only from Phase 4.5 API and Phase 5.3 portfolio query API.
- A portfolio that references a non-existent or non-published run is invalid at registration time.
- Portfolio Health Score methodology is explicitly deferred (see Phase 5.6); no aggregate health calculation ships before methodology is accepted.

---

## Alternatives Considered

**Embed portfolio logic inside the Research bounded context.**  
Rejected. Portfolio and Research have different aggregate semantics, governance, and lifecycle rules. Embedding creates hidden coupling and violates the Architecture Bible's bounded context model.

**Allow Portfolio to hold a copy of research evidence.**  
Rejected. Copies create divergence. Portfolio always reads from the authoritative Phase 4 intelligence layer.
