# Portfolio Intelligence — Vertical Slice Plan

> **Phase:** 5 — Portfolio Intelligence  
> **Status:** Phase 5.1 complete — Phase 5.2 not started

---

## Phase 5.0 Deliverables

- `docs/PHASE_5_DEFINITION.md` — canonical definition ✅
- `docs/slices/portfolio-intelligence.md` — this document ✅
- `docs/adr/ADR-0015` — Portfolio bounded context ✅
- `docs/adr/ADR-0016` — Portfolio snapshot contracts ✅
- `docs/adr/ADR-0017` — Portfolio registry and publishing ✅
- Roadmap status update ✅

---

## Phase 5.1A — Portfolio Domain and Contracts ✅ Complete

### Scope completed
- Portfolio bounded context package at `backend/app/portfolio/`
- Typed contracts: identity, version, lifecycle, mandate, member, analytical weight,
  constraints, manifest, snapshot reference/availability/type enums
- Deterministic `validate_portfolio_manifest` with stable issue codes
- Focused domain/contract/validation tests

### Contracts introduced
`PortfolioId`, `PortfolioVersion`, `PortfolioLifecycleStatus`, `PortfolioMandate`,
`PortfolioMember`, `AnalyticalWeight`, `PortfolioConstraintSet`, `PortfolioManifest`,
`WeightMethod`, `PortfolioSnapshotType`, `PortfolioSnapshotAvailability`,
`PortfolioSnapshotReference`, `PortfolioValidationIssue`, `PortfolioValidationResult`

### Validation invariants
- Portfolio ID / version / schema version
- Lifecycle timestamp consistency (DRAFT vs PUBLISHED)
- Minimum two members; duplicate `source_run_id` and `member_order` rejected
- Equal weight mode requires omitted member weights; operator-specified requires explicit weights
- Weight range `[0, 1]`; no float coercion; no automatic normalization
- Long-only; fully-invested vs allow-cash consistency; max members; weight sum tolerance
- Does **not** verify source-run existence (Phase 5.1C)

### Explicit exclusions
No registry, filesystem, publication, API, frontend, calculations, risk, backtest,
Health Score, or execution functionality.

### Verification
`pytest tests/test_portfolio_domain.py` — PASS

---

## Phase 5.1B — Registry and Filesystem ✅ Complete

### Outcome
Filesystem-backed Portfolio registry persists DRAFT and immutable PUBLISHED manifests
with canonical SHA-256 integrity, per-identity locking, and atomic writes.

### Scope completed
- `PortfolioRepository` port and `FilesystemPortfolioRepository` adapter
- Layout under `PORTFOLIO_OUTPUT_DIR` (default `backend/outputs/portfolios`)
- Canonical UTF-8 JSON serialization (sorted keys; members by `member_order`; Decimal as `"0.25"`)
- Draft replace vs published immutability; idempotent same-version same-checksum publish
- `latest` = highest published `PortfolioVersion` (not mtime)
- Focused registry/filesystem/integrity/concurrency/atomicity/path tests

### Storage layout
```text
<portfolio_registry_root>/
  {portfolio_id}/
    portfolio.lock
    draft/
      manifest.json
      integrity.json
    published/
      v0001/
        manifest.json
        integrity.json
      v0002/
        ...
    latest.json
```

### Draft vs published
- One mutable DRAFT per identity; atomic replace; never listed as a published version
- PUBLISHED versions are immutable under `published/vNNNN/`; never overwritten
- Same version + same checksum → idempotent success; different checksum → conflict
- Registry admin listing may include draft-only identities; published-only listing excludes them

### Integrity and locking
- Checksum algorithm: SHA-256 over canonical manifest bytes (not over integrity record)
- Integrity fields: schema_version, algorithm, content_checksum, portfolio_id,
  portfolio_version, created_at
- Missing/unsupported/mismatched integrity fails explicitly on read/verify
- Lock scope: per `portfolio_id` via `fcntl.flock` with explicit timeout (default 30s)
- Latest pointer updated only after published version + integrity succeed

### Recovery boundary
- Ignore orphan `*.tmp` files in lists
- Report corrupt published manifests / missing integrity / invalid latest pointer
- Preserve earlier valid published versions; no automatic delete or rewrite on read

### Explicit exclusions
No source-run lookup, publication orchestration, seed command, API, frontend,
snapshot builders, analytics, risk, backtest, Health Score, AI, or execution.

### Verification
`pytest tests/test_portfolio_registry.py` — PASS

---

## Phase 5.1C — Publication Pipeline ✅ Complete

### Outcome
Operator DRAFT manifests are admitted only when every `source_run_id` resolves to an
eligible Published Research Run with verified snapshot references, then persisted as an
immutable PUBLISHED Portfolio through the Phase 5.1B repository.

### Application workflow
```text
Load DRAFT manifest
→ Domain validation (fail closed; no source I/O if invalid)
→ Resolve each source_run_id via PublishedResearchQueryPort
→ Admit Published + validation.ok + metadata + snapshot eligibility
→ Build publication provenance
→ Prepare PUBLISHED manifest (injected UTC clock)
→ Idempotency check (portfolio_id + portfolio_version)
→ PortfolioRepository.publish (unless dry-run)
→ Post-write read-back + integrity + latest checks
→ Structured PortfolioPublicationResult
```

### Source admission policy
- Resolve via Phase 4 `IntelligenceService` adapter (not HTTP, not raw JSON files)
- Require `PUBLISHED`, `published_at`, `validation.ok`, integrity ok, identity match
- Require ≥1 `selected_snapshot_ids` (empty selection rejected; no silent defaults)
- Supported source snapshot types only: `research_summary`, `signal`
- Snapshot must belong to that run; verified with `get_snapshot_content(verify=True)`
- One invalid member rejects the entire Portfolio

### Provenance (persisted on published manifest)
Per member: `source_run_id`, `source_published_at`, `source_validation_ok`,
`selected_snapshot_ids`, `selected_snapshot_checksums` (id/checksum/type/schema),
`source_methodology_version`, `resolved_at`

### Idempotency
- Key: `portfolio_id` + `portfolio_version`
- Logical equivalence excludes `published_at` and `resolved_at`
- Equivalent retry → `ALREADY_PUBLISHED` (preserves original timestamp; no rewrite)
- Material difference → `CONFLICT` (`PUBLICATION_VERSION_CONFLICT`)
- Storage / post-write integrity failure → `FAILED`

### Dry-run
Validates, resolves, admits, prepares candidate; writes nothing.

### Seed command
```bash
cd backend
python -m app.portfolio.seed_published_portfolio --manifest path.json --dry-run
python -m app.portfolio.seed_published_portfolio --manifest path.json
```

Result statuses: `VALIDATED`, `PUBLISHED`, `ALREADY_PUBLISHED`, `REJECTED`, `CONFLICT`, `FAILED`.

### Explicit exclusions
No Portfolio snapshot builders, query API, frontend, exposure, risk, backtest,
Health Score, AI, optimization, or execution.

### Verification
`pytest tests/test_portfolio_publication.py` — PASS

## Phase 5.1 — Portfolio Registry Foundation ✅ Complete

Phase 5.1A + 5.1B + 5.1C establish:

```text
Published Research → Verified Portfolio Membership → Published Portfolio Registry
```

## Phase 5.2 — Portfolio Snapshot Contracts and Builders ⛔ Not Started

### Outcome
Deterministic builders produce typed portfolio snapshots from supported source evidence.
Unavailable or unsupported evidence produces explicit, honest snapshot states.

### Acceptance criteria
- `PortfolioSummarySnapshot` defined with schema version `portfolio-summary-snapshot/v1`
- `PortfolioMembershipSnapshot` lists members with source run references
- `PortfolioWeightSnapshot` supports equal and operator-specified weights; no optimization
- `PortfolioExposureSnapshot` aggregates compatible factor/sector dimensions only
- `PortfolioConstraintSnapshot` records deterministic constraint evaluation results
- `PortfolioRiskSnapshot` produced when backtest evidence is available
- Builders reject incompatible dimensions explicitly (not zero-fill)
- Contract tests cover: valid payload, missing optional fields, incompatible dimensions, unavailable evidence
- No optimization implemented
- No AI-generated weights
- No API or frontend

---

## Phase 5.3 — Portfolio Intelligence Query Layer

Read-only API mirrors Phase 4.5 pattern for portfolio queries.

---

## Phase 5.4 — Portfolio Intelligence Frontend

Transport, library, and published workspace (hard gate). No demo fallback.

---

## Phase 5.5 — Portfolio Analytics Depth

Exposure compatibility, constraint surfaces, risk when evidence exists. No optimizer.

---

## Phase 5.6 — Portfolio Health (deferred methodology)

Out of Phase 5 RC until methodology is accepted.

---

## Phase 5 RC

Operator-seeded published portfolios with query API and read-only workspace.
No execution, brokerage, or autonomous trading.
