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
