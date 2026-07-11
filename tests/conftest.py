import pytest

from storage import init_db


@pytest.fixture(autouse=True)
def _clew_test_db(monkeypatch, tmp_path):
    """Every test gets its own throwaway SQLite file so tests never touch
    (or depend on) the real clew.db."""
    db_path = tmp_path / "test_clew.db"
    monkeypatch.setenv("CLEW_DB_PATH", str(db_path))
    init_db()
    yield
