"""Tests for optional research lifecycle persistence helpers."""

import pytest

from app.db.repositories.backtest_runs import DatabaseUnavailableError
from app.db.repositories import research_lifecycle as repo


def test_require_database_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(repo, "is_database_configured", lambda: False)
    with pytest.raises(DatabaseUnavailableError):
        repo.require_database()


def test_persistence_mode_browser_local(monkeypatch) -> None:
    monkeypatch.setattr(repo, "is_database_configured", lambda: False)
    assert repo.persistence_mode() == "browser-local"


def test_persistence_mode_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(repo, "is_database_configured", lambda: True)

    class Boom:
        def __enter__(self):
            raise RuntimeError("offline")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(repo, "get_db_connection", lambda: Boom())
    assert repo.persistence_mode() == "persistence-unavailable"


def test_json_stable_key_order() -> None:
    a = repo._json({"b": 1, "a": 2})
    b = repo._json({"a": 2, "b": 1})
    assert a == b
