"""The Q&A function itself, executed rather than grepped.

`test_vercel_bundle` asserts that certain strings survive into the shipped
`index.js`, which catches a packaging mistake and nothing else. Scope
enforcement is the one path where a mistake silently widens what a model is
allowed to cite, so it is checked by running the handler under Node against a
real bundle built by the real builder.

Skipped when Node is unavailable; the pure-Python scope tests in
`test_ask_evidence` still cover the allow-list construction underneath.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is not installed"
)

HARNESS = """
const path = require("node:path");
const handler = require(path.join(process.argv[2], "index.js"));

const [, , , method, body] = process.argv;

const request = {
  method,
  headers: { origin: undefined, "x-forwarded-for": "203.0.113.7" },
  body: body ? JSON.parse(body) : undefined,
};

// The function sets `statusCode` directly and then calls `end`, the way a
// bare Node response works. Mirror that rather than a framework-style
// `status().json()`, or every assertion reads back a zero.
const response = {
  setHeader() {},
  statusCode: 0,
  end(text) {
    process.stdout.write(JSON.stringify({
      status: response.statusCode,
      payload: JSON.parse(text),
    }));
  },
};

handler(request, response).catch((error) => {
  process.stdout.write(JSON.stringify({ status: -1, error: String(error) }));
});
"""


def _snapshot() -> dict:
    return {
        "ticker": "ABC",
        "company_name": "ABC Corp.",
        "as_of": "2026-08-25",
        "benchmark": "SPY",
        "profile": {"display_name": "ABC Corp.", "source_url": "https://sec.gov/abc"},
        "performance": {
            "asset": {"total_return": 0.2, "cagr": 0.1, "max_drawdown": -0.2},
            "benchmark": {"total_return": 0.1},
            "relative_total_return": 0.1,
            "observations": 250,
        },
        "latest_filings": [],
        "headlines": [],
        "market_headlines": [],
    }


@pytest.fixture(scope="module")
def bundle(tmp_path_factory) -> Path:
    from build_vercel_output import build_vercel_output

    source = tmp_path_factory.mktemp("pages")
    for name in ("index.html", "404.html", "abc.html"):
        (source / name).write_text("<!doctype html><title>page</title>")
    (source / "abc.json").write_text(json.dumps(_snapshot()))
    output = build_vercel_output(source, tmp_path_factory.mktemp("out"))
    return output / "functions" / "api" / "ask.func"


def _call(bundle: Path, tmp_path: Path, method: str, body: dict | None) -> dict:
    harness = tmp_path / "harness.js"
    harness.write_text(HARNESS)
    result = subprocess.run(
        ["node", str(harness), str(bundle), method,
         json.dumps(body) if body is not None else ""],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


class TestScopeIsEnforcedByTheFunction:
    def test_get_advertises_the_scopes_and_the_default(self, bundle, tmp_path):
        answer = _call(bundle, tmp_path, "GET", None)
        assert answer["status"] == 200
        assert answer["payload"]["default_scope"] == "core"
        assert [scope["id"] for scope in answer["payload"]["scopes"]] == [
            "core", "company", "market", "all"]

    def test_an_unknown_scope_is_refused_before_any_provider_is_contacted(
            self, bundle, tmp_path):
        """Refused at 422, not quietly widened to the default.

        Falling back to a default on an unrecognised value is the failure mode
        worth avoiding here: a typo would silently answer from a different
        evidence set than the reader chose.
        """
        answer = _call(bundle, tmp_path, "POST", {
            "ticker": "ABC", "provider": "openai", "scope": "everything",
            "question": "What did the latest filing say about revenue?",
        })
        assert answer["status"] == 422
        assert answer["payload"]["error"] == "scope_not_available"
        assert answer["payload"]["scopes"] == ["core", "company", "market", "all"]

    def test_an_unknown_ticker_is_refused_before_the_scope_is_read(
            self, bundle, tmp_path):
        answer = _call(bundle, tmp_path, "POST", {
            "ticker": "ZZZZ", "provider": "openai", "scope": "core",
            "question": "What did the latest filing say about revenue?",
        })
        assert answer["status"] == 404
        assert answer["payload"]["error"] == "ticker_not_available"

    def test_a_valid_scope_passes_the_scope_gate(self, bundle, tmp_path):
        """Reaches the provider check, which fails only for a missing key.

        No provider key is configured in the test environment, so
        `model_not_available` is the correct next refusal -- and it proves the
        scope gate let the request through rather than short-circuiting it.
        """
        answer = _call(bundle, tmp_path, "POST", {
            "ticker": "ABC", "provider": "openai", "scope": "market",
            "question": "What did the latest filing say about revenue?",
        })
        assert answer["status"] == 400
        assert answer["payload"]["error"] == "model_not_available"

    def test_an_omitted_scope_falls_back_to_the_narrowest(self, bundle, tmp_path):
        answer = _call(bundle, tmp_path, "POST", {
            "ticker": "ABC", "provider": "openai",
            "question": "What did the latest filing say about revenue?",
        })
        # Same reasoning as above: past the scope gate, stopped at the key.
        assert answer["status"] == 400
        assert answer["payload"]["error"] == "model_not_available"


class TestBudgetCeiling:
    def test_get_reports_the_budget_and_whether_counters_are_shared(
            self, bundle, tmp_path):
        """The deployed limits must be checkable without spending anything."""
        answer = _call(bundle, tmp_path, "GET", None)
        limits = answer["payload"]["limits"]
        assert limits["daily_budget"] > 0
        # False here, and that is the honest answer for an unconfigured
        # environment: without a shared store the counters are per-instance.
        assert limits["shared_counters"] is False
