# Repository Migration Report

> **Audit date:** 2026-07-13 · **Mode:** Read-only review · **Action taken:** Recommendations only  
> **PR-001 follow-up:** ADR numbering, Chapter-02 collision, legacy README archive, `docs/ARCHITECTURE.md` banner, `apps/api` runbook, LICENSE, and CI workflow were resolved in the engineering-foundation remediation. See [`docs/PR-001-FINAL-REVIEW.md`](docs/PR-001-FINAL-REVIEW.md). Historical findings below remain as the original audit trail.
>
> **2026-07-16 hygiene follow-up:** verified byte-identical files with the accidental ` 2` suffix were removed, the stale duplicate ADR index was retired, and CI now rejects numbered duplicate copies, non-example environment files, credentials, and local database artifacts. The original findings remain below for traceability.

## Executive summary

The repository has a functioning demonstration runtime and a strong frozen Architecture Bible, but it is midway between two engineering eras:

- the current deployed application lives in `backend/` and `frontend/`;
- the target modular-monolith pattern has begun in `apps/api/`;
- product and engineering truth is distributed across the old root README, `docs/ARCHITECTURE.md`, a local project tracker, slice notes, new Architecture Bible chapters, and two ADR naming schemes.

No file should be deleted or moved as a first step. The recommended approach is to establish authority, add automated quality gates, then migrate one verified vertical slice at a time. This report creates that inventory; it does not modify runtime behavior.

## Audit method

The review inspected repository paths, Git status, runtime manifests, environment templates, test locations, import references, architecture documents, ADRs, generated/cache artifacts, and deployment configuration. “Unused” below means no repository reference was found during static inspection; it does not prove a path has no external or manual use.

## Priority findings

| ID | Priority | Finding | Evidence | Recommendation |
|---|---|---|---|---|
| M-01 | High | Two backend roots represent current and target architectures | `render.yaml` deploys `backend/`; `apps/api/` contains only the Research/CreateResearch reference slice | Declare `backend/` current and `apps/api/` target until an approved cutover; migrate capability by capability with parity tests |
| M-02 | High | Architecture authority was fragmented | `docs/ARCHITECTURE.md` mixes current deployment, planned modules, and prior target layouts; Architecture Bible now defines the frozen model | Treat `docs/PROJECT_BIBLE.md` and Architecture Bible as authoritative; reclassify `docs/ARCHITECTURE.md` as a legacy implementation snapshot after content owners verify it |
| M-03 | High | Chapter numbering collides | Both `Chapter-02-Domain-Model.md` and `Chapter-02-Information-Architecture.md` claim Chapter 2 | Preserve both files; assign a canonical chapter order and rename only in a dedicated link-updating documentation migration |
| M-04 | High | ADR identifiers collide across naming schemes | Foundational `ADR-0001.md`…`ADR-0004.md` coexist with `0001-create-research-vertical-slice.md` and `0002-research-initial-state-draft.md` | Keep foundational IDs as requested; choose a separate slice-decision series or renumber the existing lowercase ADRs with redirect notes and updated links |
| M-05 | High | Target API lacks a self-contained dependency/run contract | `apps/api/` has source, tests, and `pytest.ini`, but no dependency manifest or documented supported entry point | Add packaging and commands in a dedicated engineering slice; do not present it as production-ready until checks run from a clean environment |
| M-06 | Medium | Automated repository quality gates are absent | No checked-in `.github/workflows`, root task runner, Python formatter/linter config, or frontend test configuration was found | Add CI incrementally: docs/links, Python tests, frontend type/build, then boundary and contract checks |
| M-07 | Medium | License language previously implied reuse without a license | No `LICENSE` file exists | Select an OSI license or explicit proprietary policy with owner approval; until then, state that reuse rights are not granted by default |
| M-08 | Medium | Current frontend lint command may not be a reliable gate | `frontend/package.json` uses `next lint` while the stack declares Next.js 15; no ESLint configuration was found | Verify the command in the supported Node environment, adopt an explicit ESLint setup if required, and document the canonical check |
| M-09 | Medium | A second root README contains the former product identity and setup narrative | `README 2.md` is a 352-line legacy copy that differs from the canonical `README.md` | Keep it during PR-001; after link/history review, archive it with a clear banner or remove it in a dedicated cleanup PR |

## Technical debt register

| Area | Debt | Consequence | Future treatment |
|---|---|---|---|
| Build and CI | No checked-in continuous-integration workflow or root quality command | verification depends on local knowledge | add clean-environment backend tests, target API tests, frontend type/build checks, and documentation validation |
| Python packaging | `apps/api/` has no self-contained dependency manifest or supported launch contract | the reference slice cannot be reproduced independently with confidence | adopt one packaging standard and document clean install/run commands |
| Frontend quality | no visible unit, component, or accessibility test setup; lint contract is uncertain | regressions rely heavily on build/manual checks | define ESLint, component tests, accessibility checks, and supported Node version |
| Architecture enforcement | dependency rules exist in documents only | module boundaries can erode silently | add import/boundary tests and CODEOWNERS-protected architecture review |
| Persistence evolution | current durable schema is managed as a schema file rather than a visible migration sequence | upgrades and rollback are difficult to audit | choose a migration framework before schema evolution expands |
| Operations | observability, recovery, and incident processes are target-state documents | production behavior lacks a complete operational contract | add runbooks, SLOs, backup/restore tests, and incident ownership |
| Release governance | no tagged release history or automated release process | users cannot map changes to supported versions | define versioning, release checklist, artifact provenance, and changelog automation |
| Licensing | no `LICENSE` file | repository is visible but not legally open source | select a license with owner approval before describing the project as licensed open source |

## Documentation inventory

### Canonical documents

| Document | Recommended status | Notes |
|---|---|---|
| `docs/PROJECT_BIBLE.md` | Canonical | repository product and engineering constitution |
| `docs/Architecture-Bible/Chapter-01-Vision.md` | Frozen | product vision |
| `docs/Architecture-Bible/Chapter-02-Domain-Model.md` | Frozen | domain model; numbering conflict remains administrative |
| `docs/Architecture-Bible/Chapter-03-State-Machine.md` | Frozen | authoritative business state vocabulary |
| `docs/Architecture-Bible/Chapter-04-Runtime-Architecture.md` | Frozen | target runtime and dependency model |
| `docs/adr/ADR-0001.md`…`ADR-0004.md` | Accepted | foundational engineering decisions |
| `PROJECT_STRUCTURE.md` | Canonical guide | current/target coexistence and folder conventions |

## Duplicate documentation

| Candidate | Overlap | Risk | Recommendation |
|---|---|---|---|
| `docs/ARCHITECTURE.md` | product concept, providers, persistence, modules, AI boundaries, future layout | readers may confuse a v1 implementation/planning snapshot with frozen target architecture | Add a legacy-status banner and split still-useful operational facts into an operations guide after verification |
| Former root `README.md` content | feature catalog, endpoints, deployment details, roadmap | mixes portfolio-demo positioning with the new research-OS identity | The rewritten README now links to durable sources; retain detailed endpoint truth near the current backend until migration |
| `docs/PROJECT_TRACKER.md` | status, deployment, roadmap, local Git notes | date-sensitive and intentionally ignored by `.gitignore`; references local/uncommitted state | Keep as a private operating notebook or replace with issues/project board; do not treat as architecture |
| `docs/slices/*.md` | structure, dependency diagrams, TODO integration notes | can become stale as slices evolve | Add owner/status/last-verified metadata and link each slice to its tests and ADRs |
| `docs/risk_knowledge/*.md` | policy, glossary, strategy notes | likely authoritative domain knowledge but governance status is not explicit | Add status, owner, version, effective date, and link to Governance context |
| `README 2.md` | previous README’s dashboard positioning, setup, API, and deployment content | competes with canonical product identity and can mislead contributors | Preserve for history in PR-001; archive or remove only after confirming no inbound links or unique operational facts |

## Obsolete-file candidates

No candidate was deleted. “Candidate” means the file appears superseded or local/generated and requires confirmation before cleanup.

| Candidate | Evidence | Required check before action |
|---|---|---|
| `README 2.md` | former title and dashboard-centric narrative; canonical `README.md` now exists | compare unique operational details, check inbound links and Git history |
| `docs/ARCHITECTURE.md` | mixes historical implementation, deployment status, and superseded target layouts | extract still-current runbook content and add archival banner |
| `docs/PROJECT_TRACKER.md` | date-sensitive local status and Git snapshot; intentionally ignored | confirm whether an external issue/project board replaces it |
| `.DS_Store`, `.pytest_cache/`, `.next/`, `tsconfig.tsbuildinfo` | local/generated artifacts, already ignored | confirm none is tracked; clean locally only through an approved maintenance action |

Active compatibility code—including `backend/`, `frontend/app/legacy/`, and `backend/app/recommendation/scoring.py`—is not an obsolete-file candidate because repository references or deployment configuration still use it.

## Naming inconsistencies

- Architecture chapters use both `Chapter-02` and `Chapter-04` styles; normalize only with automated link checking.
- `risk_knowledge` uses snake case while most documentation paths use hyphenated or title-style names.
- Root foundational ADRs use `ADR-NNNN.md`; existing slice ADRs use `NNNN-description.md`.
- Product names still occur as “AI Quant Signal Platform” in runtime metadata and implementation-era docs. Change product-facing metadata only as an intentional behavior/release task, not during documentation cleanup.

## Legacy and compatibility surfaces

### `backend/`

**Classification:** current runtime in a legacy location, not dead code.

`render.yaml` builds and starts this tree. It contains active backtest, market-data, recommendation, risk, paper-simulation, persistence, and API code. Do not remove or rename it before target slices demonstrate contract and behavior parity and deployment configuration is cut over.

### `apps/api/`

**Classification:** target architecture reference implementation, incomplete runtime.

It demonstrates correct inward dependencies for CreateResearch and includes unit/integration tests. Gaps include an explicit dependency manifest, standard developer command from repository root, production adapter strategy, and deployment/cutover plan.

### `frontend/app/legacy/` and `frontend/components/legacy/`

**Classification:** referenced compatibility UI.

The `/legacy` route imports `LegacyDashboard`, and workspace/overview modules link to legacy anchors. It is therefore not unused. Retire individual anchors only after their replacement journey has parity, analytics or manual use has been checked, and links are removed.

### `backend/app/recommendation/scoring.py`

**Classification:** active legacy-domain naming.

`backend/app/main.py` imports `score_latest_signal`; the module is in use. Its “recommendation” vocabulary is misaligned with the new product positioning, but renaming or changing behavior belongs to a tested migration slice.

## Potentially deprecated or stale material

| Item | Confidence | Reason | Recommendation |
|---|---|---|---|
| Deprecated Render hostname in old docs | High | `docs/ARCHITECTURE.md` explicitly labels it inactive | Retain only in migration/incident context; remove from normal setup guidance after link audit |
| Planned structures in `docs/ARCHITECTURE.md` | High | Several paths differ from frozen `apps/api/src/modules/...` target | Mark historical and link to `PROJECT_STRUCTURE.md` |
| Deployment status embedded in architecture docs | High | URLs and provider status are operational and time-sensitive | Move to a deployment/runbook document with owner and verification date |
| `docs/PROJECT_TRACKER.md` Git-status snapshot | High | dated and describes uncommitted file state | Keep private/ephemeral; use Git and issue tracking for current truth |
| UI module skeletons | Medium | some routes intentionally use placeholders or mock data | Label visibly as prototype; remove only after the owning module is implemented or explicitly dropped |

## Generated and local artifacts

The audit found ignored local artifacts including `.DS_Store`, `.pytest_cache/`, `frontend/.next/`, and `frontend/tsconfig.tsbuildinfo`. None is tracked according to the Git inspection. They do not require repository deletion in this task.

Recommendations:

- keep `.gitignore` coverage;
- use clean-environment CI so local caches cannot mask missing dependencies;
- optionally add a documented, non-destructive cleanup command in a future tooling change; and
- avoid scanning `node_modules`, virtual environments, caches, and generated build output in documentation audits.

## Structural gaps for production quality

These are foundation gaps, not defects in business functionality:

1. No checked-in CI workflow or branch protection policy is visible.
2. No root command surface coordinates backend, target API, frontend, and documentation checks.
3. The target API dependency manifest and operational entry point are incomplete.
4. Frontend unit/component/accessibility test tooling is not visible.
5. No automated architectural dependency test is visible.
6. No `LICENSE`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, or release/versioning policy is present.
7. No committed database migration framework is visible; the current runtime uses a schema file.
8. Observability, backup/restore, and incident runbooks are documented as future architecture rather than current operating controls.

Add these through separate, reviewable engineering changes. Do not combine them with domain feature work.

## Future improvements

Recommended engineering-only follow-ups after PR-001:

1. add CI workflows and required branch rules;
2. validate issue forms and Markdown links automatically;
3. establish dependency update and vulnerability scanning;
4. normalize Python packaging and supported runtime versions;
5. add frontend lint, test, and accessibility tooling;
6. enforce architectural imports and cross-context boundaries;
7. choose a license and publish versioning/release governance;
8. add `GOVERNANCE.md` when maintainer roles expand;
9. create operational runbooks and recovery exercises; and
10. resolve chapter, ADR, and duplicate-document naming through a dedicated documentation migration.

## Recommended migration sequence

### Stage 1 — Establish authority

- Adopt the Project Bible, foundational ADRs, contributor guide, and structure guide.
- Add banners to legacy architecture/status docs without deleting content.
- Resolve chapter and ADR numbering policy.

### Stage 2 — Make verification repeatable

- Define clean install and check commands for each current application root.
- Add CI for current backend tests and frontend build/type checks.
- Add Markdown link and Mermaid syntax validation.

### Stage 3 — Harden the reference slice

- Give `apps/api/` a dependency manifest, documented entry point, formatter/linter/type policy, and clean-environment tests.
- Add boundary tests that reject outward Domain imports and cross-context internals.

### Stage 4 — Migrate by vertical slice

- Inventory one current capability and its observable contracts.
- Add characterization tests around the legacy behavior.
- Implement the target slice behind explicit composition or routing.
- Compare behavior, data, errors, and operations.
- Cut over intentionally, retain rollback, then mark the old path deprecated.

### Stage 5 — Consolidate only after evidence

- Remove compatibility links and duplicate implementation only after usage and rollback windows close.
- Move the web application to `apps/web/` only as a dedicated mechanical migration with verified build/deploy paths.
- Archive historical docs with redirect notes; preserve ADR history.

## Decision log required before cleanup

Before any deletion or rename, owners should decide:

1. canonical Architecture Bible chapter numbering;
2. ADR numbering namespaces for foundational and slice decisions;
3. whether `docs/ARCHITECTURE.md` becomes an operations guide or an archived v1 snapshot;
4. the target package/dependency standard for Python;
5. the supported Node and Python versions;
6. licensing and security-reporting policy; and
7. the measurable cutover criteria from `backend/` to `apps/api/`.

## No-delete statement

This audit intentionally deleted, moved, or deprecated nothing. Every recommendation requires owner confirmation, link/reference analysis, and—where runtime paths are involved—tests plus a rollback plan.
