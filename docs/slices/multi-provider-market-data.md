# Multi-provider market data (PR-014)

Research execution and validation fetch historical OHLCV through one
`MarketDataPort`. Provider selection lives in infrastructure — upper layers
never import `yfinance` or `akshare` directly.

## Architecture

```
ResearchExecutionService / ResearchValidationService
  → MarketDataPort
  → MarketDataRouter
      ├── YahooFinanceMarketDataAdapter   (us_equity, hk_equity, etf, index, crypto)
      ├── AkShareMarketDataAdapter        (cn_equity)
      └── FixtureMarketDataAdapter        (offline tests only)
```

## Symbol classification

`classify_symbol()` returns a `SymbolDescriptor` with:

| Field | Purpose |
|---|---|
| `input_symbol` | User input preserved |
| `canonical_symbol` | Upper-case research symbol |
| `provider_symbol` | Provider-specific code (e.g. `600519` for `600519.SH`) |
| `exchange` | `SZ`, `SH`, `BJ`, `HK`, or `null` |
| `asset_class` | `us_equity`, `hk_equity`, `cn_equity`, `etf`, `index`, `crypto` |
| `currency` | `USD`, `CNY`, or `HKD` |
| `preferred_provider` | `yahoo` or `akshare` |

Examples:

| Symbol | asset_class | provider |
|---|---|---|
| AAPL | us_equity | yahoo |
| SPY | etf | yahoo |
| 0700.HK | hk_equity | yahoo |
| 000001.SZ | cn_equity | akshare |
| 600519.SH | cn_equity | akshare |
| BTC-USD | crypto | yahoo |

Bare six-digit codes without an exchange suffix are rejected.

## Adjustment policy

| Provider | Default | Recorded in provenance |
|---|---|---|
| Yahoo / yfinance | `auto_adjust` | `adjustment: "auto_adjust"` |
| AkShare A-shares | `qfq` (forward-adjusted) | `adjustment: "qfq"` |

Do not compare qfq mainland prices with incompatible unadjusted benchmarks
without documenting the mismatch.

## Normalized OHLCV contract

All adapters output ascending daily rows with:

`symbol`, `date`, `open`, `high`, `low`, `close`, `volume` (+ derived
`adjusted_close` for calculations).

Duplicate dates are rejected. NaN/Infinity must not reach API JSON.

## Cache

`PriceCache` keys:

```
provider|symbol|adjustment|start|end|interval
```

TTL: 24 hours (filesystem under `backend/.cache/market_data/`). Stale entries
may be returned only when explicitly labeled after a live provider failure.

Yahoo and AkShare never share an ambiguous cache key.

## Provenance

`DataProvenance` extends PR-008B fields with routing metadata:

`adapter`, `requested_symbol`, `canonical_symbol`, `provider_symbol`,
`asset_class`, `exchange`, `adjustment`, `row_count`.

## Error model

Shared categories (mapped to HTTP 400/502 by research services):

- `UnsupportedSymbolError` — malformed or unsupported symbol
- `UnsupportedProviderError` — invalid provider override
- `ProviderNotConfiguredError` — missing package
- `MarketDataUnavailableError` — provider failure (honest, no fabricated rows)
- `InsufficientHistoryError` — empty or filtered-out range
- `InvalidProviderResponseError` — unparseable provider payload

## Failover

**Not implemented in PR-014.** Preferred provider failure returns an honest
error. Cross-provider silent fallback is explicitly forbidden.

## Data-source status

`GET /api/data-sources/status` reports `routing_mode: "asset_class"` and
per-provider `installed` / `configured` / `supported_assets` flags.
`live_health_checked: false` — status does not call providers on every request.

## Offline tests

- `tests/test_market_data_router.py` — classification, routing, cache keys
- `tests/test_akshare_adapter.py` — Chinese column normalization (mocked akshare)
- Existing SPY fixture tests unchanged (`tests/fixtures/spy_daily_sample.csv`)

Live Yahoo smoke: `tests/test_research_execution_live.py` (manual CI workflow).

## Future work

- Cross-provider failover with explicit compatibility rules
- Persistent cache / Redis
- Additional providers (Polygon, Tiingo, Tushare)
- Real-time or intraday bars

## Honest limitations

- Not an exchange-grade or institutional feed
- No guaranteed completeness or real-time data
- AkShare and Yahoo may disagree on corporate-action semantics
- Default CI does not require live provider connectivity
