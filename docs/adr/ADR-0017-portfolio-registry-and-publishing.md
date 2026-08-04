# ADR-0017 — Portfolio Registry and Publishing Lifecycle

| Field | Value |
| --- | --- |
| **ID** | ADR-0017 |
| **Status** | Draft |
| **Phase** | Phase 5 — Portfolio Intelligence |
| **Deciders** | Architecture owners |
| **Date** | 2026-07-29 |

---

## Context

Phase 5 needs a durable registry for portfolio manifests and snapshots. The Phase 4 filesystem registry (Phase 4.1–4.3) established the pattern: filesystem-based, checksummed, append-only, immutable after publication, with locks and idempotent recovery.

Phase 5 must follow this pattern for consistency and simplicity. It must also define how portfolios are published, what routes expose them, and how the publishing lifecycle maps to the read-only query layer.

---

## Decision

### 1. Filesystem registry

The portfolio registry uses a filesystem layout under ``backend/outputs/portfolios``
(or ``PORTFOLIO_OUTPUT_DIR``):

```text
backend/outputs/portfolios/
  {portfolio_id}/
    portfolio.lock              # advisory write lock (fcntl)
    draft/
      manifest.json             # mutable DRAFT only
      integrity.json
    published/
      v0001/
        manifest.json           # immutable PUBLISHED version
        integrity.json
      v0002/
        manifest.json
        integrity.json
    latest.json                 # pointer to highest published version
```

`portfolio_id` format: `portfolio_{timestamp}_{hex8}` (consistent with Phase 4 `run_id` pattern).

Published version directories use zero-padded ``vNNNN`` labels derived from
``PortfolioVersion`` (not filesystem mtime). Temporary ``.*.tmp`` files are
ignored by list/read APIs.

### 2. Portfolio manifest

Operator and registry manifests follow Phase 5.1A ``PortfolioManifest`` contracts.
Checksums are **not** caller-authored authoritative fields on the manifest.
Integrity metadata is stored beside the manifest in ``integrity.json``.

### 3. Lifecycle: DRAFT → PUBLISHED (versioned under one identity)

```text
DRAFT (mutable, one per portfolio_id)
  ↓ repository publish(manifest)
PUBLISHED vN (immutable)
  ↓ later publish with portfolio_version = N+1
PUBLISHED vN+1 (immutable)
```

- One mutable draft may exist per ``portfolio_id`` and may be replaced atomically.
- Each published version is immutable and stored under ``published/vNNNN/``.
- Multiple published versions share the same ``portfolio_id``.
- Advancing the analytical portfolio means publishing a **new version number**,
  not minting a new ``portfolio_id``.
- The Phase 5.3 public API serves only ``PUBLISHED`` versions.

### 4. Publication validation (orchestration vs storage)

**Phase 5.1C orchestration** (not 5.1B) validates source runs and snapshots before
calling the repository.

**Phase 5.1B storage publication** accepts a fully prepared ``PUBLISHED`` manifest and:

1. requires lifecycle ``PUBLISHED`` and timezone-aware ``published_at``;
2. requires ``portfolio_version >= 1``;
3. writes an immutable version directory with integrity metadata;
4. updates ``latest.json`` only after the version write succeeds.

### 5. Atomic writes and locking

- ``portfolio.lock`` is an advisory lock created before any write and released after
  commit, following the Phase 4 ``fcntl.flock`` pattern.
- Manifest and integrity writes are atomic: temp file in the same directory,
  flush/fsync, then ``os.replace``.
- Incomplete temporary files are ignored by list/read operations and are never
  treated as published versions.

### 6. Idempotency and conflicts

For ``publish(manifest)``:

- **Same** ``portfolio_id`` + **same** ``portfolio_version`` + **same** content
  checksum → idempotent success (existing record returned; files not rewritten).
- **Same** ``portfolio_id`` + **same** ``portfolio_version`` + **different**
  checksum → ``PortfolioPublicationConflictError`` (never overwrite).
- A new content revision requires a new ``portfolio_version``.

### 7. Latest pointer

``latest(portfolio_id)`` resolves the highest valid published ``PortfolioVersion``.
If ``latest.json`` is present, it must point at an existing valid published version;
otherwise the registry reports corruption. Normal reads do not rewrite storage.

### 8. Canonical routes

Phase 5 adds two canonical routes:

```text
/portfolio                  Portfolio Intelligence Library
/portfolio/[portfolioId]    Published Portfolio Workspace
```

Dispatcher logic (consistent with Phase 4):
- `portfolio_*` IDs → Published Portfolio Workspace
- other IDs → safe not-found state (no Active Portfolio Workspace in initial release)

Phase 4 routes (`/`, `/platform`, `/research/run_*`, `/engine/research/*`) are unchanged.

### 9. Query API alignment

`GET /api/v1/portfolios` and related endpoints mirror Phase 4.5 intelligence API patterns:
- Response includes `status: "PUBLISHED"` filter by default
- Error codes follow Phase 4 naming: `PORTFOLIO_NOT_FOUND`, `PORTFOLIO_NOT_PUBLISHED`, `INVALID_PORTFOLIO_ID`
- Snapshot content endpoint: `GET /api/v1/portfolios/{portfolio_id}/snapshots/{snapshot_name_or_id}`

### 10. Seed tooling

An operator seed script will be provided at:

```text
backend/scripts/seed_published_demo_portfolio.py
```

It must:
- Support `--dry-run` (print plan JSON without writing)
- Be idempotent (re-run with same manifest is a no-op)
- Reference existing `PUBLISHED` research runs
- Document the operator workflow in `docs/DEMO_MODE.md`

The seed script must not be imported or called from production application code. No frontend demo fallback.

### 11. Frontend IA and routes

Covered in ADR-0015 §7 and `docs/PHASE_5_DEFINITION.md`.

The Published Portfolio Workspace follows the same hard-gate and view-local failure pattern as the Phase 4 Published Research Workspace:
- Gate: Portfolio Detail → Membership → Run validation → Snapshot refs → Lazy content
- Gate errors and view-local errors remain separate
- No frontend automatic fallback to demo data

---

## Consequences

- Portfolio registry follows Phase 4 integrity patterns (atomic writes, flock, SHA-256).
- DRAFT portfolios are never exposed via the public query API.
- Published versions under one ``portfolio_id`` are immutable; content changes require a
  new ``portfolio_version``.
- Operator seed workflow remains the intended Phase 5 RC publishing mechanism.
- Phase 4 routes, workspaces, and release records are untouched.

---

## Alternatives Considered

**Use a database (e.g. SQLite or Postgres) instead of filesystem.**  
Deferred. Phase 4 filesystem registry is working and consistent. A database migration may be introduced as a separate ADR when operational evidence justifies it.

**Allow published portfolios to be updated in place.**  
Rejected. Immutability after publication is a core evidence integrity principle (Architecture Bible §1.2 "Immutable provenance").

**Create an Active Portfolio Workspace alongside the Published Portfolio Workspace.**  
Deferred. Active portfolio workflows (interactive construction, member management) are not in Phase 5 RC scope. They require additional ADRs and use-case design.
