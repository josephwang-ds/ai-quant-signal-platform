from __future__ import annotations

import json

from scripts.build_vercel_output import build_vercel_output


def test_vercel_bundle_contains_public_html_but_not_snapshot_json(tmp_path) -> None:
    source = tmp_path / "company_pages"
    source.mkdir()
    for name in ("index.html", "404.html", "aapl.html"):
        (source / name).write_text(f"<html>{name}</html>")
    (source / "aapl.json").write_text('{"private_build_artifact": true}')

    output = build_vercel_output(source, tmp_path / "vercel_frontend")
    static = output / "static"

    assert sorted(path.name for path in static.iterdir()) == [
        "404.html",
        "aapl.html",
        "index.html",
    ]
    assert not list(static.glob("*.json"))
    config = json.loads((output / "config.json").read_text())
    assert config["version"] == 3
    assert config["routes"][0] == {"src": "/", "dest": "/index.html"}
    assert config["routes"][-1]["status"] == 404
    assert not (output / "functions").exists()


def test_vercel_bundle_packages_private_grounded_ask_function(tmp_path) -> None:
    source = tmp_path / "company_pages"
    source.mkdir()
    for name in ("index.html", "404.html", "abc.html"):
        (source / name).write_text(f"<html>{name}</html>")
    snapshot = {
        "ticker": "ABC",
        "company_name": "ABC Corp.",
        "as_of": "2026-08-25",
        "benchmark": "SPY",
        "profile": {"display_name": "ABC Corp."},
        "performance": {
            "asset": {"total_return": 0.2, "cagr": 0.1, "max_drawdown": -0.2},
            "benchmark": {"total_return": 0.1},
            "relative_total_return": 0.1,
            "observations": 250,
        },
        "latest_filings": [],
        "headlines": [],
    }
    (source / "abc.json").write_text(json.dumps(snapshot))

    output = build_vercel_output(source, tmp_path / "vercel_frontend")
    function = output / "functions" / "api" / "ask.func"

    assert (function / "index.js").is_file()
    assert (function / ".vc-config.json").is_file()
    evidence = json.loads((function / "evidence.json").read_text())
    assert evidence["companies"]["ABC"]["evidence"]["ticker"] == "ABC"
    assert not list((output / "static").glob("*.json"))
    function_config = json.loads((function / ".vc-config.json").read_text())
    assert function_config["runtime"] == "nodejs22.x"
    assert function_config["handler"] == "index.js"
