# Deployed End-to-End Verification

> **PR-016** · Verified on 2026-07-15 · Operator-supplied public hosts from repository docs  
> Script entrypoints used: `backend/scripts/verify_deployed_research_api.py`, `curl` health/status probes

## Environment

| Component | Source of URL | Host used |
|---|---|---|
| Backend (Render) | Public docs (`backend/README.md`, `docs/PROJECT_TRACKER.md`, `docs/ARCHITECTURE.md`) | `https://ai-quant-signal-platform.onrender.com` |
| Frontend (Vercel) | Public docs (`docs/PROJECT_TRACKER.md`) | `https://signals.josephjwang.com` |
| Secrets | None printed or committed | — |

No deployment URL was hard-coded into application source. Verification passed `--base-url` on the CLI only.

## Backend Health

| Check | Result |
|---|---|
| `GET /health` | **Verified** — HTTP 200, JSON `{"status":"ok","service":"ai-quant-signal-backend"}` |
| Stack traces | **Verified** — none in health body |
| Latency | ~0.8–1.0s warm; no extreme cold-start stall observed on this run |
| Distinguishing semantics | **Verified** — process health ≠ market-data health (process up only) |

## Provider Status

`GET /api/data-sources/status` — **Verified**

| Field | Observed |
|---|---|
| `routing_mode` | `asset_class` |
| Yahoo | `installed: true`, `configured: true`, assets `us_equity/hk_equity/etf/index/crypto`, `live_health_checked: false` |
| AkShare | `installed: true`, `configured: true`, assets `cn_equity`, `live_health_checked: false` |
| Obsolete `stooq` / `auto` failover claims | **Absent** (no `stooq` or `auto` provider entries) |
| CORS for frontend origin | `Access-Control-Allow-Origin: https://signals.josephjwang.com` |

Installed/configured does **not** mean live provider connectivity was proven by the status endpoint.

## Yahoo SPY Execution

Command:

```bash
PYTHONPATH=. python scripts/verify_deployed_research_api.py \
  --base-url https://ai-quant-signal-platform.onrender.com \
  --symbol SPY \
  --start-date 2023-01-01 \
  --end-date 2024-12-31
```

| Attempt | Result | Classification |
|---|---|---|
| 1 | HTTP 502 — `No price data returned for ticker 'SPY'.` | Provider/network flake |
| 2 | HTTP 200 — verification script `ok: true` | **Verified** |

Attempt 2 provenance (summary only):

| Field | Value |
|---|---|
| `provider` | `yahoo` |
| `asset_class` | `etf` |
| `canonical_symbol` | `SPY` |
| `adjustment` | `auto_adjust` |
| `row_count` | 502 |
| `observation_count` | 443 |
| `actual_start` / `actual_end` | `2023-01-03` → `2024-12-31` |
| `cache_hit` / `cache_stale` | `false` / `false` |
| Fabricated fallback warnings | None |
| Localhost evidence | None |
| Latency | ~2s (warm) |

## AkShare 600519.SH Execution

| Attempt | Result | Classification |
|---|---|---|
| 1 | HTTP 502 — AkShare `RemoteDisconnected` | **Failed due to provider/network** |
| 2 | HTTP 502 — same `RemoteDisconnected` | **Failed due to provider/network** |

Honest classification: **egress/provider remote disconnect**, not package-missing (`data-sources/status` reports AkShare installed/configured). No fabricated OHLCV was returned. Failure detail remained JSON `detail` string (no stack trace).

## Frontend Wiring

| Check | Result |
|---|---|
| Production JS embeds Render backend host | **Verified** — `ai-quant-signal-platform.onrender.com` present in `/_next/static/chunks/637-….js` |
| Localhost fallback in production bundles scanned | **Verified absent** for `127.0.0.1:8000` / `localhost:8000` |
| CORS from frontend origin to backend health/status/execution | **Verified** |
| Research Workspace route exists | `/research/ma-crossover-spy` present in app router |
| Browser SSR load of Research Workspace | **Partially verified** — route resolves app chunks, but this probe observed HTTP 500 RSC digest during curl fetch (client-side behavior not fully audited) |
| Code contract: production requires `NEXT_PUBLIC_API_BASE_URL` | **Verified** in source (`frontend/lib/apiConfig.ts`) |

## Copilot Configuration

| Check | Result |
|---|---|
| `OPENAI_API_KEY` present | **Absent** (inferred) |
| Response without key | **Verified** — HTTP 503 `Research Copilot is not configured for this deployment.` |
| FakeLlmAdapter production path | **Verified absent** — `resolve_llm_adapter()` raises 503 when key missing; FakeLlm is test-only |
| Bounded paid Copilot smoke | **Not applicable** — key not configured; no paid request sent |

## Failure-State Verification

| Case | HTTP | Detail (category) | Result |
|---|---|---|---|
| Malformed symbol `!!!!` | 400 | Unsupported symbol format | **Verified** |
| Ambiguous bare mainland `600519` | 400 | Requires `.SZ` / `.SH` | **Verified** |
| Unknown `validation_run_id` (Evaluation) | 404 | Honest guidance message | **Verified** |
| Copilot without config / missing run | 503 | Not configured | **Verified** |
| Provider failure (AkShare disconnect) | 502 | JSON detail, no fixture rows | **Verified** |
| Stack traces in error bodies | — | None observed | **Verified** |
| Unsupported arbitrary provider override public | — | Not exposed as public request field in Execution API | **Verified** (status: Not applicable / closed design) |

## Latency Observations

| Endpoint | Observed latency (approx.) |
|---|---|
| `/health` | 0.8–1.0s |
| `/api/data-sources/status` | ~1.6s |
| SPY execution (success) | ~2s |
| A-share attempts | ~2s fail-fast on remote disconnect |

## Verified Claims

- Deployed FastAPI process is up and returns JSON health.
- Research market-data status uses `routing_mode: asset_class` with Yahoo + AkShare capability flags; no obsolete Stooq/auto failover claim in that endpoint.
- Deployed SPY Research Execution succeeds with Yahoo provenance, JSON-safe metrics, and no fabricated fallback (**after one provider flake retry**).
- Frontend production build binds to the Render backend host; CORS allows the production frontend origin.
- Copilot is honestly unconfigured (503) with no Fake LLM runtime fallback.
- Invalid symbols and missing validation runs return honest 400/404 without stack traces.
- Provider failures return HTTP 502 without inventing OHLCV.

## Unverified Claims

- Consistent Yahoo availability from Render on first try (attempt 1 failed).
- Deployed AkShare live A-share execution for `600519.SH` (both attempts failed due to remote disconnect).
- Copilot grounded LLM answer quality (key absent — not applicable).
- Persistent process cold-start after long idle (not deliberately measured).
- Exchange-grade or guaranteed continuous provider availability.

## PR-017 Research Workspace SSR exception

| Item | Detail |
|---|---|
| Production URL | `https://signals.josephjwang.com/research/ma-crossover-spy` |
| Observed digest | `440809330` |
| Local reproduction digest | `1607303388` (same class) |
| Exception | `Error: Event handlers cannot be passed to Client Component props.` |
| Root cause | Server Component Suspense fallback in `frontend/app/research/[researchId]/page.tsx` passed a no-op `onLanguageChange` callback into Client `AppShell` |
| Fix | Remove shell wrapper from the Server fallback; render only `SectionCard` + `ResearchWorkspaceSkeleton`. Add route `loading.tsx` / `error.tsx`. |
| Local production verification | **Verified** — `npm run build && next start`; `curl http://127.0.0.1:3000/research/ma-crossover-spy` → HTTP 200, `workspace-shell` present, no digest error. Also HTTP 200 when `NEXT_PUBLIC_API_BASE_URL` is absent at build time. |
| Vercel preview verification | Not verified in this documentation update — pending PR preview browser check |
| Post-merge production verification | Not verified until merge + redeploy |

## Known Limitations

- Render egress + Yahoo can occasionally return empty ticker payloads; retry once is acceptable for smoke, not for guaranteed uptime.
- AkShare mainland data from Render may be blocked or disconnect; package installed ≠ connectivity.
- Process `/health` must never be marketed as market-data readiness.
- Copilot remains disabled until `OPENAI_API_KEY` is configured in deployment secrets.
- Browser UX screenshots for Execution → Validation → Copilot remain operator-captured after production redeploy.

## Final Verdict

**Partially verified production research wiring**, with Research Workspace SSR failure **root-caused and fixed in PR-017** (local production route verified; Vercel preview/production browser confirmation pending merge).

| Area | Label |
|---|---|
| Backend health | Verified |
| Provider status | Verified |
| Yahoo SPY execution | Verified (after 1 flake) |
| AkShare 600519.SH execution | Failed due to provider/network |
| Frontend production wiring | Verified (API/CORS) |
| Research Workspace SSR route | Fixed locally; preview/production browser pending |
| Copilot configuration | Verified (absent key / honest 503) |
| Failure states | Verified |
| Deployed end-to-end readiness overall | Partially verified |
