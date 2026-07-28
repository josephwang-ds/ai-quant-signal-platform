# Intelligence Publishing — Phase 4.1 / 4.2 / 4.3

Research Run Registry + Research Artifact Registry + Intelligence Snapshot
Contracts for the AI Investment Intelligence Platform.

**Built on an Evidence-driven Quant Research Engine.**  
Every AI insight is backed by structured research evidence. Explainable. Traceable. Reviewable.

## Purpose

Phase 4.1 creates the minimum production-quality foundation for registering
completed research runs and storing **immutable** run manifests on the local
filesystem.

Phase 4.2 adds append-only, checksummed research artifact registration under
each run.

Phase 4.3 defines the first **consumer-facing snapshot contracts** and builds
them deterministically from registered artifacts. No HTTP API or frontend
consumption is implemented in this phase.

## Three structure categories

| Category | Owner | Examples | Role |
| --- | --- | --- | --- |
| Domain research structures | Existing research / evidence modules | factor metrics, model evaluation, prediction tables, validation results, signal calculations, feature importance, reproducibility evidence | Authoritative research payloads — **not redesigned** by publishing |
| Publishing registry structures | `app.intelligence` | `ResearchRunMetadata`, `ResearchRunManifest`, `ResearchArtifactReference`, `ArtifactVerificationResult`, `ResearchSnapshotReference`, `SnapshotVerificationResult` | Storage, identity, provenance, integrity, lifecycle |
| Consumer snapshot structures | `app.intelligence` snapshot contracts | `ResearchSummarySnapshot`, `SignalSnapshot` | Stable, immutable consumer projections |

Domain metrics stay inside artifact **files**. Registry references carry only
identity, type, path, integrity, and lightweight descriptive metadata.
Snapshots may summarize domain outputs for consumers but must not become
unrestricted copies of raw research artifacts.

## Canonical relationships

```text
Domain Research Object
  → serialized artifact file
  → ResearchArtifactReference
  → ResearchRunManifest.artifacts

Registered Research Artifacts
  → Snapshot Builder
  → serialized snapshot file
  → ResearchSnapshotReference
  → ResearchRunManifest.snapshots
```

`ResearchRunManifest` is the aggregate root. Snapshot **content** and
`ResearchSnapshotReference` remain separate.

## Authority boundary

| Layer | Authority |
| --- | --- |
| Deterministic research services | Own calculations (factors, models, validation) |
| Research run / artifact registry | Receives completed outputs; records metadata and lifecycle |
| Snapshot builders (Phase 4.3) | Project registered artifacts into versioned consumer contracts from **explicit** normalized inputs or clearly available registry metadata |
| Future serving APIs | Will read published runs / snapshots — not implemented yet |

Publishing **must not** trigger training, factor calculation, or model retraining.
Builders **must not** invent findings, generate LLM prose, or invent investment
logic from arbitrary factor values.

Existing reproducibility helpers in `app.research_reproducibility` continue to
own evidence-artifact fingerprints. This registry reuses git/runtime resolution
where useful and does not replace those contracts.

## Directory structure

```text
backend/outputs/                  # or $INTELLIGENCE_OUTPUT_DIR
  latest.json                     # lightweight pointer to latest published run
  runs/
    run_<UTC>_<suffix>/
      manifest.json               # versioned aggregate root
      artifacts/
        <safe-name>__<short-id>.<ext>
      snapshots/
        <safe-name>__<short-id>.json
```

Generated manifests must not be committed. See `.gitignore`.

## Research run lifecycle

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> RUNNING
    CREATED --> FAILED
    RUNNING --> VALIDATED
    RUNNING --> FAILED
    VALIDATED --> PUBLISHED
    VALIDATED --> FAILED
    PUBLISHED --> ARCHIVED
    FAILED --> ARCHIVED
    ARCHIVED --> [*]
```

### Allowed transitions

| From | To |
| --- | --- |
| CREATED | RUNNING, FAILED |
| RUNNING | VALIDATED, FAILED |
| VALIDATED | PUBLISHED, FAILED |
| PUBLISHED | ARCHIVED |
| FAILED | ARCHIVED |
| ARCHIVED | _(terminal)_ |

Rejected examples: `PUBLISHED → RUNNING`, `FAILED → RUNNING`, `ARCHIVED → *`.

## Manifest structure

Schema version: `research-run-manifest/v1`

```json
{
  "schema_version": "research-run-manifest/v1",
  "run": {
    "schema_version": "research-run-manifest/v1",
    "run_id": "run_20260728T041530Z_a1b2c3d4",
    "run_type": "FACTOR",
    "status": "CREATED",
    "created_at": "2026-07-28T04:15:30Z",
    "updated_at": "2026-07-28T04:15:30Z",
    "published_at": null,
    "dataset_version": null,
    "feature_version": null,
    "model_version": null,
    "git_commit": null,
    "generator": "intelligence-run-registry/phase-4.1",
    "environment": "python/3.x.y",
    "random_seed": null,
    "training_window": null,
    "prediction_window": null,
    "universe": null,
    "notes": null
  },
  "artifacts": [],
  "snapshots": [],
  "checksums": {},
  "validation": {
    "ok": true,
    "checks": ["registry_manifest_created"],
    "details": {"phase": "4.1"}
  },
  "errors": []
}
```

Unknown research versions are `null` — never fabricated placeholders such as `"v1"`.

Run IDs contain no ticker names, strategy names, user input, or secrets.

## Immutability rule

Once a run reaches **PUBLISHED**:

- the manifest may only transition to **ARCHIVED**;
- corrections require a **new run**;
- artifact and snapshot bytes must not be overwritten.

Artifact and snapshot registration are append-only on `CREATED` / `RUNNING` /
`VALIDATED` only. There is no `update_*` / `delete_*` for either.

## Latest pointer behaviour

`outputs/latest.json` is updated **only after** the published `manifest.json` write succeeds.

It stores lightweight pointer metadata only:

- `schema_version`
- `run_id`
- `manifest_path` (relative to the output root)
- `published_at`

It does not duplicate the full manifest.

`get_latest_published_run()` returns `None` when the pointer is absent, and fails safely when the pointer is corrupt or points at a non-published run.

## Environment configuration

| Variable | Meaning |
| --- | --- |
| `INTELLIGENCE_OUTPUT_DIR` | Absolute or relative filesystem root. Empty / unset → `backend/outputs`. |

Documented in `backend/.env.example`.

## Package layout

```text
backend/app/intelligence/
  __init__.py
  schemas.py              # enums + registry models + id generators
  errors.py               # focused domain exceptions
  storage.py              # filesystem root, atomic writes, SHA-256
  manifest.py             # build / transition / validate
  run_registry.py         # ResearchRunRegistry (Phase 4.1)
  artifact_registry.py    # ResearchArtifactRegistry (Phase 4.2)
  snapshot_contracts.py   # ResearchSummarySnapshot / SignalSnapshot (Phase 4.3)
  snapshot_registry.py    # ResearchSnapshotRegistry + builders (Phase 4.3)
```

## Phase 4.2 — Research Artifact Registry

### Artifact definition

An artifact is an immutable, checksummed **file** owned by a research run. Domain
research objects remain in the Quant Research Engine / Evidence Layer. The
publishing layer treats their serialized bytes as **opaque** content.

`ResearchArtifactReference` is a child record inside one manifest — not a second
independent artifact manifest and not a carrier of IC, Sharpe, predictions, or
other business metrics.

The registry records only:

- what was produced (`name`, `artifact_type`, `media_type`)
- which run produced it (parent manifest + run directory ownership)
- where it lives (`relative_path` under `artifacts/`)
- whether bytes changed (`sha256` checksum + `size_bytes`)

`ArtifactReference` remains a compatibility alias for
`ResearchArtifactReference`. New code should use `ResearchArtifactReference`.

### Supported artifact types

| Enum | Serialized value |
| --- | --- |
| REPRODUCIBILITY_MANIFEST | `reproducibility_manifest` |
| DATA_VALIDATION_REPORT | `data_validation_report` |
| FACTOR_METRICS | `factor_metrics` |
| FACTOR_REPORT | `factor_report` |
| MODEL_EVALUATION | `model_evaluation` |
| PREDICTION_TABLE | `prediction_table` |
| FEATURE_IMPORTANCE | `feature_importance` |
| VALIDATION_REPORT | `validation_report` |
| GENERIC_JSON | `generic_json` |
| GENERIC_PARQUET | `generic_parquet` |

### Registration lifecycle

Allowed only when run status is `CREATED`, `RUNNING`, or `VALIDATED`.

| Method | Behaviour |
| --- | --- |
| `register_json_artifact` | Deterministic JSON bytes → atomic write under `artifacts/` → SHA-256 → manifest append |
| `register_file_artifact` | Copy regular file bytes into run-owned `artifacts/` (never persist absolute source path) |
| `get_artifact` / `list_artifacts` | Resolve by name or `artifact_id` |
| `verify_artifact` | Read-only integrity check (`hmac.compare_digest`) |

Artifact IDs: `artifact_<8-hex>`.

### Checksums

- Algorithm: `sha256` only
- Source of truth: `ResearchArtifactReference.checksum`
- Top-level `manifest.checksums` is keyed by `artifact_id` and kept synchronized

### Failure rollback

Write order: validate → atomic artifact write → confirm digest → atomic manifest write.
If the manifest write fails, the newly created artifact file is removed.
Previously registered artifacts are left untouched.

## Phase 4.3 — Intelligence Snapshot Contracts

### Implemented contracts

| Contract | Schema version | Purpose |
| --- | --- | --- |
| `ResearchSummarySnapshot` | `research-summary-snapshot/v1` | Generic research summary (trend / factor / model / general) |
| `SignalSnapshot` | `signal-snapshot/v1` | Normalized consumer signals with bounded direction enum |

Only these two contracts are implemented. There is no generic reflection-based
snapshot framework.

### Snapshot reference

`ResearchSnapshotReference` (publishing layer) includes at least:

- `snapshot_id`, `name`, `snapshot_type`, `schema_version`
- `relative_path`, `media_type`
- `checksum_algorithm`, `checksum`, `size_bytes`
- `created_at`, `as_of`
- `source_artifact_ids`
- `metadata` (publication context only — **not** full snapshot content)

Snapshot IDs: `snapshot_<8-hex>`.

No preemptively invented `SnapshotReference` alias; use
`ResearchSnapshotReference` in new code.

### Source provenance

Before snapshot creation:

- every `source_artifact_id` must exist on the **same** run
- cross-run references are rejected
- missing / invalid sources are never silently omitted
- optional `require_artifact_verification=True` requires successful artifact
  integrity verification before building

Snapshot content provenance also records `source_artifact_ids` and builder id.

### Builders and registry

| Entry | Behaviour |
| --- | --- |
| `build_research_summary_snapshot` | Explicit findings / limitations + registry metadata → typed summary → file + reference |
| `build_signal_snapshot` | Explicit normalized `SignalRecord` inputs → typed signal snapshot → file + reference |
| `get_snapshot` / `list_snapshots` | Resolve by name or `snapshot_id` |
| `verify_snapshot` | Read-only integrity check |

Builders:

1. validate the run exists and status allows creation
2. validate source artifact IDs on the same run
3. optionally verify source artifact integrity
4. construct the typed snapshot
5. serialize deterministically under `snapshots/`
6. calculate checksum and size
7. append `ResearchSnapshotReference` to the manifest
8. atomically write the manifest; rollback the new snapshot file on failure

### Signal semantics

Direction enum (bounded):

- `strong_negative`, `negative`, `neutral`, `positive`, `strong_positive`

`score` is optional and **not** assumed to be a probability. `confidence` is
optional in `[0, 1]` when the producer supplies it. Builders do not auto-convert
arbitrary factor values into directional signals.

### Deterministic serialization

JSON snapshots use:

- UTF-8
- stable keys
- no NaN / Infinity
- timezone-aware UTC datetimes
- explicit enum serialization
- stable ordering where order has no semantic meaning

**Identity vs content:** two builds with identical explicit data may produce
different `snapshot_id` and `generated_at` values, but content fields excluding
identity/time remain stable for identical inputs.

### Checksum verification

`verify_snapshot` is read-only. It detects missing files and changed bytes via
SHA-256 and size comparison. It does not mutate the manifest.

### Lifecycle and immutability

- Append-only registration
- Unique snapshot `name` within a run
- Destination overwrite rejected
- `PUBLISHED` / `FAILED` / `ARCHIVED` reject snapshot creation
- No `update_snapshot()` / `delete_snapshot()`

### Metadata boundary

| Structure | Metadata rule |
| --- | --- |
| `ResearchArtifactReference.metadata` | Rejects domain / run payload keys |
| `ResearchSnapshotReference.metadata` | Publishing context only; must not duplicate full snapshot content |
| Snapshot **content** | May contain normalized consumer findings / signals (that is the contract) |

Do not apply the artifact domain-field blacklist blindly to snapshot content.

## Deliberate limitations (still deferred)

- Additional snapshot contracts beyond Research Summary + Signal
- HTTP API routes / serving layer
- Frontend integration / consumption
- Database persistence
- Schedulers / background jobs
- Portfolio / risk / market snapshot types
- Portfolio construction publishing
- Automatic CSV/Parquet row counting
- Retraining or changes to factor/model calculations
- Generic multi-contract snapshot framework

## Related roadmap

See Phase 4 in [`docs/ROADMAP.md`](ROADMAP.md) and the repository [`ROADMAP.md`](../ROADMAP.md).
