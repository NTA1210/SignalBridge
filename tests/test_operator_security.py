import pytest
from app import x_api

def test_cross_origin_writes_are_rejected(tmp_path, monkeypatch):
    """A known public header does not give untrusted web origins write access."""
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "origin.sqlite3"))
    with TestClient(app) as c:
        headers = {
            "X-Local-Operator": "signalbridge-local",
            "Origin": "https://untrusted.example",
        }
        response = c.post("/api/discover/demo",
                          json={"segment": "robotics"}, headers=headers)
        assert response.status_code == 403
        assert "Cross-origin" in response.json()["detail"]
        good = c.post("/api/discover/demo",
                      json={"segment": "robotics"},
                      headers={"X-Local-Operator": "signalbridge-local",
                               "Origin": "http://testserver"})
        assert good.status_code == 200

def test_untrusted_host_is_rejected():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        response = c.get("/healthz", headers={"Host": "untrusted.example"})
        assert response.status_code == 400

def test_malformed_allowlist_ids_do_not_enable_real_test(monkeypatch):
    monkeypatch.setenv("X_TEST_ALLOWLIST_IDS", "bad, ,123,abc-1,123")
    assert x_api.allowed_ids() == {"123"}
    monkeypatch.setenv("X_TEST_ALLOWLIST_IDS", "not-numeric")
    assert x_api.allowed_ids() == set()

