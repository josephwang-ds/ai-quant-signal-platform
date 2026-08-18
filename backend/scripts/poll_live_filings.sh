#!/bin/bash
# Cron wrapper for the live filing collector.
#
# Exists because the repository path contains spaces and non-ASCII characters,
# which are painful to quote correctly inside a crontab line, and because the
# SEC contact details should not be committed. Supply them via environment:
#
#   SEC_UA_NAME   e.g. "Jane Doe"
#   SEC_UA_EMAIL  e.g. jane@example.com
#
# Install with `crontab -e`:
#
#   SEC_UA_NAME=Your Name
#   SEC_UA_EMAIL=you@example.com
#   */30 9-18 * * 1-5 /path/to/backend/scripts/poll_live_filings.sh
#
# Deliberately no --backfill-days: the value of this collector is that receipt
# is *measured*, and sweeping old days would record "when I got round to
# reading it" under the same OBSERVED label.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -z "${SEC_UA_NAME:-}" || -z "${SEC_UA_EMAIL:-}" ]]; then
  echo "SEC_UA_NAME and SEC_UA_EMAIL must be set; SEC refuses undeclared clients" >&2
  exit 2
fi

cd "$BACKEND_DIR"
exec .venv/bin/python scripts/poll_live_filings.py \
  --name "$SEC_UA_NAME" --email "$SEC_UA_EMAIL" \
  >> "$BACKEND_DIR/outputs/text_corpus/collector.log" 2>&1
