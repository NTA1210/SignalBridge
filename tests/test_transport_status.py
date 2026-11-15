import pytest

def test_x_enabled_flag_never_claims_unverified_config_as_delivery(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "mode.sqlite3"))
    monkeypatch.setenv("X_ENABLE_LIVE_SEND", "true")
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "")
    monkeypatch.setenv("X_TEST_ALLOWLIST_IDS", "123")
    with TestClient(app) as c:
        conf = c.get("/api/state").json()["config"]
        assert conf["x_send_requested"] is True
        assert conf["x_send_enabled"] is False
        assert conf["mode"] == "LOCAL DEMO"
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "fixture-not-real")
    with TestClient(app) as c:
        conf = c.get("/api/state").json()["config"]
        assert conf["x_send_enabled"] is True
        assert "UNVERIFIED" in conf["mode"]
        assert "NOT verified" in conf["x_status"]
        assert "fixture-not-real" not in str(conf)
