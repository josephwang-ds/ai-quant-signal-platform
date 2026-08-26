"""Company Facts transport, against a fake network."""

from __future__ import annotations

from filing_triage.ingest.edgar import (
    SEC_COMPANY_FACTS_URL,
    EdgarClient,
)


def test_company_facts_url_pads_cik() -> None:
    assert SEC_COMPANY_FACTS_URL.format(cik=320193) == (
        "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
    )


def test_company_facts_uses_immutable_cache_and_refresh(tmp_path, monkeypatch) -> None:
    client = EdgarClient(user_agent="Test test@example.com", cache_dir=tmp_path)
    calls: list[str] = []

    def fake_get(url: str) -> bytes:
        calls.append(url)
        return b'{"cik":320193,"entityName":"Apple Inc.","facts":{}}'

    monkeypatch.setattr(client, "_get", fake_get)

    first = client.company_facts(320193)
    second = client.company_facts(320193)
    assert first == second
    assert len(calls) == 1
    assert calls[0].endswith("companyfacts/CIK0000320193.json")
    cache = tmp_path / "companyfacts" / "CIK0000320193.json"
    assert cache.exists()
    assert cache.read_bytes().startswith(b'{"cik"')

    refreshed = client.company_facts(320193, refresh=True)
    assert refreshed["entityName"] == "Apple Inc."
    assert len(calls) == 2


def test_company_facts_refresh_overwrites_stale_cache(tmp_path, monkeypatch) -> None:
    client = EdgarClient(user_agent="Test test@example.com", cache_dir=tmp_path)
    path = tmp_path / "companyfacts" / "CIK0000320193.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b'{"cik":320193,"entityName":"stale"}')
    monkeypatch.setattr(client, "_get", lambda _: b'{"cik":320193,"entityName":"fresh"}')

    payload = client.company_facts(320193, refresh=True)
    assert payload["entityName"] == "fresh"
    assert path.read_bytes() == b'{"cik":320193,"entityName":"fresh"}'


def test_company_facts_reuse_does_not_call_network(tmp_path, monkeypatch) -> None:
    client = EdgarClient(user_agent="Test test@example.com", cache_dir=tmp_path)
    path = tmp_path / "companyfacts" / "CIK0000320193.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b'{"cik":320193,"entityName":"cached"}')
    monkeypatch.setattr(
        client, "_get", lambda _: (_ for _ in ()).throw(AssertionError("network"))
    )

    payload = client.company_facts(320193)
    assert payload["entityName"] == "cached"
