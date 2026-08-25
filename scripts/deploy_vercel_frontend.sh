#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE_ROOT="${VERCEL_BUNDLE_ROOT:-$PROJECT_ROOT/data/build/vercel_frontend}"
GLOBAL_CONFIG="${VERCEL_GLOBAL_CONFIG:-$PROJECT_ROOT/data/vercel-cli}"

for variable in VERCEL_TOKEN VERCEL_ORG_ID VERCEL_PROJECT_ID; do
  if [[ -z "${!variable:-}" ]]; then
    echo "$variable is required for non-interactive Vercel deployment" >&2
    exit 1
  fi
done
if ! command -v vercel >/dev/null 2>&1; then
  echo "Vercel CLI is not installed" >&2
  exit 1
fi
if [[ ! -f "$BUNDLE_ROOT/.vercel/output/config.json" ]]; then
  echo "Vercel prebuilt output is missing; run scripts/build_vercel_output.py" >&2
  exit 1
fi
mkdir -p "$GLOBAL_CONFIG"

vercel deploy \
  --cwd "$BUNDLE_ROOT" \
  --global-config "$GLOBAL_CONFIG" \
  --prebuilt \
  --archive=tgz \
  --prod \
  --yes \
  --token "$VERCEL_TOKEN"
