# Production API Wiring

> **Status:** Current deployment contract · **Last reviewed:** 2026-07-14

This runbook defines how the Next.js presentation runtime reaches the FastAPI
boundary. It does not change the domain or provider architecture described by
the [Project Bible](../PROJECT_BIBLE.md).

## Frontend base URL contract

`NEXT_PUBLIC_API_BASE_URL` is the single frontend API origin setting.

- In local development and tests, an unset value resolves to exactly
  `http://127.0.0.1:8000`.
- In a production build/runtime, the variable is required. Missing or invalid
  configuration fails before any network request; there is no localhost or
  hardcoded Render fallback.
- Values are trimmed, trailing slashes are removed, and only absolute `http`
  or `https` URLs are accepted. A trailing slash is optional.
- This is a public browser variable. Put no API keys, database URLs, tokens, or
  other secrets in it.

Local example:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Production example:

```dotenv
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

In Vercel, set the variable for every intended environment and redeploy.
`NEXT_PUBLIC_*` values are embedded into the browser build, so changing the
setting without a new deployment does not update an existing build.

## Backend CORS contract

Set `ALLOWED_ORIGINS` on Render to the comma-separated browser origins allowed
to call FastAPI:

```dotenv
ALLOWED_ORIGINS=https://your-project.vercel.app,https://www.example.com
```

Origins are trimmed, trailing slashes are removed, and duplicates are ignored.
Use origins only (no paths). `*` is rejected; credentials remain disabled.
When unset, the backend keeps its explicit localhost/127.0.0.1 ports 3000 and
3001 defaults for local development.

## Failure categories

The frontend transport preserves safe backend detail for debugging while UI
hooks render stable messages:

- `configuration`: missing, malformed, or unsupported production API URL
- `network`: the browser could not reach the backend
- `timeout`: the bounded request timer elapsed
- `backend_unavailable`: HTTP 503
- `provider_unavailable`: HTTP 502; no fallback values are fabricated
- `invalid_request`: HTTP 400 or 422
- `not_found`: HTTP 404; Evaluation gives a specific missing-Validation message
- `server_error`: other 5xx responses
- `unknown`: unclassified failures or invalid JSON success responses

Caller cancellation remains an `AbortError`; it is not mislabeled as timeout.
Requests are not retried automatically.

## Timeout policy

- Canonical Research Execution, Validation, and Evaluation POST requests:
  60 seconds. This accommodates bounded validation sensitivity grids.
- `/health` and `/api/data-sources/status`: 5 seconds.

## Operational endpoint semantics

- `GET /health` is process liveness only. `status: ok` does not prove market
  data, database, or other dependency connectivity.
- `GET /api/data-sources/status` reports configured/install-time provider
  capability and planned providers. It is not a live connectivity probe.
- A request that actually retrieves historical data is the evidence of
  provider availability for that operation.

## Troubleshooting

1. A configuration message in production: verify the Vercel variable is set
   to an absolute HTTP(S) backend URL, then redeploy.
2. A browser CORS failure: verify Render `ALLOWED_ORIGINS` contains the exact
   deployed Vercel origin without a path; restart/redeploy the backend after
   changing it.
3. Backend unavailable/timeout: check Render startup and runtime logs. A cold
   start can make liveness temporarily unavailable.
4. Provider unavailable: inspect the safe backend detail/logs and the provider
   request. Do not infer live connectivity from the static status endpoint.
5. Successful `/health` with failed research: investigate the specific
   provider or application request; liveness does not certify dependencies.
