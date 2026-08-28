from __future__ import annotations

import json
from pathlib import Path

import pytest

from company_lens.cli import main
from company_lens.contracts import Citation, CompanySnapshot, FilingBrief
from company_lens.storage import LocalJsonStorage


def test_cli_reports_supported_scope_before_reading_data(tmp_path, capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["TSLA", "--data-dir", str(tmp_path)])

    assert error.value.code == 2
    message = capsys.readouterr().err
    assert "TSLA" in message
    assert "not in the current local company universe" in message
    assert "0 companies" in message


def test_cli_retrieval_controls_require_llm(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["AAPL", "--llm-document", "note.md"])

    assert error.value.code == 2
    assert "require --llm" in capsys.readouterr().err


def test_cli_search_controls_require_an_import_source(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(["AAPL", "--llm", "--llm-search-query", "management changes"])

    assert error.value.code == 2
    assert "require --llm-document or --llm-headlines" in capsys.readouterr().err


@pytest.mark.parametrize("backend", ["local"])
def test_cli_persists_retrieval_rules_and_fallback_provenance_locally(
    tmp_path,
    monkeypatch,
    backend: str,
) -> None:
    performance = {
        "asset": {"total_return": 0.2, "cagr": 0.1, "max_drawdown": -0.15},
        "benchmark": {"total_return": 0.1},
        "relative_total_return": 0.1,
        "observations": 10,
        "beta": 1.0,
    }
    filing = FilingBrief(
        accession="0001",
        form="8-K",
        accepted_at="2026-08-20T17:00:00-04:00",
        items=[{"code": "2.02", "label": "Results of operations"}],
        source_url="https://www.sec.gov/example",
        novelty=None,
        passages=[
            Citation(
                anchor="0001#sentence-1",
                accession="0001",
                source_url="https://www.sec.gov/example",
                text="Revenue increased.",
            )
        ],
    )
    snapshot = CompanySnapshot(
        schema_version="test",
        ticker="AAPL",
        company_name="Apple Inc.",
        as_of="2026-08-20",
        benchmark="SPY",
        period={"start": "2026-01-01", "end": "2026-08-20"},
        profile={},
        market={},
        performance=performance,
        growth=[],
        period_options={},
        latest_filings=[filing],
        explanation={"mode": "deterministic_fallback"},
        provenance={},
    )

    class OfflineProvider:
        provider_name = "offline-test"
        model = "no-network"

        def generate(self, request):
            del request
            raise RuntimeError("provider unavailable")

    def fake_render(value, output):
        del value
        path = Path(output)
        path.write_text("<html>offline</html>", encoding="utf-8")
        return path

    monkeypatch.setattr("company_lens.cli.build_snapshot", lambda *args, **kwargs: snapshot)
    monkeypatch.setattr(
        "company_lens.cli.create_explanation_provider",
        lambda *args, **kwargs: OfflineProvider(),
    )
    monkeypatch.setattr("company_lens.cli.render_company_page", fake_render)
    document = tmp_path / "note.md"
    document.write_text("Revenue was $45 million.", encoding="utf-8")
    storage_dir = tmp_path / "storage"

    result = main(
        [
            "AAPL",
            "--llm",
            "--llm-document",
            str(document),
            "--llm-rule",
            "Explain legal terms plainly.",
            "--llm-min-relevance",
            "0",
            "--storage-dir",
            str(storage_dir),
            "--storage-backend",
            backend,
            "--llm-cache",
            str(tmp_path / "cache"),
            "--out",
            str(tmp_path / "snapshot.json"),
            "--html-out",
            str(tmp_path / "page.html"),
        ]
    )

    storage = LocalJsonStorage(storage_dir)
    assert result == 0
    assert len(storage.list_records("documents")) == 1
    assert len(storage.list_records("chunks")) == 1
    assert len(storage.list_records("rulesets")) == 1
    assert len(storage.list_records("retrieval_runs")) == 1
    assert storage.list_records("llm_runs")[0]["validator_status"] == (
        "deterministic_fallback"
    )
    payload = json.loads((tmp_path / "snapshot.json").read_text(encoding="utf-8"))
    expected_status = "stored"
    grounded = payload["provenance"]["grounded_explanation"]
    assert grounded["storage"]["status"] == expected_status
    assert grounded["retrieval"]["storage"]["status"] == expected_status
