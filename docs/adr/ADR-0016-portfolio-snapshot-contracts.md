# ADR-0016 — Portfolio Snapshot Contracts and Provenance

| Field | Value |
| --- | --- |
| **ID** | ADR-0016 |
| **Status** | Draft |
| **Phase** | Phase 5 — Portfolio Intelligence |
| **Deciders** | Architecture owners |
| **Date** | 2026-07-29 |

---

## Context

Phase 5 produces portfolio-level analytical snapshots that aggregate evidence from published research runs. These snapshots must follow the same provenance, integrity, and immutability principles established in Phase 4 for research snapshots (ADR-0013, `docs/INTELLIGENCE_PUBLISHING.md`).

Research and Portfolio are separate bounded contexts. Their snapshot type enums must remain separate.

---

## Decision

### 1. Snapshot type separation

Portfolio snapshot types use a **separate enum** from Phase 4 research snapshot types:

```text
ResearchSnapshotType (Phase 4 — unchanged):
  research_summary
  signal

PortfolioSnapshotType (Phase 5 — new):
  portfolio_summary
  portfolio_membership
  portfolio_weights
  portfolio_exposure
  portfolio_constraints
  portfolio_risk
  portfolio_review
  portfolio_backtest
```

Phase 4 `ResearchSnapshotType` is not extended. Portfolio types are only defined in the Portfolio bounded context.

Only implement snapshot types in the slice that owns them. No placeholder values.

### 2. Portfolio snapshot contracts

Each snapshot type has a versioned schema. Initial schema versions:

| Type | Schema version |
| --- | --- |
| `portfolio_summary` | `portfolio-summary-snapshot/v1` |
| `portfolio_membership` | `portfolio-membership-snapshot/v1` |
| `portfolio_weights` | `portfolio-weights-snapshot/v1` |
| `portfolio_exposure` | `portfolio-exposure-snapshot/v1` |
| `portfolio_constraints` | `portfolio-constraints-snapshot/v1` |
| `portfolio_risk` | `portfolio-risk-snapshot/v1` |
| `portfolio_review` | `portfolio-review-snapshot/v1` |
| `portfolio_backtest` | `portfolio-backtest-snapshot/v1` |

### 3. Provenance requirements

Every portfolio snapshot must record:

```text
PortfolioSnapshotProvenance {
  portfolio_id: string
  portfolio_version: string
  source_run_ids: string[]          # all referenced published run_ids
  source_snapshot_ids: string[]     # all research snapshot_ids consumed
  builder: string                   # builder identifier + version
  generated_at: datetime
  notes: string | null
}
```

This makes the analytical chain traceable: portfolio snapshot ← research snapshots ← research artifacts.

### 4. Availability semantics

A portfolio snapshot may be in one of three states:

- **available** — produced and published; content is queryable
- **unavailable** — evidence required but not present; must render honest unavailable state
- **unsupported** — snapshot type not computed for this portfolio version; must render honest unsupported state

Frontend must distinguish these three states. Unavailable and unsupported must never silently become zero values or blank screens.

### 5. Exposure aggregation constraints

`PortfolioExposureSnapshot` must only aggregate **compatible** exposure dimensions:
- Dimensions not available from all members are listed as `partial` with an explicit member count
- Incompatible dimensions (different factor definitions, universes, or time windows) are listed as `incompatible` and must not be coerced into zero
- No synthetic exposure values may be inferred by AI or interpolation

### 6. Analytical weights

`PortfolioWeightSnapshot` records:

```text
PortfolioWeightSnapshot {
  schema_version: "portfolio-weights-snapshot/v1"
  weight_method: "equal" | "operator_specified"
  members: [
    { source_run_id: string, analytical_weight: float }
  ]
  weights_sum_to_one: bool          # validation flag
  provenance: PortfolioSnapshotProvenance
}
```

Optimization-derived weights are not supported in Phase 5. The `weight_method` field explicitly records the method used so that readers can interpret the analytical intent.

### 7. Integrity and checksums

Portfolio snapshots follow Phase 4 integrity rules:
- Content is checksummed (SHA-256) on write
- Checksums are stored in the portfolio manifest
- Frontend displays "Integrity recorded" — same pattern as Phase 4
- Frontend must not claim verification unless an explicit verify endpoint is called and succeeds
- No frontend artifact download

### 8. PortfolioReviewSnapshot

`portfolio_review` is deferred to Phase 5.6. The contract will be defined when the deterministic methodology for portfolio-level review state is accepted. Phase 5.4 frontend must not add a Health tab before this type is defined.

---

## Consequences

- Phase 4 snapshot infrastructure is reused for inspiration and consistency but not shared at the code level (separate bounded contexts).
- Portfolio snapshots carry full provenance to their source research snapshots.
- Unavailable or unsupported evidence is explicit; zero-filling is prohibited.
- Portfolio Health/Review tab deferred until ADR or review accepts the methodology.

---

## Alternatives Considered

**Extend `ResearchSnapshotType` with portfolio values.**  
Rejected. Research and Portfolio are separate bounded contexts. Merging enums creates coupling and blurs the governance boundary.

**Allow partial exposure aggregation with zero fill.**  
Rejected. Silently coercing missing dimensions to zero produces misleading analytics and violates the "evidence before conclusion" principle.
