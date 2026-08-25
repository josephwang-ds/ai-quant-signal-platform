#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${COMPANY_LENS_PYTHON:-$PROJECT_ROOT/.venv/bin/python}"
LOCK_FILE="${COMPANY_LENS_LOCK_FILE:-/tmp/company-lens-refresh.lock}"

cd "$PROJECT_ROOT" || exit 1
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "another Company Lens refresh is already running"
  exit 0
fi

status=0
PYTHONPATH=src "$PYTHON_BIN" scripts/refresh_filings.py || status=$?
PYTHONPATH=src "$PYTHON_BIN" scripts/refresh_market_data.py || status=$?
HEADLINE_INDEX="${COMPANY_LENS_HEADLINE_INDEX:-$PROJECT_ROOT/data/build/headlines.json}"
if [[ -n "${FINNHUB_API_KEY:-}" ]]; then
  PYTHONPATH=src "$PYTHON_BIN" scripts/refresh_headlines.py --out "$HEADLINE_INDEX" || status=$?
else
  echo "FINNHUB_API_KEY is not configured; skipping live headline refresh"
fi

# Always rebuild from the last good merged artifacts. A partial upstream failure
# remains visible in provenance without taking the static site offline.
build_args=()
if [[ -s "$HEADLINE_INDEX" ]]; then
  build_args+=(--headline-index "$HEADLINE_INDEX")
fi
PYTHONPATH=src "$PYTHON_BIN" scripts/build_company_pages.py "${build_args[@]}" || exit 1
PYTHONPATH=src "$PYTHON_BIN" scripts/evaluate_filing_changes.py || status=$?
PYTHONPATH=src "$PYTHON_BIN" scripts/build_vercel_output.py || status=$?

if [[ "${VERCEL_DEPLOY_ENABLED:-0}" == "1" ]]; then
  scripts/deploy_vercel_frontend.sh || status=$?
fi

echo "Company Lens scheduled refresh finished with status $status"
exit "$status"
