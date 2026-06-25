import pytest
import database
import config


@pytest.fixture
def tmp_db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.init_db(db_path)
    return db_path


@pytest.fixture
def test_client(tmp_db, monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DB_PATH", tmp_db)
    monkeypatch.setattr(config, "API_KEY", "test-key")
    monkeypatch.setattr(config, "LOG_PATH", str(tmp_path / "events.log"))
    monkeypatch.setattr(config, "SMTP_USER", "")
    from fastapi.testclient import TestClient
    import app as app_module
    with TestClient(app_module.app) as client:
        yield client
