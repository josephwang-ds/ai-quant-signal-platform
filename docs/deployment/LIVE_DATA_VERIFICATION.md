# Live Data Verification

> **Status:** Code path implemented · **Last reviewed:** 2026-07-15

This runbook describes **optional, explicit** live verification for Yahoo and
AkShare market-data routing. It is separate from required offline CI.

## Purpose

Confirm that the deployed stack can retrieve and process real historical OHLCV
through:

```
MarketDataRouter → normalized OHLCV → Research Execution → provenance
```

Target smoke cases:

| Symbol | Provider | asset_class |
|---|---|---|
| SPY | yahoo | etf |
| 600519.SH | akshare | cn_equity |

## Offline CI vs live smoke

| Check | Required for PR CI | Network |
|---|---|---|
| `pytest tests -m "not live"` | Yes | Blocked |
| `tests/test_market_data_live.py -m live` | No | Allowed |
| `live-smoke.yml` workflow | No (manual dispatch) | Allowed |
| Local scripts below | No | Allowed |

A live-provider failure must **not** fail ordinary PR CI.

## Verification status wording

Use honest status labels in release notes:

- **Code path implemented** — helpers, tests, scripts, and workflow exist
- **Offline contract verified** — offline suite passes without network
- **Live Yahoo verified / not verified** — only after a real SPY run
- **Live AkShare verified / not verified** — only after a real 600519.SH run
- **Deployed backend verified / not verified** — only after POST to a deployed host

## Local market-data check

From `backend/`:

```bash
PYTHONPATH=. python scripts/live_market_data_check.py --symbol SPY
PYTHONPATH=. python scripts/live_market_data_check.py --symbol 600519.SH
```

Optional bounded dates:

```bash
PYTHONPATH=. python scripts/live_market_data_check.py \
  --symbol SPY --start-date 2023-01-01 --end-date 2024-12-31
```

Success prints concise JSON (no full price rows):

```json
{
  "ok": true,
  "symbol": "SPY",
  "provider": "yahoo",
  "row_count": 250,
  "actual_start": "2023-01-03",
  "actual_end": "2024-12-30",
  "cache_hit": false,
  "cache_stale": false,
  "warnings": []
}
```

Failures exit non-zero with `error_category` and no stack trace unless
`--verbose` is passed.

## Deployed backend verification

Requires a non-localhost deployed FastAPI origin:

```bash
PYTHONPATH=. python scripts/verify_deployed_research_api.py \
  --base-url https://<backend-host> \
  --symbol SPY \
  --start-date 2023-01-01 \
  --end-date 2024-12-31
```

The script POSTs to `/api/v1/research/execution` and validates:

- HTTP 200
- JSON-safe response
- provider provenance matches routing (`yahoo` for SPY, `akshare` for 600519.SH)
- no fabricated fallback warnings
- observation_count > 0

Do not hardcode production URLs in the repository.

## Manual GitHub Actions workflow

Workflow: `.github/workflows/live-smoke.yml`

- Trigger: `workflow_dispatch` only (not scheduled)
- Inputs: `run_yahoo`, `run_akshare` booleans
- Jobs: `live-yahoo`, `live-akshare` (10-minute timeout, Python 3.11)
- No secrets required
- Not a required check for merge

## Live pytest suite

```bash
# All live checks
PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -v

# Provider-specific
PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -k yahoo -v
PYTHONPATH=. python -m pytest tests/test_market_data_live.py -m live -k akshare -v
```

Default CI excludes `@pytest.mark.live` via `backend/pytest.ini`.

## Expected provenance fields

Live verification checks:

`provider`, `adapter`, `requested_symbol`, `canonical_symbol`,
`provider_symbol`, `asset_class`, `exchange`, `currency`, `adjustment`,
`interval`, `actual_start`, `actual_end`, `row_count`, `cache_hit`,
`cache_stale`, and `warnings`.

On a successful fresh live fetch, expect `cache_hit=false` and
`cache_stale=false`.

## Common failure modes

| Symptom | Likely cause |
|---|---|
| Yahoo timeout | Network restrictions (common in mainland China) |
| AkShare empty response | Provider outage, symbol halt, or date range gap |
| `provider_not_configured` | `akshare` not installed in active Python env |
| `unsupported_symbol` | Malformed ticker or bare 6-digit mainland code |
| `cache_stale` warning | Prior cache entry served after live failure — labeled, not silent |
| Deployed 502 | Provider unavailable on Render host |
| Deployed timeout | Cold start + provider latency; retry once manually |

## China-network caveats

- Yahoo / yfinance may be unstable or blocked from some China networks.
- AkShare is China-friendly but still subject to provider outages and rate limits.
- Do not interpret installed/configured status as live connectivity proof.

## Cache interpretation

- Cache TTL: 24 hours (`PriceCache`)
- Keys include provider, symbol, adjustment, start, end, interval
- Stale cache may be returned only with an explicit warning after provider failure
- Use a fresh `--cache-root` or temp directory when verifying a live fetch

## Demo evidence checklist (manual — do not commit screenshots)

Capture locally for portfolio evidence:

1. Research Execution page — SPY run with provenance banner
2. Provider provenance — `provider`, `asset_class`, `adjustment`
3. Validation results after execution-backed validation
4. Evaluation governance summary
5. Copilot citation grounded in validation evidence
6. Repeat for one A-share symbol (`600519.SH`) when AkShare live check succeeds

Do not commit screenshots containing local paths, tokens, or secrets.

## Related docs

- `docs/slices/multi-provider-market-data.md`
- `docs/deployment/PRODUCTION_API_WIRING.md`
- `backend/README.md`
